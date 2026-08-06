# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3             |
| Tên nhóm         | A2   |
| Repository         | https://github.com/xuanloc49/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Trần Xuân Lộc | 2A202601671 | Data Observability Owner | quality.py, reporting.py |
| 2 | Ngô Tuấn Hưng | 2A202601409 | Corruption & Integration Owner | corruption.py, phase1.py, corruption_flow.py |
| 3 | Đào Ngọc Bích | 2A202601745 | Data Model & Eval Set Owner | cleaning.py, testset.py |
| 4 | Vũ Đức Anh | 2A202601191 | Source Ingestion Owner | crossref.py |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

- **Hoàn thành**: Nhóm đã hoàn thành toàn bộ baseline pipeline (ingestion, cleaning, eval setup, baseline evaluation) và quy trình quan sát chất lượng dữ liệu (Data Observability), cũng như mô phỏng và chạy thành công kịch bản dữ liệu bị hỏng (corruption) và phục hồi (repair).
- **Artifacts**: Đã tự động sinh ra các dữ liệu thô (raw), dữ liệu sạch (clean), embeddings (ChromaDB), file test_set, báo cáo baseline markdown, và các báo cáo quality/freshness dạng JSON.
- **Tác động của Corruption**: Các lỗi giả lập (chẳng hạn như làm mất title/summary, thêm nhiễu, làm cũ ngày tháng) đã khiến chất lượng dữ liệu (Data Quality) fail toàn bộ (paper_id_valid, summary_valid, freshness_valid báo false). Điều này dẫn đến hiệu suất của agent suy giảm nghiêm trọng (retrieval_hit_rate giảm từ 1.0 xuống 0.8, mean_token_f1 từ 1.0 xuống 0.7, mean_judge_score từ 5.0 xuống 3.8).
- **Phục hồi (Repair)**: Quá trình repair đã khôi phục thành công dữ liệu từ nguồn gốc (Crossref API), qua đó phục hồi hoàn toàn các chỉ số chất lượng dữ liệu (passed = true) và các metric của RAG agent (retrieval_hit_rate và token f1 trở lại 1.0).
- **Blocker/giới hạn**: Hạn chế chính là thời gian giới hạn khi tải các dependencies nặng của agent, đồng thời API nguồn Crossref đôi khi bị rate limit.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API | Gọi API, parse response | `data/raw/` | Vũ Đức Anh |
| Cleaning          | `data/raw/` | Lọc record, chuẩn hoá schema | `data/clean/` | Đào Ngọc Bích |
| Embedding/index   | `data/clean/` | Tạo embedding bằng all-MiniLM | `data/embeddings/` | Ngô Tuấn Hưng |
| Evaluation        | `data/clean/` | Query RAG agent, tính metrics | `data/results/` | Đào Ngọc Bích |
| Observability     | `data/clean/` | Kiểm tra độ sạch, độ tươi | `data/quality/` | Trần Xuân Lộc |
| Corruption/repair | `data/clean/` | Xóa, làm mờ, sửa sai data | `data/results/` | Ngô Tuấn Hưng |
| Orchestration     | Các module | Ghép pipeline hoàn chỉnh | `data/reports/` | Ngô Tuấn Hưng |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER` | `gemini`         |
| `LLM_MODEL` | `gemini-2.5-flash`         |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2`         |
| Số lượng Crossref records | 24         |
| Retrieval`top_k` | 4         |
| Freshness threshold | 180         |
| Random seed, nếu có | N/A         |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 10:01 | `data/reports/phase1_report.md` |
| Corruption flow | Thành công | 2026-08-06 10:07 | `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | `agentic retrieval augmented generation large language model`, filter: `has-abstract:true`                  |
| Thời điểm lấy dữ liệu | 2026-08-06                           |
| Số record nhận được | 24                         |
| Cơ chế retry/backoff | Sử dụng urllib3 Retry với backoff factor                       |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | `str` | Có | DOI của bài báo | Bỏ qua record nếu thiếu |
| `title` | `str` | Có | Tiêu đề | Bỏ qua record nếu thiếu |
| `summary` | `str` | Không | Tóm tắt | Điền chuỗi rỗng nếu thiếu |
| `published` | `str` | Không | Ngày xuất bản | Điền chuỗi rỗng nếu thiếu |
| `paper_id` | `str` | Có | DOI của bài báo | Bỏ qua record nếu thiếu |
| `title` | `str` | Có | Tiêu đề | Bỏ qua record nếu thiếu |
| `summary` | `str` | Không | Tóm tắt | Điền chuỗi rỗng nếu thiếu |
| `published` | `str` | Không | Ngày xuất bản | Điền chuỗi rỗng nếu thiếu |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Record không có title hoặc DOI | Completeness/Validity | 0 | Chạy `quality.py` kiểm tra `title_valid` |
| Record cũ quá 180 ngày | Freshness | 0 | Chạy `quality.py` kiểm tra `freshness_valid` |


Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

`text_for_embedding` được ghép từ `title`, `authors`, và `summary` để tối ưu cho semantic search. `document_id` chính là `paper_id` (DOI) để đảm bảo tính duy nhất. `age_days` được tính bằng số ngày từ lúc `published` tới hiện tại.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi | 10 |
| Các`question_type` | `factual`, `summary` |
| Ground-truth document ID | Trích xuất trực tiếp từ `paper_id` của record mẫu |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB (`papers-baseline`) |
| Retrieval`top_k` | 4                   |
| LLM provider/model | Gemini (`gemini-2.5-flash`) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Test set được sinh từ dữ liệu sạch (baseline) và được giữ nguyên nhằm tạo thước đo nhất quán. Khi đối chiếu kết quả của RAG agent giữa 3 trạng thái (baseline, corrupted, repaired), việc dùng chung bộ test set giúp cô lập biến số, đảm bảo sự suy giảm metric thuần túy là do chất lượng data index bị giảm chứ không phải do câu hỏi thay đổi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | Sinh tự động |
| Cleaned dataset          | `data/clean/`                        | Có | Sinh tự động |
| Embedding manifest/index | `data/embeddings/`                   | Có | Sinh tự động |
| Evaluation set           | `data/eval/`                         | Có | Sinh tự động |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Sinh tự động |
| Quality/freshness        | `data/quality/`                      | Có | Sinh tự động |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Sinh tự động |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` | 1.0 | Rất tốt, agent tìm được đúng context |
| `mean_token_f1` | 1.0 | Đáp án sinh ra trùng khớp cao với ground truth |
| `judge_accuracy` | 1.0 | LLM-as-a-judge đánh giá các câu trả lời đều chính xác |
| `mean_judge_score` | 5.0 | Điểm tối đa trên thang 1-5 |
| Ragas, nếu có | N/A | Chưa bật RUN_RAGAS=1 |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Tính duy nhất `paper_id` | Uniqueness | True | Pass (100%) | `baseline_quality.json` |
| Không có dòng rỗng | Completeness | True | Pass (100%) | `baseline_quality.json` |


### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | `data/clean/papers_clean.csv` |
| Timestamp mới nhất | 2026-08-01 |
| Ngưỡng freshness | 180 ngày |
| Trạng thái baseline | Fresh |
| Lý do | Không có row nào stale (stale_rows=0) |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Xoá record mới | Bỏ 2 records mới nhất | 2 | Freshness fail | `corrupted_quality.json` | Tải lại từ gốc |
| Inject noise | Thêm nhiễu vào summary | 1 | F1 giảm | `corrupted_metrics.json` | Clean lại |
| Blank summary | Xóa summary | 1 | summary_valid fail | `corrupted_quality.json` | Tải lại |


Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Có đủ các loại corruption như drop_latest, blank_summary, inject_noise, truncate_title, stale_published_date.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair được thực hiện bằng cách chạy lại pipeline ingestion để lấy trực tiếp dữ liệu chuẩn từ nguồn Crossref (hoặc fallback về dataset gốc chưa bị sửa), thay vì cố gắng sửa các mẫu đã bị nhiễu. Điều này đảm bảo tính toàn vẹn tuyệt đối của dữ liệu.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate` | 1.0 | 0.8 | 1.0 | -0.2 | 100% | Giảm rõ rệt do thiếu context |
| `mean_token_f1` | 1.0 | 0.7 | 1.0 | -0.3 | 100% | Giảm do nhiễu và thiếu summary |
| `judge_accuracy` | 1.0 | 0.7 | 1.0 | -0.3 | 100% | Câu trả lời sai thực tế |
| `mean_judge_score` | 5.0 | 3.8 | 5.0 | -1.2 | 100% | LLM đánh giá kém hơn |
| Quality checks pass/fail | Pass | Fail | Pass | Fail | Phục hồi hoàn toàn | Data quality report bắt được lỗi |
| Freshness status | Fresh | Stale | Fresh | Stale | Phục hồi hoàn toàn | Việc đổi date thành 2000 khiến data bị stale |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. Làm rỗng summary và thêm nhiễu → `summary_valid` fail, báo lỗi quality → Làm `mean_token_f1` và `judge_accuracy` suy giảm do agent không tìm đủ thông tin.
2. Fetch lại bản gốc từ nguồn API → `freshness` và `quality checks` Pass trở lại → Phục hồi hoàn toàn độ chính xác của agent (các chỉ số trở lại 1.0).

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Rate limit từ Crossref API khiến pipeline ingestion thất bại.
- **Nguyên nhân:** Gửi request liên tục mà không có trễ, hoặc không truyền header User-Agent chuẩn.
- **Cách xử lý:** Cấu hình urllib3 Retry, thiết lập backoff_factor và cài đặt header mang ý nghĩa định danh rõ ràng.
- **Cách xác minh:** Chạy `run_phase1.py` lại nhiều lần, kiểm tra số lượng bản ghi `data/raw/` không bị hụt.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Dữ liệu thô ít | Metrics chưa phản ánh hiệu năng scale lớn | Mở rộng Top_K và nạp dataset vài ngàn records |
| Chưa có LLM đánh giá logic sâu | Điểm số F1 đôi khi bị thiên vị (bias) | Tích hợp RAGAS với custom prompt |


## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
