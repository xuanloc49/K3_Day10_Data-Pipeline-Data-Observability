# Group Report — Day 10: Data Pipeline & Data Observability

> Báo cáo chung nhóm A2. Phần ingestion/cleaning đã điền theo code và artifact hiện có. Các mục evaluation, baseline metrics, corruption/repair và comparison để thành viên phụ trách điền tiếp khi có kết quả.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                                                                 |
| ------------------ | -------------------------------------------------------------------------- |
| Khóa/Lớp         | K3                                                                         |
| Tên nhóm         | A2                                                                         |
| Repository         | https://github.com/xuanloc49/K3_Day10_Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành | 2026-08-06                                                                 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Vũ Đức Anh | 2A202601191 | Source Ingestion Owner | `src/ingestion/crossref.py`; raw artifacts `data/raw/`; (đã implement thêm `src/ingestion/cleaning.py` + `data/clean/` trong code hiện tại) |
| 2 | [Họ tên] | [MSSV] | [Data model & evaluation-set owner — khuyến nghị] | [Ví dụ: `testset.py`; xác nhận/mở rộng cleaning nếu cần] |
| 3 | [Họ tên] | [MSSV] | [Observability owner — khuyến nghị] | [Ví dụ: `quality.py`, `reporting.py`] |
| 4 | [Họ tên] | [MSSV] | [Corruption & integration owner — khuyến nghị] | [Ví dụ: `corruption.py`, `phase1.py`, `corruption_flow.py`] |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

