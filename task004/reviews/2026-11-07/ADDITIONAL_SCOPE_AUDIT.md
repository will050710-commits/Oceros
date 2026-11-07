# Bản ghi kiểm bổ sung và làm rõ scope — 07/11/2026

Nguồn: người dùng chuyển tiếp kết quả kiểm trong chat. Đây là bản tổng hợp có ghi nguồn, không phải log chạy mới của implementer hay bản review đã ký. Implementation được kiểm: `47aaeee`; HEAD hồ sơ lúc kiểm: `c45347100e763fbbb1efb537b457c73f115dcaf0`.

## Kết luận được chuyển tiếp

“Phạm vi launcher/client/mock trên Linux đạt, tôi tự kiểm lại được trên máy tôi. Task 4 theo phiếu gốc ngày 24/10 chưa làm.”

Người kiểm lưu ý prompt launcher của họ dựa trên suy luận gián tiếp và lệch scope phiếu gốc. Implementer đã dừng để hỏi, người dùng đã chọn launcher/client/mock. Vì vậy ghi nhận scope thay thế là USER-DECIDED, không coi bộ ticket/ledger/costlog đã được triển khai hay mặc nhiên bị hủy.

## Quan sát được báo lại (REPORTED)

- Linux/Python 3.12.3/psutil 7.2.2; suite 106/106 ba lượt ở HEAD; không process mock mồ côi. Hai minor tests PASS; tái hiện OverflowError metric nguyên cực lớn, không chặn.
- SHA256SUMS 171/171 ở 47aaeee và 176/176 ở c453471; ba hash khóa TASK-002/spec/CVC và hash review gốc khớp.
- Bảy cấu hình sai exit 2; bốn lỗi mock exit 1/124 kèm artifact; preflight fail exit 3; SIGTERM exit 130/CANCELLED; SIGKILL mock tự thoát <0,3 giây khi kiểm lại bằng ps. Lần pgrep đầu khớp cả lệnh shell, nên kết quả đó được sửa.
- 5/5 mutation bị test bắt: thêm lock vào set, bỏ SIG_IGN guard, bỏ PASS resource guard, mở runtime khác mock, nới ảnh 2048.
- Handoff đủ 17 trường; stdlib + psutil; mọi kết quả SYNTHETIC, benchmark NOT_RUN; các evidence FAIL trước được giữ.
- ZIP người kiểm nhận được là bản 2cb9168, không phải bản đã được chấp nhận. Người kiểm mô tả ZIP đó có 50 tệp; không có tệp ZIP mới đính kèm tin nhắn này để đối chiếu con số. Kiểm riêng artifact ZIP cục bộ của implementer được ghi dưới đây.

Người kiểm không tái lập các số 30.000 fuzz, 6/6 tải hoặc 14/14 mutation của reviewer trước; chỉ làm 5 mutation riêng. Không nâng các số đó thành phép kiểm hiện tại. Verdict ACCEPT vẫn là nội dung được chuyển tiếp qua chat, không có tệp byte gốc của reviewer.

## Khoảng trống được nêu

1. Chưa có launcher llama-server thật: adapter thật bị khóa và config chỉ nhận mock.
2. Preflight chưa có bảng theo model (các mức prompt được thuật lại: 1,21 / 1,90 / 2,01–2,67 / 3,45 GiB), chưa có test RAM 0,98 GiB từ chối cả bốn model.
3. Manifest có `hardware_reference=null`.

Đây là phần chưa có so với prompt được thuật lại; không được dùng mock acceptance để khẳng định đã đáp ứng chúng. Không đưa các mức RAM vào code khi chưa có mapping/source/approval.

## Đối chiếu read-only của implementer trong bước ghi sổ

- Git diff 47aaeee→c453471 xác nhận chỉ 8 tệp hồ sơ/checksum thay đổi.
- Source hiện hành xác nhận ba khoảng trống trên; không chạy model hoặc sửa adapter để “lấp” scope trong bước này.
- ZIP cục bộ `/workspace/Oceros_TASK004_mock_handoff.zip` có 41 thành viên file, tất cả khớp byte với 2cb9168; SHA-256 `f7bdc888726aca844255081e28058e95ff92dd77376bac2c8deff613e689adbe`. Điều này xác nhận ZIP cục bộ lỗi thời, không khẳng định nó là cùng ZIP 50 tệp mà người kiểm đã nhận.
- Source/tests/schema/config/references/evidence runtime đã được chấp nhận được giữ nguyên. Chỉ cập nhật hồ sơ phạm vi và phiếu công việc.

## Hành động quản lý

Ghi sổ ở [STATUS_LEDGER.md](../../STATUS_LEDGER.md); lập phiếu [Windows mock](../../tickets/TASK-004-WIN-MOCK.md). Chờ quyết định tách/bỏ phần phiếu cũ. Đo RAM sạch và nhận phê duyệt trước khi mở scope preflight model + llama.cpp adapter. Không tự gộp legacy implementation, Windows validation, model adapter hoặc CVC thành một nhiệm vụ.
