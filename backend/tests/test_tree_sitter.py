import pytest

def test_tree_sitter_installation():
    """
    Verify that tree-sitter and the Python grammar are installed
    and can be initialized correctly.
    """
    try:
        import tree_sitter
        import tree_sitter_python
        from tree_sitter import Language, Parser
    except ImportError as e:
        pytest.fail(f"Failed to import tree-sitter dependencies: {e}")

    try:
        # Load the Python language
        # The tree-sitter-python package exposes the language binary directly
        PY_LANGUAGE = Language(tree_sitter_python.language(), "python")
        
        # Initialize parser
        parser = Parser(PY_LANGUAGE)
        
        # Test parsing a simple Python snippet
        tree = parser.parse(b"def hello(): pass")
        assert tree.root_node.type == "module"
    except Exception as e:
        pytest.fail(f"Tree-sitter functionality check failed: {e}")