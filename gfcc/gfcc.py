import os
import sys
import argparse

from   os      import getcwd, chdir, walk, remove
from   os.path import abspath, relpath, isdir, basename, join
from   gfcc import utils


# Command parser
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()


# Subparser for: gfcc status
parser_status = subparsers.add_parser('status', aliases=['s'], help='List all new or modified files.')
parser_status.add_argument(
    '-u', '--untracked',
    dest='untracked',
    choices=['no','normal','all'],
    default='normal',
    help='Show untracked files.'
)
parser_status.add_argument(
    '-v', '--view',
    dest='view',
    action='store_true',
    default=False,
    help='Show modifications in the whole view.'
)
parser_status.add_argument(
    '-co', '--checked-out',
    dest='checked-out',
    action='store_true',
    default=False,
    help='Show also files that are checked-out.'
)
parser_status.add_argument(
    'items',
    nargs='*',
    help='Get status for a specific item(s).',
)


def handler_status(res):
    untracked = getattr(res, 'untracked', None)
    whole_view = getattr(res, 'view', None)
    checked_out = getattr(res, 'checked-out', None)
    items = getattr(res, 'items', None) or [None]

    utils.print_indent(utils.run_cmd_command('cleartool pwv')[0].strip(), 0)

    for item in items:
        utils.print_indent('Status in ' +  (relpath(item) if item else basename(abspath('.'))) + ':', 0)
        modified_files, untracked_files, checked_out_unmodified = utils.get_status(
            get_modified=True, get_untracked=(untracked != 'no'), get_checkedout_unmodified=(checked_out),
            item=item, whole_view=whole_view
        )
        utils.print_indent('Modified files:', 1)
        utils.print_indent((utils.to_rel_path(modified_files) or ['None.']), 2)

        if untracked != 'no':
            utils.print_indent('Untracked files:', 1)
            utils.print_indent((utils.to_rel_path(untracked_files) or ['None.']), 2)

        if checked_out:
            utils.print_indent('Checked-out files unmodified:', 1)
            utils.print_indent((utils.to_rel_path(checked_out_unmodified) or ['None.']), 2)

parser_status.set_defaults(func=handler_status)


# Subparser for: gfcc diff
parser_diff = subparsers.add_parser('diff', aliases=['d'], help='Show differences in modified files.')
parser_diff.add_argument(
    '-g', '--graphical',
    dest='graphical',
    action='store_true',
    default=False,
    help='Open differences in GUI (if any).'
)
parser_diff.add_argument(
    'items',
    nargs='*',
    help='Find diffs on a specific item(s).',
)

def handler_diff(res):
    items = getattr(res, 'items', None)
    graphical = getattr(res, 'graphical', None)

    modified_files, _, _ = utils.get_status(get_modified=True, item=getcwd())
    for item in (items or modified_files):
        if graphical:
            if modified_files:
                utils.find_modifications([item], gui=True)
            else:
                utils.print_indent('No differences.', 1)
        else:
            checked_out_files = utils.list_checked_out()
            modifications = utils.find_modifications([item] if item else checked_out_files)
            utils.print_indent('Modifications:', 1)
            for modification in (modifications or [utils.INDENTATION * 2 + 'None.']):
                utils.print_indent(modification, 0)

parser_diff.set_defaults(func=handler_diff)


# Subparser for: gfcc log
parser_log = subparsers.add_parser('log', aliases=['l'], help='Show logerences in modified files.')
parser_log.add_argument(
    '-l', '--lines',
    dest='lines',
    help='Number of lines of history to print (default 15).'
)
parser_log.add_argument(
    '-r', '--recursive',
    dest='recursive',
    action='store_true',
    default=False,
    help='Apply recursively going into subdirectories.'
)
parser_log.add_argument(
    '-g', '--graphical',
    dest='graphical',
    action='store_true',
    default=False,
    help='Open history in GUI.'
)
parser_log.add_argument(
    '-t', '--tree',
    dest='tree',
    action='store_true',
    default=False,
    help='Open history in visual version tree.'
)
parser_log.add_argument(
    'items',
    nargs='*',
    help='You can provide one or more directory or file to get the history of that item(s) alone.',
)

