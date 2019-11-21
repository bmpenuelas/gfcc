import os
import re
import subprocess
import json
import readline

from   os       import getcwd, walk, remove, chdir
from   os.path  import abspath, join, isdir, relpath, dirname, split, exists
from   shutil   import rmtree, copyfile
from   pathlib  import Path
from   datetime import datetime


# Constants
INDENTATION = '  '
TEMPORARY_FILE_EXTENSIONS = ('~', '.contrib', '.keep', '.bak', '.swp', '.mkelem')
DEFAULT_CS = [
    'element * CHECKEDOUT',
    'element * /main/LATEST',
]


def run_cmd(cmd, get_lines=False, background=False):
    ''' Run a command in the shell and return the output '''

    is_shell = not isinstance(cmd, (list, tuple))
    if background:
        return subprocess.Popen(cmd, shell=is_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=is_shell)
        decoded_out = result.stdout.decode('utf-8')
        decoded_err = result.stderr.decode('utf-8')
        return (decoded_out, decoded_err) if not get_lines else (decoded_out.split('\n'), decoded_err.split('\n'))


def exists_try(filepath):
    ''' Alternative exists() for some clearcase files not being identified '''

    if exists(filepath):
        return True
    try:
        with open(filepath) as f:
            if f:
                return True
    except FileNotFoundError:
        pass
    return False


def rm(to_remove, r=False):
    ''' Remove files/dirs '''

    if isinstance(to_remove, (list, tuple)):
        return [rm(file_i) for file_i in to_remove]
    else:
        if exists(to_remove):
            if isdir(to_remove):
                rmtree(to_remove)
            else:
                remove(to_remove)
        return True


def difftool(file_a, file_b, background=False):
    ''' Open a diff in difftool set by env variable '''

    if not os.environ['DIFFTOOL']:
        print_indent('Error: environment variable DIFFTOOL is not set. Set it to your preferred diff tool, for example: setenv DIFFTOOL meld', 0)
        return False
    return run_cmd([os.environ['DIFFTOOL'], file_a, file_b], background=background)


def diff_text(file_a, file_b):
    ''' Return diffs between two files as text lines '''

    return run_cmd('diff ' + file_a + ' ' + file_b, get_lines=True)[0]


def send_mail(subject, body, send_to):
    ''' Send an email using the linux program sendmail '''

    header = [
        'MIME-Version: 1.0',
        'Content-Type: text/html',
        'Content-Disposition: inline',
        '<html>',
        '<body>',
    ]
    footer = [
        '</body>',
        '</html>',
    ]
    if isinstance(send_to, (list, tuple)):
        send_to = ','.join(send_to)
    email_lines = ['To: ' + send_to, 'Subject: ' + subject] + header + body + footer
    temp_file = abspath(join('.', 'cs_mail'))
    write_to_file(email_lines, temp_file)
    send_mail_command = 'sendmail -t < ' + temp_file
    send_mail_process = subprocess.Popen(send_mail_command, shell=True)
    send_mail_process.wait()
    remove(temp_file)


def print_indent(text, indent=0):
    ''' Print with the provided level of indentation '''

    if isinstance(text, (tuple, list)):
        return [print_indent(element, indent) for element in text]
    else:
        return print(indent * INDENTATION + text)


def print_rule(item, rule, indent=0):

    ''' Print a clearcase cs rule '''

    print_indent('element ' + abspath(item) + ' ' + rule, indent)


def get_date_string():

    ''' Current date as string '''

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def range_str_to_list(range_str):

    ''' Take a string like '1,2,5-7,10' and turn it into [1, 2, 5, 6, 7, 10] '''

    return sum(((list(range(*[int(j) + k for k,j in enumerate(i.split('-'))]))
         if '-' in i else [int(i)]) for i in range_str.split(',')), [])


def choose_options(options, indent=0, choose_message='Choice: '):

    ''' Show a list of options and return the chosen index '''

    for (index, option) in enumerate(options):
        print_indent('[' + str(index) + '] ' + option, indent)
    selection = None
    while not selection:
        selection = input(indent * INDENTATION + choose_message)
    return(selection)


