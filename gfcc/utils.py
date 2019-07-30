import os
import re
import subprocess

from   os       import getcwd, walk, remove
from   os.path  import abspath, join, isdir, relpath, dirname, split, exists
from   pathlib  import Path
from   datetime import datetime


# Constants
INDENTATION = '  '
TEMPORARY_FILE_EXTENSIONS = ('~', '.contrib', '.keep')
DEFAULT_CS = [
    'element * CHECKEDOUT',
    'element * /main/LATEST',
]


def run_cmd_command(cmd, get_lines=False, background=False):
    ''' Run a command in the shell and return the output. '''
    cmd = cmd.split(' ') if not isinstance(cmd, list) else cmd
    if background:
        return subprocess.Popen(cmd)
    else:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        decoded_out = result.stdout.decode('utf-8')
        decoded_err = result.stderr.decode('utf-8')
        return (decoded_out, decoded_err) if not get_lines else (decoded_out.split('\n'), decoded_err.split('\n'))


def rm(files, r=False):
    if isinstance(files, list):
        return [rm(file_i) for file_i in files]
    else:
        clearcase_cmd_rm = ['rm', '-' + ('r' if r and isdir(files) else '') + 'f', abspath(files)]
        return run_cmd_command(clearcase_cmd_rm)


def print_indent(text, indent):
    if not isinstance(text, list):
        text = [text]
    for element in text:
        print(indent * INDENTATION + element)


def get_date_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def to_abs_path(rel_path):
    if isinstance(rel_path, list):
        return [to_abs_path(element) for element in rel_path]
    else:
        return abspath(rel_path)

def to_rel_path(abs_path, from_path=None):
    if isinstance(abs_path, list):
        return [to_rel_path(element, from_path) for element in abs_path]
    else:
        return relpath(abs_path, from_path or getcwd())


def search_regex(expression, text, groups):
    search_result = re.search(expression, text)
    result = {group_i: None for group_i in groups}
    if search_result:
        for group_i in groups:
            result[group_i] = search_result.group(group_i)
    return result


def list_checked_out(directory=None, absolute=False):
    ''' List checked out takes the whole view/directory and returns abs/rel paths of the files. '''
    clearcase_cmd_list_checked_out = ['cleartool', 'lsco', '-cview', '-a', '-s']
    output = run_cmd_command(clearcase_cmd_list_checked_out, True)[0]
    if not directory:
        result = [item for item in output if item]
    else:
        directory = abspath(directory)
        result = [(relpath(item, getcwd()) if not absolute else item) for item in output
                  if item and item.startswith(directory)]
    return result


def find_modifications(to_check, gui=False):
    ''' Take one or a list of abs or rel paths and return the differences reported by cleartool. '''
    if isinstance(to_check, list):
        return list(filter(lambda x: x, [find_modifications(file_i, gui) for file_i in to_check]))
    else:
        clearcase_cmd_find_modifications = ['cleartool', 'diff']  + (['-graphical'] if gui else []) + ['-predecessor', to_check]
        if gui:
            output = run_cmd_command(clearcase_cmd_find_modifications, background=True)
        else:
            output = run_cmd_command(clearcase_cmd_find_modifications)[0]
            modified = not 'identical' in output
            return output if modified else None


def filename_from_diff(modification):
    ''' Get the filename from a diff with predecessor. '''
    if not modification:
        return None
    file2 = re.search(r'(file|directory) 2:\s(.+)\s', modification)
    return file2.group(2) if file2 else None


def list_untracked(directory):
    ''' Works with relative paths by default due to the cleartool command. '''
    clearcase_cmd_find_untracked = ['cleartool', 'ls', '-rec', '-view_only']
    output = run_cmd_command(clearcase_cmd_find_untracked, True)[0]
    if directory:
        directory = None if abspath(directory) == getcwd() else relpath(abspath(directory), getcwd())
    return list(filter(
        lambda x: x and ('Rule' not in x) and (not directory or x.startswith(directory) or x.startswith('./' + directory)),
        output
    ))


def cc_lshist(item, lines=15, recursive=False, gui=False):
    clearcase_cmd_lshist = ['cleartool', 'lshistory'] \
        + (['-recurse'] if recursive else []) \
        + (['-graphical'] if gui else ['-last', str(lines)]) \
        + [item]
    result = run_cmd_command(clearcase_cmd_lshist, True, gui)
    if gui:
        return result
    else:
        return result[0]

def cc_xlsvtree(item):
    clearcase_cmd_xlsvtree = ['xclearcase', '-vtree', item]
    return run_cmd_command(clearcase_cmd_xlsvtree, False, True)


