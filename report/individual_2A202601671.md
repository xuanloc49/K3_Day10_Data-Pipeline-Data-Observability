# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên | Trần Xuân Lộc |
| MSSV | 2A202601671 |
| Khóa/Lớp | K3 |
| Tên nhóm | A2 |
| Vai trò chính | Data Observability Owner |
| Repository | https://github.com/xuanloc49/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data quality checks | `quality.py` / `run_data_quality_checks` | `data/clean/papers_clean.csv` | `data/quality/*_quality.json` | Hoàn thành |
| Freshness monitoring | `quality.py` / `build_freshness_report` | `data/clean/papers_clean.csv` | `data/quality/*_freshness_report.json` | Hoàn thành |
| Baseline Report | `reporting.py` / `generate_phase1_report` | Các dict metrics, quality | `data/reports/phase1_report.md` | Hoàn thành |
| Comparison Report | `reporting.py` / `generate_corruption_report` | Các dict metrics | `data/reports/corruption_report.md` | Hoàn thành |


Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Phân tích và viết báo cáo nhóm | Báo cáo chung `group_report.md` | Hoàn thành điền thông số so sánh metrics |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Kiểm tra độ tươi và tính hợp lệ của dữ liệu | `src/observability/quality.py` | `data/quality/baseline_quality.json` | Chạy `run_phase1.py` |
| Tạo báo cáo đối chiếu suy giảm hiệu năng do corruption | `src/observability/reporting.py` | `data/reports/corruption_report.md` | Chạy `run_corruption_flow.py` |


Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Đã tự động tạo thành công báo cáo so sánh `data/reports/corruption_report.md` chỉ ra trực quan việc giảm 30% F1-score và Hit Rate xuống 0.8 khi dữ liệu bị hỏng.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Đảm bảo dữ liệu trước khi đưa vào RAG agent phải hợp lệ (không rỗng, không trùng DOI) và đủ mới (dưới 180 ngày). Giúp hệ thống phát tín hiệu cảnh báo kịp thời khi dữ liệu từ Crossref bị hỏng thay vì âm thầm trả kết quả sai cho người dùng.

### Cách triển khai

