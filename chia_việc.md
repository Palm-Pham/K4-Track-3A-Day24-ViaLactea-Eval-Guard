# Kế hoạch phân chia công việc nhóm 4 người — K4 Track 3A

Kế hoạch triển khai theo [README.md](README.md), [doc/CHECKPOINTS.md](doc/CHECKPOINTS.md)
và [doc/RUBRIC.md](doc/RUBRIC.md). Starter chưa có m1–m5 hay kết quả trong
`artifacts/`; các hàm phase còn TODO và báo cáo/TEAM cần nhóm tự hoàn thiện.

---

## 1. Phụ thuộc và cách phối hợp

- Các thành viên có thể viết code và chạy mock tests theo phần được giao
  mà không cần chờ kết quả thực nghiệm của nhau.
- Phase A/B live cần file đủ 50 answers do Người 1 chuẩn bị trước lớp;
  runner B vẫn validate cả file dù chỉ chọn 5 câu để so sánh. Phase A cần
  evaluator m4; Phase C dùng fixtures, không phụ thuộc kết quả A/B.
- Các lượt chạy live cần môi trường, model và API key đã sẵn sàng.
- Người 1/2 bàn giao JSON kết quả và phân tích; Người 3 bàn giao các hàm guard
  và phân tích kết quả guard cho Người 4 tổng hợp Blueprint.
- Người 3 làm Tasks 9a–11; Người 4 làm Task 12 trong cùng `src/phase_c_guard.py`.
  Hai người thống nhất giao diện `pii_scan()`/`check_input_rail()` và chỉ sửa
  các hàm được giao. Người 4 có thể viết phép đo bằng mocks trước khi tích hợp.
  Sau khi đủ Tasks 9a–12, Người 4 chạy một batch C chung với Người 3 đối chiếu
  kết quả guard, tránh chạy live lặp.
- Mỗi người tự điền `INDIVIDUAL` và bằng chứng commit trong TEAM.

---

## 2. Bảng phân công công việc chi tiết cho 4 người

<!-- markdownlint-disable MD013 -->

| Thành viên | Vai trò chính | File code & Báo cáo phụ trách | Đầu vào (Input) | Kết quả đầu ra (Deliverables) |
| --- | --- | --- | --- | --- |
| **Người 1** | **RAG Pipeline & Phase A (RAGAS Eval)** | [src/phase_a_ragas.py](src/phase_a_ragas.py), [doc/reports/failure_clusters.md](doc/reports/failure_clusters.md) | Module `m1`–`m5` từ Day 18, Qdrant Docker | `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`, Báo cáo Phase A |
| **Người 2** | **Phase B Specialist (LLM Judge & Bias)** | [src/phase_b_judge.py](src/phase_b_judge.py), [doc/reports/bias_report.md](doc/reports/bias_report.md) | `fixtures/human_labels_10q.json`, `fixtures/test_set_50q.json`, file đủ 50 answers khi chạy live | `artifacts/judge_results.json`: 5 cặp A/B, 10 binary judgments, κ/bias; Báo cáo Phase B |
| **Người 3** | **Guardrails — Tasks 9a, 9b, 10, 11** | [src/phase_c_guard.py](src/phase_c_guard.py): các hàm guard và suite | `fixtures/adversarial_set_20.json`, `fixtures/clean_set_8.json`, `fixtures/output_set_4.json`, cấu hình trong `guardrails/` | Logic guard, tests và phân tích 20 attacks, 8 clean, 4 outputs trong batch C chung |
| **Người 4** | **Latency, Blueprint & Tích hợp — Tasks 12, 13** | [src/phase_c_guard.py](src/phase_c_guard.py): `measure_p95_latency()`, [doc/reports/blueprint.md](doc/reports/blueprint.md), [doc/TEAM.md](doc/TEAM.md) | Hàm guard từ Người 3, `fixtures/clean_set_8.json`, kết quả A/B và schema checker | `artifacts/guard_results.json` từ batch C chung, raw samples/P50/P95/P99, Blueprint, TEAM và kiểm tra bài nộp |

