from dataclasses import dataclass, field
from typing import Optional


# === Statements ===

@dataclass
class AdoptStatement:
    """adopt io  /  adopt localdir.localfile"""
    module_path: list[str]  # e.g. ['localdir', 'localfile']

@dataclass
class VariableDecl:
    """[share] keep name [: type] [= expr]"""
    name: str
    value: 'Optional[Expr]'
    is_shared: bool = False
    type_ann: Optional[str] = None

@dataclass
class Assignment:
    """target op= value"""
    target: 'Expr'
    op: str  # '=', '+=', '-=', '*=', '/='
    value: 'Expr'

@dataclass
class IfStatement:
    condition: 'Expr'
    body: 'Block'
    elif_clauses: list[tuple['Expr', 'Block']] = field(default_factory=list)
    else_body: 'Optional[Block]' = None

@dataclass
class WhileStatement:
    """stay condition { body }"""
    condition: 'Expr'
    body: 'Block'

@dataclass
class ForEachStatement:
    """go iterable by var { body }"""
    iterable: 'Expr'
    var_name: str
    body: 'Block'

@dataclass
class ReturnStatement:
    value: 'Optional[Expr]' = None

@dataclass
class ExpressionStatement:
    """Wrapper for an expression used as a statement."""
    expr: 'Expr'

@dataclass
class Block:
    statements: list

# === Expressions ===

@dataclass
class NumberLiteral:
    value: object  # int or float

@dataclass
class StringLiteral:
    value: str

@dataclass
class BoolLiteral:
    value: bool

@dataclass
class ArrayLiteral:
    elements: list['Expr']

@dataclass
class Identifier:
    name: str

@dataclass
class BinaryOp:
    left: 'Expr'
    op: str
    right: 'Expr'

@dataclass
class UnaryOp:
    op: str  # '!' or '-'
    operand: 'Expr'

@dataclass
class MemberAccess:
    """object.member"""
    object: 'Expr'
    member: str

@dataclass
class ModuleAccess:
    """module::member"""
    object: 'Expr'
    member: str

@dataclass
class IndexAccess:
    """object[index]"""
    object: 'Expr'
    index: 'Expr'

@dataclass
class FunctionCall:
    callee: 'Expr'
    args: list['Expr']

@dataclass
class Param:
    name: str
    type_ann: Optional[str] = None
    is_vararg: bool = False

@dataclass
class Closure:
    """(params) => { body }  or  (params) => expr"""
    params: list[Param]
    body: 'Block'

@dataclass
class RangeExpr:
    """start to end"""
    start: 'Expr'
    end: 'Expr'

@dataclass
class MakeoutExpr:
    """makeout ClassName(args)  or  makeout mod::Class(args)"""
    callee: 'Expr'
    args: list['Expr']

@dataclass
class NativeBlock:
    """native => { raw JS code }"""
    code: str

@dataclass
class ClassDef:
    """boy [: parent] { members }"""
    name: str  # set by the enclosing VariableDecl
    parent: Optional[str]
    members: list  # list of VariableDecl

@dataclass
class Module:
    path: str  # dotted path or filename
    statements: list
    source_dir: str = ""  # directory of the source file

@dataclass
class Program:
    modules: list[Module]


# Union type alias for documentation
Expr = (NumberLiteral | StringLiteral | BoolLiteral | ArrayLiteral |
        Identifier | BinaryOp | UnaryOp | MemberAccess | ModuleAccess |
        IndexAccess | FunctionCall | Closure | RangeExpr | MakeoutExpr |
        NativeBlock | ClassDef)

Statement = (AdoptStatement | VariableDecl | Assignment | IfStatement |
             WhileStatement | ForEachStatement | ReturnStatement |
             ExpressionStatement)