def to_abs_path(rel_path):

    ''' Shorthand for list of paths to abspath '''

    if isinstance(rel_path, (list, tuple)):
        return [to_abs_path(element) for element in rel_path]
    else:
        return abspath(rel_path)


def to_rel_path(abs_path, from_path=None):

    ''' Shorthand for list of paths to relpath '''

    if isinstance(abs_path, (list, tuple)):
        return [to_rel_path(element, from_path) for element in abs_path]
    else:
        return relpath(abs_path, from_path or getcwd())


def regex_match(expression, text):

    ''' Shorthand for getting regex matching groups '''

    search_result = re.match(expression, text)
    if search_result:
        return search_result.groupdict()


def get_gfcc_config_from_cs(cs_filename=None, view=False):

    ''' A JSON can be included in the cs comments as gfcc_config={...} '''

    cs_text_lines = get_cs_text(cs_filename, view)
    cfg_string = ''
    for line in cs_text_lines:
        cfg_match = re.match(r'#+\s*gfcc_config\s*=\s*(\{.*)', line)
        comment_match = re.match(r'#+(.*)', line)
        if cfg_string:
            if comment_match:
                cfg_string += comment_match.group(1)
            else:
                break
        elif cfg_match:
            cfg_string = cfg_match.group(1)
    gfcc_config = json.loads(cfg_string)
    return gfcc_config


def list_checked_out(directory=None, absolute=False):

    ''' Take the whole view/directory and returns abs/rel paths of the files '''

    clearcase_cmd_list_checked_out = ['cleartool', 'lsco', '-cview', '-a', '-s']
    output = run_cmd(clearcase_cmd_list_checked_out, True)[0]
    if not directory:
        result = [item for item in output if item]
    else:
        directory = abspath(directory)
        result = [(relpath(item, getcwd()) if not absolute else item) for item in output
                  if item and item.startswith(directory)]
    return result


def find_modifications(to_check, gui=False):

    ''' Take one or a list of abs or rel paths and return the differences reported by cleartool '''

    if isinstance(to_check, (list, tuple)):
        return list(filter(lambda x: x, [find_modifications(file_i, gui) for file_i in to_check]))
    else:
        clearcase_cmd_find_modifications = ['cleartool', 'diff']  + (['-graphical'] if gui else []) + ['-predecessor', to_check]
        if gui:
            output = run_cmd(clearcase_cmd_find_modifications, background=True)
        else:
            output = run_cmd(clearcase_cmd_find_modifications)[0]
            modified = not 'identical' in output
            return output if modified else None


def filename_from_diff(modification):

    '''Get the filename from a diff with predecessor'''

    if not modification:
        return None
    file2 = re.search(r'(file|directory) 2:\s(.+)\s', modification)
    return file2.group(2) if file2 else None


def list_untracked(directory):

    '''List non-versioned files'''

    directory = directory or '.'
    clearcase_cmd_find_untracked = ['cleartool', 'ls', '-rec', '-view_only', directory]
    result = run_cmd(clearcase_cmd_find_untracked, True)
    directory = None if abspath(directory) == getcwd() else relpath(abspath(directory), getcwd())
    return list(filter(
        lambda x: x and ('Rule' not in x) and (not directory or x.startswith(directory) or x.startswith('./' + directory)),
        result[0]
    ))


def cc_lshist(item, lines=15, recursive=False, gui=False):

    '''ClearCase list history'''

    clearcase_cmd_lshist = ['cleartool', 'lshistory'] \
        + (['-recurse'] if recursive else []) \
        + (['-graphical'] if gui else ['-last', str(lines)]) \
        + [item]
    result = run_cmd(clearcase_cmd_lshist, True, gui)
    if gui:
        return result
    else:
        return result[0]

def cc_xlsvtree(item):

    '''ClearCase open tree'''

    clearcase_cmd_xlsvtree = ['xclearcase', '-vtree', item]
    return run_cmd(clearcase_cmd_xlsvtree, False, True)