def cc_checkout(to_cc):
    if isinstance(to_cc, list):
        return [cc_checkout(element) for element in to_cc]
    else:
        clearcase_cmd_checkout = ['cleartool', 'co', '-unr', '-nc']
        return run_cmd_command(clearcase_cmd_checkout + [to_cc], True)


def cc_checkin(to_cc, message, identical=False):
    if isinstance(to_cc, list):
        return [cc_checkin(element, message, identical) for element in to_cc]
    else:
        clearcase_cmd_checkin = ['cleartool', 'ci', '-c', message, ('-identical' if identical else '')]
        return run_cmd_command(clearcase_cmd_checkin + [to_cc], True)


def cc_uncheckout(to_cc, keep):
    if isinstance(to_cc, list):
        return [cc_uncheckout(element, keep) for element in to_cc]
    else:
        clearcase_cmd_uncheckout = ['cleartool', 'unco', '-keep' if keep else '-rm']
        return run_cmd_command(clearcase_cmd_uncheckout + [to_cc], True)


def cc_mkelem(to_cc, message):
    if isinstance(to_cc, list):
        return [cc_mkelem(element, message) for element in to_cc]
    else:
        cc_checkout(dirname(abspath(to_cc)))
        clearcase_cmd_mkelem = ['cleartool', 'mkelem', '-c', message, '-ci', ('-mkpath' if isdir(to_cc) else ''), to_cc]
        mk_result = run_cmd_command(clearcase_cmd_mkelem, True)
        cc_checkin(dirname(abspath(to_cc)), 'Added file ' + to_cc)
        return mk_result