<!-- markdownlint-enable MD013 -->

---

## 3. Chi tiết nhiệm vụ từng thành viên

### 👤 Người 1: Pipeline RAG & Đánh giá RAGAS (Phase A: 30đ + 4đ bonus)

*Có thể bắt đầu: Ngay từ đầu.*

1. **Chuẩn bị hạ tầng & Dữ liệu trước lớp (CP0):**
   - Phối hợp Người 4 chuẩn bị Python 3.11, dependencies/compiler, model cache
     và API key theo [doc/ENVIRONMENT.md](doc/ENVIRONMENT.md).
   - Đưa 5 module từ Day 18: `m1_chunking.py`, `m2_search.py`, `m3_rerank.py`, `m4_eval.py`,
     `m5_enrichment.py` vào `src/`, đối chiếu [doc/PIPELINE_INTERFACE.md](doc/PIPELINE_INTERFACE.md).
     Setup tự lắp các module, không gọi `pipeline.py`.
   - Chạy Qdrant: `docker compose -f infra/docker-compose.yml up -d`.
   - Chạy lệnh sinh câu trả lời trước lớp: `python scripts/setup_answers.py
     --live` để tạo ra `artifacts/answers_50q.json` (chia sẻ file này cho Người
     2).

2. **Implement các Tasks trong [src/phase_a_ragas.py](src/phase_a_ragas.py):**
   - **Task 1:** `group_by_distribution()`: Phân nhóm 50 câu (20 factual, 20
     multi_hop, 10 adversarial).
   - **Task 2:** `run_ragas_50q()`: Gọi `m4_eval.evaluate_ragas` tính 4 metric
     (faithfulness, answer_relevancy, context_precision, context_recall), trả về
     `RagasEvaluation` gồm 50 `RagasResult` với 4 metric hữu hạn trong [0,1]
     và `evaluator_models` thực từ m4; không lấy model judge thay evaluator.
   - **Task 3:** `bottom_10()`: Lọc 10 câu có điểm `avg_score` thấp nhất, ánh xạ
     lỗi và đề xuất sửa theo `DIAGNOSTIC_TREE`.
   - **Task 4:** `cluster_analysis()`: Đếm `worst_metric` của mọi câu theo
     3 distributions thành ma trận 4 × 3. Tổng cột 20/20/10 chỉ là số câu,
     không phải điểm chất lượng. Tính mean `avg_score` riêng để xác định
     distribution yếu nhất, kèm metric chủ đạo và insight có nghĩa.

3. **Kiểm thử & Báo cáo:**
   - Chạy unit tests: `python -m pytest tests/test_phase_a.py -q`.
   - Chạy thực nghiệm thật: `python scripts/run_experiments.py --phase a
     --live` (tạo `artifacts/ragas_50q.json`).
   - Điền đầy đủ báo cáo
     [doc/reports/failure_clusters.md](doc/reports/failure_clusters.md).
   - Bonus +4: adversarial mean < factual mean, kèm phân tích bẫy; không hạ
     chất lượng answers hoặc sửa bộ test để đạt bonus.

---

### 👤 Người 2: LLM-as-Judge & Phân tích Bias (Phase B: 35đ + 3đ bonus)

*Có thể bắt đầu: Viết code và test ngay từ đầu; chỉ cần Người 1 gửi
`answers_50q.json` khi chạy live.*

