# TASK-004-WIN-CLIENT-CANCEL — hủy HTTP không để worker đọc body còn sống

Ngày lập: 07/11/2026 (Asia/Bangkok). Ticket theo sau [Windows intake](../evidence/windows-intake-20261107/README.md); chưa tạo issue ngoài hay giao qua công cụ messaging.

| Trường | Giá trị |
| --- | --- |
| Trạng thái | READY_FOR_IMPLEMENTATION / NOT_IMPLEMENTED |
| Owner | Chưa phân công; agent sửa code và người có máy Windows phối hợp kiểm đúng revision |
| Ticket cha | [TASK-004-WIN-MOCK](TASK-004-WIN-MOCK.md) |
| Implementation baseline | `47aaeee91739c2f09ea30538e40c66e853653543`; các commit hồ sơ sau đó không thay client/tests |
| Finding | CONFIRMED_FROM_UPLOADED_LOG: `test_cancel_during_http10_body_read` fail vì `task004-http` còn sống sau khi `request_synthetic` trả CANCELLED |
| Máy cần tái kiểm | Windows 11 10.0.26200 / CPython 3.14.4 / psutil 7.2.2 theo intake |
| Ranh giới | Launcher/client/mock; stdlib + psutil; không model thật, API model, CVC, ticket/ledger/costlog |

## Vấn đề và đầu vào

Trong fixture HTTP/1.0 body stall, báo cáo cho biết `socket.shutdown(SHUT_RDWR)` từ thread khác không đánh thức worker kịp `join(.5)` trên Windows. Request chính giữ đúng CANCELLED nhưng worker còn sống. Đây là finding cần sửa; mã/output chẩn đoán đã có trong [PDF được đối chiếu](../evidence/windows-intake-20261107/SUPPLEMENT_REVIEW.md). Probe cho thấy worker còn sống sau một giây, chưa quan sát trực tiếp Winsock/select.

Bốn artifact intake đã khớp hash và validator. Log survey đã nhận, hash khớp và xác nhận 92 ok / 1 FAIL / 13 skipped. PDF có script và output shutdown/closesocket ở trang 8–11; đây là transcript, không phải script .py nguyên byte. Không cần gửi lại hoặc chạy lại toàn suite nguyên bản để thu thập các bằng chứng đã có.

## Yêu cầu bản sửa

1. Worker phải quan sát cancellation/closing và tổng deadline khi chờ HTTP, kể cả headers/body stall hoặc trickle. Có thể dùng polling khoảng 50 ms; không tuyên bố bảo đảm wall-clock 50 ms trên mọi máy. Khi request hủy/timeout trả về, worker của request phải đã thoát sạch trong phép thử body-read, đúng assertion hiện có.
2. Giữ semantics timeout tổng, CANCELLED/TIMEOUT và primary exception; phản hồi hợp lệ chậm hơn một nhịp polling nhưng nằm trong tổng deadline vẫn phải PASS. Không đổi mọi lần hết nhịp polling thành TIMEOUT của toàn request.
3. Không tiếp tục đọc buffered socket đã bị timeout, không truy cập state nội bộ của `SocketIO` để xóa cờ lỗi, không gọi raw `closesocket` qua ctypes. Cơ chế I/O cần giữ ownership và cleanup đúng của Python; chọn thiết kế sau khi kiểm buffered HTTP và partial reads.
4. Giữ kiểm endpoint loopback trước kết nối, giới hạn body 65.536 byte, xác thực JSON/fixture và nhãn SYNTHETIC/NOT_RUN. Không thay test bằng sleep dài hoặc bỏ kiểm worker để che lỗi.
5. Scope sửa ưu tiên `client.py` và test hồi quy client. Không sửa evidence cũ hoặc nâng Windows VERIFIED trong commit code. Giới hạn worker connect bị chặn đã ghi ở B1 phải được báo riêng nếu chưa được xử lý trong thiết kế này.

## Hồi quy và bằng chứng cần bàn giao

- Baseline: tái hiện fail đúng `test_cancel_during_http10_body_read` trên Windows; log chỉ rõ worker còn sống. Có thể bổ sung test Linux mô phỏng shutdown không đánh thức read, với đồng bộ pha rõ và cleanup luôn dọn thread/socket. Phân biệt mô phỏng với Windows thật.
- Fixed: test cũ PASS và worker đã thoát; thêm delayed-valid-response vượt 50 ms nhưng dưới deadline, partial header/body, stall/trickle, oversize, cancel/timeout. Các test phải bắt lỗi nếu quay lại cơ chế bị hỏng hoặc kết thúc TIMEOUT quá sớm.
- Kiểm stdout/stderr cả subprocess và finalizer: không `Exception ignored`, `ResourceWarning`, `Traceback` bất ngờ trong các lượt thành công. Baseline traceback đúng lỗi được giữ riêng làm bằng chứng hồi quy.
- Chạy suite Linux phù hợp và bộ client Windows thực trên commit mới; lưu full SHA, source fingerprints, test counts, skip reasons, exit codes và log thật. Lặp ba lượt các test cancellation/cleanup trên Windows để kiểm độ ổn định; không đổi số lượt thực thành con số dự kiến.
- Bàn giao diff, log baseline/fixed, fixture Windows, artifact mới nếu chạy dry-run, checksum và handoff đủ 17 trường. Reviewer đánh giá commit mới; Linux ACCEPT của 47aaeee không tự chuyển sang bản sửa.

## Các đường Windows còn lại

Client fix không đóng các mục Ctrl+C/Ctrl+Break, signal trong cleanup/ghi artifact, forced CLI death/watchdog, child environment hoặc exited-parent tree cleanup. Các mục đó cần test Windows thật theo ticket cha; các skip POSIX thuần túy vẫn được giải thích riêng. Không dùng survey 92 pass / 13 skip làm Windows acceptance.

## Cổng bước model

Giữ Windows NOT_VERIFIED cho tới khi đủ phép kiểm bắt buộc. Bảng preflight theo model và adapter llama.cpp chỉ mở sau Windows mock, RAM sạch có nguồn và quyết định chủ dự án; legacy và CVC vẫn ngoài scope.
