# TASK-004 — bàn giao và ghi nhận ACK orchestrator

Ngày ghi nhận: 07/11/2026 (Asia/Bangkok).

| Trường | Giá trị |
| --- | --- |
| TASK_ID | TASK-004 |
| Trạng thái bàn giao | ACK_REPORTED / PACKET_RECEIVED tại packet `879dcfa`; [ACK do người dùng chuyển tiếp](reviews/2026-11-07/ORCHESTRATOR_ACK.md), không có gì chặn ghi sổ |
| Verdict reviewer | **ACCEPT — launcher/client/mock trên Linux**, do người dùng chuyển tiếp; chỉ bao phủ 8 finding vòng hai |
| Commit implementation được chấp nhận | [`47aaeee91739c2f09ea30538e40c66e853653543`](https://github.com/will050710-commits/Oceros/commit/47aaeee91739c2f09ea30538e40c66e853653543) |
| Thay đổi sau verdict | Chỉ tài liệu, bản lưu review, log kiểm riêng hai minor và checksum; không đổi code/tests/schema/config/dependency hoặc evidence runtime đã được review |
| Scope hoàn thành | Launcher, client HTTP loopback, mock, preflight, sampling, record/schema, CLI; stdlib + psutil |
| Quyết định scope thay phiếu 24/10 | USER-DECIDED; xem [sổ trạng thái](STATUS_LEDGER.md) |
| Phần phiếu 24/10 | NOT_IMPLEMENTED; người dùng đã chọn tách [TASK-004-LEGACY-OPS](tickets/TASK-004-LEGACY-OPS.md) thành ticket riêng, giữ chưa triển khai |
| Chưa xác minh/thực thi | Windows UNVERIFIED; model thật/benchmark/CVC NOT_RUN; không freeze dataset |

## Bằng chứng và nguồn review

**Dùng snapshot 47aaeee hoặc hồ sơ main có ghim SHA đó. Không dùng ZIP cũ `Oceros_TASK004_mock_handoff.zip` (2cb9168).** [Sổ trạng thái](STATUS_LEDGER.md) phân biệt scope đã chấp nhận với phiếu cũ chưa làm. [Kiểm bổ sung](reviews/2026-11-07/ADDITIONAL_SCOPE_AUDIT.md) là nguồn REPORTED riêng, không gộp số mutation/fuzz với reviewer trước.

- [Verdict ACCEPT được lưu từ tin nhắn](reviews/2026-11-07/ACCEPT_REVIEW.md).
- [ACK orchestrator ngày 07/11](reviews/2026-11-07/ORCHESTRATOR_ACK.md): nhận packet 879dcfa, báo kiểm Linux suite 106/106 và checksum 180/180. Giữ nhãn REPORTED và gắn đúng snapshot; đây không phải lượt chạy mới của implementer hay ACK qua connector.
- [Review vòng hai gốc](reviews/2026-11-07/ROUND2_REVIEW_ORIGINAL.txt) và [đối chiếu hai minor](reviews/2026-11-07/MINOR_CROSSCHECK.md).
- [Handoff 17 trường tại commit được chấp nhận](https://github.com/will050710-commits/Oceros/blob/47aaeee91739c2f09ea30538e40c66e853653543/task004/HANDOFF_REPORT_TASK-004.md).
- [Review packet có source/diff/log](https://github.com/will050710-commits/Oceros/blob/47aaeee91739c2f09ea30538e40c66e853653543/task004/evidence/review2-20261107-release/REVIEW_PACKET.md).
- [Validation của implementer](https://github.com/will050710-commits/Oceros/blob/47aaeee91739c2f09ea30538e40c66e853653543/task004/evidence/review2-20261107-release/validation.json): 106/106 test, ba lượt, 0 failures/errors/skips/diagnostic markers; Python 3.12.14, psutil 7.2.2, Linux. Dry-run PASS/SYNTHETIC, phase metrics null, benchmark NOT_RUN.
- Reviewer báo tái lập 106/106 × 3 trên Python 3.12.3; 6/6 lượt signal/cleanup dưới tải; 14/14 mutation bị test bắt; fuzz hơn 30.000 index. Các số này là **REPORTED từ reviewer**, không gộp với các lượt implementer đã chạy.
- [SHA256SUMS tại 47aaeee](https://github.com/will050710-commits/Oceros/blob/47aaeee91739c2f09ea30538e40c66e853653543/task004/SHA256SUMS) là snapshot 171 tệp reviewer đã kiểm. SHA256SUMS trên main có thêm tài liệu bàn giao mới; số tệp mới không thay đổi phạm vi acceptance của snapshot cũ.

## Điểm còn theo dõi, không chặn verdict đã nhận

1. `validate_record` có thể ném OverflowError với metric nguyên cực lớn khi gọi như thư viện; đã tái hiện. Không đổi mã đã được chấp nhận. Nếu cần sửa, mở follow-up riêng có hồi quy.
2. Hai test compatibility đọc evidence đã commit; bản sao chạy suite cần giữ các tệp đó.
3. Hai minor đã có code/tests và kiểm lại riêng 2/2 PASS, nhưng reviewer chưa xác nhận đối chiếu từng dòng với review gốc. Ghi chú này không nâng verdict thành review bổ sung cho chúng.
4. Giữ giới hạn CPython/Linux, Windows/Job Object/console signals, log gate chỉ thấy output thu thập, SIGKILL có thể để staging, không directory fsync, worker connect daemon có thể sống tới timeout.

## Trạng thái đã được xác nhận và bước tiếp theo

ACK đã ghi nhận ACCEPT cho đúng scope Linux launcher/client/mock tại 47aaeee và tiếp nhận packet 879dcfa. Không suy từ ACK rằng một issue ngoài đã được đóng hoặc Windows/model thật/benchmark/CVC đã hoàn thành.

ACK ghi nhận [TASK-004-LEGACY-OPS](tickets/TASK-004-LEGACY-OPS.md), PLANNED / NOT_IMPLEMENTED, theo quyết định người dùng “Tách thành ticket riêng, giữ trạng thái chưa triển khai (đề xuất)”. Đây là ticket trong repo, chưa tạo issue ngoài/chưa phân công. Phiếu 24/10 nguyên byte vẫn cần được cung cấp để lưu references và đối chiếu AC chi tiết cho lượt triển khai riêng.

Đã lập [TASK-004-WIN-MOCK](tickets/TASK-004-WIN-MOCK.md) trong repo: READY_FOR_ASSIGNMENT / NOT_RUN, owner do chủ dự án chỉ định; orchestrator chưa phân công. Ticket có phương án ZIP khi không có Git. Snapshot RAM/đĩa/commit chỉ mô tả điều kiện mock, chưa tương đương TASK-001; cần JSON/probe gốc để đo lại RAM sạch và lưu nguồn/hash. Sau Windows mock và phép đo có nguồn, cần người dùng duyệt trước khi mở ticket bảng preflight theo model + adapter llama.cpp. Hiện chưa có adapter thật, bảng ngưỡng theo model hay hardware_reference khác null.

## Nội dung ngắn để cập nhật hồ sơ

> Đã ghi nhận ORCHESTRATOR ACK ngày 07/11/2026 do người dùng chuyển tiếp cho packet `879dcfa`. Launcher/client/mock Linux tại `47aaeee91739c2f09ea30538e40c66e853653543` = ACCEPTED (verdict reviewer REPORTED); scope thay phiếu 24/10 = USER-DECIDED; TASK-004-LEGACY-OPS = PLANNED / NOT_IMPLEMENTED. TASK-004-WIN-MOCK = READY_FOR_ASSIGNMENT / NOT_RUN, owner do chủ dự án chỉ định. Windows/model thật chưa xác minh; bảng preflight theo model, adapter llama.cpp và CVC chưa mở. Hai minor chưa được reviewer xác nhận. Hồ sơ: https://github.com/will050710-commits/Oceros/blob/main/task004/ORCHESTRATOR_HANDOFF.md
