# Nhóm thực hiện K4 Track 3A

Tên nhóm: ViaLactea

Repo chung: https://github.com/Palm-Pham/K4-Track-3A-Day24-ViaLactea-Eval-Guard

Trưởng nhóm/người nộp: Phạm Đình Bảo Khôi — 2A202602434.

Ngày kiểm tra bản tích hợp: 12/10/2026, Asia/Ho_Chi_Minh (UTC+07:00).
Deadline mặc định 23:59 ngày lab; trưởng nhóm xác nhận ngày lab và điều chỉnh
theo thông báo coach trước khi nộp.

Commit dùng để chấm: chưa chốt. Bản sửa của Đinh Đức Long hiện chưa commit;
trưởng nhóm ghi SHA cuối sau khi commit/push và kiểm tra đúng bản trên GitHub.

Nhóm dùng một repo chung. Thông tin cá nhân dưới đây do Đinh Đức Long xác nhận;
bằng chứng công việc đối chiếu source, artifacts/reports và lịch sử Git.
Các mục tự đánh giá của Phạm Đình Bảo Khôi, Nguyễn Thị Hải Mi và Nguyễn Thị Lê Na cần chính thành viên xác nhận trước khi nộp.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Phạm Đình Bảo Khôi | 2A202602434 | Pipeline m1–m5, Tasks 1–4, chạy A và failure_clusters.md; trưởng nhóm | `653019b`, `b476c9f`; answers/ragas JSON và báo cáo A |
| 2 | Nguyễn Thị Hải Mi | 2A202602667 | Tasks 5–8, chạy B và bias_report.md | `074976d`; judge_results.json và báo cáo B |
| 3 | Nguyễn Thị Lê Na | 2A202602501 | Tasks 9a–12, guardrails, latency, sửa output echo và tests C | `0a316c9`, `664201a`, `0d06087`; phase_c_guard.py, test_phase_c.py |
| 4 | Đinh Đức Long | 2A202602633 | Task 13, tích hợp, sửa adapter A/κ B và báo cáo A/B; runtime/model compatibility C, false positives và chạy live C | `840668b`, `a2bff0b`; Blueprint, guard_results.json và tests hồi quy A/B/C |

Người tích hợp: Đinh Đức Long. Batch A: Phạm Đình Bảo Khôi. Batch B: Nguyễn Thị
Hải Mi. Batch C: Nguyễn Thị Lê Na; JSON cuối `guard_results.json` có timestamp
2026-10-12T16:16:24.742810+00:00 (23:16:24 ngày 12/10/2026, UTC+07).
Người nộp: trưởng nhóm: Phạm Đình Bảo Khôi.

## Môi trường và chuẩn bị trước lớp

Máy tích hợp: Windows; tests offline dùng Python 3.12.10. Tạo `.venv-guard`
bằng CPython 3.11.16, nhưng cài guard trên Windows thất bại vì thiếu MSVC để
build Annoy. Chuyển sang Docker Linux với `infra/Dockerfile.guard-live`:
Python 3.11.17, NeMo 0.10.0, Annoy 1.17.3, spaCy 3.8.16,
`en_core_web_lg` 3.8.0, Presidio analyzer/anonymizer 2.2.364.
Image build, `pip check` và imports guard thành công. Guard `gpt-6-luna`
được Đinh Đức Long xác nhận sau khi key/project không có quyền `gpt-4o-mini`.
NeMo 0.10 cần explicit chat client, temperature 1 và completion-token adapter
cho model này. C live cuối: attacks 20/20, clean 8/8 (FPR=0), outputs 4/4;
20 samples/2 warm-up, input sequential P95 1845.655ms, vượt target 500ms.
`python -m pytest tests/ -q` sau sửa A/B và runtime C: 103 passed, 3 integration deselected.
Tests không gọi API, không chứng minh full runtime.

