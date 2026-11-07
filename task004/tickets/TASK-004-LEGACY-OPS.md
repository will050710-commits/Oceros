# TASK-004-LEGACY-OPS — ticket, ledger và costlog của phiếu 24/10

Ngày ghi nhận: 07/11/2026. Đây là ticket trong repo, tách theo quyết định người dùng; chưa tạo issue trên tracker ngoài.

| Trường | Giá trị |
| --- | --- |
| ID trong repo | TASK-004-LEGACY-OPS; orchestrator có thể ánh xạ sang ID của tracker khi tiếp nhận |
| Trạng thái | PLANNED / NOT_IMPLEMENTED |
| Quyết định phạm vi | SEPARATE_TICKET / USER-DECIDED |
| Owner triển khai | Chưa phân công |
| Nguồn yêu cầu | TASK-004 trong phiếu 24/10, hiện chỉ có bản thuật lại trong handoff lịch sử |
| Acceptance criteria (AC) | Cần đối chiếu nguyên bản trước khi chốt chi tiết triển khai |
| Implementation / tests / evidence riêng | Chưa có / NOT_RUN / chưa có |
| Quan hệ với scope đã ACCEPT | Độc lập với Linux launcher/client/mock tại `47aaeee91739c2f09ea30538e40c66e853653543` |

## Quyết định của người dùng

Trong chat, người dùng trả lời câu hỏi về phần ticket/ledger/costlog của phiếu TASK-004 ngày 24/10:

> Tách thành ticket riêng, giữ trạng thái chưa triển khai (đề xuất)

Quyết định này chốt việc giữ công việc trong backlog riêng. Lượt cập nhật hiện tại chỉ lập ticket và ghi sổ; trạng thái triển khai vẫn NOT_IMPLEMENTED. Kết quả ACCEPT Linux mock và 106/106 test × 3 thuộc phạm vi launcher/client/mock, không phải bằng chứng hoàn thành ticket này.

## Phạm vi được thuật lại từ phiếu cũ

Nguồn: [handoff lịch sử ngày 05/11](../references/HANDOFF_REPORT_TASK-004.md), bảng WORK_COMPLETED đối chiếu phiếu TASK-004 dòng 207–278. Các mục dưới đây là **REPORTED qua handoff**, chưa được đối chiếu trực tiếp với phiếu nguyên bản trong phiên này.

| Hạng mục | Yêu cầu được thuật lại |
| --- | --- |
| Mục tiêu | Quản lý ticket, ledger thí nghiệm, nguồn/provenance và ngân sách/costlog |
| Module | `tickets`, `ledger`, `provenance`, `costlog`, `runner`, `cli` |
| CLI | `validate-ticket`, `new-experiment`, `log-cost`, `status` |
| Vòng đời ticket | PLANNED…RELEASED; chưa có danh sách đầy đủ và quy tắc chuyển trạng thái |
| Kiểm thử | Ít nhất 25 pytest; luồng ticket → 3 nguồn → ledger → cost log; kiểm việc chặn VERIFIED/PROMOTE |
| Tài nguyên runner/mock | RSS <150 MB và thời gian <10 giây; cần xác định đơn vị, phạm vi đo và điều kiện chạy từ phiếu gốc |
| Mạng và dịch vụ nền | Cấm gọi mạng, watcher/dev server theo phiếu cũ; ngoại lệ HTTP loopback của launcher/mock không tự áp dụng cho ticket này |
| Dependency | Runtime stdlib/PyYAML tùy chọn; pytest cho phát triển; psutil tùy chọn trong runner được thuật lại nhưng chưa thống nhất với mục dependency của phiếu |
| Phụ thuộc và ngân sách | Phiếu được thuật lại là không phụ thuộc TASK-002/003; API_BUDGET trống hoặc 0 không cấp quyền gọi API trả phí |

Tên module trùng với chức năng hiện có của mock không chứng minh module đó đáp ứng hợp đồng của phiếu cũ. Schema, CLI, dependency và test của launcher/mock không tự trở thành hợp đồng cho ticket này.

## Đối chiếu cần làm khi được giao triển khai

1. Lấy nguyên bản `TASK_TICKETS_2026-10-24.md` hoặc bản `(2)` và đọc phần TASK-004. Handoff lịch sử ghi 32.133 byte, SHA-256 `27cb47fed77b5af6f300c6f3000f360c2505d84fc088684b0fe2f91b7d98a3c0`; đây là hash **được thuật lại**, chưa xác minh lại vì chưa có tệp nguyên bản trong repo.
2. Chốt schema ticket/ledger/costlog/provenance, giao diện CLI, đầy đủ trạng thái và điều kiện VERIFIED/PROMOTE. Làm rõ dependency PyYAML/psutil, ngưỡng RSS/thời gian, ngân sách và quy tắc mạng từ nguồn gốc.
3. Orchestrator phân công owner, ghi AC cuối cùng và nơi triển khai riêng; không mặc định đổi owner/nhánh theo thông tin lịch sử hoặc sửa mã Linux mock đã ACCEPT.
4. Khi triển khai được giao riêng, bàn giao diff, test hồi quy/tích hợp và phép đo thực theo AC đã chốt. Hiện chưa có lượt chạy nào để báo PASS cho ticket này.

## Liên kết theo dõi

- [Sổ trạng thái và quyết định phạm vi](../STATUS_LEDGER.md).
- [Bản bàn giao orchestrator](../ORCHESTRATOR_HANDOFF.md).
- [TASK-004-WIN-MOCK](TASK-004-WIN-MOCK.md) là ticket xác minh Windows mock riêng, vẫn NOT_RUN.

Adapter model thật, bảng preflight theo model, benchmark và CVC thuộc các phạm vi khác; việc lập ticket này không khởi động chúng. Việc gửi/tiếp nhận qua orchestrator chưa được ghi nhận.
