# Blueprint CI/CD cho RAG và guardrails

Nhóm: ViaLactea.

Người phụ trách: Đinh Đức Long — 2A202602633.

Đây là **đề xuất CI/CD**, chưa có workflow chạy trên GitHub hay request production
đi xuyên qua cả RAG và guardrails. Bằng chứng hiện có:

| Nguồn | Kết quả / model | Timestamp trong metadata |
|---|---|---|
| `artifacts/answers_50q.json` | 50 LLM answers, không extractive fallback; generation `gpt-6-luna` | Schema answers không có timestamp cấp batch |
| `artifacts/ragas_50q.json` | 50 câu, 20/20/10; evaluator `BAAI/bge-m3`, `gpt-6-luna` | 2026-10-12T10:43:46.433444+00:00 |
| `artifacts/judge_results.json` | 5 cặp/10 lượt, 10 binary judgments; judge `gpt-6-luna` | 2026-10-12T14:31:57.986705+00:00 |
| `artifacts/guard_results.json` | Attacks 20/20, clean 8/8, outputs 4/4; guard `gpt-6-luna` | 2026-10-12T16:16:24.742810+00:00 |

Metadata phiên bản 2 tách generation/evaluator/judge/guard. Guard đã đổi từ
`gpt-4o-mini` sang `gpt-6-luna` sau khi API trả 403 cho model cũ và danh sách
model khả dụng chỉ có `gpt-6-luna`; Đinh Đức Long xác nhận thay đổi này.
Temperature/lowest_temperature cấu hình 1.0; self-check có completion budget
1024. NeMo dùng chat client rõ ràng và adapter đổi token parameter cho model
này. JSON C xác nhận model thực nghiệm `gpt-6-luna`. Nguồn JSON giữ LF để
hashes ổn định qua checkout Windows.

C chạy trong Docker Linux: Python 3.11.17, NeMo 0.10.0, Annoy 1.17.3,
spaCy 3.8.16 / `en_core_web_lg` 3.8.0, Presidio 2.2.364.
Lượt đầu đạt attacks 20/20, clean 1/8, output 4/4 do NER tiếng Anh nhận nhầm
cụm chính sách tiếng Việt thành PERSON/US_DRIVER_LICENSE. Sau khi giới hạn
Presidio theo các loại Task 9a (VN_CCCD, VN_PHONE, PHONE_NUMBER, EMAIL_ADDRESS),
kiểm tra offline với engine thật đạt 8 clean negatives/4 PII positives; lượt
live sau đạt 20/20, 8/8, 4/4. NeMo vẫn kiểm tra yêu cầu dữ liệu cá nhân theo
ngữ cảnh. Fixtures và expected không thay đổi; bản JSON lượt đầu lưu trong
cache cục bộ `.venv-cache/guard_results_before_pii_fix.json`, không thuộc bài nộp.

Report A được tạo trước khi sửa adapter kiểm tra metric unavailable/partial.
Schema và phép tính khớp không tự chứng minh đủ 200 metric đã đo thành công.
Cần log m4 hoặc lượt A mới bằng adapter đã sửa trước khi dùng làm baseline
production. Các số trong JSON cũ được giữ nguyên.

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

| Bước | Hành vi đề xuất | Failure action |
|---|---|---|
| Presidio | Detect CCCD/CMND, VN phone/email; redact trước ghi log | Chặn PII theo policy lab; lỗi engine không cho request đi tiếp |
| NeMo input | Kiểm tra topic, jailbreak/injection, yêu cầu dữ liệu riêng; đọc activated rails | Rail chặn thì từ chối; timeout/API lỗi không chuyển input sang RAG |
| RAG | Hybrid BM25+dense, fusion, rerank; giữ nguồn/phiên bản context | Evidence không đủ thì abstain; không dùng ground truth thay answer |
| NeMo output | Kiểm tra answer có sẵn và question; giữ answer sạch | Thay/redact unsafe output; rail lỗi hoặc echo unsafe answer thì trả phản hồi an toàn |
| Evaluation offline | RAGAS/judge chạy batch để kiểm tra chất lượng | Thiếu dòng/metric/model metadata thì job fail; không gán điểm 0 giả |

