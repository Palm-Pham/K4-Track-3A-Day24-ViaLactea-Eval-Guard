# Phân tích lỗi Phase A

Nhóm: ViaLactea

Người phụ trách: Phạm Đình Bảo Khôi (Pipeline RAG & Đánh giá RAGAS)

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T10:43:46.433444+00:00.
Generation mode/fallback và điều kiện chạy: Live generation mode sử dụng LLM `gpt-6-luna` với OpenAI API key (temperature=1.0 theo yêu cầu của reasoning model), Qdrant v1.9.7 vector DB chạy trên Docker (port 6333), embedding model `BAAI/bge-m3` cho cả indexing và evaluator metrics.
Models generation/evaluator: generation: ['gpt-6-luna'], evaluator: ['BAAI/bge-m3', 'gpt-6-luna'].

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.9333 | 0.6854 | 0.7167 |
| answer_relevancy | 0.8236 | 0.6411 | 0.8787 |
| context_precision | 0.7750 | 0.8792 | 0.8417 |
| context_recall | 0.5583 | 0.5792 | 0.2333 |
| avg_score | 0.7726 | 0.6962 | 0.6676 |

## Bottom 10 và nguyên nhân

| Rank | ID | Question | Distribution | Avg Score | Worst Metric | Diagnosis | Suggested Fix |
|---|---|---|---|---|---|---|---|
| 1 | 8 | Nhân viên được nghỉ bao nhiêu ngày khi cha hoặc mẹ mất? | factual | 0.0000 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 5 | Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt? | factual | 0.2500 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 3 | 42 | Thâm niên bao nhiêu năm thì được cộng thêm ngày phép? | adversarial | 0.3536 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 4 | 39 | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | multi_hop | 0.3750 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 5 | 41 | Nhân viên được nghỉ bao nhiêu ngày phép năm? | adversarial | 0.4146 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 6 | 33 | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | multi_hop | 0.4167 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 7 | 50 | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | adversarial | 0.5796 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 8 | 22 | Nếu cần mua một chiếc laptop 30 triệu cho nhân viên mới, ai phê duyệt và cần gì từ phòng CNTT? | multi_hop | 0.5833 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 9 | 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | multi_hop | 0.5833 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 10 | 7 | Nghỉ phép không lương 20 ngày cần ai phê duyệt? | factual | 0.5870 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |

### Đối chiếu answer, contexts và reference của các câu đại diện

1. **Câu 8 (ID 8 - factual) - Thiếu evidence và từ chối trả lời:**
   - *Question:* "Nhân viên được nghỉ bao nhiêu ngày khi cha hoặc mẹ mất?"
   - *Answer:* "Không tìm thấy."
   - *Reference (Ground Truth):* "Nhân viên được nghỉ 3 ngày làm việc có lương khi cha mẹ mất (tang lễ). Không trừ vào phép năm."
   - *Contexts thực tế:* Ba chunks nói về nghỉ trên 14 ngày, giấy tờ y tế và chế độ bảo hiểm nghỉ ốm; thiếu quy định nghỉ tang chế.
   - *Phân tích:* Setup hiện dùng `HybridSearch` kết hợp BM25 + dense qua reciprocal rank fusion, sau đó rerank lấy top 3. Evidence cuối không chứa đáp án cần thiết. Cần lưu candidates trước/sau fusion và rerank để xác định chunk bị bỏ ở bước nào, rồi thử mở rộng top-k hoặc cải thiện từ khóa/chunking. Câu "Không tìm thấy" được sinh ở chế độ LLM, không phải `extractive_fallback`. Bốn điểm trong JSON đều bằng 0; report hiện không lưu trạng thái từng metric từ evaluator nên chưa thể phân biệt điểm 0 đã đo với placeholder khi evaluator lỗi. Cần giữ log evaluation và chạy lại bằng adapter đã sửa trước khi khẳng định nguyên nhân của các điểm 0.

