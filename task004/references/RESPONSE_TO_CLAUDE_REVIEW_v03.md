# Phản hồi review TASK-003 - v0.3

Ngày: 2026-11-03. Trạng thái: **REVISED_PENDING_REVIEW**, không phải APPROVED. Đây là vòng sửa thứ 2 của yêu cầu hiện tại.

Mình chấp nhận kết luận REQUEST_CHANGES với v0.2. Hai lỗi chính là cổng subgroup nhỏ mẫu quá chặt và decision matrix thiếu phân biệt stage/run status. Bản v0.3 đã sửa hai phần này, bổ sung kiểm tra thống kê và xử lý từng finding dưới đây. Các thông số chưa đo thật vẫn được giữ là chưa xác minh.

## 1. Baseline và bằng chứng đầu vào

| Artifact | SHA-256 đầy đủ |
| --- | --- |
| Ticket người dùng đính kèm `(2)` | `27cb47fed77b5af6f300c6f3000f360c2505d84fc088684b0fe2f91b7d98a3c0` |
| Spec v0.2 được review | `89ec037b8a371d1d786b42ac91cf10912a209db0cdb6274a114e4ac4ccf352c5` |
| Handoff v0.2 được review | `3fed490125a864fd6f646fd59316945610ead03b2830a8a515362ed8649b2abc` |
| File phản hồi Claude người dùng gửi | `3e668f4f4ee58cab870e7e487cdcc10ef93de5cc60aa3edb3bd5eec8f3a3546c` |

Ba fingerprint đầu khớp prefix/suffix reviewer ghi. Với ticket, chưa có full hash từ bản reviewer giữ nên chưa tuyên bố byte-compare hoàn tất. Đề nghị reviewer đối chiếu full SHA trên, không cần chủ dự án đoán từ filename.

## 2. Đáp ứng từng finding

| Finding | Xử lý v0.3 | Trạng thái phần thiết kế |
| --- | --- | --- |
| F1 | LAPTOP dùng point screen≥57/80; subgroup/VI-EN/auxiliary chỉ chẩn đoán; ≥48/80 đủ điều kiện xem xét FULL. Thêm bảng operating characteristics | Đã sửa, chờ reviewer kiểm |
| F2 | Decision matrix 14 hàng ưu tiên, có stage/run_status/reason/campaign_status; OOM kiểm trước SMOKE; incomplete không PROMOTE; retry tối đa1; trạng thái BLOCKED rõ | Đã sửa |
| F3 | 6 JSON item SMOKE có O≤48, L≤128; 6 câu ngắn O≤8,L≤96; tính lại9.06 phút | Đã sửa budget; **đếm tokenizer thật còn OPEN** |
| F4 | Chạy bridge cùng80/92 item hai host, pin weights/quant/config; đòi100% canonical task fields và pass vector khớp; không gọi finite bridge là chứng minh tương đương tuyệt đối | Đã thiết kế; chưa chạy |
| F5 | Người B giải blind100% corpus; agreement≥95% tổng/≥90% nhóm, unresolved0; trigger gold errors; human reference phía trên; quy trình revision sau số đo | Đã thiết kế; chưa có nhân sự/corpus |
| F6 | Khóa singleton cluster; bổ sung bootstrap power/test-size audit; đổi primary paired test thành McNemar exact để khớp MDE; bootstrap chẩn đoán | Đã sửa phương pháp, cần review lại |
| F7 | Bảng lý do riêng từng floor; phân biệt chance, usefulness và policy; sàn nhóm cứng chuyển sang FULL; không tự gọi AC5 đã đạt | Đã sửa |
| F8 | Ghi cả comment MIT của tác giả và ACCORD; CSQA HOLD; phân biệt A-E/EN với A-D; notice thành file riêng có hash | Đã xử lý registry; **không tuyên bố license đã clear** |
| F9 | Resource claim cần3 run mỗi A/B, thứ tựABBAAB, cooldown và variability; không nằm trong budget một run | Đã thiết kế; chưa đo |
| F10 | 1057 item/141 ảnh; Stage A137 và Stage B920; khoảng143-311 giờ-người; vai trò soạn/review/adjudication, chính sách LLM hỗ trợ | Đã thêm ước tính và giới hạn |
| F11 | difficulty/difficulty_basis trong schema+hash; quota theo task×language, integer rounding rõ | Đã sửa |
| F12 | Reviewer giữ receipt root/criteria/config trước run; git signed tag không tự là trusted timestamp | Đã thiết kế; chưa có receipt |
| F13 | Mục9.1 riêng: token VI/EN, thinking-off, option balance, renderer sensitivity, GQ span, OCR readability, exposure/template leak | Đã thêm |
| F14 | Tính full ticket hash, khớp fingerprint rút gọn của reviewer | **Còn đối chiếu full hash phía reviewer** |
| F15 | Chốt hai vòng; phân biệt API model với cloud compute nội bộ; nhãn bằng chứng không tự nâng; DEV budget; unsupported denominator; semantic/template checks; bỏ trùng72.14 | Đã làm rõ |

