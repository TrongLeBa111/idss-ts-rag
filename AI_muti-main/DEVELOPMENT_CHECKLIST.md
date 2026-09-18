# ✅ DEVELOPMENT ROADMAP & CHECKLIST

## Phase 1: Setup & Data Preparation (Week 1-2)

### Week 1: Environment Setup
- [ ] Clone/Create project repository
- [ ] Create Python virtual environment
- [ ] Install all dependencies (`pip install -r requirements.txt`)
- [ ] Verify installations (run `python -c "import pandas; print(pandas.__version__)"`)
- [ ] Copy `.env.example` to `.env`
- [ ] Add OpenAI API key to `.env`
- [ ] Create `.gitignore` with `.env` and `__pycache__`
- [ ] Initialize Git repo and make first commit

**Deliverables:**
```
✅ venv activated
✅ pip freeze shows all packages
✅ .env file created (not in git)
✅ Git repo initialized
```

---

### Week 2: Data Loading & EDA
- [ ] Download dataset from Kaggle (Superstore Sales)
- [ ] Save to `data/raw/superstore_sales.csv`
- [ ] Create `notebooks/01_eda_and_preprocessing.ipynb`
- [ ] Jupyter: Load data and explore shape/columns
- [ ] Jupyter: Check data types and missing values
- [ ] Jupyter: Create visualizations (sales over time, category distribution)
- [ ] Jupyter: Identify date columns and convert to datetime
- [ ] Analyze what features might be useful

**Deliverables:**
```
✅ data/raw/superstore_sales.csv (9425 rows × 21 columns)
✅ EDA notebook with insights
✅ Summary statistics generated
```

**Expected Data Structure:**
```
Order ID | Order Date | Ship Date | Ship Mode | Customer ID | Segment | Country | City | State | Postal Code | Region | Product ID | Category | Sub-Category | Product Name | Sales | Quantity | Discount | Profit | Year Of The Order
```

---

## Phase 2: Data Pipeline & Features (Week 2-3)

### Data Preprocessing
- [ ] Create `src/data_pipeline/loader.py`
  - [ ] Function: `load_csv(path)` returns DataFrame
  - [ ] Function: `validate_data(df)` checks shape/columns

```python
# Example test
from src.data_pipeline.loader import load_csv
df = load_csv('data/raw/superstore_sales.csv')
assert len(df) > 0, "Data not loaded"
assert 'Sales' in df.columns, "Missing Sales column"
print("✅ Data loaded successfully")
```

- [ ] Create `src/data_pipeline/preprocessor.py`
  - [ ] Convert dates: `Order Date` → datetime
  - [ ] Remove duplicates
  - [ ] Handle missing values (forward fill for time series)
  - [ ] Create features: Year, Month, Quarter, DayOfWeek
  - [ ] Normalize/Scale numeric columns (optional)

```python
# Test preprocessing
from src.data_pipeline.preprocessor import DataPreprocessor
proc = DataPreprocessor('data/raw/superstore_sales.csv')
df_clean = proc.run()
assert df_clean.isnull().sum().sum() == 0, "Still has NaN values"
assert 'Month' in df_clean.columns, "Month feature not created"
print("✅ Data preprocessed")
df_clean.to_csv('data/processed/superstore_sales_cleaned.csv')
```

**Deliverables:**
```
✅ data/processed/superstore_sales_cleaned.csv (cleaned data)
✅ Unit tests for loader & preprocessor
```

---

### Feature Engineering (TSFresh)
- [ ] Create `src/data_pipeline/feature_extractor.py`
- [ ] Use TSFresh library to extract time-series features
- [ ] Features to extract:
  - Mean, std, min, max (basic stats)
  - Autocorrelation, trend detection
  - Seasonality features (if data length allows)

```python
# Example
from tsfresh import extract_features
from src.data_pipeline.feature_extractor import extract_time_series_features

ts_data = df_clean['Sales'].values
features_df = extract_time_series_features(ts_data)
features_df.to_pickle('data/processed/timeseries_features.pkl')
print(f"✅ Extracted {features_df.shape[1]} features")
```

- [ ] Create `src/data_pipeline/event_simulator.py`
- [ ] Generate sample events (JSON format):
  ```json
  [
    {
      "date": "2017-11-01",
      "event_type": "seasonal",
      "description": "Black Friday season starts"
    },
    {
      "date": "2017-12-25",
      "event_type": "holiday",
      "description": "Christmas - high demand"
    }
  ]
  ```

**Deliverables:**
```
✅ data/processed/timeseries_features.pkl
✅ data/processed/events_context.json
✅ Feature extraction notebook
```

---