def cc_get_selected(item):

    '''ClearCase get items selected by current cs rules'''

    if isinstance(item, (list, tuple)):
        return [cc_get_selected(element) for element in item]
    else:
        clearcase_cmd_get_v_rule = ['cleartool', 'ls', item]
        result = run_cmd(clearcase_cmd_get_v_rule, True)
        return regex_match(r'^(?P<cc_path>.*?)\s', result[0][0])['cc_path']


def start_view(view):

    ''' Makes a view available in /view/... '''

    cmd = 'cleartool startview ' + view
    result = run_cmd(cmd, True)
    if result[1]:
        print_indent(result[1])
    return result


def cc_checkout(to_cc, verbose_indent=1):

    '''ClearCase checkout wrapper'''

    if isinstance(to_cc, (list, tuple)):
        return [cc_checkout(element, verbose_indent) for element in to_cc]
    else:
        clearcase_cmd_checkout = ['cleartool', 'co', '-unr', '-nc', '-version', to_cc]
        result = run_cmd(clearcase_cmd_checkout, True)
        if verbose_indent:
            print_indent('Checked out: ' + to_cc, verbose_indent)
        return result


def copy_co(item, view):

    ''' Copy a checked-out file into a checked-out in the current view '''

    item_path = abspath(item)
    cc_checkout(item_path)
    start_view(view)
    copyfile('/view/' + view + item_path, item_path)
    print_indent('Copied ' + item + ' from ' + view, 1)


def cc_checkin(to_cc, message, identical=False, verbose_indent=1):

    ''' ClearCase checkin wrapper '''

    if isinstance(to_cc, (list, tuple)):
        return [cc_checkin(element, message, identical, verbose_indent) for element in to_cc]
    else:
        clearcase_cmd_checkin = ['cleartool', 'ci', '-c', message] + (['-identical'] if identical else []) + [to_cc]
        result = run_cmd(clearcase_cmd_checkin, True)
        if verbose_indent:
            search_version = re.search(r'^.*?version "(?P<version>.*?)"', result[0][0])
            if search_version and search_version.group('version'):
                print_indent('Checked in: ' + to_cc, verbose_indent)
                print_indent('Add the following rule to your cs to select this version:', verbose_indent + 1)
                print_indent('element ' + to_cc + ' ' + search_version.group('version'), verbose_indent + 1)
            else:
                print_indent('Error checking-in: ' + to_cc, verbose_indent)
        return result


def cc_uncheckout(to_cc, keep, verbose_indent=1):

    ''' ClearCase uncheckout wrapper '''

    if isinstance(to_cc, (list, tuple)):
        return [cc_uncheckout(element, keep, verbose_indent) for element in to_cc]
    else:
        if verbose_indent:
            print_indent('Uncheckout: ' + to_cc, verbose_indent)
        clearcase_cmd_uncheckout = ['cleartool', 'unco', '-keep' if keep else '-rm']
        result = run_cmd(clearcase_cmd_uncheckout + [to_cc], True)
        return result


def cc_mkelem(to_cc, message, verbose_indent=1):

    ''' ClearCase make element wrapper '''

    if isinstance(to_cc, (list, tuple)):
        return [cc_mkelem(element, message) for element in to_cc]
    else:
        cc_checkout(dirname(abspath(to_cc)))
        clearcase_cmd_mkelem = ['cleartool', 'mkelem', '-c', message, '-ci', ('-mkpath' if isdir(to_cc) else ''), to_cc]
        mk_result = run_cmd(clearcase_cmd_mkelem, True)
        if verbose_indent:
            print_indent('Create and Checkin: ' + to_cc, verbose_indent)
            search_version = re.search(r'^.*?version "(?P<version>.*?)"', mk_result[0][0])
            if search_version and search_version.group('version'):
                print_indent('Add the following rule to your cs to select this version:', verbose_indent + 1)
                print_indent('element ' + to_cc + ' ' + search_version.group('version'), verbose_indent + 1)
            print_indent('Checking-in updated containing directory', verbose_indent)
        cc_checkin(dirname(abspath(to_cc)), 'Added file ' + to_cc, verbose_indent=verbose_indent)
        return mk_result


