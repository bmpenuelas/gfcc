import sys
import argparse

from   os      import getcwd, walk
from   os.path import abspath, isdir
from   gitcase import utils


# Command parser
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()


# Subparser for: gitcase status
parser_status = subparsers.add_parser('status', aliases=['s'], help='List all new or modified files.')
parser_status.add_argument(
    '-u', '--untracked-files',
    dest='untracked-files',
    choices=['no','normal','all'],
    default='normal',
    help='Show untracked files.'
)
parser_status.add_argument(
    '-view', '--whole-view',
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
    'item',
    nargs='?',
    help='Get status for a specific item.',
)


def handler_status(res):
    untracked_files = getattr(res, 'untracked-files', None)
    whole_view = getattr(res, 'whole-view', None)
    checked_out = getattr(res, 'checked-out', None)
    item = getattr(res, 'item', None)

    modified_files, untracked, checked_out_unmodified = utils.get_status(
        get_modified=True, get_untracked=(untracked_files != 'no'), get_checkedout_unmodified=(checked_out),
        item=item, whole_view=whole_view
    )
    utils.print_indent('Modified files:', 1)
    utils.print_indent((modified_files or ['None.']), 2)

    if untracked_files != 'no':
        utils.print_indent('Untracked files:', 1)
        utils.print_indent((untracked or ['None.']), 2)

    if checked_out:
        utils.print_indent('Checked-out files unmodified:', 1)
        utils.print_indent((checked_out_unmodified or ['None.']), 2)

parser_status.set_defaults(func=handler_status)


# Subparser for: gitcase diff
parser_diff = subparsers.add_parser('diff', aliases=['d'], help='Show differences in modified files.')
parser_diff.add_argument(
    'item',
    nargs='?',
    help='Find diffs on a specific item.',
)

def handler_diff(res):
    selected_item = getattr(res, 'item', None)

    checked_out_files = utils.list_checked_out()
    modifications = utils.find_modifications([selected_item] if selected_item else checked_out_files)

    utils.print_indent('Modifications:', 1)
    for modification in modifications:
        print(modification)

parser_diff.set_defaults(func=handler_diff)


# Subparser for: gitcase clean
parser_clean = subparsers.add_parser('clean', aliases=['cl'], help='Remove untracked files.')

def handler_clean(res):
    _, untracked, _ = utils.get_status(get_untracked=True)
    utils.rm(untracked, r=True)
    for file_deleted in untracked:
        utils.print_indent('Removed: ' + file_deleted, 1)

parser_clean.set_defaults(func=handler_clean)


# Subparser for: gitcase ccheckout
parser_ccheckout = subparsers.add_parser('ccheckout', aliases=['co'], help='Checkout file/dir/recursively in the ClearCase sense.')
parser_ccheckout.add_argument(
    '-r', '--recursive',
    dest='recursive',
    action='store_true',
    default=False,
    help='Apply to all subdirectories and files recursively.'
)
parser_ccheckout.add_argument(
    'item',
    nargs='?',
    help='File/dir to ccheckout.',
)

def handler_ccheckout(res):
    recursive = getattr(res, 'recursive', None)
    selected_item = getattr(res, 'item', None)
    recursive = recursive if selected_item else True
    selected_item = abspath(selected_item or getcwd())

    utils.cc_checkx('out', recursive, selected_item)

parser_ccheckout.set_defaults(func=handler_ccheckout)


# Subparser for: gitcase ccheckin
parser_ccheckin = subparsers.add_parser('ccheckin', aliases=['ci'], help='Checkin file/dir/recursively in the ClearCase sense.')
parser_ccheckin.add_argument(
    '-m', '--message',
    dest='message',
    required=True,
    help='Comment or description of the checkin (mandatory).'
)
parser_ccheckin.add_argument(
    '-r', '--recursive',
    dest='recursive',
    action='store_true',
    default=False,
    help='Apply to all subdirectories and files recursively.'
)
parser_ccheckin.add_argument(
    '-i', '--identical',
    dest='identical',
    action='store_true',
    default=False,
    help='Checkin even if files are identical.'
)
parser_ccheckin.add_argument(
    'item',
    nargs='?',
    help='Find ccheckins on a specific item.',
)

def handler_ccheckin(res):
    message = getattr(res, 'message', None)
    recursive = getattr(res, 'recursive', None)
    identical = getattr(res, 'identical', None)
    selected_item = getattr(res, 'item', None)
    recursive = recursive if selected_item else True
    selected_item = abspath(selected_item or getcwd())

    utils.cc_checkx('in', recursive, selected_item, message=message, identical=identical)

parser_ccheckin.set_defaults(func=handler_ccheckin)


# Subparser for: gitcase uncheckout
parser_uncheckout = subparsers.add_parser('uncheckout', aliases=['un'], help='Un-checkout file/dir/recursively in the ClearCase sense.')
parser_uncheckout.add_argument(
    '-r', '--recursive',
    dest='recursive',
    action='store_true',
    default=False,
    help='Apply to all subdirectories and files recursively.'
)
parser_uncheckout.add_argument(
    '-d', '--discard',
    dest='discard',
    action='store_true',
    default=False,
    help='Discard private copy.'
)
parser_uncheckout.add_argument(
    '-k', '--keep',
    dest='keep',
    action='store_true',
    default=False,
    help='Keep private copy.'
)
parser_uncheckout.add_argument(
    'item',
    nargs='?',
    help='File/dir to uncheckout.',
)

def handler_uncheckout(res):
    recursive = getattr(res, 'recursive', None)
    discard = getattr(res, 'discard', None)
    keep = getattr(res, 'keep', None)
    selected_item = getattr(res, 'item', None)
    recursive = recursive if selected_item else True
    selected_item = abspath(selected_item or getcwd())

    utils.cc_checkx('un', recursive, selected_item, keep=(keep or not discard))

parser_uncheckout.set_defaults(func=handler_uncheckout)


# main
def main():
    if len(sys.argv) == 1:
        parser.print_help()
    else:
        res = parser.parse_args()
        res.func(res)


if __name__ == "__main__":
    main()
