#
# Collective Knowledge (checking and installing software)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Developer: Leo Gordon, leo@dividiti.com
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel)

hackathon_date          = '20190127'

hackathon_tag           = 'hackathon-{}'.format(hackathon_date)
hackathon_remote_repo   = 'ck-quantum-hackathon-{}'.format(hackathon_date)
hackathon_local_repo    = hackathon_remote_repo     # to simplify hackathon.20190127.get_raw_data()
competition_tag         = 'quantum-ml-hackathon-3'


import getpass
import os
import shutil


def init(i):
    """
    Not to be called directly.
    """

    return {'return':0}


def store_experiment(i):
    """
    Input:  {
                json_file           - filename/path of the JSON file that was generated by an experimental run
                team                - your team name
                (experiment_name)   - your preferred name for the experiment (auto-generated otherwise)
            }

    Output: {
                return              - return code =  0, if successful
                                                  >  0, if error
                (error)             - error text if return > 0
            }
    """

    json_input_filepath = i.get('json_file')
    if not json_input_filepath:
        r = ck.inp({'text': "Please provide the path to the experimental JSON output to be stored: "})
        json_input_filepath = r['string']

    team_name           = i.get('team')
    if not team_name:
        r = ck.inp({'text': "Your team name: "})
        team_name = r['string']


    experiment_name     = i.get('experiment_name')
    if not experiment_name:

        r=ck.get_current_date_time({})
        if r['return']>0: return r
        timestamp   = r['iso_datetime'].split('.')[0].replace(':', '_').replace('-', '_')   # cut to seconds' resolution

        r = ck.load_json_file( {'json_file': json_input_filepath} )
        if r['return']>0: return r
        json_contents = r['dict']

        experiment_name = '-'.join( [team_name, timestamp, json_contents['problem_name'], json_contents['solution_function_name']] )

    load_adict = {  'action':           'load',
                    'module_uoa':       'program',
                    'data_uoa':         'benchmark-helper',
    }
    r=ck.access( load_adict )
    if r['return']>0: return r

    exp_generating_program_path     = r['path']

    json_output_filepath = os.path.join(exp_generating_program_path, 'solution_output.json')

    shutil.copyfile(json_input_filepath, json_output_filepath)


    ## Making sure hackathon_local_repo exists before we start recording there:
    #
    load_adict = {  'action':           'load',
                    'module_uoa':       'repo',
                    'data_uoa':         hackathon_local_repo,
    }
    r=ck.access( load_adict )
    if r['return']==16:     # No hackathon_local_repo ?  Create it then!
        add_adict = {   'action':           'add',
                        'module_uoa':       'repo',
                        'data_uoa':         hackathon_local_repo,
                        'quiet':            'yes',
        }
        r=ck.access( add_adict )
        if r['return']>0: return r

    ## The actual JSON data recording:
    #
    r = ck.access({ 'action':                   'benchmark',
                    'module_uoa':               'program',
                    'data_uoa':                 'benchmark-helper',
                    'cmd_key':                  'default',

                    'repetitions':              1,
                    'iterations':               1,
                    'skip_stat_analysis':       'yes',
                    'process_multi_keys':       [ '##choices#env#*' ],
                    'no_state_check':           'yes',
                    'no_compiler_description':  'yes',
                    'skip_calibration':         'yes',
                    'speed':                    'no',
                    'energy':                   'no',
                    'cpu_freq':                 '',
                    'gpu_freq':                 '',
                    'no_state_check':           'yes',
                    'skip_print_timers':        'yes',

                    'tags':                     ','.join(['qck', 'quantum', hackathon_tag, competition_tag]),
                    'meta': {
                        'team':             team_name,
                        'hackathon':        hackathon_tag,
                        'competition':      competition_tag,
                    },
                    'record':                   'yes',
                    'record_repo':              hackathon_local_repo,
                    'record_uoa':               experiment_name,
    })
    if r['return']>0: return r

    record_cid  = '{}:experiment:{}'.format(hackathon_local_repo, experiment_name)
    ck.out('The results have been recorded into {}\n'.format(record_cid))

    return r


