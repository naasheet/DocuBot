import os
from typing import Any, Dict, List


class RepoFileService:
    def __init__(self) -> None:
        self._extensions = {".py", ".js", ".ts"}
        self._ignore_dirs = {".git", "node_modules", "__pycache__"}

    def get_repo_file_tree(self, root_path: str) -> Dict[str, Any]:
        """
        Walk the repository and return a filtered file tree structure.
        Only files with configured extensions are included.
        """
        if not root_path or not os.path.isdir(root_path):
            raise ValueError("root_path must be an existing directory")

        root_path = os.path.abspath(root_path)
        root_node: Dict[str, Any] = {
            "name": os.path.basename(root_path.rstrip(os.sep)) or root_path,
            "path": "",
            "type": "dir",
            "children": [],
        }
        index = {"": root_node}

        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if d not in self._ignore_dirs]
            rel_dir = os.path.relpath(dirpath, root_path)
            if rel_dir == ".":
                rel_dir = ""

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in self._extensions:
                    continue

                rel_file = os.path.join(rel_dir, filename) if rel_dir else filename
                self._insert_file(root_node, index, rel_file, filename)

        self._sort_tree(root_node)
        return root_node

    def _insert_file(
        self,
        root_node: Dict[str, Any],
        index: Dict[str, Dict[str, Any]],
        rel_file: str,
        filename: str,
    ) -> None:
        dir_part = os.path.dirname(rel_file)
        parent = root_node
        if dir_part:
            parent = self._ensure_dir(root_node, index, dir_part)

        file_node = {
            "name": filename,
            "path": rel_file.replace(os.sep, "/"),
            "type": "file",
        }
        parent["children"].append(file_node)

    def _ensure_dir(
        self,
        root_node: Dict[str, Any],
        index: Dict[str, Dict[str, Any]],
        rel_dir: str,
    ) -> Dict[str, Any]:
        current_path = ""
        current_node = root_node
        for part in rel_dir.split(os.sep):
            current_path = os.path.join(current_path, part) if current_path else part
            node = index.get(current_path)
            if node is None:
                node = {
                    "name": part,
                    "path": current_path.replace(os.sep, "/"),
                    "type": "dir",
                    "children": [],
                }
                current_node["children"].append(node)
                index[current_path] = node
            current_node = node
        return current_node

    def _sort_tree(self, node: Dict[str, Any]) -> None:
        children: List[Dict[str, Any]] = node.get("children", [])
        if not children:
            return

        children.sort(key=lambda item: (item.get("type") != "dir", item.get("name", "")))
        for child in children:
            if child.get("type") == "dir":
                self._sort_tree(child)