1. **Implement các Tasks trong [src/phase_b_judge.py](src/phase_b_judge.py):**
   - **Task 5:** `pairwise_judge()`: Viết prompt gọi LLM chấm điểm so sánh A vs
     B theo 3 tiêu chí (độ chính xác, đầy đủ, súc tích) dựa trên `reference`,
     trả JSON `winner` ("A"|"B"|"tie"), `reasoning`, `scores`.
   - **Task 6:** `swap_and_average()`: Chạy 2 lượt đảo vị trí (A/B và B/A) để
     phát hiện và giảm position bias; quy đổi cả winner và scores pass 2 về
     A/B ban đầu. Hai lượt đồng thuận thì giữ winner (kể cả tie), khác nhau
     thì `final_winner = "tie"`; giữ cùng reference ở cả hai lượt.
   - **Task 7:** `cohen_kappa()`: Tính hệ số Cohen's κ giữa 10 nhãn binary 0/1
     của judge và 10 nhãn người từ `human_labels_10q.json` (dùng
     `sklearn.metrics.cohen_kappa_score` hoặc công thức tính tay).
   - **Task 8:** `bias_report()`: Tính tỷ lệ position bias và verbosity bias
     (thiên vị câu trả lời dài).

   **Hai quy trình judge phải tách rõ:**

   - Pairwise: 5 cặp ID **1, 5, 12, 21, 41**, mỗi cặp 2 lượt swap (10 calls).
     A từ `artifacts/answers_50q.json:answer`, B từ
     `fixtures/human_labels_10q.json:model_answer`, reference từ test set.
   - Calibration: 10 binary judgments trên đúng `question` và `model_answer`
     gốc của bộ nhãn người. Không dùng answer pipeline mới, không đổi
     A/B/tie thành 0/1 và không gửi `human_label`/`human_note` vào prompt.
     Runner và helper `src/experiment_support.py:judge_binary()` đã cung cấp
     quy trình này; Người 2 implement κ và kiểm tra ids/labels khớp nhau.

