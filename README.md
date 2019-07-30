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

`-u` `--untracked` Show untracked files.
* no - Show no untracked files.
* normal - *(default)* Shows untracked files and directories.

`-v` `--view` Show modifications in the whole view, untracked files will be shown for the cwd and subdirs.

`-co` `--checked-out` Show also files that are checked-out but don't have modifications.

`[item]` You can provide a directory or file to get the status of that item alone.

<br>
<br>

:pushpin: **`gitcase diff`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git diff` | Show changes. | `cleartool lsco -cview -a -s`, then `cleartool diff -predecessor` and print the differences. |

`-g` `--graphical` Open differences in GUI (if any).

`[item]` You can provide a directory or file to get differences on that item alone.

<br>
<br>

:pushpin: **`gitcase log`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git log` | Show change history. | Wrap `cleartool lshist`, `lshist -graphical` and `xlsvtree`. |

`-l` `--lines` *(optional)* Number of lines of history to print (default 15).

`-r` `--recursive` Apply recursively going into subdirectories.

`-g` `--graphical` Open history in GUI.

`-t` `--tree` Open history in visual tree.

`[item]` You can provide a directory or file to get the history of that item alone.

<br>
<br>

:pushpin: **`gitcase clean`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git clean` | Remove untracked files. | `rm -f`, `-r` for the files directories that are not under version control. |

Clean the *current working directory* (recursively). By default it will only remove files ending with *~*, *.keep* or *.contrib*.

`-a` `--clean_all` Remove ALL untracked.

<br>
<br>

### :information_source: ClearCase-only helper wrappers:
These do not have any git equivalent because they are exclusive to the ClearCase philosophy. The following are git-friendly wrappers that automate repetitive CC tasks:

:pushpin: **`gitcase ccheckout`**

| description | clearcase actions |
| --- | --- |
| Checkout in the ClearCase sense. | `cleartool co -unr -nc` per element, recursively if selected. |

If no parameters are specified, *recursive* from *cwd* will be performed.

`-r` `--recursive` If a directory is provided (defaults to *cwd*), apply to all files and subdirectories recursively.

`-e` `--edit` Open checked-out file in the editor defined by `$EDITOR` environment variable.

`[item]` File/dir to ccheckout.

<br>
<br>

:pushpin: **`gitcase ccheckin`**

| description | clearcase actions |
| --- | --- |
| Checkin in the ClearCase sense. If the file does not exist in ClearCase it will checkout the directory that contains it, create the element, check it in and check in the directory. | `cleartool ci -c` per element, recursively if selected. If the file is not in ClearCase yet, `cleartool mkelem` and checkout/checkin for the directory that contains it too. |

If no parameters are specified, *recursive* from *cwd* will be performed.

`-m` `--message` Comment or description of the checkin *(made mandatory)*.

`-r` `--recursive` If a directory is provided (defaults to *cwd*), apply to all files and subdirectories recursively.

`-u` `--untracked` In `--recursive` mode, also check-in new files. It will ignore files ending with *~*, *.keep* or *.contrib*.

`-i` `--identical` Checkin even if files are identical.

`[item]` File/dir to ccheckin.

<br>
<br>

:pushpin: **`gitcase uncheckout`**

| description | clearcase actions |
| --- | --- |
| Uncheckout in the ClearCase sense. | `cleartool unco` `-keep` or `-rm` per element, recursively if selected. |

If no parameters are specified, *recursive* from *cwd* will be performed.

`-r` `--recursive` Apply to all subdirectories and files recursively.

`-k` `--keep` Keep private copy *(defaults to False)*.

`[item]` File/dir to uncheckout.

<br>
<br>

:pushpin: **`gitcase diffcs`**

| description | clearcase actions |
| --- | --- |
| Find which files are selected by one cs file and not the other, and also files selected in both but with different versions. Also display if you have local changes. | `cleartool catcs` to save the current cs, `cleartool ls -r` to get the version and rule of each file, `cleartool setcs` on the cs file to compare, get versions and rules of the second cs file; and compare the results. |

If no parameters are provided, it will diff your current cs against your last saved user cs file. Otherwise you can diff against another view's current cs, another file, or between two files.

`-f` `--files` Diff the actual CS files, instead of the list of files and versions selected by them.

`-d` `--directory` Perform the file comparison in the provided directory, instead of the *current working directory*.

`-b` `--block` Block name (to diff against a block configspec).

`-v` `--view` Provided a view name to compare against it's current cs instead of a cs file.

`-g` `--gen_rules` Generate cs rules so that you get the same versions as others.

`[csfile(s)]` Config-spec file to diff against current one / two cs files to be diff'ed (not required if `--view`).

<br>
<br>

:pushpin: **`gitcase savecs`**

| description | clearcase actions |
| --- | --- |
| Save your current configspec in clearcase. | If your block directory can be automatically found, it will be checked-in under `blockname/cs`, otherwise you can always provide the full destination save path.|

Configspec files location:
* `$PROJVOB/src/blockname*/cs*` *Shared configspec files* (i.e to be used per team, per release...)
* `$PROJVOB/src/blockname*/cs/user*` *Default* save location for cs files if a *shared cs* file name is not provided. *The name of the cs file will be the same as the name of your view.*

`-b` `--block` Specify block (needed if it can not be automatically identified because you are not working inside the block file-tree, or want to save the cs in a different block). Destination path will be *src/`blockname`/cs* .

`-m` `--message` Comment or description (mandatory for shared cs files).

`-p` `--absolute-path` Absolute path where the cs file will be saved (ignore blockname/cs structure and file name).

`-f` `--force` By default LATEST is not allowed in your CS, and identical versions are not checked in. Use this to override that behavior.

`[cs-file-name]` Name of a shared configspec to save to.


<br>
<br>

:pushpin: **`gitcase setcs`**

| description | clearcase actions |
| --- | --- |
| Apply the provided cs in your view. | Identify the source for the cs content and apply it using `cleartool setcs`. |

`-b` `--block` Specify block (needed if it can not be automatically identified because you are not working inside the block file-tree, or want to take the cs from a different block). Source path will be *src/`blockname`/cs* .

`-k` `--backup` Save current CS in a backup file before applying the new CS.

`[cs-file]` Name or path of the configspec to apply.
