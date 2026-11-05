# TASK-002 — MODEL_MATRIX v0, RUNTIME matrix và Research Card (v2.3: vòng 2/2, đã sửa tay sau ba lượt review của Claude C)

Owner: Claude B (Research Architect, phiên Claude Web #2) · Reviewer: Claude C (Independent Reviewer) · Phiên bản v2.3 (v2 + sửa tay theo ba lượt review, xem mục 0b, 0c và 0d) · Ngày truy cập: nguồn mở mới hoặc mở lại trong v2 = **2026-10-26**; nguồn giữ nguyên từ v1 = 2026-10-25; nguồn do Claude C mở và báo lại = 2026-11-05 (S49–S52). Ghi ở Phụ lục E.

**Ký hiệu.** [P] = nguồn chính (trang/repo do chính nhà phát hành model hoặc runtime đăng); [P-m] = bản đăng lại nguyên văn của nguồn chính trên trang khác; [P-g] = repo/tệp do bên chuyển đổi hoặc lượng tử hóa đăng (unsloth, ggml-org): là nguồn chính cho chính file GGUF được đo (kích thước, danh sách file) nhưng không phải nhà phát hành model, nên license và thông tin model đọc ở đó chỉ là bản sao metadata của upstream (gián tiếp); [P-sn] = chỉ đọc trích đoạn kết quả tìm kiếm của trang chính, chưa mở trang; [T] = bên thứ ba. [S#] = mục trong Phụ lục E. Nhãn bằng chứng: REPORTED (đọc ở nguồn, kèm điều kiện) / ESTIMATE (tự tính từ số đã nêu) / ASSUMPTION / UNKNOWN. Tôi không dùng nhãn VERIFIED cho phần việc của mình. Chỗ nào chỉ dựa vào lời báo của Claude C ở review thì ghi "Claude C báo" và coi là chưa độc lập với bằng chứng của B; kèm liên kết trực tiếp khi có.

**Quy ước đơn vị (L4).** Kích thước file giữ nguyên **GB thập phân** như trang nguồn ghi (1 GB = 10^9 byte; ASSUMPTION về quy ước của Hugging Face, sai số đổi đơn vị ≤ 7%); RAM tính bằng **GiB** (1 GB = 0,9313 GiB). Mọi bảng ghi cả hai khi cần.

## 0. Tóm tắt thay đổi so với v1 và bảng đối chiếu finding

Phát hiện quan trọng nhất của v2 (đều ESTIMATE hoặc REPORTED, chưa đo trên laptop):

1. Qwen3.5-2B dùng 6/24 lớp full-attention nên KV = 12 KiB/token; đối chứng dense Qwen3-1.7B dùng 112 KiB/token (gấp 9,3 lần). Ở n_ctx = 8.192 chênh 0,78 GiB; ở 16K đối chứng dense đã vượt trần 3 GiB.
2. Hai "bẫy mặc định" làm vỡ trần RAM: ngữ cảnh mặc định 262.144 (KV 3,0 GiB, bằng cả trần) và số token ảnh tối đa mặc định của bộ xử lý ảnh Qwen3.5 là 16.384 token/ảnh. Cả hai phải đặt tường minh khi đo.
3. Công thức prefill của v1 dùng N = 2B (gồm embedding, không đi qua phép nhân) và bỏ qua bộ mã hóa ảnh. v2 tính lại: chữ rẻ hơn ≈ 31%, ảnh đắt hơn vì phải qua ViT 24 khối (Phụ lục D4).
4. Số liệu v1 lấy từ [T] có nhiều chỗ lệch so với repo gốc (Phụ lục F), trong đó Qwen3.5-4B Q4_K_M là 2,74 GB chứ không phải 2,6 GB.
5. Qwen3.5-2B không hơn Qwen3-1.7B ở mọi chỉ số: IFEval (non-thinking) 61,2 so với 68,2 theo bảng của chính Qwen (ở chế độ thinking thì ngược lại: 78,6 so với 72,5), nên đối chứng kiến trúc cũ có giá trị quyết định, không phải trang trí.

| Finding | Mức | Trạng thái v2 | Sửa ở | Cách đóng / còn lại |
| --- | --- | --- | --- | --- |
| C1 nguồn chính, license, dung lượng | Cao | Sửa phần lớn | A0–A5, E, F | Mở cây thư mục repo GGUF [P-g]: unsloth 2B/0,8B/4B và ggml-org E2B → đủ cột dung lượng; license đọc từ metadata + card của repo; S27 bị bác ở mức metadata. Còn: nội dung file LICENSE chưa mở (U7). |
| C2 tiếng Việt | Cao | Sửa một phần | A6, C1 | Không tìm được danh sách 201 ngôn ngữ của Qwen3.5. Có: "mở rộng từ 119 lên 201" [P-m] và Vietnamese nằm trong 119 ngôn ngữ của Qwen3 (bản chép [T]) → ASSUMPTION. Smoke test 24 câu đặt làm bước đầu của M2. Gemma 4: UNKNOWN. |
| T1 đối chứng kiến trúc cũ | Trung | Sửa (đối chứng); sàng lọc một phần | A0, A4, A5 | Thêm M4 Qwen3-1.7B (dense) và V2 Qwen3-VL-2B với dữ liệu [P]. Gemma 3 4B, SmolVLM2, InternVL3, Qwen2.5-VL-3B chưa sàng lọc (hết ngân sách) và xếp vào hàng chờ. |
| T2 runtime matrix | Trung | Sửa phần lớn | B | U9 đóng: OpenVINO ≥ 2026.2.0 có Qwen3.5 trên CPU/GPU, PyPI có 2026.4.1 với wheel cp314 Windows. License và dung lượng cài điền hết ô hoặc có kế hoạch đo. |
| T3 chi phí so với D4 | Trung | Sửa | C1–C3, D | Ghi độ dài đoạn; chi phí tính từ D4; cắt phạm vi ≤ ~90 phút/cấu hình. Phát hiện ràng buộc đĩa của file KL (U20). |
| T4 D4 chữ và ảnh | Trung | Sửa | D1, D4 | Tách chữ/ảnh; N không-embedding tính từ file BF16; ViT tính từ config; quy tắc token ảnh từ preprocessor_config. |
| T5 ngữ cảnh mặc định | Trung | Sửa | A1, C2 | KV@262K = 3,0 GiB; n_ctx bắt buộc đặt tường minh; trần token ảnh. |
| T6 VMLU | Trung | Sửa | C1, C3, U17 | Hạ thành "ứng viên chưa duyệt", thêm rủi ro rò rỉ dữ liệu và license, nêu phương án thay. |
| L1 C2 thiếu "cơ chế" | Thấp | Sửa | C2 | Đã thêm. |
| L2 STATUS không chuẩn | Thấp | Sửa | HANDOFF | STATUS = IMPLEMENTED (bộ trạng thái chuẩn của TASK-004). |
| L3 AC3 lạc quan | Thấp | Sửa | A, D2 | Quy tắc biên: VỪA ≤ 2,8 GiB; KV/S của M2 có phép tính; M3 có phép tính. |
| L4 GB/GiB | Thấp | Sửa | Quy ước, F | Giữ GB nguồn, quy đổi GiB tường minh. |
| L5 điều kiện điểm công bố | Thấp | Sửa | A7 | Chép đủ điều kiện lấy mẫu. |
| L6 ngày phát hành | Thấp | Sửa | A1 | Ghi khoảng ngày kèm nguồn. |
| L7 nguồn yếu | Thấp | Sửa | C2, E | S24 bỏ khỏi cơ sở nhận định; S17 và S21 chỉ còn là gợi ý. |

**Ô nên mở lại trước (gợi ý cho Claude C):** S34 (dung lượng 2B), S30 (config.json: lớp, head, ViT), S31 (preprocessor_config: quy tắc token ảnh), S37 (E2B: chỉ có Q4_0/Q8_0/BF16), S38/S40 (đối chứng), S42–S43 (OpenVINO), công thức D1 và bảng D4.

## 0b. Nhật ký sửa sau review v2 (v2.1, 2026-11-03; không có truy vấn web mới)

Claude C chấm bản v2 đạt có điều kiện (8,4/10) và nêu 8 vấn đề còn lại, trong đó 3 lỗi nhỏ sửa tay được. Bản này xử lý như sau. Nguồn và số liệu cũ giữ nguyên (không mở trang mới), nên đây không phải vòng 3. Dữ liệu nguồn chụp ngày 2026-10-26; đến ngày sửa có thể đã có bản phát hành mới (llama.cpp, OpenVINO, ONNX Runtime GenAI) và chưa được kiểm lại.

| Mục của review v2 | Xử lý trong v2.1 |
| --- | --- |
| TRUNG 1 tiếng Việt | Không đóng được nếu không có truy vấn mới. Thêm câu "chưa coi M1 đủ điều kiện CORE về ngôn ngữ cho tới khi smoke test chạy" ở A6 và RECOMMENDATION. Sửa ước tính thời gian smoke còn 5–10 phút/model (v2 ghi 15–20 phút là cao, lệch với tầng SMOKE ≤ 10 phút của TASK-003). |
| TRUNG 2 ngân sách tra cứu | Giữ nguyên lời khai: 33 lệnh web ở vòng 2; bản sửa tay không dùng thêm. |
| TRUNG 3 license chưa hoàn toàn từ nguồn chính | Nêu rõ trực tiếp và gián tiếp bằng nhãn [P-g]: M1, Qwen3-1.7B, Qwen3-VL-2B đọc ở trang Qwen; M2, M3, E2B chỉ qua metadata repo của bên chuyển đổi. U7 viết lại. Nội dung file LICENSE vẫn chưa mở. |
| TRUNG 4 research card khả thi | C3 viết lại: 60 câu + 20 ảnh, 2 lượt cho mọi mục, ≈ 60 phút. C1: cổng đĩa theo TASK-001 A5, tải tuần tự, N_KL phụ thuộc đĩa trống (2.048 token hiện tại; 16.384 khi đĩa ≥ 12 GiB), chi phí tính lại. Thêm bộ pilot tạm P-60 với công soạn (≈ 3 giờ người) và quan hệ với tầng LAPTOP của TASK-003. |
| TRUNG 5 dung lượng cài còn UNKNOWN | Sửa câu "không còn ô trống": nêu rõ ô nào còn UNKNOWN (Phụ lục B, HANDOFF). |
| THẤP 6 nhãn nguồn | Thêm nhãn [P-g] cho repo của bên chuyển đổi (S34–S37 và phần HF của S46); S42, S43, S45 đổi [P] thành [P-sn]. |
| THẤP 7 D5 sai dấu | Sửa: 0,76 − 0,2 − 0,4 − 0,11 = +0,05 GiB (−0,03 với 0,68). Kết luận không đổi. |
| THẤP 8 dẫn "Claude C đã kiểm" | Đổi thành "Claude C báo", kèm liên kết trực tiếp (S2, S3). Card Google 12B và E4B chỉ là trích đoạn tìm kiếm. |
| Khuyến nghị 2 | Bỏ truy vấn config Qwen3.5-4B khỏi danh sách còn lại (Claude C báo hidden 2560 và FFN 9216 qua bản sao config; B chưa tự mở). |
| Phát hiện khi rà lại | RISKS, RECOMMENDATION và C1 bổ sung cổng đĩa của TASK-001 (A5); D5 bổ sung ghi chú phiếu TASK-004 mô tả RAM khả dụng "thường < 1 GiB". |

## 0c. Nhật ký sửa sau review v2.1 (v2.2, 2026-11-05; không có truy vấn web mới)

Lượt review thứ hai (accept with conditions) nêu 7 điểm; điều kiện là sửa các điểm 1–4 trong văn bản, không cần nghiên cứu mới. Tôi đã tự tính lại các con số của reviewer bằng script (hệ số KL, độ lệch nhỏ nhất phát hiện của so sánh cặp, số hạng n², RAM của V2) và đều khớp nên áp dụng. Phần dựa vào nguồn bên thứ ba do reviewer báo (kích thước projector, bảng bộ nhớ Unsloth, nội dung LICENSE, mô tả multimodal.md, khuyến nghị độ dài đầu ra của card) ghi là "Claude C báo"; B chưa tự mở các nguồn đó.

| Điểm của review | Xử lý trong v2.2 |
| --- | --- |
| 1. AC6 mạnh hơn bằng chứng | AC6 thành có điều kiện: chỉ đúng nếu RAM khả dụng khi máy sạch ≥ 3 GiB (số đo duy nhất là 0,68–0,76 GiB). Sửa ở HANDOFF, A0, A5, D2. |
| 2. Chi phí KL thiếu | Thêm hệ số 1,37 (ma trận đầu ra tied 0,509B chạy ở mọi vị trí chấm): 6 mức ≈ 81 phút (N_KL = 2.048) và ≈ 179 phút (16.384), thay cho 77 và 149. Thêm bộ đệm logits fp32 ≈ 1 MB/vị trí (cửa sổ ≤ 256 token) và câu hỏi N_KL là token xử lý hay token được chấm (U20). |
| 3. MDES của so sánh cặp | Thêm công thức 2,8·√(d/n): với n = 60, ≈ 16 điểm (d = 0,2) và ≈ 20 điểm (d = 0,3); n = 100 cho ≈ 12 và ≈ 15. Mốc 10 điểm chỉ đạt khi d ≲ 0,08 (hai mức lượng tử của cùng model). Sửa P-60, H1b, rủi ro C1 và C3, KNOWN_LIMITATIONS. |
| 4. Hai khe hở của D4 | Thêm số hạng attention bậc hai (M4 +34%, M1 +7% ở 8K) và ghi η đồng nhất giữa các lớp là giả định (18/24 lớp của M1 là Gated DeltaNet); C2 đo η theo từng kiến trúc, chi phí C2 thành ≈ 58 phút. D3 dùng băng thông bền vững đo được khi có thay cho 19,2 GB/s lý thuyết. |
| 5. Projector của V2 | Q8_0 ≈ 445 MB (Claude C báo, [T]), F16 ≈ 0,8 GB: V2 @4K với Q8_0 ≈ 2,3–2,7 GiB (VỪA), @8K ≈ 2,7–3,1 (BIÊN); với F16 vẫn BIÊN. Sửa A0, A4, D2, U22; chất lượng OCR của projector Q8_0 chưa đo. |
| 6. Thinking mode | Thêm phạm vi: non-thinking với max_new_tokens ≤ 96; thinking ngoài phạm vi (≈ 36 phút/truy vấn ở trần 15 tok/s). Thêm hàng IFEval (thinking) vào A7 và sửa câu so sánh Qwen3.5-2B với Qwen3-1.7B. |
| 7. Điểm nhỏ | E2B: ngoài CORE theo trần file nhưng chưa loại về RAM thực, ưu tiên đo đầu tiên khi đĩa cho phép. U12: bảng Unsloth 3,5 / 7,5 / 9 GB, phần dư ≈ 2,2–5,5 GB nên chỉ là gợi ý thô. U5: multimodal.md là danh sách model ggml-org đã lượng tử sẵn nên không phải bằng chứng chống lại. U7: Claude C báo LICENSE của Qwen3.5-2B là Apache-2.0 chuẩn. C1: thêm quy tắc quyết định và tham chiếu BF16 (cần ≈ 4,3 GiB RAM). P-60: độ dài prompt ≈ 150 token là giả định, tính lại từ A6(iv). M3 (130 s/1.000 token) dựa trên config báo lại. Tên file đổi sang v2.2 để khỏi lẫn với vòng 3. |

## 0d. Nhật ký sửa sau review thứ ba (v2.3, 2026-11-05; không có truy vấn web mới)

Lượt review thứ ba kết luận accept (đủ điều kiện) kèm 3 sửa chữ nhỏ; không còn finding mức cao. Bản này chỉ sửa chữ và đưa vào các số mà Claude C đã mở ngày 2026-11-05 (B chưa mở các nguồn đó, nên ghi "Claude C mở").

| Điểm của review | Xử lý trong v2.3 |
| --- | --- |
| 1. C1 quá dài (≈ 1.200 từ so với ≈ 600 từ của C2 và C3) | Rút C1 còn ≈ 400 từ. Công thức chi phí, ràng buộc đĩa, RAM của lượt KL và quy tắc quyết định chuyển sang mục D6 (mới). |
| 2. Thiếu nhãn ESTIMATE cho vài trần tok/s | Thêm "(ESTIMATE)" ở A3 (IQ4_XS), đoạn "Phạm vi chế độ sinh", C3 (OCR cả trang), D2 (so sánh 4B với 2B) và H1a. |
| 3. Thay "B chưa tự mở" bằng số đã có | Config 4B (hidden 2560, FFN 9216, 32 lớp với 8 lớp full-attention, 16 Q-head, 4 KV-head, head_dim 256): κ = 32 KiB/token, KV@8K = 0,25 GiB, S ≈ 0,05 GiB, M3 Q4_K_M @8K ≈ 3,15–3,35 GiB (kết luận loại không đổi). License 0,8B và 4B đọc ở trang Qwen; LICENSE của Qwen3.5-2B là Apache-2.0 chuẩn; wheel openvino 2026.4.1 cp314 win_amd64 nặng 85,0 MB. Cập nhật A0, A1–A3, A5, B, D1, D2, D4, U3, U7, E1 (S49–S52). |
| 4. Quy trình | HANDOFF ghi Claude C kết luận accept và đề nghị Claude A ghi nhận phần vượt ngân sách (53 lệnh), chốt đóng băng, không mở vòng 3. |
| 5. Mục còn mở | Giữ nguyên nhãn: tiếng Việt của Qwen3.5, projector V2 (chỉ [T]), license E2B ở trang Google, README/LICENSE/releases của llama.cpp, MiniCPM5, dung lượng openvino-genai và ORT GenAI, hàng chờ A5. Claude C báo các bản Qwen3.6 thấy được chỉ có 35B-A3B và 27B (A5). |

## HANDOFF REPORT

**TASK_ID:** TASK-002

**OWNER:** Claude B — phiên Claude Web #2 (Research Architect)

**STATUS:** IMPLEMENTED. Đây là vòng cuối trong 2 vòng cho phép; chờ Claude C kiểm độc lập. Tôi không tự nâng lên VERIFIED. Phần còn hở nằm ở UNVERIFIED_CLAIMS (U1–U24). Bản v2.3 sửa tay theo ba lượt review (mục 0b, 0c và 0d), không có truy vấn web mới nên không phải vòng 3. Claude C đã kết luận accept (đủ điều kiện) và đề nghị Claude A chốt đóng băng; việc đóng chính thức do Claude A quyết định.

**BASELINE_REVISION:** N/A (chưa có baseline General, đúng đề bài). Dựa trên CONTEXT PACKAGE v1 (2026-10-24), bản v1 của tài liệu này (2026-10-25) và danh sách finding của Claude C. Không dùng SMOKE hay số liệu Toán cũ.

**FILES_READ:** Cục bộ: TASK_TICKETS_2026-10-24.md (phiếu TASK-002 và mẫu handoff), v1 dạng .md và .docx (cùng nội dung), văn bản review của Claude C về v1 và về v2. Web: các trang ở Phụ lục E mục S29–S48 (đọc 2026-10-26).

**FILES_CHANGED:** Tạo mới tài liệu này. Không có repo, không sửa file nào khác.

**WORK_COMPLETED:**

1. MODEL_MATRIX v0 (bản vòng 2): 4 LLM (M1 Qwen3.5-2B, M2 Qwen3.5-0.8B, M3 Qwen3.5-4B, M4 Qwen3-1.7B làm đối chứng kiến trúc cũ) và 2 VLM (V1 = M1 + mmproj, V2 Qwen3-VL-2B làm đối chứng). Gemma 4 E2B chuyển sang bảng sàng lọc A5 vì file vượt trần.
2. Bảng sàng lọc 8 ứng viên (A5) và bằng chứng tiếng Việt kèm giao thức smoke test (A6).
3. RUNTIME matrix 3 runtime + 3 phương án không chọn (Phụ lục B), mọi ô có giá trị kèm nhãn hoặc UNKNOWN kèm kế hoạch đo; dung lượng cài của llama.cpp, wheel openvino-genai và phụ thuộc ONNX Runtime vẫn UNKNOWN.
4. 3 research card, mỗi card đủ 7 trường, chi phí tính từ D4 và nằm trong ~90 phút/cấu hình (Phụ lục C), kèm bộ pilot tạm P-60 dùng chung.
5. Phân tích độ nhạy RAM 2/3/5 GiB, băng thông ×2, prefill chữ/ảnh (Phụ lục D).
6. Bảng đối chiếu finding (mục 0) và bảng hiệu chỉnh số liệu v1 → v2 (Phụ lục F).
7. Tự đánh giá AC:
   - AC1: đạt phần lớn; ô còn UNKNOWN đều có đường đóng cụ thể (U1–U24).
   - AC2: license đọc trực tiếp ở trang Qwen cho M1, M2, M3, M4, V2 [P] (M2 và M3 do Claude C mở 2026-11-05); gián tiếp chỉ còn E2B (metadata repo ggml-org [P-g]); file LICENSE của Qwen3.5-2B là Apache-2.0 chuẩn theo Claude C (U7).
   - AC3: công thức W + M + KV + S + A + R hiển thị, mọi ô có phép tính; quy tắc biên nêu rõ.
   - AC4: 3 runtime với trade-off ở Phụ lục B.
   - AC5: mọi số tốc độ gắn REPORTED hoặc ESTIMATE.
   - AC6 (có điều kiện): M1, M2 và M4 (n_ctx ≤ 8K) vừa 3 GiB theo công thức, chỉ khi RAM khả dụng khi máy sạch được xác nhận ≥ 3 GiB; số duy nhất đã đo là 0,68–0,76 GiB (D5, RISK 1), tại đó không phương án nào vừa mà không phân trang. M3 bị loại khỏi CORE theo trần file; E2B ngoài CORE theo trần file nhưng chưa loại về RAM thực (U13); V2 vừa @4K nếu dùng projector Q8_0 (U22), ở biên @8K. Lý do ghi ở A0–A5.

**EVIDENCE:**

- Qwen3.5-2B (config.json [P], S30): 24 lớp, bố cục 6×(3 Gated DeltaNet + 1 full attention) = 18 + 6; full attention 8 Q-head / 2 KV-head / head_dim 256; GDN 16 head K/V, head_dim 128; hidden 2048, FFN 6144, từ vựng 248.320 (tied), ngữ cảnh gốc 262.144; ViT 24 khối, hidden 1024, patch 16, gộp 2×2.
- Quy tắc token ảnh (preprocessor_config.json [P], S31): patch 16, gộp 2×2 → 1 token LLM cho mỗi vùng 32×32 pixel; kích thước cho phép từ 65.536 đến 16.777.216 pixel, tức 64 đến 16.384 token/ảnh (ESTIMATE từ cấu hình).
- Dung lượng GGUF đọc từ cây thư mục repo của bên chuyển đổi [P-g] (S34–S37). 2B: Q4_K_M 1,28 GB, UD-Q4_K_XL 1,34 GB, Q8_0 2,01 GB, BF16 3,78 GB, mmproj F16 668 MB. 0,8B: Q4_K_M 533 MB, mmproj F16 205 MB. 4B: Q4_K_M 2,74 GB, IQ4_XS 2,48 GB, mmproj F16 672 MB. Gemma 4 E2B (ggml-org): Q4_0 2,84 GB, Q8_0 4,97 GB, BF16 9,31 GB, không có Q4_K_M.
- License: trường "License: apache-2.0" trên trang repo Qwen3.5-2B (S29), Qwen3-1.7B-GGUF (S38) và Qwen3-VL-2B-Instruct-GGUF (S40) [P]; trang Qwen/Qwen3.5-0.8B và repo Qwen/Qwen3.5-4B do Claude C mở 2026-11-05 (S49, S50) [P]; gián tiếp ở 3 repo unsloth (S34–S36) và repo ggml-org E2B (S37) [P-g]. Repo Qwen3.5-2B có file LICENSE 11,5 kB.
- Đối chứng dense: Qwen3-1.7B có 28 lớp, 16 Q-head / 8 KV-head, 1,4B tham số không-embedding, ngữ cảnh 32.768 (S38); Q4_K_M 1,28 GB và Q8_0 2,17 GB ở ggml-org (S39, [P-sn]). Qwen3-VL-2B: Q4_K_M 1,11 GB, Q8_0 1,83 GB, F16 3,45 GB; OCR 32 ngôn ngữ (S40).
- OpenVINO: ghi chú phát hành 2026.2.0 thêm Gemma 4 E2B/E4B và "Qwen3.5" chỉ trên CPU và GPU (S42); PyPI có openvino 2026.4.1 với wheel cp314 win_amd64 và ghi rõ Apache-2.0 (S43). ORT GenAI: wheel cp314 win_amd64 của bản DirectML 0.14.0 nặng 4,1 MB (S45).
- Bảng điểm của Qwen cho Qwen3.5-2B/0,8B, Qwen3-1.7B, Qwen3-4B-2507 và cấu hình lấy mẫu kèm theo (S32); tổng hợp ở A7.
- Chưa có số đo nào trên laptop mục tiêu.

**TESTS_EXECUTED:** N/A (chỉ nghiên cứu tài liệu; không chạy model, không viết code dự án). Có dùng một đoạn tính nháp để kiểm lại phép tính số học (đổi đơn vị, KV, FLOP); không phải sản phẩm.

**TEST_RESULTS:** N/A.

**BENCHMARK_RESULTS:** N/A, không đo gì. Điểm công bố là REPORTED (A7, kèm điều kiện); tốc độ và RAM là ESTIMATE (A, D).

**COST_OR_RESOURCE_USAGE:** $0. Vòng này dùng **33 lệnh gọi web** (18 web_search + 15 web_fetch; trong đó 3 fetch bị từ chối vì URL chưa nằm trong kết quả và 2 search không có ích) và 1 phiên chat. Vượt ngân sách "~20 truy vấn" khoảng 65%. Lý do: review yêu cầu mở nguồn chính cho từng repo (C1, C2, T1, T2) và mỗi repo cần ít nhất một lệnh; vòng này là vòng cuối nên tôi chọn đóng finding cao trước. Cần Claude A ghi nhận phần vượt. Tổng cả hai vòng: 53 lệnh. Các bản sửa tay v2.1, v2.2 và v2.3 không dùng thêm lệnh web. Không tải model, không gọi API trả phí.

**KNOWN_LIMITATIONS:**

- Không có số đo nào trên laptop mục tiêu; mọi thứ về "chạy được" mới là tuyên bố từ tài liệu.
- Không mở được trang GitHub của llama.cpp (README, LICENSE, releases) vì công cụ chỉ cho mở URL đã xuất hiện trong kết quả; license và cách cài llama.cpp dựa trên [T] và trích đoạn HF tự sinh.
- Tôi chưa tự mở nội dung file LICENSE của Qwen, trang license Gemma 4, config của Qwen3.5-4B và Gemma 4 E2B. LICENSE của Qwen3.5-2B, license 0,8B và 4B, config 4B do Claude C mở 2026-11-05 (S49–S52); config E2B chưa ai mở.
- Chưa sàng lọc Gemma 3 4B, SmolVLM2-2.2B, InternVL3-2B, Qwen2.5-VL-3B, Qwen3-4B-2507 (chỉ có điểm từ bảng Qwen), Qwen3-VL-4B.
- Không tìm được danh sách 201 ngôn ngữ của Qwen3.5 nên tiếng Việt vẫn là ASSUMPTION.
- Bộ pilot P-60 chỉ phát hiện được chênh ≈ 16–20 điểm giữa hai model khác nhau (so sánh cặp, d = 0,2–0,3) và ≈ 10 điểm giữa hai mức lượng tử của cùng một model (d ≲ 0,08). η đồng nhất giữa các lớp là giả định, và mọi số tốc độ/RAM là ESTIMATE.

**RISKS:**

1. RAM khả dụng đo được 0,68–0,76 GiB (điều kiện tải chưa rõ), thấp hơn cả kịch bản 2 GiB. Nếu là trạng thái thường trực (phiếu TASK-004 mô tả RAM khả dụng "thường < 1 GiB"), mọi kết luận về cỡ model đổi (D5). TASK-001 phải chốt trước.
2. Đĩa trống 4,01 GiB và đang giảm; phiếu TASK-001 (A5) yêu cầu ≥ 12 GiB hoặc ổ ngoài và ghi rằng với ~4 GiB thì chưa thể tải model 1–2 GB mỗi cái. Qwen3.5-2B Q8_0 (2,01 GB) cộng một file Q4 (1,28 GB) đã ≈ 3,3 GB; các phép đo tải tuần tự, không giữ hai file lượng tử cùng lúc.
3. Kiến trúc Gated DeltaNet còn mới: hỗ trợ llama.cpp mới có REPORTED (metadata qwen35 trên HF), chưa chạy thử trên máy này.
4. Prefill bị giới hạn tính toán: 1.000 token chữ ≈ 50 s với M1 ở G = 100 GFLOPS; một ảnh 768×768 ≈ 64 s; một trang A4 150 dpi ≈ 5,6 phút (ESTIMATE, D4). VLM trên CORE chỉ hợp xử lý theo lô. η của lớp Gated DeltaNet (18/24 lớp của M1) có thể thấp hơn GEMM nên prefill M1/M2 có thể chậm hơn con số này (D1, C2).
5. Bẫy mặc định: ngữ cảnh 262.144 (KV 3,0 GiB) và trần 16.384 token/ảnh; đỉnh RAM của bộ mã hóa ảnh ở độ phân giải cao chưa biết (U24).
6. Tiếng Việt chưa có bằng chứng theo từng ngôn ngữ cho Qwen3.5 và Gemma 4.
7. Số [T] lệch giữa các repo (ví dụ E2B Q4_0: 2,84 GB ở ggml-org so với 3,36 GB ở một repo khác; Qwen3-1.7B Q8_0: 1,83 GB bản Qwen so với 2,17 GB bản ggml-org).
8. Tập trung một hãng (Qwen). Đối chứng khác hãng duy nhất (Gemma 4 E2B) vượt trần file.
9. Tên lệnh llama.cpp khác nhau giữa các bản (`llama serve`/`llama cli` ở trích đoạn HF mới, `llama-server`/`llama-cli` ở bản cũ); mọi cờ phải kiểm bằng `--help`.
10. File logits cơ sở của phép đo KL có thể lớn hơn đĩa trống (U20).

**RECOMMENDATION:** (thứ tự ưu tiên đo, không phải kết luận hiệu năng)

1. Cổng trước khi tải model: RAM khả dụng khi máy sạch, đĩa trống đạt A5 của TASK-001 (≥ 12 GiB hoặc ổ ngoài; hiện 4,01 GiB), GFLOPS bền vững/throttle (TASK-001).
2. Smoke test tiếng Việt 24 câu (A6) với M2 trước, vì file nhỏ nhất (0,53 GB); nếu M2 sai chuẩn tiếng Việt thì lặp lại với M1. Cho đến khi smoke test chạy, M1 chưa được coi là "đủ điều kiện CORE" về ngôn ngữ.
3. Đo M1 Q4_K_M (chữ) với n_ctx tường minh 4.096 và 8.192, ghi RSS, tok/s decode và prefill; sau đó V1 (ảnh ≤ 768×768).
4. Đo M4 Qwen3-1.7B Q4_K_M cùng điều kiện để lượng hóa chênh KV và tốc độ giữa hybrid và dense; đo V2 chỉ với n_ctx ≤ 4.096 hoặc KV q8_0.
5. Runtime chính: llama.cpp bản dựng sẵn + llama-server gọi qua HTTP từ Python 3.14 (không cần compiler). Runtime phụ: OpenVINO GenAI nếu đĩa cho phép và muốn thử iGPU. ORT GenAI để sau.
6. M3 và Gemma 4 E2B chỉ mở khi RAM sạch ≥ ~4–5 GiB và đĩa cho phép.
7. Thứ tự research card: C1, C2, C3. Ngân sách ở G = 100 GFLOPS: C1 ≈ 13–30 phút/mức (≈ 81–179 phút cho 6 mức, tùy N_KL theo đĩa trống), C2 ≈ 58 phút, C3 ≈ 60 phút; ở G = 200 giảm còn khoảng một nửa. Chưa tính công soạn bộ pilot P-60 (≈ 3 giờ người).

**NEXT_ACTION:**

1. Chủ dự án chuyển nguyên văn tài liệu này cho Claude C (context mới). Checklist: mở lại ≥ 30% ô có nguồn (gợi ý ở mục 0); kiểm công thức D1 và bảng D4; đọc file LICENSE gốc (U7); xử lý U12 và U20.
2. Chủ dự án chạy probe (không tải model): RAM sạch; kích thước zip và thư mục giải nén của bản llama.cpp Windows; kích thước wheel của openvino-genai và onnxruntime-genai (CPU).
3. Claude C (review thứ ba) kết luận accept và đề nghị Claude A ghi nhận phần vượt ngân sách (53 lệnh) và chốt đóng băng, không mở vòng 3. Nếu vẫn còn finding thì Claude A quyết định: chấp nhận ô UNKNOWN và đóng bằng đo ở M2, hoặc cho thêm một vòng. Danh sách truy vấn tối thiểu còn lại (≤ 6, theo thứ tự ưu tiên): (a) card Gemma 4 E2B-it và trang license Google; (b) phụ lục ngôn ngữ của báo cáo Qwen3 và bản gốc blog Qwen3.5; (c) README/LICENSE/releases của llama.cpp; (d) card MiniCPM5-2B; (e) repo Qwen3-4B-2507 và Qwen3-VL-4B. Config Qwen3.5-4B và file LICENSE Qwen đã bỏ khỏi danh sách vì Claude C đã mở ngày 2026-11-05 (S50, S52).

**UNVERIFIED_CLAIMS:** (trạng thái: ĐÓNG / THU HẸP / MỞ so với v1)

- **U1 [THU HẸP].** Dung lượng GGUF của M1, M2, M3, E2B đã đọc ở repo của bên chuyển đổi [P-g]. Còn mở: mmproj của V2, Qwen3-4B-2507, Qwen3-VL-4B; kích thước phụ thuộc repo (tied embedding) nên số của repo khác có thể lệch.
- **U2 [ĐÓNG].** UD-Q4_K_XL: 2B 1,34 GB; 0,8B 559 MB; 4B 2,91 GB [P].
- **U3 [ĐÓNG cho M3; MỞ cho E2B].** Hình học 0,8B (hidden 1024, FFN 3584, 8Q/2KV, head_dim 256, GDN 16/16 × 128) đọc từ bản sao card Qwen trong repo unsloth [P-m], nên KV 0,8B = 12 KiB/token. Config 4B do Claude C mở ngày 2026-11-05 [P, S50]: hidden 2560, FFN 9216, 32 lớp (8 lớp full-attention), 16 Q-head, 4 KV-head, head_dim 256, nên κ(M3) = 32 KiB/token (B chưa tự mở). Config của E2B vẫn chưa mở.
- **U4 [THU HẸP].** Tiếng Việt: xem A6. Qwen3.5 là ASSUMPTION; Qwen3 là REPORTED [T]; Gemma 4 là UNKNOWN.
- **U5 [THU HẸP].** llama.cpp + qwen35 + mmproj: metadata HF ghi kiến trúc qwen35; repo unsloth đưa mmproj kèm lệnh chạy llama.cpp; README bản sao dùng ví dụ Qwen3.5. Vẫn là REPORTED, chưa chạy. multimodal.md chính thức không liệt kê Qwen3.5 (Claude C mở nguyên trang ở review v1 và báo kết quả này; B không mở lại; liên kết: https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md). Claude C báo thêm rằng tài liệu này tự mô tả là danh sách model ggml-org đã lượng tử sẵn, nên việc không có Qwen3.5 không phải bằng chứng chống lại hỗ trợ.
- **U6 [THU HẸP].** `winget install llama.cpp` có trong trích đoạn HF [P]; tên asset Windows (cpu-x64, vulkan-x64, sycl-x64) từ [T]; dung lượng zip và có AVX2 mặc định hay không: UNKNOWN, đo.
- **U7 [THU HẸP, gần đóng].** License: đọc trực tiếp ở trang Qwen cho M1 (S29), M2 (S49), M3 (S50), Qwen3-1.7B (S38) và Qwen3-VL-2B (S40) [P]; S49 và S50 do Claude C mở ngày 2026-11-05. Gián tiếp chỉ còn E2B (metadata repo ggml-org [P-g], S37). File LICENSE của Qwen3.5-2B: Claude C mở và báo là văn bản Apache-2.0 chuẩn (S52); repo 4B có file LICENSE 11,5 kB (S50); trang 0,8B có liên kết tới file LICENSE (S49). Chưa mở: trang license Gemma 4, LICENSE của llama.cpp (MIT qua [T]), Qwen3-4B-2507 và Qwen3-VL-4B.
- **U8 [THU HẸP].** Ngày phát hành Qwen3.5: 2026-02-17 (blog, bản đăng lại [P-m]) đến 2026-03-02 (dòng nhỏ, [T]); card ghi "February 2026".
- **U9 [ĐÓNG].** OpenVINO không cần nightly cho Qwen3.5 từ 2026.2.0. Còn mở: IR int4 cỡ 2B có sẵn không; hiệu năng UHD 620.
- **U10 [THU HẸP].** ORT GenAI: wheel cp314 DirectML 0.14.0 = 4,1 MB [P]; ONNX dựng sẵn cho Qwen3.5-2B/0,8B và chất lượng int4: UNKNOWN.
- **U11 [MỞ].** "MTP speculative decoding nhanh ~1,5–2×" (Unsloth) là REPORTED, không nêu phần cứng; không dùng cùng `--mmproj`.
- **U12 [MỞ, thu hẹp].** Chênh giữa khuyến nghị bộ nhớ của Unsloth (3,5 GB ở 4-bit) và ESTIMATE 1,6–1,8 GiB (chữ) ít mâu thuẫn hơn vẻ ngoài: Claude C báo bảng Unsloth cho nhóm 0,8B + 2B là 3,5 / 7,5 / 9 GB (4-bit / 8-bit / BF16), tức phần dư so với file 2B dao động ≈ 2,2–5,5 GB (3,5 − 1,28; 7,5 − 2,01; 9 − 3,78), nên đó là gợi ý cỡ thô, không phải số đo. Chỉ đo RSS ở M2 mới chốt được.
- **U13 [THU HẸP].** S = 19,3 MiB tính từ config [P] với giả định trạng thái fp32 (ASSUMPTION; config ghi mamba_ssm_dtype float32 cho bản tham chiếu HF, chưa biết llama.cpp lưu dtype gì). Giả thuyết PLE + mmap hạ RSS của Gemma 4: UNKNOWN.
- **U14 [MỞ].** ASSUMPTION: A + R = 0,3–0,5 GiB; bộ đệm ảnh 0,1–0,3 GiB; η = 0,4–0,7; G = 100 hoặc 200 GFLOPS; mmap giữ resident ≤ kích thước file.
- **U15 [ĐÓNG một phần].** Quy tắc token ảnh của bộ xử lý HF đã có (1 token/32×32 px; 64–16.384 token). Còn UNKNOWN: mặc định và tên cờ giới hạn token ảnh của libmtmd.
- **U16 [MỞ].** MiniCPM5-2B "chỉ en/zh" và ngày 2026-09-07 là [T]; chưa mở card gốc (Claude C báo nhiều nguồn [T] độc lập khớp; B chưa mở card gốc).
- **U17 [MỞ, viết lại].** VMLU: quyền truy cập và license chưa kiểm; công khai từ trước nên có thể đã lọt vào dữ liệu huấn luyện của model 2026 (suy luận, cần kiểm); dùng nguyên sẽ vướng AC2 của TASK-003 (mọi nguồn item phải có license rõ). Chỉ là ứng viên chưa duyệt.
- **U18 [MỞ].** So sánh điểm Qwen và Gemma không hợp lệ (khác harness, chế độ nghĩ, định nghĩa OmniDocBench: Qwen báo điểm càng cao càng tốt, Gemma báo khoảng cách chỉnh sửa càng thấp càng tốt).
- **U19 [THU HẸP].** Chưa đánh giá: Ollama/LM Studio, CTranslate2, hàng chờ ở A5, model chuyên tiếng Việt, OCR-VLM chuyên dụng.
- **U20 [MỚI].** ASSUMPTION: file logits cơ sở của phép đo KL lưu logits toàn bộ từ vựng ≈ n_vocab × 2 byte/token; nếu đúng thì 16.384 token Qwen3.5 ≈ 8,1 GB, lớn hơn đĩa trống hiện tại (4,01 GiB) nhưng vừa nếu TASK-001 A5 đạt; C1 chọn N_KL theo đĩa trống. Phải kiểm bằng `--help`/mã nguồn công cụ perplexity trước M2. Cũng phải xác định N_KL là số token xử lý hay số token được chấm: công cụ kiểu perplexity có thể chỉ chấm một phần mỗi cửa sổ (ví dụ nửa sau), khi đó file cơ sở và độ chính xác của KL tính theo số token được chấm, còn thời gian tính theo số token xử lý. Lượt KL còn phải giữ logits fp32 ≈ 1 MB mỗi vị trí (C1).
- **U21 [MỚI].** head_dim = 128 của Qwen3-1.7B là suy luận (hidden 2048 ÷ 16 head, khớp 1,4B tham số không-embedding); hình học Qwen3-VL-2B (28 lớp, 8 KV-head) từ [T]. κ = 112 KiB/token là ESTIMATE.
- **U22 [THU HẸP].** Kích thước mmproj của V2: Claude C báo từ ghi chú phát hành [T] liệt kê file của repo chính thức rằng Q8_0 ≈ 445 MB, và một bản fine-tune cùng kiến trúc có BF16 ≈ 822 MB, nên F16 ≈ 0,8 GB (hơi trên ESTIMATE cũ 0,65–0,8 GB); B chưa mở các nguồn đó. Chất lượng OCR khi dùng projector Q8_0 chưa đo.
- **U23 [MỚI].** Danh sách 32 ngôn ngữ OCR của Qwen3-VL chưa thấy; Vietnamese có nằm trong đó hay không: UNKNOWN.
- **U24 [MỚI].** Đỉnh RAM của bộ mã hóa ảnh ở độ phân giải cao và tên/mặc định cờ giới hạn token ảnh: UNKNOWN; giữ ảnh ≤ 768 px cho tới khi đo.

## Phụ lục A — MODEL_MATRIX.md (v0, bản vòng 2)

**Công thức RAM (AC3):** `RAM ≈ W + M + KV + S + A + R (+ E_img khi có ảnh)`

- **W** là file trọng số (GiB = GB × 0,9313). Xấu nhất là đọc hết vào RAM; nếu mmap thì resident ≤ W.
- **M** là mmproj, chỉ tính khi dùng ảnh.
- **KV** = n_ctx × κ, với κ = 2 × L_attn × n_kv × d_head × b (b = 2 byte nếu fp16); chỉ tính lớp full-attention.
  - M1, M2: κ = 2 × 6 × 2 × 256 × 2 = 12.288 B = **12 KiB/token** (M1 từ config [S30]; M2 từ bản sao card [S35]).
  - M4, V2: κ = 2 × 28 × 8 × 128 × 2 = 114.688 B = **112 KiB/token** (ESTIMATE, U21).
  - M3: κ = 2 × 8 × 4 × 256 × 2 = 32 KiB/token (config 4B do Claude C mở 2026-11-05, S50).
- **S** (trạng thái hồi quy của lớp Gated DeltaNet) = L_gdn × (H_v × d_k × d_v × 4 B + trạng thái conv). Với M1 và M2: 18 × (16 × 128 × 128 × 4 B + 3 × 6.144 × 4 B) = 18 × (1,0 MiB + 72 KiB) ≈ **19,3 MiB = 0,019 GiB** (ESTIMATE từ [S30]; fp32 là ASSUMPTION, U13). M3 ≈ 0,05 GiB (Claude C tính từ config 4B). Dense thì S = 0.
- **A + R** (bộ đệm tính toán + runtime + thư viện): ASSUMPTION 0,3–0,5 GiB. **E_img** (đỉnh bộ đệm bộ mã hóa ảnh): ASSUMPTION 0,1–0,3 GiB (U14, U24).
- **Quy tắc biên (L3):** VỪA nếu ≤ 2,8 GiB (trần 3,0 trừ biên 0,2 cho sai số của A + R); BIÊN nếu 2,8–3,0; VƯỢT nếu > 3,0. Với trần 2 và 5 GiB trừ biên tương tự (1,8 và 4,8). Trần file ≤ 2,5 GB của planning envelope kiểm riêng.
- Mặc định n_ctx = 8.192, KV fp16.

### A0. Tóm tắt (n_ctx = 8.192; chi tiết ở A1–A5)

Cột cuối chỉ có nghĩa nếu RAM khả dụng khi máy sạch đạt ≥ 3 GiB; số đo duy nhất hiện có là 0,68–0,76 GiB (D5).

| ID | Model | Vai trò | Quant tham chiếu | File GB (+mmproj) | RAM ESTIMATE, GiB (chữ / ảnh) | License [nguồn] | Với trần 3 GiB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1/V1 | Qwen3.5-2B | LLM + VLM chính; ứng viên baseline CORE | Q4_K_M | 1,28 (+0,668) | 1,6–1,8 / 2,3–2,7 | Apache-2.0 [P: S29; P-g: S34] | VỪA theo công thức; phải đo RSS (U12) |
| M2 | Qwen3.5-0.8B | LLM dự phòng ≤ 2 GiB; VLM nhẹ | Q4_K_M | 0,533 (+0,205) | 0,9–1,1 / 1,2–1,6 | Apache-2.0 [P: S49; P-g: S35] | VỪA |
| M3 | Qwen3.5-4B | LLM cho kịch bản 5 GiB | Q4_K_M (IQ4_XS) | 2,74 (2,48) (+0,672) | 3,15–3,35 (IQ4_XS: 2,9–3,1) | Apache-2.0 [P: S50; P-g: S36] | LOẠI: file > 2,5 GB và RAM > 3,0; IQ4_XS ở BIÊN/VƯỢT |
| M4 | Qwen3-1.7B | LLM đối chứng kiến trúc cũ (dense) | Q4_K_M | 1,28 | 2,4–2,6 @8K; 1,9–2,1 @4K; 3,2–3,4 @16K | Apache-2.0 [P: S38; P-sn: S39] | VỪA nếu n_ctx ≤ 8K; VƯỢT từ 16K |
| V2 | Qwen3-VL-2B-Instruct | VLM đối chứng | Q4_K_M | 1,11 (+mmproj Q8_0 ≈ 0,445 [T, Claude C báo]; F16 ≈ 0,8) | — / Q8_0: 2,3–2,7 @4K, 2,7–3,1 @8K; F16: 2,5–3,0 @4K | Apache-2.0 [P: S40] | VỪA @4K với projector Q8_0 (OCR chưa đo); BIÊN @8K hoặc với F16 @4K |
| X1 | Gemma 4 E2B | đối chứng khác hãng (đã sàng lọc, không thuộc 4+2) | Q4_0 | 2,84 | ≥ 2,9–3,1 chưa tính KV | Apache-2.0 [P-g, gián tiếp: S37] | Ngoài CORE theo trần file 2,5 GB; chưa loại về RAM thực (PLE + mmap có thể hạ RSS, U13); ưu tiên đo đầu tiên khi đĩa cho phép; giữ cho 5 GiB |
| X2 | MiniCPM5-2B | — | — | — | — | Apache-2.0 [T] | LOẠI: chỉ en/zh (U16) |

### A1. M1/V1 — Qwen3.5-2B

- **Tên/phiên bản:** Qwen/Qwen3.5-2B (bản post-trained; có thêm Qwen3.5-2B-Base) [S29, S32]. GGUF đo: unsloth/Qwen3.5-2B-GGUF [S34], đã mở cây thư mục 2026-10-26.
- **Kiến trúc [P, config.json, S30]:** 24 lớp, bố cục 6 × (3 Gated DeltaNet + 1 full attention) = 18 + 6; hidden 2048; FFN 6144; từ vựng 248.320, embedding tied; full attention 8 Q-head / 2 KV-head / head_dim 256; GDN 16 head K và 16 head V, head_dim 128, kernel conv 4; ngữ cảnh gốc 262.144; có 1 lớp MTP trong checkpoint. Bộ mã hóa ảnh: 24 khối, hidden 1024, FFN 4096, 16 head, patch 16, gộp 2×2.
- **Số tham số (ESTIMATE):** LM ≈ 1,89B (= file BF16 3,78 GB ÷ 2 byte [S34]), trong đó embedding 0,509B (248.320 × 2048) và không-embedding 1,381B; cộng trực tiếp từ config ra 1,372B (MLP 906M + GDN 378M + attention 88M), khớp ≤ 1%. ViT + projector ≈ 0,334B (mmproj F16 668 MB ÷ 2). Đây là cơ sở của N trong D4.
- **Dung lượng GGUF [P-g, S34, 2026-10-26]:** Q4_K_M 1,28 GB (1,19 GiB); UD-Q4_K_XL 1,34 (1,25); IQ4_XS 1,17 (1,09); Q5_K_M 1,44 (1,34); Q6_K 1,57 (1,46); Q8_0 2,01 (1,87); BF16 3,78 (3,52). mmproj: F16 668 MB (0,62 GiB), BF16 671 MB, F32 1,33 GB. Repo này **không có** mmproj Q8_0 (số 348 MiB ở v1 là của một bản fine-tune [T]).
- **RAM (ESTIMATE):**
  - W = 1,28 GB = 1,19 GiB (Q4_K_M); KV = 12 KiB × 8.192 = 96 MiB = 0,094 GiB; S = 0,019 GiB.
  - **Chữ:** 1,19 + 0,094 + 0,019 + (0,3–0,5) = **1,6–1,8 GiB** (VỪA).
  - **Ảnh (V1):** + M 0,62 + E_img (0,1–0,3) = **2,3–2,7 GiB** (VỪA). Với Q8_0: chữ 2,3–2,5 (VỪA) nhưng ảnh 3,0–3,4 (VƯỢT), nên đường ảnh chỉ dùng lớp Q4.
  - Đối chiếu: Unsloth khuyến nghị 3,5 GB bộ nhớ tổng cho 4-bit nhóm 0,8B + 2B [S47]; mâu thuẫn chưa giải (U12), chỉ đo RSS mới chốt.
  - **Bẫy ngữ cảnh (T5):** card ghi ngữ cảnh mặc định 262.144 và khuyên giảm khi OOM [S32]. Với κ = 12 KiB/token, KV@262.144 = **3,0 GiB**, bằng cả trần. Khi đo bắt buộc đặt n_ctx tường minh (tên cờ kiểm bằng `--help`) và coi KV@262K là điều kiện cần tránh.
  - **Bẫy token ảnh (U15, U24):** bộ xử lý ảnh gốc cho phép tới 16.384 token/ảnh (D4); phải hạ độ phân giải trước khi đưa vào.
- **License:** Apache-2.0, đọc từ trường license trên trang repo Qwen/Qwen3.5-2B (S29, 2026-10-26) và card (S32, có license_link); repo có file LICENSE 11,5 kB; Claude C mở ngày 2026-11-05 và báo đó là văn bản Apache-2.0 chuẩn (S52, U7); B chưa tự mở. Repo GGUF unsloth [P-g] cũng ghi apache-2.0 (S34), gián tiếp.
- **Ngày phát hành (L6):** card ghi "February 2026" cho cả họ [S32]; blog Qwen3.5 đăng lại ngày 2026-02-17 [P-m, S33] (bài về model lớn); dòng nhỏ 0,8B–9B khoảng 2026-03-02 [T, S10 của v1]. Ghi khoảng 2026-02-17 đến 2026-03-02; không ảnh hưởng quyết định.
- **Tiếng Việt:** xem A6 (ASSUMPTION, chưa có bằng chứng riêng).
- **Điểm công bố (REPORTED, nêu điều kiện):** xem A7.
- **Runtime Windows CPU:** llama.cpp: metadata kiến trúc qwen35 trên HF, mmproj đi kèm (U5, REPORTED). OpenVINO GenAI: Qwen3.5 trên CPU và GPU từ 2026.2.0 [S42]. ORT GenAI: chế độ text-only cho Qwen3.5 từ 0.14.0 [S16 của v1].
- **Rủi ro:** mặc định non-thinking, ở chế độ thinking 2B dễ rơi vòng lặp [S32]; card định vị 2B cho prototyping/fine-tune/nghiên cứu [S32]; kiến trúc mới nên runtime và quant chưa chín; MTP speculative decoding không dùng cùng `--mmproj` [S9 của v1]; các bẫy ngữ cảnh và token ảnh ở trên.

### A2. M2 — Qwen3.5-0.8B (dự phòng)

- **Cấu hình [P-m: bản sao card Qwen trong repo unsloth, S35]:** hidden 1024; 24 lớp; cùng bố cục 6 × (3 GDN + 1 attention); attention 8 Q-head / 2 KV-head / head_dim 256; GDN 16 head V và 16 head QK, head_dim 128; FFN 3584; từ vựng 248.320 (đệm); ngữ cảnh 262.144. Suy ra κ = 12 KiB/token và S = 19,3 MiB như M1 (ESTIMATE; U3 đã thu hẹp).
- **Số tham số (ESTIMATE):** LM ≈ 0,76B (BF16 1,52 GB ÷ 2), embedding 0,254B, không-embedding 0,506B; ViT + projector ≈ 0,10B (mmproj 205 MB ÷ 2).
- **Dung lượng [P-g, S35]:** Q4_K_M 533 MB (0,50 GiB); UD-Q4_K_XL 559 MB; Q8_0 812 MB (0,76 GiB); BF16 1,52 GB; Q4_0 và IQ4_NL 507 MB; mmproj F16 205 MB (0,19 GiB), BF16 207 MB, F32 402 MB. **Đóng U15 cho mmproj 0,8B.**
- **RAM (ESTIMATE):** chữ 0,50 + 0,094 + 0,019 + (0,3–0,5) = **0,9–1,1 GiB**; ảnh + 0,19 + (0,1–0,3) = **1,2–1,6 GiB**. Cả hai VỪA, kể cả ở trần 2 GiB.
- **License:** Apache-2.0: trang Qwen/Qwen3.5-0.8B ghi apache-2.0 kèm liên kết file LICENSE (Claude C mở 2026-11-05 [P, S49]); metadata repo unsloth cùng giá trị [P-g, S35].
- **Điểm (REPORTED, A7):** MMLU-Pro 29,7 (non-thinking) và 42,3 (thinking); IFEval 52,1; MMMLU 34,1; GPQA 11,9 (thinking); OCRBench 74,5/79,1; OmniDocBench1.5 61,0/70,6.
- **Rủi ro:** chất lượng thấp, chỉ hợp tác vụ đơn giản hoặc có ràng buộc cứng; card nêu dễ rơi vòng lặp khi thinking; mặc định non-thinking [S35].

### A3. M3 — Qwen3.5-4B (kịch bản 5 GiB)

- **Dung lượng [P-g, S36, 2026-10-26]:** Q4_K_M **2,74 GB** (2,55 GiB); IQ4_XS 2,48 GB (2,31 GiB); UD-Q3_K_XL 2,44; Q3_K_M 2,29; UD-Q4_K_XL 2,91; Q8_0 4,48; BF16 8,42; mmproj F16 672 MB (0,63 GiB). Số 2,6 GB ở v1 (bản fine-tune [T]) sai; số đúng lớn hơn 5%.
- **Tham số (ESTIMATE):** LM ≈ 4,21B (8,42 GB ÷ 2); không-embedding ≈ 3,57B (= 4,21B trừ embedding 248.320 × 2560 = 0,636B). Config 4B do Claude C mở ngày 2026-11-05 [P, S50]: hidden 2560, FFN 9216, 32 lớp (8 lớp full-attention), 16 Q-head và 4 KV-head, head_dim 256; khớp con số trên. B chưa tự mở.
- **RAM (ESTIMATE):** từ config 4B (Claude C mở): κ = 2 × 8 × 4 × 256 × 2 B = 32 KiB/token, nên KV@8K = 0,25 GiB; S ≈ 0,05 GiB (Claude C tính). Q4_K_M: 2,55 + 0,25 + 0,05 + (0,3–0,5) = **3,15–3,35 GiB** (VƯỢT). IQ4_XS: 2,31 + 0,25 + 0,05 + (0,3–0,5) = **2,9–3,1 GiB** (BIÊN/VƯỢT). Có ảnh (Q4_K_M): + 0,63 + E_img (0,1–0,3) ≈ 3,9–4,3 GiB (VƯỢT ở 3 GiB).
- **License:** Apache-2.0: trang repo Qwen/Qwen3.5-4B ghi apache-2.0 và có file LICENSE 11,5 kB (Claude C mở 2026-11-05 [P, S50]); metadata repo unsloth cùng giá trị [P-g, S36]. Cấu hình: có (S50). Điểm công bố của M3: chưa có (card chưa mở).
- **OpenVINO:** IR fp16 và int8 cần OpenVINO ≥ 2026.2.0 [S13 của v1]; int8 cỡ 4B ≈ 4 GB (ESTIMATE = tham số × 1 byte), vượt trần file.
- **Kết luận (AC6):** LOẠI khỏi kịch bản 3 GiB vì Q4_K_M vượt trần file 2,5 GB (thêm 0,24 GB, +9,6%) và vượt biên RAM (3,15–3,35 GiB); IQ4_XS lọt trần file 2,5 GB nhưng ở BIÊN/VƯỢT RAM (2,9–3,1 GiB), tốc độ decode trần 7,7 tok/s (ESTIMATE) và prefill ≈ 130 s/1.000 token (ESTIMATE, D4), nên không đưa vào CORE mặc định. Giữ cho kịch bản 5 GiB.

### A4. M4 — Qwen3-1.7B (đối chứng LLM kiến trúc cũ) và V2 — Qwen3-VL-2B-Instruct (đối chứng VLM)

**M4 Qwen3-1.7B**

- **Nguồn [P]:** Qwen/Qwen3-1.7B-GGUF (S38): license apache-2.0; 28 lớp; 16 Q-head / 8 KV-head (GQA); ngữ cảnh 32.768; 1,7B tham số, 1,4B không-embedding; hỗ trợ "100+ ngôn ngữ và phương ngữ"; repo chính thức chỉ có Q8_0 = 1,83 GB. Bản ggml-org [S39, [P-sn] từ trích đoạn tìm kiếm]: apache-2.0, Q4_K_M 1,28 GB, Q8_0 2,17 GB, F16 4,07 GB.
- **Chênh file giữa repo (U1):** Q8_0 1,83 GB (Qwen) so với 2,17 GB (ggml-org) chênh ≈ 0,33 GB, đúng cỡ ma trận đầu ra 311M tham số ở 8 bit nếu repo ggml-org không dùng tied embedding (ESTIMATE). Dùng số lớn hơn (1,28 GB cho Q4_K_M) làm số thận trọng.
- **KV:** κ = 112 KiB/token (ESTIMATE; head_dim = 128 suy từ hidden 2048 ÷ 16 head và khớp 1,4B tham số không-embedding, U21). KV@4K = 0,44 GiB; @8K = **0,875 GiB**; @16K = 1,75; @32K = **3,5 GiB** (vượt trần chỉ với ngữ cảnh gốc).
- **RAM (ESTIMATE):** W 1,19 + KV + (0,3–0,5): @4K **1,9–2,1**; @8K **2,4–2,6**; @16K **3,2–3,4 (VƯỢT)**. Không có lớp hồi quy nên S = 0.
- **Điểm (REPORTED, bảng của Qwen trong card Qwen3.5-2B [S32]):** non-thinking MMLU-Pro 40,2, IFEval 68,2, MMMLU 46,7; thinking MMLU-Pro 56,5, GPQA 40,1, IFEval 72,5, MMMLU 57,0, INCLUDE 51,8, WMT24++ 39,3.
- **Tiếng Việt:** Vietnamese nằm trong 119 ngôn ngữ của Qwen3 (REPORTED [T], A6). Card chính thức chỉ ghi "100+ ngôn ngữ".
- **Runtime:** llama.cpp (GGUF chính thức của Qwen và ggml-org); kiến trúc dense GQA đã hỗ trợ lâu nên rủi ro kiến trúc thấp hơn qwen35.
- **Vai trò:** (a) đối chứng "kiến trúc cũ, trưởng thành" cho T1: nếu bản build llama.cpp hoặc quant của qwen35 lỗi thì vẫn có đường chạy; (b) đo trực tiếp lợi thế KV của hybrid (12 so với 112 KiB/token) ở cùng cỡ file 1,28 GB. Ngày phát hành: năm 2025; báo cáo kỹ thuật Qwen3 là arXiv 2505.09388, tức tháng 5/2025 theo mã (ngày phát hành model: UNKNOWN chính xác, không ảnh hưởng quyết định).

**V2 Qwen3-VL-2B-Instruct**

- **Nguồn [P]:** Qwen/Qwen3-VL-2B-Instruct-GGUF (S40): license apache-2.0; LLM GGUF Q4_K_M 1,11 GB, Q8_0 1,83 GB, F16 3,45 GB; mmproj F16 và Q8_0 (trang không nêu dung lượng; Claude C báo từ ghi chú phát hành [T] liệt kê file của repo chính thức rằng Q8_0 ≈ 445 MB, và một bản fine-tune cùng kiến trúc có BF16 ≈ 822 MB, nên F16 ≈ 0,8 GB, hơi trên khoảng 0,65–0,8 GB ESTIMATE trước đây; B chưa mở các nguồn đó, U22); card nêu OCR mở rộng 32 ngôn ngữ (không liệt kê, U23); yêu cầu llama.cpp từ bản b6907 trở lên. Hình học LLM (28 lớp, 2048d, 16 head, 8 KV-head) từ [T] cstr (U21).
- **RAM (ESTIMATE):** LLM Q4_K_M 1,03 GiB + mmproj + KV + (0,3–0,5) + E_img (0,1–0,3). Với projector Q8_0 (≈ 0,445 GB = 0,41 GiB, [T], Claude C báo): @4K (KV 0,44) **2,3–2,7** (VỪA); @8K (KV 0,875) **2,7–3,1** (BIÊN); @8K với KV q8_0 (nửa KV) 2,3–2,7. Với projector F16 (ESTIMATE ≈ 0,65–0,82 GB): @4K **2,5–3,0** (BIÊN); @8K **2,9–3,5**. Chất lượng OCR khi dùng projector Q8_0 chưa đo.
- **Điểm (REPORTED, bảng Qwen [S32]; thinking/non-thinking khi có hai số):** OCRBench Qwen3-VL-2B 79,2, Qwen3-VL-4B 80,8, Qwen3.5-2B 84,5/85,4; OmniDocBench1.5 65,9, 80,0, 79,8/80,9; CC-OCR (VL-2B) 68,3 so với 72,9/75,8; MMMU 61,4 so với 64,2/64,2; CharXiv-RQ 37,1 so với 58,8/52,6.
- **Vai trò:** đối chứng đường VLM kiến trúc dense, có tài liệu llama.cpp riêng và quant mmproj Q8_0 sẵn; dùng để biết lỗi (nếu có) thuộc về qwen35 hay thuộc về máy.

### A5. Sàng lọc: loại, hàng chờ (T1, AC6)

**Kết luận AC6 (có điều kiện).** Điều kiện: RAM khả dụng khi máy sạch ≥ 3 GiB, chưa đo (snapshot 0,68–0,76 GiB; D5). Nếu điều kiện đúng thì vừa 3 GiB: M1 (chữ và ảnh), M2 (chữ và ảnh), M4 (n_ctx ≤ 8K), V2 (n_ctx ≤ 4K với projector Q8_0, OCR chưa đo). Ở biên: V2 @8K hoặc với projector F16, và M3 IQ4_XS. Bị loại khỏi CORE: M3 Q4_K_M (file 2,74 GB > 2,5 GB; RAM 3,15–3,35 GiB), X1 Gemma 4 E2B (file 2,84 GB > 2,5 GB; chưa loại về RAM thực, U13), X2 MiniCPM5-2B (thiếu tiếng Việt).

| ID | Ứng viên | Bằng chứng đã có | License | File / RAM | Tiếng Việt | Quyết định và lý do |
| --- | --- | --- | --- | --- | --- | --- |
| X1 | Gemma 4 E2B-it | Repo ggml-org [P-g, S37]: kiến trúc gemma4, "5B params"; chỉ có Q4_0 2,84 GB, Q8_0 4,97 GB, BF16 9,31 GB (và bản MTP ≈ 59 MB); **không có Q4_K_M** (3,1 GB ở v1 là repo khác [T]); một repo cộng đồng ghi Q4_0 3,36 GB và Q4_K_M 3,43 GB [T, S48], tức lệch tới 18% giữa các repo | Apache-2.0 theo metadata repo ggml-org [P-g, gián tiếp]; Claude C báo thấy cùng giá trị ở card Google 12B và E4B nhưng chỉ qua trích đoạn tìm kiếm (không phải trang đầy đủ); card E2B-it và trang license Google chưa ai mở (U7). Bài [T] S27 ("Gemma Terms of Use") mâu thuẫn và bị bác ở mức metadata | W 2,65 GiB + (0,3–0,5) ≥ 2,9–3,1, chưa tính KV (UNKNOWN) | UNKNOWN: "35+ ngôn ngữ ngoài hộp, huấn luyện trên 140+", không liệt kê | **Ngoài CORE theo trần file** (file > 2,5 GB; RAM ≥ 2,9 là cận thận trọng giả định cả file resident). **Chưa loại về RAM thực**: 2,3B tham số hiệu dụng so với 5,1B kể cả embedding nên RSS có thể thấp hơn file nhiều (U13). Ưu tiên đo đầu tiên khi đĩa cho phép vì là đối chứng khác hãng duy nhất; giữ cho 5 GiB. Điểm mạnh VLM: ngân sách token ảnh chọn được 70–1120 (v1 S2) |
| X2 | MiniCPM5-2B | [T] (v1 S19): 2.516.756.480 tham số, ctx 131.072, Apache-2.0, 2026-09-07; chỉ en/zh (Claude C báo nhiều nguồn [T] độc lập khớp; B chưa mở card gốc) | Apache-2.0 [T] | — | không (en/zh) | **LOẠI** vì thiếu tiếng Việt. Card gốc chưa mở (U16) |
| X3 | Qwen3-4B-2507 | Chỉ có điểm trong bảng Qwen [S32]: MMLU-Pro 69,6, IFEval 83,4 (non-thinking) | UNKNOWN (ASSUMPTION Apache-2.0 như họ Qwen3 dense; repo chưa mở) | UNKNOWN; ESTIMATE 2,4–2,8 GB nếu cùng cỡ Qwen3.5-4B (Q4_K_M 2,74 GB) | như Qwen3 (REPORTED [T]) | **HÀNG CHỜ** kịch bản 5 GiB: mạnh hơn rõ về chữ so với Qwen3.5-2B nhưng file gần gấp đôi |
| X4 | Qwen3-VL-4B | Điểm trong bảng Qwen [S32]: OCRBench 80,8, OmniDocBench1.5 80,0 | UNKNOWN | UNKNOWN; LLM 4B + mmproj chắc chắn > 2,5 GB | UNKNOWN | **HÀNG CHỜ** kịch bản 5 GiB |
| X5 | Gemma 3 4B | Có trong danh sách llama.cpp [P, S3]; chưa mở card/repo | UNKNOWN | UNKNOWN | UNKNOWN | **CHƯA SÀNG LỌC** (hết ngân sách) |
| X6–X8 | SmolVLM2-2.2B, InternVL3-2B, Qwen2.5-VL-3B | Có trong danh sách llama.cpp [P, S3]; chưa mở | UNKNOWN | UNKNOWN | UNKNOWN | **CHƯA SÀNG LỌC**; hàng chờ đối chứng VLM nếu cả V1 và V2 thất bại ở M2 (mỗi ứng viên ≈ 2 truy vấn: card + cây thư mục GGUF) |

Chưa khảo sát (không phải loại): SmolLM3-3B, LFM2.5-1.2B, Phi-4-mini, Llama 3.2 1B/3B, Ministral 3B, MiniCPM-V 4.6 [T, S28]; OCR-VLM chuyên dụng (PaddleOCR-VL, GLM-OCR, DeepSeek-OCR, dots.ocr, HunyuanOCR) [P, S3]; model chuyên tiếng Việt (chưa tìm thấy, không có nghĩa là không tồn tại).

Kiểm tra thế hệ mới (Claude C báo, 2026-11-05): các bản Qwen3.6 thấy được chỉ là 35B-A3B và 27B, không có cỡ nhỏ; chưa thấy dấu hiệu bỏ sót một thế hệ Qwen nhỏ mới hơn.

### A6. Bằng chứng tiếng Việt (C2, U4) và smoke test

| Model | Bằng chứng | Nhãn | Khoảng trống |
| --- | --- | --- | --- |
| Qwen3.5 (M1, M2, M3) | Card ghi 201 ngôn ngữ và phương ngữ [P, S32]. Blog (bản đăng lại ngày 2026-02-17) nêu mở rộng từ 119 lên 201 và từ vựng 250k (trước đó 150k) giúp hiệu quả mã hóa tăng 10–60% ở hầu hết ngôn ngữ [P-m, S33]. Không có danh sách ngôn ngữ ở trang nào đã mở | Số lượng: REPORTED. "Có tiếng Việt": **ASSUMPTION** (suy luận: Vietnamese thuộc 119 của Qwen3, và 201 là "mở rộng") | Chưa thấy tên Vietnamese ở nguồn nào của Qwen3.5. Cần danh sách gốc hoặc smoke test |
| Qwen3 (M4) | Vietnamese nằm trong nhóm Austroasiatic của bảng 119 ngôn ngữ (bản chép [T, S41]); báo cáo kỹ thuật arXiv 2505.09388 nêu 29 → 119 ngôn ngữ [P-sn]; card chính thức chỉ ghi "100+" | REPORTED [T] | Chưa mở phụ lục báo cáo gốc |
| Qwen3-VL-2B (V2) | OCR 32 ngôn ngữ (trước là 19), không liệt kê [P, S40] | UNKNOWN cho Vietnamese | U23 |
| Gemma 4 (X1) | "35+ ngoài hộp, huấn luyện 140+", không liệt kê (v1 S2: https://huggingface.co/google/gemma-4-12B) | UNKNOWN | Không có danh sách |
| MiniCPM5-2B (X2) | en/zh [T] | REPORTED [T] | Loại |

Các điểm đa ngữ của Qwen (MMMLU, MMLU-ProX 29 ngôn ngữ, INCLUDE, WMT24++ 55 ngôn ngữ; A7) là số gộp, không tách tiếng Việt, nên không đủ để kết luận. Cho đến khi smoke test chạy, M1 chưa được coi là "đủ điều kiện CORE" về ngôn ngữ.

**Smoke test tiếng Việt 24 câu** (bước đầu của M2; $0; ≈ 5–10 phút/model, ESTIMATE: 24 câu × 12–25 s, chưa đo, cùng cỡ tầng SMOKE ≤ 10 phút của TASK-003; chỉ là cổng sàng lọc, chất lượng thật đo ở TASK-003):

- **Thành phần:** 6 hỏi đáp có đáp án kiểm được; 4 tóm tắt đoạn có dấu; 4 làm theo định dạng (JSON hoặc bảng); 4 dịch Việt↔Anh; 3 toán đố lời; 3 khôi phục dấu thanh. Câu lấy từ cùng nguồn với bộ pilot P-60 (Phụ lục C) nên không soạn hai lần; tự biên soạn hoặc tái dùng tài liệu chủ dự án có quyền, không dùng dữ liệu học sinh hay cá nhân, không lấy từ VMLU (U17).
- **Tiêu chí (ngưỡng do Claude A chốt; đề xuất là ASSUMPTION):** (i) không hỏng dấu: 0/20 đầu ra mất hoặc sai dấu bất thường; (ii) bám ngôn ngữ: không tự chuyển sang tiếng Anh/Trung khi không yêu cầu; (iii) ≥ 5/6 đáp án kiểm được đúng; (iv) ghi số token/từ tiếng Việt của M1 (từ vựng 248.320) và M4 bằng trường usage của llama-server hoặc công cụ tokenize, không cần sinh văn bản.
- **Nếu M2 hỏng ở (i) hoặc (ii):** lặp lại với M1 và M4 trước khi kết luận về họ Qwen3.5.

### A7. Điểm công bố (REPORTED) và điều kiện (L5)

**Điều kiện (S32):** số do Qwen tự chạy, không nêu phần cứng, không so được với tốc độ trên laptop. Bảng văn bản/đa ngữ: top_p = 0,95, top_k = 20, presence_penalty = 1,5, temperature = 1,0. Bảng thị giác: benchmark video dùng cùng bộ tham số trên; các benchmark còn lại cùng cấu hình nhưng temperature = 0,6 ở thinking; ở non-thinking dùng top_p = 0,8, top_k = 20, presence_penalty = 1,5, temperature = 0,7. M3 (Qwen3.5-4B): chưa có điểm nào vì chưa mở card. Khuyến nghị lấy mẫu của card khi dùng thật (không phải điều kiện của điểm): non-thinking văn bản temperature 1,0, top_p 1,0, top_k 20, presence_penalty 2,0; non-thinking thị giác 0,7 / 0,8 / 20 / 1,5; thinking văn bản 1,0 / 0,95 / 20 / 1,5.

| Chỉ số (chế độ) | Qwen3.5-2B | Qwen3.5-0.8B | Qwen3-1.7B | Qwen3-4B-2507 |
| --- | --- | --- | --- | --- |
| MMLU-Pro (non-thinking) | 55,3 | 29,7 | 40,2 | 69,6 |
| IFEval (non-thinking) | 61,2 | 52,1 | 68,2 | 83,4 |
| MMMLU (non-thinking) | 56,9 | 34,1 | 46,7 | 64,9 |
| MMLU-Pro (thinking) | 66,5 | 42,3 | 56,5 | 74,0 |
| GPQA (thinking) | 51,6 | 11,9 | 40,1 | 65,8 |
| MMMLU (thinking) | 63,1 | 44,3 | 57,0 | 70,8 |
| INCLUDE (thinking) | 55,4 | 40,6 | 51,8 | 64,4 |
| WMT24++ (thinking) | 45,8 | 27,2 | 39,3 | 58,9 |
| IFEval (thinking) | 78,6 | 44,0 | 72,5 | 87,4 |

| Chỉ số thị giác | Qwen3-VL-4B | Qwen3-VL-2B | Qwen3.5-2B (thinking/non) | Qwen3.5-0.8B (thinking/non) |
| --- | --- | --- | --- | --- |
| OCRBench | 80,8 | 79,2 | 84,5 / 85,4 | 74,5 / 79,1 |
| OmniDocBench1.5 | 80,0 | 65,9 | 79,8 / 80,9 | 61,0 / 70,6 |
| CC-OCR | — | 68,3 | 72,9 / 75,8 | — |
| MMMU | — | 61,4 | 64,2 / 64,2 | — |
| CharXiv-RQ | — | 37,1 | 58,8 / 52,6 | — |

Review v2 của Claude C báo toàn bộ ô điểm ở A2, A4 và A7 khớp S32; đó là lời báo của reviewer, chưa phải bằng chứng độc lập của B, nên Claude C nên mở lại ≥ 3 ô khi kiểm bản này. Dấu "—" là ô tôi không chép, không phải UNKNOWN của nguồn.

**Đọc bảng (ESTIMATE/lập luận, không phải kết luận hiệu năng):** Qwen3.5-2B hơn Qwen3-1.7B về kiến thức và đa ngữ gộp nhưng **thua ở IFEval non-thinking** (61,2 so với 68,2), trong khi ở chế độ thinking thì ngược lại (78,6 so với 72,5); Qwen3-4B-2507 hơn hẳn cả hai về chữ nhưng file gần gấp đôi. Về thị giác, Qwen3.5-2B hơn Qwen3-VL-2B ở mọi dòng chép và ngang hoặc hơn Qwen3-VL-4B ở OCRBench. Điểm Qwen và Gemma không so trực tiếp được (U18).

## Phụ lục B — RUNTIME matrix (T2, AC4)

Mỗi ô có giá trị kèm nhãn, hoặc UNKNOWN kèm cách đóng (cuối phụ lục); không ô nào để trống. Các ô UNKNOWN chính: dung lượng cài của llama.cpp, wheel openvino-genai và phụ thuộc ONNX Runtime, IR/ONNX dựng sẵn cho Qwen3.5-2B, hiệu năng iGPU.

| Thuộc tính | R1 llama.cpp | R2 OpenVINO GenAI | R3 ONNX Runtime GenAI |
| --- | --- | --- | --- |
| Bản mới nhất thấy | Build b11081 (wiki [T], 2026-09-29). Bản mới hơn: UNKNOWN (chưa mở trang releases) | openvino 2026.4.1 trên PyPI [P-sn, S43]; ghi chú phát hành 2026.2.0 và 2026.3.0 [P-sn, S42]; 2026.4.0 [T, mirror]. openvino-genai: bản sao PyPI ghi 2026.1.0.0 [T, S44], bản mới hơn UNKNOWN | onnxruntime-genai-directml 0.14.0 trên PyPI [P-sn, S45]; depscope ghi 0.13.2 (2026-05-01) [T]; 0.14.0 thêm chế độ text-only cho Qwen3.5 [S16 của v1] |
| Cài trên Win11 + Python 3.14 | Zip dựng sẵn từ trang releases (asset Windows: cpu-x64, vulkan-x64, sycl-x64 [T, S46]) hoặc `winget install llama.cpp` [P-g: lệnh trong trích đoạn HF tự sinh trên S35]. Chạy server rồi gọi bằng HTTP (API tương thích OpenAI) từ Python 3.14, nên không phụ thuộc wheel cp314. Tên lệnh khác nhau giữa bản: `llama serve`/`llama cli` (HF mới) hoặc `llama-server`/`llama-cli` (cũ), kiểm bằng `--help` | `pip install openvino-genai` (kéo openvino, openvino-tokenizers). Wheel cp314 win_amd64 của **openvino** có ở 2026.4.1 và 2026.3.0 [P-sn, S43]. Wheel openvino-genai cp314: chủ dự án đã xác nhận ở v1; tôi chưa mở trang gốc | `pip install onnxruntime-genai`. Wheel cp314 win_amd64 của bản **DirectML** 0.14.0 có [P-sn, S45]; bản CPU: chủ dự án đã xác nhận cp314 ở v1 |
| Cần compiler? | Không với zip. llama-cpp-python chỉ có sdist cp314 và cần compiler (chủ dự án xác nhận ở v1) nên không dùng | Không với wheel. Chuyển đổi model (optimum-intel + torch) nặng; ưu tiên IR dựng sẵn | Không với wheel. Model builder cần torch, transformers, onnx [T, S17, chỉ là gợi ý] nên nặng đĩa |
| Dung lượng cài | **UNKNOWN**: đo kích thước zip và thư mục giải nén (kế hoạch ở cuối phụ lục) | Wheel openvino 2026.4.1 cp314 win_amd64 = **85,0 MB** (Claude C mở 2026-11-05 [P, S51]); wheel openvino-genai: UNKNOWN. Runtime Windows ≈ 130 MB (bộ DLL tinh gọn) đến ≈ 233 MB (kho chính thức) theo gói pub.dev bản 2026.0.0.0 [T, S44]. IR int4 cỡ 2B: UNKNOWN (ESTIMATE ≈ 1,1 GB = 2,3B × 0,5 byte) | Wheel genai ≈ **4,1 MB** (DirectML, cp314, 0.14.0) [P-sn, S45]; onnxruntime phụ thuộc: UNKNOWN; file ONNX int4 cỡ 2B: UNKNOWN (ESTIMATE ≈ 1–1,5 GB) |
| Định dạng model | GGUF tải sẵn (unsloth, ggml-org, Qwen) hoặc tự lượng tử; mmproj là file riêng | OpenVINO IR. IR int4 dựng sẵn cho Qwen3.5-2B: UNKNOWN (có IR fp16/int8 cho 4B, v1 S13) | ONNX. ONNX dựng sẵn cho Qwen3.5-2B/0,8B: UNKNOWN (U10) |
| Hỗ trợ Qwen3.5 | REPORTED: metadata kiến trúc qwen35 trên repo HF [P-g, S34, S35]; README bản sao dùng ví dụ Qwen3.5 [T]. multimodal.md chính thức không liệt kê Qwen3.5 (Claude C báo; liên kết trực tiếp ở U5), nhưng đó là danh sách model ggml-org đã lượng tử sẵn nên không phải bằng chứng chống lại | Từ 2026.2.0 trên CPU và GPU, cùng Gemma 4 E2B/E4B [P-sn, S42]. **U9 đóng: không cần nightly.** 2026.4.0 thêm MTP speculative decoding cho Qwen3.5 và Gemma 4 [T, mirror] | v0.13.0 thêm Qwen3.5 và Qwen3-VL đa ảnh; v0.14.0 thêm text-only [S16 của v1, không mở lại] |
| Hỗ trợ VLM | Có (libmtmd, `--mmproj`; llama-server/llama-cli/llama-mtmd-cli nhận ảnh, âm thanh, video) [P, S3]. Qwen3-VL: Qwen nêu trong card GGUF [P, S40]. Qwen3.5 + mmproj: REPORTED | Có VLMPipeline (ảnh/video) [T, S21, chỉ là gợi ý]. VLM Qwen3.5 cỡ 2B: UNKNOWN | Có (Qwen3-VL). VLM Qwen3.5-2B: UNKNOWN |
| iGPU UHD 620 (giả thuyết cần đo) | Backend SYCL (Intel GPU) và Vulkan; backend OpenVINO "đang phát triển" [T, README bản sao]; binary Windows sycl/vulkan có [T, wiki]. UHD 620 chạy được hay nhanh hơn CPU: ASSUMPTION. iGPU dùng chung DDR4 nên không tăng băng thông decode | Intel iGPU là đích gốc; danh sách phần cứng GPU gồm Intel UHD Graphics trên Windows 11 [P, S15 của v1]. UHD 620 cụ thể và hiệu năng: UNKNOWN. Dự đoán (ASSUMPTION): có thể giúp prefill, không tăng băng thông decode | DirectML (DX12) dùng được trên UHD 620 về nguyên tắc; ma trận hỗ trợ liệt kê CUDA/DirectML/QNN/ROCm/OpenVINO [T, S17, gợi ý]; hiệu năng UNKNOWN |
| License | MIT [T: ecosyste.ms, gói Alpine, README bản sao; S46]. File LICENSE của repo chưa mở (U7) | Apache-2.0 [P-sn, S43: trích đoạn trang PyPI openvino; Claude C mở trang 2026-11-05 và xác nhận, S51]; openvino-genai: Apache Software License [T: bản sao metadata PyPI và depscope, S44] | MIT [T: depscope, S45; Claude C báo đã thấy trang license NuGet Microsoft.ML.OnnxRuntimeGenai bản 0.9.0 ở review v1, B chưa mở] |
| Trade-off và vai trò | Hệ sinh thái GGUF/quant rộng nhất, đường chính thức cho Gemma 4, nhẹ đĩa; đổi lại kiến trúc mới có rủi ro bug và cần bản build đủ mới; iGPU chưa rõ. **Runtime chính cho M2** | Kernel tối ưu Intel và có đường iGPU; phụ thuộc phiên bản; IR dựng sẵn cỡ 2B/4-bit chưa xác nhận; footprint pip chưa biết. **Runtime phụ** (so iGPU) | pip-only, API ổn định; phải xuất hoặc tải ONNX, chất lượng lượng tử chưa biết; chưa thấy hỗ trợ Gemma 4. **Hoãn** |

**Điều chỉnh so với v1.** v1 đánh giá thấp R2 vì cho rằng cần wheel nightly (từ card S13). Ghi chú phát hành [P-sn, S42] cho thấy Qwen3.5 đã có trong bản release từ 2026.2.0, nên ràng buộc "nightly" không còn đúng và R2 có thể đo như phương án phụ ngay trên bản release.

**R4. Không chọn hoặc chưa đánh giá.**

- **llama-cpp-python:** loại (cần compiler; chỉ có sdist cp314).
- **CTranslate2:** có wheel cp314 (chủ dự án xác nhận ở v1) nhưng chưa thấy bằng chứng hỗ trợ qwen35 hoặc VLM.
- **Ollama/LM Studio:** chưa đánh giá. Trích đoạn tài liệu Unsloth (tìm kiếm 2026-10-26, S47) ghi hiện chưa có GGUF Qwen3.5 nào chạy được trong Ollama vì mmproj tách file riêng, khớp với S23 ở v1 [T]; không dùng Ollama cho VLM Qwen3.5.

**Kế hoạch đo để đóng ô UNKNOWN** (chủ dự án chạy; không tải model):

1. Tải zip llama.cpp Windows CPU; ghi kích thước zip và thư mục giải nén; chạy `--help` ghi lại tên cờ cho ngữ cảnh, mmproj, giới hạn token ảnh, flash-attention, cache prompt (U6, U15, U24).
2. `pip download --only-binary=:all: openvino-genai onnxruntime-genai -d <thư mục tạm>`; ghi dung lượng wheel và xác nhận có wheel cp314; rồi xóa thư mục tạm.

## Phụ lục C — Research card (mỗi card đủ 7 trường; chi phí tính từ D4, ở G = 100 GFLOPS, η = 0,55)

Mốc ngân sách: ≤ ~90 phút máy cho mỗi cấu hình (mốc của TASK-003). Tốc độ prefill dùng: M1 ≈ 19,9 token/s ở G = 100 (39,8 ở G = 200), tức 50,2 s/1.000 token (D4). Tất cả là ESTIMATE, chờ hiệu chỉnh bằng llama-bench ở M2.

**Phạm vi chế độ sinh.** Mọi phép đo ở Phụ lục C dùng chế độ non-thinking với max_new_tokens bị chặn (≤ 96 token). Chế độ thinking nằm ngoài phạm vi: Claude C báo card Qwen khuyến nghị độ dài đầu ra tới 32.768 token cho phần lớn truy vấn (≈ 36 phút mỗi truy vấn ở trần 15 tok/s của M1, ESTIMATE) và nêu 2B dễ rơi vào vòng lặp suy nghĩ [S32].

**Bộ pilot tạm P-60 (dùng chung cho C1, C3 và smoke tiếng Việt ở A6).** 60 câu MCQ ngắn (40 Việt + 20 Anh), tự biên soạn hoặc tái dùng tài liệu chủ dự án có quyền; mỗi câu ghi nguồn gốc và license (chuẩn bị cho AC2 của TASK-003); không dùng dữ liệu học sinh hay cá nhân. Đây không phải benchmark đóng băng: cỡ nằm ở đầu dải 60–100 item của tầng LAPTOP trong phiếu TASK-003. Khi TASK-003 đóng băng tầng LAPTOP thì thay P-60 bằng bộ đó (hoặc dùng P-60 làm hạt giống nếu license đạt) để không soạn hai lần. Smoke 24 câu ở A6 lấy từ cùng nguồn. Công soạn là giờ người, không tính vào giờ máy: ước ≈ 3 giờ (ASSUMPTION: ≈ 3 phút/câu gồm đáp án và đối chiếu nguồn). Với 60 câu, sai số chuẩn của accuracy một model ≈ 6 điểm (CI 95% ≈ ± 12). Khi so hai model (hoặc hai mức lượng tử) trên cùng các câu, độ lệch nhỏ nhất phát hiện được (công suất 80%, α = 0,05) ≈ 2,8·√(d/n), với d là tỉ lệ câu hai bên làm khác nhau: n = 60 cho ≈ 16 điểm (d = 0,2) và ≈ 20 điểm (d = 0,3); n = 100 cho ≈ 12 và ≈ 15 điểm. Mốc 10 điểm chỉ đạt khi d ≲ 0,08 ở n = 60, hợp lý cho hai mức lượng tử của cùng một model (C1) nhưng không cho M1 so với M4 (C3 và so sánh giữa model). Độ dài prompt ≈ 150 token dùng để tính chi phí là ASSUMPTION; tính lại từ số token/từ đo ở A6(iv).

### C1. Thang lượng tử hóa cho Qwen3.5-2B (và 0,8B)

- **Giả thuyết:**
  - H1a: khi bị chặn băng thông, tok/s decode (ESTIMATE) tăng gần tỉ lệ nghịch với kích thước file (trần ở D1).
  - H1b: tồn tại mức bit mà ΔKL và top-1 agreement so với Q8_0 nằm trong ngưỡng do Claude A/C chốt (ASSUMPTION, chưa có). Accuracy trên P-60 chỉ bắt được lệch cỡ ≥ 10 điểm giữa hai mức lượng tử của cùng một model (d ≲ 0,08), không phân giải được chênh 2 điểm.
  - H1c: hybrid có thể nhạy lượng tử hơn dense (tín hiệu gián tiếp yếu [S4]); M4 chạy cùng quy trình để đối chứng.
- **Cơ chế:** weight-only quantization giảm số byte đọc mỗi token (decode bị chặn băng thông), đổi lại sai số trọng số; bản Dynamic đổi một chút dung lượng lấy độ giữ chất lượng.
- **Baseline so sánh:** Q8_0 (2,01 GB) làm tham chiếu; ứng viên Q6_K 1,57, Q5_K_M 1,44, UD-Q4_K_XL 1,34, Q4_K_M 1,28, IQ4_XS 1,17 GB [S34].
- **Metric:** (a) KL(Q8_0 || ứng viên) và top-1 agreement trên N_KL token; (b) accuracy trên P-60, temperature 0; (c) tok/s decode và prefill, RSS đỉnh, kích thước file; (d) CER ảnh (chỉ khi chạy V1, ngoài ngân sách).
- **Phép thử:** qua cổng TASK-001 trước (A5: đĩa ≥ 12 GiB hoặc ổ ngoài; RAM sạch). Tải tuần tự: Q8_0, chạy P-60 và sinh dữ liệu cơ sở cho KL, xóa Q8_0; rồi mỗi ứng viên: tải, chạy KL + P-60 + đo tốc độ, xóa. Cùng prompt và seed; 3 lần lặp đo tốc độ; ghi throttle. N_KL = 2.048 token với đĩa hiện tại, 16.384 khi A5 đạt (U20, D6).
- **Chi phí:** ở G = 100 GFLOPS, ≈ 13,4 phút/mức (N_KL = 2.048; ≈ 81 phút cho 6 mức) hoặc ≈ 29,8 phút/mức (N_KL = 16.384; ≈ 179 phút); ở G = 200 giảm còn khoảng một nửa. Mỗi mức nằm trong mốc 90 phút. Công thức, ràng buộc đĩa và RAM của lượt KL ở D6. Chưa tính công soạn P-60 (≈ 3 giờ người).
- **Rủi ro:**
  - Khả năng phát hiện: P-60 có sai số chuẩn ≈ 6 điểm và độ lệch nhỏ nhất của so sánh cặp ≈ 2,8·√(d/n) (đầu Phụ lục C); với N_KL = 2.048 sai số KL lớn hơn, nên xếp hạng các mức gần nhau (Q5_K_M so với Q6_K) kém tin cậy.
  - Q8_0 làm tham chiếu thì khó tách KL của Q6_K khỏi sai số của chính Q8_0; BF16 làm tham chiếu cần ≈ 4,3 GiB RAM (D6).
  - **VMLU (T6):** chỉ là ứng viên chưa duyệt: có thể đã lọt vào dữ liệu huấn luyện của model 2026 (suy luận, cần kiểm) và vướng AC2 của TASK-003 (license). Thay bằng P-60 hoặc tầng LAPTOP của TASK-003.
  - Dynamic quant có thể chậm hơn trên AVX2 (UNKNOWN).

### C2. Ngữ cảnh, KV, token ảnh và prefix cache trên kiến trúc hybrid

- **Giả thuyết:**
  - H2a: κ = 12 KiB/token (M1) so với 112 KiB/token (M4): ở cùng cỡ file 1,28 GB, hybrid tốt hơn rõ về RAM và trần decode khi n_ctx ≥ 4K. Lượng tử hóa KV tiết kiệm < 0,05 GiB ở 8K với hybrid (ROI thấp) nhưng ≈ 0,44 GiB với dense.
  - H2b: chi phí thật của ngữ cảnh dài và ảnh là thời gian prefill (bị chặn tính toán), không phải RAM.
  - H2c: hạ token ảnh/độ phân giải và tái sử dụng prefix cho system prompt cố định cắt TTFT đáng kể; nhưng lớp hồi quy phải lưu trạng thái tại biên prefix (≈ 19,3 MiB mỗi điểm lưu), nên hiệu quả phụ thuộc runtime có hỗ trợ hay không (UNKNOWN). Hai nguồn yếu của v1 (S24 model card 122B, S21 docs [T]) đã bị bỏ khỏi cơ sở (L7); đây chỉ là giả thuyết cần đo.
- **Cơ chế (L1):**
  1. KV chỉ lớn theo n_ctx ở 6/24 lớp full-attention; trạng thái GDN là hằng số 19,3 MiB.
  2. Prefill chữ có FLOP ∝ token × 2N_không-embedding; ảnh: mỗi vùng 32×32 px thành 1 token LLM nhưng phải qua ViT với 4 patch/token, FLOP ViT = 2·N_vit·P + 4·P²·d·L (D1), nên ảnh đắt hơn chữ cùng số token.
  3. Prefix reuse bỏ tính lại phần chung; với lớp hồi quy cần khôi phục trạng thái đã lưu thay vì cắt KV.
- **Baseline so sánh:** n_ctx 8.192 đặt tường minh, không cache, ảnh hạ về ≤ 1024 px cạnh dài.
- **Metric:** TTFT p50 và min/max (n = 3–5); prefill tok/s; RSS đỉnh; decode tok/s theo mức ngữ cảnh đã đầy; CER OCR theo độ phân giải; chất lượng QA không đổi; η hiệu dụng theo kiến trúc (M1 hybrid so với M4 dense) = FLOP lý thuyết (gồm số hạng n² của D1) ÷ thời gian prefill đo ở (b).
- **Phép thử:**
  - (a) quét prefill 512/1.024/2.048 token × 3 lần;
  - (b) quét ngữ cảnh đã đầy 2K/4K/8K cho M1 và M4: RSS và decode tok/s;
  - (c) quét ảnh 512²/768²/1024² × 3 lần với V1 (V2 nếu RAM cho phép, n_ctx ≤ 4K);
  - (d) prefix: system prompt 1K token lặp 10 lượt, bật/tắt tái sử dụng (tên cờ kiểm bằng `--help`);
  - (e) mọi lần đo phải ghi n_ctx và giới hạn token ảnh đã đặt (T5).
- **Chi phí (T3):** (a) 10.752 token ÷ 19,9 = 540 s = 9 phút; (b) 14.336 token cộng số hạng attention bậc hai (trung bình trên 2K/4K/8K: M1 ≈ +5,5%, M4 ≈ +25%): M1 ≈ 12,7 phút, M4 ≈ 15,3 phút, tổng ≈ 28 phút; (c) (26 + 64 + 126) s × 3 = 648 s ≈ 11 phút; (d) không cache 10 × 51 s ≈ 8,5 phút + có cache ≈ 1,5 phút = 10 phút. Tổng ≈ **58 phút** ở G = 100 (≈ 29 phút ở G = 200). v1 ghi 1–2 giờ nhưng p95 cần ≥ 20 lần chạy: prompt 4K đã 4.000 ÷ 19,9 ≈ 201 s, 20 lần = 67 phút cho một điều kiện, nên không làm p95 ở 4K; chỉ p50 và min/max.
- **Rủi ro:** hành vi cache với trạng thái hồi quy (UNKNOWN); bẫy mặc định (n_ctx 262.144 → KV 3,0 GiB; tối đa 16.384 token/ảnh); đỉnh RAM bộ mã hóa ảnh ở độ phân giải cao (U24); hạ độ phân giải làm tăng CER; MTP speculative decoding không dùng cùng `--mmproj` [S9 của v1].

### C3. Leo thang chọn lọc + xác minh chọn lọc (CORE → HYBRID)

- **Giả thuyết:** độ tin cậy cục bộ (logprob/entropy, hoặc nhất quán giữa 2 lần giải mã) dự báo lỗi đủ tốt để một ngưỡng gửi ≤ X% truy vấn lên API vẫn giữ ≥ Y% chất lượng "luôn-API". X và Y do Claude A đặt sau khi có baseline.
- **Cơ chế:** selective prediction (đường risk–coverage): xếp hạng truy vấn theo độ tin cậy và chỉ leo thang phần nhiều khả năng sai. Với trích xuất/OCR, xác minh bằng ràng buộc cứng (regex, tổng kiểm, khớp chéo hai độ phân giải) thay vì gọi API.
- **Baseline so sánh:** luôn-cục-bộ; leo thang ngẫu nhiên cùng tỉ lệ. "Luôn-API" chỉ là tham chiếu giả định (ASSUMPTION), không gọi.
- **Metric:** accuracy tại coverage 50/70/90%; diện tích dưới đường risk–coverage; tỉ lệ leo thang; chi phí trên mỗi câu đúng (ước tính theo token, không gọi API); latency p95; tỉ lệ "sai nhưng giữ cục bộ".
- **Phép thử:**
  - Văn bản: P-60 (60 câu MCQ ngắn, ≈ 150 token prompt, giải mã ≤ 8 token).
  - Ảnh: 20 ảnh tài liệu công khai hoặc tổng hợp ≤ 768×768 (576 token) với tác vụ trích xuất ngắn (≤ 32 token đầu ra, ví dụ đọc một trường số, ngày hoặc tên); nguồn ảnh có license rõ.
  - Mỗi mục chạy 2 lượt giải mã (seed khác nhau) để lấy độ nhất quán; lưu đặc trưng tin cậy; mô phỏng định tuyến offline. Không đưa dữ liệu học sinh hay cá nhân vào prompt.
  - Ngoài ngân sách (tùy chọn): khớp chéo thêm một lượt ở 512² cho 20 ảnh (thêm ≈ 9 phút ở G = 100). OCR cả trang không thuộc phạm vi: mỗi trang ≥ 500 token đầu ra, riêng giải mã đã ≈ 34 giây trở lên (ESTIMATE, ở trần 14,6 tok/s).
- **Chi phí (T3), G = 100 | G = 200:**
  - Chữ: mỗi lượt ≈ 150 ÷ 19,9 + 8 ÷ 14,6 ≈ 8,1 | 4,3 s; 60 câu × 2 lượt = 972 | 516 s, tức **≈ 16,2 | 8,6 phút**.
  - Ảnh: mỗi lượt ≈ 64 | 32 s prefill (D4) + 32 ÷ 14,6 ≈ 2,2 s giải mã ≈ 66 | 34 s; 20 ảnh × 2 lượt = 2.640 | 1.360 s, tức **≈ 44 | 22,7 phút** (không tái dùng prefill giữa hai lượt; nếu runtime tái dùng được thì ≈ 24 phút ở G = 100, UNKNOWN).
  - Tổng ≈ **60 | 31 phút**, trong mốc 90 phút; chưa tính công soạn P-60.
  - Lịch sử: bản v2 chưa sửa ghi 83 phút nhưng chạy chữ 2 lượt và ảnh 1 lượt, trong khi phép thử nêu 2 lượt cho mọi mục; làm đủ hai lượt cho 40 ảnh và 150 câu thì vượt mốc 90 phút, nên v2.1 cắt còn 20 ảnh và 60 câu. v1 ghi "$0" và bỏ qua giờ máy cho ~100 ảnh (≈ 107 phút).
- **Rủi ro:** model nhỏ hiệu chỉnh tin cậy kém, nhất là ở chế độ thinking; 60 câu và 20 ảnh chỉ đủ kiểm tra đường ống và đặc trưng tin cậy, không đủ ước lượng đường risk–coverage (CI rất rộng, ± ~12 điểm với 60 câu; so sánh cặp M1 với M4 trên cùng 60 câu chỉ phát hiện được chênh ≈ 16–20 điểm, d = 0,2–0,3); chất lượng API chỉ là giả định; cờ lấy logprob của runtime cần kiểm bằng `--help` hoặc tài liệu.

## Phụ lục D — Phân tích độ nhạy (RAM cho model 2 / 3 / 5 GiB và băng thông ×2)

Dữ kiện quyết định, không phải đề xuất mua phần cứng.

### D1. Công thức

- **Ngân sách trọng số:** B_w = RAM_khả_dụng − 0,2 (biên) − (A + R) − KV − S.
  - Hybrid (M1, M2) ở n_ctx = 8.192: A + R = 0,4 (giữa 0,3–0,5), KV = 0,094, S = 0,019 → B_w ≈ **RAM − 0,71 GiB**.
  - Dense κ = 112 KiB/token (M4, V2) ở 8K: KV = 0,875 → B_w ≈ **RAM − 1,5 GiB**.
  - Suy ra B_w (hybrid / dense): 2 GiB → 1,29 / 0,5 GiB; 3 GiB → 2,29 / 1,5 GiB (≈ 2,46 / 1,6 GB); 5 GiB → 4,29 / 3,5 GiB.
- **Decode (trần, ESTIMATE):** tok/s ≤ min( BW ÷ (W_đọc + KV_đọc), η·G ÷ (2·N_act) ).
  - BW = 19,2 GB/s (INFERRED từ một kênh DDR4-2400, theo phiếu) là đỉnh lý thuyết nên các trần ở D3 cao hơn thực tế; khi TASK-001 đo được băng thông bền vững (kiểu STREAM) thì thay vào, không giả định hệ số. W_đọc ≈ kích thước file (xấu nhất); KV_đọc = KV đã đầy (đọc hết mỗi token).
  - N_act = tham số LM gồm đầu ra tied: M1 1,89B; M2 0,76B; M3 4,21B; M4 ≈ 1,71B (1,4B + 0,31B embedding).
- **Prefill chữ (ESTIMATE):** T = n × 2·N_ne ÷ (η·G), với N_ne là tham số không-embedding (embedding chỉ tra bảng, đầu ra chỉ tính cho token cuối). N_ne: M1 1,381B; M2 0,506B; M3 ≈ 3,57B (config 4B do Claude C mở 2026-11-05: hidden 2560); M4 1,4B. Chưa gồm số hạng attention bậc hai: thêm ≈ 2·n²·d_q·L_attn FLOP (mặt nạ nhân quả; d_q = n_head × head_dim = 2048 ở cả M1 và M4, L_attn = 6 ở M1 và 28 ở M4), tức ở n = 2K/4K/8K cộng ≈ +2/+4/+7% (M1) và ≈ +8/+17/+34% (M4); dưới 2K không đáng kể.
- **Prefill ảnh (ESTIMATE):** T = [2·N_vit·P + 4·P²·d_v·L_v + n_img·2·N_ne] ÷ (η·G), với P = (W/16)·(H/16) patch, n_img = P/4 token, N_vit = 0,302B (24 × (4·1024² + 2·1024·4096), từ config [S30]), d_v = 1024, L_v = 24. Giả định ViT dùng attention đầy đủ trên toàn ảnh và (ASSUMPTION) mtmd dùng flash-attention; nếu không thì thêm bộ đệm P² (U24).
- **Giả định:** G ∈ {100, 200} GFLOPS (chưa đo; TASK-001), η = 0,55 (0,4–0,7). G gắn với FP32 của probe trong khi kernel lượng tử dùng số nguyên, nên các số chỉ để định hướng và phải hiệu chỉnh bằng llama-bench ở M2 (T4). η đồng nhất giữa các lớp cũng là ASSUMPTION: 18/24 lớp của M1 là Gated DeltaNet, phần hồi quy có thể chạy dưới hiệu suất GEMM trên CPU, nên prefill M1/M2 có thể chậm hơn D4 trong khi M4 (dense) thì không; C2 phải đo η theo từng kiến trúc.

### D2. Vừa/không vừa theo RAM khả dụng cho model (ESTIMATE; n_ctx = 8.192 trừ khi ghi khác)

Ngưỡng VỪA theo quy tắc biên ở Phụ lục A: ≤ 1,8 / 2,8 / 4,8 GiB cho trần 2 / 3 / 5 GiB. Mỗi cột chỉ có nghĩa nếu RAM khả dụng thật đạt trần tương ứng khi máy sạch; số đo duy nhất hiện có là 0,68–0,76 GiB (D5).

| Phương án | RAM ước tính, GiB | 2 GiB | 3 GiB | 5 GiB |
| --- | --- | --- | --- | --- |
| M2 chữ | 0,9–1,1 | VỪA | VỪA | VỪA |
| M2 + ảnh (mmproj 0,19) | 1,2–1,6 | VỪA | VỪA | VỪA |
| M1 chữ Q4_K_M | 1,6–1,8 | VỪA, sát biên | VỪA | VỪA |
| M1 + ảnh (Q4_K_M + mmproj 0,62) | 2,3–2,7 | VƯỢT | VỪA | VỪA |
| M1 chữ Q8_0 | 2,3–2,5 | VƯỢT | VỪA | VỪA |
| M1 Q8_0 + ảnh | 3,0–3,4 | VƯỢT | VƯỢT | VỪA |
| M4 Q4_K_M @4K | 1,9–2,1 | BIÊN/VƯỢT | VỪA | VỪA |
| M4 Q4_K_M @8K | 2,4–2,6 | VƯỢT | VỪA | VỪA |
| M4 Q4_K_M @16K | 3,2–3,4 | VƯỢT | VƯỢT | VỪA |
| V2 @4K, projector Q8_0 (≈ 0,445 GB, [T] Claude C báo) | 2,3–2,7 | VƯỢT | VỪA | VỪA |
| V2 @4K, projector F16 (ESTIMATE ≈ 0,65–0,82 GB) | 2,5–3,0 | VƯỢT | BIÊN | VỪA |
| V2 @8K, projector Q8_0 | 2,7–3,1 | VƯỢT | BIÊN | VỪA |
| V2 @8K, projector F16 | 2,9–3,5 | VƯỢT | BIÊN/VƯỢT | VỪA |
| M3 Q4_K_M chữ (κ = 32 KiB/token) | 3,15–3,35 | VƯỢT | VƯỢT | VỪA |
| M3 IQ4_XS chữ | 2,9–3,1 | VƯỢT | BIÊN/VƯỢT | VỪA |
| M3 Q4_K_M + ảnh (mmproj 0,63) | ≈ 3,9–4,3 | VƯỢT | VƯỢT | VỪA |
| M3 Q8_0 chữ | ≈ 4,8–5,0 | VƯỢT | VƯỢT | BIÊN |
| X1 Gemma 4 E2B Q4_0 chữ (giả định cả file resident) | ≥ 2,9–3,1 + KV | VƯỢT | VƯỢT | VỪA |
| Qwen3.5-9B Q4_K_M | W ≈ 4,9–5,6 (5,3–6,0 GB, hai nguồn [T] lệch 13%) | VƯỢT | VƯỢT | VƯỢT |

- **2 GiB:** chỉ M2 chắc chắn (chữ và ảnh). M1 chỉ chạy chữ và sát biên. Đường ảnh của M1 cần mmproj nhỏ hơn F16 mà repo unsloth không cung cấp (mmproj Q8_0 không có trong S34), nên chưa có phương án chuẩn.
- **3 GiB:** M1 vừa cả chữ và ảnh nếu giữ lớp Q4; nếu khuyến nghị 3,5 GB của Unsloth đúng thì không (U12), quyết định chờ RSS đo thực. M4 vừa với n_ctx ≤ 8K; V2 vừa @4K với projector Q8_0 (OCR chưa đo) và ở biên @8K.
- **5 GiB:** mở M3 (Q4_K_M, kể cả có ảnh), Gemma 4 E2B Q4_0 và M1 Q8_0 + ảnh. Chọn giữa 4B và 2B tùy chênh chất lượng đo ở TASK-003 so với tốc độ giảm (ESTIMATE: trần decode 7,0 so với 15,0 tok/s; prefill ≈ 130 s so với 50 s/1.000 token).
- **Ngữ cảnh dài:** hybrid giữ KV ≤ 0,375 GiB đến 32K, trong khi M4 (dense) đã 3,5 GiB ở 32K; đây là chênh lệch lớn nhất giữa hai họ kiến trúc trong ma trận.

### D3. Băng thông ×2 (38,4 GB/s)

Trần decode theo băng thông (ESTIMATE; thực tế thấp hơn) và trần theo tính toán:

| Model | File GB | Trần @19,2 GB/s | Trần @38,4 GB/s | Trần tính toán η·G ÷ (2·N_act), G = 100 / 200 |
| --- | --- | --- | --- | --- |
| M2 | 0,533 | 36 tok/s | 72 tok/s | 36 / 72 |
| M1 | 1,28 | 15,0 (13,9 khi 8K đầy) | 30 | 14,6 / 29,1 |
| M4 | 1,28 | 15,0 (11,0 khi 4K đầy; 8,7 khi 8K đầy) | 30 (17,3 khi 8K đầy) | 16,1 / 32,1 |
| V2 (LLM) | 1,11 | 17,3 (9,4 khi 8K đầy) | 34,6 | ≈ như M4 |
| M3 | 2,74 | 7,0 | 14,0 | 6,5 / 13,1 |
| X1 E2B Q4_0 | 2,84 (đọc hết file: cận thận trọng) | 6,8 | 13,5 | UNKNOWN (N hiệu dụng 2,3B) |

- Hai trần bằng nhau ở G_c = 2·BW·N_act ÷ (η·W_đọc). Với M1: G_c ≈ **103 GFLOPS** (khoảng 81–142 theo η 0,7–0,4) ở băng thông hiện tại và ≈ **206** ở băng thông ×2 (v1 ghi 110 và 220).
  - Nếu G bền vững < G_c thì băng thông ×2 gần như không giúp decode; nếu G ≥ ~206 thì decode hưởng gần trọn ×2.
  - Ở G = 100, decode của M1 đã bị chặn bởi tính toán (14,6) ngang trần băng thông (15,0).
  - G chưa đo (UNKNOWN), nên là điểm cần đo trước.
- Prefill và token ảnh chỉ phụ thuộc G, không phụ thuộc băng thông.

### D4. Prefill, tách chữ và ảnh (T4), η = 0,55 (ESTIMATE)

**Chữ, mỗi 1.000 token:**

| Model | N_ne (tỉ) | G = 100 | G = 200 | Khoảng η 0,4–0,7 ở G = 100 |
| --- | --- | --- | --- | --- |
| M2 | 0,506 | ≈ 18 s | ≈ 9 s | 14–25 s |
| M1 | 1,381 | ≈ 50 s | ≈ 25 s | 39–69 s |
| M4 | 1,4 | ≈ 51 s | ≈ 26 s | 40–70 s |
| M3 | ≈ 3,57 (config 4B, Claude C 2026-11-05) | ≈ 130 s | ≈ 65 s | 102–179 s |

Chi phí chữ của v2 thấp hơn v1 khoảng 31% (50 s so với 73 s): v1 dùng N = 2B cho M1, tính cả 0,5B embedding không đi qua phép nhân. Số của M3 dựa trên config 4B do Claude C mở ngày 2026-11-05 (hidden 2560, 32 lớp), sai số ±5%. Các số chưa gồm số hạng attention bậc hai (D1): thêm ≈ +2/+4/+7% (M1) và ≈ +8/+17/+34% (M4) ở 2K/4K/8K.

**Ảnh, mỗi ảnh (V1; token = pixel ÷ 1.024, mỗi token cần 4 patch qua ViT):**

| Ảnh | P (patch) | Token LLM | ViT (TFLOP) | LLM (TFLOP) | G = 100 | G = 200 |
| --- | --- | --- | --- | --- | --- | --- |
| 512×512 | 1.024 | 256 | 0,72 | 0,71 | ≈ 26 s | ≈ 13 s |
| 768×768 | 2.304 | 576 | 1,91 | 1,59 | ≈ 64 s | ≈ 32 s |
| 1024×1024 | 4.096 | 1.024 | 4,12 | 2,83 | ≈ 126 s | ≈ 63 s |
| Trang A4 150 dpi (≈ 1.248×1.760) | 8.580 | 2.145 | 12,42 | 5,92 | ≈ 334 s (5,6 phút) | ≈ 167 s (2,8 phút) |

- Ảnh 768×768 tốn ≈ 64 s. Cùng 576 token chữ chỉ tốn ≈ 29 s theo D4 mới (576 × 50,2 s/1.000), tức ảnh đắt gấp ≈ 2,2 lần vì ViT thêm 1,91 TFLOP; so với D4 cũ của v1 (≈ 42 s) là +52%. Phần bậc hai của ViT còn tăng nhanh theo độ phân giải.
- Trần của bộ xử lý ảnh là 16.384 token/ảnh (S31). Một ảnh ở trần đó có phần attention bậc hai của ViT cỡ 400 TFLOP (ESTIMATE), tức hàng giờ trên laptop này, nên không dùng. Giữ ảnh ≤ 768 px cạnh dài tới khi đo.
- Gemma 4 chọn được ngân sách token ảnh 70–1120 (v1 S2) nên khống chế chi phí dễ hơn; với Qwen3.5 phải khống chế bằng độ phân giải ảnh đầu vào và cờ của mtmd (U24).

### D5. Nếu RAM thực tế đúng như snapshot (0,68–0,76 GiB)

B_w ≈ 0,76 − 0,2 − 0,4 − 0,11 = +0,05 GiB (và −0,03 GiB với 0,68), tức gần bằng 0, nên không phương án nào có chỗ cho trọng số mà không phải phân trang. M2 cần 0,9–1,1 GiB (W 0,50 + KV/S 0,11 + A + R 0,3–0,5) nên chỉ chạy được nhờ mmap/paging, dự báo chậm và không ổn định (ASSUMPTION). Đo RAM sạch trước mọi việc khác (TASK-001). Nếu RAM sạch < 3 GiB thì trần model của CORE phải hạ: tra cột 2 GiB ở D2. Phiếu TASK-004 mô tả RAM khả dụng "thường < 1 GiB", nên D5 có thể là trạng thái thường gặp chứ không phải ngoại lệ; mọi kết luận "vừa 3 GiB" chỉ đúng khi RAM sạch được xác nhận ≥ 3 GiB.

### D6. Chi phí, đĩa và RAM của lượt KL (chuyển từ C1)

- **Công thức chi phí:** t_mức = 1,37 × N_KL ÷ v_prefill + 60 × 8,1 s (P-60) + ≈ 3 phút đo tốc độ (≈ 2 phút ở G = 200), với v_prefill = 19,9 | 39,8 token/s (D4). Hệ số 1,37 vì lượt KL tính logits ở mọi vị trí chấm, nên chạy thêm ma trận đầu ra tied 0,509B: 2 × 0,509B ÷ (2 × 1,381B) = +36,9% so với prefill thuần (D4 không gồm đầu ra).
- **N_KL = 2.048 (số token xử lý), G = 100 | 200:** KL 2,3 | 1,2 phút; P-60 8,1 | 4,3 phút; tốc độ 3 | 2 phút, tức ≈ 13,4 | 7,5 phút/mức; 6 mức (Q8_0 + 5 ứng viên) ≈ 81 | 45 phút.
- **N_KL = 16.384:** KL 18,8 | 9,4 phút, tức ≈ 29,8 | 15,7 phút/mức; 6 mức ≈ 179 | 94 phút (≈ 3,0 | 1,6 giờ).
- **So với v1:** v1 ghi "~2–4 giờ" không nêu độ dài đoạn; với 400 đoạn × 256 token = 102.400 token thì riêng KL đã ≈ 86 phút/mức (≈ 118 phút nếu tính cả đầu ra), tức ≈ 8,6–11,8 giờ cho 6 mức ở G = 100, nên v1 mâu thuẫn với D4.
- **Ràng buộc đĩa và N_KL (U20, ASSUMPTION):** nếu file cơ sở lưu logits toàn bộ từ vựng (≈ n_vocab × 2 byte/token ≈ 0,497 MB/token), N_KL tối đa ≈ (đĩa trống − 2,5 GB) ÷ 0,497 MB/token, với 2,5 GB = Q8_0 2,01 GB + biên ≈ 0,5 GB. Đĩa hiện tại 4,01 GiB (≈ 4,31 GB): N_KL tối đa ≈ 3.600, nên dùng 2.048 token (8 đoạn × 256 token: 4 Việt + 4 Anh; file ≈ 1,0 GB; đỉnh dùng đĩa ≈ 3,0 GB). Khi TASK-001 A5 đạt (≥ 12 GiB ≈ 12,9 GB): N_KL tối đa ≈ 20.900, dùng 16.384 token (64 đoạn × 256 token: 32 Việt + 32 Anh; file ≈ 8,1 GB; đỉnh dùng đĩa ≈ 10,1 GB). Nếu công cụ chỉ lưu top-K hoặc không cần file (kiểm bằng `--help`/mã nguồn trước M2) thì không có ràng buộc này; dự phòng: tính KL trên top-K logprob lấy từ API của server (cận dưới; cần script của TASK-004) hoặc chỉ dùng ΔPPL và top-1 agreement.
- **RAM của lượt KL:** logits fp32 ≈ 0,99 MB mỗi vị trí giữ lại (248.320 × 4 B); cửa sổ 256 token ≈ 0,25 GB, 512 token ≈ 0,5 GB, ngoài A + R (0,3–0,5 GiB). Giữ cửa sổ ≤ 256 token và đo RSS đỉnh của lượt KL. N_KL phải được định nghĩa là số token xử lý hay số token được chấm (U20): công cụ kiểu perplexity có thể chỉ chấm một phần mỗi cửa sổ, khi đó số token chấm (quyết định kích thước file cơ sở và độ chính xác của KL) nhỏ hơn số token xử lý (quyết định thời gian).
- **Quy tắc quyết định và tham chiếu:** đăng ký trước ngưỡng (Claude A chốt) rồi mới chạy; chọn mức có file nhỏ nhất thỏa ngưỡng ΔKL/top-1 agreement và không lệch lớn trên P-60. Khi đĩa và RAM cho phép thì thêm BF16 (3,78 GB) làm tham chiếu trên cùng N_KL; BF16 cần ≈ 4,3 GiB RAM (3,52 + KV/S 0,11 + A + R 0,4 + logits ≈ 0,25), nên chỉ chạy nếu RAM khả dụng đạt hoặc ở máy khác (tầng FULL của TASK-003).

## Phụ lục E — Danh mục nguồn

### E1. Nguồn mở mới hoặc mở lại trong v2 (truy cập 2026-10-26)

- **S29** [P] Cây thư mục Qwen/Qwen3.5-2B (trường license apache-2.0; file LICENSE 11,5 kB; README 62,8 kB) — https://huggingface.co/Qwen/Qwen3.5-2B/tree/main
- **S30** [P] config.json của Qwen3.5-2B (lớp, head, GDN, ViT) — https://huggingface.co/Qwen/Qwen3.5-2B/resolve/main/config.json?download=true
- **S31** [P] preprocessor_config.json (kích thước ảnh, patch, gộp) — https://huggingface.co/Qwen/Qwen3.5-2B/resolve/main/preprocessor_config.json?download=true
- **S32** [P] README.md = card Qwen3.5-2B (bảng điểm, cấu hình lấy mẫu, ngữ cảnh mặc định, license_link) — https://huggingface.co/Qwen/Qwen3.5-2B/resolve/main/README.md?download=true
- **S33** [P-m] Blog Qwen3.5 đăng lại trên Alibaba Cloud Community (17/02/2026): 119 → 201 ngôn ngữ, từ vựng 250k — https://www.alibabacloud.com/blog/qwen3-5-towards-native-multimodal-agents_602894
- **S34** [P-g] unsloth/Qwen3.5-2B-GGUF, cây thư mục (dung lượng, mmproj, license) — https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/tree/main
- **S35** [P-g] unsloth/Qwen3.5-0.8B-GGUF, trang repo (bản sao card, bảng dung lượng) và cây thư mục (mmproj) — https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF ; https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF/tree/main
- **S36** [P-g] unsloth/Qwen3.5-4B-GGUF, cây thư mục — https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/main
- **S37** [P-g] ggml-org/gemma-4-E2B-it-GGUF (dung lượng, license apache-2.0, kiến trúc gemma4) — https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF
- **S38** [P] Qwen/Qwen3-1.7B-GGUF (license, 28 lớp, 16Q/8KV, ngữ cảnh, Q8_0) — https://huggingface.co/Qwen/Qwen3-1.7B-GGUF
- **S39** [P-sn] ggml-org/Qwen3-1.7B-GGUF (Q4_K_M, Q8_0, F16, license; chỉ trích đoạn tìm kiếm) — https://huggingface.co/ggml-org/Qwen3-1.7B-GGUF
- **S40** [P] Qwen/Qwen3-VL-2B-Instruct-GGUF (dung lượng, license, OCR 32 ngôn ngữ, b6907) — https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF
- **S41** [T] Bản chép bảng 119 ngôn ngữ của Qwen3 — https://dev.to/projedefteri/qwen3-hybrid-thinking-and-superior-performance-in-119-languages-proje-defteri-56d2 ; [P-sn] báo cáo kỹ thuật Qwen3 (29 → 119) — https://arxiv.org/html/2505.09388v1
- **S42** [P-sn] Ghi chú phát hành OpenVINO (2026.2.0, 2026.3.0; chỉ trích đoạn tìm kiếm) — https://github.com/openvinotoolkit/openvino/releases ; https://github.com/openvinotoolkit/openvino/releases/tag/2026.3.0 ; [T] 2026.4.0 — https://newreleases.io/project/github/openvinotoolkit/openvino/release/2026.4.0
- **S43** [P-sn] PyPI openvino 2026.4.1 và 2026.3.0 (Apache-2.0, wheel cp314 win_amd64; trích đoạn) — https://pypi.org/project/openvino/2026.4.1/ ; https://pypi.org/project/openvino/2026.3.0/
- **S44** [T] openvino-genai: bản sao metadata PyPI — https://simple-repository.app.cern.ch/project/openvino-genai ; https://mcp.depscope.dev/pkg/pypi/openvino-genai ; kích thước runtime Windows — https://pub.dev/packages/openvino_genai_windows
- **S45** [P-sn] PyPI onnxruntime-genai-directml 0.14.0 (wheel cp314 win_amd64 4,1 MB) — https://pypi.org/project/onnxruntime-genai-directml/0.14.0/ ; [T] license MIT, 0.13.2 — https://mcp.depscope.dev/pkg/pypi/onnxruntime-genai
- **S46** [T] llama.cpp: license/đóng gói — https://summary.ecosyste.ms/projects/124144 ; https://pkgs.alpinelinux.org/package/v3.24/community/x86_64/llama.cpp-libs ; asset Windows và b11081 — https://github.com/feder-cr/jev/wiki/llama-cpp-on-windows ; lệnh winget và `llama serve` lấy từ trích đoạn HF tự sinh trên trang S35 [P-g]; tôi không đọc lại được trang đó lần nữa để chép nguyên văn, nên Claude C nên mở S35 kiểm
- **S47** [T-vendor] Unsloth, hướng dẫn Qwen3.5 (trích đoạn: bộ nhớ khuyến nghị, ghi chú Ollama) — https://unsloth.ai/docs/models/qwen3.5.md
- **S48** [T] Đối chiếu chéo dung lượng/kiến trúc — https://huggingface.co/prithivMLmods/gemma-4-E2B-it-GGUF ; https://huggingface.co/Hanish/quill-models ; https://huggingface.co/cstr/qwen3-vl-2b-crispembed-gguf
- **S49** [P, do Claude C mở 2026-11-05; B chưa mở] Trang model Qwen/Qwen3.5-0.8B: trường license apache-2.0 kèm liên kết tới file LICENSE.
- **S50** [P, do Claude C mở 2026-11-05; B chưa mở] Repo Qwen/Qwen3.5-4B: license apache-2.0, file LICENSE 11,5 kB; config.json: hidden 2560, FFN 9216, 32 lớp (8 lớp full-attention), 16 Q-head, 4 KV-head, head_dim 256.
- **S51** [P, do Claude C mở 2026-11-05; B chưa mở] Trang PyPI openvino 2026.4.1: wheel cp314 win_amd64 nặng 85,0 MB; giấy phép Apache-2.0 (bổ sung cho S43).
- **S52** [P, do Claude C mở 2026-11-05; B chưa mở] File LICENSE của Qwen/Qwen3.5-2B: văn bản Apache-2.0 chuẩn (đường dẫn qua license_link trong S32).

### E2. Nguồn của v1 (truy cập 2026-10-25) và tình trạng ở v2

- **Giữ làm [P]:** S1 (nay mở lại qua S29–S32); S2 (thẻ họ Gemma 4, trang 12B: https://huggingface.co/google/gemma-4-12B); S3 (multimodal.md: https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md; Claude C mở nguyên trang ở review v1 và báo kết quả khớp); S12–S16 (OpenVINO, ORT GenAI; bổ sung S42–S43, S45; S16 không mở lại); S18 (VMLU: chỉ còn là ứng viên chưa duyệt).
- **Hạ xuống đối chiếu chéo [T]:** S5–S8 và S25 (dung lượng nay lấy từ S34–S37); S9, S10, S11 (MTP, ngày phát hành).
- **Hạ xuống gợi ý, không làm cơ sở nhận định (L7):** S17, S21, S20 (README bản sao; thay bằng S46), S23, S28.
- **Bỏ khỏi cơ sở:** S22 (bản fine-tune 9B; 9B chỉ còn là ghi chú [T] ở D2) và S24 (card 122B từng dùng cho H2c).
- **Bác bỏ (mức metadata):** S27 (mâu thuẫn với metadata license của S37 [P-g]; Claude C báo card Google 12B và E4B cũng ghi Apache-2.0 nhưng chỉ qua trích đoạn tìm kiếm; card E2B-it và trang license Google chưa ai mở).
- **Không đổi:** S19 (MiniCPM5, [T]); S26 không dùng.

## Phụ lục F — Hiệu chỉnh số liệu v1 → v2

| Mục | v1 | v2 | Nguồn |
| --- | --- | --- | --- |
| Qwen3.5-2B Q4_K_M | ≈ 1,19 GB hoặc ≈ 1,3 GB [T] (dùng 1,21 GiB) | 1,28 GB = 1,19 GiB | S34 |
| Qwen3.5-2B mmproj F16 | ≈ 637 MB, 0,59 GiB [T] | 668 MB = 0,62 GiB | S34 |
| Qwen3.5-2B Q8_0 | ≈ 1,9 GiB [T] | 2,01 GB = 1,87 GiB | S34 |
| Qwen3.5-2B BF16 | ≈ 3,6 GiB [T] | 3,78 GB = 3,52 GiB | S34 |
| mmproj Q8_0 của 2B | ≈ 348 MiB (bản fine-tune [T]) | không có trong repo unsloth | S34 |
| Qwen3.5-0.8B mmproj | UNKNOWN | F16 205 MB (0,19 GiB) | S35 |
| UD-Q4_K_XL (U2) | UNKNOWN | 2B 1,34 GB; 0,8B 559 MB; 4B 2,91 GB | S34–S36 |
| Qwen3.5-4B Q4_K_M | ≈ 2,6 GB (bản fine-tune [T]) | 2,74 GB (IQ4_XS 2,48 GB) | S36 |
| Qwen3.5-4B mmproj | UNKNOWN | F16 672 MB | S36 |
| Gemma 4 E2B Q4_K_M | ≈ 3,1 GB [T] | ggml-org không có Q4_K_M; Q4_0 2,84; Q8_0 4,97; BF16 9,31 GB | S37 |
| Công thức prefill | N = số tham số (2B cho M1) | N không-embedding (1,381B) và ViT riêng cho ảnh | S30, S34 |
| Prefill M1 / 1.000 token, G = 100 | ≈ 73 s | ≈ 50 s (chữ); ảnh 768² ≈ 64 s | D4 |
| Prefill M2 / M3 | ≈ 29 s / ≈ 145 s | ≈ 18 s / ≈ 130 s | D4 |
| G_c | ≈ 110 / 220 GFLOPS | ≈ 103 / 206 | D3 |
| Token ảnh Qwen3.5 (U15) | UNKNOWN | 1 token / 32×32 px; 64–16.384 token/ảnh | S31 |
| Ngữ cảnh mặc định | không nêu | 262.144 → KV 3,0 GiB | S32, A1 |
| Cần OpenVINO nightly (U9) | "cần wheel nightly" | không cần: Qwen3.5 từ 2026.2.0 | S42 |
| License runtime | UNKNOWN | OpenVINO Apache-2.0 [P]; ORT GenAI MIT; llama.cpp MIT [T] | S43–S46 |
| License M2, M3, E2B | suy từ họ | đọc từ metadata repo | S35–S37 |
| Chi phí C1 | "~2–4 giờ", không nêu độ dài đoạn | ≈ 13,4 phút/mức (≈ 81 phút cho 6 mức) với N_KL = 2.048; ≈ 29,8 phút/mức (≈ 179 phút) với N_KL = 16.384 (đã gồm hệ số 1,37 của ma trận đầu ra); bộ P-60 thay bộ ≥ 150 câu | C1 |
| Chi phí C2 / C3 | "1–2 giờ" / "$0" | 58 phút (đã gồm số hạng n²) / 60 phút (G = 100; C3 gồm 60 câu và 20 ảnh, 2 lượt) | C2, C3 |
| Bộ MCQ pilot | không có | P-60: 60 câu (40 Việt + 20 Anh), công soạn ≈ 3 giờ người (ASSUMPTION) | C |
| Nhãn nguồn | [P] cho mọi repo | [P-g] cho repo của bên chuyển đổi; S42, S43, S45 là [P-sn] | E |
| STATUS | DONE_V1_WITH_GAPS | IMPLEMENTED | HANDOFF |

Hết tài liệu v2.2.