2. **Kiểm thử & Báo cáo:**
   - Chạy unit tests offline với mock: `python -m pytest tests/test_phase_b.py -q`.
   - Chạy thực nghiệm live: `python scripts/run_experiments.py --phase b
     --live` (tạo `artifacts/judge_results.json`).
   - Điền đầy đủ báo cáo [doc/reports/bias_report.md](doc/reports/bias_report.md)
     (lưu ý mục tiêu bonus: Cohen's κ > 0.6).

---

### 👤 Người 3: Guardrail Stack (Tasks 9a, 9b, 10, 11)

*Có thể code và test ngay; chạy live khi môi trường/model/API key đã sẵn sàng.
Không cần answers hoặc kết quả Phase A/B; bàn giao kết quả cho Người 4.*

1. **Implement các Tasks trong [src/phase_c_guard.py](src/phase_c_guard.py):**
   - **Task 9a:** `pii_scan()`: Quét và che giấu PII (CCCD 12 số, CMND 9 số, SĐT
     Việt Nam, Email) bằng Presidio.
   - **Task 9b:** `check_input_rail()`: Tầng lọc đầu vào async với NeMo
     Guardrails (kiểm tra jailbreak, off-topic, prompt injection dựa vào
     `result.log.activated_rails`).
   - **Task 10:** `run_adversarial_suite()`: Chạy bộ 28 câu (20 attacks + 8 câu
     sạch) qua 2 lớp (Presidio -> NeMo input rail). Bắt buộc ≥ 15/20 attacks
     bị chặn; bonus ≥ 18/20. Cả hai mốc đều cần 8/8 câu sạch allowed
     (`false_positive_rate = 0`). Không dùng `expected` để quyết định `actual`.
   - **Task 11:** `check_output_rail()`: Tầng lọc đầu ra async với NeMo
     Guardrails (kiểm tra rò rỉ thông tin nhạy cảm). Chạy đủ 4 cases trong
     `fixtures/output_set_4.json`: giữ nguyên output sạch, thay/redact output
     không an toàn; đọc quyết định từ activated rails.

2. **Kiểm thử & Bàn giao:**
   - Chạy unit tests: `python -m pytest tests/test_phase_c.py -q`.
     Tests latency có thể chưa pass khi Task 12 của Người 4 chưa hoàn thành.
   - Bàn giao các hàm guard đã kiểm tra cho Người 4 để tích hợp phép đo latency.
   - Đối chiếu 20 attacks, 8 clean và 4 outputs từ batch C chung; xử lý chặn
     nhầm/lọt tấn công và cung cấp phân tích cho Blueprint.

---

### 👤 Người 4: Đo Latency, Blueprint & Tích hợp bài nộp (Tasks 12, 13)

*Có thể viết Task 12 với mocks và khung Blueprint ngay; phép đo thật cần các
hàm guard của Người 3. Hỗ trợ môi trường chung và tích hợp kết quả A/B/C.*

1. **Quản lý Repo & Điều phối:**
   - Trước lớp: khởi tạo GitHub repo chung `K4-L3-DAY24-TenNhom-Eval-Guard`,
     phối hợp kiểm tra môi trường với các thành viên. Nhóm có thể dùng branch
     riêng để phối hợp; đây là lựa chọn tổ chức, không phải yêu cầu lab.
   - Đảm bảo **tất cả 4 thành viên đều có commit** trên repo (yêu cầu bắt buộc
     để được chấm điểm).

2. **Task 12 — Đo latency và chạy batch C chung:**
   - Implement `measure_p95_latency()` trong [src/phase_c_guard.py](src/phase_c_guard.py):
     đo tuần tự Presidio + NeMo input, warm-up thật 2 lượt bị loại khỏi mẫu,
     thu thập ≥ 20 mẫu hợp lệ và tính P50/P95/P99 tuyến tính.
   - Tái sử dụng engines, chạy trong một event loop; luôn đo đủ cả hai tầng
     dù Presidio chặn. Lưu raw samples theo từng tầng và tổng từng sample.
     Scope là `input_layers_sequential`, không phải RAG/output/full guard
     hoặc request dừng sớm. Target P95 < 500ms; vượt budget vẫn ghi số thật.
   - Tích hợp Tasks 9a–11 từ Người 3, chạy `python -m pytest tests/test_phase_c.py -q`.
   - Chạy một batch thật: `python scripts/run_experiments.py --phase c --live
     --latency-samples 20` để tạo `artifacts/guard_results.json` chứa cả guard
     và latency. Cùng Người 3 đối chiếu kết quả; chạy lại khi cần sửa lỗi.

3. **Task 13 — Blueprint CI/CD ([doc/reports/blueprint.md](doc/reports/blueprint.md)):**
   - Mô tả kiến trúc luồng dữ liệu bảo vệ nhiều lớp: `Input -> Presidio -> NeMo
     input -> RAG -> NeMo output -> Response`.
   - Định nghĩa hành động khi gặp lỗi (failure action), lưu vết (audit log) và cơ
     chế fallback.
   - Dùng số đo Task 12 để điền bảng latency (P50, P95, P99), giải thích
     bottleneck nếu vượt target 500ms; nhận phân tích guard từ Người 3.
   - Đề xuất CI gates theo mẫu Blueprint: RAGAS faithfulness ≥ 0.75,
     avg_score ≥ 0.65 trên 50 câu; attacks ≥ 18/20, clean 8/8 allowed và
     output cases đúng. Mốc lab bắt buộc vẫn là attacks ≥ 15/20.
   - Ghi rõ Blueprint là đề xuất, chưa mặc nhiên có workflow đã chạy; mô tả
     cách job trả nonzero khi gate không đạt. Full guard P95 < 500ms chỉ áp
     dụng sau khi đo full guard thật; RAG/output/full guard chưa đo được ghi
     “chưa đo” kèm kế hoạch, không suy từ `input_guard_ms`.
   - Thiết kế kế hoạch monitoring, xử lý data drift và false positives trong
     production.

4. **Kiểm tra bài nộp toàn diện & Bàn giao:**
   - Đối chiếu [doc/TEAM.md](doc/TEAM.md) với đóng góp và commit của từng người.
   - Chạy kiểm tra hợp đồng bài nộp: `python scripts/check_lab.py`
     (đối chiếu schema, nguồn/hash, model metadata, counts và phép tính).
     Dùng `--with-tests` nếu cần kiểm tra tổng hợp cả unit tests.
     Checker pass không thay bằng chứng chạy live hoặc điểm rubric.
   - Kiểm tra artifacts không bị ignore bằng lệnh với bốn đường dẫn cụ thể:

     ```bash
     git check-ignore artifacts/answers_50q.json artifacts/ragas_50q.json artifacts/judge_results.json artifacts/guard_results.json
     ```

     Không in đường dẫn, exit code 1 là bình thường: file không bị ignore.
     Lệnh này không quét secrets.
   - Kiểm tra riêng nội dung bốn JSON và diff sẽ commit để loại API key,
     dữ liệu cá nhân thật; kiểm tra `.env` không được track (ví dụ
     `git ls-files -- .env` phải không có output). Không nộp virtualenv/cache.
     Sau kiểm tra, commit/push đủ answers, ragas, judge và guard JSON cùng
     source, ba báo cáo và TEAM; đối chiếu đúng commit trên GitHub.
   - Nộp link repo và commit hash đúng hạn.

---

## 4. Lộ trình thực hiện trên lớp (Timeline 105 phút)

Hoàn tất chuẩn bị trước lớp theo nhiệm vụ CP0. Lịch dưới đây theo đề bài:
15 phút kiểm tra sẵn sàng và 30 phút cho mỗi phase. Thành viên phụ trách dẫn
phần tương ứng; các thành viên khác hỗ trợ hoặc làm phần được giao song song
khi lịch coach cho phép. Task 13 và tổng hợp nằm trong quỹ thời gian này.

```text
00' ── 15': [Kiểm tra sẵn sàng]
      • Cả nhóm: Xác nhận môi trường, Qdrant, module và đủ 50 answers.
      • Người 4: Xác nhận repo và phân công trong TEAM.

15' ── 45': [Phase A]
      • Người 1: Tasks 1–4 -> tests -> chạy A live -> failure_clusters.md.
      • Người 4: Viết khung Blueprint; chuẩn bị Task 12 với mocks nếu lịch cho phép.

45' ── 75': [Phase B]
      • Người 2: Tasks 5–8 -> tests -> chạy B live -> bias_report.md.
      • Người 4: Tổng hợp kết quả A/B vào Blueprint.

75' ── 105': [Phase C & Tổng hợp]
      • Người 3: Tasks 9a–11 -> tests guard -> bàn giao hàm, phân tích kết quả.
      • Người 4: Task 12 -> tests C -> chạy batch C chung -> Blueprint/TEAM/checker.
```

Mọi thành viên nộp cùng link repo theo README và hướng dẫn coach; trưởng nhóm
ghi commit nộp. Deadline mặc định 23:59 ngày lab (UTC+07).

---

## 5. Các lưu ý quan trọng để không bị mất điểm (Checklist Rubric)

Điểm Phase C (35đ + tối đa 3đ bonus) là điểm phần việc chung của Người 3/4;
việc chia Tasks 9a–12 không thay đổi rubric hay tự đặt tỷ lệ điểm cá nhân.

> [!WARNING]
>
> - **Không còn `# TODO` trong code:** Mỗi file `src/phase_*.py` còn sót `# TODO`
>   sẽ bị **trừ 5 điểm/module**.
> - **Student Tests:** Mỗi test fail bị **trừ 3 điểm/test**.
> - **Báo cáo:** Hoàn thiện TEAM và ba báo cáo; Blueprint trống, giữ placeholder
>   hoặc chỉ giữ mẫu bị **trừ 10 điểm**.
> - **Bằng chứng thật:** Unit/mock tests không thay thực nghiệm API. Thiếu
>   `artifacts/answers_50q.json` khiến Phase A 0 điểm. Giữ metadata phiên bản 2,
>   đúng source hashes và model IDs theo generation/evaluator/judge/guard.
>   Không chạy live integration thêm nếu batch B/C đã có để tránh trả phí lặp.
