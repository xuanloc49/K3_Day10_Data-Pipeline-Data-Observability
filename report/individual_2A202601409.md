# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên | Ngô Tuấn Hưng |
| MSSV | 2A202601409 |
| Khóa/Lớp | K3 |
| Tên nhóm | A2 |
| Vai trò chính | Corruption & Integration Owner (Thành viên 4) |
| Repository | https://github.com/xuanloc49/K3_Day10_Data-Pipeline-Data-Observability (branch `01409_NgoTuanHung`) |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------- | --------------------- | ---------------- | ------------------ | ------------ |
| Data corruption pipeline | `src/ingestion/corruption.py::corrupt_clean_dataframe` | Clean DataFrame (`data/clean/papers_clean.json`) | Corrupted DataFrame, `data/results/corruption_log.json` | Hoàn thành |
| Baseline Pipeline (Phase 1) | `src/pipelines/phase1.py::main` | Crossref API / Raw records | Baseline Chroma index, metrics (`baseline_metrics.json`), answers (`baseline_answers.json`), report (`phase1_report.md`) | Hoàn thành |
| Corruption & Repair Flow | `src/pipelines/corruption_flow.py::main` | Baseline dataset, raw records | Corrupted/repaired datasets, embeddings, metrics, comparison report (`corruption_report.md`) | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ------------------------------ | -------- |
| Tích hợp end-to-end pipeline với ChromaDB index & RAG QA agent | Thành viên 1, 2, 3 | Đảm bảo pipeline chạy mượt từ ingestion -> cleaning -> embedding -> eval -> observability -> corruption -> repair |
| Debug & kiểm thử chạy tự động script qua CLI | Toàn nhóm | Đảm bảo `python -m src.pipelines.phase1` và `python -m src.pipelines.corruption_flow` thực thi không lỗi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| ---------------------- | ----------------------------- | ------------------- | --------------- |
| Mô phỏng 6 dạng hư hại dữ liệu (drop, blank summary, inject noise, truncate title, stale date, duplicate) | `src/ingestion/corruption.py` | `data/clean/papers_clean_corrupted.csv`, `data/results/corruption_log.json` | Chạy `corruption_flow.py`, kiểm tra `corruption_log.json` |
| Xây dựng và thực thi Phase 1 Baseline Pipeline | `src/pipelines/phase1.py` | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` | Chạy `python -m src.pipelines.phase1` thành công |
| Xây dựng và thực thi Corruption & Repair Pipeline Flow | `src/pipelines/corruption_flow.py` | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` | Chạy `python -m src.pipelines.corruption_flow` thành công |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Đã tạo thành công `data/results/corruption_log.json` ghi vết chi tiết các thao tác hư hại dữ liệu và `data/reports/corruption_report.md` chứng minh việc khôi phục thành công các chỉ số chất lượng RAG agent sau khi repair từ raw source.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Cần mô phỏng chính xác các lỗi dữ liệu thực tế (dữ liệu bị rỗng, nhiễu, tiêu đề bị cắt gọt, dữ liệu quá cũ, dữ liệu trùng lặp) tác động thế nào tới Vector Search và RAG Agent; đồng thời kết nối toàn bộ hệ thống (ingestion, cleaning, embedding, evaluation, observability) thành 2 pipeline tự động hoàn chỉnh: Phase 1 Baseline và Corruption/Repair Flow.

### Cách triển khai

