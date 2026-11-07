# Review packet Antigravity — 08/11/2026 (Asia/Bangkok)

**Verdict: REQUEST_CHANGES / CANDIDATE_NOT_MERGED.** Packet có bản vá client và test mới, ngoài phần đối chiếu ban đầu. Đã kiểm hash, đọc mã và chạy bản sao trên Linux. Bản vá chưa được đưa vào `task004/client.py` đang dùng; Linux ACCEPT vẫn chỉ áp dụng implementation `47aaeee`.

## Nguồn và toàn vẹn

ZIP `TASK-004-WIN-CLIENT-CANCEL_packet_20261107.zip`: 56.659 byte, SHA-256 `0bf2e4cdfbc2e3ad49bf61e8969307875727b515a75cedfb6ef2ddab9745ec5d`, không có ZIP comment. Định danh candidate bằng hash nội dung:

- [client.py được gửi](submission/task004/client.py): `7e0ab19d5abe28ecf6fa04246bb6809b69ad998108ea3144bdb890ed196cbeca`.
- [test_client_edges.py được gửi](submission/task004/tests/test_client_edges.py): `5bcb64e2e9db43114437ccb17ea0b7883d3f0c6b01818f91ce0eb7e842ccb239`.
- [Patch](submission/task004/evidence/windows-client-cancel-20261107/client-cancel.patch) áp lên 47aaeee tạo đúng hai tệp trên. Đã đối chiếu đủ 43 source fingerprints của candidate.
- [PACKET_SHA256SUMS.txt](submission/PACKET_SHA256SUMS.txt) có 209 mục khớp khi ghép các tệp packet vào baseline hồ sơ 60d9b11. ZIP là packet một phần, không phải checkout đầy đủ.
- 15 hash evidence trong validation khớp; smoke manifest/run qua schema/validate_record, config hash và liên kết JSONL khớp. Số liệu SYNTHETIC/NOT_RUN, không chạy model.

[review-verification.json](review-verification.json) lưu kết quả kiểm tự động và mapping 19 tệp được lưu nguyên byte. Bản đối chiếu Markdown ở gốc ZIP có đường dẫn cục bộ, nên chỉ giữ hash/định danh trong metadata; bản gốc vẫn ở tệp người dùng đính kèm. Không công bố các đường dẫn đó. Thư mục `submission/` là nguồn được gửi, không phải source đã tích hợp.

## Kết quả kiểm

| Phép kiểm | Kết quả | Mức bằng chứng |
| --- | --- | --- |
| Windows client/hardening × 3 | Mỗi lượt 11 test = 10 ok + 1 skip; không marker bất ngờ | Đã đối chiếu log được gửi; chưa chạy lại Windows |
| Windows full suite × 3 | Mỗi lượt 110 test = 97 ok + 13 skip; không marker bất ngờ | Đã đối chiếu log được gửi; không phải full Windows acceptance |
| Linux full suite lượt 1 | 110/110, rc 0 | Chạy trực tiếp Linux/Python 3.12.14/psutil 7.2.2 |
| Linux full suite lượt 2 | 110/110, rc 0 | Chạy trực tiếp |
| Linux full suite lượt 3 | 109 đạt, 1 lỗi burst SIGINT gap 3 ms; rc -2 của CLI thay vì 130 | Chạy trực tiếp; giữ nguyên lượt FAIL |
| Test burst riêng, baseline47 | 10/10 lượt PASS | Chạy trực tiếp, xen kẽ với candidate |
| Test burst riêng, candidate | 9/10 PASS; lượt 4 SIGTERM gap 3 ms, rc -15 thay vì 130 | Chạy trực tiếp; nguyên nhân chính xác chưa chốt |
| Request hợp lệ với socket descriptor cao | Baseline PASS, candidate FAIL/CLIENT_ERROR | Hồi quy Linux xác nhận, cùng testcase |

Log Linux nằm ở [linux-review](linux-review), gồm [summary.json](linux-review/summary.json), [suite-3.log](linux-review/suite-3.log), [signal-comparison.json](linux-review/signal-comparison.json) và cả 20 log so sánh. Log Windows nằm trong [submission evidence](submission/task004/evidence/windows-client-cancel-20261107). Không đổi các lượt FAIL thành PASS sau phép kiểm bổ sung.

