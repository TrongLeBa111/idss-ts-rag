# 📖 HƯỚNG DẪN CHI TIẾT PHÁT TRIỂN IDSS - Bước Đầu Tiên

## 🎯 Mục tiêu của tài liệu này
Hướng dẫn bạn từng bước từ lúc setup môi trường cho đến khi chạy được hệ thống TS-RAG đầu tiên.

---

## 📋 PHASE 1: CHUẨN BỊ MÔI TRƯỜNG (1-2 ngày)

### Bước 1.1: Chuẩn bị máy tính

**Kiểm tra yêu cầu tối thiểu:**
```bash
# Kiểm tra phiên bản Python (cần 3.10+)
python --version
# Expected output: Python 3.10.x hoặc cao hơn

# Kiểm tra Git
git --version

# Kiểm tra pip
pip --version
```

**Nếu Python chưa đủ phiên bản:**
- **Windows:** Tải từ python.org
- **Mac:** `brew install python@3.11`
- **Linux:** `sudo apt-get install python3.11`

---

### Bước 1.2: Clone/Setup Project

```bash
# Option A: Nếu bạn đã có repo trên GitHub
git clone https://github.com/yourname/intelligent-decision-support-system.git
cd intelligent-decision-support-system

# Option B: Nếu bắt đầu mới từ đầu
mkdir intelligent-decision-support-system
cd intelligent-decision-support-system
git init

# Tạo folder structure cơ bản
mkdir -p data/{raw,processed,vector_db}
mkdir -p src/{data_pipeline,ts_rag_engine,agents,integrations,compliance,utils}
mkdir -p notebooks tests web_dashboard docker docs logs

# Khởi tạo git
git config user.name "Your Name"
git config user.email "your-email@example.com"
```

---

### Bước 1.3: Tạo Virtual Environment

```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (Mac/Linux)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

**✅ Xác nhận:** Khi thành công, dòng lệnh sẽ bắt đầu với `(venv) $`

---

### Bước 1.4: Cài đặt Dependencies

```bash
# Copy requirements.txt vào thư mục project
# (Bạn đã có file này rồi)

# Cài đặt tất cả package
pip install -r requirements.txt

# Xác nhận cài đặt thành công (nên không có error)
pip list | grep -E "pandas|langchain|faiss"
```

**⏱️ Thời gian:** ~5-10 phút (tuỳ tốc độ internet)

---

### Bước 1.5: Cấu hình File .env

```bash
# Copy .env.example thành .env
cp .env.example .env  # Mac/Linux
# hoặc: copy .env.example .env  (Windows)

# Mở file .env bằng editor yêu thích
# Windows: code .env
# Mac: nano .env
# Linux: vim .env
```

**Những gì cần điền (bắt buộc):**

```env
# 1. OpenAI API Key (để sử dụng GPT-4)
OPENAI_API_KEY=sk-xxxxx  # Lấy từ https://platform.openai.com/api-keys

# 2. Slack Bot Token (để tích hợp Slack sau)
SLACK_BOT_TOKEN=xoxb-xxxxx  # (Tuỳ chọn cho Phase 3, có thể bỏ qua lúc này)

# 3. Các config khác có thể giữ mặc định
```

**⚠️ Lưu ý:** Không commit file `.env` lên GitHub!

```bash
# Thêm vào .gitignore
echo ".env" >> .gitignore
```

---

## 📊 PHASE 2: CHUẨN BỊ DỮ LIỆU (2-3 ngày)

### Bước 2.1: Tải Dataset

**Option A: Tải từ Kaggle (có thể cần tài khoản)**
```bash
# Cài kaggle CLI
pip install kaggle

# Tải dataset Superstore Sales
kaggle datasets download -d rohitsahoo/sales-forecasting-data -p data/raw/

# Unzip file
cd data/raw
unzip sales-forecasting-data.zip
cd ../..

# Xác nhận file tồn tại
ls -la data/raw/
# Nên thấy file: superstore_sales.csv
```

**Option B: Tạo dataset giả lập (nếu không thể tải Kaggle)**
```bash
# Chạy script tạo dữ liệu sample
python src/data_pipeline/create_sample_data.py
# File sẽ được lưu ở: data/raw/superstore_sales.csv
```

---

### Bước 2.2: Khám phá Dữ liệu (EDA)

```bash
# Mở Jupyter Notebook
jupyter lab

# Tạo notebook mới: 01_eda_exploration.ipynb
# Hoặc sử dụng notebook đã chuẩn bị sẵn
```

**Notebook Content (các cell):**

```python
# Cell 1: Load dữ liệu
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data/raw/superstore_sales.csv')