“Đã sửa” ở đây nghĩa là đã chỉnh văn bản và phép tính thiết kế, chưa đồng nghĩa reviewer đã chấp nhận hoặc implementation đã qua test.

## 3. Các thay đổi định lượng chính

### Cổng LAPTOP

Tái tạo 200000 dataset mỗi true-p, group sizes và language quotas v0.2, chưa gồm auxiliary/resource:

| True accuracy đồng đều | Qua tất cả cổng cũ | Qua point screen mới≥57/80 | Đủ điểm để xem xét FULL≥48/80 |
| --- | ---: | ---: | ---: |
| 70% | 4.53% | 45.79% | 97.89% |
| 75% | 14.81% | 81.81% | 99.90% |
| 80% | 34.22% | 97.83% | 99.999% |
| 85% | 60.28% | 99.95% | >99.999% |
| 90% | 84.32% | >99.999% | >99.999% |

Ngưỡng mới chỉ là sàng lọc/provisional. Đạt57/80 không tự chứng nhận population floor60%. Tất cả subgroup và auxiliary vẫn được báo; chúng trở thành cổng cứng khi FULL có120-160 câu/nhóm. Candidate48-56/80 có thể lên FULL, không cần chạy lại LAPTOP để thử vận may.

### SMOKE và DEV

- SMOKE mới: `120 + 6*(96/10+8/3+2) + 6*(128/10+48/3+2) + 3*(288/10+16/3+15+2) = 543.8 s = 9.06 phút`.
- LAPTOP text+ảnh không đổi:3851.87s =64.20 phút.
- SMOKE+LAPTOP mới:4395.67s =73.26 phút.
- Stress LAPTOP+25% input:4328.67s =72.14 phút, khác đại lượng trên.
- DEV24 text+6 ảnh có budget riêng, cận theo caps đã nêu khoảng29.18 phút ở tốc độ chậm. Không nằm trong64.20 phút.

Không có tokenizer candidate/task002 trong đầu vào hoặc thư viện tokenizer cài sẵn. Vì vậy **F3 chưa khép phần thực nghiệm**. v0.3 bắt buộc báo cáo token_feasibility thật trước freeze; không lấy tokenizer không liên quan hoặc ký tự/token giả định để ghi PASS.

### Bootstrap và lựa chọn primary test

Thêm audit5000 outer datasets/case, q=.30,12 strata nhóm×ngôn ngữ, finite bootstrap10000, nearest-rank quantiles. Lưu tham số, seed, versions và kết quả trong `TASK003_NUMERICAL_AUDIT_v03.json`. Phép tích phân conditional bootstrap bằng phân phối tổng dấu đã kiểm chéo với polynomial convolution trực tiếp, max difference khoảng2.36e-16 ở case kiểm tra.

Ở80 singleton, delta16pp cho power khoảng80.07%, nhưng null rejection rate khoảng5.83%. Nếu80 hàng chỉ là40 cluster lặp đôi, null rejection khoảng9.10%, và delta17.6pp chỉ có power khoảng65.46%. Ở800 singleton, MDE theo grid khoảng5.5pp, null rejection khoảng5.06%. Đây là **tự tính, chưa được reviewer tái tạo**, không phải số đo model. Sự khác biệt với mô phỏng reviewer có thể do phân tầng và quantile rule; các tham số hiện được nêu tường minh để so lại.

Vì percentile bootstrap nhỏ mẫu không giữ alpha tốt trong stress case, v0.3 không tiếp tục dùng nó làm cổng chính. Thiết kế điểm chính yêu cầu singleton clusters và dùng **McNemar exact** làm paired test, cùng giả định exchangeability ghi rõ. Bảng MDE exact cũ vì thế khớp test chính. Bootstrap dùng xem sensitivity; nếu mâu thuẫn hoặc có phụ thuộc thì giữ experimental và rà lại thiết kế. Không dùng N hàng thay N tình huống độc lập.