Nhóm A2 hiện đã hoàn thành khối nguồn dữ liệu: gọi Crossref REST API (`https://api.crossref.org/works`), parse về `PaperRecord`, lưu raw response/raw records, và làm sạch thành dataset sẵn sàng embed (`papers_clean.csv` / `papers_clean.json`). Lần chạy ngày 2026-08-06 nhận 24 bản ghi API, parse được 24 raw records và 24 clean rows; abstract có thẻ JATS/HTML đã được strip khi cleaning. Các khối còn lại (evaluation set, embedding/index, baseline pipeline end-to-end, quality/freshness, corruption/repair, comparison metrics) chưa có artifact trong `data/` nên chưa kết luận được impact của corruption hay mức phục hồi sau repair. Blocker chính hiện tại là pipeline chưa chạy hết Pha 1/Pha 2 — cần thành viên phụ trách orchestration và các module downstream hoàn thiện rồi cập nhật lại các mục metrics trong báo cáo này.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

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
| Ingestion         | Crossref `/works` + `settings.source_query` / `source_filter` / `max_results` | Fetch HTTP, retry/backoff 429/503, parse `PaperRecord`, lưu JSON | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Vũ Đức Anh |
| Cleaning          | `list[PaperRecord]` | Drop title trống / summary &lt; 100 ký tự; strip HTML/XML; join authors/categories; `age_days`; `text_for_embedding`; dedupe `paper_id` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Vũ Đức Anh (code hiện tại); [TV2 xác nhận nếu đổi ownership] |
| Embedding/index   | Clean dataframe | [MiniLM + Chroma — starter có sẵn, chờ orchestration] | [Đường dẫn `data/embeddings/`, `data/chroma/`] | [Thành viên] |
| Evaluation        | Clean dataframe | [Test set + metrics] | [Đường dẫn `data/eval/`, `data/results/`] | [Thành viên] |
| Observability     | Clean dataframe | [Quality/freshness checks] | [Đường dẫn `data/quality/`] | [Thành viên] |
| Corruption/repair | Clean baseline + raw | [Corruption và repair] | [Đường dẫn corrupted/repaired + comparison] | [Thành viên] |
| Orchestration     | Settings + modules trên | [Thứ tự chạy phase1 / corruption_flow] | [Reports/metrics] | [Thành viên] |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini` (mặc định `config.py`; chưa bắt buộc cho ingestion/cleaning) |
| `LLM_MODEL`                | `gemini-2.5-flash` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `max_results=24` (lần fetch: 24 raw / 24 clean) |
| Retrieval `top_k`           | `4` |
| Freshness threshold          | `180` ngày (`from-pub-date` + ngưỡng freshness) |
| Random seed, nếu có        | [Chưa dùng / thành viên evaluation điền] |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Cách đã dùng cho phần ingestion/cleaning (chỉ cài deps tối thiểu vì mạng yếu):

```bash
uv pip install --python .venv/Scripts/python.exe requests pandas python-dotenv
uv pip install --python .venv/Scripts/python.exe -e . --no-deps
```

Khi chạy full pipeline, nhóm nên dùng:

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

Ghi chú: `phase1.py` / `corruption_flow.py` vẫn là `NotImplementedError` tại thời điểm viết mục này — thành viên orchestration cập nhật khi đã chạy được.

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Fetch + clean (ingestion) | Thành công | 2026-08-06 ~09:22 | `data/raw/crossref_*.json`, `data/clean/papers_clean.*` |
| Baseline pipeline | [Chưa chạy / thành viên orchestration điền] | [Thời gian] | [Artifact hoặc log đã che secret] |
| Corruption flow   | [Chưa chạy / thành viên orchestration điền] | [Thời gian] | [Artifact hoặc log đã che secret] |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API — `https://api.crossref.org/works` |
| Query/filter                | query=`agentic retrieval augmented generation large language model`; filter=`from-pub-date:2026-02-07,has-abstract:true` (filter date phụ thuộc ngày chạy + `freshness_threshold_days=180`) |
| Thời điểm lấy dữ liệu | 2026-08-06T09:22:42 (mtime artifact) |
| Số record nhận được    | 24 items API → 24 `PaperRecord` → 24 clean rows |
| Cơ chế retry/backoff      | Tối đa 5 lần; status 429/503 (ưu tiên `Retry-After`, không thì exponential backoff `1.5 * 2^attempt` giây); lỗi mạng cũng backoff |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | string (DOI) | Có | ID ổn định của bài báo | Bỏ record nếu không có DOI/URL/title |
| `title` | string | Có | Tiêu đề | Raw: bỏ nếu trống; clean: strip markup, bỏ nếu trống |
| `summary` | string | Có | Abstract/description | Raw: bỏ nếu thiếu abstract/description; clean: strip markup, bỏ nếu &lt; 100 ký tự |
| `authors` | list[string] | Không | Danh sách tác giả đã flatten | Empty list nếu thiếu |
| `categories` | list[string] | Không | Subject/topic Crossref | Empty list nếu thiếu |
| `primary_category` | string | Không | Category đầu tiên | `""` nếu không có categories |
| `published` | string `YYYY-MM-DD` | Ưu tiên có | Ngày xuất bản | Lấy từ published-print/online/published/issued/created; clean tính `age_days` nếu parse được |
| `updated` | string `YYYY-MM-DD` | Không | Ngày cập nhật/deposited | Fallback date-parts Crossref |
| `abs_url` | string | Không | URL abstract/DOI | `https://doi.org/{DOI}` nếu thiếu URL |
| `pdf_url` | string | Không | Link PDF nếu có | `""` nếu không tìm thấy |
| `comment` | string | Không | Container/journal title | `""` nếu thiếu |
| `authors_joined` | string | Clean | Authors ghép bằng `, ` | Dùng trong embedding/metadata |
| `categories_joined` | string | Clean | Categories ghép bằng `, ` | Có thể rỗng |
| `summary_chars` | int | Clean | Độ dài summary sau clean | Dùng kiểm tra completeness |
| `age_days` | int / null | Clean | Số ngày từ `published` đến `run_date` | `null` nếu không parse được ngày |
| `text_for_embedding` | string | Clean | Text đưa vào embed | Bắt buộc sau cleaning |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại record không có title hoặc summary &lt; 100 ký tự | Completeness / Validity | 0 (24→24 trong lần chạy hiện tại) | So sánh `len(raw_records)` vs `len(clean)` |
| Strip thẻ XML/HTML (`&lt;jats:p&gt;`, `&lt;b&gt;`, …) khỏi title/summary | Consistency / Validity | Toàn bộ clean rows có abstract JATS ở raw | Raw có JATS; clean summary không còn thẻ HTML |
| Gộp authors/categories thành `*_joined` | Consistency | 24 | Cột trong `papers_clean.json` |
| Chuẩn hóa `published` → `YYYY-MM-DD`, tính `age_days` | Freshness / Timeliness | 24 (có published parse được trong sample) | Cột `published`, `age_days` |
| Dedupe theo `paper_id`, sort theo published giảm dần | Uniqueness | 0 trùng trong lần chạy hiện tại | `paper_id` unique trong clean CSV |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

- **Document ID / `paper_id`:** dùng DOI Crossref; nếu thiếu thì fallback URL hoặc title đã chuẩn hóa.
- **`age_days`:** parse `published` (hoặc `updated` nếu thiếu) về ngày, lấy `(run_date.date() - published_date).days`.
- **`text_for_embedding`:** `Title: {title} | Authors: {authors_joined} | Summary: {summary}` sau khi strip markup.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | [Thành viên evaluation điền] |
| Các `question_type`                    | [Thành viên evaluation điền] |
| Ground-truth document ID                 | [Đối chiếu `paper_id`] |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | Chroma; collection mặc định `papers-baseline` / `papers-corrupted` / `papers-repaired` |
| Retrieval `top_k`                       | `4` |
| LLM provider/model                       | `gemini` / `gemini-2.5-flash` (mặc định config) |
| Test set dùng chung cho ba trạng thái | [Đường dẫn `data/eval/test_set.json` khi có] |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

