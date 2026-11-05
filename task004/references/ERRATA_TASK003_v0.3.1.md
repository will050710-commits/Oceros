# Errata TASK-003 v0.3.1, sau review vòng 2

Ngày2026-11-04. Áp lên spec v0.3 SHA-256 `27081c85020e4526ca9b1a1dab3941e2f6a340b0709528fe7f5a0d5bb2675037` (79084 byte,613 dòng). Không mở vòng sửa thiết kế thứ ba.

**Trạng thái:** Claude C duyệt v0.3 có điều kiện: APPROVE_DESIGN_WITH_EXECUTION_CHECKS. Đây là REPORTED từ review chủ dự án cung cấp. E1-E4 đã được áp vào spec hiện hành; reviewer chưa kiểm errata. **NOT_FROZEN, chưa baseline, chưa APPROVED/FROZEN.**

## Các sửa bắt buộc

| Mục | Sửa trong spec | Bằng chứng/giới hạn |
| --- | --- | --- |
| E1 | §6.2.2, §6.3: LAPTOP hợp lệ/hoàn chỉnh, đủ resource, k≤39 => REJECT / COMPLETE_FOR_CONFIG / QUALITY_BELOW_FLOOR | Wilson U(39)=.59506666<.60, U(40)=.60702585; false reject p=.70 là0.00567268% |
| E2 | Veto provisional nếu một trong sáu nhóm text<1/3, hoặc một nhánh HC có0/6 strict pass; eligibility FULL không bị veto | Cần phần HC bổ sung vì always-answer đạtHC6/12, không bị nhóm<1/3 chặn. False veto cuối1.0935% ởp=.70, .2540% ởp=.75, .0429% ởp=.80 |
| E3 | §6.1-6.2.3: SO-strict FULL100→96/120, parse110 giữ nguyên; thêm bảng chính/phụ/ảnh và sensitivity | Với R,p=.85: text74.2136→94.4210%; text+ảnh mới93.8802%. Ngưỡng mục tiêu90% đạt cảR và parse=.95. Không bảo đảm cho mọi profile có cùngp |
| E4 | §6.3: bỏ hàng incomplete trùng; thống nhất walkthrough một retry tối đa | Hết90 phút/cause-unresolved: attempt0 RETRY_PENDING; attempt1 còn unresolved BLOCKED_UNRESOLVED |

Các bảng dưới là phép tính độc lập từ công thức và ngưỡng, không dùng script của reviewer. Exact và MC mới đối chiếu lẫn nhau. Không có số đo model hay tính lại bootstrap v0.3 trong errata này; audit bootstrap cũ giữ nguyên, reviewer đã báo tái tạo.

## Tái tạo bảng LAPTOP

| p đồng đều | v0.3 công bố: mọi gate v0.2 (MC) | Tái tạo exact mọi gate v0.2 | MC mới (500000) | Point≥57 exact | FULL≥48 exact | Point + veto cuối exact |
| --- | --- | --- | --- | --- | --- | --- |
| 0.70 | 4.53% | 4.55% | 4.49% | 45.791% | 97.88607% | 45.732% |
| 0.75 | 14.81% | 14.71% | 14.66% | 81.805% | 99.89567% | 81.742% |
| 0.80 | 34.22% | 34.11% | 34.02% | 97.833% | 99.99885% | 97.806% |
| 0.85 | 60.28% | 60.25% | 60.18% | 99.951% | 100.00000% | 99.946% |
| 0.90 | 84.32% | 84.37% | 84.31% | 100.000% | 100.00000% | 100.000% |

Exact gate v0.2 dùng convolution hai biến theo VI/EN, đúng sàn từng nhóm, ngôn ngữ và tổng. Exact point+veto dùng convolution PMF theo nhóm và liệt kê hai nhánh HC. “Point + veto” là xác suất qua quality screen provisional, chưa gồm resource hay ảnh; veto không giảm cột FULL≥48. Các xác suất99.999... làm tròn không phải1 tuyệt đối.

## REJECT và veto

| p thật đồng đều | P(REJECT), exact |
| --- | --- |
| 0.25 | 99.999869% |
| 0.40 | 95.550294% |
| 0.50 | 45.553606% |
| 0.60 | 2.712356% |
| 0.70 | 0.005673% |
| 0.75 | 0.00004174% |
| 0.80 | 0.00000005% |