# Cell 2: Khám phá dữ liệu
print(f"Shape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nFirst 5 rows:\n{df.head()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nMissing values:\n{df.isnull().sum()}")

# Cell 3: Thống kê cơ bản
print(df.describe())

# Cell 4: Kiểm tra date format
print(df['Order Date'].min())
print(df['Order Date'].max())

# Cell 5: Vẽ biểu đồ doanh thu theo thời gian
df['Order Date'] = pd.to_datetime(df['Order Date'])
daily_sales = df.groupby('Order Date')['Sales'].sum().sort_index()
plt.figure(figsize=(14, 6))
daily_sales.plot()
plt.title('Daily Sales Over Time')
plt.xlabel('Date')
plt.ylabel('Sales ($)')
plt.show()
```

**✅ Output mong đợi:**
- Dữ liệu có ~9000 rows, ~21 columns
- Cột chính: Order Date, Sales, Quantity, Profit, Category, Region
- Dữ liệu từ năm 2014-2017

---

### Bước 2.3: Tiền Xử Lý Dữ Liệu

Tạo file: `src/data_pipeline/preprocessor.py`

```python
import pandas as pd
import numpy as np
from pathlib import Path

class DataPreprocessor:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
    
    def load_data(self):
        """Load raw data"""
        df = pd.read_csv(self.input_path)
        print(f"✅ Loaded {len(df)} records")
        return df
    
    def clean_data(self, df):
        """Xử lý dữ liệu"""
        # 1. Convert date column
        df['Order Date'] = pd.to_datetime(df['Order Date'])
        df['Ship Date'] = pd.to_datetime(df['Ship Date'])
        
        # 2. Remove duplicates
        initial_rows = len(df)
        df = df.drop_duplicates()
        print(f"✅ Removed {initial_rows - len(df)} duplicates")
        
        # 3. Handle missing values
        df = df.fillna(0)
        
        # 4. Create time-based features
        df['Year'] = df['Order Date'].dt.year
        df['Month'] = df['Order Date'].dt.month
        df['Quarter'] = df['Order Date'].dt.quarter
        df['DayOfWeek'] = df['Order Date'].dt.dayofweek
        
        return df
    
    def run(self):
        df = self.load_data()
        df = self.clean_data(df)
        
        # Save processed data
        df.to_csv(self.output_path, index=False)
        print(f"✅ Saved to {self.output_path}")
        
        return df

if __name__ == "__main__":
    preprocessor = DataPreprocessor(
        input_path='data/raw/superstore_sales.csv',
        output_path='data/processed/superstore_sales_cleaned.csv'
    )
    preprocessor.run()
```

**Chạy script:**
```bash
python src/data_pipeline/preprocessor.py
# Output: data/processed/superstore_sales_cleaned.csv
```

---

### Bước 2.4: Tạo Event Context (Sự kiện Ngữ cảnh)

Tạo file: `src/data_pipeline/create_events.py`

```python
import json
from datetime import datetime, timedelta
import pandas as pd