Answers hiện có 50/50 `generation_mode=llm`, model `gpt-6-luna`, đủ 20/20/10.
Report A khai generation `gpt-6-luna`, evaluator `BAAI/bge-m3`/`gpt-6-luna`;
report B khai judge `gpt-6-luna`. Qdrant/model cache từ máy sinh answers không
được xác nhận trực tiếp trên máy tích hợp. Nguồn JSON giữ LF để hash đối chiếu đúng.
Key cấu hình riêng trong `.env`/biến môi trường, không nằm trong bản nộp.

## INDIVIDUAL

### PhamDinhBaoKhoi-2A202602434

- Công việc có bằng chứng: pipeline Day 18, Tasks 1–4, answers/RAGAS JSON,
  báo cáo lỗi A và điều phối repo; commits `b476c9f`, `653019b`.
- Kiểm tra: 6 tests A ban đầu pass; JSON đủ 50 câu, bottom 10 và matrix/means.
  Metadata/hash được kiểm tra trên máy tích hợp sau chuẩn hóa LF.
- Giới hạn: adapter cũ bỏ trạng thái metric lỗi; Đinh Đức Long đã bổ sung validation.
  Baseline A cũ cần log m4 hoặc lượt mới để xác minh đầy đủ metric thật.
- Tự đánh giá: thành viên cần xác nhận bài học về retrieval/generation,
  phần được AI hỗ trợ nếu có và cách tự kiểm chứng; Đinh Đức Long không viết thay
  trải nghiệm cá nhân của thành viên.

### NguyenThiHaiMi-2A202602667

- Công việc có bằng chứng: Tasks 5–8, JSON judge và bias_report; commit `074976d`.
- Kiểm tra: 8 tests B ban đầu pass; nguồn 5 cặp/10 binary answers khớp fixtures,
  κ=0.6153846, position inconsistency=0/5, verbosity win rate=2/5.
- Giới hạn: cỡ mẫu nhỏ, judge cùng model generator; κ sát ngưỡng bonus.
  Đinh Đức Long sửa nhánh κ không xác định và nhận xét sai về cặp ID 5 trong báo cáo.
- Tự đánh giá: thành viên cần xác nhận điều học được về swap/calibration,
  nguồn hoặc AI hỗ trợ và cách tự kiểm chứng.

### NguyenThiLeNa-2A202602501

- Công việc có bằng chứng: Tasks 9a–12, suite, output fallback chuẩn hóa
  khoảng trắng và regression test; commits `0a316c9`, `664201a`, `0d06087`.
- Kiểm tra: 13 tests C ban đầu pass, gồm latency; sau khi Đinh Đức Long bổ sung
  3 tests hồi quy runtime/PII, suite C hiện có 16 tests. Tests dùng engines/rails giả.
- Tích hợp live do Đinh Đức Long chạy: 20/20 attacks, clean 8/8, outputs 4/4,
  20 mẫu/2 warm-up; input P95 1845.655ms. Lượt đầu clean fail do English NER;
  Đinh Đức Long giới hạn loại PII theo Task 9a và sửa tương thích chat/token API.
- Giới hạn: model/runtime mới có phương sai; target 500ms chưa đạt, không dùng
  số input sequential làm full-guard latency.
- Tự đánh giá: thành viên cần xác nhận điều học được về Presidio/NeMo/async,
  nguồn hoặc AI hỗ trợ và cách tự kiểm chứng.

### DinhDucLong-2A202602633

- Phần phụ trách: Blueprint/Task 13, tích hợp và kiểm tra bản nộp. Sửa lỗi A
  (unavailable/partial, row count, metric/model validation) và nhánh κ B;
  chỉnh báo cáo A/B theo evidence, ổn định JSON source hashes qua LF. Tạo
  Docker runtime C, sửa chat/token compatibility và false positives Presidio
  theo phạm vi Task 9a, chạy C live và điền số đo thật vào Blueprint.
- Bằng chứng: code/tests A/B/C, `infra/Dockerfile.guard-live`,
  `guardrails/config.yml`, `artifacts/guard_results.json` và ba báo cáo trong
  working tree; commit `a2bff0b`.