## Phase 3: TS-RAG Engine (Week 4-5)

### Vector Embeddings
- [ ] Create `src/ts_rag_engine/embeddings.py`
- [ ] Choose embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- [ ] Implement:
  - [ ] `EmbeddingGenerator` class
  - [ ] `embed_text(text: str)` → numpy array (384 dimensions)
  - [ ] `embed_time_series(ts_data)` → embed numeric data as text

```python
# Test embeddings
from src.ts_rag_engine.embeddings import EmbeddingGenerator

gen = EmbeddingGenerator()

# Test 1: Embed text
emb1 = gen.embed_text("Sales increased by 20% last month")
assert emb1.shape == (384,), f"Expected shape (384,), got {emb1.shape}"

# Test 2: Embed time series
import pandas as pd
ts = pd.Series([100, 110, 120, 115, 125])
emb2 = gen.embed_time_series(ts)
assert emb2.shape == (384,)

print("✅ Embeddings working")
```

**Deliverables:**
```
✅ Working embedding generator
✅ Test cases pass
```

---

### Vector Database (FAISS)
- [ ] Create `src/ts_rag_engine/vector_store.py`
- [ ] Implement `FAISSVectorStore` class:
  - [ ] `__init__(dimension=384)` - Initialize FAISS index
  - [ ] `add_embedding(embedding, metadata)` - Add vector + metadata
  - [ ] `search(query_embedding, k=3)` - Find k nearest neighbors
  - [ ] `save(path)` - Persist to disk
  - [ ] `load(path)` - Load from disk

```python
# Test vector store
from src.ts_rag_engine.vector_store import FAISSVectorStore
import numpy as np

vs = FAISSVectorStore(dimension=384)

# Add sample embeddings
for i in range(10):
    emb = np.random.rand(384).astype('float32')
    vs.add_embedding(emb, {"date": f"2017-01-{i+1:02d}", "sales": 1000 + i*100})

# Search
query = np.random.rand(384).astype('float32')
results = vs.search(query, k=3)
assert len(results) == 3, "Should return 3 results"

# Save & Load
vs.save('data/vector_db')
vs_loaded = FAISSVectorStore()
vs_loaded.load('data/vector_db')
assert vs_loaded.index.ntotal == 10, "Should load 10 embeddings"

print("✅ Vector store working")
```

**Deliverables:**
```
✅ data/vector_db/index.faiss (FAISS index)
✅ data/vector_db/metadata.pkl (Metadata)
✅ Vector store tests pass
```

---

### Retriever
- [ ] Create `src/ts_rag_engine/retriever.py`
- [ ] Implement `TimeSeriesRetriever` class:
  - [ ] Load preprocessed features
  - [ ] Load FAISS index
  - [ ] `retrieve(query_features, top_k=3)` - Find similar historical patterns

```python
# Test retriever
from src.ts_rag_engine.retriever import TimeSeriesRetriever

retriever = TimeSeriesRetriever('data/vector_db')

# Simulate a query: current month's sales pattern
query_pattern = np.random.rand(384).astype('float32')
similar_dates = retriever.retrieve(query_pattern, top_k=3)

for date, score in similar_dates:
    print(f"Date: {date}, Similarity: {score:.2f}")

print("✅ Retriever working")
```

**Deliverables:**
```
✅ Retriever returns top-k similar patterns
```

---

### Context Augmentor
- [ ] Create `src/ts_rag_engine/context_augmentor.py`
- [ ] Load events data (JSON)
- [ ] Implement `ContextAugmentor` class:
  - [ ] `augment(retrieved_patterns, current_date)` - Combine patterns + events

```python
# Test context augmentor
from src.ts_rag_engine.context_augmentor import ContextAugmentor

augmentor = ContextAugmentor('data/processed/events_context.json')

retrieved = [
    {"date": "2016-11-01", "sales": 2500},
    {"date": "2015-11-01", "sales": 2400}
]

context = augmentor.augment(retrieved, "2017-11-01")
print(context)
# Output: "Similar patterns: 2016-11-01 (2500), 2015-11-01 (2400). Events: Black Friday happening."

print("✅ Context augmentor working")
```

**Deliverables:**
```
✅ Context enrichment working
```

---

### LLM Reasoner
- [ ] Create `src/ts_rag_engine/llm_reasoner.py`
- [ ] Implement `LLMReasoner` class:
  - [ ] `reason(context)` - Take rich context, call LLM (GPT-4)
  - [ ] Output: Natural language analysis + recommendations

