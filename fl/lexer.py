from fl.tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"Lexer error at {line}:{col}: {message}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str, filename: str = "<stdin>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def error(self, msg: str):
        raise LexerError(msg, self.line, self.col)

    def peek(self, offset: int = 0) -> str:
        p = self.pos + offset
        if p < len(self.source):
            return self.source[p]
        return '\0'

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.advance()
            return True
        return False

    def make_token(self, type: TokenType, value, line: int, col: int, pos: int) -> Token:
        return Token(type, value, line, col, pos)

    def skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in (' ', '\t', '\r'):
            self.advance()

    def skip_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.advance()

    def read_string(self) -> Token:
        line, col, pos = self.line, self.col, self.pos
        self.advance()  # skip opening "
        result = []
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == '"':
                self.advance()
                return self.make_token(TokenType.STRING, ''.join(result), line, col, pos)
            if ch == '\\':
                self.advance()
                if self.pos >= len(self.source):
                    self.error("Unterminated string escape")
                esc = self.advance()
                if esc == 'n':
                    result.append('\n')
                elif esc == 't':
                    result.append('\t')
                elif esc == 'r':
                    result.append('\r')
                elif esc == '\\':
                    result.append('\\')
                elif esc == '"':
                    result.append('"')
                elif esc == '0':
                    result.append('\0')
                else:
                    result.append('\\')
                    result.append(esc)
            elif ch == '\n':
                self.error("Unterminated string literal")
            else:
                result.append(self.advance())
        self.error("Unterminated string literal")

    def read_number(self) -> Token:
        line, col, pos = self.line, self.col, self.pos
        start = self.pos
        is_float = False
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.advance()
        if self.pos < len(self.source) and self.source[self.pos] == '.':
            next_ch = self.peek(1)
            if next_ch.isdigit():
                is_float = True
                self.advance()  # skip .
                while self.pos < len(self.source) and self.source[self.pos].isdigit():
                    self.advance()
        text = self.source[start:self.pos]
        if is_float:
            return self.make_token(TokenType.FLOAT, float(text), line, col, pos)
        else:
            return self.make_token(TokenType.INT, int(text), line, col, pos)

    def read_identifier(self) -> Token:
        line, col, pos = self.line, self.col, self.pos
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.advance()
        text = self.source[start:self.pos]
        token_type = KEYWORDS.get(text, TokenType.IDENT)
        return self.make_token(token_type, text, line, col, pos)

    def extract_raw_block(self) -> str:
        """Extract raw text inside { } for native blocks, tracking nesting."""
        depth = 1
        start = self.pos
        while self.pos < len(self.source) and depth > 0:
            ch = self.source[self.pos]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    raw = self.source[start:self.pos]
                    self.advance()  # skip closing }
                    return raw
            if ch == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1
        self.error("Unterminated native block")

    def tokenize(self) -> list[Token]:
        tokens = []
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.source[self.pos]
            line, col, pos = self.line, self.col, self.pos

            # Newline
            if ch == '\n':
                self.advance()
                tokens.append(self.make_token(TokenType.NEWLINE, '\\n', line, col, pos))
                continue

            # Comment
            if ch == '#':
                self.skip_comment()
                continue

            # String
            if ch == '"':
                tokens.append(self.read_string())
                continue

            # Number
            if ch.isdigit():
                tokens.append(self.read_number())
                continue

            # Identifier / keyword
            if ch.isalpha() or ch == '_':
                tokens.append(self.read_identifier())
                continue

            # Operators and delimiters
            if ch == '+':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.PLUS_ASSIGN, '+=', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.PLUS, '+', line, col, pos))
            elif ch == '-':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.MINUS_ASSIGN, '-=', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.MINUS, '-', line, col, pos))
            elif ch == '*':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.STAR_ASSIGN, '*=', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.STAR, '*', line, col, pos))
            elif ch == '/':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.SLASH_ASSIGN, '/=', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.SLASH, '/', line, col, pos))
            elif ch == '%':
                self.advance()
                tokens.append(self.make_token(TokenType.PERCENT, '%', line, col, pos))
            elif ch == '=':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.EQ, '==', line, col, pos))
                elif self.match('>'):
                    tokens.append(self.make_token(TokenType.ARROW, '=>', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.ASSIGN, '=', line, col, pos))
            elif ch == '!':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.NEQ, '!=', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.BANG, '!', line, col, pos))
            elif ch == '<':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.LTE, '<=', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.LT, '<', line, col, pos))
            elif ch == '>':
                self.advance()
                if self.match('='):
                    tokens.append(self.make_token(TokenType.GTE, '>=', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.GT, '>', line, col, pos))
            elif ch == '&':
                self.advance()
                if self.match('&'):
                    tokens.append(self.make_token(TokenType.AND, '&&', line, col, pos))
                else:
                    self.error(f"Unexpected character '&', did you mean '&&'?")
            elif ch == '|':
                self.advance()
                if self.match('|'):
                    tokens.append(self.make_token(TokenType.OR, '||', line, col, pos))
                else:
                    self.error(f"Unexpected character '|', did you mean '||'?")
            elif ch == ':':
                self.advance()
                if self.match(':'):
                    tokens.append(self.make_token(TokenType.COLONCOLON, '::', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.COLON, ':', line, col, pos))
            elif ch == '.':
                self.advance()
                if self.peek() == '.' and self.peek(1) == '.':
                    self.advance()
                    self.advance()
                    tokens.append(self.make_token(TokenType.DOTDOTDOT, '...', line, col, pos))
                else:
                    tokens.append(self.make_token(TokenType.DOT, '.', line, col, pos))
            elif ch == '(':
                self.advance()
                tokens.append(self.make_token(TokenType.LPAREN, '(', line, col, pos))
            elif ch == ')':
                self.advance()
                tokens.append(self.make_token(TokenType.RPAREN, ')', line, col, pos))
            elif ch == '{':
                self.advance()
                tokens.append(self.make_token(TokenType.LBRACE, '{', line, col, pos))
            elif ch == '}':
                self.advance()
                tokens.append(self.make_token(TokenType.RBRACE, '}', line, col, pos))
            elif ch == '[':
                self.advance()
                tokens.append(self.make_token(TokenType.LBRACKET, '[', line, col, pos))
            elif ch == ']':
                self.advance()
                tokens.append(self.make_token(TokenType.RBRACKET, ']', line, col, pos))
            elif ch == ',':
                self.advance()
                tokens.append(self.make_token(TokenType.COMMA, ',', line, col, pos))
            else:
                self.error(f"Unexpected character: {ch!r}")

        tokens.append(self.make_token(TokenType.EOF, None, self.line, self.col, self.pos))
        self.tokens = tokens
        return tokens
