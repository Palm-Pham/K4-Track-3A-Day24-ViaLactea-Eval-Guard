# Đánh giá LLM Judge Phase B

Nhóm: ViaLactea

Người phụ trách: Nguyễn Thị Hải Mi — 2A202602667

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T14:31:57.986705+00:00.
Models generation/judge: generation `gpt-6-luna`; judge `gpt-6-luna` (cả pairwise
`phase_b_judge.JUDGE_MODEL` và binary helper `experiment_support.JUDGE_MODEL`).

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

Mỗi cặp chạy 2 lượt với cùng reference: pass 1 thứ tự (A, B), pass 2 thứ tự (B, A).
`winner_pass2` và `scores_pass2` dưới đây đã quy về A/B gốc. Riêng text
`reasoning_pass2` trong JSON giữ nguyên nhãn của lượt đảo, nên "A" trong reasoning
pass 2 là answer B gốc và ngược lại; phần tóm tắt bên dưới đã quy về A/B gốc.

| id | Candidate A (pipeline) | Candidate B (model_answer) | len A / len B | winner_pass1 | winner_pass2 (A/B gốc) | final_winner | position_consistent | scores pass 1 (A, B) | scores pass 2 (A, B) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc khi kết hôn. | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 48 / 57 | B | B | B | true | 0.85, 0.95 | 0.65, 0.85 |
| 5 | Không tìm thấy. | Cần Giám đốc phòng ban phê duyệt. | 15 / 33 | A | A | A | true | 0.30, 0.10 | 0.30, 0.00 |
| 12 | Tối thiểu **1 tháng lương**. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 28 / 50 | A | A | A | true | 0.98, 0.82 | 0.98, 0.82 |
| 21 | 18 ngày phép năm (15 + 3); khoảng lương: Không tìm thấy. | 18 ngày phép (15 cơ bản + 3 thâm niên); lương Senior 20–35 triệu. | 98 / 82 | B | B | B | true | 0.55, 1.00 | 0.60, 1.00 |
| 41 | 15 ngày phép năm có lương theo chính sách 2024. | Nhân viên được nghỉ 12 ngày phép năm. | 87 / 37 | A | A | A | true | 0.85, 0.20 | 0.80, 0.10 |

Reasoning hai lượt (tóm tắt, đã quy về A/B gốc):

- **id 1** — Pass 1 và pass 2 đều chọn B vì nêu thêm "có lương" khớp reference; A
  đúng số ngày nhưng thiếu ý hưởng lương. Cả hai lượt ghi nhận A và B cùng thiếu
  ý "không trừ vào phép năm".
- **id 5** — A từ chối trả lời ("Không tìm thấy."), B nói "Giám đốc phòng ban" trái
  với reference (CEO). Cả hai lượt chọn A vì không khẳng định sai, nhưng cho điểm
  rất thấp cả hai (0.00–0.30): A thắng theo kiểu "ít tệ hơn", không phải A đúng.
- **id 12** — Cả hai cùng nêu đúng mức 1 tháng lương. Cả hai lượt chọn A với cùng
  lý do: B khẳng định chung cho "nhân viên", bỏ điều kiện từ 6 tháng trở lên. Pass
  2 lại ghi thêm rằng điều kiện đã nằm trong câu hỏi — lý do phạt B khá gượng; đây
  là cặp sát nút về nội dung.
- **id 21** — A đúng 18 ngày phép nhưng nói lương "Không tìm thấy"; B đúng cả 18
  ngày và khoảng lương 20–35 triệu. Cả hai lượt chọn B vì đủ ý thiết yếu.
- **id 41** — A nêu 15 ngày theo chính sách 2024 hiện hành; B nêu 12 ngày của v2023
  đã bị thay thế. Cả hai lượt chọn A; cả hai lượt cùng nhắc A thiếu mức cộng 1
  ngày/3 năm thâm niên và thêm chi tiết ("nhân viên chính thức", "có lương") mà
  reference không nêu.

Position bias count/rate: 0/5 = 0.0.
Verbosity win rate: 0.4 (2/5: a_wins_a_longer = 1, b_wins_b_longer = 1); decisive cases: 5.

Không cặp nào đổi winner khi đảo thứ tự, nên với 5 cặp này chưa quan sát thấy
position bias; swap-and-average không phải hạ cặp nào thành tie. Scores lệch giữa
hai lượt tối đa 0.20 (id 1, điểm A 0.85 → 0.65) nhưng không đổi thứ hạng.

