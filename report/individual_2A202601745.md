# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đào Ngọc Bích           |
| MSSV               | 2A202601745                 |
| Khóa/Lớp         | K3                          |
| Tên nhóm         | A2                          |
| Vai trò chính    | Data model & Evaluation-set owner (Thành viên 2 trong nhóm 4 người) |
| Repository         | https://github.com/xuanloc49/K3_Day10_Data-Pipeline-Data-Observability (branch `2A202601745-DaoNgocBich`) |
| Ngày hoàn thành | 2026-08-06                  |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------- | --------------------- | ---------------- | ------------------ | ------------ |
| Cleaning & data modeling | `src/ingestion/cleaning.py::build_clean_dataframe` | `list[PaperRecord]` (từ `src/ingestion/crossref.py` — Thành viên 1) và `run_date` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` (DataFrame 16 cột, gồm `text_for_embedding`, `age_days`, `authors_joined`, `categories_joined`) | Hoàn thành |
| Frozen evaluation set | `src/evaluation/testset.py::build_test_set` | Cleaned DataFrame ở trên | `data/eval/test_set.json` (10 câu hỏi cố định, 4 loại: authors/date/categories/summary) | Hoàn thành |

Ghi chú quan trọng về ownership: Thành viên 1 (Source owner) đã chủ động code sẵn một bản `cleaning.py` trong cùng commit với `crossref.py` (ngoài phạm vi được giao). Tôi đã review lại toàn bộ logic, xác nhận đúng với nhóm là tôi tiếp nhận ownership file này, và đã sửa một lỗi dữ liệu quan trọng (mục 5) trước khi coi là hoàn thành.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ------------------------------ | -------- |
| Kiểm tra tích hợp thủ công giữa `test_set.json` và module retrieval có sẵn (`retrieval/index.py`, `retrieval/qa.py`) trước khi Thành viên 4 hoàn thành `phase1.py` | Thành viên 4 (Corruption & integration owner) | Xác nhận contract dữ liệu đúng: build thử ChromaDB từ `papers_clean.json`, cho agent trả lời 10 câu trong `test_set.json`, đạt `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`. Đây là kiểm tra thủ công, không phải artifact chính thức của pipeline (`phase1.py` chưa chạy được). |
| Hỗ trợ debug môi trường ban đầu của nhóm (Python 3.14 không tương thích `great-expectations`) | Toàn nhóm | Chuyển sang dùng `uv sync` để lấy đúng Python 3.11–3.13 theo `uv.lock`, không sửa `pyproject.toml`. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| ---------------------- | ----------------------------- | ------------------- | --------------- |
| Chuẩn hóa raw records thành bảng sạch: strip HTML/XML, gộp authors/categories, tính `age_days`, tạo `text_for_embedding` | `src/ingestion/cleaning.py` → `data/clean/papers_clean.csv`, `papers_clean.json` | 24/24 record giữ lại (không mất record nào so với raw), 0 duplicate `paper_id` | `python -c` gọi `build_clean_dataframe`, kiểm tra `df.shape`, `df['paper_id'].duplicated().sum()` |
| Sửa lỗi category rỗng bằng fallback tên journal | `src/ingestion/cleaning.py` (đoạn xử lý `categories`) | `categories_joined` non-null tăng từ 0/24 lên 15/24 | So sánh `df.isnull().sum()` trước/sau khi sửa |
| Sinh bộ câu hỏi eval cố định, 4 loại, ground truth trích trực tiếp từ dữ liệu sạch | `src/evaluation/testset.py` → `data/eval/test_set.json` | 10 câu hỏi đúng schema (`id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`) | Đọc `test_set.json`, kiểm tra `set(sample.keys())` khớp schema cho toàn bộ 10 mẫu |
| Kiểm tra tích hợp test set với retrieval module có sẵn | `retrieval/index.py`, `retrieval/qa.py` (không sửa code) | `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0` trên 10/10 câu | Script thủ công build Chroma index từ `papers_clean.json` rồi gọi `answer_question` cho từng câu trong `test_set.json` |

Output cụ thể đáng chú ý: `data/eval/test_set.json` — 10 câu hỏi, mỗi câu bọc tên bài báo trong dấu nháy đơn (`'...'`) để kích hoạt exact-match lookup theo title trong `retrieval/index.py::lookup`, giúp baseline trả lời gần như hoàn hảo và tạo "điểm gãy" rõ ràng khi Thành viên 4 chạy corruption (ví dụ title bị truncate).

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Dữ liệu thô từ Crossref (`PaperRecord`) chứa abstract dạng JATS XML (`<jats:p>...</jats:p>`), tên tác giả/category dạng list, và hoàn toàn thiếu field `subject` (category taxonomy). Phần của tôi phải biến dữ liệu này thành một bảng phẳng, sạch, có `text_for_embedding` dùng được cho bước embedding, đồng thời tạo ra một **bộ câu hỏi đánh giá cố định** để đo lường công bằng chất lượng agent qua 3 trạng thái baseline/corrupted/repaired.

### Cách triển khai

**`cleaning.py`:**
- Loại bản ghi không có `title`, hoặc `summary` sau khi strip tag còn dưới 100 ký tự (`MIN_SUMMARY_CHARS`).
- `strip_markup` dùng regex bỏ toàn bộ thẻ `<...>` rồi chuẩn hóa whitespace.
- Ngày xuất bản được parse theo 3 format (`YYYY-MM-DD`, `YYYY-MM`, `YYYY`) rồi fallback `datetime.fromisoformat`, tính `age_days = run_day - published_date`.
- Fallback category: nếu `categories` rỗng (100% trường hợp thực tế), dùng tên journal (`container-title`, đã có sẵn trong `record.comment` do Thành viên 1 parse) làm category proxy.
- Dedup theo `paper_id`, sort theo `published` giảm dần.

**`testset.py`:**
- Sinh tối thiểu 5, tối đa 10 câu hỏi, xoay vòng 4 `question_type`: `authors`, `date`, `categories`, `summary`.
- Mỗi câu hỏi được viết theo đúng cụm từ khóa mà `retrieval/qa.py::_extract_answer` dùng để trích câu trả lời (`"who authored"`, `"when was"`, `"what categories"`), và bọc title trong dấu nháy đơn để kích hoạt exact-match lookup thay vì chỉ semantic search.
- Nếu một loại câu hỏi không có dữ liệu hợp lệ cho một bài báo (ví dụ vẫn thiếu category dù đã fallback), hàm tự thử loại câu hỏi khác cho bài đó trước khi bỏ qua.
- Nếu tổng số mẫu hợp lệ dưới 5, hàm chủ động raise `ValueError` thay vì âm thầm ghi ra một file nhỏ hơn yêu cầu.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | `list[PaperRecord]` từ `ingestion/crossref.py` (Thành viên 1) + `run_date: datetime`; ở bước sau là cleaned `pandas.DataFrame` |
| Output | `data/clean/papers_clean.csv` + `.json` (16 cột); `data/eval/test_set.json` (list[dict], schema cố định) |
| Module phụ thuộc | `ingestion/crossref.py` (định nghĩa `PaperRecord`), `core/utils.py` (`normalize_whitespace`, `compact_join`, `first_sentence`, `write_json`) |
| Module sử dụng output | `retrieval/index.py` (đọc `papers_clean.json` để build embedding/ChromaDB), `evaluation/metrics.py` + `pipelines/phase1.py` (đọc `test_set.json` để evaluate — thuộc Thành viên 4) |
| Điều kiện lỗi cần xử lý | Record thiếu title/summary ngắn → drop khỏi cleaned dataset; category rỗng → fallback journal name; test set sinh được ít hơn 5 mẫu → raise lỗi rõ ràng |

### Cách xác minh

```bash
.venv/bin/python -c "
from core.config import load_settings
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from evaluation.testset import build_test_set
from core.utils import now_utc

