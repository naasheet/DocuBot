from typing import Any, Dict, List, Optional

from app.services.code_parser import CodeParserService


class CodeChunkingService:
    def __init__(self) -> None:
        self.parser = CodeParserService()

    def chunk_python_file(self, content: bytes, file_path: str) -> List[Dict[str, Any]]:
        if not content:
            return []

        tree = self.parser.parse_python_file(content)
        imports = self._extract_imports(tree, content)
        chunks: List[Dict[str, Any]] = []
        index = 0

        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if node.type == "function_definition":
                chunks.append(
                    self._build_function_chunk(node, content, file_path, imports, index)
                )
                index += 1
            elif node.type == "class_definition":
                chunks.append(
                    self._build_class_chunk(node, content, file_path, imports, index)
                )
                index += 1
            stack.extend(node.named_children)

        return chunks

    def _extract_imports(self, tree, content: bytes) -> List[str]:
        imports: List[str] = []
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if node.type in {"import_statement", "import_from_statement"}:
                imports.append(self._node_text(content, node))
            stack.extend(node.named_children)
        return imports

    def _build_function_chunk(
        self,
        node,
        content: bytes,
        file_path: str,
        imports: List[str],
        index: int,
    ) -> Dict[str, Any]:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        return_node = node.child_by_field_name("return_type")

        name = self._node_text(content, name_node) if name_node else ""
        params_text = self._node_text(content, params_node) if params_node else "()"
        return_type = self._node_text(content, return_node) if return_node else None

        signature = f"def {name}{params_text}"
        if return_type:
            signature += f" -> {return_type}"

        return {
            "type": "function",
            "name": name,
            "signature": signature,
            "file_path": file_path,
            "imports": imports,
            "language": "python",
            "code": self._node_text(content, node),
            "chunk_index": index,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
        }

    def _build_class_chunk(
        self,
        node,
        content: bytes,
        file_path: str,
        imports: List[str],
        index: int,
    ) -> Dict[str, Any]:
        name_node = node.child_by_field_name("name")
        bases_node = node.child_by_field_name("superclasses")

        name = self._node_text(content, name_node) if name_node else ""
        bases = []
        if bases_node:
            for child in bases_node.named_children:
                bases.append(self._node_text(content, child))

        signature = f"class {name}"
        if bases:
            signature += f"({', '.join(bases)})"

        return {
            "type": "class",
            "name": name,
            "signature": signature,
            "file_path": file_path,
            "imports": imports,
            "language": "python",
            "code": self._node_text(content, node),
            "chunk_index": index,
            "start_byte": node.start_byte,
            "end_byte": node.end_byte,
        }

    def _node_text(self, content: bytes, node) -> str:
        if node is None:
            return ""
        return content[node.start_byte:node.end_byte].decode("utf-8")
