# pysh

A library of small functions that simplify scripting in python

## Installation

```bash
pip install pysh
```

## Usage

```python
from pysh import sh, cd, env, which

sh("git status") # will display the output of git status
res = sh("git status", capture=True) # will capture stdout and stderr of git status
print(res.stdout) # will print stdout of git status


cd("path/to/dir") # will change the current working directory to path/to/dir
with cd("path/to/dir"): # will change the current working directory to path/to/dir and then change it back to the original directory
    sh("git status")


env(var="value") # will set the environment variable var to value
with env(PGPASSWORD="MyPassword"): # will set the environment variable PGPASSWORD to MyPassword and then set it back to the original value
    sh("createdb -U postgres -h localhost -p 5432 -O postgres mydb")


which("git") # will return the path to the git executable or None if git is not installed

```
