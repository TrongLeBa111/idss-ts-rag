"""
tests/test_ts_rag_engine.py
Unit tests for Phase 2 deliverables:
  - EmbeddingGenerator
  - FAISSVectorStore
  - TimeSeriesRetriever
  - ContextAugmentor
  - LLMReasoner / RuleBasedReasoner
"""
import sys
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ======================================================================
# Fixtures
# ======================================================================
@pytest.fixture(scope="session")
def monthly_df():
    """Build a small monthly series for TS-RAG tests."""
    from src.data_pipeline.create_sample_data import generate_dataset
    from src.data_pipeline.preprocessor import DataPreprocessor
    import tempfile, os

    raw = generate_dataset(800)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        raw.to_csv(f.name, index=False)
        tmp_path = f.name

    proc = DataPreprocessor(tmp_path)
    _, monthly = proc.run()
    os.unlink(tmp_path)
    return monthly


@pytest.fixture(scope="session")
def embedder():
    from src.ts_rag_engine.embeddings import EmbeddingGenerator
    return EmbeddingGenerator()


@pytest.fixture(scope="session")
def vector_store(tmp_path_factory, embedder):
    from src.ts_rag_engine.vector_store import FAISSVectorStore
    vs = FAISSVectorStore(dimension=256)
    for i in range(15):
        emb = np.random.rand(256).astype("float32")
        vs.add_embedding(emb, {"id": i, "category": "Furniture", "yearmonth": f"2017-{(i%12)+1:02d}"})
    return vs


@pytest.fixture(scope="session")
def built_retriever(tmp_path_factory, monthly_df):
    from src.ts_rag_engine.retriever import TimeSeriesRetriever
    db_path = str(tmp_path_factory.mktemp("vector_db"))
    r = TimeSeriesRetriever(db_path)
    r.build_index(monthly_df, window=6, save=True)
    return r, monthly_df


@pytest.fixture(scope="session")
def events_json(tmp_path_factory):
    from src.data_pipeline.event_simulator import create_events_json
    p = str(tmp_path_factory.mktemp("events") / "events.json")
    create_events_json(p)
    return p


# ======================================================================
# 1. EmbeddingGenerator
# ======================================================================
class TestEmbeddingGenerator:
    def test_embed_text_shape(self, embedder):
        emb = embedder.embed_text("Sales surged 30% in Q4")
        assert emb.shape == (256,), f"Expected (256,), got {emb.shape}"

    def test_embed_text_dtype(self, embedder):
        emb = embedder.embed_text("Holiday demand is high")
        assert emb.dtype == np.float32

    def test_embed_text_nonzero(self, embedder):
        emb = embedder.embed_text("Black Friday sales spike")
        assert np.linalg.norm(emb) > 0, "Embedding should not be all zeros"

    def test_embed_texts_batch(self, embedder):
        texts = ["Sales up 20%", "Inventory low", "Demand stable"]
        batch = embedder.embed_texts(texts)
        assert batch.shape == (3, 256)

    def test_embed_time_series_shape(self, embedder):
        ts = pd.Series([100, 120, 115, 140, 160, 180])
        emb = embedder.embed_time_series(ts, label="Furniture 2017-11")
        assert emb.shape == (256,)

    def test_embed_time_series_dtype(self, embedder):
        ts = np.array([200, 250, 230, 270, 300])
        emb = embedder.embed_time_series(ts)
        assert emb.dtype == np.float32

    def test_different_texts_different_embeddings(self, embedder):
        e1 = embedder.embed_text("strongly increasing trend high volatility")
        e2 = embedder.embed_text("strongly decreasing trend low volatility")
        # Should not be identical
        assert not np.allclose(e1, e2), "Different text should produce different embeddings"

    def test_embed_monthly_window_returns_tuple(self, embedder, monthly_df):
        result = embedder.embed_monthly_window(monthly_df, "Furniture", 2017, 11, window=6)
        assert isinstance(result, tuple)
        assert len(result) == 2
        emb, text = result
        assert emb.shape == (256,)
        assert isinstance(text, str)
        assert len(text) > 10

    def test_ts_description_contains_trend(self, embedder):
        ts = pd.Series([100, 200, 300, 400, 500, 600])  # strongly increasing
        text = embedder._ts_to_text(ts, "test")
        assert "increasing" in text.lower()

    def test_empty_ts_handled(self, embedder):
        emb = embedder.embed_time_series(pd.Series([], dtype=float))
        assert emb.shape == (256,)  # should not crash


