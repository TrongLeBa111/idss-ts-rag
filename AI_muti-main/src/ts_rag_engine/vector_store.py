"""
src/ts_rag_engine/vector_store.py
FAISS-backed vector store with metadata persistence.
Default dimension = 256 (matches EmbeddingGenerator.DIM).
"""
import numpy as np
import pickle
from pathlib import Path


class FAISSVectorStore:
    """
    Wraps a FAISS IndexFlatL2 index with a parallel metadata list.
    Supports add / search / save / load.
    """

    def __init__(self, dimension: int = 256):  # fixed: was 384
        import faiss
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: list = []
        self._faiss = faiss

    # ------------------------------------------------------------------
    def add_embedding(self, embedding: np.ndarray, metadata: dict) -> None:
        vec = embedding.reshape(1, -1).astype("float32")
        self.index.add(vec)
        self.metadata.append(metadata)

    def add_batch(self, embeddings: np.ndarray, metadatas: list) -> None:
        assert len(embeddings) == len(metadatas)
        self.index.add(embeddings.astype("float32"))
        self.metadata.extend(metadatas)
        print(f"✅ Added {len(metadatas)} embeddings — total: {self.index.ntotal}")

    # ------------------------------------------------------------------
    def search(self, query: np.ndarray, k: int = 5) -> list:
        """Return top-k (metadata, distance) pairs."""
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        q = query.reshape(1, -1).astype("float32")
        distances, indices = self.index.search(q, k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx >= 0:
                results.append((self.metadata[idx], float(dist)))
        return results

    def similarity_score(self, distance: float) -> float:
        """Convert L2 distance → 0-1 similarity (higher = more similar)."""
        return float(1 / (1 + distance))

    # ------------------------------------------------------------------
    def save(self, directory: str) -> None:
        import faiss
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "index.faiss"))
        with open(path / "metadata.pkl", "wb") as f:
            pickle.dump(self.metadata, f)
        print(f"💾 Saved FAISS index ({self.index.ntotal} vectors) → {path}")

    def load(self, directory: str) -> None:
        import faiss
        path = Path(directory)
        self.index = faiss.read_index(str(path / "index.faiss"))
        with open(path / "metadata.pkl", "rb") as f:
            self.metadata = pickle.load(f)
        print(f"📂 Loaded FAISS index ({self.index.ntotal} vectors) from {path}")

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal


# ------------------------------------------------------------------
if __name__ == "__main__":
    DIM = 256
    vs = FAISSVectorStore(DIM)

    for i in range(20):
        emb = np.random.rand(DIM).astype("float32")
        vs.add_embedding(emb, {"id": i, "category": "Furniture", "yearmonth": f"2017-{i+1:02d}"})

    query = np.random.rand(DIM).astype("float32")
    results = vs.search(query, k=3)
    print(f"\nTop-3 results:")
    for meta, dist in results:
        print(f"  {meta}  |  sim={vs.similarity_score(dist):.3f}")

    vs.save("data/test_faiss")
    vs2 = FAISSVectorStore(DIM)
    vs2.load("data/test_faiss")
    assert vs2.total_vectors == 20
    print("✅ Save/load round-trip passed")