def create_sample_events():
    """Tạo dữ liệu sự kiện giả lập"""
    
    events = [
        {
            "date": "2017-11-01",
            "event_type": "seasonal",
            "description": "Bắt đầu mùa mua sắm cuối năm"
        },
        {
            "date": "2017-12-25",
            "event_type": "holiday",
            "description": "Giáng sinh - nhu cầu cao"
        },
        {
            "date": "2017-01-01",
            "event_type": "holiday",
            "description": "Tết - nhu cầu cao"
        },
        {
            "date": "2017-04-01",
            "event_type": "competitor_action",
            "description": "Đối thủ chạy khuyến mãi giảm 30%"
        },
        {
            "date": "2017-06-15",
            "event_type": "product_launch",
            "description": "Ra mắt sản phẩm mới - tăng doanh số 15%"
        },
        {
            "date": "2017-08-20",
            "event_type": "supply_chain",
            "description": "Gián đoạn chuỗi cung ứng - tồn kho giảm"
        }
    ]
    
    # Lưu JSON
    with open('data/processed/events_context.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Created {len(events)} events")
    return events

if __name__ == "__main__":
    create_sample_events()
```

**Chạy script:**
```bash
python src/data_pipeline/create_events.py
```

---

## 🧠 PHASE 3: KIẾN THỨC CƠNG NGHỆ TS-RAG (2-3 ngày)

### Bước 3.1: Hiểu TS-RAG là gì

**TS-RAG = Time-Series RAG**

Cấu trúc:
```
Raw Sales Data → Extract Time-Series Features → Embeddings → FAISS Index
                                                    ↓
User Question → Retrieve Similar Patterns → Augment with Events → LLM Reasoner → Response
```

**Ví dụ cụ thể:**

```
User: "Tại sao doanh số tháng 10 cao hơn tháng 9?"

Flow:
1. RETRIEVE: Tìm mẫu tương tự tháng 10 năm trước trong lịch sử
2. AUGMENT: Kết hợp với events: "Tháng 10 năm ngoái là Black Friday"
3. LLM REASON: "Doanh số tháng 10 cao hơn 20% do:
                - Mẫu tăng tương tự năm ngoái (seasonal pattern)
                - Black Friday event sắp diễn ra
                → Khuyến nghị: Tăng lượng nhập kho 15%"
```

---

### Bước 3.2: Tạo Vector Embeddings

Tạo file: `src/ts_rag_engine/embeddings.py`

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingGenerator:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """Load pre-trained embedding model"""
        self.model = SentenceTransformer(model_name)
    
    def embed_text(self, text: str):
        """Convert text to embedding"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_time_series(self, ts_data):
        """Convert time series data to text representation, then embed"""
        # Convert numeric data to description
        text = f"Sales trend: {ts_data.mean():.2f} avg, {ts_data.std():.2f} volatility"
        return self.embed_text(text)

if __name__ == "__main__":
    gen = EmbeddingGenerator()
    
    # Test 1: Embed text
    text = "Sales increased by 20% last month due to seasonal demand"
    emb = gen.embed_text(text)
    print(f"Embedding shape: {emb.shape}")  # (384,) - 384 dimensions
    
    # Test 2: Embed time series
    import pandas as pd
    ts_data = pd.Series([100, 110, 120, 115, 125])
    emb_ts = gen.embed_time_series(ts_data)
    print(f"Time series embedding shape: {emb_ts.shape}")
```

**Chạy test:**
```bash
python src/ts_rag_engine/embeddings.py
# ✅ Output: Embedding shape: (384,)
```

---

### Bước 3.3: Tạo Vector Database (FAISS)

Tạo file: `src/ts_rag_engine/vector_store.py`

```python
import faiss
import numpy as np
import pickle
from typing import List, Tuple

class FAISSVectorStore:
    def __init__(self, dimension=384):
        """Initialize FAISS index"""
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance (Euclidean)
        self.metadata = []  # Lưu thông tin gốc (không embed)
    
    def add_embedding(self, embedding: np.ndarray, metadata: dict):
        """Add embedding to index"""
        embedding = embedding.reshape(1, -1).astype('float32')
        self.index.add(embedding)
        self.metadata.append(metadata)
        print(f"✅ Added embedding. Total: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, k=3) -> List[Tuple[dict, float]]:
        """Search for k most similar embeddings"""
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            results.append((self.metadata[idx], distance))
        return results
    
    def save(self, path: str):
        """Save index to disk"""
        faiss.write_index(self.index, f'{path}/index.faiss')
        with open(f'{path}/metadata.pkl', 'wb') as f:
            pickle.dump(self.metadata, f)
        print(f"✅ Saved to {path}")
    
    def load(self, path: str):
        """Load index from disk"""
        self.index = faiss.read_index(f'{path}/index.faiss')
        with open(f'{path}/metadata.pkl', 'rb') as f:
            self.metadata = pickle.load(f)
        print(f"✅ Loaded from {path}")

if __name__ == "__main__":
    # Test
    vs = FAISSVectorStore(dimension=384)
    
    # Add sample embeddings
    emb1 = np.random.rand(384).astype('float32')
    emb2 = np.random.rand(384).astype('float32')
    
    vs.add_embedding(emb1, {"date": "2017-10-01", "sales": 1000})
    vs.add_embedding(emb2, {"date": "2017-11-01", "sales": 1200})
    
    # Search
    query = np.random.rand(384).astype('float32')
    results = vs.search(query, k=2)
    print(f"Found {len(results)} results")
```

---

## 🤖 PHASE 4: SLACK BOT ĐẦU TIÊN (1-2 ngày)

### Bước 4.1: Tạo Slack App

**Hướng dẫn trên Slack API:**

1. Vào https://api.slack.com/apps
2. Nhấp "Create New App" → "From scratch"
3. Đặt tên: "IDSS-Bot"
4. Chọn workspace test
5. Vào "OAuth & Permissions":
   - Scope: `chat:write`, `commands` → Copy **Bot User OAuth Token**
6. Vào "App Home":
   - Bật "Always Show My Bot as Online"

**Lưu token vào .env:**
```env
SLACK_BOT_TOKEN=xoxb-xxxx
SLACK_SIGNING_SECRET=xxxx
```

---

### Bước 4.2: Slack Bot Đơn giản

Tạo file: `src/integrations/slack_bot_simple.py`

```python
import os
from slack_bolt import App
from dotenv import load_dotenv

load_dotenv()

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

@app.message("hello")
def message_hello(message, say):
    say(f"Hey <@{message['user']}>, nice to meet you!")

@app.command("/sales")
def handle_sales_command(ack, command, say):
    ack()
    
    # Giả lập phân tích
    response = """
📊 *Sales Analysis*
• Current Month: $2,500
• Previous Month: $2,300
• Change: +8.7% ↑
    """
    say(response)

if __name__ == "__main__":
    app.start(port=int(os.getenv("SLACK_PORT", 3000)))
```

**Chạy bot:**
```bash
python src/integrations/slack_bot_simple.py
# Output: ⚡️ Bolt app is running!
```

**Kiểm thử trên Slack:**
- Gõ: `hello`
- Hoặc: `/sales`

---

## 📈 PHASE 5: STREAMLIT DASHBOARD (1-2 ngày)

### Bước 5.1: Dashboard Cơ bản

Tạo file: `web_dashboard/app.py`

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="IDSS Dashboard", layout="wide")

