from pathlib import Path
import ast

SERVER = Path(__file__).parents[2] / 'services' / 'mcp' / 'server.py'


def _registry():
    tree = ast.parse(SERVER.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == 'CAPABILITY_REGISTRY' for t in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError('CAPABILITY_REGISTRY not found')


def test_mcp_registry_has_exactly_100_unique_tools():
    registry = _registry()
    names = [row[0] for row in registry]
    assert len(registry) == 100
    assert len(set(names)) == 100


def test_mcp_registry_contains_the_execution_primitives():
    names = {row[0] for row in _registry()}
    required = {
        'inspect_part', 'analyze_dfm', 'auto_fix_dfm', 'verify_fixes',
        'generate_manufacturing_package', 'release_manufacturing_package',
        'engineering_agent_run', 'agent_fleet_run', 'agent_step',
        'trace_provenance', 'build_inspection_plan', 'acceptance_gate',
    }
    assert required <= names


def test_mcp_paths_are_non_empty_and_structured():
    for name, description, path in _registry():
        assert name and description
        assert path.startswith('/v1/')