Sử dụng DataFrame của pandas để vector hóa việc kiểm tra: đánh giá `is_unique` và `notna` cho `paper_id`. Đoạn check summary loại bỏ các nội dung quá ngắn (< 10 ký tự). Freshness được kiểm định thông qua việc so sánh cột `age_days` với `freshness_threshold_days` truyền từ cấu hình môi trường.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input | `df: pd.DataFrame` chứa dữ liệu đã làm sạch, đối tượng `Settings` |
| Output | Các file `.json` và `.md` lưu tại `data/quality` và `data/reports` |
| Module phụ thuộc | `src/core/config.py`, `pandas` |
| Module sử dụng output | `src/pipelines/phase1.py` và `corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Nếu một vài cột quan trọng bị mất hoặc thiếu trong df |

### Cách xác minh

```bash
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Report báo cáo rõ ràng dữ liệu bị corrupted (passed = False) và agent bị suy giảm metric.
- **Kết quả thực tế:** Code sinh ra `corrupted_quality.json` bắt chính xác lỗi `summary_valid = False` và `freshness_valid = False`.
- **Artifact/log:** `data/quality/corrupted_quality.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn cách xuất báo cáo đối chiếu giữa baseline, corrupted, và repaired.
- **Các phương án đã cân nhắc:** Xuất thành HTML động hoặc ghi thẳng vào file Markdown qua template string cơ bản.
- **Phương án đã chọn:** Dùng Markdown với `json.dumps()` cho các metrics dictionary.
- **Lý do:** Tối ưu hóa tính đơn giản, dễ theo dõi log trên Git, phù hợp chuẩn báo cáo của bài Lab mà không cần thêm thư viện phức tạp.
- **Bằng chứng quyết định phù hợp:** File `corruption_report.md` đọc rất rõ ràng, tích hợp tốt với Github markdown.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `NotImplementedError: Student task: implement phase1 pipeline.`
- **Lệnh hoặc bước tái hiện:** `uv run python script/run_phase1.py` ở thời điểm đầu tích hợp.
- **Nguyên nhân gốc:** Thành viên phụ trách pipeline chưa push code module `phase1.py` lên nhánh chính.
- **Cách xử lý:** Sync và `git pull` nhánh code mới nhất có đủ phase1.py để chạy test pipeline end-to-end.
- **Cách xác minh sau khi sửa:** Chạy lại script trả về kết quả `Phase 1 baseline pipeline completed successfully.`
- **Điều học được:** Tầm quan trọng của việc đồng bộ tích hợp liên tục (CI) và trao đổi tiến độ trong teamwork.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** N/A
- **Những gì đã loại trừ:** N/A
- **Bước tiếp theo:** N/A

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Data từ Crossref được ingestion kéo về lưu dưới dạng raw, sau đó làm sạch và trích xuất cột `text_for_embedding` rồi mã hóa qua model MiniLM để đẩy vào ChromaDB index.
2. Ground-truth ID giúp biết chính xác source document nằm ở đâu. Nếu retrieval trả về ID trùng ground-truth -> Hit Rate = 1.0.
3. Quality check kiểm tra cấu trúc/schema/độ logic của dữ liệu (như rỗng, null, length). Freshness giám sát việc dữ liệu có bị cũ/lỗi thời không theo thời gian thực (đảm bảo tính cập nhật của pipeline).
4. Để đảm bảo tính nhất quán (control variable). Bất kỳ độ lệch metric nào cũng 100% là do dữ liệu đầu vào bị hỏng/phục hồi chứ không phải do độ khó của câu hỏi thay đổi.
5. Khi và chỉ khi các chỉ số data quality pass 100%, freshness báo Fresh, và evaluation metrics (Hit Rate, F1) phục hồi ngang bằng chỉ số baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.0 | 0.8 | 1.0 | Context bị mất khi drop và truncate |
| `mean_token_f1` | 1.0 | 0.7 | 1.0 | Giảm mạnh do dữ liệu bị inject noise |
| `judge_accuracy` | 1.0 | 0.7 | 1.0 | Chất lượng câu trả lời tệ khi mất summary |
| `mean_judge_score` | 5.0 | 3.8 | 5.0 | LLM chấm điểm kém khi không có thông tin |
| Quality checks | Pass | Fail | Pass | Bắt được chính xác lỗi null và noise |
| Freshness status | Fresh | Stale | Fresh | Phát hiện ngay bản ghi năm 2000 |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data bị blank summary & inject noise → `summary_valid` fail → Mất context khiến `mean_token_f1` giảm từ 1.0 xuống 0.7.
2. Gọi lại script Fetch API gốc làm Repair → `summary_valid` pass, freshness pass → Metric của Agent phục hồi hoàn toàn.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Lỗi "blank_summary" và "inject_noise" gây tác động mạnh nhất. Nó đánh thẳng vào `text_for_embedding` làm embedding bị nhiễu loạn hoặc rỗng thông tin quan trọng. Khiến hit rate giảm, mô hình sinh ảo giác (hallucination) và score giảm sâu.

Kết quả nào khác với kỳ vọng ban đầu?

Hit Rate chỉ rớt xuống 0.8 chứ không rớt sâu hơn. Giả thuyết là do `title` vẫn được mã hóa chung với text nên semantic search đôi khi vẫn tìm được context nhờ tiêu đề. Đã kiểm tra lại log và thấy context vẫn về đúng ở một số câu hỏi liên quan tiêu đề.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Pipeline tốt cần xử lý chuẩn các case rate limit (như API Crossref) và ghép mượt mà các khâu ingestion-clean-embedding.
2. Data Observability là cứu cánh giúp chặn bắt dữ liệu bẩn trước khi user nhận được câu trả lời vô nghĩa từ RAG.
3. Garbage in, garbage out. Agent tốt đến mấy, xài model to đến mấy mà ChromaDB index toàn rác thì `judge_score` vẫn tệ.

### Nếu có thêm thời gian

Bổ sung thêm rule Expectation bằng thư viện Great Expectations (Gx) thay vì code pandas thuần túy. Lý do: Gx hỗ trợ render data doc HTML siêu trực quan. Đo bằng cách kiểm tra thư mục `data/quality/gx`.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Xuân Lộc
**Ngày xác nhận:** 2026-08-06