Cổng absolute quality FULL dùng lower bound Hoeffding cho trung bình biến độc lập bị chặn, không yêu cầu đồng phân phối. Margin text800=.04327; ảnh120=.11172. Điều kiện image L≥.65 và point≥.75 thực tế cần92/120. Đây là bound bảo thủ với giả định độc lập, không miễn trừ kiểm family/template.

### Đánh đổi mới cần reviewer chú ý

Đường resource promotion đòi cả ba block tái lập và non-inferiority3pp. Bound paired Hoeffding bảo thủ tại N800 có margin8.65pp, nên hai model ngang chất lượng chưa đủ chứng minh NI3pp; cần≥6658 item để margin≤3pp khi delta=0. v0.3 **không hứa FULL800 đủ cho claim này**. Nếu không có ngân sách xác nhận lớn hơn, giữ resource result là experimental. Reviewer có thể đề xuất phương pháp paired NI hiệu quả hơn trong ticket thống kê tiếp nối, nhưng không được thay bằng “p không significant nghĩa là tương đương”.

## 4. Tình huống decision để reviewer kiểm lại

Đây là walkthrough thiết kế bằng tay, không phải test runner đã triển khai.

| Tình huống | Kết quả bắt buộc |
| --- | --- |
| SMOKE OOM; preflight đủ, log chứng minh do candidate | REJECT cấu hình, không dừng ở dòng KEEP_SMOKE |
| SMOKE đầy đủ, quality thấp nhưng không lỗi hard | KEEP_EXPERIMENTAL, cho phép LAPTOP |
| Preflight fail hai lần sau một lần khắc phục | decision RETRY + campaign BLOCKED_BY_HARDWARE, không tự thử lần3 |
| Hết90 phút, chưa đủ câu, không phân loại được nguyên nhân | RETRY + BLOCKED_UNRESOLVED, không chấm phần đã xong để PROMOTE |
| LAPTOP60/80, resource đạt, chưa có FULL, chưa có baseline | PROMOTE scope provisional, không confirmed |
| LAPTOP52/80, resource đạt, SO thấp | KEEP_EXPERIMENTAL + FULL_ELIGIBLE; SO thấp không cắt đường lên FULL |
| FULL đủ quality nhưng bridge sai một canonical tool argument | KEEP_EXPERIMENTAL cho local; FULL quality chỉ gắn host đã chạy |
| Resource median giảm20% nhưng một block không đạt | KEEP_EXPERIMENTAL, không chọn median bỏ qua biến thiên |
| Model ngang baseline, N800, muốn claim NI3pp | Bằng chứng NI chưa đủ theo bound mặc định; không resource-PROMOTE |

## 5. License và bằng chứng cần tránh diễn giải quá mức

Comment Jonathan Herzig ngày2020-09-25 ở issue#5 có nội dung xác nhận MIT, phiên này mở được: https://github.com/jonathanherzig/commonsenseqa/issues/5 . ACCORD phụ lụcI.1, trangPDF29, ghi nhận không thấy license CSQA tính đến2024-10-14: https://aclanthology.org/2025.naacl-long.193.pdf . Registry giữ cả hai; không phán quyết lại pháp lý của dataset dẫn xuất trong task này. CSQA tiếp tục HOLD.

Notice riêng thay anchor dễ hỏng. Nó chỉ áp dụng cho đóng góp nguyên gốc mà contributor có quyền và đã đồng ý; chưa có permission record thì chưa được nhập freeze. Không coi việc tạo file notice là đã lấy đủ sự đồng ý của mọi người.

## 6. Gói gửi lại và việc còn mở

Gói có5 file: spec v0.3, HANDOFF đúng17 trường, phản hồi này, notice, numerical audit JSON. Không có implementation benchmark/model code. Các công thức và pseudocode đủ cho reviewer tái tạo; không giao scratch arithmetic thành harness vì ticket cấm mở rộng code triển khai.

Nhờ Claude C kiểm lại trước: §6 decision/eligibility, §5 đổi primary test và bound, §3.3 token feasibility chưa đo, §2.3 gold/labor, §2.2 CSQA HOLD. Full hash ticket đã cung cấp để giải quyết F14.

Kết luận hiện tại: **đã sửa thiết kế, chưa APPROVED; chưa thể freeze hoặc chạy baseline**. Tokenizer/hardware, corpus/gold/permissions, bridge và resource repeat là các kiểm tra thực thi tương lai, không được đánh dấu xong bằng sửa văn bản. Không tự động gửi gói này cho người khác.
