# TÀI LIỆU BÀN GIAO CÔNG VIỆC: PHASE B (LLM-AS-JUDGE & BIAS)

**Dự án:** K4 Track 3A — ViaLactea  
**Người bàn giao:** Người 1 (Pipeline RAG & Đánh giá RAGAS)  
**Người tiếp nhận:** Người 2 (Phase B Specialist — LLM Judge & Bias)  
**Ngày bàn giao:** 12/10/2026  
**Trạng thái Phase A:** Đã hoàn thành 100% (`PASS` toàn bộ tests và contract checker).

---

## 1. Tổng quan & Trạng thái dữ liệu đã sẵn sàng

Phase A đã hoàn tất việc xây dựng RAG Pipeline, sinh câu trả lời cho toàn bộ 50 câu hỏi test set và đánh giá 4 metrics Ragas. Toàn bộ dữ liệu đầu vào cần thiết cho Người 2 đã được chuẩn bị đầy đủ và đồng bộ tại các đường dẫn sau:

1. **`artifacts/answers_50q.json` (Source A):** Chứa 50 câu trả lời của RAG pipeline sinh bởi mô hình `gpt-6-luna`, kèm đầy đủ contexts và metadata truy vết. File này đóng vai trò là **Ứng viên A** trong các lượt so sánh Pairwise.
2. **`fixtures/human_labels_10q.json` (Source B & Calibration):** Chứa 10 câu trả lời đối chứng từ mô hình baseline cùng nhãn người (0/1). 5 câu trong file này được dùng làm **Ứng viên B** cho Pairwise; toàn bộ 10 câu được dùng để cân chỉnh và tính Cohen's $\kappa$.
3. **`fixtures/test_set_50q.json` (Reference):** Chứa đáp án chuẩn (`ground_truth`) dùng làm căn cứ tham chiếu cho LLM Judge.
4. **Môi trường & Cấu hình:** Đã cấu hình `JUDGE_MODEL = "gpt-6-luna"` trong `config.py` và hỗ trợ API key OpenAI hiện tại. Helper `judge_binary()` trong `src/experiment_support.py` đã được kiểm thử và xử lý tương thích với reasoning model `gpt-6-luna` (`temperature=1.0`).

---

## 2. Chi tiết 5 Cặp Câu hỏi Đánh giá Pairwise (Task 5 & 6)

Theo quy định hợp đồng tại `src/report_contracts.py` (`PAIR_QUESTION_IDS = (1, 5, 12, 21, 41)`), Người 2 sẽ thực hiện đánh giá so sánh cặp đôi trên **đúng 5 câu hỏi** sau đây:

### 📌 Cặp 1: Câu hỏi ID 1 (Phân phối: `factual`)
* **Câu hỏi:** *Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?*
* **Reference (`ground_truth`):** `Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn, không trừ vào phép năm.`
* **Source A (Pipeline Phase A):**
  > `Nhân viên được nghỉ 3 ngày làm việc khi kết hôn.`
* **Source B (Baseline `human_labels_10q.json`):**
  > `Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn.`
* **Ghi chú đối chiếu:** Cả hai đều nêu chính xác số lượng 3 ngày làm việc; Source B đầy đủ hơn một chút khi có thêm cụm từ "có lương".

---

### 📌 Cặp 2: Câu hỏi ID 5 (Phân phối: `factual`)
* **Câu hỏi:** *Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?*
* **Reference (`ground_truth`):** `Đơn hàng trên 50.000.000 VNĐ cần Tổng Giám đốc (CEO) phê duyệt.`
* **Source A (Pipeline Phase A):**
  > `Không tìm thấy.`
* **Source B (Baseline `human_labels_10q.json`):**
  > `Cần Giám đốc phòng ban phê duyệt.`
* **Ghi chú đối chiếu:** 
  * Source B bị hallucination nghiêm trọng: 55 triệu vượt ngưỡng 50 triệu nên phải do CEO phê duyệt, trả lời Giám đốc phòng ban là sai quy chế tài chính.
  * Source A do thiếu chunk hạn mức trong context nên chọn giải pháp từ chối trả lời ("Không tìm thấy") để tránh bịa đặt.

---

### 📌 Cặp 3: Câu hỏi ID 12 (Phân phối: `factual`)
* **Câu hỏi:** *Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là bao nhiêu?*
* **Reference (`ground_truth`):** `Nhân viên chính thức có thời gian làm việc từ 6 tháng trở lên được thưởng Tết tối thiểu 1 tháng lương. Nhân viên dưới 6 tháng được hưởng pro-rata theo số tháng làm việc thực tế.`
* **Source A (Pipeline Phase A):**
  > `Tối thiểu **1 tháng lương**.`
* **Source B (Baseline `human_labels_10q.json`):**
  > `Nhân viên được thưởng Tết tối thiểu 1 tháng lương.`
* **Ghi chú đối chiếu:** Cả Source A và B đều trả lời chính xác và súc tích về mức tối thiểu 1 tháng lương.

---

