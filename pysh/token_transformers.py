from collections import namedtuple
from io import StringIO
import re
import tokenize
from typing import Any, Generator, List, Union

try:
    from rich import print as pprint
except ImportError:
    pass


def pprint(*a, **kw):
    pass


Token = namedtuple("Token", "string type")
MAGICAL_COMMANDS = {"cd": "os.chdir(f'{argv}')"}
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
        return f"{{os.environ['{varname}'] if '{varname}' in os.environ else {varname}}}"


def convert_to_magical_command(cmd: str, argv: str) -> str:
    if cmd == "cd":
        return f"os.chdir(f'{argv}')"
    else:
        raise NotImplementedError(f"Magical command '{cmd}' is not supported")


def modify_tokens(tokens: List[tokenize.TokenInfo]) -> Generator[Union[tokenize.TokenInfo, Token], None, None]:
    bash_line_started = False
    piped_bash_line_started = False
    cmd = None
    for i, token in enumerate(tokens):
        if bash_line_started:
            if token.type == tokenize.NEWLINE:
                if cmd is None:
                    raise SyntaxError(f"Unknown syntax error on line: {token.line}")
                prev_token = tokens[i - 1]
                argv = prev_token.line[prev_token.line.rindex("!" + cmd) + len(cmd) + 1 :]
                argv = argv.replace('"', '\\"').rstrip("\n")
                for var in set(RE_SHELLVAR.findall(argv)):
                    argv = argv.replace(var, convert_to_shell_var(var[1:]))
                if cmd in MAGICAL_COMMANDS:
                    yield Token(tokenize.NAME, MAGICAL_COMMANDS[cmd].format(cmd=cmd, argv=argv.strip()))
                else:
                    yield Token(
                        tokenize.NAME,
                        f'''sh(f"""{cmd} {argv}""", pipe_stdout={piped_bash_line_started}).stdout''',
                    )
                bash_line_started = piped_bash_line_started = False
                cmd = None
                yield token
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
            yield token


def transform_source(source: str, **kwargs: Any) -> str:
    tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    source = tokenize.untokenize(modify_tokens(tokens))
    pprint(source)
    return source