2. **Câu 5 (ID 5 - factual) - Lỗi thiếu chunk hạn mức phê duyệt:**
   - *Question:* "Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?"
   - *Answer:* "Không tìm thấy."
   - *Reference:* "Đơn hàng trên 50.000.000 VNĐ cần Tổng Giám đốc (CEO) phê duyệt."
   - *Contexts thực tế:* Chunk trả về chỉ chứa phần "Lưu ý đặc biệt: Mua sắm thiết bị CNTT cần xác nhận phòng CNTT..." mà không bao gồm bảng hạn mức tài chính (ngưỡng 50.000.000 VNĐ).
   - *Phân tích:* Context cuối thiếu bảng phân quyền tài chính. Chunking hoặc xếp hạng có thể đã tách/bỏ đoạn cần thiết, nhưng JSON không có candidates trung gian để xác định chính xác. Cần thử mở rộng context từ child sang parent hoặc tăng top-k reranking, rồi đối chiếu lại evidence về thẩm quyền CEO.

3. **Câu 42 (ID 42 - adversarial) - Bẫy xung đột phiên bản (Version Conflict Trap):**
   - *Question:* "Thâm niên bao nhiêu năm thì được cộng thêm ngày phép?"
   - *Answer:* "Từ 3 năm thâm niên trở lên, nhân viên được cộng thêm 1 ngày phép cho mỗi 3 năm làm việc liên tục."
   - *Reference:* "Theo v2024 (hiện hành): từ 3 năm thâm niên, cứ mỗi 3 năm thêm 1 ngày. Chính sách v2023 (đã hết hiệu lực) yêu cầu 5 năm. Câu trả lời đúng là theo v2024."
   - *Contexts thực tế:* Retriever trả về cả chunk v2023 ("từ 5 năm trở lên được cộng thêm 1 ngày phép...") và chunk v2024 ("từ 3 năm thâm niên...").
   - *Phân tích:* Answer chọn đúng quy tắc v2024 nhưng context chứa cả quy tắc 5 năm và 3 năm. JSON ghi faithfulness và context_recall bằng 0; chưa có log nhận định của evaluator để kết luận nguyên nhân hai điểm này. Cần kiểm tra tình trạng metric và xử lý version-aware retrieval: ưu tiên policy hiện hành khi hỏi chính sách hiện tại, vẫn giữ bản cũ khi câu hỏi yêu cầu so sánh lịch sử.

4. **Câu 39 (ID 39 - multi_hop) - Lỗi Multi-hop Retrieval:**
   - *Question:* "So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA."
   - *Answer:* "Không tìm thấy thông tin của policy v2.0, nên không thể so sánh đầy đủ. Policy v1.0 yêu cầu đổi mật khẩu mỗi 120 ngày và chấp nhận MFA bằng ứng dụng Authenticator (ưu tiên), SMS OTP hoặc YubiKey. Context không nêu độ dài tối thiểu."
   - *Reference:* "v1.0 (đã hết hiệu lực): tối thiểu 8 ký tự, đổi mỗi 90 ngày, không yêu cầu MFA. v2.0 (hiện hành): tối thiểu 12 ký tự, đổi mỗi 120 ngày, MFA bắt buộc cho tất cả: email, VPN và hệ thống nội bộ."
   - *Contexts thực tế:* Top 3 gồm header v1.0 đã bị thay thế, đoạn MFA/chu kỳ đổi mỗi 120 ngày và ghi chú chuyển sang v2.0. JSON chỉ lưu text, không có metadata nguồn; chưa đủ để quy cả 3 chunks về tài liệu v1.0. Các contexts thiếu bảng so sánh đầy đủ mà reference yêu cầu.
   - *Phân tích:* Answer gán chu kỳ 120 ngày và MFA cho v1.0, trái reference về v1.0 (90 ngày, không yêu cầu MFA). Có dấu hiệu trộn phiên bản giữa header và nội dung chunks. Cần giữ metadata nguồn/phiên bản đến bước generation và tách truy vấn cho từng policy khi câu hỏi yêu cầu so sánh.