Verbosity win rate 0.4 dưới ngưỡng cảnh báo 0.6. Ba trong năm cặp có answer ngắn
hơn thắng (id 5: 15 vs 33; id 12: 28 vs 50; id 21: 82 vs 98). Hai case answer dài hơn
thắng đều được giải thích bằng nội dung, không phải độ dài: id 1 B dài hơn vì chứa
đúng ý "có lương" của reference; id 41 A dài hơn và là answer duy nhất đúng phiên
bản chính sách. Đây là dấu hiệu thống kê trên 5 cặp, chưa đủ để kết luận judge
không có verbosity bias — bộ cặp không có case answer dài hơn nhưng sai.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| question_id | model_answer gốc | judge label | reasoning (tóm tắt) | human_label | agree |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Đúng 3 ngày làm việc có lương; ý không trừ phép năm không thiết yếu | 1 | yes |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | 55 triệu vượt ngưỡng 50 triệu, cần CEO phê duyệt | 0 | yes |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 0 | Bỏ điều kiện nhân viên chính thức từ 6 tháng trở lên, khẳng định quá rộng | 1 | no |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Đúng 18 ngày phép và lương Senior 20–35 triệu | 1 | yes |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Nghỉ sau 8 tháng chưa đủ cam kết 1 năm, hoàn trả 100% = 25 triệu | 1 | yes |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Thiếu Kế toán trưởng; không đưa đúng số phí 80.000 VNĐ | 0 | yes |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Đúng phụ cấp 1.500.000 VNĐ và 19 ngày phép cho Manager 12 năm thâm niên | 1 | yes |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | 12 ngày là chính sách v2023 đã thay thế; v2024 là 15 ngày | 0 | yes |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 0 | Đúng ý chính nhưng thiếu điều kiện trưởng phòng phê duyệt | 1 | no |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Reference cấm VPN cá nhân, bắt buộc dùng WireGuard của công ty | 0 | yes |

Cohen’s κ: 0.615 (0.6153846).
Observed/chance agreement và diễn giải: judge có 4 nhãn 1 / 6 nhãn 0, human có 6
nhãn 1 / 4 nhãn 0. p_o = 8/10 = 0.80; p_e = 0.4 × 0.6 + 0.6 × 0.4 = 0.48;
κ = (0.80 − 0.48) / (1 − 0.48) = 0.615 — mức "substantial" theo Landis-Koch, vượt
mục tiêu bonus κ > 0.6 nhưng chỉ sát ngưỡng.

Hai case lệch đều theo cùng một hướng: judge chấm 0 khi human chấm 1, tức judge
khắt khe hơn human về độ đầy đủ. Ở id 12 judge phạt vì answer không lặp lại điều
kiện "từ 6 tháng trở lên" — điều kiện đã nằm sẵn trong câu hỏi, nên human xem là
đúng. Ở id 46 judge đòi thêm chi tiết "trưởng phòng phê duyệt", trong khi human
note xem hành động thay thế (xin nghỉ không lương) là đủ. Không có case judge dễ
dãi hơn human: cả 4 answer human chấm 0 đều bị judge chấm 0 với lý do trùng
human_note (sai người phê duyệt, thiếu Kế toán trưởng và phí pro-rata, dùng chính
sách v2023, cho phép VPN cá nhân). Pairwise id 12 cũng phạt đúng answer B này với
cùng lý do, cho thấy đây là thiên hướng nhất quán của judge, không phải nhiễu đơn lẻ.

## Giới hạn và cách dùng judge

- **Model/prompt:** judge và generation cùng là `gpt-6-luna`, nên có rủi ro
  self-preference khi chấm answer của pipeline (A). Model này từ chối
  `temperature=0`; pairwise chạy với temperature mặc định (1) và `judge_binary`
  thử 0 rồi chuyển sang 1.0. Kết quả vì thế không tái lập hoàn toàn.
- **Độ dao động đã quan sát:** một lượt chạy trước của nhóm (trên bản answers cũ,
  đã bị thay khi pipeline sinh lại answers) cho cùng 10 câu calibration — input
  không đổi — đạt κ = 1.0, trong đó id 12 và id 46 được chấm 1. Hai lượt khác
  nhau đúng ở hai case biên, nên κ 0.615 lần này nên được hiểu là một điểm trong
  khoảng dao động, không phải giá trị cố định.
- **Cỡ mẫu nhỏ:** 5 cặp pairwise và 10 nhãn binary. Chỉ một nhãn lệch thêm sẽ
  kéo κ xuống dưới 0.6; position bias 0/5 cũng chỉ cho thấy judge ổn định trên bộ
  nhỏ này.
- **Pairwise là so sánh tương đối:** id 5 A thắng chỉ vì B sai nặng hơn; winner
  pairwise không được dùng như nhãn đúng/sai.
- **Cách kiểm chứng tiếp:** chạy lặp mỗi câu calibration nhiều lần và lấy nhãn đa
  số để đo độ ổn định; làm rõ trong prompt rằng điều kiện đã có trong câu hỏi
  không cần lặp lại; mở rộng bộ nhãn human với case biên; thử judge khác model
  generation; thêm cặp answer dài hơn nhưng sai để kiểm tra verbosity bias.
- Judge chỉ là công cụ hỗ trợ đánh giá, không phải đáp án tuyệt đối. Case biên
  hoặc khi judge mâu thuẫn với metric khác cần người xem lại.
