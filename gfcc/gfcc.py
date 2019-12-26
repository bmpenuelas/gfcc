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
    '-wv', '--whole-view',
    dest='whole-view',
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
    whole_view = getattr(res, 'whole-view', None)
    checked_out = getattr(res, 'checked-out', None)
    items = getattr(res, 'items', None) or [None]

    utils.print_indent('Current view: ' + utils.get_working_view_name(), 0)

    for item in items:
        utils.print_indent('Status in ' +  (relpath(item) if item else basename(abspath('.'))) + ':', 0)
        modified_files, untracked_files, checked_out_unmodified = utils.get_status(
            get_modified=True, get_untracked=(untracked != 'no'), get_checkedout_unmodified=(checked_out),
            item=item, whole_view=whole_view
        )
        utils.print_indent('Modified files:', 1)
        utils.print_indent((utils.to_rel_path(modified_files) or ['None.']), 2)

        if untracked != 'no':
            untracked_filtered = [item for item in utils.to_rel_path(untracked_files) if not item.endswith(utils.TEMPORARY_FILE_EXTENSIONS)]
            untracked_ignored = [item for item in utils.to_rel_path(untracked_files) if item.endswith(utils.TEMPORARY_FILE_EXTENSIONS)]
            utils.print_indent('Untracked files:', 1)
            utils.print_indent((untracked_filtered or ['None.']), 2)
            if untracked_ignored:
              utils.print_indent('Untracked files (ignored):', 1)
              utils.print_indent(untracked_ignored, 2)

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
    '-a', '--all',
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
            utils.run_cmd([os.environ['EDITOR'], item], background=True)
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
    '-da', '--dont-add-to-cs',
    dest='dont_add_to_cs',
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
    dont_add_to_cs = getattr(res, 'dont_add_to_cs', None)
    items = getattr(res, 'items', None)
    recursive = recursive if items else True
    items = items or [getcwd()]

    for item in items:
        item = abspath(item)
        utils.cc_checkx('in', recursive, item, untracked, message=message, identical=identical, add_rule_to_cs=(not dont_add_to_cs))

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

    if not items:
        modified_files, _, checked_out_unmodified = utils.get_status(
            get_modified=True, get_untracked=False, get_checkedout_unmodified=True, item=getcwd()
        )
        items = modified_files + checked_out_unmodified

    for item in items:
        item = abspath(item)
        utils.cc_checkx('un', recursive, item, keep=keep)

parser_uncheckout.set_defaults(func=handler_uncheckout)


# Subparser for: gfcc copyco
parser_copyco = subparsers.add_parser('copyco', aliases=['cco'], help='Copy the checked-out modified version from some other view into yours.')
parser_copyco.add_argument(
    '-v', '--view',
    dest='view',
    default=None,
    required=True,
    help='Perform the search on another view.'
)
parser_copyco.add_argument(
    'items',
    nargs='*',
    help='File(s)/dir(s) to copyco.',
)

def handler_copyco(res):
    view = getattr(res, 'view', None)
    items = getattr(res, 'items', None)

    for item in items:
        utils.copy_co(item, view)

parser_copyco.set_defaults(func=handler_copyco)


# Subparser for: gfcc edcs
parser_edcs = subparsers.add_parser('edcs', aliases=['ed'], help='Edit current cs.')
parser_edcs.add_argument(
    'item',
    nargs='?',
    help='CS file to edit',
)