| p đồng đều | Chỉ nhóm <1/3 | Cuối: thêm HC 0/6 | Nếu dùng nhóm <1/2 |
| --- | --- | --- | --- |
| 0.70 | 0.9859% | 1.0935% | 18.8994% |
| 0.75 | 0.2135% | 0.2540% | 6.9857% |
| 0.80 | 0.0314% | 0.0429% | 1.8425% |
| 0.85 | 0.0026% | 0.0047% | 0.3005% |
| 0.90 | 0.0001% | 0.0003% | 0.0213% |

“Cuối” dùng strict pass ở cả nhánh HC trả lời được và không nên trả lời, mỗi nhánh6 câu. Các tỷ lệ veto là vô điều kiện. Không dùng <50%, không áp sàn1/3 lên nhóm ảnh4 câu. Công thức exact: no-veto nhóm = SF(5;16,p)^2 SF(3;12,p)^4. Veto cuối thay một SF(3;12,p) bằng tổng BinPMF(a;6,p)BinPMF(u;6,p), a,u≥1,a+u≥4. Xác suất vừa point≥57 vừa không veto nằm trong bảng LAPTOP.

## FULL cổng chính, exact

| p đồng đều | Text≥560/800 | Mọi sàn nhóm v0.3 | SO≥100/120 | Mọi sàn nhóm v0.3.1 | SO≥96/120 | Ảnh≥92/120 | Ảnh92 + mỗi nhóm24/40 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.70 | 51.743% | 0.001% | 0.060% | 0.017% | 0.911% | 6.512% | 6.505% |
| 0.75 | 99.941% | 0.583% | 1.934% | 3.664% | 12.166% | 38.207% | 38.180% |
| 0.80 | 100.000% | 18.480% | 21.464% | 47.726% | 55.434% | 84.770% | 84.745% |
| 0.85 | 100.000% | 74.222% | 74.432% | 94.453% | 94.720% | 99.444% | 99.441% |
| 0.90 | 100.000% | 99.206% | 99.206% | 99.969% | 99.969% | 99.999% | 99.999% |

Tích sáu sàn nhóm không chứa tổng/ngôn ngữ/cổng phụ. Giá trị74.222% mọi nhóm ởp=.85 thấp hơn SO riêng74.432%; đây là chi tiết cần tách trong bảng reviewer. Không có mâu thuẫn bản chất với kết luận SO là bottleneck.

## FULL gồm cổng phụ, MC500000 mỗi profile

R: strict-p đồng đều; parse98%; GQ unsupported2% trên toàn160; HC false assertion3% trên60 unanswerable, refusal3% trên60 answerable. Mỗi lỗi phụ là tập con strict-fail trong mô hình multinomial, không độc lập với strict score. Cùng p không xác định được các tỷ lệ phụ, vì vậy kết luận chỉ có điều kiện theoR.

| p strict | Text chính + ngôn ngữ cũ / mới | Text mọi gate cũ / mới | Text + ảnh mọi gate mới |
| --- | --- | --- | --- |
| 0.70 | 0.001% / 0.013% | 0.001% / 0.013% | 0.001% |
| 0.75 | 0.583% / 3.662% | 0.582% / 3.660% | 1.371% |
| 0.80 | 18.448% / 47.841% | 18.440% / 47.823% | 40.567% |
| 0.85 | 74.246% / 94.462% | 74.214% / 94.421% | 93.880% |
| 0.90 | 99.193% / 99.967% | 99.151% / 99.924% | 99.923% |

| Thay đổi tại p=.85, còn lại như R | Text mọi gate mới | Text + ảnh mọi gate mới |
| --- | --- | --- |
| parse=.90 | 33.497% | 33.299% |
| parse=.95 | 91.834% | 91.317% |
| unsupported=.10 | 6.357% | 6.323% |
| false assertion=.15 | 67.773% | 67.396% |
| parse=.90, unsupported=.10, false assertion=.15 | 1.612% | 1.603% |

Mục tiêu thiết kế: tạip=.85, cả CORE và VLM quality có lower95% Monte Carlo≥90% trongR và sensitivity parse95%. R: CORE94.421% [94.357,94.484], VLM93.880% [93.813,93.946]; parse95%: CORE91.834% [91.758,91.909], VLM91.317% [91.239,91.395]. Các khoảng này chỉ đo precision Monte Carlo. Sàn SO96/120=80% giữ semantic gate và vượt mục tiêu; không chuyển SO thành report-only. Lower95% là Wilson hai phía trên số dataset mô phỏng qua cổng, không CI năng lực model.

