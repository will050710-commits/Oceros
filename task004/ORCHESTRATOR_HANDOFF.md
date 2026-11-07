# TASK-004 — sẵn sàng bàn giao orchestrator

Ngày ghi nhận: 07/11/2026 (Asia/Bangkok).

| Trường | Giá trị |
| --- | --- |
| TASK_ID | TASK-004 |
| Trạng thái bàn giao | READY_FOR_ORCHESTRATOR_HANDOFF; chưa gửi qua công cụ messaging/tracker, chưa có acknowledgment từ orchestrator |
| Verdict reviewer | **ACCEPT — launcher/client/mock trên Linux**, do người dùng chuyển tiếp; chỉ bao phủ 8 finding vòng hai |
| Commit implementation được chấp nhận | [`47aaeee91739c2f09ea30538e40c66e853653543`](https://github.com/will050710-commits/Oceros/commit/47aaeee91739c2f09ea30538e40c66e853653543) |
| Thay đổi sau verdict | Chỉ tài liệu, bản lưu review, log kiểm riêng hai minor và checksum; không đổi code/tests/schema/config/dependency hoặc evidence runtime đã được review |
| Scope hoàn thành | Launcher, client HTTP loopback, mock, preflight, sampling, record/schema, CLI; stdlib + psutil |
| Quyết định scope thay phiếu 24/10 | USER-DECIDED; xem [sổ trạng thái](STATUS_LEDGER.md) |
| Phần phiếu 24/10 | NOT_IMPLEMENTED: ticket/ledger/provenance/costlog/CLI cũ; chờ quyết định tách ticket hoặc bỏ, không tự coi là hoàn thành/hủy |
| Chưa xác minh/thực thi | Windows UNVERIFIED; model thật/benchmark/CVC NOT_RUN; không freeze dataset |

## Bằng chứng và nguồn review

**Dùng snapshot 47aaeee hoặc hồ sơ main có ghim SHA đó. Không dùng ZIP cũ `Oceros_TASK004_mock_handoff.zip` (2cb9168).** [Sổ trạng thái](STATUS_LEDGER.md) phân biệt scope đã chấp nhận với phiếu cũ chưa làm. [Kiểm bổ sung](reviews/2026-11-07/ADDITIONAL_SCOPE_AUDIT.md) là nguồn REPORTED riêng, không gộp số mutation/fuzz với reviewer trước.

- [Verdict ACCEPT được lưu từ tin nhắn](reviews/2026-11-07/ACCEPT_REVIEW.md).
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

## Quyết định đề nghị orchestrator

Ghi nhận ACCEPT cho đúng scope Linux launcher/client/mock tại 47aaeee; xác nhận đã nhận packet và quyết định đóng/ghi hoàn thành scope này theo workflow dự án. Không tự nâng thành hoàn thành Windows, chạy model thật, benchmark hoặc CVC.

Đã lập [TASK-004-WIN-MOCK](tickets/TASK-004-WIN-MOCK.md) trong repo: READY_FOR_ASSIGNMENT / NOT_RUN, chưa tạo issue ngoài/giao owner. Sau Windows mock và phép đo RAM sạch có nguồn, cần người dùng duyệt trước khi mở ticket bảng preflight theo model + adapter llama.cpp. Hiện chưa có adapter thật, bảng ngưỡng theo model hay hardware_reference khác null; không coi các phần đó hoàn thành.

## Nội dung ngắn để người dùng gửi orchestrator

> TASK-004 đã nhận verdict ACCEPT cho launcher/client/mock trên Linux tại commit `47aaeee91739c2f09ea30538e40c66e853653543`. Reviewer báo tái lập thành công; evidence implementer có 106/106 test × 3 lượt và dry-run SYNTHETIC. Xin ghi nhận: scope launcher/mock Linux ACCEPTED; thay scope phiếu 24/10 USER-DECIDED; ticket/ledger/costlog cũ NOT_IMPLEMENTED, chờ quyết định tách hoặc bỏ. Xác nhận đã nhận packet và phân công ticket TASK-004-WIN-MOCK trong repo. Windows/model thật chưa xác minh; chưa mở adapter thật hoặc bảng RAM theo model. Hai minor có đối chiếu bổ sung riêng, và OverflowError với metric cực lớn được theo dõi như ghi chú không chặn. Packet: https://github.com/will050710-commits/Oceros/blob/main/task004/ORCHESTRATOR_HANDOFF.md