def handler_edcs(res):
    utils.run_cmd(['cleartool', 'edcs'], False, True)

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
    '-g', '--gen_rules',
    dest='gen_rules',
    action='store_true',
    default=False,
    help='Generate cs rules so that you get the found versions.'
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
    gen_rules = getattr(res, 'gen_rules', None)
    view = getattr(res, 'view', None)
    directory = getattr(res, 'directory', None)

    if directory:
        chdir(directory)

    if latest:
        files_versions = utils.get_file_versions(view, view=bool(view))[0]
        files_rule_latest = [
            file_i for file_i in files_versions
            if (not file_i == 'cs' and not file_i.endswith(('.cs', '/cs', '/cs/user')) and files_versions[file_i]['rule'].endswith('/LATEST'))]

        utils.print_indent('Files selected by rule /LATEST' + ((' in view ' + view) if view else '') + ((' in ' + directory) if directory else '') + ': ', 0)
        utils.print_indent(files_rule_latest or 'None.', 1)

    if not_latest:
        files_versions = utils.get_file_versions(view, view=bool(view))[0]
        files_latest_versions = utils.get_file_versions(get_latest=True)[0]
        files_not_latest = [
            file_i for file_i in files_versions
            if ((file_i in files_latest_versions) and (files_versions[file_i]['version'] != files_latest_versions[file_i]['version']))]

        utils.print_indent( \
            ('Rules for f' if gen_rules else 'F') + 'iles not at their latest version ' + \
            ((' in view ' + view) if view else '') + \
            ((' in ' + directory) if directory else '') + ': ', 0)
        if gen_rules:
            for file_i in files_not_latest:
                utils.print_rule(file_i, files_latest_versions[file_i]['version'], 0)
        else:
            result_text = [file_i + '   (selected: ' + files_versions[file_i]['version'] + ' vs latest: ' + files_latest_versions[file_i]['version']  + ')'for file_i in files_not_latest]
            utils.print_indent(result_text or 'None.', 1)


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
    '-p', '--previous',
    dest='previous',
    action='store_true',
    default=False,
    help='Diff against the previous to LATEST version of the provided cs.'
)
parser_diffcs.add_argument(
    '-r', '--review',
    dest='review',
    action='store_true',
    default=False,
    help='Review the differences with your preferred difftool.'
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
    previous = getattr(res, 'previous', None)
    review = getattr(res, 'review', None)
    cs_file = getattr(res, 'cs-file', None)

    csfile_a = utils.guess_cs_file(block, view, cs_file[0] if cs_file else None)
    if not csfile_a:
        utils.print_indent('Error: cannot find the cs files to compare. Try providing the --block or the filepaths.', 0)
        return
    if view:
        csfile_b = None
    elif len(cs_file) < 2:
        if previous:
            csfile_b = utils.get_previous_to_latest(csfile_a)
        else:
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
            (' ...' if diff_files else ' in ' + (relpath(dir_i) if dir_i != getcwd() else basename(abspath(dir_i))) + ':' ),
            0
        )

        utils.diffcs(csfile_a, csfile_b, view, diff_files, dir_i, gen_rules, review)

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
    cs_file_name = getattr(res, 'cs-file-name', '')

    gfcc_config = utils.get_gfcc_config_from_cs()

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
        current_version = None
    elif force or current_cs != utils.get_cs_text(absolute_path):
        current_version = utils.get_single_file_version(absolute_path)
        utils.cc_checkx('out', False, absolute_path)

    utils.write_to_file(current_cs, absolute_path)

    mail_updates = cs_file_name and current_version and gfcc_config and gfcc_config['email_updates_to']
    if mail_updates:
        diff = utils.diff_text(absolute_path + '@@' + current_version, 'current.cs.bak')
        diff = (['<pre style="font: monospace">'] + diff + ['</pre>']) if diff else []

    utils.cc_checkx(
        'in', False, absolute_path,
        message=message or ('Saved ' + utils.get_date_string()),
        identical=force,
        add_rule_to_cs=False
    )
    utils.set_cs(current_cs)
    remove('current.cs.bak')
    utils.print_indent('Current version of your CS saved in: ' + relpath(absolute_path), 1)

    if mail_updates:
        new_version = utils.change_version_no(current_version, utils.get_version_no(current_version) + 1)
        mail_body = ['Message: ' + message + '\n'] + \
            ['New version: ' + new_version + '\n'] + \
            ['Changes:\n'] + diff
        utils.send_mail('CS Updated: ' + cs_file_name, mail_body, gfcc_config['email_updates_to'])
        utils.print_indent('Sent update email to ' + ', '.join(gfcc_config['email_updates_to']), 2)

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
    '-p', '--previous',
    dest='previous',
    action='store_true',
    default=False,
    help='Set to the previous to LATEST version of this cs.'
)
parser_setcs.add_argument(
    '-s', '--setup',
    dest='setup',
    action='store_true',
    default=False,
    help='Set the environment up applying modules and environment variables.'
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
    previous = getattr(res, 'previous', None)
    setup = getattr(res, 'setup', None)
    cs_file = getattr(res, 'cs-file', None)

    cs_to_apply = utils.guess_cs_file(block, view, cs_file)

    if cs_to_apply:
        if backup:
            utils.write_to_file(utils.get_cs_text(), 'my_current.cs.bak')
            utils.print_indent('Current CS backup saved in ./my_current.cs.bak', 0)
        if view:
            cs_to_apply = utils.get_cs_text(cs_to_apply, view)
            if not cs_to_apply:
                utils.print_indent('Error: View cs could not be found.', 0)
                return
        elif previous:
            cs_to_apply = utils.get_previous_to_latest(cs_to_apply)

        utils.set_cs(cs_to_apply)
        utils.print_indent('Current CS set to: ' + (cs_to_apply if not view else ('current cs of ' + view)), 0)

        if setup:
            gfcc_config = utils.get_gfcc_config_from_cs()
            if gfcc_config:
                utils.print_indent('Copy and run the following commands to get the environment configured:')
                if ('modules' in gfcc_config):
                    for module_i in gfcc_config['modules']:
                        utils.print_indent('module add ' +  module_i, 1)
                if ('env' in gfcc_config):
                    for env_i in gfcc_config['env']:
                        utils.print_indent('setenv ' + env_i[0] + ' ' + env_i[1], 1)
            else:
                utils.print_indent('No gfcc_config found in this cs.')

    else:
        utils.print_indent('Error: CS file not found. It could not be identified with the provided parameters or found in your filesystem, maybe not visible due to current cs.', 0)
        return

parser_setcs.set_defaults(func=handler_setcs)


# Subparser for: gfcc codereview
parser_codereview = subparsers.add_parser('codereview', aliases=['cr'], help='Create, share and review sets of code changes.')
parser_codereview.add_argument(
    '-c', '--create',
    dest='create',
    help='Create a diffs bundle to be reviewed by others.'
)
parser_codereview.add_argument(
    '-b', '--block',
    dest='block',
    help='Block to which this code review belongs.'
)
parser_codereview.add_argument(
    '-o', '--old_cs',
    dest='old_cs',
    help='CS with versions reflecting the "OLD" state.'
)
parser_codereview.add_argument(
    '-n', '--new_cs',
    dest='new_cs',
    help='CS with versions reflecting the "NEW" state.'
)
parser_codereview.add_argument(
    'name',
    nargs='*',
    help='Name or path of the codereview you want to go through.',
)

def handler_codereview(res):
    create = getattr(res, 'create', None)
    block = getattr(res, 'block', None)
    old_cs = getattr(res, 'old_cs', None)
    new_cs = getattr(res, 'new_cs', None)
    name = getattr(res, 'name', None)

    if (not (old_cs and new_cs)) and (len(name) == 2):
        old_cs = name[0]
        new_cs = name[1]

    code_reviews_dir = utils.find_save_cs_dir(block, False, True)

    if old_cs and new_cs:
        utils.diffcs(old_cs, new_cs, review_diffs=True)

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