Chưa tính runtime/resources, permission/gold, bridge, exposure, so baseline hay NI, nên không gọi đây là xác suất PROMOTE cuối. Không suy profile đồng đều chứng minh fairness/ngôn ngữ hay corpus thật độc lập. Các stress xấu còn fail mạnh có chủ đích; không nới các cổng phụ để làm mọi profile đạt90%.

## Walkthrough thay phần mâu thuẫn của RESPONSE v0.3

Các case giả định input/scorer hợp lệ và resource đạt trừ khi ghi khác. Đây là walkthrough tài liệu, không phải test chạy harness.

| Case | Kết quả hiện hành |
| --- | --- |
| SMOKE đầy đủ không hard-fail | KEEP_EXPERIMENTAL / READY_FOR_LAPTOP |
| Candidate OOM có log quy nguyên nhân, kể cả SMOKE | REJECT / COMPLETE_FOR_CONFIG |
| LAPTOP đủ80, k=20 hoặc39 | REJECT / COMPLETE_FOR_CONFIG / QUALITY_BELOW_FLOOR |
| LAPTOP k=40 hoặc47 | KEEP_EXPERIMENTAL / NO_FULL_SLOT_CURRENT_CAMPAIGN |
| LAPTOP k=48-56 | KEEP_EXPERIMENTAL / FULL_ELIGIBLE nếu resource đạt |
| SO0/12, nhóm khác hoàn hảo, tổng68 | KEEP_EXPERIMENTAL / FULL_ELIGIBLE; CATASTROPHIC_SUBGROUP |
| Always-answer, HC nhánh không nên trả lời0/6, tổng74 | KEEP_EXPERIMENTAL / FULL_ELIGIBLE; HC veto |
| Always-abstain, HC nhánh trả lời được0/6, tổng74 giả định các nhóm khác hoàn hảo | KEEP_EXPERIMENTAL / FULL_ELIGIBLE; HC veto |
| k≥57, không veto, image≥9 nếu VLM, chưa có baseline cần thay | PROMOTE / PROVISIONAL_LOCAL_BASELINE; FULL_NOT_RUN vẫn hợp lệ |
| k≥57 nhưng đang thay baseline | KEEP_EXPERIMENTAL / FULL_ELIGIBLE; chờ xác nhận FULL |
| Hết90 phút, không phân loại được nguyên nhân, attempt0 | RETRY / RETRY_PENDING; tối đa một retry sau xử lý có bằng chứng |
| Cùng case, attempt1 vẫn unresolved | RETRY / BLOCKED_UNRESOLVED; không retry lần ba |
| FULL đạt quality nhưng chưa bridge | KEEP_EXPERIMENTAL / FULL_NOT_CONFIRMED_FOR_LOCAL |

## P1-P5 và phần còn mở

| Check | Xử lý errata | Execution còn cần |
| --- | --- | --- |
| P1 NI | Giữ Hoeffding bảo thủ; không tự thay bằng asymptotic NI | Ticket CVC nghiên cứu paired NI, size/power; hoặc đăng ký margin khác trước data |
| P2 SMOKE | Nói rõ15% reserve chỉ LAPTOP; SMOKE stress599s | Tokenizer thật, IF8/OCR16, DEV timing và memory |
| P3 bridge | Thêm DEV pilot hai host trước campaign | Log mismatch; bridge strict hoặc FULL shard local |
| P4 gold batch | Khóa batch100, tail<50 gộp, split<100 dùng cảsplit; min2 lỗi cho trigger | NgườiB/C, agreement, danh sách batch trước review, mọi lỗi sửa trước freeze |
| P5 Hoeffding | Ghi textL≥.60 redundant khiS≥.70; ảnh92/120 binding | Validator giữ đúng integer gates và báo bounds |

F14 đóng theo reviewer full-hash match. F3 tokenizer còn mở. CSQA HOLD không đổi. TASK-003-CVC-001 đã soạn riêng, PLANNED; chưa triển khai corpus/validator hay chạy calibration. Chủ dự án chuyển errata để Claude C kiểm nhanh, chưa gửi tự động. Tài liệu RESPONSE v0.3 giữ nguyên làm lịch sử; walkthrough E4 ở đây thay phần cũ hiện hành. Không dùng việc đã viết errata làm receipt freeze.
