# Intelligent Decision Support System (IDSS) - Lightweight TS-RAG Architecture

**Hệ thống Hỗ trợ Ra Quyết định Thông minh dựa trên Time-Series RAG dành cho Doanh nghiệp Bán lẻ và Logistics**

![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Tổng Quan Dự Án

IDSS là một hệ thống AI hỗ trợ ra quyết định kinh doanh được thiết kế theo hướng **tối ưu hóa (lightweight)**. Khắc phục nhược điểm của các hệ thống AI phụ thuộc quá nhiều vào LLM lớn và cồng kềnh, hệ thống này được xây dựng để hoạt động **off-line hoàn toàn**, tối ưu bộ nhớ bằng cách kết hợp **Time-Series RAG (TS-RAG)** với **Rule-Based Expert System**.

Hệ thống cho phép các nhà quản lý doanh nghiệp đưa ra quyết định dự báo nhanh, không chỉ hiển thị các con số trực quan thông qua Web Dashboard, mà còn cung cấp **giải thích logic rõ ràng (Explainable AI - XAI)** và các khuyến nghị hành động cụ thể cho từng loại sự kiện (tăng trưởng, rủi ro, dự trữ tồn kho).

### 🎯 Mục tiêu & Tính năng Chính

- ✅ **Phân tích Chuỗi Thời Gian**: Phân tích dữ liệu bán hàng, phát hiện xu hướng và dị thường tự động thông qua Z-score anomaly detection.
- ✅ **Offline TS-RAG Engine**: Truy xuất mẫu hình lịch sử tương tự. Hệ thống tự động chuyển đổi Time-series thành Dữ liệu Text phân tích (Semantic Text) và sử dụng thuật toán nhúng TF-IDF/N-gram hash rút gọn để index vào **FAISS**. Không yêu cầu GPU hay API trả phí.
- ✅ **Expert System Reasoning**: Tập luật (Rule-based engine) sinh báo cáo ngôn ngữ tự nhiên, cảnh báo rủi ro dựa trên dữ liệu RAG truy xuất được, đảm bảo độ chính xác (deterministic) và chi phí thấp.
- ✅ **Web Dashboard Trực Quan**: Giao diện UI/UX hiện đại bằng Streamlit với custom CSS, hỗ trợ điều hướng Side-bar và Top-navbar, filter linh hoạt.
- ✅ **Logging & Compliance (Tuân thủ)**: Tuân thủ dự thảo Luật AI Việt Nam 2025. Tính năng ghi nhật ký hoạt động rẽ nhánh đầy đủ, hỗ trợ Audit và đánh giá rủi ro an toàn AI.

---

## 🏗️ Kiến trúc Modular & Tối ưu hóa

Dự án đã được **Tái cấu trúc (Refactoring)** theo chuẩn Enterprise, đồng thời tập trung loại bỏ dư thừa tài nguyên phần cứng:

1. **Lightweight Backend Layer**:
   - Chuyển đổi từ mô hình sử dụng Langchain/LlamaIndex, OpenAI (~2GB+ space/RAM) xuống cấu trúc Lightweight Python tự thiết kế (chỉ khoảng ~350MB).
   - Tự xây dựng Embedding Engine offline.

2. **Dữ liệu & Pipeline**:
   - Tích hợp luồng sinh dữ liệu giả lập (`event_simulator.py`) cho tập dataset Superstore (2014-2017).
   - End-to-end từ bước đọc dữ liệu, làm sạch, tìm kiếm vector, tới lưu file kết quả.

3. **Cấu trúc Thư mục (`src/`)**:
   - `data_pipeline/`: Module nạp, xử lý và mô phỏng sự kiện.
   - `ts_rag_engine/`: Module lõi về xử lý Embedding, Vector retrieval (FAISS) và Agent Suy luận.
   - `agents/`: Phân luồng điều phối (SupervisorAgent, ForecastAgent, AnomalyAgent).
   - `compliance/`: Log, giải thích quyết định của AI hỗ trợ kiểm toán (Audit logs).

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Khởi Động

### 1. Setup Môi trường
Hệ thống sử dụng Python 3.11+. Tránh cài đặt tại các đường dẫn có khoảng trắng/kí tự đặc biệt.

```bash
# Clone source code
git clone <url-to-your-repo>
cd IDSS-AI

# Phân tách môi trường ảo (Virtual Environment)
python -m venv .venv

# Active môi trường:
# Trên Windows cmd/powershell:
.venv\Scripts\activate
# Trên Linux/Mac:
# source .venv/bin/activate

# Cài đặt thư viện yêu cầu đã được tối ưu
pip install -r requirements.txt
```

### 2. Chạy Data Pipeline & Cập nhật Index FAISS
Quá trình này sẽ giả lập, làm sạch dữ liệu, tạo Vector DB cục bộ, và chạy thử qua một luồng pipeline phân tích hoàn chỉnh:

```bash
python main_pipeline.py
```
*Kết quả:* Các thư mục dữ liệu `data/` (data/processed, data/vector_db) và `logs/` sẽ được tự động cập nhật để chuẩn bị cho Dashboard.

### 3. Mở Web Dashboard Trực Quan
Ứng dụng giao diện được chạy trên Streamlit.

```bash
streamlit run web_dashboard/app.py --server.port 8501
```

Mở trình duyệt truy cập `http://localhost:8501` để trải nghiệm các phân hệ:
- **🏠 Tổng quan**: Tổng quan dữ liệu có bộ lọc tùy biến liên kết chéo.
- **📈 Phân tích Dự báo**: Giao diện chọn kịch bản để kích hoạt Agent TS-RAG.
- **🚨 Phát hiện Bất thường**: Đánh giá biến động quá mức thông qua thuật toán Z-score.
- **📋 Nhật ký Kiểm toán**: Report Compliance Audit track lại toàn bộ các decision của AI.

---

## 🐳 Khởi chạy với Docker

Dự án đã đóng gói `Dockerfile` sẵn sàng triển khai dễ dàng:

```bash
docker build -t idss-pipeline .
# Mount volume lưu kết quả và chạy:
docker run --rm -v ${PWD}/data:/app/data idss-pipeline
```

---

## 📝 Đóng góp & Quản lý Git

- Dự án sử dụng mô hình Git Branch workflows. `main` cho Production code và phân nhánh xử lý chức năng từ branch `dev` hoặc `feature/*`.
- Tuân thủ PEP-8.

**Tác giả & Đóng góp:**   
**Phiên bản hiện tại:** v1.0.0 (Cập nhật T04/2026)