5. **Câu 50 (ID 50 - adversarial) - Bẫy phủ định và ngụy biện chính sách (Policy Contradiction Trap):**
   - *Question:* "Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không?"
   - *Answer:* "Không. Không được sử dụng VPN cá nhân như NordVPN trong mạng công ty."
   - *Reference:* "KHÔNG. Chính sách VPN v1.3 cấm sử dụng VPN cá nhân (NordVPN, ExpressVPN) trong mạng công ty. Bắt buộc dùng VPN WireGuard của công ty. Đây là policy contradiction trap — câu hỏi nghe hợp lý nhưng vi phạm chính sách."
   - *Contexts thực tế:* Chunk chứa điều khoản "Không sử dụng VPN cá nhân (NordVPN, ExpressVPN) trong mạng công ty...".
   - *Phân tích:* Answer giữ đúng sự phủ định ("Không"), còn context cuối thiếu phần WireGuard bắt buộc trong reference. JSON ghi context_recall bằng 0; đây là dấu hiệu cần kiểm tra độ bao phủ evidence, chưa phải bằng chứng đầy đủ về cách evaluator đi đến điểm đó.

## Matrix và nhóm yếu nhất

| Metric | factual (20) | multi_hop (20) | adversarial (10) | Tổng câu có worst metric |
|---|---|---|---|---|
| faithfulness | 2 | 7 | 2 | 11 |
| context_recall | 9 | 5 | 8 | 22 |
| context_precision | 3 | 2 | 0 | 5 |
| answer_relevancy | 6 | 6 | 0 | 12 |

Nhóm yếu theo mean thấp nhất: adversarial; mean: 0.6676.
Worst metric xuất hiện nhiều nhất: context_recall; số câu: 22.

### Giải thích vì sao nhóm adversarial yếu nhất và đề xuất khắc phục

- **Nguyên nhân cốt lõi:**
  1. Nhóm `adversarial` có mean score thấp nhất (0.6676 so với 0.7726 của `factual` và 0.6962 của `multi_hop`), đặc biệt là `context_recall` rơi xuống mức báo động 0.2333 (8/10 câu adversarial có worst metric là context_recall).
  2. Bẫy adversarial được thiết kế có chủ đích bằng cách trộn lẫn các tài liệu hết hạn (v2023, v1.0) bên cạnh tài liệu hiện hành (v2024, v2.0), hoặc đặt các câu hỏi tiền giả định sai ("tăng bảo mật bằng VPN cá nhân"). Retriever không nhận biết được metadata về `effective_date` hay `status: superseded`, do đó trả về các chunk xung đột hoặc bỏ sót các điều kiện loại trừ cần thiết.
  3. `context_recall` là metric thấp nhất ở 22/50 câu. Đây là số câu theo `worst_metric`, không phải 22 failures. Các câu đại diện thiếu evidence gợi ý kiểm tra m2/m3 và top-3 context; cần ablation top-k/chunking để xác nhận bottleneck.

- **Đề xuất sửa đổi cụ thể:**
  1. *Metadata Filtering:* Bổ sung metadata filter trong Qdrant (`status: active` hoặc `effective_date`) để tự động loại bỏ các tài liệu v2023 cũ khi câu hỏi không yêu cầu truy vết lịch sử.
  2. *Điều chỉnh hybrid retrieval đang có:* Kiểm tra tokenization tiếng Việt, số candidates BM25/dense, fusion và rerank với các từ khóa "tang lễ", "cha mẹ", "55 triệu". So sánh candidates và điểm trước/sau từng bước; không coi việc thêm BM25 là thay đổi mới vì m2 đã có sẵn.
  3. *Query Rewriting / Decomposition:* Với các câu hỏi so sánh (multi-hop) hoặc bẫy logic (adversarial), áp dụng bước phân rã câu hỏi trước khi truy xuất.