- **`corrupt_clean_dataframe` (`src/ingestion/corruption.py`):** Tạo bản sao `clean_df`, áp dụng các biến đổi độc hại (bỏ bản ghi mới nhất, xóa summary, chèn xâu rác `[CORRUPTED_GARBAGE_TEXT...]`, cắt ngắn title còn 15 ký tự, set `age_days = 9999`, nhân bản dòng), sau đó cập nhật lại `text_for_embedding` và lưu log chi tiết tại `corruption_log.json`.
- **`phase1.py` (`src/pipelines/phase1.py`):** Load settings, fetch/load raw records từ Crossref, clean dữ liệu, xây dựng Chroma vector DB index (`LocalEmbeddingIndex.build`), tạo evaluation test set, đo lường metrics (`evaluate_pipeline`), chạy quality checks & freshness reports, tạo báo cáo baseline markdown.
- **`corruption_flow.py` (`src/pipelines/corruption_flow.py`):** Nạp baseline clean data, áp dụng `corrupt_clean_dataframe`, lưu corrupted CSV/JSON, rebuild vector index cho corrupted data, chạy đánh giá & observability (phát hiện lỗi pass = False), sau đó thực hiện repair bằng cách load lại raw records từ `raw_records_json` và gọi `build_clean_dataframe`, rebuild index cho repaired data, đánh giá lại và xuất báo cáo so sánh `corruption_report.md`.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ------ |
| Input | Baseline DataFrame (`papers_clean.json`), Raw records (`crossref_records.json`), `Settings` |
| Output | Corrupted/Repaired CSV/JSON, Embeddings JSON, ChromaDB stores, Metrics JSON (`baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`), Markdown Reports |
| Module phụ thuộc | `src/core/config.py`, `src/ingestion/cleaning.py`, `src/ingestion/crossref.py`, `src/retrieval/index.py`, `src/evaluation/metrics.py`, `src/observability/quality.py`, `src/observability/reporting.py` |
| Module sử dụng output | Toàn bộ nhóm sử dụng để xem báo cáo so sánh baseline vs corrupted vs repaired |
| Điều kiện lỗi cần xử lý | Báo lỗi nếu thiếu baseline clean dataset hoặc baseline metrics trước khi chạy corruption flow |

### Cách xác minh

```bash
python -m src.pipelines.phase1
python -m src.pipelines.corruption_flow
```

- **Kết quả mong đợi:** Cả 2 pipeline chạy hoàn tất không ném ra exception; các file `.json` metrics và `.md` reports được sinh ra đầy đủ tại `data/results`, `data/quality`, `data/reports`.
- **Kết quả thực tế:** Phase 1 tạo baseline metrics (Hit Rate 1.0, Token F1 1.0). Flow corruption làm giảm Hit Rate xuống 0.8 và Token F1 xuống 0.7; flow repair khôi phục chỉ số về 1.0.
- **Artifact/log:** `data/results/corruption_log.json`, `data/reports/corruption_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn cơ chế Repair dữ liệu trong pipeline sau khi phát hiện dữ liệu bẩn.
- **Các phương án đã cân nhắc:**
  1. Dùng LLM hoặc thuật toán Imputation để tự động vá/sửa dữ liệu hư hại ngay trên bản corrupted.
  2. Nạp lại dữ liệu gốc từ Nguồn (Raw source of truth) qua `load_raw_records` và chạy lại `build_clean_dataframe`.
- **Phương án đã chọn:** Phương án 2 - Phục hồi từ nguồn dữ liệu thô ban đầu (Raw Records Data Lineage).
- **Lý do:** Đúng bản chất Data Pipeline/Data Observability: khi phát hiện dữ liệu bẩn/hỏng trong warehouse/vectorDB, cách chuẩn xác nhất là replay lại pipeline làm sạch từ nguồn gốc (Data Lineage / Re-ingestion) thay vì tự bịa/sửa chữa dữ liệu trên bản corrupted.
- **Bằng chứng quyết định phù hợp:** Sau khi repair từ raw records, chất lượng dữ liệu sạch 100% (Quality Pass = True, Freshness = Fresh) và các chỉ số evaluation khôi phục lại mức baseline ban đầu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ChromaDB collection mismatch` hoặc lỗi không tìm thấy collection khi rebuild index trên corrupted dataset.
- **Lệnh hoặc bước tái hiện:** Chạy `python -m src.pipelines.corruption_flow` khi chưa chỉ định rõ output path cho embeddings.
- **Nguyên nhân gốc:** `LocalEmbeddingIndex` mặc định derive collection name dựa trên path. Nếu không truyền đúng `embeddings_output_path`, ChromaDB reuse collection cũ gây sai lệch kết quả đánh giá giữa baseline và corrupted.
- **Cách xử lý:** Truyền đường dẫn `embeddings_output_path` riêng biệt (`corrupted_embeddings_json` và `repaired_embeddings_json`) cho `LocalEmbeddingIndex.build(...)` để phân tách rõ ràng vector store cho từng trạng thái.
- **Cách xác minh sau khi sửa:** Kết quả đánh giá của corrupted data độc lập hoàn toàn với baseline và repaired data.
- **Điều học được:** Cần quản lý isolations cho vector DB collections trong quá trình test nhiều trạng thái pipeline.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**  
   `fetch_source_records` gọi Crossref REST API -> Parse về `PaperRecord` -> Lưu `crossref_records.json` -> `build_clean_dataframe` làm sạch (strip HTML, join authors/categories, tính `age_days`, tạo `text_for_embedding`) -> `LocalEmbeddingIndex.build` dùng MiniLM mã hóa `text_for_embedding` thành vector embedding -> Thêm vào ChromaDB collection.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**  
   Bộ câu hỏi test set cố định chứa `ground_truth` và `ground_truth_doc_ids`. Khi RAG Agent trả lời, retrieval search trả ra danh sách doc IDs. Nếu doc ID nằm trong ground-truth doc IDs -> Hit Rate = 1.0. Đáp án sinh ra được so sánh token F1 với `ground_truth` và chấm điểm qua LLM Judge.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**  
   Quality checks kiểm tra tính hợp lệ của cấu trúc/schema (không rỗng title, summary không null, độ dài summary >= 10, paper_id không trùng). Freshness monitoring kiểm tra tuổi thọ dữ liệu (`age_days <= freshness_threshold_days`), đảm bảo dữ liệu không bị lỗi thời (ví dụ bị set năm 2000).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**  
   Để làm biến kiểm soát (control variable). Giữ nguyên câu hỏi và ground truth giúp việc so sánh các chỉ số (Hit Rate, Token F1, Judge score) giữa 3 trạng thái phản ánh chính xác 100% tác động của chất lượng dữ liệu.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**  
   Khi `repaired_quality.json` pass = True, `repaired_freshness_report.json` status = Fresh, và `repaired_metrics.json` ghi nhận Hit Rate = 1.0, Token F1 = 1.0 (khôi phục về mức baseline).

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.0 | 0.8 | 1.0 | Truncate title và drop record làm suy giảm khả năng retrieval |
| `mean_token_f1` | 1.0 | 0.7 | 1.0 | Chèn xâu rác và blank summary làm câu trả lời của agent sai lệch |
| `judge_accuracy` | 1.0 | 0.7 | 1.0 | LLM judge đánh giá kém khi thông tin trong context bị hư hại |
| `mean_judge_score` | 5.0 | 3.8 | 5.0 | Điểm số sụt giảm tương ứng khi context không đầy đủ |
| Quality checks | Pass | Fail | Pass | Bắt được chính xác lỗi `summary_valid = False` |
| Freshness status | Fresh | Stale | Fresh | Bắt được chính xác bản ghi bị ép về năm 2000 (`age_days = 9999`) |

