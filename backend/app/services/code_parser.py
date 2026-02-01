from typing import Any, Dict, List, Union
import tree_sitter_python
from tree_sitter import Language, Parser, Tree

class CodeParserService:
    _LANGUAGE = None

    def __init__(self):
        # Load the Python language
        # The tree-sitter-python package exposes the language binary directly
        if CodeParserService._LANGUAGE is None:
            CodeParserService._LANGUAGE = Language(tree_sitter_python.language(), "python")
        
        # Initialize parser
        self.parser = Parser(CodeParserService._LANGUAGE)

    def parse_python_file(self, content: bytes) -> Dict[str, Any]:
        """
        Parses the given Python source code content and returns the AST structure.
        
        Args:
            content (bytes): The Python source code encoded as bytes.
            
        Returns:
            Dict[str, Any]: A dictionary containing the Tree-sitter AST and a
            serializable AST structure.
        """
        try:
            tree = self.parser.parse(content or b"")
            return {
                "tree": tree,
                "ast": self._node_to_dict(tree.root_node),
            }
        except ValueError as e:
            raise ValueError(f"Parsing failed. Ensure tree-sitter and tree-sitter-python versions are compatible (e.g., 0.23.0). Error: {e}")

    def extract_function_names(self, tree_data: Union[Tree, Dict[str, Any]]) -> List[str]:
        """
        Extracts names of all functions defined in the AST.
        
        Args:
            tree_data (Tree | Dict[str, Any]): The parsed Tree-sitter AST or
                the dictionary returned by parse_python_file.
            
        Returns:
            List[str]: A list of function names.
        """
        tree = tree_data["tree"] if isinstance(tree_data, dict) else tree_data
        query_scm = """
        (function_definition
          name: (identifier) @function.name)
        """
        query = self._LANGUAGE.query(query_scm)
        captures = query.captures(tree.root_node)
        
        return [node.text.decode('utf-8') for node, _ in captures]

    def extract_class_names(self, tree_data: Union[Tree, Dict[str, Any]]) -> List[str]:
        """
        Extracts names of all classes defined in the AST.
        """
        tree = tree_data["tree"] if isinstance(tree_data, dict) else tree_data
        query_scm = """
        (class_definition
          name: (identifier) @class.name)
        """
        query = self._LANGUAGE.query(query_scm)
        captures = query.captures(tree.root_node)
        
        return [node.text.decode('utf-8') for node, _ in captures]

    def _node_to_dict(self, node) -> Dict[str, Any]:
        """Convert a Tree-sitter node into a serializable dictionary."""
        return {
            "type": node.type,
            "start_point": node.start_point,
            "end_point": node.end_point,
            "children": [self._node_to_dict(child) for child in node.children],
        }
