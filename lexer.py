# The lexical analyzer for a custom json-like language.
from enum import Enum
from typing import List, Optional, Tuple, Dict


class TokenType(Enum):
    # Literal
    STRING = 1
    NUMBER = 2
    BOOLEAN = 3
    NULL = 5
    VARIABLE = 12
    # Non-editable
    LBRACE = 6
    RBRACE = 7
    LBRACKET = 8
    RBRACKET = 9
    COLON = 10
    COMMA = 11
    COMMENT = 13
    # Text format
    NEWLINES = 14
    SPACES = 15
    TABS = 16


LITERAL_TYPES = {TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL, TokenType.VARIABLE}
NON_EDITABLE_TYPES = {TokenType.LBRACE, TokenType.RBRACE, TokenType.LBRACKET, TokenType.RBRACKET, TokenType.COLON,
                      TokenType.COMMA, TokenType.COMMENT, TokenType.NEWLINES, TokenType.SPACES, TokenType.TABS}
NON_JSON_TYPES = {TokenType.COMMENT, TokenType.NEWLINES, TokenType.SPACES, TokenType.TABS}
EMPTY_SPACE_TYPES = {TokenType.SPACES, TokenType.TABS, TokenType.NEWLINES}

# define tokens
class Token:
    def __init__(self, type: TokenType, value: str):
        self.type: TokenType = type
        self.value: str = value

    def __str__(self):
        if self.type in [TokenType.COLON, TokenType.LBRACE, TokenType.RBRACE, TokenType.LBRACKET, TokenType.RBRACKET,
                         TokenType.COMMA]:
            return f'{self.type.name}'
        elif self.type in [TokenType.SPACES, TokenType.TABS]:
            return f'{self.type.name}*{len(self.value)}'
        elif self.type == TokenType.NEWLINES:
            return f'{self.type.name}{self.value}'
        return f'{self.type.name}({self.value})'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        return False

    def __hash__(self):
        return hash((self.type, self.value))


class AlexsonLexicalError(Exception):
    def __init__(self, msg: str, row: int, col: int):
        self.msg = msg
        self.row = row
        self.col = col

    def __str__(self):
        return f'Lexical error at line {self.row}:{self.col}: {self.msg}'


class Lexer:
    def __init__(self, text: str):
        self.text: str = text
        self.pos: int = 0
        self.row: int = 1
        self.col: int = 0
        self.current_char: Optional[str] = self.text[self.pos] if len(self.text) > 0 else None
        self.token_id_position_map: Dict[int, Tuple[int, int]] = {}

    def error(self, msg=''):
        raise AlexsonLexicalError(msg, self.row, self.col)

    def _next(self) -> None:
        self.pos += 1

        if self.pos == len(self.text):
            self.current_char = None  # Indicates end of input
        elif self.pos > len(self.text):
            self.error('End of input')
        else:
            self.current_char = self.text[self.pos]

        if self.current_char == '\n':
            self.row += 1
            self.col = 0
        else:
            self.col += 1

    def next(self, length: int = 1):
        for i in range(length):
            self._next()

    def peek(self, length: int = 1) -> Optional[str]:
        peek_pos = self.pos + length
        if peek_pos >= len(self.text):
            return None
        else:
            return self.text[self.pos + 1:peek_pos + 1]

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while self.current_char is not None:
            token = self.next_token()
            if token is not None:
                tokens.append(token)
        return tokens

    def next_token(self) -> Optional[Token]:
        token = None
        if self.current_char is not None:
            if self.current_char == 't' and self.peek(3) == 'rue':
                token = Token(TokenType.BOOLEAN, 'true')
                self.next(4)
            elif self.current_char == 'f' and self.peek(4) == 'alse':
                token = Token(TokenType.BOOLEAN, 'false')
                self.next(5)
            elif self.current_char == 'n' and self.peek(3) == 'ull':
                token = Token(TokenType.NULL, 'null')
                self.next(4)
            elif self.current_char == '"':
                token = self.string()
            elif self.current_char == '#':
                token = self.comment()
            elif self.current_char == '\n':
                token = self.newlines()
            elif self.current_char == '\t':
                token = self.tabs()
            elif self.current_char == ' ':
                token = self.whitespaces()
            elif self.current_char == '{':
                self.next()
                token = Token(TokenType.LBRACE, '{')
            elif self.current_char == '}':
                self.next()
                token = Token(TokenType.RBRACE, '}')
            elif self.current_char == '[':
                self.next()
                token = Token(TokenType.LBRACKET, '[')
            elif self.current_char == ']':
                self.next()
                token = Token(TokenType.RBRACKET, ']')
            elif self.current_char == ':':
                self.next()
                token = Token(TokenType.COLON, ':')
            elif self.current_char == ',':
                self.next()
                token = Token(TokenType.COMMA, ',')
            elif self.current_char.isalpha() or self.current_char == '_':
                token = self.variable()
            elif self.current_char.isdigit():
                token = self.number()
            else:
                self.error(f'Unexpected character {self.current_char}')

        # Record the position of the token
        if token is not None:
            self.token_id_position_map[id(token)] = (self.row, self.col)

        return token

    def get_token_position(self, token: Token) -> Optional[Tuple[int, int]]:
        return self.token_id_position_map.get(id(token), None)

    def whitespaces(self) -> Token:
        value = ''
        while self.current_char is not None and self.current_char == ' ':
            value += self.current_char
            self.next()
        return Token(TokenType.SPACES, value)

    def tabs(self) -> Token:
        value = ''
        while self.current_char is not None and self.current_char == '\t':
            value += self.current_char
            self.next()
        return Token(TokenType.TABS, value)

    def newlines(self) -> Token:
        value = ''
        while self.current_char is not None and self.current_char == '\n':
            value += self.current_char
            self.next()
        return Token(TokenType.NEWLINES, value)

    def comment(self) -> Token:
        comment = ''
        while self.current_char is not None and self.current_char != '\n':
            comment += self.current_char
            self.next()
        return Token(TokenType.COMMENT, comment)

    def string(self) -> Token:
        string = ''
        escaped = False

        # skip the initial quote
        self.next()
        # read the string
        while self.current_char is not None and not (self.current_char == '"' and not escaped):

            # check if the current character is escaped
            if self.current_char == '\\':
                escaped = True
            else:
                escaped = False
                string += self.current_char

            self.next()
        # skip the final quote
        self.next()
        return Token(TokenType.STRING, string)

    def number(self) -> Token:
        number = ''
        while self.current_char is not None and self.current_char.isdigit() or self.current_char == '.':
            number += self.current_char
            self.next()
        return Token(TokenType.NUMBER, number)

    def variable(self) -> Token:
        variable = self.current_char
        self.next()

        while self.current_char is not None and (
                self.current_char.isalpha() or self.current_char.isdigit() or self.current_char == '_'):
            variable += self.current_char
            self.next()
        return Token(TokenType.VARIABLE, variable)


if __name__ == '__main__':
    lexer = Lexer('''{
 	   "nav_buoy":{
			"baseId":"base_campaign \\"_objective",
			"defaultName":"导航浮标", # used if name=null in addCustomEntity()   
			"tags":["nav_buoy", "neutrino_high", "objective"],   
			"layers":[STATIONS], # what layer(s) to render in. See CampaignEngineLayers.java for possible values
		}
	}''')
    print(' '.join([str(token) for token in lexer.tokenize()]))
    print(lexer.token_id_position_map)