```python
# Test LLM reasoner
from src.ts_rag_engine.llm_reasoner import LLMReasoner

reasoner = LLMReasoner()

context = """
Current month: November 2017
Similar patterns found:
- November 2016: $2,500 sales
- November 2015: $2,400 sales

External events:
- Black Friday sale starting
- New product launch
"""

analysis = reasoner.reason(context)
print(analysis)
# Output: "Based on historical patterns and current events, we forecast..."

print("✅ LLM reasoner working")
```

**⚠️ IMPORTANT:** Ensure OPENAI_API_KEY is set in `.env`

**Deliverables:**
```
✅ LLM can generate explanations
✅ Analysis notebook with examples
```

---

## Phase 4: Agents & Orchestration (Week 5-6)

### Supervisor Agent
- [ ] Create `src/agents/supervisor_agent.py`
- [ ] Use LangChain Agent
- [ ] Define tools: `forecast`, `anomaly_detect`, `explain`
- [ ] Supervisor decides which tool to call based on user query

```python
from langchain.agents import AgentType, initialize_agent
from src.agents.supervisor_agent import SupervisorAgent

supervisor = SupervisorAgent()

# Test 1: Forecast query
response = supervisor.run("What will sales be next month?")
# Should call: forecast tool

# Test 2: Anomaly query
response = supervisor.run("Are there any unusual patterns in the data?")
# Should call: anomaly_detect tool

print("✅ Supervisor agent working")
```

**Deliverables:**
```
✅ Supervisor agent making tool decisions
✅ Tool calling working
```

---

### Specialized Agents
- [ ] Create `src/agents/forecast_agent.py`
- [ ] Create `src/agents/anomaly_agent.py`
- [ ] Each agent handles specific domain

**Deliverables:**
```
✅ Forecast agent outputting predictions
✅ Anomaly agent detecting outliers
```

---

## Phase 5: Integration & Platform (Week 6-7)

### Slack Bot
- [ ] Create Slack app at https://api.slack.com/apps
  - [ ] Generate Bot Token
  - [ ] Set signing secret
  - [ ] Add scopes: `chat:write`, `commands`

- [ ] Create `src/integrations/slack_bot.py`
- [ ] Implement:
  - [ ] Event handling: `@app.message()`
  - [ ] Command handling: `@app.command("/forecast")`
  - [ ] Call supervisor agent for each interaction

```python
# Test Slack bot locally
from slack_bolt import App

app = App(
    token="xoxb-...",
    signing_secret="..."
)

@app.message("hello")
def handle_hello(message, say):
    say(f"Hi <@{message['user']}>!")

# Run locally for testing
if __name__ == "__main__":
    app.start(port=3000)
```

**Testing:**
- [ ] Use ngrok to expose local bot: `ngrok http 3000`
- [ ] Update Slack Webhook URL
- [ ] Test bot on Slack workspace

**Deliverables:**
```
✅ Slack bot responding to messages
✅ /forecast command working
✅ Demo video recorded
```

---

### Streamlit Dashboard
- [ ] Create `web_dashboard/app.py`
- [ ] Create pages:
  - [ ] `pages/forecast_analysis.py` - Sales forecast chart
  - [ ] `pages/anomaly_detection.py` - Anomaly visualization
  - [ ] `pages/explain.py` - AI explanation

```python
# test streamlit app
streamlit run web_dashboard/app.py
# Visit: http://localhost:8501
```

**Deliverables:**
```
✅ Dashboard showing metrics
✅ Forecast chart interactive
✅ Anomaly points highlighted
```

---

## Phase 6: Compliance & Testing (Week 7-8)

### Activity Logging
- [ ] Create `src/compliance/activity_logger.py`
- [ ] Log all AI decisions:
  ```python
  {
    "timestamp": "2024-01-15T10:30:00Z",
    "user_id": "U123456",
    "action": "forecast_request",
    "input": "What's next month sales?",
    "output": "Predicted: 2500 VNĐ",
    "confidence": 0.85,
    "explanation": "Based on seasonal pattern..."
  }
  ```

- [ ] Create `src/compliance/risk_assessor.py`
- [ ] Generate risk assessment report per Luật AI 2025

**Deliverables:**
```
✅ Activity logs being generated
✅ Risk assessment document
✅ Compliance checklist complete
```

---

### Unit Tests
- [ ] Create `tests/test_data_pipeline.py`
  - [ ] Test data loader
  - [ ] Test preprocessor
  - [ ] Test feature extractor

- [ ] Create `tests/test_ts_rag_engine.py`
  - [ ] Test embeddings
  - [ ] Test vector store
  - [ ] Test retriever
  - [ ] Test LLM reasoner

- [ ] Create `tests/test_agents.py`
  - [ ] Test supervisor agent
  - [ ] Test tool calling

