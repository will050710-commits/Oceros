# Bổ sung log Windows và đối chiếu hội thoại Gemini — 07/11/2026

Đã nhận tệp log nguyên byte và PDF hội thoại 17 trang. Kết quả hiện tại: **SURVEY_LOG_CONFIRMED / WINDOWS_NOT_VERIFIED**. Đây là kiểm tệp do người dùng cung cấp; không phải lượt chạy Windows mới của implementer. Không thực thi các lệnh trong PDF hoặc coi lời hướng dẫn của Gemini là yêu cầu thay đổi code.

## Định danh nguồn

| Tệp được cung cấp | Byte | SHA-256 | Lưu trong repo |
| --- | ---: | --- | --- |
| `unittest-survey.sanitized.log` | 16245 | `8592f8a806b10bf376fa3afcda204bfc1c3c5f855329492960c631c303c23b13` | [Nguyên byte](unittest-survey.sanitized.log) |
| `Hướng dẫn xác thực tệp ZIP nhiệm vụ.pdf` | 427847 | `b8394b319989dd9991834cec75976247160b15f3221b3c191317143db79ba39d` | Chỉ bản đối chiếu này và metadata; PDF đính kèm có đường dẫn hồ sơ cá nhân và URL/ID hội thoại |

[supplement-verification.json](supplement-verification.json) được sinh từ phân tích log và kiểm nội dung PDF. [intake-verification.json](intake-verification.json) giữ nguyên kết quả tiếp nhận lần trước, lúc chưa nhận hai tệp mới; các mục thiếu log/chẩn đoán trong tệp cũ nay được bổ sung tại đây.

## Kết quả xác nhận từ log

- Hash khớp chính xác giá trị báo trước. Phân tích được 106 ID test duy nhất: **92 ok, 1 FAIL, 0 ERROR, 13 skipped**; footer khớp `Ran 106 tests in 17.224s` và `FAILED (failures=1, skipped=13)`.
- Failure duy nhất là `test_client_edges.ClientEdgeTests.test_cancel_during_http10_body_read`: assertion kiểm thread `task004-http` còn sống, tại dòng 77 gọi helper dòng 53. Danh sách 13 skip khớp bảng đã nhận, không quy skip thành PASS.
- Có một traceback của failure dự kiến; không có `Exception ignored`. Chuỗi `ResourceWarning` xuất hiện một lần trong lệnh `-W error::ResourceWarning`, không phải cảnh báo thực thi. Log failed này không được dùng làm evidence của lượt thành công.
- PowerShell thêm wrapper `NativeCommandError` quanh stderr của unittest; không có một test ERROR thứ hai. Log không in `suite_exit=1`, nên mã thoát 1 vẫn là giá trị được báo trong handoff.
- Không thấy đường dẫn tuyệt đối dạng ổ đĩa, NUL hay ký tự thay thế Unicode trong tệp log. PDF trang 7–10 ghi quá trình sửa lần chuẩn hóa sai encoding sang UTF-8; hash cuối ở trang 10 khớp tệp nhận được. Chưa nhận log UTF-16 trước chuẩn hóa; không gọi tệp sanitized là bản console gốc chưa biến đổi.
- Log UTF-8 được cung cấp có chuỗi xuống dòng CRCRLF và khoảng trắng cuối dòng. Giữ nguyên để bảo toàn hash; chỉ loại đúng tệp nhập này khỏi kiểm whitespace của diff, không sửa lại byte log.

## Bằng chứng chẩn đoán trong PDF

| Trang | Nội dung | Phân loại |
| --- | --- | --- |
| 8–9 | Gemini cung cấp script so sánh shutdown và shutdown+close với fixture body stall | Mã đề xuất trong hội thoại |
| 9, phần **User prompt** | `Method=shutdown_only: elapsed=1.0077s, alive=True`; `Method=shutdown_and_close: elapsed=1.0056s, alive=True` | Output người dùng dán sau khi chạy |
| 10 | Script raw `ctypes.windll.ws2_32.closesocket(...)` và sửa encoding log | Mã đề xuất trong hội thoại |
| 10–11, phần **User prompt** | `Winsock closesocket: elapsed=0.0575s, alive=False`; `Exception ignored while finalizing` và `WinError 10038` | Output người dùng dán sau khi chạy; không phải cách sửa sạch |
| 11, 14 | Timeout từng nhịp 50 ms rồi lặp đọc | Đề xuất chưa có bản vá/test chứng minh |

Mã và output chẩn đoán đã có trong PDF: **TRANSCRIPT_SUPPORTED / NOT_INDEPENDENTLY_REPRODUCED**. Không cần yêu cầu gửi lại nội dung này để chốt intake. PDF có dòng code dài bị cắt và phần lệnh dán mất định dạng; chưa có script `.py` nguyên byte, không xuất bản một bản chép lại như thể đó là script gốc.

## Giới hạn của kết luận kỹ thuật

Probe quan sát worker vẫn sống sau khoảng một giây, không quan sát chính xác worker đang ở `select()` và không chứng minh nó tồn tại đủ năm giây. Script dùng `headers_sent.wait()` rồi `sleep(.05)`, `resp.read(100)`, nuốt exception và không đóng response tường minh; chưa phải regression test hoàn chỉnh. Nhận định “100% nguyên nhân” hoặc “luôn thoát trong 50 ms” của Gemini vượt bằng chứng hiện có.

Đề xuất timeout ngắn phải giữ buffered I/O và tổng deadline đúng. Kiểm Linux trước đây đã chỉ ra việc tiếp tục đọc cùng socket.makefile sau timeout có thể ném `cannot read from timed out object`. Không áp dụng raw closesocket hoặc giảm timeout rồi bỏ qua lỗi để làm test xanh.

## Bước tiếp theo

Bổ sung evidence intake đã xong; chưa cần người dùng chạy lại suite nguyên bản. Thực hiện [TASK-004-WIN-CLIENT-CANCEL](../../tickets/TASK-004-WIN-CLIENT-CANCEL.md) trong commit riêng, có hồi quy cho response hợp lệ chậm hơn nhịp polling và worker thực sự thoát khi hủy. Sau đó kiểm đúng commit mới trên Linux và Windows, hoàn tất các đường Windows còn thiếu. Windows vẫn NOT_VERIFIED; Linux ACCEPT tại 47aaeee, model/CVC và legacy không đổi trạng thái.