### Kết luận từ số liệu

1. Data bị blank summary & inject noise -> Data quality check `FAIL` -> Token F1 rớt từ 1.0 xuống 0.7.
2. Thực hiện repair tái tạo dữ liệu sạch từ raw records -> Quality check `PASS`, Freshness `Fresh` -> Metrics phục hồi 100% về mức baseline.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**  
Lỗi `blank_summary` và `inject_noise` gây tác động mạnh nhất vì đánh trực tiếp vào `text_for_embedding`, làm vector embedding mất đi ngữ cảnh quan trọng hoặc bị sai lệch hoàn toàn, khiến RAG Agent sinh ảo giác (hallucination).

**Kết quả nào khác với kỳ vọng ban đầu?**  
`retrieval_hit_rate` khi corrupted chỉ rớt xuống 0.8 chứ không rớt xuống 0. Lý do là `title` dù bị truncate ở một số bài nhưng keyword chính ở các câu hỏi tra cứu theo authors/categories vẫn khớp được một vài document.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Trực tiếp chứng minh nguyên lý "Garbage In, Garbage Out": chất lượng dữ liệu đầu vào quyết định trực tiếp hiệu năng của RAG Agent.
2. Data Observability (Quality & Freshness Checks) là lá chắn thiết yếu giúp hệ thống tự phát hiện sự cố dữ liệu trước khi ảnh hưởng đến người dùng cuối.
3. Việc phân chia module rõ ràng (Ingestion, Cleaning, Indexing, Observability, Evaluation, Pipeline Orchestration) giúp làm việc nhóm hiệu quả và dễ dàng tích hợp.

### Nếu có thêm thời gian

Tự động hóa trigger chạy Repair dựa trên Webhook / Event notification từ Observability module khi Quality Check ném về status Fail, thay vì phải chạy script thủ công.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Ngô Tuấn Hưng  
**Ngày xác nhận:** 2026-08-06
