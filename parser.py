from typing import List, Tuple, Union, Optional

from config import Config
from lexer import TokenType, Token, Lexer, EMPTY_SPACE_TYPES, NON_JSON_TYPES
from syntax_tree import AlexsonNode, Literal, String, Number, Null, Boolean, Variable, Object, Array, \
    NewLine, WhiteSpace, Tab, BlockNode, LBrace, Colon, Comma, RBrace, NonJson, Comment, LBracket, RBracket, Root


class AlexsonParserException(Exception):
    def __init__(self, msg: str, row: int, col: int):
        self.msg = msg
        self.row = row
        self.col = col

    def __str__(self):
        return f'Parsing error at line {self.row}:{self.col}: {self.msg}'


class AlexsonParser:
    def __init__(self, text: str, config: Config = Config()):
        self.text = text
        self.lexer = Lexer(text)
        self.tokens = self.lexer.tokenize()
        self._token_index = 0
        self._current_token = self.tokens[self._token_index] if len(self.tokens) > 0 else None
        self.config = config

    def get_token_pos(self, token: Token) -> Tuple[int, int]:
        if token is None:
            return -1, -1

        return self.lexer.get_token_position(token)

    def parse(self) -> Root:
        node = Root()

        # Return empty block node if the alexson string is empty
        if self.current() is None:
            return node

        # Parse empty spaces before the root object/array node
        node.children.extend(self._parse_non_json())
        # Return empty block node if the alexson string only contains empty spaces
        if self.current() is None:
            return node

        # Parse root object/array node
        if self.current().type == TokenType.LBRACE:
            node.children.append(self._parse_obj())
        elif self.current().type == TokenType.LBRACKET:
            node.children.append(self._parse_array())
        else:
            raise AlexsonParserException(
                f'Unexpected token {self.current()}, expecting Object or Array '
                f'at the top level of the alexson string',
                *self.get_token_pos(self.current()))

        # Parse empty spaces after the root object/array node
        node.children.extend(self._parse_non_json())

        # Check if the alexson string is fully parsed
        assert self.current() is None

        return node

    def _parse_obj(self) -> Object:
        obj = Object()

        if self.current().type != TokenType.LBRACE:
            raise AlexsonParserException(f'Unexpected token {self.current()}, expecting "{{" here.',
                                         *self.get_token_pos(self.current()))

        # Consume '{', add it to the syntax tree
        obj.children.append(LBrace())
        self.advance()

        while self.current().type != TokenType.RBRACE:
            # Parse empty spaces before the key
            obj.children.extend(self._parse_non_json())

            # Parse key
            if self.current().type != TokenType.STRING:
                raise AlexsonParserException(f'Unexpected token {self.current()}', *self.get_token_pos(self.current()))

            key = String(self.current().value)
            obj.children.append(key)
            self.advance()

            # Parse empty spaces after the key
            obj.children.extend(self._parse_non_json())

            # Consume ':'
            if self.current().type != TokenType.COLON:
                raise AlexsonParserException(f'Unexpected token {self.current()}', *self.get_token_pos(self.current()))
            obj.children.append(Colon())
            self.advance()

            # Parse empty spaces before the value
            obj.children.extend(self._parse_non_json())

            # Parse value
            value = self.parse_value()
            obj.children.append(value)

            # Check if the key is already in the dictionary
            if key.get_value() in obj.dict:
                raise AlexsonParserException(f'Duplicate key {key.get_value()}', *self.get_token_pos(self.current()))
            # Add the key-value pair to the dictionary
            obj.dict[key.get_value()] = (key, value)

            # Parse empty spaces after the value
            obj.children.extend(self._parse_non_json())

            # Consume ','
            if self.current().type == TokenType.COMMA:
                obj.children.append(Comma())
                self.advance()
            elif self.current().type != TokenType.RBRACE:
                raise AlexsonParserException(f'Unexpected token {self.current()}', *self.get_token_pos(self.current()))

            # Parse empty spaces after ','
            obj.children.extend(self._parse_non_json())

            # If allow_trailing_comma is True, check if the next token is '}' and break the loop
            if self.config.allow_trailing_comma and self.current().type == TokenType.RBRACE:
                break

        # Consume '}', add it to the syntax tree
        obj.children.append(RBrace())
        self.advance()

        return obj

    def _parse_non_json(self) -> List[NonJson]:
        if self.current() is None:
            return []

        empty_spaces: List[NonJson] = []
        while self.current().type in NON_JSON_TYPES:
            if self.current().type == TokenType.NEWLINES:
                empty_spaces.extend([NewLine()] * len(self.current().value))
            elif self.current().type == TokenType.SPACES:
                empty_spaces.extend([WhiteSpace()] * len(self.current().value))
            elif self.current().type == TokenType.TABS:
                empty_spaces.extend([Tab()] * len(self.current().value))
            elif self.current().type == TokenType.COMMENT and self.config.allow_comments:
                empty_spaces.append(Comment(self.current().value))
            self.advance()
        return empty_spaces

    def _parse_array(self) -> Array:
        array = Array()

        # Consume '[', add it to the syntax tree
        array.children.append(LBracket())
        self.advance()

        while self.current().type != TokenType.RBRACKET:
            # Parse empty spaces before the value
            array.children.extend(self._parse_non_json())

            # Parse value
            value = self.parse_value()
            array.children.append(value)
            array.items.append(value)

            # Parse empty spaces after the value
            array.children.extend(self._parse_non_json())

            # Consume ','
            if self.current().type == TokenType.COMMA:
                array.children.append(Comma())
                self.advance()
            elif self.current().type != TokenType.RBRACKET:
                raise AlexsonParserException(f'Unexpected token {self.current()}, expecting "," or "]" here.',
                                             *self.get_token_pos(self.current()))

        # Consume ']', add it to the syntax tree
        array.children.append(RBracket())
        self.advance()

        return array

    def parse_value(self) -> AlexsonNode:
        value = None
        if self.current().type == TokenType.STRING:
            value = String(self.current().value)
        elif self.current().type == TokenType.NUMBER:
            try:
                # check if the number is a valid float
                float(self.current().value)
                value = Number(self.current().value)
            except ValueError:
                raise AlexsonParserException(f'Invalid number value {self.current().value}',
                                             *self.get_token_pos(self.current()))
        elif self.current().type == TokenType.NULL:
            value = Null()
        elif self.current().type == TokenType.BOOLEAN:
            if self.current().value == 'true':
                value = Boolean(True)
            elif self.current().value == 'false':
                value = Boolean(False)
            else:
                raise AlexsonParserException(f'Invalid boolean value {self.current().value}',
                                             *self.get_token_pos(self.current()))
        elif self.current().type == TokenType.VARIABLE:
            value = Variable(self.current().value)
        # Nested structures
        elif self.current().type == TokenType.LBRACE:
            return self._parse_obj()
        elif self.current().type == TokenType.LBRACKET:
            return self._parse_array()
        else:
            raise AlexsonParserException(f'Unexpected token {self.current()}', *self.get_token_pos(self.current()))

        self.advance()
        return value

    def advance(self) -> Token:
        self._token_index += 1
        self._current_token = self.tokens[self._token_index] if self._token_index < len(self.tokens) else None
        return self._current_token

    def current(self) -> Optional[Token]:
        return self._current_token


if __name__ == '__main__':
    string = ('{\n'
              '    "nav_buoy": {\n'
              '        "baseId": "base_campaign \\"_objective",\n'
              '        "defaultName":"Nav Buoy", # used if name=null in addCustomEntity() \n'
              '        "tags":["nav_buoy", "neutrino_high", "objective"],\n'
              '        "layers":[STATIONS], # what layer(s) to render in. See CampaignEngineLayer for possible values\n'
              '    }\n'
              '}')

    parser = AlexsonParser(string)
    node = parser.parse()

    node['nav_buoy']['defaultName'] = String('导航浮标')
    print(node)