# ======================================================================
# 2. FAISSVectorStore
# ======================================================================
class TestFAISSVectorStore:
    def test_add_and_count(self, vector_store):
        assert vector_store.total_vectors == 15

    def test_search_returns_k_results(self, vector_store):
        query = np.random.rand(256).astype("float32")
        results = vector_store.search(query, k=3)
        assert len(results) == 3

    def test_search_result_structure(self, vector_store):
        query = np.random.rand(256).astype("float32")
        results = vector_store.search(query, k=1)
        meta, dist = results[0]
        assert "id" in meta
        assert "category" in meta
        assert isinstance(dist, float)
        assert dist >= 0

    def test_similarity_score_range(self, vector_store):
        query = np.random.rand(256).astype("float32")
        results = vector_store.search(query, k=3)
        for _, dist in results:
            sim = vector_store.similarity_score(dist)
            assert 0 < sim <= 1.0

    def test_exact_match_high_similarity(self, vector_store):
        """Adding a vector then querying it should return highest similarity."""
        from src.ts_rag_engine.vector_store import FAISSVectorStore
        vs = FAISSVectorStore(256)
        vec = np.ones(256, dtype="float32")
        vs.add_embedding(vec, {"label": "exact"})
        results = vs.search(vec, k=1)
        meta, dist = results[0]
        assert dist < 0.01, f"Exact match distance should be ~0, got {dist}"

    def test_save_and_load(self, vector_store, tmp_path):
        from src.ts_rag_engine.vector_store import FAISSVectorStore
        save_path = str(tmp_path / "faiss_test")
        vector_store.save(save_path)
        vs2 = FAISSVectorStore(256)
        vs2.load(save_path)
        assert vs2.total_vectors == vector_store.total_vectors

    def test_save_creates_files(self, vector_store, tmp_path):
        save_path = str(tmp_path / "faiss_check")
        vector_store.save(save_path)
        assert (Path(save_path) / "index.faiss").exists()
        assert (Path(save_path) / "metadata.pkl").exists()

    def test_search_empty_store(self):
        from src.ts_rag_engine.vector_store import FAISSVectorStore
        vs = FAISSVectorStore(256)
        result = vs.search(np.zeros(256, dtype="float32"), k=3)
        assert result == []


# ======================================================================
# 3. TimeSeriesRetriever
# ======================================================================
class TestTimeSeriesRetriever:
    def test_index_built(self, built_retriever):
        retriever, _ = built_retriever
        assert retriever.vs.total_vectors > 0

    def test_retrieve_returns_list(self, built_retriever):
        retriever, monthly = built_retriever
        results = retriever.retrieve(monthly, "Furniture", 2017, 11, top_k=3)
        assert isinstance(results, list)

    def test_retrieve_top_k(self, built_retriever):
        retriever, monthly = built_retriever
        results = retriever.retrieve(monthly, "Furniture", 2017, 11, top_k=3)
        assert len(results) <= 3

    def test_retrieve_result_structure(self, built_retriever):
        retriever, monthly = built_retriever
        results = retriever.retrieve(monthly, "Technology", 2017, 6, top_k=2)
        for r in results:
            assert "yearmonth" in r
            assert "avg_sales" in r
            assert "similarity" in r
            assert "sales_trend_pct" in r
            assert 0 <= r["similarity"] <= 1.0

    def test_retrieve_excludes_same_period(self, built_retriever):
        retriever, monthly = built_retriever
        results = retriever.retrieve(monthly, "Furniture", 2017, 11, top_k=5,
                                     exclude_same_period=True)
        for r in results:
            assert not (r["year"] == 2017 and r["month"] == 11)

    def test_retrieve_all_categories(self, built_retriever):
        retriever, monthly = built_retriever
        for cat in ["Furniture", "Technology", "Office Supplies"]:
            results = retriever.retrieve(monthly, cat, 2016, 6, top_k=2)
            assert isinstance(results, list)