def cc_checkx(select, recursive, selected_item, untracked=False, **kwargs):

    ''' Abstraction of all the ClearCase check-x operations '''

    config = {
        'out': {
            'succes_str': 'checked out',
            'fn': cc_checkout,
            'parameters': []
        },
        'in': {
            'succes_str': 'checked in',
            'fn': cc_checkin,
            'parameters': ['message', 'identical']
        },
        'un': {
            'succes_str': 'checkout cancelled',
            'fn': cc_uncheckout,
            'parameters': ['keep']
        },
        'mk': {
            'succes_str': 'created element',
            'fn': cc_mkelem,
            'parameters': ['message']
        },
        'reserved_str': 'is checked out reserved',
        'not_in_cc_str': 'not an element',
    }

    arguments = {name: kwargs[name] for name in config[select]['parameters']}

    file_list = []
    single_item = True
    if recursive and selected_item and isdir(selected_item):
        for root, _, files in walk(selected_item):
            file_list.extend([root] + [join(root, file_i) for file_i in files])
        single_item = False
    else:
        file_list = [selected_item]

    modified_files, untracked_files, _ = get_status(get_modified=True, get_untracked=True,item=selected_item)
    untracked_filtered = [f for f in untracked_files if not f.endswith(TEMPORARY_FILE_EXTENSIONS)]

    success = {file_i:{select: False} for file_i in file_list}
    for file_i in file_list:
        process_file = False
        if select == 'in':
            if single_item or arguments['identical']:
                process_file = True
            elif (file_i in modified_files + (untracked_filtered if untracked else [])):
                process_file = True
        else:
            process_file = True

        if process_file:
            result = config[select]['fn'](file_i, **arguments)
            if any([(config[select]['succes_str'] in line.lower()) for line in result[0]]):
                success[file_i] = {select: True}
            elif any([(config['reserved_str'] in line.lower()) for line in result[1]]):
                print_indent('Error File is reserved: ' + file_i, 1)
            elif any([(config['not_in_cc_str'] in line.lower()) for line in result[1]]) and select == 'in':
                mk_arguments = {name: kwargs[name] for name in config['mk']['parameters']}
                mk_result = config['mk']['fn'](file_i, **mk_arguments)
                if any([(config['mk']['succes_str'] in line.lower()) for line in mk_result[0]]):
                    success[file_i] = {'mk': True}
                else:
                    print_indent(mk_result[0] + mk_result[1], 1)
            elif single_item:
                print_indent('Ignored: ' + file_i, 1)
            else:
                if False: # Use for debug cc_checkx
                    print_indent('Unexpected result for ' + file_i, 1)
                    print_indent(result, 1)


def get_status(get_modified=False, get_untracked=False, get_checkedout_unmodified=False,
               item=None, whole_view=False):

    ''' Collect checked-out, modified, untracked if requested '''

    directory = item if (item and isdir(item)) else (None if whole_view else getcwd())
    checked_out_files = list_checked_out(directory)
    modifications = find_modifications(checked_out_files)

    modified_files = [filename_from_diff(changed) for changed in modifications] if get_modified else []
    untracked_files = list_untracked(directory) if get_untracked else []
    checked_out_unmodified = list(set(checked_out_files) - set(modified_files)) if get_checkedout_unmodified else []

    return (to_abs_path(modified_files), to_abs_path(untracked_files), to_abs_path(checked_out_unmodified))


def get_working_view_name():

    " Get current view name as string "

    result_pwv = run_cmd('cleartool pwv', get_lines=True)
    if not any(['Set view: ** NONE **' in line for line in result_pwv[0]]):
        search_view = re.search(r'^Set view: (?P<view>.*?)$', result_pwv[0][1])
        if search_view:
            return search_view.group('view')
    return None


