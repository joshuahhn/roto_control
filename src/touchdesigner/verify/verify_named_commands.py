"""Finite command-migration check for TD Python roots and literal executable code.

This checks lexical aliases and known wire-identity shapes, not arbitrary Python
reflection or runtime-generated source. Raw expected/inbound fixtures are legal;
using a raw fixture at an output boundary is not.
"""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import textwrap

ROOTS = ('code', 'scripts', 'build', 'upgrade', 'verify', 'tests', 'diagnostics', 'prototypes')
CATEGORIES = ('legacy_definitions', 'legacy_imports', 'legacy_references', 'legacy_calls',
              'serial_selectors', 'raw_dispatch', 'raw_send', 'syntax')
LEGACY = {'sysex', '_command', '_packet', 'COMMANDS'}
TEXT_FIXTURES = {
    ('tests/test_owned_inspector.py', 'test_generic_scrub_preserves_source_local_refs_and_external_state', 'exact embedded code'),
    ('tests/test_owned_inspector.py', 'test_archive_is_taken_before_upgrade_source_or_file_settings', 'old source'),
    ('tests/test_owned_inspector.py', 'test_archive_is_taken_before_upgrade_source_or_file_settings', 'new source'),
    ('tests/test_owned_inspector.py', 'test_required_runtime_and_helper_source_mismatch_stops_packaging', 'wrong helper'),
    ('tests/test_owned_inspector.py', 'test_required_runtime_and_helper_source_mismatch_stops_packaging', 'wrong runtime'),
    ('tests/test_serial_packaging.py', 'test_source_checker_rejects_both_serial_module_and_worker_mismatch', 'stale source'),
}
EXCLUSIONS = {'projects, exports': 'Preserved artifacts and receipts; native embedding checked separately',
              '.venv, __pycache__, bytecode': 'Not maintained Python source',
              'system temporary evidence': 'Pinned pre-migration oracle',
              'Markdown': 'Scoped prose consistency review',
              'src/ableton, src/bitwig, src/logic': 'Inherited read-only integrations'}


def symbol(node):
    return node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ''


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return None


def unwrap(node):
    if isinstance(node, ast.Call) and symbol(node.func) in ('tuple', 'list', 'bytes') and len(node.args) == 1:
        return unwrap(node.args[0])
    return node


def slot(node):
    node = unwrap(node)
    if not isinstance(node, ast.Subscript):
        return None
    index = node.slice
    if isinstance(index, ast.Constant) and index.value in (5, 6):
        return ast.unparse(node.value), str(index.value)
    if isinstance(index, ast.Slice):
        low = literal(index.lower) if index.lower else 0
        high = literal(index.upper)
        if (low, high) in ((5, 7), (5, 9), (0, 7), (0, 5)):
            return ast.unparse(node.value), str(low) + ':' + str(high)
    return None


def numeric(node):
    value = literal(node)
    return type(value) is int or isinstance(value, (tuple, list)) and bool(value) and all(
        type(x) is int or isinstance(x, (tuple, list)) and all(type(y) is int for y in x) for x in value)


def raw_packet(node, aliases):
    node = unwrap(node)
    if isinstance(node, ast.Name):
        return node.id in aliases
    if isinstance(node, (ast.Tuple, ast.List)):
        values = node.elts
        if len(values) >= 7 and [literal(x) for x in values[:5]] == [240, 0, 34, 3, 2]:
            return True
        return len(values) >= 3 and isinstance(values[0], ast.Starred) and symbol(values[0].value) == 'HEADER'
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return raw_packet(node.left, aliases) or raw_packet(node.right, aliases)
    return False


def cli_exception(path, node, parents):
    if path != 'diagnostics/runtime/layout_protocol_probe.py':
        return False
    if isinstance(node, ast.FunctionDef):
        return (node.name == 'command' and isinstance(parents.get(node), ast.ClassDef)
                and parents[node].name == 'Probe' and [a.arg for a in node.args.args] == ['self', 'line'])
    return (isinstance(node, ast.Attribute) and ast.unparse(node) == 'probe.command'
            and isinstance(parents.get(node), ast.Call)
            and ast.unparse(parents[node]) == "probe.command(line.decode('ascii'))")


