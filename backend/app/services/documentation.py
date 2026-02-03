from typing import Any, Dict, List

from app.core.database import SessionLocal
from app.models.documentation import Documentation, DocType
from app.models.repository_file import RepositoryFile
from app.models.repository import Repository
from app.models.repository_cache import RepositoryCache
from app.services.llm import LLMService
from app.utils.prompts import README_PROMPT_TEMPLATE, API_DOCS_PROMPT_TEMPLATE

MAX_TREE_LINES = 300
MAX_SUMMARY_LINES = 300
MAX_SECTION_CHARS = 12000
MAX_API_SECTION_CHARS = 6000
MAX_API_FILES = 120


def generate_readme(repo_id: int) -> Dict[str, Any]:
    """
    Generate and persist a README for a repository using cached analysis data.
    """
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return {"status": "not_found", "repo_id": repo_id}

        # Prefer cached analysis so README generation is fast and deterministic.
        cache = db.query(RepositoryCache).filter(
            RepositoryCache.repository_id == repo.id,
            RepositoryCache.cache_type == "analysis",
        ).first()

        if not cache or not cache.payload:
            return {"status": "missing_analysis", "repo_id": repo_id}

        payload = cache.payload
        code_tree = _truncate_text(
            _render_tree(payload.get("file_tree")), MAX_SECTION_CHARS
        )
        file_summaries = _truncate_text(
            _summarize_files(payload.get("files", [])), MAX_SECTION_CHARS
        )

        prompt = README_PROMPT_TEMPLATE.format(
            repo_name=repo.name,
            repo_description=repo.description or "Not specified",
            code_tree=code_tree,
            file_summaries=file_summaries,
        )

        llm = LLMService()
        content = llm.generate_text(prompt, model="deepseek-coder:6.7b")
        content = content.strip()

        existing = db.query(Documentation).filter(
            Documentation.repository_id == repo.id,
            Documentation.doc_type == DocType.README,
        ).first()

        if existing:
            existing.content = content
        else:
            existing = Documentation(
                repository_id=repo.id,
                doc_type=DocType.README,
                content=content,
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        return {"status": "completed", "repo_id": repo.id, "doc_id": existing.id}
    finally:
        db.close()


def generate_api_docs(repo_id: int) -> Dict[str, Any]:
    """
    Generate and persist API documentation for a repository using cached analysis data.
    """
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return {"status": "not_found", "repo_id": repo_id}

        # Use parsed repository_files if available; fall back to cached analysis.
        files = db.query(RepositoryFile).filter(
            RepositoryFile.repository_id == repo.id
        ).all()

        if files:
            grouped = _group_functions_by_module_from_db(files)
        else:
            cache = db.query(RepositoryCache).filter(
                RepositoryCache.repository_id == repo.id,
                RepositoryCache.cache_type == "analysis",
            ).first()

            if not cache or not cache.payload:
                return {"status": "missing_analysis", "repo_id": repo_id}

            payload = cache.payload
            grouped = _group_functions_by_module(payload.get("files", []))

        prompt = API_DOCS_PROMPT_TEMPLATE.format(
            repo_name=repo.name,
            repo_description=repo.description or "Not specified",
            function_signatures=_truncate_text(grouped["signatures"], MAX_API_SECTION_CHARS),
            docstrings=_truncate_text(grouped["docstrings"], MAX_API_SECTION_CHARS),
        )

        llm = LLMService()
        content = llm.generate_text(prompt, model="deepseek-coder:6.7b").strip()

        existing = db.query(Documentation).filter(
            Documentation.repository_id == repo.id,
            Documentation.doc_type == DocType.API,
        ).first()

        if existing:
            existing.content = content
        else:
            existing = Documentation(
                repository_id=repo.id,
                doc_type=DocType.API,
                content=content,
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        return {"status": "completed", "repo_id": repo.id, "doc_id": existing.id}
    finally:
        db.close()


def _render_tree(tree: Dict[str, Any] | None) -> str:
    if not tree:
        return "TBD"

    lines: List[str] = []
    _walk_tree(tree, lines, depth=0, max_lines=MAX_TREE_LINES)
    return "\n".join(lines) if lines else "TBD"


def _walk_tree(
    node: Dict[str, Any],
    lines: List[str],
    depth: int,
    max_lines: int,
) -> None:
    if len(lines) >= max_lines:
        return
    name = node.get("name", "")
    if name:
        prefix = "  " * depth
        lines.append(f"{prefix}- {name}/" if node.get("type") == "dir" else f"{prefix}- {name}")
        if len(lines) >= max_lines:
            return

    for child in node.get("children", []):
        _walk_tree(child, lines, depth + 1, max_lines)


def _summarize_files(files: List[Dict[str, Any]]) -> str:
    if not files:
        return "TBD"

    lines: List[str] = []
    for item in files[:MAX_SUMMARY_LINES]:
        path = item.get("path", "unknown")
        language = item.get("language", "unknown")
        line = f"- {path} ({language})"
        if language == "python":
            functions = item.get("functions", [])
            classes = item.get("classes", [])
            parts = []
            if functions:
                parts.append(f"functions: {', '.join(f.get('name', '') for f in functions[:6])}")
            if classes:
                parts.append(f"classes: {', '.join(c.get('name', '') for c in classes[:6])}")
            if parts:
                line = f"{line} - " + "; ".join(parts)
        lines.append(line)

    return "\n".join(lines)

def _group_functions_by_module(files: List[Dict[str, Any]]) -> Dict[str, str]:
    if not files:
        return {"signatures": "TBD", "docstrings": "TBD"}

    sig_lines: List[str] = []
    doc_lines: List[str] = []

    for item in files[:MAX_API_FILES]:
        if item.get("language") != "python":
            continue

        path = item.get("path", "unknown")
        functions = item.get("functions", [])
        if not functions:
            continue

        sig_lines.append(f"{path}")
        doc_lines.append(f"{path}")

        for func in functions[:20]:
            signature = func.get("signature") or func.get("name", "unknown")
            sig_lines.append(f"- {signature}")

            doc = func.get("docstring") or "TBD"
            doc_lines.append(f"- {signature}: {doc}")

        sig_lines.append("")
        doc_lines.append("")

    signatures = "\n".join(sig_lines).strip() or "TBD"
    docstrings = "\n".join(doc_lines).strip() or "TBD"
    return {"signatures": signatures, "docstrings": docstrings}


def _group_functions_by_module_from_db(files: List[RepositoryFile]) -> Dict[str, str]:
    if not files:
        return {"signatures": "TBD", "docstrings": "TBD"}

    sig_lines: List[str] = []
    doc_lines: List[str] = []

    for item in files[:MAX_API_FILES]:
        if item.language != "python":
            continue
        payload = item.payload or {}
        functions = payload.get("functions", [])
        if not functions:
            continue

        sig_lines.append(item.path)
        doc_lines.append(item.path)

        for func in functions[:20]:
            signature = func.get("signature") or func.get("name", "unknown")
            sig_lines.append(f"- {signature}")

            doc = func.get("docstring") or "TBD"
            doc_lines.append(f"- {signature}: {doc}")

        sig_lines.append("")
        doc_lines.append("")

    signatures = "\n".join(sig_lines).strip() or "TBD"
    docstrings = "\n".join(doc_lines).strip() or "TBD"
    return {"signatures": signatures, "docstrings": docstrings}


def _truncate_text(text: str, max_chars: int) -> str:
    if not text:
        return "TBD"
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + "\n... [truncated]"
