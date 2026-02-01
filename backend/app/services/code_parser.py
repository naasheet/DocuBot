from typing import List
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

    def parse_python_file(self, content: bytes) -> Tree:
        """
        Parses the given Python source code content and returns the AST structure.
        
        Args:
            content (bytes): The Python source code encoded as bytes.
            
        Returns:
            Tree: The Tree-sitter AST.
        """
        try:
            if not content:
                return self.parser.parse(b"")
            return self.parser.parse(content)
        except ValueError as e:
            raise ValueError(f"Parsing failed. Ensure tree-sitter and tree-sitter-python versions are compatible (e.g., 0.23.0). Error: {e}")

    def extract_function_names(self, tree: Tree) -> List[str]:
        """
        Extracts names of all functions defined in the AST.
        
        Args:
            tree (Tree): The parsed Tree-sitter AST.
            
        Returns:
            List[str]: A list of function names.
        """
        query_scm = """
        (function_definition
          name: (identifier) @function.name)
        """
        query = self._LANGUAGE.query(query_scm)
        captures = query.captures(tree.root_node)
        
        return [node.text.decode('utf-8') for node, _ in captures]

    def extract_class_names(self, tree: Tree) -> List[str]:
        """
        Extracts names of all classes defined in the AST.
        """
        query_scm = """
        (class_definition
          name: (identifier) @class.name)
        """
        query = self._LANGUAGE.query(query_scm)
        captures = query.captures(tree.root_node)
        
        return [node.text.decode('utf-8') for node, _ in captures]