**Run tests:**
```bash
pytest -v --cov=src tests/
# Target: > 80% coverage
```

**Deliverables:**
```
✅ tests/ directory with 10+ test files
✅ Code coverage > 80%
✅ All tests passing (green checkmarks)
```

---

### Documentation
- [ ] Update `README.md` with final status
- [ ] Create `docs/ARCHITECTURE.md` - System design details
- [ ] Create `docs/API_SPECIFICATION.md` - API endpoints
- [ ] Create `docs/DEPLOYMENT_GUIDE.md` - Production checklist

**Deliverables:**
```
✅ Comprehensive documentation
✅ Architecture diagrams (ASCII or images)
✅ Deployment instructions
```

---

## Phase 7: Packaging & Portfolio (Week 8)

### Code Quality
- [ ] Clean up all code (remove debug prints)
- [ ] Format code with `black`:
  ```bash
  black src/ tests/
  ```

- [ ] Run linter:
  ```bash
  flake8 src/ --max-line-length=100
  ```

- [ ] Type hints on all functions:
  ```python
  def load_csv(path: str) -> pd.DataFrame:
      ...
  ```

### Docker Packaging
- [ ] Create `docker/Dockerfile`
- [ ] Create `docker/docker-compose.yml`
- [ ] Build & test:
  ```bash
  docker-compose build
  docker-compose up
  ```

**Deliverables:**
```
✅ docker/Dockerfile
✅ docker/docker-compose.yml
✅ Images build successfully
```

---

### GitHub Presentation
- [ ] Push all code to GitHub
- [ ] Add meaningful commits:
  ```
  git commit -m "feat: add TS-RAG engine with FAISS retrieval"
  git commit -m "feat: integrate Slack bot with supervisor agent"
  git commit -m "docs: add comprehensive README and guides"
  ```

- [ ] Create GitHub README with badges:
  ```markdown
  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
  ![Tests](https://img.shields.io/badge/Tests-85%25%20Pass-green)
  ![License](https://img.shields.io/badge/License-MIT-green)
  ```

- [ ] Prepare portfolio demo:
  - [ ] Record 2-3 min demo video
  - [ ] Create slide deck (5-10 slides)
  - [ ] Write project summary (500 words)

**Deliverables:**
```
✅ GitHub repo with clean commit history
✅ Professional README with badges
✅ Demo video (YouTube or Google Drive)
✅ Slide presentation
✅ Project summary document
```

---

## Final Checklist (Before Submission)

### Code Quality (Must Have)
- [ ] All imports organized (no unused imports)
- [ ] All functions have docstrings
- [ ] No hardcoded values (use config/env)
- [ ] No print() statements (use logger)
- [ ] All tests passing (`pytest -v`)
- [ ] Code coverage > 80%

### Functionality (Must Have)
- [ ] TS-RAG engine working end-to-end
- [ ] Slack bot responding correctly
- [ ] Streamlit dashboard displaying data
- [ ] API endpoints functional (if FastAPI)
- [ ] Logging working properly

### Documentation (Must Have)
- [ ] README.md comprehensive
- [ ] GETTING_STARTED.md clear instructions
- [ ] API documentation (if applicable)
- [ ] Architecture explained
- [ ] Compliance checklist completed

### Compliance (Must Have)
- [ ] Risk assessment done (Luật AI 2025)
- [ ] Activity logging implemented
- [ ] Explainability documented
- [ ] Privacy measures in place

### Portfolio (Nice to Have)
- [ ] GitHub stars/follow buttons on repo
- [ ] Demo video uploaded
- [ ] LinkedIn post prepared
- [ ] Interview talking points ready

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| TS-RAG Accuracy | > 80% | 🔲 |
| Forecast RMSE | < ±15% | 🔲 |
| Bot Response Time | < 3s | 🔲 |
| Code Coverage | > 80% | 🔲 |
| Tests Pass Rate | 100% | 🔲 |
| Documentation | 100% | 🔲 |

---

## Timeline Summary

```
Week 1-2: Setup & Data (✅ Foundation)
Week 2-3: Features (✅ Data Ready)
Week 4-5: TS-RAG Engine (✅ AI Core)
Week 5-6: Agents & Integrations (✅ Orchestration)
Week 6-7: Bot & Dashboard (✅ User Interface)
Week 7-8: Testing & Compliance (✅ Production Ready)
Week 8: Portfolio & Polish (✅ Ready to Show)

TOTAL: 8 Weeks = 2 Months (Perfect for semester project!)
```

---

**Good luck! You've got this! 🚀**

Questions? Check:
- [GETTING_STARTED.md](GETTING_STARTED.md) - Step-by-step guide
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - File explanations
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues
