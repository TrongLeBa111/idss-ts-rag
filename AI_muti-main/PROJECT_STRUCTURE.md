# 🏗️ PROJECT STRUCTURE GUIDE - Hiểu Rõ Từng Tệp Và Vai Trò

## 📁 Cấu Trúc Thư Mục Chi Tiết

```
intelligent-decision-support-system/
│
├── 📄 README.md                          ← TÔI ĐẠO NẠI (dành cho GitHub)
├── 📄 GETTING_STARTED.md                 ← Hướng dẫn bắt đầu
├── 📄 requirements.txt                   ← Python dependencies
├── 📄 .env.example                       ← Mẫu biến môi trường
├── 📄 .gitignore                         ← Git ignore rules
├── 📄 LICENSE                            ← MIT License
│
├── 📁 data/
│   ├── 📁 raw/
│   │   ├── superstore_sales.csv          ← Dataset gốc (từ Kaggle)
│   │   └── events_sample.json            ← Sự kiện mẫu
│   ├── 📁 processed/
│   │   ├── superstore_sales_cleaned.csv  ← Data sau xử lý
│   │   ├── timeseries_features.pkl       ← Features đã trích xuất (TSFresh)
│   │   └── events_context.json           ← Sự kiện ngữ cảnh
│   └── 📁 vector_db/
│       ├── index.faiss                   ← FAISS vector index
│       └── metadata.pkl                  ← Metadata embeddings
│
├── 📁 src/
│   ├── __init__.py
│   │
│   ├── 📁 data_pipeline/                 ← Xử lý & chuẩn bị dữ liệu
│   │   ├── __init__.py
│   │   ├── loader.py                     ← Load data từ CSV
│   │   │   • Function: load_csv()
│   │   │   • Mục đích: Đọc raw data
│   │   │
│   │   ├── preprocessor.py               ← Tiền xử lý dữ liệu
│   │   │   • Class: DataPreprocessor
│   │   │   • Methods: clean_data(), handle_missing(), create_time_features()
│   │   │   • Mục đích: Xử lý NaN, tạo datetime features
│   │   │
│   │   ├── feature_extractor.py          ← Trích xuất đặc trưng thời gian
│   │   │   • Library: TSFresh
│   │   │   • Methods: extract_time_series_features()
│   │   │   • Mục đích: Tạo 100+ features từ sliding windows
│   │   │
│   │   └── event_simulator.py            ← Tạo dữ liệu sự kiện giả lập
│   │       • Methods: generate_random_events()
│   │       • Mục đích: Giả lập "Black Friday", "Tết", etc.
│   │
│   ├── 📁 ts_rag_engine/                 ← Trái tim: Time-Series RAG
│   │   ├── __init__.py
│   │   ├── embeddings.py                 ← Chuyển dữ liệu → Vector
│   │   │   • Class: EmbeddingGenerator
│   │   │   • Models: all-MiniLM-L6-v2 hoặc OpenAI Embeddings
│   │   │   • Output: 384-dimensional vectors
│   │   │
│   │   ├── vector_store.py               ← Quản lý FAISS database
│   │   │   • Class: FAISSVectorStore
│   │   │   • Methods: add_embedding(), search(), save(), load()
│   │   │   • Mục đích: Lưu & truy xuất embeddings nhanh
│   │   │
│   │   ├── retriever.py                  ← Truy xuất mẫu tương tự
│   │   │   • Class: TimeSeriesRetriever
│   │   │   • Methods: retrieve_similar_patterns()
│   │   │   • Output: Top-k similar historical patterns
│   │   │   • Ví dụ: "Tháng 10 năm ngoái giống tháng 10 năm nay"
│   │   │
│   │   ├── context_augmentor.py          ← Làm giàu ngữ cảnh
│   │   │   • Class: ContextAugmentor
│   │   │   • Methods: augment_with_events(), add_market_intel()
│   │   │   • Input: Similar patterns + external events
│   │   │   • Output: Rich context string
│   │   │   • Ví dụ: "Pattern + Black Friday happening"
│   │   │
│   │   └── llm_reasoner.py               ← LLM Suy luận & Giải thích
│   │       • Class: LLMReasoner
│   │       • Methods: reason(), explain_decision()
│   │       • Model: GPT-4 / LLaMA
│   │       • Output: Natural language analysis + recommendations
│   │       • Ví dụ: "Doanh số dự báo ↑15% vì: (1) pattern tương tự, (2) event"
│   │
│   ├── 📁 agents/                        ← AI Agents (Agentic AI)
│   │   ├── __init__.py
│   │   ├── supervisor_agent.py           ← Supervisor điều phối
│   │   │   • Role: Nhận intent từ user, gọi công cụ đúng
│   │   │   • Tool calling: ["forecast", "anomaly_detection", "explain"]
│   │   │   • Framework: LangChain Agent
│   │   │
│   │   ├── forecast_agent.py             ← Agent dự báo
│   │   │   • Input: "Doanh số tháng tới?"
│   │   │   • Process: Gọi TS-RAG engine
│   │   │   • Output: "Doanh số dự báo: 2.5B VNĐ"
│   │   │
│   │   └── anomaly_agent.py              ← Agent phát hiện dị thường
│   │       • Input: "Có gì lạ trong dữ liệu không?"
│   │       • Process: Isolation Forest, Z-score
│   │       • Output: "Phát hiện 3 điểm bất thường"
│   │
│   ├── 📁 integrations/                  ← Tích hợp nền tảng bên ngoài
│   │   ├── __init__.py
│   │   ├── slack_bot.py                  ← Slack Bot
│   │   │   • Framework: Slack Bolt
│   │   │   • Events: message, command, action
│   │   │   • Demo: User types "hi" → Bot responds
│   │   │
│   │   ├── teams_bot.py                  ← Teams Bot (Phase sau)
│   │   │   • Framework: Microsoft Bot Framework
│   │   │   • Status: WIP (Work In Progress)
│   │   │
│   │   └── messaging_gateway.py          ← Unified API cho tất cả platform
│   │       • Purpose: Một interface duy nhất cho Slack/Teams/Web
│   │       • Methods: send_message(), handle_events()
│   │
│   ├── 📁 compliance/                    ← Tuân thủ pháp lý
│   │   ├── __init__.py
│   │   ├── activity_logger.py            ← Ghi nhật ký hoạt động
│   │   │   • Purpose: Log tất cả AI decisions (dùng cho audit)
│   │   │   • Logs: [timestamp, user_id, action, result, confidence]
│   │   │   • Retention: 1 năm (theo Luật AI)
│   │   │
│   │   ├── risk_assessor.py              ← Đánh giá rủi ro theo Luật AI 2025
│   │   │   • Method: assess_system_risk()
│   │   │   • Levels: LOW, MEDIUM, HIGH
│   │   │   • Output: Risk report (tự đánh giá)
│   │   │
│   │   └── explainability.py             ← Giải thích AI decisions
│   │       • Method: explain_decision()
│   │       • Output: "Dự báo này dựa trên: (1) ..., (2) ..., (3) ..."
│   │
│   └── 📁 utils/                         ← Tiện ích & helper functions
│       ├── __init__.py
│       ├── config.py                     ← Load .env, quản lý cấu hình
│       │   • Methods: get_config(), validate_env()
│       │
│       ├── logger.py                     ← Setup logging
│       │   • Methods: get_logger(), log_event()
│       │
│       └── helpers.py                    ← Hàm tiện ích
│           • Functions: parse_date(), calculate_metrics()
│
├── 📁 notebooks/                         ← Jupyter Notebooks (Exploratory)
│   ├── 01_eda_and_preprocessing.ipynb    ← Khám phá & tiền xử lý
│   │   • Cell 1: Load data
│   │   • Cell 2: Explore columns
│   │   • Cell 3: Missing values analysis
│   │   • Cell 4: Visualizations
│   │
│   ├── 02_ts_pattern_discovery.ipynb     ← Khám phá mẫu thời gian
│   │   • Tìm mẫu lặp lại trong lịch sử
│   │   • Vẽ biểu đồ tương tự
│   │
│   └── 03_rag_pipeline_testing.ipynb     ← Test full TS-RAG pipeline
│       • Test embeddings
│       • Test retriever
│       • Test LLM reasoner
│
├── 📁 tests/                             ← Unit Tests
│   ├── __init__.py
│   ├── test_data_pipeline.py             ← Test data loading & preprocessing
│   ├── test_ts_rag_engine.py             ← Test TS-RAG components
│   ├── test_agents.py                    ← Test agents
│   └── test_integrations.py              ← Test Slack/Teams bots
│
│   💡 Chạy: pytest -v (chạy tất cả tests)
│
├── 📁 web_dashboard/                     ← Streamlit Dashboard
│   ├── app.py                            ← Main entry point
│   │   • Page: Home page with metrics
│   │   • Chạy: streamlit run web_dashboard/app.py
│   │
│   ├── 📁 pages/
│   │   ├── forecast_analysis.py          ← Trang dự báo
│   │   │   • Chart: Sales forecast chart
│   │   │   • Table: Detailed breakdown
│   │   │
│   │   ├── anomaly_detection.py          ← Trang phát hiện dị thường
│   │   │   • Scatter plot: Anomaly points
│   │   │
│   │   └── ai_explanation.py             ← Trang giải thích AI
│   │       • Text: Why this recommendation?
│   │
│   └── 📁 config/
│       └── streamlit_config.toml         ← Cấu hình Streamlit
│
├── 📁 docker/                            ← Container & Deployment
│   ├── Dockerfile                        ← Build image cho app
│   │   • Base: python:3.11
│   │   • Install: dependencies
│   │   • Expose: port 8000
│   │
│   └── docker-compose.yml                ← Multi-container orchestration
│       • Service 1: FastAPI (port 8000)
│       • Service 2: Streamlit (port 8501)
│       • Service 3: PostgreSQL (optional)
│
├── 📁 docs/                              ← Documentation
│   ├── ARCHITECTURE.md                   ← Kiến trúc chi tiết
│   ├── API_SPECIFICATION.md              ← API endpoints
│   ├── COMPLIANCE_CHECKLIST.md           ← Tuân thủ Luật AI 2025
│   ├── DEPLOYMENT_GUIDE.md               ← Triển khai production
│   └── TROUBLESHOOTING.md                ← Gỡ lỗi
│
└── 📁 logs/                              ← Log files (created at runtime)
    ├── app.log                           ← Application logs
    ├── errors.log                        ← Error logs
    └── audit.log                         ← Audit trail
```

---

## 🎯 Luồng Dữ Liệu (Data Flow)

```
┌─────────────────┐
│  Raw CSV Data   │
│  superstore.csv │
└────────┬────────┘
         │ (loader.py)
         ▼
┌─────────────────┐
│  Data Frame     │
│  pandas df      │
└────────┬────────┘
         │ (preprocessor.py)
         ▼
┌─────────────────┐
│  Cleaned Data   │
│  + Features     │
└────────┬────────┘
         │ (feature_extractor.py)
         ▼
┌─────────────────┐      ┌──────────────┐
│  Time-Series    │ ───▶ │  Embeddings  │
│  Features       │      │  (384 dims)  │
└─────────────────┘      └────────┬─────┘
                                  │ (vector_store.py)
                                  ▼
                         ┌──────────────┐
                         │  FAISS Index │
                         │  (on disk)   │
                         └──────────────┘
```

---

## 👤 User Interaction Flow (Slack Bot Example)

```
User: "Why is this month's sales high?"
  │
  ▼
Slack API ──▶ slack_bot.py ──▶ supervisor_agent.py
                                     │
                                     ▼
                         ┌─────────────────────────┐
                         │  Supervisor decides:    │
                         │  "Call forecast agent"  │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │  forecast_agent.py      │
                         │  1. Get current month   │
                         │  2. Call TS-RAG engine  │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │ Retriever    │  │ Context      │  │ LLM Reasoner │
            │ (Find similar│  │ Augmentor    │  │ (Generate    │
            │  patterns)   │  │ (Add events) │  │  explanation)│
            └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                   │                 │                 │
                   └─────────────────┴────────────────┬┘
                                                      │
                                    ┌─────────────────▼──────────────┐
                                    │  Response to User:             │
                                    │  "Sales high because:          │
                                    │  1) Similar pattern last year  │
                                    │  2) Black Friday happening"    │
                                    └────────────────────────────────┘
```

---

## 💾 Database Schema

### Table: `user_queries` (SQLite)
```sql
CREATE TABLE user_queries (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    user_id VARCHAR(50),
    platform VARCHAR(20),        -- 'slack', 'teams', 'web'
    query TEXT,
    agent_type VARCHAR(50),       -- 'forecast', 'anomaly', 'explain'
    result TEXT,
    confidence FLOAT,
    execution_time FLOAT         -- ms
);
```

### Table: `ai_decisions` (Audit Trail)
```sql
CREATE TABLE ai_decisions (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    decision_type VARCHAR(50),
    input_data JSONB,
    model_used VARCHAR(50),
    output_recommendation TEXT,
    explanation TEXT,
    confidence FLOAT,
    user_action VARCHAR(50)       -- 'accepted', 'rejected', 'modified'
);
```

---

## 🔑 Key Functions Reference

### 1. Load Data
```python
from src.data_pipeline.loader import load_csv

df = load_csv('data/raw/superstore_sales.csv')
```

### 2. Preprocess
```python
from src.data_pipeline.preprocessor import DataPreprocessor

processor = DataPreprocessor('data/raw/sales.csv')
df_clean = processor.run()
```

### 3. Extract Features
```python
from src.data_pipeline.feature_extractor import extract_time_series_features

features = extract_time_series_features(df['Sales'])
```

### 4. Create Embeddings
```python
from src.ts_rag_engine.embeddings import EmbeddingGenerator

gen = EmbeddingGenerator()
embedding = gen.embed_text("Sales increased 20%")
```

### 5. Retrieve Similar Patterns
```python
from src.ts_rag_engine.vector_store import FAISSVectorStore

vs = FAISSVectorStore()
vs.load('data/vector_db')
similar = vs.search(query_embedding, k=3)
```

### 6. Reason with LLM
```python
from src.ts_rag_engine.llm_reasoner import LLMReasoner

reasoner = LLMReasoner()
analysis = reasoner.reason(context)
```

### 7. Log Activity
```python
from src.compliance.activity_logger import ActivityLogger

logger = ActivityLogger()
logger.log_decision(user_id, decision, confidence)
```

---

## 📊 Metrics & Testing

### Code Coverage Target
- ✅ `data_pipeline/`: 90%+ (critical)
- ✅ `ts_rag_engine/`: 85%+ (core logic)
- ✅ `agents/`: 80%+ (orchestration)
- ✅ `integrations/`: 70%+ (interfaces)

### Performance Targets
- Response time: < 3 seconds
- Forecast accuracy: > 80%
- Bot reliability: > 99.9%

---

## 🚀 Deployment Checklist

- [ ] All tests passing
- [ ] Docker image builds successfully
- [ ] Environment variables configured
- [ ] Logs rotate properly
- [ ] Activity logging functional
- [ ] Risk assessment completed
- [ ] Documentation updated

---

Giờ bạn đã hiểu rõ cấu trúc! Ready to code? 🎉