def handler_log(res):
    lines = getattr(res, 'lines', None)
    recursive = getattr(res, 'recursive', None)
    graphical = getattr(res, 'graphical', None)
    tree = getattr(res, 'tree', None)
    items = getattr(res, 'items', None) or ['.']

    for item in items:
        if tree:
            utils.cc_xlsvtree(item)
        else:
            result = utils.cc_lshist(item, lines or 5, recursive, graphical)
            if not graphical:
                utils.print_indent('Change history of ' +  item, 0)
                result = utils.print_indent(result, 1)

parser_log.set_defaults(func=handler_log)


# Subparser for: gfcc clean
parser_clean = subparsers.add_parser('clean', aliases=['cl'], help='Remove untracked files.')
parser_clean.add_argument(
    '-a', '--clean_all',
    dest='clean_all',
    action='store_true',
    default=False,
    help='Remove ALL untracked.'
)
parser_clean.add_argument(
    'items',
    nargs='*',
    help='Clean one or several directories.',
)

def handler_clean(res):
    clean_all = getattr(res, 'clean_all', None)
    items = getattr(res, 'items', None) or ['.']
    items = [abspath(item) for item in items if isdir(item)]

    for item in items:
        chdir(item)
        _, untracked_files, _ = utils.get_status(get_untracked=True)
        files_to_delete = untracked_files if clean_all else [f for f in untracked_files if f.endswith(utils.TEMPORARY_FILE_EXTENSIONS)]
        utils.rm(files_to_delete, r=True)
        for file_deleted in files_to_delete:
            utils.print_indent('Removed: ' + file_deleted, 1)
        utils.print_indent('Directory ' + item + ' clean.', 1)

parser_clean.set_defaults(func=handler_clean)


# Subparser for: gfcc checkout
parser_checkout = subparsers.add_parser('checkout', aliases=['co'], help='Checkout file/dir/recursively in the ClearCase sense.')
parser_checkout.add_argument(
    '-r', '--recursive',
    dest='recursive',
    action='store_true',
    default=False,
    help='Apply to all subdirectories and files recursively.'
)
parser_checkout.add_argument(
    '-e', '--edit',
    dest='edit',
    action='store_true',
    default=False,
    help='Open checked-out file in the editor defined by $EDITOR'
)
parser_checkout.add_argument(
    'items',
    nargs='*',
    help='File(s) or dir(s) to check-out.',
)

def handler_checkout(res):
    recursive = getattr(res, 'recursive', None)
    edit = getattr(res, 'edit', None)
    items = getattr(res, 'items', None)
    recursive = recursive if items else True
    items = items or [getcwd()]

    for item in items:
        item = abspath(item)
        utils.cc_checkx('out', recursive, item)

        if edit and ('EDITOR' in os.environ) and not isdir(item):
            utils.print_indent('opening in ' + os.environ['EDITOR'] + ' ...', 2)
            utils.run_cmd_command([os.environ['EDITOR'], item], background=True)
        elif not ('EDITOR' in os.environ):
            utils.print_indent('Error opening file: EDITOR environment variable is not set. You can set it like: setenv EDITOR gedit', 2)

parser_checkout.set_defaults(func=handler_checkout)


# Subparser for: gfcc checkin
parser_checkin = subparsers.add_parser('checkin', aliases=['ci'], help='Checkin file/dir/recursively in the ClearCase sense.')
parser_checkin.add_argument(
    '-m', '--message',
    dest='message',
    required=True,
    help='Comment or description of the checkin (mandatory).'
)
parser_checkin.add_argument(
    '-r', '--recursive',
    dest='recursive',
    action='store_true',
    default=False,
    help='Apply to all subdirectories and files recursively.'
)
parser_checkin.add_argument(
    '-u', '--untracked',
    dest='untracked',
    action='store_true',
    default=False,
    help='Create element and check-in untracked items too.'
)
parser_checkin.add_argument(
    '-i', '--identical',
    dest='identical',
    action='store_true',
    default=False,
    help='Checkin even if files are identical.'
)
parser_checkin.add_argument(
    'items',
    nargs='*',
    help='File(s) or dir(s) to check-in.',
)

def handler_checkin(res):
    message = getattr(res, 'message', None)
    recursive = getattr(res, 'recursive', None)
    untracked = getattr(res, 'untracked', None)
    identical = getattr(res, 'identical', None)
    items = getattr(res, 'items', None)
    recursive = recursive if items else True
    items = items or [getcwd()]

    for item in items:
        item = abspath(item)
        utils.cc_checkx('in', recursive, item, untracked, message=message, identical=identical)

parser_checkin.set_defaults(func=handler_checkin)


# Subparser for: gfcc uncheckout
parser_uncheckout = subparsers.add_parser('uncheckout', aliases=['un', 'unco'], help='Un-checkout file/dir/recursively in the ClearCase sense.')
parser_uncheckout.add_argument(
    '-r', '--recursive',
    dest='recursive',
    action='store_true',
    default=False,
    help='Apply to all subdirectories and files recursively.'
)
parser_uncheckout.add_argument(
    '-k', '--keep',
    dest='keep',
    action='store_true',
    default=False,
    help='Keep private copy.'
)
parser_uncheckout.add_argument(
    'items',
    nargs='*',
    help='File(s)/dir(s) to uncheckout.',
)

def handler_uncheckout(res):
    recursive = getattr(res, 'recursive', None)
    keep = getattr(res, 'keep', None)
    items = getattr(res, 'items', None)
    recursive = recursive if items else True
    items = items or [getcwd()]

    for item in items:
        item = abspath(item)
        utils.cc_checkx('un', recursive, item, keep=keep)

parser_uncheckout.set_defaults(func=handler_uncheckout)


# Subparser for: gfcc edcs
parser_edcs = subparsers.add_parser('edcs', aliases=['ed'], help='Edit current cs.')
parser_edcs.add_argument(
    'item',
    nargs='?',
    help='CS file to edit',
)

def handler_edcs(res):
    utils.run_cmd_command(['cleartool', 'edcs'], False, True)

parser_edcs.set_defaults(func=handler_edcs)


# Subparser for: gfcc find
parser_find = subparsers.add_parser('find', aliases=['f'], help='Quick access to useful filters.')
parser_find.add_argument(
    '-l', '--latest',
    dest='latest',
    action='store_true',
    default=False,
    help='Find files selected by rule /LATEST.'
)
parser_find.add_argument(
    '-nl', '--not-latest',
    dest='not-latest',
    action='store_true',
    default=False,
    help='Find files for which a newer version exists.'
)
parser_find.add_argument(
    '-v', '--view',
    dest='view',
    default=None,
    help='Perform the search on another view.'
)
parser_find.add_argument(
    '-d', '--directory',
    dest='directory',
    default='.',
    help='Perform the search in the provided directory.'
)
parser_find.add_argument(
    'item',
    nargs='?',
    help='Item.',
)

def handler_find(res):
    item = getattr(res, 'item', None)
    latest = getattr(res, 'latest', None)
    not_latest = getattr(res, 'not-latest', None)
    view = getattr(res, 'view', None)
    directory = getattr(res, 'directory', None)

    if directory:
        chdir(directory)

    if latest:
        files_versions = utils.get_cs_files(view, view=bool(view))[0]
        files_rule_latest = [
            file_i for file_i in files_versions
            if (not file_i == 'cs' and not file_i.endswith(('.cs', '/cs', '/cs/user')) and files_versions[file_i]['rule'].endswith('/LATEST'))]

        utils.print_indent('Files selected by rule /LATEST' + ((' in view ' + view) if view else '') + ((' in ' + directory) if directory else '') + ' : ', 0)
        utils.print_indent(files_rule_latest or 'None.', 1)


parser_find.set_defaults(func=handler_find)


# Subparser for: gfcc diffcs
parser_diffcs = subparsers.add_parser('diffcs', aliases=['dcs'], help='Diff the files selected by two Config-Spec files.')
parser_diffcs.add_argument(
    '-f', '--files',
    dest='files',
    action='store_true',
    default=False,
    help='Diff the actual CS files, instead of the list of files and versions selected by them.'
)
parser_diffcs.add_argument(
    '-d', '--directory',
    dest='directory',
    nargs='*',
    default=['.'],
    help='Perform the comparison in the provided directory (or directories).'
)
parser_diffcs.add_argument(
    '-b', '--block',
    dest='block',
    help='Block name (to diff against a block configspec).'
)
parser_diffcs.add_argument(
    '-v', '--view',
    dest='view',
    help='Diff against current CS in the provided view.'
)
parser_diffcs.add_argument(
    '-g', '--gen_rules',
    dest='gen_rules',
    action='store_true',
    default=False,
    help='Generate cs rules so that you get the same versions as others.'
)
parser_diffcs.add_argument(
    'cs-file',
    nargs='*',
    help='CS file to diff against current one, or two CS files to be diffed.',
)

def handler_diffcs(res):
    diff_files = getattr(res, 'files', None)
    directory = getattr(res, 'directory', None)
    block = getattr(res, 'block', None)
    view = getattr(res, 'view', None)
    gen_rules = getattr(res, 'gen_rules', None)
    cs_file = getattr(res, 'cs-file', None)

    csfile_a = utils.guess_cs_file(block, view, cs_file[0] if cs_file else None)
    if not csfile_a:
        utils.print_indent('Error: cannot find the cs files to compare. Try providing the --block or the filepaths.', 0)
        return
    if len(cs_file) < 2 or view:
        csfile_b = None
    elif len(cs_file) == 2:
        csfile_b = abspath(cs_file[1])
    else:
        utils.print_indent('Error: max two files to diff.', 0)

    directory = [abspath(dir_i) for dir_i in directory]
    for dir_i in directory:
        utils.print_indent(
            'Comparing ' + \
            ('files selected by ' if not diff_files else '') + \
            'CS files ' + relpath(csfile_a) + ' vs ' +  (relpath(csfile_b) if csfile_b else 'CURRENT') + \
            (' ...' if diff_files else ' in ' + (relpath(dir_i) if dir_i != getcwd() else basename(abspath(dir_i))) + ' :' ),
            0
        )

        chdir(dir_i)

        cs_a, cs_b, a_not_b, b_not_a, diff_v = utils.diff_cs(csfile_a, csfile_b, bool(view), diff_files)

        if not diff_files:
            if not any([a_not_b, b_not_a, diff_v]):
                utils.print_indent('Identical: Both CS files select the same files and versions.', 1)
            else:
                utils.print_indent('Files selected by ' + (csfile_b or 'CURRENT') + ' and NOT by ' + relpath(csfile_a)  + ':', 1)
                if not b_not_a:
                    utils.print_indent('None.', 2)
                else:
                    for item in utils.sort_paths(b_not_a):
                        if gen_rules:
                            utils.print_indent(('element ' + abspath(item) + ' ' + cs_b[0][item]['rule']) if cs_b[0][item]['rule']
                                else ('* ' + relpath(item) + ' has NO rule in ' + (csfile_b or 'CURRENT')), 2)
                        else:
                            utils.print_indent(relpath(item) + '   (Rule ' + (cs_b[0][item]['rule'] or 'NONE') + ')', 2)

                utils.print_indent('Files selected by ' + relpath(csfile_a) + ' and NOT by ' + (csfile_b or 'CURRENT') + ':', 1)
                if not a_not_b:
                    utils.print_indent('None.', 2)
                else:
                    for item in utils.sort_paths(a_not_b):
                        if gen_rules:
                            utils.print_indent(('element ' + abspath(item) + ' ' + cs_a[0][item]['rule']) if cs_a[0][item]['rule']
                                else ('* ' + relpath(item) + ' has NO rule in ' + csfile_a), 2)
                        else:
                            utils.print_indent(relpath(item) + '   (Rule ' + (cs_a[0][item]['rule'] or 'NONE') + ')', 2)

                utils.print_indent('Files with different versions in ' + (csfile_b or 'CURRENT') + ' vs ' + relpath(csfile_a) + ':', 1)
                if not diff_v:
                    utils.print_indent('None.', 2)
                else:
                    for item in utils.sort_paths(diff_v.keys()):
                        if gen_rules:
                            utils.print_indent(('element ' + abspath(item) + ' ' + cs_a[0][item]['rule']) if cs_a[0][item]['rule']
                                else ('* ' + relpath(item) + ' has NO rule in ' + csfile_a), 2)
                        else:
                            utils.print_indent(
                                relpath(item) \
                                + '   ' + diff_v[item][1]['version'] + ' vs ' + diff_v[item][0]['version'] \
                                + '   (Rule ' + (diff_v[item][1]['rule'] or 'NONE') \
                                + ' vs ' + (diff_v[item][0]['rule'] or 'NONE') + ')',
                                2
                            )

            if csfile_b == None:
                modified_files, _, _ = utils.get_status(
                    get_modified=True, item=dir_i
                )
                if modified_files:
                    utils.print_indent('Warning: The following changes are local, only visible in your view.', 1)
                    utils.print_indent('Modified files:', 2)
                    utils.print_indent((modified_files or ['None.']), 3)

