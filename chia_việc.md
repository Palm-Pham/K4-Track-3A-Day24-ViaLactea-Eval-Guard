# Kế hoạch phân chia công việc nhóm 4 người — K4 Track 3A

---

## 1. Phân tích tính độc lập & Khả năng làm việc song song (Parallelism Analysis)

Hệ thống được thiết kế theo kiến trúc module hóa rất cao, cho phép phân tách thành các luồng độc lập:

```
[Khởi động / Setup ban đầu]
  │
  ├──► [Người 3: Phase C (Guardrails)] ──► Hoàn toàn ĐỘC LẬP 100% ngay từ phút đầu!
  │                                        (Dùng fixtures có sẵn, không phụ thuộc RAG/answers)
  │
  ├──► [Người 2: Phase B (LLM Judge)]  ──► Viết code & Unit test ĐỘC LẬP ngay từ đầu!
  │                                        (Chỉ cần 5 answers khi chạy live batch)
  │
  ├──► [Người 1: Phase A (RAGAS Eval)] ──► Code Task 1, 3, 4 ĐỘC LẬP ngay từ đầu!
  │                                        (Task 2 & live batch cần setup answers)
  │
  └──► [Người 4: Blueprint & CI/CD]    ──► Soạn thảo kiến trúc, CI gates ĐỘC LẬP!
                                           (Điền số liệu đo khi có kết quả A, B, C)
```

- **Phần làm việc song song 100% ngay từ đầu (Zero Dependency):**
  1. **Phase C (Guardrails - Presidio + NeMo):** Chỉ sử dụng dữ liệu có sẵn trong `fixtures/` (`adversarial_set_20.json`, `clean_set_8.json`, `output_set_4.json`) và config trong thư mục `guardrails/`. **Không phụ thuộc vào pipeline RAG, không phụ thuộc vào 50 answers.** Thành viên phụ trách Phase C có thể code, chạy unit tests và chạy thực nghiệm `--live` ngay lập tức.
  2. **Code Logic & Unit Tests của Phase A và B:** Các hàm thuật toán (như `group_by_distribution`, `bottom_10`, `cluster_analysis` ở Phase A; `pairwise_judge`, `swap_and_average`, `cohen_kappa`, `bias_report` ở Phase B) đều có mock tests (`pytest tests/test_phase_a.py`, `pytest tests/test_phase_b.py`). Cả hai thành viên có thể code và pass toàn bộ unit tests độc lập mà không cần chờ dữ liệu thật.
  3. **Khung báo cáo Blueprint (Task 13):** Thành viên phụ trách CI/CD có thể bắt đầu phác thảo luồng dữ liệu, chính sách xử lý lỗi (failure action), và tiêu chí CI gates ngay.

- **Điểm đồng bộ duy nhất (Single Sync Point):**
  - Chạy thực nghiệm live cho **Phase A** (`run_experiments.py --phase a --live`) và **Phase B** (`run_experiments.py --phase b --live`) cần file [artifacts/answers_50q.json](artifacts/answers_50q.json). File này do **Người 1** sinh ra bằng lệnh `python scripts/setup_answers.py --live`.

---

## 2. Bảng phân công công việc chi tiết cho 4 người

| Thành viên | Vai trò chính | File code & Báo cáo phụ trách | Đầu vào (Input) | Kết quả đầu ra (Deliverables) |
|---|---|---|---|---|
| **Người 1** | **RAG Pipeline & Phase A (RAGAS Eval)** | - [src/phase_a_ragas.py](src/phase_a_ragas.py)<br>- [doc/reports/failure_clusters.md](doc/reports/failure_clusters.md) | - Module `m1`–`m5` từ Day 18<br>- Qdrant Docker | - `artifacts/answers_50q.json`<br>- `artifacts/ragas_50q.json`<br>- Báo cáo phân tích lỗi Phase A |
| **Người 2** | **Phase B Specialist (LLM Judge & Bias)** | - [src/phase_b_judge.py](src/phase_b_judge.py)<br>- [doc/reports/bias_report.md](doc/reports/bias_report.md) | - `fixtures/human_labels_10q.json`<br>- 5 answers (khi chạy live) | - `artifacts/judge_results.json`<br>- Báo cáo phân tích bias & Cohen's κ |
| **Người 3** | **Phase C Specialist (Guardrails & Latency)** | - [src/phase_c_guard.py](src/phase_c_guard.py) | - `fixtures/adversarial_set_20.json`<br>- `fixtures/clean_set_8.json`<br>- `guardrails/config.yml` | - `artifacts/guard_results.json`<br>- Kết quả đo P95 Latency 2 tầng |
| **Người 4** | **DevOps, Blueprint CI/CD & Integration Lead** | - [doc/reports/blueprint.md](doc/reports/blueprint.md)<br>- [doc/TEAM.md](doc/TEAM.md) | - Kết quả đo từ Người 1, 2, 3<br>- Schema checker | - Báo cáo `blueprint.md`<br>- File `TEAM.md` hoàn chỉnh<br>- Pass `scripts/check_lab.py` |

---

## 3. Chi tiết nhiệm vụ từng thành viên

