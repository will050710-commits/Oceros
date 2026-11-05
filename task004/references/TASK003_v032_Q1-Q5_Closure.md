# TASK-003: ghi nhận APPROVE_DESIGN và xử lý Q1-Q5

Ngày ghi nhận: 2026-11-04. Bản tài liệu hiện hành: spec v0.3.2; CVC-001 revision1.1. Không mở vòng thiết kế mới.

## Quyết định và phạm vi bằng chứng

Claude C kết luận **ACCEPT_ERRATA** cho v0.3.1, nâng TASK-003 lên **APPROVE_DESIGN**. Đây là REPORTED từ nội dung chủ dự án cung cấp. Reviewer báo đã đối chiếu diff, hash, bảng exact và mô phỏng độc lập300000 dataset ở10 profile; chỉ spot-check audit JSON. Không diễn giải thành đã kiểm từng bản ghi, license/corpus, tokenizer hay hardware.

Spec được reviewer kiểm là SHA-256 `380be7cf340fb22961dc3f36d383dc04a3f68180e2a549e8471720e96be87ead`, 91350 byte,695 dòng. Audit v031 `ec3e91e03ccddf1a5c567dd37f4c20c554e2667eec0e3e34c7980c9526716503` giữ nguyên. Q1-Q5 không chặn duyệt; thay đổi dưới đây là sửa nhỏ sau duyệt, không tuyên bố reviewer đã đọc v0.3.2.

**Trạng thái hiện tại: thiết kế đã duyệt; corpus NOT_FROZEN; CVC PLANNED/READY_FOR_ASSIGNMENT; baseline NOT_RUN.**

## Ánh xạ Q1-Q5

| Mục | Đã áp | Tiêu chí kiểm |
| --- | --- | --- |
| Q1 | Spec§6.2.2 và§6.3: quality REJECT đặt ở hàng6 trước hàng thiếu resource7; bỏ điều kiện resource đầy đủ | Đủ80 outputs hợp lệ,k20/39,thiếu phase timer => REJECT; k40 thiếu timer => KEEP/LOCAL_EVIDENCE_INCOMPLETE; incomplete vẫn theo hàng lỗi |
| Q2 | Spec§6.2.3 ghi thẳng khoảng cách provisional/confirmed, targetp=.85 là policy; C7 bắt buộc báo p50/p90 | Báo riêng CORE/VLM trong R và parse95%, bracket/grid/MC uncertainty; chưa tính nghiệm mới trong lần sửa tài liệu này |
| Q3 | CVC ALLOWED/FORBIDDEN và RESOURCE_BUDGET thống nhất quyền tải/chạy shortlist | Chỉ config/revision/host và ngân sách đã duyệt; không API trả phí; calibration được làm khi giao CVC, baseline chờ freeze |
| Q4 | Thêm C11 null policies và yêu cầu C10 chờ C11 | Mỗi policy không qua tổ hợp quality cho PROMOTE; REJECT khi≤39/80 hợp lệ, còn lại KEEP theo matrix; không cấm FULL_ELIGIBLE hay PASS một gate riêng |
| Q5 | C6 có registry mọi ngưỡng nguyên±1, bảng biên đầy đủ; C7 có hợp đồng auxiliary flags | Counts, denominator, strict-fail subset và phân bổ subtype rõ; fixture item-level cố định giữa hai implementation |

## Hai diễn giải cần chính xác

“Cổng tổng70% không bao giờ ràng buộc” chỉ phản ánh thực tế gần như không chi phối các profile đồng đều đã tính, không phải đồng nhất thức. Tổng các sàn nhóm mới là516/800, thấp hơn560/800; chia đều mỗi ngôn ngữ258/400 vẫn qua language gate nhưng trượt total. Spec giữ cổng tổng và ghi phản ví dụ này.

“Null policy không qua cổng nào” được thực hiện ở mức **tổ hợp quality đủ PROMOTE**, không phải từng gate riêng. Ví dụ {} có thể parse được; always-answer có thể trả lời đúng nhánh HC answerable. Không nên biến C11 thành veto FULL_ELIGIBLE vì E2 đã xác định veto chỉ chặn provisional. Case giả định các nhóm khác hoàn hảo là fixture kiểm matrix, không phải score null policy thật.

Các chênh lệch mô phỏng0.1-0.2 pp có thể là nhiễu MC. Hợp đồng phân bổ lỗi nhằm loại mơ hồ implementation, không khẳng định reviewer mắc lỗi. Với p/e đồng đều, gộp/tách subtype đúng cách giữ nguyên luật phân phối; RNG stream có thể khác.

## Bàn giao

- Giao TASK-003-CVC-001.md revision1.1 cùng spec v0.3.2 và gói này cho implementer; chủ dự án phân công A/B/C, chốt shortlist và quyền/ngân sách môi trường.
- Các ngưỡng, bảng xác suất, schema examples, notice và audit v0.3.1 giữ nguyên; không chạy thêm simulation/model trong lần sửa này.
- CVC kiểm C1-C11, P1-P5, tokenizer thật, DEV/bridge, permission/gold và receipt trước freeze. Chưa tự giao ticket, liên hệ người khác hay chạy calibration/baseline.
- ERRATA v0.3.1 và RESPONSE v0.3 trong gói là lịch sử giữ nguyên byte. Trạng thái hiện hành lấy từ spec/header/handoff v0.3.2.