def get_cs_text(cs_filename=None, view=False):

    " Get currently applied CS as list of lines "

    if view and cs_filename:
        result_provided_name = run_cmd('cleartool catcs -tag ' + cs_filename, get_lines=True)
        if not any(['Error: View tag' in line for line in result_provided_name[1]]):
            return result_provided_name[0]
        elif 'USER' in os.environ:
            result_user_name = run_cmd('cleartool catcs -tag ' + os.environ['USER'] + '_' + cs_filename, get_lines=True)
            if not any(['Error: View tag' in line for line in result_user_name[1]]):
                return result_user_name[0]
        print_indent('Error getting cs ' + cs_filename, 0)
        return False

    elif cs_filename:
        return [line.rstrip() for line in open(cs_filename)]
    else:
        return run_cmd('cleartool catcs', get_lines=True)[0]


def get_file_versions(cs_filename=None, view=False, file_path='', get_latest=False):

    ''' Get the files selected by a given configspec file and their versions '''

    cs_file_current = get_cs_text()
    if cs_filename:
        cs_file_new = get_cs_text(cs_filename, view)
        if cs_file_new:
            set_cs(cs_file_new)
        else:
            return None, None

    if get_latest:
        cmd = 'cleartool find . -version "{version(main/LATEST) && ! lbtype(find)}" -print'
    else:
        cmd = 'cleartool ls -r ' + file_path

    result = run_cmd(cmd, get_lines=True)[0]
    cs_files = {}
    for item in result:
        matched = re.search(r'^(.*from\s)?(?P<filename>.*?)(@@(?P<version>.*?))?\s*(Rule: (?P<rule>.*?))?$', item)
        if matched:
            if matched.group('filename'):
                cs_files[matched.group('filename')] = {'version': '', 'rule': ''}
                if matched.group('version'):
                    cs_files[matched.group('filename')]['version'] = matched.group('version')
                if matched.group('rule'):
                    cs_files[matched.group('filename')]['rule'] = matched.group('rule')

    if cs_filename:
        set_cs(cs_file_current)
    return cs_files, cs_file_new if cs_filename else cs_file_current


def get_single_file_version(file_path):

    ''' Get the /branch/version of a single file '''

    return list(get_file_versions(file_path=file_path)[0].values())[0]['version']


def is_checked_out(file_path):
    ''' Check whether a single file is checked out '''
    print(list(get_file_versions(file_path=file_path)[0].values())[0]['rule'])

    return list(get_file_versions(file_path=file_path)[0].values())[0]['rule'] == 'CHECKEDOUT'


def get_version_no(curr_version):

    ''' Get the number corresponding to a file branch/version_no '''

    return int(regex_match(r'^.*\/(?P<version_no>\d+)', curr_version)['version_no'])


def change_version_no(current, new_version_no):

    ''' Change the number only in file@@branch/version_no '''

    version = regex_match(r'^(?P<branch>.*\/)(?P<no>\d+)', current)
    return version['branch'] + str(new_version_no)


def write_to_file(line_list, path):

    ''' Create a file with the provided lines '''

    with open(path, 'w+') as destination_file:
        file_lines = [line.rstrip() + '\n' for line in line_list]
        while not file_lines[-2].rstrip():
            file_lines.pop()
        destination_file.writelines(file_lines)


def set_cs(new_cs):

    ''' Set the current cs to the provided file or list of lines '''

    if isinstance(new_cs, (list, tuple)):
        write_to_file(new_cs, 'temp.cs')
        new_cs = 'temp.cs'
    result = run_cmd('cleartool setcs ' +  new_cs)
    if new_cs == 'temp.cs':
        remove(new_cs)
    return result


def diff_cs_versions(csfile_a, csfile_b, view=False, diff_files=False):

    ''' Find which files and versions selected by two cs differ '''

    cs_a = get_file_versions(csfile_a, view=view)
    cs_b = get_file_versions(csfile_b)
    if cs_a[0] and cs_b[0]:
        if diff_files:
            filename_a = csfile_a
            filename_b = (csfile_b or 'CURRENT')
            created_a = False
            created_b = False
            if not exists_try(filename_a):
                created_a = True
                write_to_file(cs_a[1], filename_a)
            if not exists_try(filename_b):
                created_b = True
                write_to_file(cs_b[1], filename_b)
            difftool(abspath(filename_a), abspath(filename_b))
            if created_a:
                remove(filename_a)
            if created_b:
                remove(filename_b)
            return cs_a, cs_b, None, None, None
        else:
            return (cs_a, cs_b) + versions_diff(cs_a[0], cs_b[0])
    else:
        return None, None, None, None, None