### 📌 Cặp 4: Câu hỏi ID 21 (Phân phối: `multi_hop`)
* **Câu hỏi:** *Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?*
* **Reference (`ground_truth`):** `Theo chính sách v2024: 15 ngày cơ bản + 3 ngày thâm niên (9÷3=3) = 18 ngày phép. Lương Senior (P3-P4): 20-35 triệu VNĐ/tháng.`
* **Source A (Pipeline Phase A):**
  > `Nhân viên có 9 năm thâm niên được **18 ngày phép năm** (15 + 3). Khoảng lương: **Không tìm thấy.**`
* **Source B (Baseline `human_labels_10q.json`):**
  > `Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu.`
* **Ghi chú đối chiếu:** Source A tính đúng ngày phép nhưng thiếu vế thang bảng lương do hạn chế của multi-hop retrieval. Source B trả lời đầy đủ và chính xác cả 2 vế.

---

### 📌 Cặp 5: Câu hỏi ID 41 (Phân phối: `adversarial` — Bẫy xung đột phiên bản)
* **Câu hỏi:** *Nhân viên được nghỉ bao nhiêu ngày phép năm?*
* **Reference (`ground_truth`):** `Theo chính sách v2024 HIỆN HÀNH: 15 ngày cơ bản (+1 ngày/3 năm thâm niên). Chính sách v2023 (đã bị thay thế) là 12 ngày. RAG có thể retrieve cả 2 tài liệu — câu trả lời đúng phải ưu tiên v2024.`
* **Source A (Pipeline Phase A):**
  > `Mỗi nhân viên chính thức được hưởng **15 ngày phép năm có lương** theo chính sách 2024.`
* **Source B (Baseline `human_labels_10q.json`):**
  > `Nhân viên được nghỉ 12 ngày phép năm.`
* **Ghi chú đối chiếu (Điểm nhấn quan trọng):**
  * Source B sập bẫy dữ liệu cũ của chính sách v2023 đã hết hiệu lực (12 ngày).
  * **Source A của nhóm đã xuất sắc vượt qua bẫy**: Ưu tiên chính xác chính sách v2024 hiện hành (15 ngày). Khi viết prompt judge, LLM cần nhận ra ưu thế vượt trội này của Source A.

---

## 3. Bản đồ Nhiệm vụ cho Người 2 (`src/phase_b_judge.py`)