settings = load_settings()
records = load_raw_records(settings.paths.raw_records_json)
df = build_clean_dataframe(records, now_utc())
df.to_csv(settings.paths.clean_csv, index=False)
samples = build_test_set(df, settings.paths.eval_testset)
print(len(records), df.shape, len(samples))
"
```

- **Kết quả mong đợi:** 24 raw records → 24 dòng cleaned, không mất record; sinh được ít nhất 5 câu hỏi test set hợp lệ schema.
- **Kết quả thực tế:** `24 records`, `df.shape = (24, 16)`, `10 test samples`. Sau đó build thử ChromaDB từ `papers_clean.json` và cho agent trả lời cả 10 câu trong `test_set.json`: `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`.
- **Artifact/log:** `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`, `data/eval/test_set.json` (không chứa secret).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Sau khi kiểm tra raw response thật từ Crossref, phát hiện **0/24 bài báo có field `subject`** (category taxonomy). Nếu giữ nguyên, `categories_joined` rỗng 100%, và loại câu hỏi `"categories"` trong `testset.py` không thể có ground truth có ý nghĩa.
- **Các phương án đã cân nhắc:**
  1. Bỏ hẳn loại câu hỏi `"categories"` khỏi bộ eval set, chỉ dùng 3 loại còn lại.
  2. Dùng tên journal (`container-title`, field `record.comment` đã có sẵn từ bước parse của Thành viên 1) làm category proxy khi `subject` rỗng.
- **Phương án đã chọn:** Phương án 2.
- **Lý do:** Giữ đủ 4 loại câu hỏi theo đúng thiết kế ban đầu (Guide.md yêu cầu: summary, authors, date, categories) thay vì cắt giảm phạm vi eval; tên journal là một proxy hợp lý cho "category" (lĩnh vực xuất bản) trong ngữ cảnh học thuật; không cần sửa lại schema hay logic đã thống nhất với các module khác (`quality.py`, `testset.py`), tránh phá vỡ contract dữ liệu chung của nhóm.
- **Bằng chứng quyết định phù hợp:** `categories_joined` non-null tăng từ 0/24 lên 15/24 sau khi sửa; câu hỏi `q3` (loại `categories`) trong `test_set.json` trả lời đúng 100% khi kiểm tra tích hợp với retrieval module.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ERROR: Could not find a version that satisfies the requirement great-expectations>=1.16.1` khi chạy `pip install -r requirements.txt`.
- **Lệnh hoặc bước tái hiện:** `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` trên máy có `python3 --version` = `3.14.6`.
- **Nguyên nhân gốc:** Python hệ thống mặc định là 3.14.6, nằm ngoài khoảng `>=3.11,<3.14` mà `pyproject.toml`/`uv.lock` yêu cầu — hầu hết bản `great-expectations` mới đều khai báo `Requires-Python <3.14`, nên pip không tìm được bản phù hợp.
- **Cách xử lý:** Cài `uv` qua Homebrew (`brew install uv`), xóa `.venv` cũ, chạy `uv sync` để tool tự lấy đúng phiên bản Python tương thích (3.13.14) và cài toàn bộ dependency theo `uv.lock` — không sửa `pyproject.toml` hay hạ cấp `great-expectations`.
- **Cách xác minh sau khi sửa:** `.venv/bin/python --version` → `Python 3.13.14`; import thử `pandas`, `chromadb`, `sentence_transformers` trong venv mới đều thành công.
- **Điều học được:** Với project đã cung cấp `uv.lock`, không nên tự `python3 -m venv` bằng Python hệ thống mặc định — cần kiểm tra `requires-python` trong `pyproject.toml` trước, và ưu tiên dùng đúng tool quản lý lockfile mà nhóm đã chọn.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. **Crossref → vector index:** Thành viên 1 gọi Crossref API, lưu raw response và raw records vào `data/raw/`. Tôi nhận `list[PaperRecord]` từ đó, strip markup, chuẩn hóa và tạo `text_for_embedding` cho mỗi bài, lưu vào `data/clean/`. Bước sau (đã có sẵn trong starter, không phải phần tôi code) dùng `sentence-transformers/all-MiniLM-L6-v2` để đổi `text_for_embedding` thành vector 384 chiều và nạp vào ChromaDB kèm metadata (`paper_id`, `title`, `published`, ...).
2. **Evaluation set & ground-truth doc IDs:** Tôi tạo 10 câu hỏi cố định từ dữ liệu sạch, mỗi câu gắn với `ground_truth_doc_ids` — chính là `paper_id` của bài chứa đáp án đúng. Khi evaluate, hệ thống so khớp `paper_id` mà agent thực sự truy xuất được với `ground_truth_doc_ids` này để tính `retrieval_hit_rate`, và so khớp câu trả lời với `ground_truth` để tính `token_f1`/điểm giám khảo LLM.
3. **Quality checks vs freshness monitoring:** Quality checks (thuộc Thành viên 3, `quality.py`) kiểm tra tính đúng đắn/đầy đủ của schema tại một thời điểm (null, duplicate, độ dài tóm tắt...) — trả lời câu hỏi "dữ liệu có sạch không". Freshness monitoring kiểm tra khía cạnh thời gian — dựa vào `age_days` mà tôi đã tính trong `cleaning.py`, trả lời câu hỏi "dữ liệu có còn mới không, hay đã lỗi thời (stale)".
4. **Vì sao dùng cùng test set cho cả 3 trạng thái:** Để đảm bảo biến duy nhất thay đổi giữa 3 lần đánh giá là **trạng thái dữ liệu** (sạch/hỏng/đã sửa), không phải do đề bài khác nhau. Nếu mỗi lần sinh lại câu hỏi mới từ dữ liệu hiện tại, sự khác biệt về điểm số có thể do đề dễ/khó khác nhau, làm mất khả năng so sánh nhân quả.
5. **Repair thành công dựa trên gì:** Dựa trên việc `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score` sau khi repair quay trở lại gần với giá trị baseline (không cần tuyệt đối bằng), kết hợp với quality/freshness report cho thấy các vấn đề đã inject (record thiếu, summary rỗng, title bị cắt, ngày cũ, duplicate) không còn xuất hiện trong dataset đã repair.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |     1.0* |    Chưa có |    Chưa có | *Đo bằng kiểm tra tích hợp thủ công của tôi (build index + chạy `answer_question`), không phải artifact chính thức từ `phase1.py` (Thành viên 4 chưa hoàn thành). Corrupted/Repaired chưa thể đo vì `corruption_flow.py` chưa chạy được. |
| `mean_token_f1`      |     1.0* |    Chưa có |    Chưa có | Tương tự trên. |
| `judge_accuracy`     |   Chưa có |    Chưa có |    Chưa có | Cần LLM judge trong `evaluation/metrics.py::evaluate_pipeline`, được gọi từ `phase1.py` — ngoài phạm vi kiểm tra thủ công của tôi. |
| `mean_judge_score`   |   Chưa có |    Chưa có |    Chưa có | Tương tự trên. |
| Quality checks         |   Chưa có |    Chưa có |    Chưa có | `observability/quality.py` vẫn còn `NotImplementedError` (Thành viên 3). |
| Freshness status       |   Chưa có |    Chưa có |    Chưa có | Tương tự trên; tuy nhiên `age_days` cần thiết đã có sẵn trong `papers_clean.json` do tôi tính, sẵn sàng cho Thành viên 3 dùng. |

