# GitCase
## Git commands for ClearCase

The goal is to have a behavior as similar as possible to the most common git commands while using clearcase.

Some companies keep (typically older) projects in ClearCase, this should make working with them a bit more efficient for git users. The two are fundamentally different and therefore technically they won't be able to behave exactly the same way, so feel free to use the ones that are useful for you and tweak, request or contribute other commands.

<br>

### :information_source: Available equivalent commands:
These commands provide as-close-as possible syntax and functionality to the most used ones in git.

:pushpin: **`gitcase status`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git status` | List all new or modified files. | `cleartool ls -rec -view_only` to get new files. `cleartool lsco -cview -a -s` to get all the checked out files, then find those which have been actually modified with `cleartool diff -predecessor`. |

Available options:

`-u` `--untracked-files` Show untracked files.
* no - Show no untracked files.
* normal - *(default)* Shows untracked files and directories.

`-view` `--whole-view` Show modifications in the whole view, untracked files will be shown for the cwd and subdirs.

`-co` `--checked-out` Show also files that are checked-out but don't have modifications.

`[item]` You can provide a directory or file to get the status of that item alone.

<br>
<br>

:pushpin: **`gitcase diff`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git diff` | Show changes. | `cleartool lsco -cview -a -s`, then `cleartool diff -predecessor` and print the differences. |

`[item]` You can provide a directory or file to get differences on that item alone.

<br>
<br>

:pushpin: **`gitcase clean`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git clean` | Remove untracked files. | `rm -f`, `-r` for the files directories that are not under version control. |

Clean the *current working directory* (recursively).

<br>
<br>

### :information_source: ClearCase-only helper wrappers:
These do not have any git equivalent because they are exclusive to the ClearCase philosophy. The following are git-friendly wrappers that automate repetitive CC tasks:

:pushpin: **`gitcase ccheckout`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| None | Checkout in the ClearCase sense. | `cleartool co -unr -nc` per element, recursively if selected. |

If no parameters are specified, *recursive* from *cwd* will be performed.

`-r` `--recursive` If a directory is provided (defaults to *cwd*), apply to all files and subdirectories recursively.

`[item]` File/dir to ccheckout.

<br>
<br>

:pushpin: **`gitcase ccheckin`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| None | Checkin in the ClearCase sense. | `cleartool ci -c` per element, recursively if selected. |

If no parameters are specified, *recursive* from *cwd* will be performed.

`-m` `--message` Comment or description of the checkin *(made mandatory)*.

`-r` `--recursive` If a directory is provided (defaults to *cwd*), apply to all files and subdirectories recursively.

`-i` `--identical` Checkin even if files are identical.

`[item]` File/dir to ccheckin.

<br>
<br>

:pushpin: **`gitcase uncheckout`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| None | Uncheckout in the ClearCase sense. | `cleartool unco` `-keep` or `-rm` per element, recursively if selected. |

If no parameters are specified, *recursive* from *cwd* will be performed.

`-r` `--recursive` Apply to all subdirectories and files recursively.

`-d` `--discard` Discard private copy.

`-k` `--keep` Keep private copy *(defaults to keep)*.

`[item]` File/dir to uncheckout.