File code chính của bạn: **[src/phase_b_judge.py](file:///home/palm/Desktop/vin_ai20k/K4-Track-3A-Day24-ViaLactea-Eval-Guard/src/phase_b_judge.py)**. Cần hoàn thiện 4 tasks (Tasks 5 đến 8):

```
                     ┌────────────────────────────────────────┐
                     │          Người 2: Phase B              │
                     └──────────────────┬─────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
  [Task 5 & 6: Pairwise]      [Task 7: Cohen's κ]             [Task 8: Bias Report]
  - 5 cặp câu hỏi             - 10 binary judgments           - Đo Position Bias
  - Swap order (A/B vs B/A)   - So sánh với human_labels      - Đo Verbosity Bias
  - Consensus -> final_winner - Mục tiêu: κ > 0.6 (+3đ bonus) - Phân tích nguyên nhân
```

### 🔹 Task 5: `pairwise_judge()`
* **Mục tiêu:** Gọi LLM so sánh hai câu trả lời `answer_a` và `answer_b` dựa trên `reference`.
* **3 tiêu chí đánh giá:**
  1. *Độ chính xác (accuracy):* Có khớp với chính sách tham chiếu không?
  2. *Độ đầy đủ (completeness):* Có trả lời đủ các vế câu hỏi không?
  3. *Tính súc tích (conciseness):* Có thừa thãi hoặc lan man không?
* **Đầu ra bắt buộc:** Trả về dictionary dạng:
  ```json
  {
    "winner": "A", // hoặc "B", "tie"
    "reasoning": "Giải thích lý do lựa chọn...",
    "scores": {"A": 0.9, "B": 0.2}
  }
  ```
* **Lưu ý kỹ thuật:** Sử dụng `JUDGE_MODEL = "gpt-6-luna"`. Do mô hình này là reasoning model, bắt buộc dùng `temperature=1.0` (không dùng `temperature=0` để tránh lỗi HTTP 400).

---

### 🔹 Task 6: `swap_and_average()`
* **Mục tiêu:** Loại bỏ Position Bias bằng cách chạy 2 lượt:
  * **Pass 1:** `pairwise_judge(question, answer_a, answer_b, reference)` $\rightarrow$ `winner_pass1`
  * **Pass 2:** `pairwise_judge(question, answer_b, answer_a, reference)` $\rightarrow$ `pass2_raw` (đảo vị trí!)
* **Quy đổi kết quả Pass 2:** 
  * Ánh xạ ngược về không gian A/B ban đầu: Nếu `pass2_raw["winner"] == "A"` thì thực chất là `B`; nếu là `"B"` thì thực chất là `A`.
  * `scores_pass2`: Đảo lại điểm tương ứng: `{"A": pass2_raw["scores"]["B"], "B": pass2_raw["scores"]["A"]}`.
* **Xác định Final Winner:**
  * Nếu `winner_pass1 == winner_pass2` $\rightarrow$ `final_winner = winner_pass1` (Đồng thuận).
  * Nếu khác nhau $\rightarrow$ `final_winner = "tie"` (Bất đồng do bias vị trí).
  * `position_consistent`: `True` nếu cả 2 pass cùng chọn một đáp án, ngược lại `False`.

---

### 🔹 Task 7: `cohen_kappa()`
* **Mục tiêu:** Đo độ đồng thuận giữa nhãn dự đoán của LLM (`judge_labels`) và nhãn của con người (`human_labels`) trên 10 câu hỏi chuẩn.
* **Quy trình chạy:**
  * Runner trong `scripts/run_experiments.py` đã tích hợp sẵn việc gọi `judge_binary()` cho 10 câu trong `fixtures/human_labels_10q.json` để tạo ra list 10 nhãn 0/1.
  * Nhiệm vụ của bạn là cài đặt hàm `cohen_kappa(judge_labels, human_labels) -> float`.
  * Có thể dùng `sklearn.metrics.cohen_kappa_score` hoặc tính bằng công thức:
    $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
    Trong đó $p_o$ là tỷ lệ quan sát trùng khớp, $p_e$ là xác suất ngẫu nhiên.
* **Tiêu chí Bonus (+3đ):** Đạt $\kappa > 0.6$ (Mức độ đồng thuận đáng kể - Substantial agreement).

---

### 🔹 Task 8: `bias_report()`
* **Mục tiêu:** Đo lường 2 loại bias chính trong quá trình LLM đánh giá:
  1. **Position Bias:** Tỷ lệ các trường hợp đổi thứ tự làm đổi kết quả:
     $$\text{position\_bias\_rate} = \frac{\text{số case } position\_consistent == False}{\text{tổng số case judged}}$$
  2. **Verbosity Bias:** Xu hướng ưu tiên câu trả lời dài hơn dù nội dung tương đương:
     $$\text{verbosity\_bias} = \frac{\text{số case A thắng và A dài hơn} + \text{số case B thắng và B dài hơn}}{\text{tổng số case có kết quả rõ ràng (decisive)}}$$
* **Đầu ra:** Trả về dictionary theo đúng schema gồm `total_judged`, `position_bias_rate`, `position_bias_count`, `verbosity_bias`, `verbosity_details`, `interpretation`.

---

## 4. Các Bước Kiểm thử & Hoàn thiện Báo cáo

### Bước 1: Chạy Unit Test Mock (Offline)
Kiểm tra logic thuật toán mà không tốn chi phí gọi API:
```bash
.venv/bin/pytest tests/test_phase_b.py -q
```
*Yêu cầu: Pass 100% tất cả các test case.*

### Bước 2: Chạy Thực nghiệm Thật (`--live`)
Sau khi test offline pass, thực hiện chạy thí nghiệm live với OpenAI API:
```bash
.venv/bin/python scripts/run_experiments.py --phase b --live
```
*Kết quả:* Sinh file `artifacts/judge_results.json`.

### Bước 3: Kiểm tra Hợp đồng & Schema
Chạy kiểm tra tính hợp lệ của bài nộp:
```bash
.venv/bin/python scripts/check_lab.py
```
*Yêu cầu:* `PASS Phase B artifact`.

### Bước 4: Điền Báo cáo [doc/reports/bias_report.md](file:///home/palm/Desktop/vin_ai20k/K4-Track-3A-Day24-ViaLactea-Eval-Guard/doc/reports/bias_report.md)
* Điền thông tin cá nhân (Họ tên, MSSV).
* Điền bảng 5 cặp so sánh (id, candidate A/B, winner pass 1, winner pass 2, final winner, reasoning, scores).
* Điền bảng 10 câu Calibration và chỉ số Cohen's $\kappa$.
* Xóa sạch toàn bộ các placeholder `{{...}}`.

---

## 5. Checklist Tránh Mất Điểm (Rubric Warning)

> [!WARNING]
> 1. **Tuyệt đối không để sót `# TODO`:** Xóa sạch comment `# TODO` trong [src/phase_b_judge.py](file:///home/palm/Desktop/vin_ai20k/K4-Track-3A-Day24-ViaLactea-Eval-Guard/src/phase_b_judge.py) sau khi hoàn thiện (vi phạm bị trừ **5 điểm/module**).
> 2. **Không leak nhãn người vào prompt:** Tuyệt đối không gửi `human_label` hay `human_note` vào prompt đánh giá của LLM; việc so sánh với nhãn người chỉ được thực hiện sau khi LLM đã đưa ra kết quả độc lập.
> 3. **Độ ổn định của temperature:** Đảm bảo prompt pairwise chỉ định `temperature=1.0` để tương thích hoàn toàn với model `gpt-6-luna`.
> 4. **Giữ nguyên định dạng dữ liệu:** Không tự ý thay đổi nguồn A (phải là `artifacts/answers_50q.json`) hoặc nguồn B (`fixtures/human_labels_10q.json`).
