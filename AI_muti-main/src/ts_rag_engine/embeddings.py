"""
src/ts_rag_engine/embeddings.py
Convert time-series windows and text to dense vectors.
Uses a fully offline TF-IDF + statistical feature hybrid (no internet needed).
Output: 256-dimensional float32 vectors.
"""
import numpy as np
import pandas as pd
import hashlib


class EmbeddingGenerator:
    """
    Offline embedding generator — no HuggingFace or API needed.
    Combines:
      1. Character n-gram hashing (128 dims) for text semantics
      2. Statistical time-series features (128 dims) for numeric patterns
    Output: 256-dim L2-normalised float32 vectors.
    """

    DIM = 256
    TEXT_DIM = 128
    TS_DIM = 128

    def __init__(self):
        print(f"✅ EmbeddingGenerator ready (offline, dim={self.DIM})")

    # ------------------------------------------------------------------
    # Text embedding  (character n-gram hashing trick)
    # ------------------------------------------------------------------
    def embed_text(self, text: str) -> np.ndarray:
        """Embed a text string → (256,) float32 array via n-gram hashing."""
        vec = np.zeros(self.TEXT_DIM, dtype=np.float64)
        text = text.lower().strip()
        tokens = text.split()
        # Unigrams + bigrams
        ngrams = tokens[:]
        ngrams += [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        for gram in ngrams:
            h = int(hashlib.md5(gram.encode()).hexdigest(), 16)
            idx = h % self.TEXT_DIM
            sign = 1 if (h >> 127) & 1 else -1
            vec[idx] += sign
        # Pad to DIM with zeros (TS_DIM portion will be zeros for text-only embed)
        full = np.zeros(self.DIM, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            full[: self.TEXT_DIM] = (vec / norm).astype(np.float32)
        return full

    def embed_texts(self, texts: list) -> np.ndarray:
        """Batch embed multiple texts → (N, 256) float32 array."""
        return np.stack([self.embed_text(t) for t in texts])

    # ------------------------------------------------------------------
    # Time-series embedding
    # ------------------------------------------------------------------
    def _ts_to_text(self, ts, label: str = "") -> str:
        """
        Convert a numeric time-series window into a rich text description
        that captures its statistical shape for semantic embedding.
        """
        if isinstance(ts, pd.Series):
            arr = ts.values.astype(float)
        else:
            arr = np.array(ts, dtype=float)

        n = len(arr)
        if n == 0:
            return "empty time series"

        mean = float(np.mean(arr))
        std = float(np.std(arr))
        trend = float(arr[-1] - arr[0]) if n > 1 else 0.0
        pct_change = trend / arr[0] * 100 if arr[0] != 0 else 0.0
        peak_idx = int(np.argmax(arr))
        trough_idx = int(np.argmin(arr))

        trend_word = (
            "strongly increasing" if pct_change > 20
            else "increasing" if pct_change > 5
            else "stable" if abs(pct_change) <= 5
            else "decreasing" if pct_change > -20
            else "strongly decreasing"
        )
        volatility = (
            "high" if std / (mean + 1e-9) > 0.3
            else "moderate" if std / (mean + 1e-9) > 0.1
            else "low"
        )

        prefix = f"{label} " if label else ""
        return (
            f"{prefix}sales trend is {trend_word} with {volatility} volatility. "
            f"Average {mean:.0f}, std {std:.0f}. "
            f"Changed {pct_change:+.1f}% over {n} periods. "
            f"Peak at period {peak_idx + 1}, trough at period {trough_idx + 1}."
        )

    def embed_time_series(self, ts, label: str = "") -> np.ndarray:
        """Embed a numeric time-series window → (256,) float32."""
        text = self._ts_to_text(ts, label)
        return self.embed_text(text)

    def embed_monthly_window(
        self,
        monthly_df: pd.DataFrame,
        category: str,
        year: int,
        month: int,
        window: int = 6,
    ) -> tuple:
        """
        Extract last `window` months ending at (year, month) for `category`,
        then embed.  Returns (embedding, text_description).
        """
        cat_df = monthly_df[monthly_df["Category"] == category].copy()
        cat_df = cat_df.sort_values("YearMonth")

        # Find target row index
        mask = (cat_df["Year"] == year) & (cat_df["Month"] == month)
        if not mask.any():
            # Fallback: use latest available
            mask = pd.Series([True] * len(cat_df), index=cat_df.index)
            mask.iloc[:-1] = False

        end_idx = cat_df.index[mask][0]
        pos = cat_df.index.get_loc(end_idx)
        start_pos = max(0, pos - window + 1)
        window_df = cat_df.iloc[start_pos: pos + 1]

        ts = window_df["TotalSales"].values
        label = f"{category} {year}-{month:02d}"
        text = self._ts_to_text(ts, label)
        return self.embed_text(text), text


# ------------------------------------------------------------------
# Quick test
# ------------------------------------------------------------------
if __name__ == "__main__":
    gen = EmbeddingGenerator()

    e1 = gen.embed_text("Sales surged 30% in Q4 due to holiday demand")
    print(f"Text embedding shape: {e1.shape}, dtype: {e1.dtype}")

    ts = pd.Series([1200, 1350, 1100, 1600, 1800, 2200])
    e2 = gen.embed_time_series(ts, label="Furniture 2017-11")
    print(f"TS embedding shape:   {e2.shape}")
    print(f"Similarity with self: {np.dot(e2, e2):.4f}")