def versions_diff(cs_files_a, cs_files_b):

    ''' Find differences in selected files sets '''

    set_a = set(cs_files_a.keys())
    set_b = set(cs_files_b.keys())

    files_a_not_b = set_a - set_b
    files_b_not_a = set_b - set_a

    different_versions = {
        filename: [
            {'version': cs_files_a[filename]['version'], 'rule': cs_files_a[filename]['rule']},
            {'version': cs_files_b[filename]['version'], 'rule': cs_files_b[filename]['rule']}
        ]
        for filename in cs_files_a.keys()
        if filename in cs_files_b and cs_files_a[filename]['version'] != cs_files_b[filename]['version']
    }
    return list(files_a_not_b), list(files_b_not_a), different_versions


def diffcs(csfile_a, csfile_b, view=None, diff_files=False, dir_path=None, gen_rules=False, review_diffs=False):

    ''' Find different versions selected by two cs files '''

    if dir_path:
        chdir(dir_path)
    cs_a, cs_b, a_not_b, b_not_a, diff_v = diff_cs_versions(csfile_a, csfile_b, bool(view), diff_files)

    if not diff_files and (cs_a and cs_b):
        if not any([a_not_b, b_not_a, diff_v]):
            print_indent('Identical: Both CS files select the same files and versions.', 1)
        else:
            print_indent('Files selected by ' + (csfile_b or 'CURRENT') + ' and NOT by ' + relpath(csfile_a)  + ':', 1)
            if not b_not_a:
                print_indent('None.', 2)
            else:
                for item in sort_paths(b_not_a):
                    if gen_rules:
                        print_indent(('element ' + abspath(item) + ' ' + cs_b[0][item]['rule']) if cs_b[0][item]['rule']
                            else ('* ' + relpath(item) + ' has NO rule in ' + (csfile_b or 'CURRENT')), 2)
                    else:
                        print_indent(relpath(item) + '   (Rule ' + (cs_b[0][item]['rule'] or 'NONE') + ')', 2)

            print_indent('Files selected by ' + relpath(csfile_a) + ' and NOT by ' + (csfile_b or 'CURRENT') + ':', 1)
            if not a_not_b:
                print_indent('None.', 2)
            else:
                for item in sort_paths(a_not_b):
                    if gen_rules:
                        print_indent(('element ' + abspath(item) + ' ' + cs_a[0][item]['rule']) if cs_a[0][item]['rule']
                            else ('* ' + relpath(item) + ' has NO rule in ' + csfile_a), 2)
                    else:
                        print_indent(relpath(item) + '   (Rule ' + (cs_a[0][item]['rule'] or 'NONE') + ')', 2)

            print_indent('Files with different versions in ' + (csfile_b or 'CURRENT') + ' vs ' + relpath(csfile_a) + ':', 1)
            if not diff_v:
                print_indent('None.', 2)
            else:
                different_items = sort_paths(diff_v.keys())
                different_items_diff = {
                    abspath(item): {
                        'print': \
                            relpath(item) \
                            + '   ' + diff_v[item][1]['version'] + ' vs ' + diff_v[item][0]['version'] \
                            + '   (Rule ' + (diff_v[item][1]['rule'] or 'NONE') \
                            + ' vs ' + (diff_v[item][0]['rule'] or 'NONE') + ')',
                        'old': item + '@@' + diff_v[item][0]['version'],
                        'new': item + '@@' + diff_v[item][1]['version'],
                    }
                    for item in different_items
                }
                different_items_prints = [different_items_diff[abspath(item)]['print'] for item in different_items]

                if review_diffs:
                    print_indent('(Select which ones you want to review, you can provide a range like 1,2,5-7,10)', 1)
                    choices = ['ALL'] + different_items_prints + ['EXIT']
                    choices_indentation = 2
                    choice = choose_options(choices, choices_indentation)
                    choice = range_str_to_list(choice)
                    if len(choice) == 1 and choice[0] == 0:
                        to_difftool = [abspath(item) for item in different_items]
                    elif len(choice) == 1 and choice[0] > len(different_items):
                        return
                    else:
                        to_difftool = [abspath(different_items[index-1]) for index in choice]
                    for diff_i in to_difftool:
                        difftool(different_items_diff[diff_i]['old'], different_items_diff[diff_i]['new'], background=True)

                else:
                    if gen_rules:
                        for item in different_items:
                            print_indent(('element ' + abspath(item) + ' ' + cs_a[0][item]['rule']) if cs_a[0][item]['rule']
                                else ('* ' + relpath(item) + ' has NO rule in ' + csfile_a), 2)
                    else:
                        print_indent(different_items_prints, 2)

        if csfile_b == None:
            modified_files, _, _ = get_status(
                get_modified=True, item=dir_path
            )
            if modified_files:
                print_indent('Warning: The following changes are local, only visible in your view.', 1)
                print_indent('Modified files:', 2)
                print_indent((modified_files or ['None.']), 3)