def scan_source(source, path='<source>', depth=0):
    findings, snippets, dynamic, text_fixtures, cli_exclusions = [], [], [], [], []
    def report(node, category, detail=None):
        item = dict(path=path, line=node.lineno, category=category, expression=detail or ast.unparse(node))
        if item not in findings:
            findings.append(item)
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return dict(findings=[dict(path=path, line=exc.lineno or 1, category='syntax', expression=str(exc))], snippets=[], dynamic=[])
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    scopes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    scope_for = {}
    for node in ast.walk(tree):
        current = node
        while current in parents and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            current = parents[current]
        scope_for[node] = current if current in scopes else tree
    imported_gets = {'SerialGet'}
    constructors = {'ReadSession'}
    command_types = {'SysExCommand', 'SerialGet'}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for name in node.names:
                if name.name == 'SerialGet': imported_gets.add(name.asname or name.name)
                if name.name == 'ReadSession': constructors.add(name.asname or name.name)
                if name.name in ('SysExCommand', 'SerialGet'): command_types.add(name.asname or name.name)
    type_aliases = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)]
    for _ in range(len(type_aliases) + 1):
        before = len(command_types)
        for node in type_aliases:
            if isinstance(node.value, (ast.Name, ast.Attribute)) and symbol(node.value) in command_types:
                command_types.update(target.id for target in node.targets if isinstance(target, ast.Name))
        if len(command_types) == before: break
    module_strings = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name): module_strings[target.id] = node.value
    tables = {}
    for scope in scopes:
        nodes = [n for n in ast.walk(scope) if scope_for.get(n) is scope]
        sessions, getters, named, identities, frames, packets, strings = {'session'}, set(), set(), {}, {'message', 'm', 'packet', 'raw'}, set(), module_strings.copy()
        if isinstance(scope, ast.FunctionDef) and isinstance(parents.get(scope), ast.ClassDef) and parents[scope].name == 'ReadSession':
            sessions.add('self')
        def named_get(node, named=named):
            if isinstance(node, ast.Name): return node.id in named
            if isinstance(node, ast.Attribute): return symbol(node.value) in imported_gets
            if isinstance(node, ast.IfExp): return named_get(node.body, named) and named_get(node.orelse, named)
            return False
        def resolve(node, seen=(), strings=strings):
            if isinstance(node, ast.Constant) and isinstance(node.value, str): return node.value
            if isinstance(node, ast.Name) and node.id in strings and node.id not in seen:
                return resolve(strings[node.id], (*seen, node.id), strings)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                a, b = resolve(node.left, seen, strings), resolve(node.right, seen, strings)
                return a + b if a is not None and b is not None else None
            if isinstance(node, ast.Call) and symbol(node.func) == 'dedent' and node.args:
                value = resolve(node.args[0], seen, strings)
                return textwrap.dedent(value) if value is not None else None
            return None
        assignments = [n for n in nodes if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None]
        for assignment in assignments:
            for target in assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]:
                if isinstance(target, ast.Name): strings[target.id] = assignment.value
        for _ in range(len(assignments) + 1):
            before = repr((sessions, getters, named, identities, frames, packets))
            for assignment in assignments:
                value = assignment.value
                for target in assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]:
                    if isinstance(target, ast.Name):
                        key = target.id
                        if isinstance(value, ast.Call) and symbol(value.func) in constructors or isinstance(value, ast.Name) and value.id in sessions:
                            sessions.add(key)
                        if isinstance(value, ast.Attribute) and value.attr == 'get' and ast.unparse(value.value) in sessions or isinstance(value, ast.Name) and value.id in getters:
                            getters.add(key)
                        if named_get(value): named.add(key)
                        origin = slot(value) or identities.get(symbol(value))
                        if origin:
                            identities[key] = origin; frames.add(origin[0])
                        if raw_packet(value, packets): packets.add(key)
                    elif isinstance(target, (ast.Tuple, ast.List)):
                        values = value.elts if isinstance(value, (ast.Tuple, ast.List)) else []
                        origin = slot(value)
                        for index, name in enumerate(target.elts):
                            if not isinstance(name, ast.Name): continue
                            item = slot(values[index]) if index < len(values) else None
                            if origin and origin[1] == '5:7' and index < 2: item = origin[0], str(index + 5)
                            if item: identities[name.id] = item; frames.add(item[0])
            if repr((sessions, getters, named, identities, frames, packets)) == before: break
        for node in nodes:
            if isinstance(node, ast.Compare):
                for part in (node.left, *node.comparators):
                    origin = slot(part)
                    if origin and origin[1] in ('0:5', '0:7', '5:7'): frames.add(origin[0])
        tables[scope] = (sessions, getters, named_get, identities, frames, packets, resolve)
        for node in nodes:
            if isinstance(node, ast.Compare):
                def identity_operand(part):
                    if isinstance(part, ast.Name): return part.id in identities
                    origin = slot(part)
                    if origin: return origin[0] in frames and origin[1] != '0:5'
                    part = unwrap(part)
                    return isinstance(part, (ast.Tuple, ast.List)) and any(identity_operand(x) for x in part.elts)
                parts = (node.left, *node.comparators)
                if any(identity_operand(x) for x in parts) and any(numeric(x) or raw_packet(x, packets) for x in parts):
                    report(node, 'raw_dispatch')
                for part in parts:
                    if isinstance(part, ast.Subscript) and isinstance(part.slice, ast.Slice) and literal(part.slice.lower) == 1 and literal(part.slice.upper) == 3:
                        if any(isinstance(literal(other), bytes) and len(literal(other)) == 2 for other in parts):
                            report(node, 'raw_dispatch')
                    if isinstance(part, ast.Call) and isinstance(part.func, ast.Attribute) and part.func.attr == 'startswith' and part.args:
                        if raw_packet(part.args[0], packets): report(part, 'raw_dispatch')
            if isinstance(node, ast.Return) and node.value and raw_packet(node.value, packets):
                function = scope if isinstance(scope, ast.FunctionDef) else None
                if function and len(function.args.args) >= 2:
                    header = ast.unparse(node.value)
                    if any(a.arg in header for a in function.args.args if a.arg not in ('self',)):
                        report(node, 'raw_send', 'Raw command encoder: ' + header)
            if isinstance(node, ast.Call):
                if symbol(node.func) in ('send', '_send', 'write') and node.args and raw_packet(node.args[0], packets):
                    report(node, 'raw_send')
                if symbol(node.func) in command_types:
                    report(node, 'raw_dispatch', 'Raw command constructor: ' + ast.unparse(node))
                is_get = (isinstance(node.func, ast.Name) and node.func.id in getters or
                          isinstance(node.func, ast.Attribute) and node.func.attr == 'get' and ast.unparse(node.func.value) in sessions)
                if is_get and node.args and not named_get(node.args[0]):
                    negative_boundary = (path == 'tests/test_named_commands.py'
                        and getattr(scope, 'name', '') == 'test_serial_named_requests_keep_their_wire_and_response_lengths'
                        and ast.unparse(node) == 'session.get(selector)')
                    ancestor = parents.get(node)
                    guarded = False
                    while ancestor is not None and ancestor is not scope:
                        if isinstance(ancestor, ast.With):
                            guarded |= any(isinstance(item.context_expr, ast.Call)
                                and symbol(item.context_expr.func) == 'assertRaisesRegex'
                                and [ast.unparse(arg) for arg in item.context_expr.args] == ['TypeError', "'SerialGet'"]
                                for item in ancestor.items)
                        ancestor = parents.get(ancestor)
                    if negative_boundary and guarded:
                        text_fixtures.append(dict(path=path, line=node.lineno, expression=ast.unparse(node),
                            reason='Exact non-member selector rejection test, guarded by TypeError assertion'))
                    else:
                        report(node, 'serial_selectors')
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'startswith' and node.args and raw_packet(node.args[0], packets):
                    report(node, 'raw_dispatch')
    for node in ast.walk(tree):
        if cli_exception(path, node, parents):
            cli_exclusions.append(dict(path=path, line=node.lineno,
                expression='Probe.command(self, line)' if isinstance(node, ast.FunctionDef) else ast.unparse(node),
                reason='Existing unrelated diagnostic text CLI'))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (node.name in LEGACY or node.name == 'command' and not cli_exception(path, node, parents)):
            report(node, 'legacy_definitions')
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for name in node.names:
                if name.name.rsplit('.', 1)[-1] in LEGACY: report(node, 'legacy_imports')
        if isinstance(node, (ast.Name, ast.Attribute)) and (symbol(node) in LEGACY or isinstance(node, ast.Attribute) and node.attr == 'command' and not cli_exception(path, node, parents)):
            parent = parents.get(node)
            if isinstance(parent, ast.Call) and parent.func is node: report(node, 'legacy_calls')
            else: report(node, 'legacy_references')
        if isinstance(node, ast.Call) and symbol(node.func) in ('getattr', 'hasattr', 'setattr') and len(node.args) > 1 and literal(node.args[1]) in LEGACY:
            report(node, 'legacy_references')
        expression = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('exec', 'compile', 'run') and node.args:
            if not (symbol(node.func) == 'exec' and isinstance(node.args[0], ast.Call) and symbol(node.args[0].func) == 'compile'):
                expression = node.args[0]
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Attribute) and t.attr == 'text' and symbol(t.value) != 'par' for t in targets):
                expression = node.value
        if expression is not None:
            scope = scope_for[node]
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(literal(expression), str) and (path, getattr(scope, 'name', ''), literal(expression)) in TEXT_FIXTURES:
                text_fixtures.append(dict(path=path, line=node.lineno, value=literal(expression), reason='Non-executable DAT corruption fixture'))
                continue
            resolve = tables[scope_for[node]][6]
            value = resolve(expression)
            if value is None:
                dynamic.append(dict(path=path, line=node.lineno, expression=ast.unparse(expression)))
            elif depth >= 8:
                report(node, 'syntax', 'Literal executable nesting exceeds finite limit')
            else:
                nested_path = path + ':snippet@' + str(node.lineno)
                snippets.append(dict(path=nested_path, line=node.lineno))
                nested = scan_source(value, nested_path, depth + 1)
                findings.extend(nested['findings']); snippets.extend(nested['snippets']); dynamic.extend(nested['dynamic']); text_fixtures.extend(nested.get('text_fixtures', [])); cli_exclusions.extend(nested.get('cli_exclusions', []))
    return dict(findings=findings, snippets=snippets, dynamic=dynamic, text_fixtures=text_fixtures, cli_exclusions=cli_exclusions)


