#!/usr/bin/env python3
"""Femboy Language Compiler — compiles .fl files to JavaScript."""

import sys
import os
import argparse

from fl.lexer import Lexer, LexerError
from fl.parser import Parser, ParseError, parse
from fl.codegen import CodeGen, CodeGenError
from fl.stdlib import is_stdlib
from fl.ast_nodes import (
    AdoptStatement, Program, Module, VariableDecl, Assignment,
    IfStatement, WhileStatement, ForEachStatement, ReturnStatement,
    ExpressionStatement, Block, NumberLiteral, StringLiteral, BoolLiteral,
    ArrayLiteral, Identifier, BinaryOp, UnaryOp, MemberAccess, ModuleAccess,
    IndexAccess, FunctionCall, Closure, Param, RangeExpr, MakeoutExpr,
    NativeBlock, ClassDef,
)


# === AST Pretty Printer ===

# Box-drawing pieces
_PIPE  = "\033[90m\u2502\033[0m"   # │
_TEE   = "\033[90m\u251c\u2500\u2500\033[0m" # ├──
_BEND  = "\033[90m\u2514\u2500\u2500\033[0m" # └──
_BLANK = "   "

# ANSI helpers
def _c(code: int, text: str) -> str:
    return f"\033[{code}m{text}\033[0m"

def _node(name: str) -> str:
    return _c(1, _c(36, name))          # bold cyan

def _key(name: str) -> str:
    return _c(33, name)                 # yellow

def _val(text: str) -> str:
    return _c(32, text)                 # green

def _dim(text: str) -> str:
    return _c(90, text)                 # gray

def _str(text: str) -> str:
    return _c(33, f'"{text}"')          # yellow quoted


def print_ast(program: Program):
    """Pretty-print a Program AST as a coloured tree."""
    print(_node("Program"))
    modules = program.modules
    for i, mod in enumerate(modules):
        last = i == len(modules) - 1
        _print_module(mod, prefix="", is_last=last)


def _print_module(mod: Module, prefix: str, is_last: bool):
    connector = _BEND if is_last else _TEE
    child_prefix = prefix + (_BLANK if is_last else f"{_PIPE}  ")
    label = _dim(mod.path) if mod.path == "__main__" else _val(mod.path)
    print(f"{prefix}{connector} {_node('Module')} {label}")
    stmts = mod.statements
    for i, stmt in enumerate(stmts):
        _print_node(stmt, child_prefix, i == len(stmts) - 1)