### Kết luận từ số liệu

Tại thời điểm báo cáo này, tôi **chỉ có thể kết luận về phần việc của mình**, chưa thể hoàn thành 2 chuỗi nhân quả đầy đủ baseline → corrupted → repaired vì đó phụ thuộc vào `corruption.py`, `phase1.py`, `corruption_flow.py`, `quality.py`, `reporting.py` (Thành viên 3 và 4, chưa hoàn thành tại thời điểm này).

Kết luận có thể chứng minh ngay bằng artifact của riêng tôi: **dữ liệu sạch do tôi xử lý + bộ câu hỏi do tôi thiết kế → agent trả lời đúng 10/10 câu (hit rate và token F1 đều bằng 1.0)**. Đây là điều kiện cần để các bước so sánh sau này (corrupted/repaired) có ý nghĩa — nếu baseline không đạt gần như hoàn hảo, không thể phân biệt được sụt giảm chất lượng là do corruption hay do chính testset/cleaning có vấn đề từ đầu.

Kết quả khác với kỳ vọng ban đầu: tôi kỳ vọng `categories_joined` sẽ có dữ liệu ngay từ Crossref như các trường khác, nhưng thực tế 0/24 bài có `subject`. Tôi đã kiểm tra trực tiếp raw response (`data/raw/crossref_response.json`) để xác nhận đây là giới hạn thật của nguồn dữ liệu, không phải lỗi parse, trước khi quyết định fallback (mục 5).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Raw ingestion và cleaning không nên tách rời hoàn toàn — cần kiểm tra dữ liệu thô thật (không chỉ đọc pseudo-code) trước khi viết rule cleaning, vì nguồn dữ liệu thật (Crossref) có nhiều giới hạn không thấy trước được (thiếu category taxonomy).
2. **Về data quality/observability:** Một trường luôn rỗng (như `categories`) không tự động là lỗi code — cần xác minh ở tầng raw response trước khi kết luận, và quyết định fallback phải được ghi lại rõ ràng để các thành viên khác (đặc biệt Thành viên 3 làm quality checks) không hiểu nhầm đây là dữ liệu thiếu do lỗi.
3. **Về ảnh hưởng của data đến RAG agent:** Cách viết câu hỏi eval ảnh hưởng trực tiếp đến việc đo được impact của corruption hay không — nếu câu hỏi không gắn với cơ chế trả lời cụ thể của agent (ví dụ exact-match theo title), sẽ khó tạo ra "điểm gãy" rõ ràng khi dữ liệu bị làm hỏng.

### Nếu có thêm thời gian

Tôi sẽ thêm một bước kiểm tra tự động (không cần chờ Thành viên 4) để so sánh số lượng record có category thật (từ `subject`) và category fallback (từ journal name) ngay trong `data/clean/`, giúp Thành viên 3 phân biệt rõ hai loại category này khi viết quality checks, đo bằng: thêm cột boolean `category_is_fallback` vào cleaned dataset và kiểm tra tỷ lệ này trong quality report.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đào Ngọc Bích
**Ngày xác nhận:** 2026-08-06
