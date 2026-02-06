# Standard library module definitions for Femboy Language.
# Each entry maps a module name to its JS inline definition.

STDLIB_MODULES = {
    'io': {
        'js_name': 'io',
        'js_def': '{ print: (...args) => console.log(...args) }',
    },
    'math': {
        'js_name': 'math',
        'js_def': '{ '
                  'floor: (x) => Math.floor(x), '
                  'ceil: (x) => Math.ceil(x), '
                  'round: (x) => Math.round(x), '
                  'abs: (x) => Math.abs(x), '
                  'sqrt: (x) => Math.sqrt(x), '
                  'pow: (x, y) => Math.pow(x, y), '
                  'min: (...args) => Math.min(...args), '
                  'max: (...args) => Math.max(...args), '
                  'random: () => Math.random(), '
                  'PI: Math.PI, '
                  'E: Math.E '
                  '}',
    },
    'str': {
        'js_name': 'str',
        'js_def': '{ '
                  'len: (s) => s.length, '
                  'upper: (s) => s.toUpperCase(), '
                  'lower: (s) => s.toLowerCase(), '
                  'trim: (s) => s.trim(), '
                  'split: (s, sep) => s.split(sep), '
                  'join: (arr, sep) => arr.join(sep), '
                  'includes: (s, sub) => s.includes(sub), '
                  'replace: (s, from, to) => s.replace(from, to), '
                  'slice: (s, start, end) => s.slice(start, end) '
                  '}',
    },
    'arr': {
        'js_name': 'arr',
        'js_def': '{ '
                  'len: (a) => a.length, '
                  'push: (a, v) => { a.push(v); return a; }, '
                  'pop: (a) => a.pop(), '
                  'shift: (a) => a.shift(), '
                  'slice: (a, s, e) => a.slice(s, e), '
                  'map: (a, fn) => a.map(fn), '
                  'filter: (a, fn) => a.filter(fn), '
                  'reduce: (a, fn, init) => a.reduce(fn, init), '
                  'find: (a, fn) => a.find(fn), '
                  'sort: (a, fn) => [...a].sort(fn), '
                  'reverse: (a) => [...a].reverse(), '
                  'includes: (a, v) => a.includes(v) '
                  '}',
    },
}


def is_stdlib(module_name: str) -> bool:
    return module_name in STDLIB_MODULES


def get_stdlib_js(module_name: str) -> str | None:
    entry = STDLIB_MODULES.get(module_name)
    if entry:
        return f"const {entry['js_name']} = {entry['js_def']};"
    return None