### 👤 Người 1: Lead Pipeline RAG & Đánh giá RAGAS (Phase A — 30 điểm + 4 điểm bonus)
*Có thể bắt đầu: Ngay từ đầu.*

1. **Chuẩn bị hạ tầng & Dữ liệu (CP0):**
   - Đưa 5 module `m1_chunking.py`, `m2_search.py`, `m3_rerank.py`, `m4_eval.py`, `m5_enrichment.py` vào `src/`.
   - Chạy Qdrant: `docker compose -f infra/docker-compose.yml up -d`.
   - Chạy lệnh sinh câu trả lời trước lớp: `python scripts/setup_answers.py --live` để tạo ra `artifacts/answers_50q.json` (chia sẻ file này cho Người 2).
2. **Implement các Tasks trong [src/phase_a_ragas.py](src/phase_a_ragas.py):**
   - **Task 1:** `group_by_distribution()`: Phân nhóm 50 câu (20 factual, 20 multi_hop, 10 adversarial).
   - **Task 2:** `run_ragas_50q()`: Gọi `m4_eval.evaluate_ragas` tính 4 metric (faithfulness, answer_relevancy, context_precision, context_recall), trả về `RagasEvaluation`.
   - **Task 3:** `bottom_10()`: Lọc 10 câu có điểm `avg_score` thấp nhất, ánh xạ lỗi và đề xuất sửa theo `DIAGNOSTIC_TREE`.
   - **Task 4:** `cluster_analysis()`: Tính ma trận 4 metric × 3 distributions, xác định distribution có điểm trung bình thấp nhất.
3. **Kiểm thử & Báo cáo:**
   - Chạy unit tests: `pytest tests/test_phase_a.py`.
   - Chạy thực nghiệm thật: `python scripts/run_experiments.py --phase a --live` (tạo `artifacts/ragas_50q.json`).
   - Điền đầy đủ báo cáo [doc/reports/failure_clusters.md](doc/reports/failure_clusters.md).

---

### 👤 Người 2: Đánh giá LLM-as-Judge & Phân tích Thiên lệch (Phase B — 35 điểm + 3 điểm bonus)
*Có thể bắt đầu: Viết code và test ngay từ đầu; chỉ cần Người 1 gửi `answers_50q.json` khi chạy live.*

1. **Implement các Tasks trong [src/phase_b_judge.py](src/phase_b_judge.py):**
   - **Task 5:** `pairwise_judge()`: Viết prompt gọi LLM chấm điểm so sánh A vs B theo 3 tiêu chí (độ chính xác, đầy đủ, súc tích) dựa trên `reference`, trả JSON `winner` ("A"|"B"|"tie"), `reasoning`, `scores`.
   - **Task 6:** `swap_and_average()`: Chạy 2 lượt đảo vị trí (A/B và B/A) để khử position bias; quy đổi pass 2 về A/B ban đầu; chỉ đồng thuận nếu cả 2 lượt cùng chọn 1 đáp án.
   - **Task 7:** `cohen_kappa()`: Tính hệ số Cohen's κ giữa 10 nhãn của judge và 10 nhãn người từ `human_labels_10q.json` (dùng `sklearn.metrics.cohen_kappa_score` hoặc công thức tính tay).
   - **Task 8:** `bias_report()`: Tính tỷ lệ position bias và verbosity bias (thiên vị câu trả lời dài).
