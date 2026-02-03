from typing import Any, Dict, List, Optional
import tree_sitter_python
from tree_sitter import Language, Parser, Tree
import ast

class CodeParserService:
    _LANGUAGE = None

    def __init__(self):
        # Load the Python language with compatibility for different tree-sitter-python APIs.
        if CodeParserService._LANGUAGE is None:
            language = tree_sitter_python.language()
            if isinstance(language, Language):
                CodeParserService._LANGUAGE = language
            else:
                try:
                    CodeParserService._LANGUAGE = Language(language)
                except TypeError:
                    # Fall back to the provided object if Language() is not compatible.
                    CodeParserService._LANGUAGE = language

        # Initialize parser with compatibility for different tree-sitter APIs.
        parser = Parser()
        try:
            parser.set_language(CodeParserService._LANGUAGE)
        except AttributeError:
            parser = Parser(CodeParserService._LANGUAGE)
        self.parser = parser

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

    def extract_functions(self, tree: Tree, content: bytes) -> List[Dict[str, Any]]:
        """
        Extracts structured data about functions, including parameters,
        return types (if annotated), and docstrings.
        """
        if not content:
            return []

        functions: List[Dict[str, Any]] = []
        stack = [tree.root_node]

        while stack:
            node = stack.pop()
            if node.type == "function_definition":
                functions.append(self._build_function_data(node, content))
            stack.extend(node.named_children)

        return functions

    def extract_classes(self, tree: Tree, content: bytes) -> List[Dict[str, Any]]:
        """
        Extracts structured data about classes, including methods, attributes,
        docstrings, and inheritance hierarchy.
        """
        if not content:
            return []

        classes: List[Dict[str, Any]] = []
        for node in tree.root_node.named_children:
            if node.type == "class_definition":
                classes.append(self._build_class_data(node, content, parent_name=None))

        return classes

    def _build_function_data(self, node, content: bytes) -> Dict[str, Any]:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        return_node = node.child_by_field_name("return_type")
        body_node = node.child_by_field_name("body")

        if body_node is None:
            body_node = next((child for child in node.named_children if child.type == "block"), None)

        name = self._node_text(content, name_node) if name_node else ""
        params_text = self._node_text(content, params_node) if params_node else "()"
        return_type = self._node_text(content, return_node) if return_node else None

        parameters = []
        if params_node:
            for child in params_node.named_children:
                if child.type == "comment":
                    continue
                parameters.append(self._node_text(content, child))

        signature = f"def {name}{params_text}"
        if return_type:
            signature += f" -> {return_type}"

        return {
            "name": name,
            "signature": signature,
            "parameters": parameters,
            "parameters_text": params_text,
            "return_type": return_type,
            "docstring": self._extract_docstring(body_node, content),
        }

    def _build_class_data(
        self, node, content: bytes, parent_name: Optional[str]
    ) -> Dict[str, Any]:
        name_node = node.child_by_field_name("name")
        body_node = node.child_by_field_name("body")
        bases_node = node.child_by_field_name("superclasses")

        name = self._node_text(content, name_node) if name_node else ""
        qualified_name = f"{parent_name}.{name}" if parent_name else name

        bases = []
        if bases_node:
            for child in bases_node.named_children:
                if child.type == "comment":
                    continue
                bases.append(self._node_text(content, child))

        methods = self._extract_class_methods(body_node, content)
        attributes = self._extract_class_attributes(body_node, content)
        docstring = self._extract_docstring(body_node, content)
        nested_classes = self._extract_nested_classes(body_node, content, qualified_name)

        return {
            "name": name,
            "qualified_name": qualified_name,
            "bases": bases,
            "docstring": docstring,
            "attributes": attributes,
            "methods": methods,
            "nested_classes": nested_classes,
        }

    def _extract_class_methods(self, body_node, content: bytes) -> List[Dict[str, Any]]:
        if body_node is None:
            return []

        methods: List[Dict[str, Any]] = []
        for child in body_node.named_children:
            if child.type == "function_definition":
                methods.append(self._build_function_data(child, content))
        return methods

    def _extract_class_attributes(self, body_node, content: bytes) -> List[str]:
        if body_node is None:
            return []

        attributes: List[str] = []
        for child in body_node.named_children:
            if child.type in {"assignment", "annotated_assignment"}:
                attributes.extend(self._assignment_targets(child, content))
                continue

            if child.type == "expression_statement":
                for expr_child in child.named_children:
                    if expr_child.type in {"assignment", "annotated_assignment"}:
                        attributes.extend(self._assignment_targets(expr_child, content))
        return attributes

    def _assignment_targets(self, node, content: bytes) -> List[str]:
        if node.type == "assignment":
            left = node.child_by_field_name("left")
            if left is None and node.named_children:
                left = node.named_children[0]
            return self._collect_identifiers(left, content)

        if node.type == "annotated_assignment":
            target = node.child_by_field_name("left")
            if target is None:
                target = node.child_by_field_name("target")
            return self._collect_identifiers(target, content)

        return []

    def _collect_identifiers(self, node, content: bytes) -> List[str]:
        if node is None:
            return []

        if node.type == "identifier":
            return [self._node_text(content, node)]

        identifiers: List[str] = []
        for child in node.named_children:
            if child.type == "identifier":
                identifiers.append(self._node_text(content, child))
            else:
                identifiers.extend(self._collect_identifiers(child, content))
        return identifiers

    def _extract_nested_classes(
        self, body_node, content: bytes, parent_name: str
    ) -> List[Dict[str, Any]]:
        if body_node is None:
            return []

        nested: List[Dict[str, Any]] = []
        for child in body_node.named_children:
            if child.type == "class_definition":
                nested.append(self._build_class_data(child, content, parent_name=parent_name))
        return nested

    def _extract_docstring(self, body_node, content: bytes) -> Optional[str]:
        if body_node is None:
            return None

        first_named = next(iter(body_node.named_children), None)
        if first_named is None:
            return None

        if first_named.type == "expression_statement" and first_named.named_children:
            first_named = first_named.named_children[0]

        if first_named.type in {"string", "string_literal", "concatenated_string"}:
            raw = self._node_text(content, first_named)
            return self._clean_docstring(raw)

        return None

    def _clean_docstring(self, raw: str) -> str:
        try:
            return ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return raw

    def _node_text(self, content: bytes, node) -> str:
        if node is None:
            return ""
        return content[node.start_byte:node.end_byte].decode("utf-8")
