import unittest

from lexer import Lexer, TokenType, Token


class TestLexer(unittest.TestCase):
    def test_white_spaces(self):
        lexer = Lexer('  ')
        token = lexer.whitespaces()
        self.assertEqual(token, Token(TokenType.SPACES, '  '))

    def test_tabs(self):
        lexer = Lexer('\t\t')
        token = lexer.tabs()
        self.assertEqual(token, Token(TokenType.TABS, '\t\t'))

    def test_newlines(self):
        lexer = Lexer('\n\n')
        token = lexer.newlines()
        self.assertEqual(token, Token(TokenType.NEWLINES, '\n\n'))

    def test_comment(self):
        lexer = Lexer('# hello world \n blablabla')
        token = lexer.comment()
        self.assertEqual(token, Token(TokenType.COMMENT, '# hello world '))

    def test_string(self):
        lexer = Lexer('"I say hello world "blablabla')
        token = lexer.string()
        self.assertEqual(token, Token(TokenType.STRING, 'I say hello world '))

    def test_string_with_escape(self):
        lexer = Lexer('"I say \\"hello world\\""blablabla')
        token = lexer.string()
        self.assertEqual(token, Token(TokenType.STRING, 'I say "hello world"'))

    def test_number(self):
        lexer = Lexer('1234"blabla"')
        token = lexer.number()
        self.assertEqual(token, Token(TokenType.NUMBER, '1234'))

    def test_number_with_decimal(self):
        lexer = Lexer('1234.5678"blabla"')
        token = lexer.number()
        self.assertEqual(token, Token(TokenType.NUMBER, '1234.5678'))

    def test_variable(self):
        lexer = Lexer('STATIONS]123')
        token = lexer.variable()
        self.assertEqual(token, Token(TokenType.VARIABLE, 'STATIONS'))

    def test_boolean(self):
        lexer = Lexer('true false')
        tokens = lexer.tokenize()
        expected = [
            Token(TokenType.BOOLEAN, 'true'),
            Token(TokenType.SPACES, ' '),
            Token(TokenType.BOOLEAN, 'false')
        ]
        self.assertEqual(expected, tokens)

    def test_tokenize_1(self):
        lexer = Lexer('{"key": "value"} # comment bla bla \n')
        tokens = lexer.tokenize()
        expected = [
            Token(TokenType.LBRACE, '{'),
            Token(TokenType.STRING, 'key'),
            Token(TokenType.COLON, ':'),
            Token(TokenType.SPACES, ' '),
            Token(TokenType.STRING, 'value'),
            Token(TokenType.RBRACE, '}'),
            Token(TokenType.SPACES, ' '),
            Token(TokenType.COMMENT, '# comment bla bla '),
            Token(TokenType.NEWLINES, '\n')
        ]
        self.assertEqual(expected, tokens)

    def test_tokenize_2(self):
        lexer = Lexer('{"key": VARIABLE, "key2": "value2"} # comment bla bla \n')
        tokens = lexer.tokenize()
        expected = [
            Token(TokenType.LBRACE, '{'),
            Token(TokenType.STRING, 'key'),
            Token(TokenType.COLON, ':'),
            Token(TokenType.SPACES, ' '),
            Token(TokenType.VARIABLE, 'VARIABLE'),
            Token(TokenType.COMMA, ','),
            Token(TokenType.SPACES, ' '),
            Token(TokenType.STRING, 'key2'),
            Token(TokenType.COLON, ':'),
            Token(TokenType.SPACES, ' '),
            Token(TokenType.STRING, 'value2'),
            Token(TokenType.RBRACE, '}'),
            Token(TokenType.SPACES, ' '),
            Token(TokenType.COMMENT, '# comment bla bla '),
            Token(TokenType.NEWLINES, '\n')
        ]
        self.assertEqual(expected, tokens)