parser_diffcs.set_defaults(func=handler_diffcs)


# Subparser for: gfcc difflabels
parser_difflabels = subparsers.add_parser('difflabels', aliases=['dl'], help='Diff the files selected by two different labels.')
parser_difflabels.add_argument(
    '-d', '--directory',
    dest='directory',
    nargs='*',
    default=['.'],
    help='Perform the comparison in the provided directory (or directories).'
)
parser_difflabels.add_argument(
    'labels',
    nargs=2,
    help='Two labels to diff against each other.',
)

def handler_difflabels(res):
    directory = getattr(res, 'directory', None)
    labels = getattr(res, 'labels', None)

parser_difflabels.set_defaults(func=handler_difflabels)


# Subparser for: gfcc savecs
parser_savecs = subparsers.add_parser('savecs', aliases=['scs'], help='Save your current cs state in cc.')
parser_savecs.add_argument(
    '-b', '--block',
    dest='block',
    help='Block name.'
)
parser_savecs.add_argument(
    '-m', '--message',
    dest='message',
    required=False,
    help='Comment or description (mandatory for shared cs files).'
)
parser_savecs.add_argument(
    '-p', '--absolute-path',
    dest='absolute-path',
    help='Absolute path where the cs file will be saved (ignore blockname/cs structure and file name).'
)
parser_savecs.add_argument(
    '-f', '--force',
    dest='force',
    action='store_true',
    default=False,
    help='Overrides "LATEST not allowed" and "identical versions are not checked in".'
)
parser_savecs.add_argument(
    'cs-file-name',
    nargs='?',
    help='Name of a shared configspec to save to.',
)