st.title("📊 Intelligent Decision Support System")
st.markdown("---")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('data/processed/superstore_sales_cleaned.csv')

df = load_data()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    selected_region = st.selectbox("Region", df['Region'].unique())
    selected_category = st.selectbox("Category", df['Category'].unique())

# Filter data
filtered_df = df[(df['Region'] == selected_region) & (df['Category'] == selected_category)]

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_sales = filtered_df['Sales'].sum()
    st.metric("Total Sales", f"${total_sales:,.0f}")

with col2:
    avg_profit = filtered_df['Profit'].mean()
    st.metric("Avg Profit", f"${avg_profit:,.0f}")

with col3:
    num_orders = len(filtered_df)
    st.metric("Orders", f"{num_orders:,}")

with col4:
    profit_margin = (filtered_df['Profit'].sum() / filtered_df['Sales'].sum() * 100) if filtered_df['Sales'].sum() > 0 else 0
    st.metric("Profit Margin", f"{profit_margin:.1f}%")

# Charts
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales Over Time")
    daily_sales = filtered_df.groupby('Order Date')['Sales'].sum().sort_index()
    st.line_chart(daily_sales)

with col2:
    st.subheader("Sales by Sub-Category")
    subcat_sales = filtered_df.groupby('Sub-Category')['Sales'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(subcat_sales, title="Top 10 Sub-Categories")
    st.plotly_chart(fig)

# Analysis section
st.markdown("---")
st.subheader("💡 AI Analysis")
st.info("""
**TS-RAG Analysis Result:**
- Current sales trend shows 15% increase YoY
- Similar pattern detected from 2016 Q4
- Recommendation: Increase stock level by 10%
""")
```

**Chạy dashboard:**
```bash
streamlit run web_dashboard/app.py
# Opens at: http://localhost:8501
```

---

## ✅ CHECKLIST HOÀN TẤT

Sau khi hoàn thành các bước trên, bạn cần:

- [ ] Virtual environment setup & dependencies installed
- [ ] .env file created với OpenAI API key
- [ ] Data đã tải & xử lý (data/processed folder full)
- [ ] EDA notebook hoàn thành
- [ ] Embedding generator test passed
- [ ] FAISS vector store test passed
- [ ] Slack bot hello world chạy được
- [ ] Streamlit dashboard hiển thị dữ liệu

---

## 🎓 Tài Liệu Tham Khảo

- **LangChain Docs:** https://python.langchain.com/docs/
- **FAISS Tutorial:** https://github.com/facebookresearch/faiss/wiki
- **Slack API:** https://api.slack.com/docs
- **Streamlit:** https://docs.streamlit.io/

---

## 💬 Gặp Vấn Đề?

| Vấn đề | Giải pháp |
|--------|----------|
| Import error | `pip install -r requirements.txt` lại |
| OpenAI API not working | Check API key trong .env |
| FAISS not found | `pip install faiss-cpu` |
| Slack token invalid | Kiểm tra token từ Slack API dashboard |

---

**Happy Coding! 🚀**