def scan(root):
    root = Path(root).resolve()
    files = sorted(p for name in ROOTS for p in (root / name).rglob('*.py') if '__pycache__' not in p.parts)
    findings, snippets, dynamic, text_fixtures, cli_exclusions = [], [], [], [], []
    for path in files:
        result = scan_source(path.read_text(encoding='utf-8'), path.relative_to(root).as_posix())
        findings.extend(result['findings']); snippets.extend(result['snippets']); dynamic.extend(result['dynamic']); text_fixtures.extend(result.get('text_fixtures', [])); cli_exclusions.extend(result.get('cli_exclusions', []))
    totals = {category: 0 for category in CATEGORIES}; totals.update(Counter(x['category'] for x in findings))
    return dict(root=str(root), roots=list(ROOTS), files=len(files), literal_snippets=len(snippets),
                categories=totals, zero=not findings, findings=findings, snippets=snippets, exclusions=EXCLUSIONS,
                dynamic_execution=dynamic, fixture_exclusions=text_fixtures, cli_exclusions=cli_exclusions, coverage_limits=['Lexical direct aliases and documented wire-identity shapes only',
                    'Dynamic executable expressions are listed; arbitrary reflection and generated source are not evaluated'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--json', type=Path, help='Also retain the complete report at this path')
    args = parser.parse_args(argv)
    result = scan(args.root)
    encoded = json.dumps(result, indent=2)
    if args.json: args.json.write_text(encoded + '\n', encoding='utf-8')
    for item in result['findings']:
        print(f"{item['path']}:{item['line']}: {item['category']}: {item['expression']}")
    print(json.dumps({key: result[key] for key in ('root', 'roots', 'files', 'literal_snippets', 'categories', 'zero', 'exclusions', 'coverage_limits')}))
    print('Dynamic executable expressions listed in JSON report:', len(result['dynamic_execution']))
    return 0 if result['zero'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