- Cách kiểm tra: viết tests hồi quy trước sửa (11 tests A, 2 tests B fail đúng
  lỗi), bổ sung tests cho chat/token và NER false positives, sửa tối thiểu rồi
  chạy toàn bộ suite: 103 passed, 3 integration deselected. Kiểm tra Presidio
  thật offline 8 clean negatives/4 PII positives và đối chiếu JSON C live.
- Bài học từ kiểm chứng: mock tests pass chưa chứng minh live metric thật;
  điểm 0 có thể là placeholder, hash phụ thuộc byte/line endings; pairwise
  winner khác binary correctness; latency input không phải full request.
- Giới hạn: baseline A cũ vẫn cần xác minh availability; C đã đạt chất lượng
  nhưng vượt latency target. Không điền số đo thiếu hoặc coi đề xuất CI/CD
  là workflow đã chạy. Trưởng nhóm còn chốt SHA nộp; thành viên khác xác nhận
  phần tự đánh giá của mình.
- AI hỗ trợ: OpenAI Codex sửa code, thêm tests, rà artifacts và soạn báo cáo;
  đối chiếu bằng tests, schema/source hashes và dữ liệu JSON thực có.

#### Các lỗi A/B do Đinh Đức Long sửa khi tích hợp

| Phần việc | Lỗi đã xác định | Thay đổi của Đinh Đức Long | Bằng chứng kiểm tra |
|---|---|---|---|
| Code Phase A - Task 2 | Adapter bỏ trạng thái unavailable/partial, gán 0 cho metric thiếu và dùng zip khi số dòng không khớp | Từ chối evaluation chưa đo đầy đủ; kiểm tra số dòng, metric hữu hạn trong [0,1] và evaluator models; m4 không khai models cho kết quả unavailable | `src/phase_a_ragas.py`, `src/m4_eval.py`; 17 tests A pass, có 11 cases hồi quy fail trước sửa |
| Báo cáo A | Mô tả retrieval là dense thuần dù m2 đã có BM25; quy nguồn chunk và nguyên nhân điểm 0 khi chưa có evidence; nhầm ID 45 thành câu hỏi mua sắm | Chỉnh theo source/JSON: hybrid BM25+dense, phân biệt giả thuyết với nguyên nhân đã xác minh, dùng đúng các câu adversarial và nêu giới hạn metric availability | `doc/reports/failure_clusters.md`; đối chiếu m2, answers, RAGAS JSON và fixtures |
| Code Phase B - Task 7 | Trả κ=0 khi hai bộ nhãn đồng nhất khiến κ không xác định; chấp nhận bool như nhãn 0/1 | Báo lỗi cho κ không xác định, chỉ nhận integer 0/1; không thay nhãn hoặc κ của thực nghiệm đang lưu | `src/phase_b_judge.py`; 10 tests B pass, 2 cases hồi quy fail trước sửa |
| Báo cáo B | Nói không có answer dài hơn nhưng sai, trái với cặp ID 5 | Bổ sung ID 5 làm phản chứng, giữ giới hạn cỡ mẫu và phân biệt verbosity win rate với kết luận nguyên nhân bias | `doc/reports/bias_report.md`; đối chiếu `judge_results.json`, giữ κ=0.6153846 và verbosity win rate=0.4 |
| Provenance A/B | Source hashes lệch khi Git đổi JSON từ LF sang CRLF | Khôi phục LF và thêm `.gitattributes` cho JSON; không sửa điểm, nhãn, timestamp hay hash trong metadata để làm checker đạt | Checker xác nhận nguồn/hash và phép tính A/B; diff JSON không có thay đổi nội dung |

## Cập nhật sau khi nộp

Chưa xác nhận nhóm đã nộp bản nào. Trưởng nhóm chốt SHA và thời điểm nộp;
nếu có sửa sau deadline, ghi commit/thời điểm/lý do và thông báo coach cho phép
áp dụng bản cập nhật. Không khai working tree hiện tại là bản đã nộp.
