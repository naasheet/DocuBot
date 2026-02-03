import os
import shutil
import subprocess
import httpx
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.database import SessionLocal
from app.models.repository import Repository
from app.models.repository_cache import RepositoryCache
from app.models.repository_file import RepositoryFile
from app.models.user import User
from app.services.code_parser import CodeParserService
from app.services.chunking import CodeChunkingService
from app.services.repo_file_tree import RepoFileService
from app.services.documentation import generate_readme, generate_api_docs
from app.workers.celery_app import celery_app
from app.services.vector_db import VectorDBService

@celery_app.task
def generate_documentation(repository_id: int):
    # Task logic here
    pass

@celery_app.task
def index_code(repository_id: int):
    # Task logic here
    pass


@celery_app.task
def analyze_repository(repository_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            return {"status": "not_found", "repository_id": repository_id}

        # Persist status so UI can track progress without polling logs.
        _upsert_cache(db, repo.id, "analysis_status", _status_payload("running"))

        user = db.query(User).filter(User.id == repo.user_id).first()
        if not user or not user.github_access_token:
            _upsert_cache(
                db,
                repo.id,
                "analysis_status",
                _status_payload("failed", error="GitHub token missing"),
            )
            return {"status": "failed", "error": "GitHub token missing"}

        # Clone to a temporary path; it will be cleaned up in finally.
        clone_path = _prepare_clone_path(repo.id)
        _clone_repo(repo.full_name, user.github_access_token, clone_path)

        file_service = RepoFileService()
        file_tree = file_service.get_repo_file_tree(clone_path)
        files = _collect_files(clone_path)

        parser = CodeParserService()
        parsed_files: List[Dict[str, Any]] = []
        for file_path in files:
            rel_path = os.path.relpath(file_path, clone_path).replace(os.sep, "/")
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, "rb") as handle:
                content = handle.read()

            parsed_files.append(
                _parse_file(parser, rel_path, ext, content)
            )

        # Cache the structured analysis for README/API generation.
        analysis_payload = {
            "repository_id": repo.id,
            "file_tree": file_tree,
            "files": parsed_files,
            "summary": {
                "total_files": len(parsed_files),
                "python_files": sum(1 for item in parsed_files if item["language"] == "python"),
                "js_files": sum(1 for item in parsed_files if item["language"] == "javascript"),
                "ts_files": sum(1 for item in parsed_files if item["language"] == "typescript"),
            },
        }

        _upsert_cache(db, repo.id, "analysis", analysis_payload)
        _upsert_cache(db, repo.id, "analysis_status", _status_payload("completed"))

        return {"status": "completed", "repository_id": repo.id}
    except Exception as exc:
        _upsert_cache(db, repository_id, "analysis_status", _status_payload("failed", error=str(exc)))
        raise
    finally:
        _cleanup_clone_path(repository_id)
        db.close()


@celery_app.task
def generate_docs(repository_id: int, doc_type: str = "readme") -> Dict[str, Any]:
    try:
        if doc_type == "api":
            return generate_api_docs(repository_id)
        return generate_readme(repository_id)
    except Exception as exc:
        message = str(exc)
        lowered = message.lower()
        if "rate_limit" in lowered or "tpm" in lowered or "request too large" in lowered or "429" in lowered:
            message = "Prompt limit reached. Please try again shortly."
        return {"status": "failed", "repo_id": repository_id, "error": message}


