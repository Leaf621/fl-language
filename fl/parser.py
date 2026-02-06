from fl.tokens import Token, TokenType
from fl.lexer import Lexer
from fl.ast_nodes import (
    AdoptStatement, VariableDecl, Assignment, IfStatement, WhileStatement,
    ForEachStatement, ReturnStatement, ExpressionStatement, Block,
    NumberLiteral, StringLiteral, BoolLiteral, ArrayLiteral, Identifier,
    BinaryOp, UnaryOp, MemberAccess, ModuleAccess, IndexAccess,
    FunctionCall, Closure, Param, RangeExpr, MakeoutExpr, NativeBlock,
    ClassDef, Module,
)


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"Parse error at {token.line}:{token.col}: {message}")
        self.token = token


class Parser:
    def __init__(self, tokens: list[Token], source: str, filename: str = "<stdin>"):
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.pos = 0

    def error(self, msg: str) -> ParseError:
        return ParseError(msg, self.current())

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF

    def peek(self, offset: int = 0) -> Token:
        p = self.pos + offset
        if p < len(self.tokens):
            return self.tokens[p]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, type: TokenType, msg: str = None) -> Token:
        tok = self.current()
        if tok.type != type:
            expected = msg or type.name
            raise self.error(f"Expected {expected}, got {tok.type.name} ({tok.value!r})")
        return self.advance()

    def match(self, *types: TokenType) -> Token | None:
        if self.current().type in types:
            return self.advance()
        return None

    def skip_newlines(self):
        while self.current().type == TokenType.NEWLINE:
            self.advance()

    def at_statement_end(self) -> bool:
        return self.current().type in (TokenType.NEWLINE, TokenType.EOF, TokenType.RBRACE)

    def expect_statement_end(self):
        if self.current().type == TokenType.RBRACE or self.current().type == TokenType.EOF:
            return
        if self.current().type == TokenType.NEWLINE:
            self.skip_newlines()
            return
        raise self.error(f"Expected end of statement, got {self.current().type.name}")

    # === Top-level parsing ===

    def parse_module(self, path: str = "__main__") -> Module:
        self.skip_newlines()
        stmts = []
        while self.current().type != TokenType.EOF:
            stmts.append(self.parse_statement())
            self.skip_newlines()
        return Module(path=path, statements=stmts)

    def parse_statement(self):
        tok = self.current()

        if tok.type == TokenType.ADOPT:
            return self.parse_adopt()
        if tok.type == TokenType.SHARE:
            return self.parse_share()
        if tok.type == TokenType.KEEP:
            return self.parse_keep(is_shared=False)
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.STAY:
            return self.parse_while()
        if tok.type == TokenType.GO:
            return self.parse_foreach()
        if tok.type == TokenType.RETURN:
            return self.parse_return()

        # Expression statement (could be assignment or function call)
        expr = self.parse_expression()

        # Check for assignment operators
        if self.current().type in (TokenType.ASSIGN, TokenType.PLUS_ASSIGN,
                                    TokenType.MINUS_ASSIGN, TokenType.STAR_ASSIGN,
                                    TokenType.SLASH_ASSIGN):
            op_tok = self.advance()
            value = self.parse_expression()
            self.expect_statement_end()
            return Assignment(target=expr, op=op_tok.value, value=value)

        self.expect_statement_end()
        return ExpressionStatement(expr=expr)

    # === Import ===

    def parse_adopt(self) -> AdoptStatement:
        self.expect(TokenType.ADOPT)
        parts = [self.expect(TokenType.IDENT).value]
        while self.match(TokenType.DOT):
            parts.append(self.expect(TokenType.IDENT).value)
        self.expect_statement_end()
        return AdoptStatement(module_path=parts)

    # === Variable declaration ===

    def parse_share(self):
        self.expect(TokenType.SHARE)
        if self.current().type == TokenType.KEEP:
            return self.parse_keep(is_shared=True)
        raise self.error("Expected 'keep' after 'share'")

    def parse_keep(self, is_shared: bool) -> VariableDecl:
        self.expect(TokenType.KEEP)
        name = self.expect(TokenType.IDENT).value
        type_ann = None

        # Optional type annotation
        if self.current().type == TokenType.COLON:
            self.advance()
            if self.current().type == TokenType.NATIVE:
                type_ann = self.advance().value
            else:
                type_ann = self.expect(TokenType.IDENT).value
            # If no = follows, it's just a typed declaration
            if self.current().type != TokenType.ASSIGN:
                self.expect_statement_end()
                return VariableDecl(name=name, value=None, is_shared=is_shared, type_ann=type_ann)

        # Value assignment
        if self.match(TokenType.ASSIGN):
            value = self.parse_expression()
            # If it's a ClassDef, set its name
            if isinstance(value, ClassDef):
                value.name = name
            self.expect_statement_end()
            return VariableDecl(name=name, value=value, is_shared=is_shared, type_ann=type_ann)

        self.expect_statement_end()
        return VariableDecl(name=name, value=None, is_shared=is_shared, type_ann=type_ann)

    # === Control flow ===

    def parse_if(self) -> IfStatement:
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        body = self.parse_block()
        elif_clauses = []
        else_body = None

        while self.current().type == TokenType.ELSE:
            self.advance()
            if self.current().type == TokenType.IF:
                self.advance()
                elif_cond = self.parse_expression()
                elif_body = self.parse_block()
                elif_clauses.append((elif_cond, elif_body))
            else:
                else_body = self.parse_block()
                break

        self.skip_newlines()
        return IfStatement(condition=condition, body=body,
                          elif_clauses=elif_clauses, else_body=else_body)

    def parse_while(self) -> WhileStatement:
        self.expect(TokenType.STAY)
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileStatement(condition=condition, body=body)

    def parse_foreach(self) -> ForEachStatement:
        self.expect(TokenType.GO)
        iterable = self.parse_expression()
        self.expect(TokenType.BY)
        var_name = self.expect(TokenType.IDENT).value
        body = self.parse_block()
        return ForEachStatement(iterable=iterable, var_name=var_name, body=body)

    def parse_return(self) -> ReturnStatement:
        self.expect(TokenType.RETURN)
        if self.at_statement_end():
            self.expect_statement_end()
            return ReturnStatement(value=None)
        value = self.parse_expression()
        self.expect_statement_end()
        return ReturnStatement(value=value)

    # === Block ===

    def parse_block(self) -> Block:
        self.skip_newlines()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        stmts = []
        while self.current().type != TokenType.RBRACE:
            if self.current().type == TokenType.EOF:
                raise self.error("Unexpected end of file, expected '}'")
            stmts.append(self.parse_statement())
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return Block(statements=stmts)

    # === Expressions (precedence climbing) ===

    def parse_expression(self) -> object:
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.match(TokenType.OR):
            right = self.parse_and()
            left = BinaryOp(left=left, op='||', right=right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.match(TokenType.AND):
            right = self.parse_equality()
            left = BinaryOp(left=left, op='&&', right=right)
        return left

    def parse_equality(self):
        left = self.parse_comparison()
        while self.current().type in (TokenType.EQ, TokenType.NEQ):
            op = self.advance().value
            right = self.parse_comparison()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def parse_comparison(self):
        left = self.parse_range()
        while self.current().type in (TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.advance().value
            right = self.parse_range()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def parse_range(self):
        left = self.parse_addition()
        if self.current().type == TokenType.TO:
            self.advance()
            right = self.parse_addition()
            return RangeExpr(start=left, end=right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.parse_multiplication()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while self.current().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOp(left=left, op=op, right=right)
        return left

    def parse_unary(self):
        if self.current().type == TokenType.BANG:
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op='!', operand=operand)
        if self.current().type == TokenType.MINUS:
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op='-', operand=operand)
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.current().type == TokenType.LPAREN:
                # Function call
                self.advance()
                args = self.parse_args_list()
                self.expect(TokenType.RPAREN)
                expr = FunctionCall(callee=expr, args=args)
            elif self.current().type == TokenType.DOT:
                self.advance()
                member = self.expect(TokenType.IDENT).value
                expr = MemberAccess(object=expr, member=member)
            elif self.current().type == TokenType.COLONCOLON:
                self.advance()
                member = self.expect(TokenType.IDENT).value
                expr = ModuleAccess(object=expr, member=member)
            elif self.current().type == TokenType.LBRACKET:
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = IndexAccess(object=expr, index=index)
            else:
                break
        return expr

    def parse_args_list(self) -> list:
        args = []
        self.skip_newlines()
        if self.current().type == TokenType.RPAREN:
            return args
        args.append(self.parse_expression())
        while self.match(TokenType.COMMA):
            self.skip_newlines()
            args.append(self.parse_expression())
        self.skip_newlines()
        return args

    def parse_primary(self):
        tok = self.current()

        # Number literals
        if tok.type == TokenType.INT:
            self.advance()
            return NumberLiteral(value=tok.value)
        if tok.type == TokenType.FLOAT:
            self.advance()
            return NumberLiteral(value=tok.value)

        # String literal
        if tok.type == TokenType.STRING:
            self.advance()
            return StringLiteral(value=tok.value)

        # Boolean literals
        if tok.type == TokenType.YES:
            self.advance()
            return BoolLiteral(value=True)
        if tok.type == TokenType.NO:
            self.advance()
            return BoolLiteral(value=False)

        # Array literal
        if tok.type == TokenType.LBRACKET:
            return self.parse_array_literal()

        # Makeout expression (constructor)
        if tok.type == TokenType.MAKEOUT:
            return self.parse_makeout()

        # Native block: native => { ... }
        if tok.type == TokenType.NATIVE and self.peek(1).type == TokenType.ARROW:
            return self.parse_native_block()

        # Boy (class definition)
        if tok.type == TokenType.BOY:
            return self.parse_class_def()

        # Parenthesized expression or closure
        if tok.type == TokenType.LPAREN:
            return self.parse_paren_or_closure()

        # Identifier
        if tok.type == TokenType.IDENT:
            self.advance()
            return Identifier(name=tok.value)

        # Native as identifier (for type annotations used as values)
        if tok.type == TokenType.NATIVE:
            self.advance()
            return Identifier(name='native')

        raise self.error(f"Unexpected token: {tok.type.name} ({tok.value!r})")

    def parse_array_literal(self) -> ArrayLiteral:
        self.expect(TokenType.LBRACKET)
        elements = []
        self.skip_newlines()
        if self.current().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            while self.match(TokenType.COMMA):
                self.skip_newlines()
                if self.current().type == TokenType.RBRACKET:
                    break
                elements.append(self.parse_expression())
        self.skip_newlines()
        self.expect(TokenType.RBRACKET)
        return ArrayLiteral(elements=elements)

    def parse_makeout(self) -> MakeoutExpr:
        self.expect(TokenType.MAKEOUT)
        # Parse callee: could be simple ident or module path (a::b::C)
        callee = Identifier(name=self.expect(TokenType.IDENT).value)
        while self.current().type == TokenType.COLONCOLON:
            self.advance()
            member = self.expect(TokenType.IDENT).value
            callee = ModuleAccess(object=callee, member=member)
        self.expect(TokenType.LPAREN)
        args = self.parse_args_list()
        self.expect(TokenType.RPAREN)
        return MakeoutExpr(callee=callee, args=args)

    def parse_native_block(self) -> NativeBlock:
        self.expect(TokenType.NATIVE)
        self.expect(TokenType.ARROW)
        lbrace = self.expect(TokenType.LBRACE)
        # Extract raw JS from source between this { and matching }
        raw = self._extract_raw_js(lbrace.pos)
        return NativeBlock(code=raw)

    def _extract_raw_js(self, lbrace_pos: int) -> str:
        """Extract raw JS code from source, consuming tokens until matching }."""
        # Find position in source after the {
        start = lbrace_pos + 1
        depth = 1
        i = start
        while i < len(self.source) and depth > 0:
            ch = self.source[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif ch == '"' or ch == "'":
                # Skip string literals
                quote = ch
                i += 1
                while i < len(self.source) and self.source[i] != quote:
                    if self.source[i] == '\\':
                        i += 1
                    i += 1
            elif ch == '/' and i + 1 < len(self.source) and self.source[i + 1] == '/':
                # Skip // comments
                while i < len(self.source) and self.source[i] != '\n':
                    i += 1
                continue
            i += 1

        raw = self.source[start:i - 1]  # exclude closing }

        # Advance parser past all tokens until we're past the closing }
        while self.pos < len(self.tokens) and self.tokens[self.pos].type != TokenType.RBRACE:
            self.pos += 1
        # Find the RBRACE that corresponds to our closing position
        # We need to skip inner braces
        target_pos = i - 1  # position of closing }
        while self.pos < len(self.tokens):
            if self.tokens[self.pos].type == TokenType.RBRACE and self.tokens[self.pos].pos >= target_pos:
                self.advance()  # consume the }
                break
            self.pos += 1

        return raw

    def parse_class_def(self) -> ClassDef:
        self.expect(TokenType.BOY)
        parent = None
        if self.match(TokenType.COLON):
            parent = self.expect(TokenType.IDENT).value
        self.skip_newlines()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        members = []
        while self.current().type != TokenType.RBRACE:
            if self.current().type == TokenType.EOF:
                raise self.error("Unexpected end of file in class body")
            if self.current().type == TokenType.SHARE:
                members.append(self.parse_share())
            elif self.current().type == TokenType.KEEP:
                members.append(self.parse_keep(is_shared=False))
            else:
                raise self.error(f"Expected member declaration in class body, got {self.current().type.name}")
            self.skip_newlines()
        self.expect(TokenType.RBRACE)
        return ClassDef(name="", parent=parent, members=members)

    def parse_paren_or_closure(self):
        """Parse either a parenthesized expression or a closure definition."""
        # Save position for backtracking
        saved_pos = self.pos

        # Try to parse as closure parameters
        if self._is_closure():
            return self.parse_closure()

        # Otherwise it's a parenthesized expression
        self.pos = saved_pos
        self.expect(TokenType.LPAREN)
        self.skip_newlines()
        expr = self.parse_expression()
        self.skip_newlines()
        self.expect(TokenType.RPAREN)
        return expr

    def _is_closure(self) -> bool:
        """Look ahead to determine if this is a closure (params) => ..."""
        saved = self.pos
        try:
            if self.current().type != TokenType.LPAREN:
                return False
            self.advance()  # skip (
            depth = 1
            while depth > 0 and self.pos < len(self.tokens):
                t = self.current().type
                if t == TokenType.LPAREN:
                    depth += 1
                elif t == TokenType.RPAREN:
                    depth -= 1
                if depth > 0:
                    self.advance()
            if depth != 0:
                return False
            self.advance()  # skip closing )
            # Check for =>
            self.skip_newlines()
            result = self.current().type == TokenType.ARROW
            return result
        finally:
            self.pos = saved

    def parse_closure(self) -> Closure:
        self.expect(TokenType.LPAREN)
        params = self.parse_params()
        self.expect(TokenType.RPAREN)
        self.skip_newlines()
        self.expect(TokenType.ARROW)
        self.skip_newlines()

        if self.current().type == TokenType.LBRACE:
            body = self.parse_block()
        else:
            # Single expression body
            expr = self.parse_expression()
            body = Block(statements=[ReturnStatement(value=expr)])

        return Closure(params=params, body=body)

    def parse_params(self) -> list[Param]:
        params = []
        self.skip_newlines()
        if self.current().type == TokenType.RPAREN:
            return params
        params.append(self.parse_param())
        while self.match(TokenType.COMMA):
            self.skip_newlines()
            params.append(self.parse_param())
        self.skip_newlines()
        return params

    def parse_param(self) -> Param:
        self.skip_newlines()
        name = self.expect(TokenType.IDENT).value
        type_ann = None
        is_vararg = False

        # Check for vararg: name...
        if self.current().type == TokenType.DOTDOTDOT:
            self.advance()
            is_vararg = True

        # Check for type annotation: name: type
        if self.current().type == TokenType.COLON:
            self.advance()
            if self.current().type == TokenType.NATIVE:
                type_ann = self.advance().value
            else:
                type_ann = self.expect(TokenType.IDENT).value
        elif self.current().type == TokenType.NATIVE:
            # Handle : native where native is a keyword
            pass

        return Param(name=name, type_ann=type_ann, is_vararg=is_vararg)


def parse(source: str, filename: str = "<stdin>") -> Module:
    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source, filename)
    return parser.parse_module()
