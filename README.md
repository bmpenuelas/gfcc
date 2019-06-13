# GitCase
### Git commands for ClearCase

The goal is to have a behavior as similar as possible to the most common git commands while using clearcase.

The two are fundamentally different and therefore technically they won't be able to behave exactly the same way, so feel free to use the ones that are useful for you and tweak, request or contribute other commands.

<br>

#### :information_source: Available commands:

:pushpin: **`gitcase status`**

| git equivalent | description | clearcase actions |
| --- | --- | --- |
| `git status` | List all new or modified files. | `cleartool lsprivate` to get new files. `cleartool lsco -cview -a -s` to get all the checked out files, then find those which have been actually modified with `cleartool diff -predecessor`. |
