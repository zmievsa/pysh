import re
import tokenize
from collections import namedtuple
from io import StringIO
from typing import Any, Generator, List, Optional, Tuple, Union

try:
    from rich import print as pprint
except ImportError:
    pass


def pprint(*a, **kw):
    pass


"""
char *special_builtins[] =
{
  ":", ".", "source", "break", "continue", "eval", "exec", "exit",
  "export", "readonly", "return", "set", "shift", "times", "trap", "unset",
  (char *)NULL
};

/* The builtin commands that take assignment statements as arguments. */
char *assignment_builtins[] =
{
  "alias", "declare", "export", "local", "readonly", "typeset",
  (char *)NULL
};

char *localvar_builtins[] =
{
  "declare", "local", "typeset", (char *)NULL
};

/* The builtin commands that are special to the POSIX search order. */
char *posix_builtins[] =
{
  "alias", "bg", "cd", "command", "false", "fc", "fg", "getopts", "jobs",
  "kill", "newgrp", "pwd", "read", "true", "umask", "unalias", "wait",
  (char *)NULL
};
"""


SIMPLE_MAGICAL_COMMANDS = {"cd": 'os.chdir(f"{argv}")'}
COMPLEX_MAGICAL_COMMANDS = {"set", "exit"}
RE_SHELLVAR = re.compile(r"(?<!\\)\$[\w@#]+")


def convert_to_shell_var(varname: str) -> str:
    if varname.isdigit():
        return f"{{sys.argv[{varname}] if len(sys.argv) > int({varname}) else __raise_exception__(IndexError('Command line argument ${varname} was not passed'))}}"
    elif varname == "#":
        return "{len(sys.argv) - 1}"
    elif varname == "@":
        return "{' '.join(sys.argv[1:])}"
    elif varname == "?":
        return "{__last_bash_cmd_returncode__}"
    elif varname == "$":
        return "{os.getpid()}"
    else:
        return f"{{os.environ['{varname}']}}"


def convert_to_magical_command(cmd: str, argv: str) -> Optional[str]:
    if cmd in SIMPLE_MAGICAL_COMMANDS:
        return SIMPLE_MAGICAL_COMMANDS[cmd].format(cmd=cmd, argv=argv)
    elif cmd in COMPLEX_MAGICAL_COMMANDS:
        if cmd == "set" and argv.startswith(("+e", "-e")):
            return f'__pysh_check_returncodes__.set({argv.startswith("-e")})'
        elif cmd == "exit":
            if not argv:
                argv = "0"
            if not argv.isdigit():
                raise SyntaxError(
                    f"only integer arguments for the exit command are supported. Problematic command: {cmd} {argv}"
                )
            return f"sys.exit({int(argv)})"


def modify_tokens(tokens: List[tokenize.TokenInfo]) -> Generator[Tuple[int, str], None, None]:
    bash_line_started = False
    piped_bash_line_started = False
    cmd = None
    for i, token in enumerate(tokens):
        if bash_line_started:
            if token.type == tokenize.NEWLINE:
                if cmd is None:
                    raise SyntaxError(f"Unknown syntax error on line: {token.line}")
                prev_token = tokens[i - 1]
                sep = "!!" if piped_bash_line_started else "!"
                _, _, argv = prev_token.line.partition(sep + cmd)
                argv = argv.replace('"', '\\"').strip()
                for var in set(RE_SHELLVAR.findall(argv)):
                    argv = argv.replace(var, convert_to_shell_var(var[1:]))
                magical_command = convert_to_magical_command(cmd, argv.strip())
                if magical_command is not None:
                    yield tokenize.NAME, magical_command
                else:
                    command = f'''sh(f"""{cmd} {argv}""", pipe_stdout={piped_bash_line_started}).stdout'''
                    yield tokenize.NAME, command
                bash_line_started = piped_bash_line_started = False
                cmd = None
                yield token[:2]
            elif token.string == "!":
                if piped_bash_line_started:
                    raise SyntaxError(f'Three "!" in one line are not supported. Problematic line: {token.line}')
                else:
                    pprint("PIPE", token)
                    piped_bash_line_started = True
            elif cmd is None:
                pprint("CMD", token)
                cmd = token.string
            else:
                pprint("ADD", token)
        elif token.string == "!":
            pprint("START", token)
            bash_line_started = True
        else:
            pprint("STANDARD", token)
            yield token[:2]


def transform_source(source: str, **kwargs: Any) -> str:
    tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    tokens = list(modify_tokens(tokens))
    for tok in tokens:
        pprint(tok)
    source = tokenize.untokenize(tokens)
    pprint(source)
    return source
