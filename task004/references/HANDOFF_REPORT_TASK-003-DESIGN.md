# HANDOFF REPORT - TASK-003, post-approval v0.3.2

TASK_ID: TASK-003

OWNER: ChatGPT trong phiên Work, Role D; sửa tài liệu, không triển khai CVC hay gọi inference API.

STATUS: APPROVE_DESIGN (REPORTED từ Claude C cho v0.3.1 sau ACCEPT_ERRATA). Q1-Q5 đã áp vào tài liệu v0.3.2/CVC revision1.1; không tuyên bố reviewer đã kiểm bản sửa này. NOT_FROZEN; baseline NOT_RUN.

BASELINE_REVISION:

- Spec được reviewer duyệt v0.3.1: `380be7cf340fb22961dc3f36d383dc04a3f68180e2a549e8471720e96be87ead`,91350 byte,695 dòng.
- Spec v0.3.2 hiện hành: `a02e3e391b49e3ede390fa4904ccbc550c748ab0652da90483788454b7ed614b`,94029 byte,701 dòng.
- CVC-001 revision1.1: `6a89687992dd3f79405dbce7c2c6de94e04a3c5b234d527f70ecbde5bdb7bac2`,18604 byte.
- Ticket gốc SHA-256 `27cb47fed77b5af6f300c6f3000f360c2505d84fc088684b0fe2f91b7d98a3c0`; F14 đã đóng. Dataset manifest=null.

FILES_READ: Spec/handoff/CVC/errata hiện hành và kiểm nhanh của Claude C do chủ dự án cung cấp. Đối chiếu byte nguồn local trước sửa. Không đọc lại license sources hay script reviewer.

FILES_CHANGED:

- BENCHMARK_SPEC_v0.md: status, lịch sử review, Q1 thứ tự quality REJECT, Q2 design point và phần bàn giao hiện hành.
- TASK-003-CVC-001.md: Q2-Q5, C6/C7 chi tiết, C11 null policies và C10 chờ C11; quyền shortlist thống nhất.
- HANDOFF_REPORT_TASK-003-DESIGN.md và TASK003_v032_Q1-Q5_Closure.md.
- Tạo TASK003_v032_Design_Approved_CVC_Package.zip gồm9 file: bốn file trên, ERRATA_TASK003_v0.3.1.md, TASK003_NUMERICAL_AUDIT_v031.json, GB0_INTERNAL_NOTICE_v1.txt, RESPONSE_TO_CLAUDE_REVIEW_v03.md, TASK003_NUMERICAL_AUDIT_v03.json. Năm file lịch sử/bằng chứng giữ nguyên byte.

WORK_COMPLETED:

1. Ghi ACCEPT_ERRATA / APPROVE_DESIGN; tách design approval khỏi execution/freeze.
2. Q1: quality REJECT trước missing resource; thiếu phase timer không che k≤39/80 hợp lệ.
3. Q2: làm rõ provisional/confirmed, target chính sách và reporting p50/p90 trong C7; ghi total gate vẫn có thể binding với profile lệch.
4. Q3: CVC cho phép calibration trong shortlist/ngân sách được giao; không API trả phí hoặc tự mở rộng môi trường.
5. Q4-Q5: C11 null policy chống PROMOTE; C6 toàn bộ biên±1; C7 auxiliary allocation và item-level fixture rõ.

EVIDENCE:

- Claude C báo bảng exact khớp,10 profile MC khớp trong≤0.2pp; audit JSON chỉ spot-check. Đây là REPORTED, không giả kiểm từng record.
- Audit v031 giữ SHA-256 `ec3e91e03ccddf1a5c567dd37f4c20c554e2667eec0e3e34c7980c9526716503`; notice `39510d0f581c3db835465afd95e3a0d0a799cb657d2189c7fd3ff1ca4013eb9e`.
- Q2 phản ví dụ số học:80+90+60+100+96+90=516<560, chia đều258/400 mỗi ngôn ngữ.

TESTS_EXECUTED: Đối chiếu diff với v0.3.1; kiểm14 hàng decision,17 trường handoff, C1-C11 và freeze dependency; parse2 JSONL; kiểm bảng số/ngưỡng/schema không đổi; hash năm file lịch sử và ZIP CRC/bytes. Walkthrough Q1 và C11 bằng tài liệu, không test implementation.

TEST_RESULTS: Sửa giới hạn ở Q1-Q5 và trạng thái review. Các bảng xác suất/schema examples giữ nguyên. Handoff/spec/CVC hashes nhất quán; đủ9 file trong gói. Không chạy lại Monte Carlo hoặc model; p50/p90 là output bắt buộc của CVC, chưa có nghiệm tính mới.

BENCHMARK_RESULTS: N/A. Chưa có corpus, tokenizer measurements, DEV, bridge hay baseline model.

COST_OR_RESOURCE_USAGE: API model$0; không tải/chạy model, không Colab/GPU. Chỉ sửa/kiểm tài liệu; billing/token phiên UNKNOWN. CVC vẫn chưa được giao thực thi.

KNOWN_LIMITATIONS: Design approval cho v0.3.1 không chứng minh corpus thật độc lập, gold đúng, caps khả thi hay model≤3B đạt target. Nhân sự A/B/C, permission, hardware/shortlist và receipt còn cần chốt. Nguồn license không tái duyệt, CSQA HOLD.

RISKS: Gọi thiết kế đã duyệt là FROZEN; chặn quality REJECT bằng metric thiếu; dùng null policy PASS một gate làm failure sai; đổi target theo candidate; trộn lỗi phụ sai mẫu số; nhầm MC noise là lỗi implementation.

RECOMMENDATION: Kết thúc phần thiết kế TASK-003; giao CVC-001 đã cập nhật cho implementer/người A/B/C khi đủ quyền và nguồn lực. Không mở vòng thiết kế mới, chưa freeze/chạy baseline.

NEXT_ACTION: Chủ dự án phân công và chuyển gói cho implementer; thực hiện CVC Stage A trước; hoàn tất C1-C11/P1-P5 và receipt cho tập dự kiến freeze; baseline campaign chỉ sau freeze theo scope/ngân sách đã chốt. Không có tin nhắn hay ticket tracker ngoài được gửi/tạo trong phiên này.

UNVERIFIED_CLAIMS: Corpus/permission/gold, token feasibility, runtime, bridge và NI thay thế chưa có execution evidence. p50/p90 chưa tính chính xác. Q1-Q5 đã áp không đồng nghĩa reviewer đã kiểm v0.3.2; dataset vẫn NOT_FROZEN.