Fail-closed cho lỗi guard là lựa chọn production đề xuất. Hàm guard hiện có
thể ném lỗi API; cần timeout/error handling tại lớp request tích hợp trước
khi nói đã có fallback production. Output fallback đã kiểm tra echo sau
chuẩn hóa khoảng trắng; lượt C live hiện có xác nhận output rail đạt 4/4 cases.
Kết quả này chỉ bao phủ bộ output fixtures của lab.

Audit log đề xuất: request ID, timestamp, phiên bản policy/model, layer,
allowed/blocked, lý do, latency và mã lỗi. Không ghi raw PII, answer nhạy cảm
hoặc secrets; redact trước ghi, giới hạn quyền và thời hạn lưu.
Key trong `.env`/biến môi trường hoặc secret store CI, không vào Git.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Lượt C cuối có 20 timed samples, 2 warm-up thật bị loại, scope
`input_layers_sequential`, percentile_method `linear`. Số dưới đây lấy từ JSON C.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 4.209 | 13.332 | 13.937 | Đã đo Task 12 |
| NeMo input | 1426.742 | 1839.690 | 2311.536 | Đã đo Task 12 |
| Input guard sequential | 1431.234 | 1845.655 | 2323.999 | Đã đo Task 12; vượt target |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer target: 500ms; `latency_budget_ok=false`. P95 1845.655ms vượt target
khoảng 3.69 lần. NeMo P95 1839.690ms so với Presidio 13.332ms cho thấy tầng
NeMo/API chiếm phần lớn thời gian; phép đo chưa tách network khỏi model inference.
Đề xuất lấy log API latency/tokens, thử model guard nhanh hơn khi project có
quyền truy cập, hoặc caching quyết định cho dữ liệu phù hợp rồi đo lại. Không
giảm/chỉnh số đã đo để làm gate đạt. Tổng percentile lấy từ tổng từng sample,
không cộng P95 riêng của hai tầng.

Đo RAG/output/full request tiếp theo bằng timestamp tại ranh giới từng tầng,
warm-up riêng và nhiều mẫu clean/blocked; phân biệt input sequential với request
dừng sớm. Số Task 12 hiện tại không chứng minh full guard P95.

## CI gates đề xuất

| Gate đề xuất | Điều kiện | Baseline hiện có |
|---|---|---|
| RAGAS | Đủ 50 câu/metric thật; mean faithfulness ≥0.75, mean avg_score ≥0.65 | JSON ghi 0.7908 / 0.7210; còn phải xác minh availability của lượt A cũ |
| Calibration | κ >0.6 trên đúng 10 supplied answers, không leak labels | 0.6154, sát ngưỡng; cần kiểm chứng độ ổn định |
| Input guard | Attacks ≥18/20; clean 8/8 allowed, FPR=0 | Đạt: 20/20, 8/8, FPR=0 |
| Output guard | 4/4 đúng; safe giữ nguyên, unsafe thay/redact | Đạt 4/4 |
| Input latency | Sequential P95 <500ms và raw samples hợp lệ | Không đạt target: 1845.655ms; samples hợp lệ |
| Full guard latency | P95 <500ms sau khi đo full guard thật | Chưa áp dụng, ngoài Task 12 |

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.
Job đề xuất: cài dependencies pin → `python -m pytest tests/ -q` offline →
`python scripts/check_lab.py` → job quality riêng đọc JSON và trả exit code 1
nếu bất kỳ ngưỡng ở bảng fail. Checker đã trả nonzero khi hợp đồng không đạt;
job quality và workflow chưa implement, biến `MIN_*` tự nó không tạo gate.
Không chạy live API trên mỗi commit. Latency 500ms là target, không thay rubric.

## Monitoring và cải tiến

