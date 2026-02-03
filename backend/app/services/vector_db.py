from typing import Any, Dict, List, Optional
import zlib

from qdrant_client import QdrantClient, models

from app.config import settings
from app.services.embeddings import EmbeddingService


class VectorDBService:
    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or settings.QDRANT_URL
        self.client = QdrantClient(url=self.url)
        self.embedding_service = EmbeddingService()

    def create_collection(
        self,
        name: str,
        vector_size: int = 1536,
        distance: models.Distance = models.Distance.COSINE,
        recreate: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a Qdrant collection with vector + payload schema.
        """
        if not name:
            raise ValueError("Collection name is required")

        if self._collection_exists(name):
            if not recreate:
                return {"status": "exists", "collection": name}
            self.client.delete_collection(collection_name=name)

        self.client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=vector_size, distance=distance),
        )

        payload_schema = {
            "repo_id": models.PayloadSchemaType.INTEGER,
            "path": models.PayloadSchemaType.KEYWORD,
            "language": models.PayloadSchemaType.KEYWORD,
            "doc_type": models.PayloadSchemaType.KEYWORD,
            "symbol": models.PayloadSchemaType.KEYWORD,
            "chunk_index": models.PayloadSchemaType.INTEGER,
            "content": models.PayloadSchemaType.TEXT,
        }

        for field_name, field_type in payload_schema.items():
            try:
                self.client.create_payload_index(
                    collection_name=name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except Exception:
                # Ignore if index already exists (version differences)
                pass

        return {
            "status": "created",
            "collection": name,
            "vector_size": vector_size,
            "distance": distance.value,
        }

    def search_code(
        self,
        query: str,
        repo_id: int,
        collection_name: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not query:
            raise ValueError("query is required")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        vector = self.embedding_service.generate_embedding(query)

        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="repo_id",
                    match=models.MatchValue(value=repo_id),
                )
            ]
        )

        # Newer qdrant-client uses query_points; keep search for backward compatibility.
        if hasattr(self.client, "search"):
            results = self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=top_k,
                with_payload=True,
                query_filter=query_filter,
            )
        else:
            response = self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=top_k,
                with_payload=True,
                query_filter=query_filter,
            )
            results = getattr(response, "points", response)

        return [
            {
                "score": result.score,
                "id": result.id,
                "payload": result.payload,
            }
            for result in results
        ]

    def upsert_code_chunks(
        self,
        repo_id: int,
        collection_name: str,
        file_path: str,
        chunks: List[Dict[str, Any]],
    ) -> None:
        if not chunks:
            return

        points = []
        for chunk in chunks:
            content = chunk.get("code", "")
            if not content:
                continue
            chunk_index = chunk.get("chunk_index", 0)
            point_id = self._point_id(repo_id, file_path, chunk_index)
            vector = self.embedding_service.generate_embedding(content)

            payload = {
                "repo_id": repo_id,
                "path": file_path,
                "language": chunk.get("language"),
                "doc_type": chunk.get("type"),
                "symbol": chunk.get("name"),
                "chunk_index": chunk_index,
                "content": content,
            }
            points.append(models.PointStruct(id=point_id, vector=vector, payload=payload))

        if points:
            self.client.upsert(collection_name=collection_name, points=points)

    def delete_by_path(self, repo_id: int, collection_name: str, file_path: str) -> None:
        self.client.delete(
            collection_name=collection_name,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(key="repo_id", match=models.MatchValue(value=repo_id)),
                    models.FieldCondition(key="path", match=models.MatchValue(value=file_path)),
                ]
            ),
        )

    def _point_id(self, repo_id: int, file_path: str, chunk_index: int) -> int:
        checksum = zlib.crc32(f"{file_path}:{chunk_index}".encode("utf-8")) % 1_000_000
        return repo_id * 1_000_000 + checksum

    def _collection_exists(self, name: str) -> bool:
        try:
            return self.client.collection_exists(collection_name=name)
        except AttributeError:
            collections = self.client.get_collections()
            return any(col.name == name for col in collections.collections)
