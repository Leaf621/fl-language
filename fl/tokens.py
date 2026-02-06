from enum import Enum, auto


class TokenType(Enum):
    # Literals
    INT = auto()
    FLOAT = auto()
    STRING = auto()

    # Identifier
    IDENT = auto()

    # Keywords
    ADOPT = auto()      # import
    KEEP = auto()       # variable declaration
    SHARE = auto()      # public modifier
    GO = auto()         # for-each
    BY = auto()         # for-each variable
    STAY = auto()       # while
    IF = auto()
    ELSE = auto()
    RETURN = auto()
    BOY = auto()        # class
    MAKEOUT = auto()    # constructor call (new)
    NATIVE = auto()     # native JS interop
    TO = auto()         # range operator
    YES = auto()        # true
    NO = auto()         # false

    # Operators
    PLUS = auto()       # +
    MINUS = auto()      # -
    STAR = auto()       # *
    SLASH = auto()      # /
    PERCENT = auto()    # %
    ASSIGN = auto()     # =
    EQ = auto()         # ==
    NEQ = auto()        # !=
    LT = auto()         # <
    GT = auto()         # >
    LTE = auto()        # <=
    GTE = auto()        # >=
    PLUS_ASSIGN = auto()   # +=
    MINUS_ASSIGN = auto()  # -=
    STAR_ASSIGN = auto()   # *=
    SLASH_ASSIGN = auto()  # /=
    BANG = auto()       # !
    AND = auto()        # &&
    OR = auto()         # ||
    COLONCOLON = auto() # ::
    ARROW = auto()      # =>
    DOT = auto()        # .
    COLON = auto()      # :
    DOTDOTDOT = auto()  # ... (vararg)

    # Delimiters
    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    LBRACKET = auto()   # [
    RBRACKET = auto()   # ]
    COMMA = auto()      # ,

    # Special
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    'adopt': TokenType.ADOPT,
    'keep': TokenType.KEEP,
    'share': TokenType.SHARE,
    'go': TokenType.GO,
    'by': TokenType.BY,
    'stay': TokenType.STAY,
    'if': TokenType.IF,
    'else': TokenType.ELSE,
    'return': TokenType.RETURN,
    'boy': TokenType.BOY,
    'makeout': TokenType.MAKEOUT,
    'native': TokenType.NATIVE,
    'to': TokenType.TO,
    'YES': TokenType.YES,
    'NO': TokenType.NO,
}


class Token:
    __slots__ = ('type', 'value', 'line', 'col', 'pos')

    def __init__(self, type: TokenType, value, line: int, col: int, pos: int):
        self.type = type
        self.value = value
        self.line = line
        self.col = col
        self.pos = pos

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"