2. **Kiểm thử & Báo cáo:**
   - Chạy unit tests offline với mock: `pytest tests/test_phase_b.py`.
   - Chạy thực nghiệm live: `python scripts/run_experiments.py --phase b --live` (tạo `artifacts/judge_results.json`).
   - Điền đầy đủ báo cáo [doc/reports/bias_report.md](doc/reports/bias_report.md) (lưu ý mục tiêu bonus: Cohen's $\kappa > 0.6$).

---

### 👤 Người 3: Bộ lọc Bảo vệ Guardrails & Đo lường Độ trễ (Phase C — 35 điểm + 3 điểm bonus)
*Có thể bắt đầu: Song song 100% độc lập từ đầu đến cuối, không cần đợi bất kỳ ai.*

1. **Implement các Tasks trong [src/phase_c_guard.py](src/phase_c_guard.py):**
   - **Task 9a:** `pii_scan()`: Quét và che giấu PII (CCCD 12 số, CMND 9 số, SĐT Việt Nam, Email) bằng Presidio.
   - **Task 9b:** `check_input_rail()`: Tầng lọc đầu vào async với NeMo Guardrails (kiểm tra jailbreak, off-topic, prompt injection dựa vào `result.log.activated_rails`).
   - **Task 10:** `run_adversarial_suite()`: Chạy bộ 28 câu (20 attacks + 8 câu sạch) qua 2 lớp (Presidio -> NeMo input rail). Mục tiêu: $\ge 15/20$ attacks bị chặn (bonus $\ge 18/20$) và $8/8$ câu sạch được phép qua (`false_positive_rate = 0`).
   - **Task 11:** `check_output_rail()`: Tầng lọc đầu ra async với NeMo Guardrails (kiểm tra rò rỉ thông tin nhạy cảm).
   - **Task 12:** `measure_p95_latency()`: Đo tuần tự 2 tầng input (Presidio + NeMo), warm-up 2 lượt (loại bỏ khỏi mẫu), thu thập $\ge 20$ mẫu hợp lệ, tính phân vị P50, P95, P99 tuyến tính. Mục tiêu target: $P95 < 500\text{ms}$.
2. **Kiểm thử & Báo cáo:**
   - Chạy unit tests: `pytest tests/test_phase_c.py`.
   - Chạy thực nghiệm live: `python scripts/run_experiments.py --phase c --live --latency-samples 20` (tạo `artifacts/guard_results.json`).
   - Cung cấp số liệu P50, P95, P99 cho Người 4 để điền vào Blueprint.

---

### 👤 Người 4: DevOps, Blueprint CI/CD & Trưởng nhóm Tích hợp (Task 13 + Tổng kết)
*Có thể bắt đầu: Viết phần phân tích kiến trúc/CI gates ngay từ đầu, sau đó tích hợp số liệu.*

1. **Quản lý Repo & Điều phối:**
   - Khởi tạo GitHub repo nhóm, tạo branch làm việc cho các thành viên.
   - Đảm bảo **tất cả 4 thành viên đều có commit** trên repo (yêu cầu bắt buộc để được chấm điểm).
2. **Báo cáo Blueprint CI/CD ([doc/reports/blueprint.md](doc/reports/blueprint.md)):**
   - Mô tả kiến trúc luồng dữ liệu bảo vệ nhiều lớp: `Input -> Presidio -> NeMo input -> RAG -> NeMo output -> Response`.
   - Định nghĩa hành động khi gặp lỗi (failure action), lưu vết (audit log) và cơ chế fallback.
   - Nhận số liệu độ trễ từ Người 3 để điền bảng latency (P50, P95, P99), giải thích bottleneck nếu vượt ngưỡng 500ms.
   - Đề xuất các ngưỡng CI gates (RAGAS $\ge 0.65$, Attacks $\ge 18/20$, Clean $8/8$, Latency target).
   - Thiết kế kế hoạch monitoring, xử lý data drift và false positives trong production.
3. **Kiểm tra bài nộp toàn diện & Bàn giao:**
   - Hoàn thiện file [doc/TEAM.md](doc/TEAM.md): Nhắc nhở từng thành viên viết mục `INDIVIDUAL` (công việc đã làm, bài học rút ra, bằng chứng commit).
   - Chạy kiểm tra hợp đồng bài nộp: `python scripts/check_lab.py --with-tests` (đảm bảo không còn bất kỳ cảnh báo hoặc lỗi schema nào).
   - Kiểm tra không để lọt API key hay `.env` vào git: `git check-ignore artifacts/*.json`.
   - Nộp link repo và commit hash đúng hạn.

---

## 4. Lộ trình thực hiện trên lớp (Timeline 105 phút)

```
00' ── 15': [Kiểm tra sẵn sàng]
      • Người 1: Chạy docker Qdrant, hoàn tất setup_answers.py.
      • Người 4: Tạo repo, phân branch, kiểm tra môi trường cả 4 máy.

15' ── 45': [Code song song]
      • Người 3: Code xong Phase C (Tasks 9a–12) & chạy unit tests.
      • Người 2: Code xong Phase B (Tasks 5–8) & chạy unit tests.
      • Người 1: Code Tasks 1, 3, 4 Phase A & chạy unit tests.
      • Người 4: Viết khung kiến trúc trong blueprint.md.

45' ── 75': [Chạy thực nghiệm thật (Live Experiments)]
      • Người 1: Chạy Phase A live -> xuất ragas_50q.json -> viết failure_clusters.md.
      • Người 2: Nhận answers_50q.json -> chạy Phase B live -> xuất judge_results.json -> viết bias_report.md.
      • Người 3: Chạy Phase C live -> xuất guard_results.json -> bàn giao số liệu latency.

75' ── 105': [Tổng hợp & Nộp bài]
      • Người 4: Nhập số liệu vào blueprint.md, hoàn tất TEAM.md.
      • Chạy python scripts/check_lab.py --with-tests để xác nhận 100% hợp lệ.
      • Cả nhóm push commit, trưởng nhóm nộp link qua hệ thống.
```

---

## 5. Các lưu ý quan trọng để không bị mất điểm (Checklist Rubric)

> [!WARNING]
> - **Không còn `# TODO` trong code:** Mỗi file `src/phase_*.py` còn sót `# TODO` sẽ bị **trừ 5 điểm/module**.
> - **Không để fail Student Tests:** Mỗi test fail bị **trừ 3 điểm/test**. Hãy chạy `pytest tests/` trước khi nộp.
> - **Không giữ placeholder:** Không được để sót `{{...}}` trong các file `.md` tại `doc/reports/` và `doc/TEAM.md` (vi phạm bị **trừ 10 điểm**).
> - **Commit của từng người:** Trưởng nhóm nhắc nhở cả 4 thành viên commit từ tài khoản GitHub của chính mình để giảng viên đối chiếu chấm điểm cá nhân trong `doc/TEAM.md`.