# ======================================================================
# 4. ContextAugmentor
# ======================================================================
class TestContextAugmentor:
    def test_augment_returns_string(self, events_json, monthly_df):
        from src.ts_rag_engine.context_augmentor import ContextAugmentor
        aug = ContextAugmentor(events_json)
        ctx = aug.augment([], "Furniture", 2017, 11)
        assert isinstance(ctx, str)
        assert len(ctx) > 50

    def test_augment_contains_category(self, events_json):
        from src.ts_rag_engine.context_augmentor import ContextAugmentor
        aug = ContextAugmentor(events_json)
        ctx = aug.augment([], "Technology", 2017, 12)
        assert "TECHNOLOGY" in ctx.upper()

    def test_augment_contains_patterns(self, events_json):
        from src.ts_rag_engine.context_augmentor import ContextAugmentor
        aug = ContextAugmentor(events_json)
        patterns = [
            {"yearmonth": "2016-11", "avg_sales": 2800.0, "peak_sales": 4200.0,
             "sales_trend_pct": 22.5, "similarity": 0.91},
        ]
        ctx = aug.augment(patterns, "Furniture", 2017, 11)
        assert "2016-11" in ctx
        assert "2,800" in ctx

    def test_augment_with_current_stats(self, events_json):
        from src.ts_rag_engine.context_augmentor import ContextAugmentor
        aug = ContextAugmentor(events_json)
        ctx = aug.augment([], "Furniture", 2017, 11,
                          current_sales_stats={"total_sales": 5000, "avg_monthly": 4000,
                                               "mom_change_pct": 12.5, "order_count": 80})
        assert "5,000" in ctx
        assert "12.5%" in ctx

    def test_get_relevant_events_november(self, events_json):
        from src.ts_rag_engine.context_augmentor import ContextAugmentor
        aug = ContextAugmentor(events_json)
        events = aug.get_relevant_events(2017, 11, window_days=30)
        assert len(events) > 0

    def test_augment_missing_events_file(self, tmp_path):
        from src.ts_rag_engine.context_augmentor import ContextAugmentor
        aug = ContextAugmentor(str(tmp_path / "no_events.json"))
        ctx = aug.augment([], "Furniture", 2017, 11)
        assert "No significant events" in ctx


# ======================================================================
# 5. LLMReasoner / RuleBasedReasoner
# ======================================================================
SAMPLE_CONTEXT = """
=== CONTEXT FOR: FURNITURE — November 2017 ===

## Current Period Stats
- Total Sales: $31,200
- Average Monthly Sales: $2,600
- Month-over-Month Change: +18.4%
- Order Count: 142

## Similar Historical Patterns Found
1. 2016-11 | Avg Sales: $2,800 | Peak: $4,200 | 6-month trend: ↑22.5% | Similarity: 91.0%
2. 2015-11 | Avg Sales: $2,550 | Peak: $3,800 | 6-month trend: ↑15.3% | Similarity: 87.0%

## Relevant Business Events (±45 days)
- 🔴 [SEASONAL] 2017-11-24: Black Friday — highest revenue day projected (impact: high)
- 🔴 [HOLIDAY] 2017-12-25: Christmas — technology & furniture peak demand (impact: high)

## Pattern Summary
- Historical avg sales (similar periods): $2,675
- Average 6-month trend in similar periods: +18.9%
- Number of comparable historical periods found: 2
"""


class TestLLMReasoner:
    def test_reason_returns_dict(self):
        from src.ts_rag_engine.llm_reasoner import LLMReasoner
        r = LLMReasoner()
        result = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        assert isinstance(result, dict)

    def test_reason_required_keys(self):
        from src.ts_rag_engine.llm_reasoner import LLMReasoner
        r = LLMReasoner()
        result = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        for key in ["period", "forecast_sales", "confidence", "forecast_range",
                    "key_drivers", "risks", "recommendation", "stock_adjustment"]:
            assert key in result, f"Missing key: {key}"

    def test_forecast_positive(self):
        from src.ts_rag_engine.llm_reasoner import LLMReasoner
        r = LLMReasoner()
        result = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        assert result["forecast_sales"] > 0

    def test_confidence_range(self):
        from src.ts_rag_engine.llm_reasoner import LLMReasoner
        r = LLMReasoner()
        result = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        assert 0.4 <= result["confidence"] <= 0.95

    def test_forecast_range_ordered(self):
        from src.ts_rag_engine.llm_reasoner import LLMReasoner
        r = LLMReasoner()
        result = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        assert result["forecast_range"]["low"] < result["forecast_range"]["high"]

    def test_holiday_boosts_confidence(self):
        from src.ts_rag_engine.llm_reasoner import LLMReasoner
        r = LLMReasoner()
        result_with = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        no_event_ctx = SAMPLE_CONTEXT.replace("Black Friday", "").replace("Christmas", "")
        result_without = r.reason(no_event_ctx, "Furniture", 2017, 11)
        assert result_with["confidence"] >= result_without["confidence"]

    def test_format_report_is_string(self):
        from src.ts_rag_engine.llm_reasoner import LLMReasoner
        r = LLMReasoner()
        result = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        report = r.format_report(result)
        assert isinstance(report, str)
        assert "REPORT" in report.upper()
        assert "RECOMMENDATION" in report.upper()

    def test_summer_month_lower_forecast(self):
        from src.ts_rag_engine.llm_reasoner import RuleBasedReasoner
        r = RuleBasedReasoner()
        summer = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 7)
        winter = r.reason(SAMPLE_CONTEXT, "Furniture", 2017, 11)
        assert winter["forecast_sales"] > summer["forecast_sales"]


# ======================================================================
# Run
# ======================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