def cc_checkx(select, recursive, selected_item, untracked=False, **kwargs):
    config = {
        'out': {
            'succes_str': 'checked out',
            'succes_print': 'Checked out: ',
            'fn': cc_checkout,
            'parameters': []
        },
        'in': {
            'succes_str': 'checked in',
            'succes_print': 'Checked in: ',
            'fn': cc_checkin,
            'parameters': ['message', 'identical']
        },
        'un': {
            'succes_str': 'checkout cancelled',
            'succes_print': 'Uncheckedout: ',
            'fn': cc_uncheckout,
            'parameters': ['keep']
        },
        'mk': {
            'succes_str': 'created element',
            'succes_print': 'Created and Checked in: ',
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
    for file_i in file_list:
        if (select == 'in' and (file_i in modified_files + (untracked_filtered if (untracked or single_item) else []) or arguments['identical'])) \
        or (select != 'in'):
            result = config[select]['fn'](file_i, **arguments)
            if any([(config[select]['succes_str'] in line.lower()) for line in result[0]]):
                print_indent(config[select]['succes_print'] + file_i, 1)
                if select in ('in', 'mk'):
                    search_version = re.search(r'^.*?version "(?P<version>.*?)"', result[0][0])
                    if search_version and search_version.group('version'):
                        print_indent('Add the following rule to your cs to select this version:', 2)
                        print_indent('element ' + file_i + ' ' + search_version.group('version'), 2)
            elif any([(config['reserved_str'] in line.lower()) for line in result[1]]):
                print_indent('ERROR File is reserved: ' + file_i, 1)
            elif any([(config['not_in_cc_str'] in line.lower()) for line in result[1]]) and select == 'in':
                mk_arguments = {name: kwargs[name] for name in config['mk']['parameters']}
                mk_result = config['mk']['fn'](file_i, **mk_arguments)
                if any([(config['mk']['succes_str'] in line.lower()) for line in mk_result[0]]):
                    print_indent(config['mk']['succes_print'] + file_i, 1)
                else:
                    print_indent(mk_result[0] + mk_result[1], 1)
            elif single_item:
                print_indent('Ignored: ' + file_i, 1)
            else:
                print_indent(result + file_i, 1)

def get_status(get_modified=False, get_untracked=False, get_checkedout_unmodified=False,
               item=None, whole_view=False):
    directory = item if item else (None if whole_view else getcwd())
    checked_out_files = list_checked_out(directory)
    modifications = find_modifications(checked_out_files)

    modified_files = [filename_from_diff(changed) for changed in modifications] if get_modified else []
    untracked_files = list_untracked(directory) if get_untracked else []
    checked_out_unmodified = list(set(checked_out_files) - set(modified_files)) if get_checkedout_unmodified else []

    return (to_abs_path(modified_files), to_abs_path(untracked_files), to_abs_path(checked_out_unmodified))


def get_working_view_name():
    result_pwv = run_cmd_command('cleartool pwv', get_lines=True)
    if not any(['Set view: ** NONE **' in line for line in result_pwv[0]]):
        search_view = re.search(r'^Set view: (?P<view>.*?)$', result_pwv[0][1])
        if search_view:
            return search_view.group('view')
    return None

def get_cs_text(cs_filename=None, view=False):
    if view and cs_filename:
        result_provided_name = run_cmd_command('cleartool catcs -tag ' + cs_filename, get_lines=True)
        if not any(['Error: View tag' in line for line in result_provided_name[1]]):
            return result_provided_name[0]
        elif 'USER' in os.environ:
            result_user_name = run_cmd_command('cleartool catcs -tag ' + os.environ['USER'] + '_' + cs_filename, get_lines=True)
            if not any(['Error: View tag' in line for line in result_user_name[1]]):
                return result_user_name[0]
        print_indent('Error getting cs ' + cs_filename, 0)
        return

    elif cs_filename:
        return [line.rstrip() for line in open(cs_filename)]
    else:
        return run_cmd_command('cleartool catcs', get_lines=True)[0]

def get_cs_files(cs_filename=None, view=False):
    cs_file_current = get_cs_text()
    if cs_filename:
        cs_file_new = get_cs_text(cs_filename, view)
        set_cs(cs_file_new)

    ct_ls = run_cmd_command('cleartool ls -r', get_lines=True)[0]
    cs_files = {}
    for item in ct_ls:
        matched = re.search(r'^(?P<filename>.*?)(@@(?P<version>.*?))?\s*(Rule: (?P<rule>.*?))?$', item)
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


def write_to_file(line_list, path):
    with open(path, 'w+') as destination_file:
        file_lines = [line.rstrip() + '\n' for line in line_list]
        while not file_lines[-2].rstrip():
            file_lines.pop()
        destination_file.writelines(file_lines)


def set_cs(new_cs):
    if isinstance(new_cs, list):
        write_to_file(new_cs, 'cs_temp')
        new_cs = 'cs_temp'
    result = run_cmd_command('cleartool setcs ' +  new_cs)
    if new_cs == 'cs_temp':
        remove(new_cs)
    return result


def diff_cs(csfile_a, csfile_b, view=False, diff_files=False):
    cs_a = get_cs_files(csfile_a, view=view)
    cs_b = get_cs_files(csfile_b)
    if diff_files:
        if ('DIFFTOOL' in os.environ):
            filename_a = csfile_a + '.cs'
            filename_b = (csfile_b or 'CURRENT') + '.cs'
            created_a = False
            created_b = False
            if not exists(filename_a):
                created_a = True
                write_to_file(cs_a[1], filename_a)
            if not exists(filename_b):
                created_b = True
                write_to_file(cs_b[1], filename_b)
            run_cmd_command([os.environ['DIFFTOOL'], abspath(filename_a), abspath(filename_b)])
            if created_a:
                remove(filename_a)
            if created_b:
                remove(filename_b)
        else:
            print_indent('error: environment variable DIFFTOOL is not set. Set it to your preferred diff tool, for example: setenv DIFFTOOL meld', 0)
        return None, None, None
    else:
        return diff_cs_versions(cs_a[0], cs_b[0])


def diff_cs_versions(cs_files_a, cs_files_b):
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


def sort_paths(path_list):
    sorted_paths = sorted([[filepath, Path(filepath)] for filepath in path_list], key = lambda x: x[1])
    return [str(i[0]) for i in sorted_paths]


def get_block_name_path(blockname=None):
    if not ('PROJVOB' in os.environ):
        return None, None
    src_path = join((os.environ['PROJVOB']), 'src')
    if not blockname:
        cwd = abspath(getcwd())
        if cwd.startswith(src_path):
            blockname = search_regex(r'^(\/|\\)?(?P<blockname>\w+)(\/|\\)?', cwd[len(src_path):], ['blockname'])['blockname']
    if blockname:
        return blockname, join(src_path, blockname)
    else:
        return None, None


def find_save_cs_dir(blockname=None, user=False):
    block_path = get_block_name_path(blockname)[1]
    if not block_path:
        print_indent(
            'Unable to find block name automatically. Try running from inside the block file-tree or provide --block or --absolute-path.', 0)
        return None
    needed_paths = [join(block_path, 'cs')]
    if user:
        needed_paths.append(join(needed_paths[0], 'user'))
    current_cs = get_cs_text()
    set_cs(DEFAULT_CS)
    for cs_path in needed_paths:
        if not exists(cs_path):
            print_indent('Creating ' + cs_path, 1)
            os.mkdir(cs_path)
            cc_checkx('in', recursive=False, selected_item=cs_path, message='Create directory to store CS files.', identical=False)
    set_cs(current_cs)
    if user:
        return needed_paths[1]
    else:
        return needed_paths[0]


def get_cs_path(block=None, cs_file_name=None):
    is_user = not cs_file_name
    save_cs_dir = find_save_cs_dir(block, is_user)
    if not save_cs_dir:
        return None
    save_cs_file_name = (cs_file_name or get_working_view_name()) + '.cs'
    return join(save_cs_dir, save_cs_file_name)
