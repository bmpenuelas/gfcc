# gfcc
## git flavoured ClearCase

*gfcc* provides a layer of automation on top of ClearCase. The goal is twofold: speed-up working with cc, and provide additional checks for a more robust workflow.

Some companies keep projects in **ClearCase** while most people currently prefer **git**, *gfcc* should also make working with them a bit more efficient for git users through emulation of some of the most-used git commands.

<br>
<br>

#### Install:
* Easiest *(requires internet connection)*:

    `pip3 install gfcc`

* Manual:

    Download or clone the project, and run `pip3 install --user -e .` inside the `/gfcc` directory, at the same level as `setup.py` (not inside /gfcc/gfcc).

Now you can type `gfcc` add access all the commands.

(In more restrictive environments you might need to run it as `python3 -m gfcc` and create an alias like `alias gfcc="python3 -m gfcc"` if using the *bash* shell or `alias gfcc 'python3 -m gfcc'` if using *csh* or *tcsh* )

<br>
<br>

### :information_source: git-like commands:
These commands provide as-close-as-possible syntax and functionality to the most used ones in git.


:pushpin: **`gfcc status`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git status` | List all new or modified files. | `cleartool ls -rec -view_only` to get new files. `cleartool lsco -cview -a -s` to get all the checked out files, then find those which have been actually modified with `cleartool diff -predecessor`. |

Available options:

`-u` `--untracked` Show untracked files.
* no - Show no untracked files.
* normal - *(default)* Shows untracked files and directories.

`-v` `--view` Show modifications in the whole view, untracked files will be shown for the cwd and subdirs.

`-co` `--checked-out` Show also files that are checked-out but don't have modifications.

`[item(s)]` You can provide one (or more) directory or file to get the status of that item(s) alone.

<br>
<br>

:pushpin: **`gfcc setcs`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git checkout` |  Apply the provided cs in your view. | Identify the appropriate source for the cs content and apply it using `cleartool setcs`. |

Used in conjunction with `gfcc savecs` to track development across several files, this command emulates `git checkout`.

With due respect to the inevitable differences, the name of the shared configspec file can be seen as the branch name, and each version of that configspec reflects the evolution of the included files with time, as the history of commits does in git. Using `gfcc setcs <name>` will get you the files as stated in the latest version of *<name>.cs*, and using `gfcc setcs <name>@@/other/version` will get you the files selected in that earlier point in time; similarly to *git checkout <branch_name>* and *git checkout <older_commit_sha>*.


`-b` `--block` Specify block (needed if it can not be automatically identified because you are not working inside the block file-tree, or want to take the cs from a different block). Source path will be *src/`blockname`/cs* .

`-v` `--view` Copy the current CS in another view to this one.

`-k` `--backup` Save current CS in a backup file before applying the new CS.

`[cs-file]` Name or path of the configspec to apply.

<br>
<br>

:pushpin: **`gfcc diff`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git diff` | Show changes. | `cleartool lsco -cview -a -s`, then `cleartool diff -predecessor` and print the differences. |

`-g` `--graphical` Open differences in GUI (if any).

`[item(s)]` You can provide a directory or file to get differences on that item (s) alone.

<br>
<br>

:pushpin: **`gfcc log`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git log` | Show change history. | Wrap `cleartool lshist`, `lshist -graphical` and `xlsvtree`. |

`-l` `--lines` *(optional)* Number of lines of history to print (default 15).

`-r` `--recursive` Apply recursively going into subdirectories.

`-g` `--graphical` Open history in GUI.

`-t` `--tree` Open history in visual tree.

`[item(s)]` You can provide one or more directory or file to get the history of that item(s) alone.

<br>
<br>