@celery_app.task
def analyze_changed_files(
    repository_id: int,
    added: List[str],
    modified: List[str],
    removed: List[str],
) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repository_id).first()
        if not repo:
            return {"status": "not_found", "repository_id": repository_id}

        user = db.query(User).filter(User.id == repo.user_id).first()
        if not user or not user.github_access_token:
            return {"status": "failed", "error": "GitHub token missing"}

        collection_name = os.getenv("QDRANT_COLLECTION", "docubot_code")
        vector_service = VectorDBService()
        chunking_service = CodeChunkingService()
        parser = CodeParserService()

        changed_files = _filter_code_files(list(set(added + modified)))
        removed_files = _filter_code_files(removed)

        # Remove deleted files from vector DB and DB cache.
        for path in removed_files:
            vector_service.delete_by_path(repo.id, collection_name, path)
            db.query(RepositoryFile).filter(
                RepositoryFile.repository_id == repo.id,
                RepositoryFile.path == path,
            ).delete()

        # Re-parse only changed files to keep indexing fast.
        for path in changed_files:
            content = _fetch_github_file(repo.full_name, path, user.github_access_token)
            if content is None:
                continue

            ext = os.path.splitext(path)[1].lower()
            if ext == ".py":
                tree = parser.parse_python_file(content)
                functions = parser.extract_functions(tree, content)
                classes = parser.extract_classes(tree, content)
                chunks = chunking_service.chunk_python_file(content, path)
                language = "python"
            else:
                functions = []
                classes = []
                chunks = [
                    {
                        "type": "file",
                        "name": os.path.basename(path),
                        "signature": os.path.basename(path),
                        "file_path": path,
                        "imports": [],
                        "language": "javascript" if ext == ".js" else "typescript",
                        "code": content.decode("utf-8", errors="ignore"),
                        "chunk_index": 0,
                        "start_byte": 0,
                        "end_byte": len(content),
                    }
                ]
                language = "javascript" if ext == ".js" else "typescript"

            vector_service.delete_by_path(repo.id, collection_name, path)
            vector_service.upsert_code_chunks(repo.id, collection_name, path, chunks)

            payload = {
                "functions": functions,
                "classes": classes,
            }

            entry = db.query(RepositoryFile).filter(
                RepositoryFile.repository_id == repo.id,
                RepositoryFile.path == path,
            ).first()

            if entry is None:
                entry = RepositoryFile(
                    repository_id=repo.id,
                    path=path,
                    language=language,
                    payload=payload,
                )
                db.add(entry)
            else:
                entry.language = language
                entry.payload = payload

        db.commit()
        if changed_files:
            generate_docs.delay(repo.id, "api")

        return {
            "status": "completed",
            "repository_id": repo.id,
            "changed_files": len(changed_files),
            "removed_files": len(removed_files),
        }
    finally:
        db.close()


def _filter_code_files(paths: List[str]) -> List[str]:
    allowed = {".py", ".js", ".ts"}
    return [path for path in paths if os.path.splitext(path)[1].lower() in allowed]


def _fetch_github_file(full_name: str, path: str, token: str) -> bytes | None:
    owner, repo = full_name.split("/", 1)
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.raw",
    }
    response = httpx.get(url, headers=headers, timeout=30)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.content


def _prepare_clone_path(repository_id: int) -> str:
    base_dir = "/tmp/docubot/repos"
    os.makedirs(base_dir, exist_ok=True)
    clone_path = os.path.join(base_dir, str(repository_id))
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)
    return clone_path


def _cleanup_clone_path(repository_id: int) -> None:
    clone_path = os.path.join("/tmp/docubot/repos", str(repository_id))
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)


def _clone_repo(full_name: str, token: str, clone_path: str) -> None:
    owner, repo = full_name.split("/", 1)
    clone_url = f"https://{token}@github.com/{owner}/{repo}.git"
    subprocess.run(
        ["git", "clone", "--depth", "1", clone_url, clone_path],
        check=True,
        capture_output=True,
        text=True,
    )


def _collect_files(root_path: str) -> List[str]:
    allowed_extensions = {".py", ".js", ".ts"}
    ignored_dirs = {".git", "node_modules", "__pycache__"}
    results: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in allowed_extensions:
                results.append(os.path.join(dirpath, filename))
    return results


def _parse_file(
    parser: CodeParserService,
    rel_path: str,
    ext: str,
    content: bytes,
) -> Dict[str, Any]:
    if ext == ".py":
        tree = parser.parse_python_file(content)
        functions = parser.extract_functions(tree, content)
        classes = parser.extract_classes(tree, content)
        return {
            "path": rel_path,
            "language": "python",
            "functions": functions,
            "classes": classes,
        }
    if ext == ".js":
        return {"path": rel_path, "language": "javascript"}
    if ext == ".ts":
        return {"path": rel_path, "language": "typescript"}
    return {"path": rel_path, "language": "unknown"}


def _upsert_cache(db, repository_id: int, cache_type: str, payload: Dict[str, Any]) -> None:
    entry = db.query(RepositoryCache).filter(
        RepositoryCache.repository_id == repository_id,
        RepositoryCache.cache_type == cache_type,
    ).first()

    if entry is None:
        entry = RepositoryCache(
            repository_id=repository_id,
            cache_type=cache_type,
            payload=payload,
        )
        db.add(entry)
    else:
        entry.payload = payload

    db.commit()
    db.refresh(entry)


def _status_payload(status: str, error: str | None = None) -> Dict[str, Any]:
    payload = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        payload["error"] = error
    return payload
