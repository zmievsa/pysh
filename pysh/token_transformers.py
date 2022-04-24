from collections import deque, namedtuple
from io import StringIO
import tokenize
from typing import Generator, List, Union
from rich import print

Token = namedtuple("Token", "string type")
MAGICAL_COMMANDS = {"cd"}


def convert_to_shell_var(varname: str) -> str:
    if varname.isdigit():
        return f"{{sys.argv[{varname}]}}"
    elif varname == "#":
        return "{len(sys.argv) - 1}"
    elif varname == "@":
        return "{' '.join(sys.argv[1:])}"
    elif varname == "?":
        return "{__last_bash_cmd_returncode__}"
    else:
        return f"{{os.environ['{varname}'] if '{varname}' in os.environ else {varname}}}"


def convert_to_magical_command(tokens: List[str]) -> str:
    if tokens[0] == "cd":
        argv = "".join(tokens[1:])
        return f"os.chdir(f'{argv}')"
    else:
        raise NotImplementedError(f"Magical command '{tokens}' is not supported")


def modify_tokens(tokens: List[tokenize.TokenInfo]) -> Generator[Union[tokenize.TokenInfo, Token], None, None]:
    bash_line_started = False
    piped_bash_line_started = False
    skip_next_token = False

    cmd_tokens = deque()
    for first, second in zip(tokens, tokens[1:]):
        if skip_next_token and second.type != tokenize.NEWLINE:
            # print("SKIP", first)
            skip_next_token = False
        elif first.string == "!":
            # print("START", first)
            if piped_bash_line_started:
                raise SyntaxError(f'Three "!" in one line are not supported. Problematic line: {first.line}')
            elif bash_line_started:
                piped_bash_line_started = True
            else:
                bash_line_started = True
        elif second.type == tokenize.NEWLINE and bash_line_started:
            # print("END", first)
            if not skip_next_token:
                cmd_tokens.append(first.string)
            if cmd_tokens[0] in MAGICAL_COMMANDS:
                yield Token(tokenize.NAME, convert_to_magical_command(list(cmd_tokens)))
            else:
                cmd = " ".join(cmd_tokens).replace('"', '\\"')
                yield Token(tokenize.NAME, f'''sh(f"""{cmd}""", pipe_stdout={piped_bash_line_started}).stdout''')
            cmd_tokens.clear()
            bash_line_started = piped_bash_line_started = skip_next_token = False
        elif bash_line_started:
            # print("ADD", first)
            if first.string == "$":
                cmd_tokens.append(convert_to_shell_var(second.string))
                skip_next_token = True
            else:
                cmd_tokens.append(first.string)
        else:
            # print("STANDARD", first)
            yield first
    yield tokens[-1]


def transform_source(source, **kwargs):
    tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    source = tokenize.untokenize(modify_tokens(tokens))
    return source