:pushpin: **`gfcc clean`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git clean` | Remove untracked files. | `rm -f`, `-r` for the files directories that are not under version control. |

Clean the *current working directory* (recursively). By default it will only remove files ending with *~*, *.keep* or *.contrib*.

`-a` `--clean_all` Remove ALL untracked.

`[item(s)]` Clean the provided directory or directories, (defaults to the *current working directory*).

<br>
<br>

### :information_source: ClearCase automation commands:
These do not have any git equivalent because they are exclusive to the ClearCase philosophy, they automate repetitive CC tasks or provide additional automated checks:


:pushpin: **`gfcc checkout`**

| description | clearcase actions |
| --- | --- |
| Checkout in the ClearCase sense. | `cleartool co -unr -nc -version` per element, recursively if selected. |

If no parameters are specified, *recursive* from *cwd* will be performed. It will checkout the version that is selected by your configspec, or the version that you provide with *@@/branch/version*.

`-r` `--recursive` If a directory is provided (defaults to *cwd*), apply to all files and subdirectories recursively.

`-e` `--edit` Open checked-out file in the editor defined by the `$EDITOR` environment variable.

`[item(s)]` File(s)/dir(s) to checkout.

<br>
<br>

:pushpin: **`gfcc checkin`**

| description | clearcase actions |
| --- | --- |
| Checkin in the ClearCase sense. If the file does not exist in ClearCase it will checkout the directory that contains it, create the element, check it in and check in the directory. | `cleartool ci -c` per element, recursively if selected. If the file is not in ClearCase yet, `cleartool mkelem` and checkout/checkin for the directory that contains it too. |

If no parameters are specified, *recursive* from *cwd* will be performed. If the file does not exist in clearcase yet, the element will automatically be created and checked-in.

`-m` `--message` Comment or description of the checkin *(made mandatory)*.

`-r` `--recursive` If a directory is provided (defaults to *cwd*), apply to all files and subdirectories recursively.

`-u` `--untracked` In `--recursive` mode, also check-in new files. It will ignore files ending with *~*, *.keep* or *.contrib*.

`-i` `--identical` Checkin even if files are identical.

`[item(s)]` File(s)/dir(s) to checkin.

<br>
<br>

:pushpin: **`gfcc uncheckout`**

| description | clearcase actions |
| --- | --- |
| Uncheckout in the ClearCase sense. | `cleartool unco` `-keep` or `-rm` per element, recursively if selected. |

If no parameters are specified, *recursive* from *cwd* will be performed.

`-r` `--recursive` Apply to all subdirectories and files recursively.

`-k` `--keep` Keep private copy *(defaults to False)*.

`[item(s)]` File(s)/dir(s) to uncheckout.

<br>
<br>

:pushpin: **`gfcc find`**

| description | clearcase actions |
| --- | --- |
| Show lists of items of interest. | Combine and filter several `cleartool find` and `cleartool ls` to find the desired sets of files. |

`-l` `--latest` Find files selected by rule /LATEST (ignores *.cs* files).

`-nl` `--not-latest` Find files for which a newer version exists.

`-v` `--view` Perform the search based on the current cs of another view.

`-d` `--directory` Perform the search in the provided directory.

<br>
<br>

:pushpin: **`gfcc difflabels`**

| description | clearcase actions |
| --- | --- |
| Diff the files selected by two different labels. | Apply find for both labels and compare the results. |

`-d` `--directory` Show diffs only in the provided directory or directories, (defaults to *any directory*).

`labels` Provide the two labels to diff against each other.

<br>
<br>

:pushpin: **`gfcc diffcs`**

| description | clearcase actions |
| --- | --- |
| Find which files are selected by one cs file and not the other, and also files selected in both but with different versions. Also display if you have local changes. | `cleartool catcs` to save the current cs, `cleartool ls -r` to get the version and rule of each file, `cleartool setcs` on the cs file to compare, get versions and rules of the second cs file; and compare the results. |

If no parameters are provided, it will diff your current cs against your last saved user cs file. Otherwise you can diff against another view's current cs, another file, or between two files.

`-f` `--files` Diff the actual CS files, instead of the list of files and versions selected by them.

`-d` `--directory` Perform the comparison in the provided directory or directories, (defaults to the *current working directory*).

`-b` `--block` Block name (to diff against a block configspec).

`-v` `--view` Provide a view name to compare against it's current cs instead of a cs file.

`-g` `--gen_rules` Generate cs rules so that you get the same versions as others.

`[csfile(s)]` Config-spec file to diff against current one / two cs files to be diff'ed (not required if `--view`).

<br>
<br>

:pushpin: **`gfcc savecs`**

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

:pushpin: **`gfcc codereview`**

| description | clearcase actions |
| --- | --- |
| Create, share and review sets of code changes. | Save CS files with "old" and "new" status. When shared, open diffs for the chosen files. |

`-c` `--create` Set this to **create** a new code review. The *default* behaviour is to **review** the provided one.

`-b` `--block` Specify block (needed if it can not be automatically identified because you are not working inside the block file-tree, or want to take the cs from a different block). Source path will be *src/`blockname`/cs* .

`-o` `--old_cs` CS file with the old, original, status.

`-n` `--new_cs` CS file with the new status.

`[name]` Name for/of this code review.

<br>

Most used combinations:

`gfcc codereview [name]` Will start the review of *name*.

<br>

`gfcc codereview --create` Creates a code review where the last version of your user cs is the *new* state, and the one previous to that is the *old* state.

`gfcc codereview --create [shared_cs_name]` If you provide the name of a shared CS file, the last version of your user cs is the *new* state, and the latest version of *shared_cs_name* is the *old* state.

`gfcc codereview --create --old_cs <old_cs_file_path> --new_cs <new_cs_file_path> [name]` Create a code review explicitly providing the path to two cs files.
