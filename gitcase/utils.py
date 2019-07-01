import re
import subprocess

from   os      import path, getcwd, walk
from   os.path import abspath


# Constants
INDENTATION = '  '


def run_cmd_command(cmd, get_lines=False):
    ''' Run a command in the shell and return the output. '''
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    decoded_out = result.stdout.decode('utf-8')
    decoded_err = result.stderr.decode('utf-8')
    return (decoded_out, decoded_err) if not get_lines else (decoded_out.split('\n'), decoded_err.split('\n'))


def print_indent(text, indent):
    if not isinstance(text, list):
        text = [text]
    for element in text:
        print(indent * INDENTATION + element)


def list_checked_out(directory=None):
    ''' List checked out takes the whole view/directory and returns abs/rel paths of the files. '''
    clearcase_cmd_list_checked_out = ['cleartool', 'lsco', '-cview', '-a', '-s']
    output = run_cmd_command(clearcase_cmd_list_checked_out, True)[0]
    if not directory:
        result = [item for item in output if item]
    else:
        directory = abspath(directory)
        result = [path.relpath(item, getcwd()) for item in output if item and item.startswith(directory)]
    return result


def find_modifications(to_check):
    ''' Take one or a list of abs or rel paths and return the differences reported by cleartool. '''
    if isinstance(to_check, list):
        return list(filter(lambda x: x, [find_modifications(file_i) for file_i in to_check]))
    else:
        clearcase_cmd_find_modifications = ['cleartool', 'diff', '-predecessor', to_check]
        output = run_cmd_command(clearcase_cmd_find_modifications)[0]
        modified = not 'identical' in output
        return output if modified else None


def filename_from_diff(modification):
    ''' Get the filename from a diff with predecessor. '''
    if not modification:
        return None
    file2 = re.search(r'file 2:\s(.+)\s', modification)
    return file2.group(1) if file2 else None


def list_untracked(directory):
    ''' List untracked works with relative paths by default due to the cleartool command. '''
    clearcase_cmd_find_untracked = ['cleartool', 'ls', '-rec', '-view_only']
    output = run_cmd_command(clearcase_cmd_find_untracked, True)[0]
    if directory:
        directory = None if abspath(directory) == getcwd() else path.relpath(abspath(directory), getcwd())
    return list(filter(lambda x: x and ('Rule' not in x) and (not directory or x.startswith(directory) or x.startswith('./' + directory)), output))


def cc_checkout(to_cc):
    if isinstance(to_cc, list):
        return [cc_checkout(element) for element in to_cc]
    else:
        clearcase_cmd_checkout = ['cleartool', 'co', '-unr', '-nc']
        return run_cmd_command(clearcase_cmd_checkout + [to_cc], True)


def cc_checkin(to_cc, message, identical):
    if isinstance(to_cc, list):
        return [cc_checkin(element, message, identical) for element in to_cc]
    else:
        clearcase_cmd_checkin = ['cleartool', 'ci', '-c', message] + (['-identical'] if identical else [])
        return run_cmd_command(clearcase_cmd_checkin + [to_cc], True)


def cc_uncheckout(to_cc, keep):
    if isinstance(to_cc, list):
        return [cc_uncheckout(element, keep) for element in to_cc]
    else:
        clearcase_cmd_uncheckout = ['cleartool', 'unco', '-keep' if keep else '-rm']
        return run_cmd_command(clearcase_cmd_uncheckout + [to_cc], True)


def cc_checkx(select, recursive, selected_item, **kwargs):
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
    }

    arguments = {name: kwargs[name] for name in config[select]['parameters']}

    file_list = []
    if recursive and selected_item and path.isdir(selected_item):
        for root, _, files in walk(selected_item):
            file_list.extend([root] + files)
    else:
        file_list = [selected_item]
    for file_i in file_list:
        if (select == 'in' and filename_from_diff(find_modifications(file_i))) or (select != 'in'):
            result = config[select]['fn'](file_i, **arguments)
            if any([(config[select]['succes_str'] in line.lower()) for line in result[0]]):
                print_indent(config[select]['succes_print'] + file_i, 1)
            elif file_list == [selected_item]:
                print_indent('Ignored: ' + selected_item, 1)