[Thành viên evaluation/integration điền: cần cùng test set để so sánh công bằng ba trạng thái.]

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | `crossref_response.json`, `crossref_records.json` |
| Cleaned dataset          | `data/clean/`                        | Có | `papers_clean.csv`, `papers_clean.json` |
| Embedding manifest/index | `data/embeddings/`                   | Thiếu | Chờ chạy phase1 |
| Evaluation set           | `data/eval/`                         | Thiếu | Chờ `testset.py` |
| Baseline metrics         | `data/results/baseline_metrics.json` | Thiếu | Chờ phase1 |
| Quality/freshness        | `data/quality/`                      | Thiếu | Chờ observability |
| Baseline report          | `data/reports/phase1_report.md`      | Thiếu | Chờ reporting/orchestration |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     [Điền sau khi có `baseline_metrics.json`] | [Ý nghĩa] |
| `mean_token_f1`      |     [ ] | [ ] |
| `judge_accuracy`     |     [ ] | [ ] |
| `mean_judge_score`   |     [ ] | [ ] |
| Ragas, nếu có        | [N/A hoặc giá trị] | [ ] |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| [Thành viên observability điền] | [Dimension] | [Ngưỡng] | [Pass/Fail] | [Artifact `data/quality/`] |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean dataset (`age_days` đã có trong schema) |
| Timestamp mới nhất       | Sample clean: `published` mới nhất quan sát được `2026-08-01` |
| Ngưỡng freshness         | 180 ngày (`settings.freshness_threshold_days`) |
| Trạng thái baseline      | [Observability điền sau khi chạy freshness report] |
| Lý do                     | Cột `age_days` đã sẵn trong clean; chờ `build_freshness_report` |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| [Thành viên corruption điền] | [ ] | [ ] | [ ] | [ ] | [ ] |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Thiếu
- Nhận xét: Chưa chạy corruption flow.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

[Thành viên corruption/integration điền. Gợi ý: repair từ `data/raw/crossref_records.json` / raw response rồi chạy lại cleaning, không “sửa tay” metric.]

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | Chờ artifacts |
| `mean_token_f1`        |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [ ] |
| `judge_accuracy`       |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [ ] |
| `mean_judge_score`     |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [ ] |
| Quality checks pass/fail |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [ ] |
| Freshness status         |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [ ] |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. [Điền sau khi có metrics — ví dụ: corruption blank summary → quality fail → retrieval/answer giảm.]
2. [Điền sau repair — ví dụ: repair từ raw → quality/freshness hồi → metric agent hồi hoặc chưa hồi vì lý do X.]

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** [Thành viên integration điền khi ghép module.]
- **Nguyên nhân:** [Root cause.]
- **Cách xử lý:** [Thay đổi đã thực hiện.]
- **Cách xác minh:** [Lệnh và artifact.]

Ghi chú từ phần ingestion: môi trường chỉ cài deps tối thiểu (`requests`, `pandas`, `python-dotenv`) thay vì `uv sync` toàn bộ vì mạng yếu — full pipeline sẽ cần cài thêm embedding/LLM deps.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Chưa chạy end-to-end phase1/corruption | Chưa có metrics baseline/corrupted/repaired để kết luận impact | Hoàn thiện orchestration + chạy `script/run_phase1.py` / `run_corruption_flow.py` |
| Crossref sống, filter theo ngày chạy | Số record/query có thể lệch giữa các lần fetch | Pin snapshot raw đã lưu; chỉ refresh khi `REFRESH_SOURCE=true` |
| Nhiều paper thiếu `subject` → `categories` rỗng | `categories_joined` yếu cho câu hỏi theo topic | Bổ sung fallback category từ container/type hoặc mở rộng filter nguồn |
| [Thành viên khác bổ sung] | [ ] | [ ] |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác (phần đã biết).
- [ ] Phân công khớp với module, artifact và kết quả thực tế (còn thiếu TV2–TV4).
- [ ] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [ ] Baseline, corrupted và repaired dùng cùng evaluation set.
- [ ] Bảng metrics khớp với các file trong `data/results/`.
- [ ] Quality/freshness conclusions khớp với `data/quality/`.
- [ ] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