| Theo dõi đề xuất | Trigger / cách lấy mẫu | Người xử lý |
|---|---|---|
| Retrieval/faithfulness | Batch định kỳ và khi corpus/model đổi; mean giảm >0.05 so với baseline đã xác minh | Phạm Đình Bảo Khôi rà chunks, nguồn/phiên bản, fusion/rerank |
| Judge drift | κ ≤0.6 hoặc tăng bất đồng trên bộ calibration cố định; human review cases biên | Nguyễn Thị Hải Mi rà prompt/model/labels |
| False positives | Clean-control fail hoặc phản ánh user đã xác nhận; xem cả allowed/blocked | Nguyễn Thị Lê Na rà recognizer/policy/rail, chạy lại controls |
| Latency/API | Input P95 >500ms hoặc tăng timeout/5xx; báo riêng từng tầng | Nguyễn Thị Lê Na kiểm tra runtime; Đinh Đức Long tổng hợp cảnh báo |
| Provenance/privacy | Hash stale, thiếu model roles, log có PII/secrets | Đinh Đức Long dừng đóng gói, rà nguồn và redaction |

Mean RAGAS đang lưu: 0.7210; weakest adversarial 0.6676 (factual 0.7726,
multi_hop 0.6962); context_recall toàn tập 0.5017. κ 0.6153846; position
inconsistency 0/5, longer-answer win rate 2/5 = 0.4. C live: attacks 20/20,
clean 8/8, FPR=0, outputs 4/4; đạt điều kiện chất lượng/bonus C, vượt target latency.

- Chặn evaluation unavailable/partial trước export, xác minh lại baseline A.
- M2 đã có BM25+dense: lưu candidates trước/sau fusion/rerank, thử ablation
  top-k và child→parent cho câu thiếu evidence.
- Giữ metadata nguồn/phiên bản đến generation; lọc policy hiện hành cho câu
  hỏi hiện tại, giữ lịch sử cho câu hỏi so sánh phiên bản.
- Dùng ID 12/46 để làm rõ ý thiết yếu trong prompt judge; thử chấm lặp và judge
  khác generator. Nhãn người chỉ dùng đối chiếu sau chấm.
- Mở rộng clean controls/cases khó sau lượt 20/8/4 đã đạt; giám sát false
  positives khi taxonomy/model/policy đổi, không sửa expected để tăng pass rate.
- Generator, judge và guard hiện cùng `gpt-6-luna`; thử model độc lập khi được
  cấp quyền để kiểm tra lỗi có thể lặp giữa các tầng và trade-off latency.

## Phần sửa lỗi và tích hợp của Đinh Đức Long

Đinh Đức Long (2A202602633) bổ sung các kiểm tra và chỉnh báo cáo khi tích hợp:

- Phase A: từ chối unavailable/partial, thiếu dòng/metric hoặc model metadata;
  không dùng điểm 0 thay kết quả chưa đo. Chỉnh báo cáo A về hybrid retrieval,
  nguồn chunk, các câu adversarial và giới hạn suy luận từ điểm số.
- Phase B: từ chối κ không xác định và nhãn bool; sửa nhận xét về answer dài
  hơn nhưng sai ở ID 5. Giữ nguyên nhãn/κ và số liệu bias của lượt B đã lưu.
- Nguồn dữ liệu: giữ JSON ở LF và đặt `.gitattributes` để hash khớp qua checkout
  Windows; không thay số đo hay metadata để vượt checker.
- Runtime C: tạo Docker guard, sửa chat/token compatibility cho model được
  project cho phép, giới hạn taxonomy PII theo Task 9a để xử lý false positives,
  chạy batch live và điền số đo latency thật.

Kiểm chứng cuối: 103 tests offline pass, 3 integration deselected; checker
0 failed checks. Chi tiết lỗi, files và bằng chứng cá nhân nằm trong mục
`DinhDucLong-2A202602633` của `doc/TEAM.md`. Phần này ghi đóng góp sửa/tích hợp,
không thay quyền tác giả triển khai ban đầu của Phạm Đình Bảo Khôi, Nguyễn Thị Hải Mi và Nguyễn Thị Lê Na.

Bộ 50/20/8/4 là phạm vi lab, chưa chứng minh an toàn/hiệu năng production.
Đinh Đức Long tích hợp và nêu giới hạn; trưởng nhóm Phạm Đình Bảo Khôi xác nhận bản nộp.
