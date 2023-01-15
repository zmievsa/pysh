# pysh

A library of small functions that simplify scripting in python

## Installation

```bash
pip install pysh
```

## Usage

### sh

Run a shell command and display the output:

```python
sh("git status")
```

Capture the output of a shell command:

```python
res = sh("git status", capture=True)
print(res.stdout)
```

### cd

Change the current working directory:

```python
cd("path/to/dir")
```

Change the current working directory temporarily:

```python
with cd("path/to/dir"):
    sh("git status")
```

### env

Set an environment variable:

```python
env(var="value")
```

Set an environment variable temporarily:

```python
with env(PGPASSWORD="MyPassword", PGUSER="postgres"):
    sh("createdb -h localhost -p 5432 -O postgres mydb")
```

### which

Checks whether an executable/script/builtin is available:

```python
git_is_installed = which("git")
```