- **Cách chạy lại để kiểm chứng hiệu quả:**
  1. Sửa validation evaluator trước, rồi thử điều chỉnh m2/m3 với metadata filtering và các cấu hình hybrid retrieval đang có.
  2. Chạy `python scripts/setup_answers.py --live` để sinh lại answers với context mới.
  3. Chạy `python scripts/run_experiments.py --phase a --live` để đo lại 4 metric trên 50 câu hỏi.
  4. Mục tiêu cải thiện đề xuất: `context_recall` của adversarial tăng từ 0.2333 lên trên 0.60, đồng thời các câu đại diện lấy đủ evidence và không giảm chất lượng factual. Không dùng riêng số câu có `worst_metric=context_recall` làm số failures.

## Bẫy adversarial và giới hạn

### So sánh điểm số và phân tích bẫy

- Điểm trung bình nhóm `adversarial` (0.6676) thấp hơn rõ rệt so với nhóm `factual` (0.7726). Sự chênh lệch này đạt điều kiện `adversarial_mean < factual_mean` cho tiêu chí bonus (+4đ).
- Phân tích chi tiết các dạng bẫy chính trong tập 10 câu adversarial:
  1. *Version Conflict (Xung đột phiên bản - Câu 41, 42):* Tập dữ liệu chứa cả quy chế nghỉ phép 2023 (12 ngày phép, 5 năm thâm niên +1 ngày) và quy chế 2024 (15 ngày phép, 3 năm thâm niên +1 ngày). Context ID 42 có cả hai quy tắc; các điểm thấp gợi ý cần kiểm tra xử lý phiên bản và log evaluator, không tự xác nhận quan hệ nhân quả.
  2. *Negation Traps & Policy Contradictions (Câu 46–48, 50):* ID 46 trả lời đúng việc nhân viên thử việc không có phép năm và phải xin nghỉ không lương có phê duyệt. ID 47 giữ đúng phủ định tự xử lý malware và nêu kênh/thời hạn báo cáo, nhưng không nhắc mức vi phạm nghiêm trọng. ID 48 phủ định đúng quyền PVI của nhân viên thử việc, còn thiếu ý BHXH bắt buộc trong reference. ID 50 bác bỏ VPN cá nhân nhưng chưa nêu WireGuard bắt buộc. ID 45 thuộc bẫy phiên bản MFA, không phải câu hỏi mua sắm; answer đã chọn đúng quy tắc MFA hiện hành.
- **Lưu ý về giới hạn nhận thức:** Điểm số adversarial thấp hơn chỉ phản ánh rằng phân phối câu hỏi bẫy gây khó khăn hơn cho hệ thống retrieval và generation; nó không tự chứng minh pipeline đã hoàn toàn có nhận thức phân biệt bẫy version conflict. Ở nhiều câu, pipeline chỉ may mắn trích xuất được chunk 2024 hoặc bị giảm điểm do retriever đưa về thông tin mâu thuẫn.

### Giới hạn thực nghiệm

1. *Số lượng mẫu:* Tập adversarial gồm 10 câu hỏi, dù đủ để phát hiện xu hướng nhưng dung lượng mẫu còn nhỏ để tổng quát hóa cho toàn bộ các kịch bản tấn công prompt injection hay logic poisoning phức tạp.
2. *Mô hình và nhiệt độ:* Code cấu hình `gpt-6-luna` với temperature 1 cho lượt chạy này. Chưa có thực nghiệm lặp để định lượng phương sai. Hash cố định nguồn đầu vào của report, không chứng minh tính tái lập hoặc rằng mọi metric đã đo thành công.
3. *Fallback:* Trong lượt chạy này, 100% câu hỏi đều được sinh thành công ở chế độ live LLM (`generation_mode: llm`, model: `gpt-6-luna`), không có câu nào phải kích hoạt `extractive_fallback`.
4. *Tình trạng evaluation:* Report này được tạo trước khi adapter A kiểm tra `status`/`missing_metrics`. Các điểm số/bottom/matrix được giữ nguyên để phản ánh JSON đã lưu; cần xác minh log m4 hoặc chạy lại Phase A với adapter mới để xác nhận đủ 200 metric thật. Không suy rằng mọi điểm 0 đều lỗi, cũng không coi chúng mặc nhiên là điểm đo hợp lệ.
