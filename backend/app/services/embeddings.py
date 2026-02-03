from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self) -> None:
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def generate_embedding(self, text: str) -> List[float]:
        if not text:
            raise ValueError("text is required")
        embedding = self.model.encode([text], normalize_embeddings=True)[0]
        return embedding.tolist()