def _print_node(node, prefix: str, is_last: bool):
    connector = _BEND if is_last else _TEE
    next_prefix = prefix + (_BLANK if is_last else f"{_PIPE}  ")

    # --- Statements ---
    if isinstance(node, AdoptStatement):
        path = _val(".".join(node.module_path))
        print(f"{prefix}{connector} {_node('Adopt')} {path}")

    elif isinstance(node, VariableDecl):
        mods = []
        if node.is_shared:
            mods.append(_c(35, "share"))
        tag = " ".join(mods)
        if tag:
            tag += " "
        ann = f" {_dim(':' + node.type_ann)}" if node.type_ann else ""
        print(f"{prefix}{connector} {tag}{_node('Keep')} {_key(node.name)}{ann}")
        if node.value is not None:
            _print_node(node.value, next_prefix, True)

    elif isinstance(node, Assignment):
        print(f"{prefix}{connector} {_node('Assign')} {_dim(node.op)}")
        _print_node(node.target, next_prefix, False)
        _print_node(node.value, next_prefix, True)

    elif isinstance(node, IfStatement):
        print(f"{prefix}{connector} {_node('If')}")
        parts = []
        parts.append(("condition", node.condition))
        parts.append(("then", node.body))
        for idx, (econd, ebody) in enumerate(node.elif_clauses):
            parts.append((f"else if", econd))
            parts.append((f"then", ebody))
        if node.else_body:
            parts.append(("else", node.else_body))
        for i, (label, child) in enumerate(parts):
            last = i == len(parts) - 1
            c2 = _BEND if last else _TEE
            np2 = next_prefix + (_BLANK if last else f"{_PIPE}  ")
            print(f"{next_prefix}{c2} {_dim(label)}")
            _print_node(child, np2, True)

    elif isinstance(node, WhileStatement):
        print(f"{prefix}{connector} {_node('Stay')}")
        _print_node(node.condition, next_prefix, False)
        _print_node(node.body, next_prefix, True)

    elif isinstance(node, ForEachStatement):
        print(f"{prefix}{connector} {_node('Go')} {_dim('by')} {_key(node.var_name)}")
        _print_node(node.iterable, next_prefix, False)
        _print_node(node.body, next_prefix, True)

    elif isinstance(node, ReturnStatement):
        print(f"{prefix}{connector} {_node('Return')}")
        if node.value:
            _print_node(node.value, next_prefix, True)

    elif isinstance(node, ExpressionStatement):
        _print_node(node.expr, prefix, is_last)

    elif isinstance(node, Block):
        stmts = node.statements
        if not stmts:
            print(f"{prefix}{connector} {_dim('{}')} ")
            return
        print(f"{prefix}{connector} {_node('Block')}")
        for i, s in enumerate(stmts):
            _print_node(s, next_prefix, i == len(stmts) - 1)

    # --- Expressions ---
    elif isinstance(node, NumberLiteral):
        print(f"{prefix}{connector} {_val(str(node.value))}")

    elif isinstance(node, StringLiteral):
        print(f"{prefix}{connector} {_str(node.value)}")

    elif isinstance(node, BoolLiteral):
        print(f"{prefix}{connector} {_val('YES' if node.value else 'NO')}")

    elif isinstance(node, ArrayLiteral):
        if not node.elements:
            print(f"{prefix}{connector} {_node('Array')} {_dim('[]')}")
            return
        print(f"{prefix}{connector} {_node('Array')}")
        for i, el in enumerate(node.elements):
            _print_node(el, next_prefix, i == len(node.elements) - 1)

    elif isinstance(node, Identifier):
        print(f"{prefix}{connector} {_key(node.name)}")

    elif isinstance(node, BinaryOp):
        print(f"{prefix}{connector} {_node('BinOp')} {_dim(node.op)}")
        _print_node(node.left, next_prefix, False)
        _print_node(node.right, next_prefix, True)

    elif isinstance(node, UnaryOp):
        print(f"{prefix}{connector} {_node('UnaryOp')} {_dim(node.op)}")
        _print_node(node.operand, next_prefix, True)

    elif isinstance(node, MemberAccess):
        print(f"{prefix}{connector} {_node('Member')} {_dim('.')} {_key(node.member)}")
        _print_node(node.object, next_prefix, True)

    elif isinstance(node, ModuleAccess):
        print(f"{prefix}{connector} {_node('Access')} {_dim('::')} {_key(node.member)}")
        _print_node(node.object, next_prefix, True)

    elif isinstance(node, IndexAccess):
        print(f"{prefix}{connector} {_node('Index')}")
        _print_node(node.object, next_prefix, False)
        _print_node(node.index, next_prefix, True)

    elif isinstance(node, FunctionCall):
        print(f"{prefix}{connector} {_node('Call')}")
        _print_node(node.callee, next_prefix, not node.args)
        for i, arg in enumerate(node.args):
            _print_node(arg, next_prefix, i == len(node.args) - 1)

    elif isinstance(node, Closure):
        params = ", ".join(_format_param(p) for p in node.params)
        print(f"{prefix}{connector} {_node('Closure')} {_dim('('+ params +')')}")
        _print_node(node.body, next_prefix, True)

    elif isinstance(node, RangeExpr):
        print(f"{prefix}{connector} {_node('Range')} {_dim('to')}")
        _print_node(node.start, next_prefix, False)
        _print_node(node.end, next_prefix, True)

    elif isinstance(node, MakeoutExpr):
        print(f"{prefix}{connector} {_node('Makeout')}")
        _print_node(node.callee, next_prefix, not node.args)
        for i, arg in enumerate(node.args):
            _print_node(arg, next_prefix, i == len(node.args) - 1)

    elif isinstance(node, NativeBlock):
        preview = node.code.strip().replace('\n', ' ')
        if len(preview) > 40:
            preview = preview[:37] + "..."
        print(f"{prefix}{connector} {_node('Native')} {_dim(preview)}")

    elif isinstance(node, ClassDef):
        parent = f" {_dim(':')} {_val(node.parent)}" if node.parent else ""
        print(f"{prefix}{connector} {_node('Boy')}{parent}")
        for i, m in enumerate(node.members):
            _print_node(m, next_prefix, i == len(node.members) - 1)

    else:
        print(f"{prefix}{connector} {_dim(repr(node))}")


def _format_param(p: Param) -> str:
    s = p.name
    if p.is_vararg:
        s += "..."
    if p.type_ann:
        s += f": {p.type_ann}"
    return s


# === Module discovery ===

def discover_modules(entry_path: str) -> list[tuple[str, str, str]]:
    """
    Starting from the entry file, discover all imported FL modules.
    Returns list of (module_dotted_path, file_path, source) in dependency order.
    """
    entry_dir = os.path.dirname(os.path.abspath(entry_path))
    visited = set()
    ordered = []

    def visit(dotted_path: str, file_path: str):
        if dotted_path in visited:
            return
        visited.add(dotted_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # Parse to find adopt statements
        module = parse(source, file_path)
        mod_dir = os.path.dirname(os.path.abspath(file_path))

        for stmt in module.statements:
            if isinstance(stmt, AdoptStatement):
                imp_path = stmt.module_path
                if is_stdlib(imp_path[0]):
                    continue
                # Resolve relative path from the entry directory
                rel_path = os.path.join(entry_dir, *imp_path) + '.fl'
                if not os.path.exists(rel_path):
                    # Try from current module's directory
                    rel_path = os.path.join(mod_dir, *imp_path) + '.fl'
                if not os.path.exists(rel_path):
                    print(f"Error: Cannot find module '{'.'.join(imp_path)}' "
                          f"(searched {entry_dir} and {mod_dir})",
                          file=sys.stderr)
                    sys.exit(1)
                visit('.'.join(imp_path), rel_path)

        ordered.append((dotted_path, file_path, source))

    visit('__main__', entry_path)
    return ordered


# === Compilation ===

def compile_file(entry_path: str, output_path: str | None = None,
                 show_ast: bool = False):
    """Compile an FL file (and its dependencies) to a single JS file."""
    if not os.path.exists(entry_path):
        print(f"Error: File not found: {entry_path}", file=sys.stderr)
        sys.exit(1)

    modules_info = discover_modules(entry_path)

    # Parse all modules into AST
    modules = []
    for dotted_path, file_path, source in modules_info:
        module = parse(source, file_path)
        module.path = dotted_path
        module.source_dir = os.path.dirname(os.path.abspath(file_path))
        modules.append(module)

    program = Program(modules=modules)

    if show_ast:
        print_ast(program)
        print()

    # Generate JS
    codegen = CodeGen()
    js_output = codegen.generate_program(program)

    # Write output
    if output_path is None:
        base = os.path.splitext(entry_path)[0]
        output_path = base + '.js'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_output)
        f.write('\n')

    print(f"Compiled {entry_path} -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Femboy Language Compiler — compiles .fl to JavaScript',
        prog='flc',
    )
    parser.add_argument('input', help='Input .fl file')
    parser.add_argument('-o', '--output', help='Output .js file (default: <input>.js)')
    parser.add_argument('--ast', action='store_true', help='Print the AST tree')
    args = parser.parse_args()

    try:
        compile_file(args.input, args.output, show_ast=args.ast)
    except LexerError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except CodeGenError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