def sort_paths(path_list):

    ''' Sort paths in lexicographical order '''

    sorted_paths = sorted([[filepath, Path(filepath)] for filepath in path_list], key = lambda x: x[1])
    return [str(i[0]) for i in sorted_paths]


def get_block_name_path(blockname=None):

    ''' Attempt to guess the current block path '''

    if not ('PROJVOB' in os.environ):
        return None, None
    src_path = join((os.environ['PROJVOB']), 'src')
    if not blockname:
        cwd = abspath(getcwd())
        if cwd.startswith(src_path):
            blockname = regex_match(r'^(\/|\\)?(?P<blockname>\w+)(\/|\\)?', cwd[len(src_path):])['blockname']
    if blockname:
        return blockname, join(src_path, blockname)
    else:
        return None, None


def find_save_cs_dir(blockname=None, user=False, code_review=False):

    ''' Get the path to the directory where a given cs file should be stored '''

    block_path = get_block_name_path(blockname)[1]
    if not block_path:
        print_indent(
            'Unable to find block name automatically. Try running from inside the block file-tree or provide --block or --absolute-path.', 0)
        return None

    needed_paths = [join(block_path, 'cs')]
    if user:
        needed_paths.append(join(needed_paths[0], 'user'))
    if code_review:
        needed_paths.append(join(needed_paths[0], 'code_review'))
    current_cs = get_cs_text()
    set_cs(DEFAULT_CS)
    for cs_path in needed_paths:
        if not exists_try(cs_path):
            print_indent('Creating ' + cs_path, 1)
            os.mkdir(cs_path)
            cc_checkx('in', recursive=False, selected_item=cs_path, message='Create directory to store CS files.', identical=False, untracked=True)
    set_cs(current_cs)

    if code_review:
        return needed_paths[-1]
    elif user:
        return needed_paths[1]
    else:
        return needed_paths[0]


def get_cs_path(block=None, cs_file_name=None):

    ''' Guess the full path were a given cs can be found '''

    is_user = not cs_file_name
    save_cs_dir = find_save_cs_dir(block, is_user)
    if not save_cs_dir:
        return None
    save_cs_file_name = (cs_file_name or get_working_view_name())
    return join(save_cs_dir, save_cs_file_name)


def guess_cs_file(block, view, cs_file):

    ''' Given a name, try to guess where it would be stored and the full file path '''

    guessed_csfile = None
    if view and cs_file:
        print_indent('Error: provide view or cs-file to diff against, not both.', 0)
        return None
    if view:
        guessed_csfile = view
    elif cs_file:
        guessed_path = get_cs_path(block, cs_file)
        if not block and exists_try(abspath(cs_file)):
            guessed_csfile = abspath(cs_file)
        elif guessed_path and exists_try(guessed_path):
            guessed_csfile = guessed_path
    else:
        guessed_path = get_cs_path(block)
        if guessed_path and exists_try(guessed_path):
            guessed_csfile = guessed_path
    return guessed_csfile
