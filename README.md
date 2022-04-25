# Pysh
Bash is said to be the opposite of riding the bike -- you have to re-learn it every time. So if we're doing anything more complex than running a few commands, chances are google will be needed. But if we switch to python, then the reverse is true -- python is a bit too cumbersome for simple scripts. I try to alleviate this problem by making it easier to use bash from python.

It was inspired by Jupyter's way of handling bash.

## Installation
```bash
pip install pysh-stub
```
## Quickstart
* If you have a hello_world.pysh file with the contents below, you can run it using `pysh hello_world.pysh`:
```bash
!echo Hello World
print("Hello World")
```
* Most bash is going to be one-to-one translatable to pysh by putting exclamation marks at the beginning of each line:
```bash
!ls
!cp some_file some/place
```
* It has most of the variables (\$@, \$#, $1, $2, etc) you would expect:
```bash
!echo $*
```
* You can also access python variables from bash using f-string notation
```bash
my_file = "~/some/file" + ".txt"
!cp {my_file} {my_file + ".bak"}
```
* If you wish to get the output of any command into a python variable, you can use double exclamation mark:
```bash
# Note that the default output of ls is silenced when !! are used
lines = !!ls -lA
for line in lines.splitlines():
    print(line)
```
## Builtins
I consider the most comfortable way to write python scripts is to import os, pathlib, sys, and re first. Thus, all of these modules are pre-imported. However, instead of "pathlib.Path", we have "P". 

I also import typer as I consider it to be the most concise way to write any command line application.

If you wish to customize how you call bash subprocesses, you can use the builtin "sh" function. It supports all the same arguments as subprocess.run but has text=True and shell=True by default.

## Magical Commands
We use subprocess.run to run bash commands but that has a few quirks. If you modify the process info in any way within the subprocess (cd, set, unset, etc), this information will not change for the currently running process. Hence we have a few magical commands that do not create a subprocess but instead use roughly equivalent python constructs.

Here's a list of all the magical commands and the approximate conversions we apply to them:
| Original        | Converted                                 |
| -----------     | -----------                               |
| !cd arg         | os.chdir(arg)                             |
| !set -e         | \_\_pysh_check_returncodes\_\_.set(True)  |
| !set +e         | \_\_pysh_check_returncodes\_\_.set(False) |
| !exit arg       | sys.exit(int(arg))                        |
## Notes on syntax
* Each bash call is parsed until the end of the line so they are closer to statements than expressions. Hence the following is not possible:
```bash
print(!!ls)
```
* Because we use f-strings to interface between python and bash, you will have to escape non-formatting "{" and "}" by typing them twice. You will also have to wrap these characters in quotes because prior to converting bash into executable format, we tokenize the entire file as if it was valid python. I.e. Unclosed braces, parenthesis, etc will cause a tokenize.TokenError.
```bash
# The invalid ways to do it
!echo {
!echo {{

# The valid way to do it
!echo "{{"
```
## FAQ
* If you have any questions, encounter any bugs or want to suggest/contribute new features, please, use the issues in the github repository