## AG-1 — P2: select.select làm hỏng request hợp lệ khi fd cao

[Candidate client.py dòng 45](submission/task004/client.py#L45) dùng `select.select([self._sock], ...)`. Trên Linux, socket fd từ 1024 trở lên vượt giới hạn FD_SETSIZE; exception được chuyển thành CLIENT_ERROR. Khi harness được nhúng trong tiến trình có nhiều file/socket đang mở, bản cũ xử lý được request mà bản vá từ chối.

Đã mở 1.050 file `/dev/null` trong subprocess thử nghiệm, server socket có fd 1053, rồi gọi cùng request mock hợp lệ. Baseline47 PASS/rc 0; candidate FAIL/rc 1. Xem [reproducer](linux-review/high-fd-regression.py), [baseline log](linux-review/high-fd-baseline47.log), [candidate log](linux-review/high-fd-candidate.log) và [metadata](linux-review/high-fd-summary.json). Script tự đóng các handle/server và skip khi giới hạn fd của máy quá thấp.

Yêu cầu sửa: dùng cơ chế selector/poll hỗ trợ descriptor cao trên POSIX, vẫn giữ cancellation/deadline và khả năng Windows. Thêm hồi quy có assertion tương đương reproducer. Không bắt ValueError rồi tiếp tục coi request thành công.

## AG-2 — cần xử lý: kiểm tín hiệu trên Linux chưa ổn định

Test `SignalArtifactTests.test_burst_signals_do_not_interrupt_cleanup_or_artifacts` thất bại trong một lượt full suite và một lượt kiểm riêng candidate; baseline đạt 10 lượt kiểm riêng. Các lỗi đều ở assertion exit 130 khi gửi ba tín hiệu cách 3 ms. Đây là failure quan sát được, chưa phải bằng chứng đã định vị được lỗi trong client.

Cần xác định tín hiệu đến trong request/cleanup hay sau lúc CLI phục hồi handler/kết thúc; đối chiếu stdout, artifact và thời điểm vòng đời. Trường hợp tín hiệu đến muộn sau hoàn tất đã được ghi là giới hạn; nếu đúng trường hợp đó, test cần đồng bộ pha và assertion theo phạm vi đã chốt. Không bỏ assertion hoặc chạy lại tới khi xanh rồi bỏ log FAIL. Sau thay đổi, lưu ba lượt hồi quy Linux liên tiếp thật sự đạt.

Ghi chú test không chặn riêng: các test cancel mới lấy marker phía server rồi sleep 20 ms, chưa chứng minh client đã vào đúng pha đọc trong mọi lượt. Nên dùng đồng bộ pha rõ cho hồi quy nhạy thời gian. Hướng RawIO + nonblocking phù hợp hơn việc tạo timeout từng nhịp trên buffered SocketIO, nhưng chưa đủ để chấp nhận candidate này.

## Nội dung gửi lại Antigravity

> Review REQUEST_CHANGES cho packet SHA-256 0bf2e4cd…745ec5d. Sửa AG-1: select.select trong client dòng 45 fail trên Linux khi socket fd ≥1024; reproducer kèm theo cho baseline PASS/candidate FAIL. Giữ hỗ trợ Windows và tổng deadline. Điều tra AG-2: Linux full suite lượt 3 fail burst SIGINT 3 ms; test riêng candidate fail 1/10 với SIGTERM 3 ms, baseline 0/10 fail. Phân loại pha tín hiệu và artifact trước khi sửa test; giữ mọi log FAIL. Sau sửa, gửi diff, exact source hashes/revision, baseline/fixed regression, ba lượt Linux và Windows phù hợp, checksum và handoff cập nhật. Chưa nâng parent Windows mock lên VERIFIED.

B1 connect bị chặn, console signals Windows, watchdog khi CLI chết, cây tiến trình sau cha thoát và kiểm environment Windows vẫn cần theo dõi riêng. Model/CVC và legacy không đổi. Review này không sửa source candidate hoặc tự tích hợp bản vá.