def handler_savecs(res):
    block = getattr(res, 'block', None)
    message = getattr(res, 'message', None)
    force = getattr(res, 'force', None)
    absolute_path = getattr(res, 'absolute-path', None)
    cs_file_name = getattr(res, 'cs-file-name', None)

    if cs_file_name and not message:
        return utils.print_indent(
            'Error: Description is mandatory for shared CS files. Add it with -m "Your description."', 1)
    current_cs = utils.get_cs_text()
    if any([('/LATEST' in line) and not (('/cs/...' in line) or line.strip().startswith('#')) for line in current_cs]) and not force:
        return utils.print_indent(
            'Error: Using LATEST in your CS is not allowed unless you --force it.', 1)

    utils.write_to_file(current_cs, 'current.cs.bak')
    utils.set_cs(utils.DEFAULT_CS)
    if not absolute_path:
        absolute_path = utils.get_cs_path(block, cs_file_name)
        if not absolute_path:
            return
    if not utils.exists_try(absolute_path):
        open(absolute_path, 'a').close()
    elif force or current_cs != utils.get_cs_text(absolute_path):
        utils.cc_checkx('out', False, absolute_path)

    utils.write_to_file(current_cs, absolute_path)
    utils.cc_checkx(
        'in', False, absolute_path,
        message=message or ('Saved ' + utils.get_date_string()), identical=force
    )
    utils.set_cs(current_cs)
    remove('current.cs.bak')
    utils.print_indent('Current version of your CS saved in: ' + relpath(absolute_path), 1)

parser_savecs.set_defaults(func=handler_savecs)


# Subparser for: gfcc setcs
parser_setcs = subparsers.add_parser('setcs', aliases=['stcs'], help='Save your current cs state in cc.')
parser_setcs.add_argument(
    '-b', '--block',
    dest='block',
    help='Block name (if you want to load a block or user cs file and the path cannot be automatically identified).'
)
parser_setcs.add_argument(
    '-v', '--view',
    dest='view',
    help='Copy the current CS in another view to this one.'
)
parser_setcs.add_argument(
    '-k', '--backup',
    dest='backup',
    action='store_true',
    default=False,
    help='Save current CS in a backup file before applying the new CS.'
)
parser_setcs.add_argument(
    'cs-file',
    nargs='?',
    help='Name or path of the configspec to apply.',
)

def handler_setcs(res):
    block = getattr(res, 'block', None)
    view = getattr(res, 'view', None)
    backup = getattr(res, 'backup', None)
    cs_file = getattr(res, 'cs-file', None)

    cs_to_apply = utils.guess_cs_file(block, view, cs_file)

    if cs_to_apply:
        cs_name = cs_to_apply
        if backup:
            utils.write_to_file(utils.get_cs_text(), 'current.cs.bak')
            utils.print_indent('Current CS backup saved in ./current.cs.bak', 0)
        if view:
            cs_to_apply = utils.get_cs_text(cs_to_apply, view)
        utils.set_cs(cs_to_apply)
        utils.print_indent('Current CS set to: ' + cs_name, 0)
    else:
        utils.print_indent('Source CS file could not be identified with the provided parameters or found in your filesystem.', 0)
        return

parser_setcs.set_defaults(func=handler_setcs)


# Subparser for: gfcc codereview
parser_codereview = subparsers.add_parser('codereview', aliases=['cr'], help='Create, share and review sets of code changes.')
parser_codereview.add_argument(
    '-c', '--create',
    dest='create',
    help='Block name (if you want to load a block or user cs file and the path cannot be automatically identified).'
)
parser_codereview.add_argument(
    '-b', '--block',
    dest='block',
    help='Block name (if you want to load a block or user cs file and the path cannot be automatically identified).'
)
parser_codereview.add_argument(
    '-o', '--old_cs',
    dest='old_cs',
    help='Copy the current CS in another view to this one.'
)
parser_codereview.add_argument(
    '-n', '--new_cs',
    dest='new_cs',
    help='Copy the current CS in another view to this one.'
)
parser_codereview.add_argument(
    'name',
    nargs='?',
    help='Name or path of the configspec to apply.',
)

def handler_codereview(res):
    create = getattr(res, 'create', None)
    block = getattr(res, 'block', None)
    old_cs = getattr(res, 'old_cs', None)
    new_cs = getattr(res, 'new_cs', None)
    name = getattr(res, 'name', None)

    code_reviews_dir = utils.find_save_cs_dir(block, False, True)

    if create:
        pass
    else:
        pass

parser_codereview.set_defaults(func=handler_codereview)


# main
def main():
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        res = parser.parse_args()
        res.func(res)


if __name__ == '__main__':
    main()
