"""
src/ts_rag_engine/retriever.py
Retrieve similar historical time-series patterns from FAISS.
(Corrected from root-level typo: retriver.py → retriever.py)
"""
import numpy as np
import pandas as pd
from pathlib import Path

from src.ts_rag_engine.vector_store import FAISSVectorStore
from src.ts_rag_engine.embeddings import EmbeddingGenerator


class TimeSeriesRetriever:
    """
    Indexes monthly sales windows into FAISS and retrieves
    the most similar historical periods for any query window.
    """

    def __init__(self, vector_db_path: str = "data/vector_db"):
        self.db_path = vector_db_path
        self.vs = FAISSVectorStore(dimension=256)   # fixed: matched EmbeddingGenerator.DIM
        self.embedder = EmbeddingGenerator()
        self._indexed = False

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------
    def build_index(
        self,
        monthly_df: pd.DataFrame,
        window: int = 6,
        save: bool = True,
    ) -> None:
        """
        Slide a window over the monthly series and embed each window.
        Each embedding stores metadata about that historical period.
        """
        categories = monthly_df["Category"].unique()
        all_embeddings = []
        all_metadata = []

        for cat in categories:
            cat_df = monthly_df[monthly_df["Category"] == cat].sort_values("YearMonth")
            sales_values = cat_df["TotalSales"].values
            years = cat_df["Year"].values
            months = cat_df["Month"].values
            yearmonths = cat_df["YearMonth"].astype(str).values

            for i in range(window - 1, len(cat_df)):
                window_sales = sales_values[i - window + 1: i + 1]
                emb, description = self.embedder.embed_monthly_window(
                    monthly_df, cat, int(years[i]), int(months[i]), window
                )
                meta = {
                    "category": cat,
                    "year": int(years[i]),
                    "month": int(months[i]),
                    "yearmonth": yearmonths[i],
                    "total_sales": float(np.sum(window_sales)),
                    "avg_sales": float(np.mean(window_sales)),
                    "peak_sales": float(np.max(window_sales)),
                    "sales_trend_pct": float(
                        (window_sales[-1] - window_sales[0]) / (window_sales[0] + 1e-9) * 100
                    ),
                    "description": description,
                    "window_sales": window_sales.tolist(),
                }
                all_embeddings.append(emb)
                all_metadata.append(meta)

        embeddings_arr = np.stack(all_embeddings)
        self.vs.add_batch(embeddings_arr, all_metadata)
        self._indexed = True

        if save:
            Path(self.db_path).mkdir(parents=True, exist_ok=True)
            self.vs.save(self.db_path)

        print(f"✅ Index built: {self.vs.total_vectors} vectors across {len(categories)} categories")

    def load_index(self) -> None:
        self.vs.load(self.db_path)
        self._indexed = True

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def retrieve(
        self,
        monthly_df: pd.DataFrame,
        category: str,
        year: int,
        month: int,
        top_k: int = 3,
        window: int = 6,
        exclude_same_period: bool = True,
    ) -> list:
        """
        Find top-k historical periods most similar to the given (category, year, month).
        Returns enriched metadata dicts with similarity score.
        """
        if not self._indexed:
            self.load_index()

        query_emb, query_desc = self.embedder.embed_monthly_window(
            monthly_df, category, year, month, window
        )

        raw_results = self.vs.search(query_emb, k=top_k + 5)  # over-fetch, then filter

        results = []
        for meta, dist in raw_results:
            if exclude_same_period and meta["year"] == year and meta["month"] == month:
                continue
            results.append({
                **meta,
                "similarity": self.vs.similarity_score(dist),
                "distance": dist,
                "query_description": query_desc,
            })
            if len(results) >= top_k:
                break

        return results

    def retrieve_from_embedding(self, query_embedding: np.ndarray, top_k: int = 3) -> list:
        """Direct retrieval from a pre-computed embedding."""
        if not self._indexed:
            self.load_index()
        raw = self.vs.search(query_embedding, k=top_k)
        return [
            {**meta, "similarity": self.vs.similarity_score(dist), "distance": dist}
            for meta, dist in raw
        ]


# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    from src.data_pipeline.preprocessor import DataPreprocessor

    _, monthly = DataPreprocessor(
        "data/raw/superstore_sales.csv",
        "data/processed/superstore_sales_cleaned.csv",
    ).run()

    retriever = TimeSeriesRetriever("data/vector_db")
    retriever.build_index(monthly, window=6)

    results = retriever.retrieve(monthly, "Furniture", 2017, 11, top_k=3)
    print("\n📊 Top similar periods for Furniture Nov 2017:")
    for r in results:
        print(f"  {r['yearmonth']} | sim={r['similarity']:.3f} | "
              f"avg=${r['avg_sales']:,.0f} | trend={r['sales_trend_pct']:+.1f}%")
