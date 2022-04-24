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
    convert_next_token_to_shell_cmd = False

    cmd_tokens = deque()
    for token in tokens:
        if convert_next_token_to_shell_cmd:
            cmd_tokens.append(convert_to_shell_var(token.string))
            convert_next_token_to_shell_cmd = False
        elif token.string == "!":
            # print("START", token)
            if piped_bash_line_started:
                raise SyntaxError(f'Three "!" in one line are not supported. Problematic line: {token.line}')
            elif bash_line_started:
                piped_bash_line_started = True
            else:
                bash_line_started = True
        elif token.type == tokenize.NEWLINE and bash_line_started:
            if cmd_tokens[0] in MAGICAL_COMMANDS:
                yield Token(tokenize.NAME, convert_to_magical_command(list(cmd_tokens)))
            else:
                cmd = " ".join(cmd_tokens).replace('"', '\\"')
                yield Token(tokenize.NAME, f'''sh(f"""{cmd}""", pipe_stdout={piped_bash_line_started}).stdout''')
            cmd_tokens.clear()
            bash_line_started = piped_bash_line_started = False
            yield token
        elif bash_line_started:
            # print("ADD", token)
            if token.string == "$":
                convert_next_token_to_shell_cmd = True
            else:
                cmd_tokens.append(token.string)
        else:
            # print("STANDARD", token)
            yield token
    yield tokens[-1]


def transform_source(source, **kwargs):
    tokens = list(tokenize.generate_tokens(StringIO(source).readline))
    source = tokenize.untokenize(modify_tokens(tokens))
    # print(source)
    return source
