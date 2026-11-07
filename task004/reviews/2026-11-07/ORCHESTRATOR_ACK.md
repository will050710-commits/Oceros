# ORCHESTRATOR ACK — TASK-004, 07/11/2026

Nguồn: xác nhận do người dùng chuyển tiếp trong chat ngày 07/11/2026 (Asia/Bangkok). Đây là bản ghi nội dung được cung cấp, không phải log chạy mới của implementer hay sự kiện từ connector/tracker. Trạng thái tiếp nhận: **ACK_REPORTED / PACKET_RECEIVED**.

| Mốc | Giá trị |
| --- | --- |
| Packet được xác nhận | `879dcfae77bac2990c6ee4ba3946d26be1bbbb08` trên main |
| Implementation Linux mock được chấp nhận | `47aaeee91739c2f09ea30538e40c66e853653543` |
| Văn bản packet | [ORCHESTRATOR_HANDOFF tại 879dcfa](https://github.com/will050710-commits/Oceros/blob/879dcfae77bac2990c6ee4ba3946d26be1bbbb08/task004/ORCHESTRATOR_HANDOFF.md) |
| Kết luận được chuyển tiếp | Handoff đúng, nhất quán; đã nhận packet; không có gì chặn việc ghi sổ |

## Văn bản xác nhận được cung cấp

> ORCHESTRATOR ACK, TASK-004, 07/11/2026. Đã nhận packet tại `main` `879dcfa` và kiểm độc lập trên Linux: code, tests, schema, config, references, evidence không đổi so với `47aaeee`; suite 106/106; SHA256SUMS 180/180. Ghi nhận: launcher/client/mock Linux tại `47aaeee` = ACCEPTED (verdict reviewer là REPORTED); thay scope phiếu 24/10 = USER-DECIDED; TASK-004-LEGACY-OPS = PLANNED / NOT_IMPLEMENTED; TASK-004-WIN-MOCK = READY_FOR_ASSIGNMENT, owner do chủ dự án chỉ định. Chưa mở: Windows, model thật, bảng preflight theo model, CVC. Hai minor chưa được reviewer xác nhận.

## Chi tiết kiểm tra được báo lại

Các mục dưới đây là **REPORTED từ bên xác nhận**; không gộp với các lượt test/mutation của implementer hoặc reviewer trước:

- Từ 47aaeee đến 879dcfa chỉ đổi 12 tệp hồ sơ/ticket/checksum; code, tests, schema, config, references, evidence và requirements giữ nguyên.
- Suite tại 879dcfa: 106/106; SHA256SUMS 180/180. Danh sách checksum không bao gồm README.md ở gốc repo hay chính SHA256SUMS, như snapshot trước.
- Tệp handoff người kiểm nhận giống bản trên main tại 879dcfa; sổ trạng thái và kiểm bổ sung giữ đúng nhãn REPORTED, không trộn 5 mutation của người kiểm với 14 mutation/30.000 fuzz của reviewer trước.
- Làm rõ ZIP người kiểm nhận: 50 mục = 42 tệp + 8 thư mục; cả 42 tệp khớp byte với 2cb9168 và comment ZIP ghi commit đó. ZIP cục bộ của implementer có 41 thành viên tệp; chưa có cơ sở coi hai ZIP là cùng artifact. Nội dung này bổ sung cách gọi “50 tệp” trong [bản kiểm trước](ADDITIONAL_SCOPE_AUDIT.md), không thay đổi bản ghi lịch sử.
- Ticket Windows phản ánh đúng các test POSIX có skip, fallback terminate/kill qua psutil và việc chưa có Job Object. Người kiểm ghi nhận test cấp phát 16 MB; đây không phải bằng chứng test đã chạy trên laptop hay bảo đảm tài nguyên của máy tại lúc chạy.

## Các điều chỉnh sau ACK

1. WIN-MOCK giữ READY_FOR_ASSIGNMENT / NOT_RUN; chủ dự án chỉ định người có máy Windows thực hiện. Orchestrator không được ghi là đã phân công owner.
2. Ticket Windows bổ sung cách nhận diện source khi tải ZIP GitHub và không có Git: đọc full commit từ comment ZIP, ghi SHA-256 archive và kiểm checksum các tệp giải nén. Comment/hash là dữ liệu provenance, không tự xác thực nguồn hay chứng minh Windows PASS.
3. Snapshot RAM/đĩa/commit trong ticket chỉ phục vụ điều kiện chạy mock, chưa tương đương hồ sơ TASK-001. CPU i7-8665U và 94 GFLOPS hiện là thông tin người dùng thuật lại; chưa có JSON gốc/probe để xác minh hoặc tái lập. Khi có nguồn, đo theo probe gốc trên máy vừa khởi động lại, ghi chế độ Best performance thực tế, lưu JSON và SHA-256 cùng điều kiện đo.
4. Phiếu `TASK_TICKETS_2026-10-24.md` nguyên byte vẫn chưa có trong repo/các tệp đính kèm hiện có. Cần nhận tệp gốc để lưu vào references và đối chiếu AC của LEGACY-OPS; không dựng lại tệp từ bản tóm tắt.

Cổng tiếp theo giữ nguyên: Windows mock hoàn tất, RAM sạch có nguồn và chủ dự án duyệt trước khi mở bảng preflight theo model + adapter llama.cpp. Model thật, benchmark và CVC chưa chạy. Hai minor chưa có xác nhận riêng từ reviewer.

[Sổ trạng thái hiện tại](../../STATUS_LEDGER.md) · [Handoff hiện tại](../../ORCHESTRATOR_HANDOFF.md) · [Ticket Windows](../../tickets/TASK-004-WIN-MOCK.md) · [Ticket legacy](../../tickets/TASK-004-LEGACY-OPS.md).