def list_experiments(i):
    """
    Input:  {
                (repo_uoa)          - experiment repository name (defaults to '*')
                (extra_tags)        - extra tags to filter
                (add_meta)          - request to return metadata with each experiment entry
            }

    Output: {
                return              - return code =  0, if successful
                                                  >  0, if error
                (error)             - error text if return > 0
            }
    """

    repo_uoa        = i.get('repo_uoa', '*')
    extra_tags      = i.get('extra_tags')
    all_tags        = 'qck,' + hackathon_tag + ( ',' + extra_tags if extra_tags else '' )
    add_meta        = i.get('add_meta')

    search_adict    = { 'action':       'search',
                        'repo_uoa':     repo_uoa,
                        'module_uoa':   'experiment',
                        'data_uoa':     '*',
                        'tags':         all_tags,
                        'add_meta':     add_meta,
    }
    r=ck.access( search_adict )
    if r['return']>0: return r

    list_of_experiments = r['lst']

    repo_to_names_list = {}
    for entry in list_of_experiments:
        repo_uoa    = entry['repo_uoa']
        data_uoa    = entry['data_uoa']
        if not repo_uoa in repo_to_names_list:
            repo_to_names_list[ repo_uoa ] = []
        repo_to_names_list[ repo_uoa ] += [ data_uoa ]

    if i.get('out')=='con':
        for repo_uoa in repo_to_names_list:
            experiments_this_repo = repo_to_names_list[ repo_uoa ]
            ck.out( '{} ({}) :'.format(repo_uoa, len(experiments_this_repo) ) )
            for data_uoa in experiments_this_repo:
                ck.out( '\t' + data_uoa )
            ck.out( '' )

    return {'return':0, 'lst': list_of_experiments, 'repo_to_names_list': repo_to_names_list}


def pick_an_experiment(i):
    """
    Input:  {
                (repo_uoa)          - experiment repository name (defaults to hackathon_local_repo, but can be overridden by '*')
                (extra_tags)        - extra tags to filter
            }

    Output: {
                return              - return code =  0, if successful
                                                  >  0, if error
                (error)             - error text if return > 0
            }
    """

    repo_uoa        = i.get('repo_uoa', hackathon_local_repo)
    extra_tags      = i.get('extra_tags')

    list_exp_adict  = { 'action':       'list_experiments',
                        'module_uoa':   work['self_module_uoa'],
                        'repo_uoa':     repo_uoa,
                        'extra_tags':   extra_tags,
    }
    r=ck.access( list_exp_adict )
    if r['return']>0: return r

    if len(r['lst'])==0:
        return {'return':1, 'error':'No experiments to choose from - please relax your filters'}

    all_experiment_names = [ '{repo_uoa}:{module_uoa}:{data_uoa}'.format(**entry_dict) for entry_dict in r['lst']]

    number_of_experiments = len(all_experiment_names)
    select_adict = {'action': 'select_string',
                    'module_uoa': 'misc',
                    'options': all_experiment_names,
                    'default': str(number_of_experiments-1),
                    'question': 'Please select the experiment entry',
    }
    r=ck.access( select_adict )
    if r['return']>0:
        return r
    else:
        cid = r['selected_value']

    return {'return':0, 'cid': cid}


def upload(i):
    """
    Input:  {
                (cids[])            - CIDs of entries to upload (interactive by default)
                OR
                (repo_uoa)          - experiment repository name (defaults to hackathon_local_repo, but can be overridden by '*')
                (extra_tags)        - extra tags to filter
            }

    Output: {
                return              - return code =  0, if successful
                                                  >  0, if error
                (error)             - error text if return > 0
            }
    """

    cids                = i.get('cids')

    if len(cids)==0:
        repo_uoa        = i.get('repo_uoa', hackathon_local_repo)
        extra_tags      = i.get('extra_tags')

        pick_exp_adict  = { 'action':       'pick_an_experiment',
                            'module_uoa':   work['self_module_uoa'],
                            'repo_uoa':     repo_uoa,
                            'extra_tags':   extra_tags,
        }
        r=ck.access( pick_exp_adict )
        if r['return']>0: return r
        cids = [ r['cid'] ]

    target_server_uoa = 'remote-ck'
    transfer_adict = {  'action':               'transfer',
                        'module_uoa':           'misc',
                        'cids':                 cids,                       # 'ck transfer' will perform its own cids->xcids parsing
                        'target_server_uoa':    target_server_uoa,
                        'target_repo_uoa':      hackathon_remote_repo,
    }
    r=ck.access( transfer_adict )
    if r['return']>0: return r

    ck.out('The entries {} have been uploaded to {}/{}'.format(cids, target_server_uoa, hackathon_remote_repo))
    return {'return': 0}

