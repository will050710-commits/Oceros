# TASK-004 — verdict ACCEPT do người dùng chuyển tiếp

Ngày ghi nhận: 07/11/2026 (Asia/Bangkok).

- Commit được review: `47aaeee91739c2f09ea30538e40c66e853653543`.
- Verdict: **ACCEPT — launcher/client/mock trên Linux**, bao phủ 8 mục WORK_COMPLETED trong handoff của commit này.
- Nguồn: nội dung review người dùng dán vào cuộc trò chuyện. Các thí nghiệm độc lập được kể bên dưới có nhãn **REPORTED**; agent không coi đó là các lượt chạy do mình vừa thực hiện.
- Không bao phủ Windows, model thật hoặc hai minor chưa được reviewer đối chiếu với review gốc. [Đối chiếu minor riêng](MINOR_CROSSCHECK.md) không thay đổi phạm vi verdict.
- Phần dưới là bản chép nội dung hiển thị của tin nhắn; người dùng không cung cấp tệp byte gốc của verdict. Review vòng hai gốc được lưu nguyên byte tại [ROUND2_REVIEW_ORIGINAL.txt](ROUND2_REVIEW_ORIGINAL.txt).

## Nội dung reviewer do người dùng cung cấp

Mình đang chạy lại chính runner evidence của packet (`validate_hardening.py`) trên máy mình để xem kết quả có tái lập được không.

Mình đang fuzz thêm đường provenance/index và kiểm vài điều kiện biên cuối cùng trước khi chốt verdict.

**Verdict: ACCEPT** cho launcher/client/mock trên Linux. Cả 8 finding vòng hai đều đã được xử lý và có test bắt đúng lỗi, mình không thấy lỗi chặn nào. Đây không phải chấp thuận cho Windows hay model thật.

Packet không liệt kê riêng các finding, nên mình lấy danh sách từ mục WORK_COMPLETED 1–8 của handoff.

| # | Finding | Kết quả kiểm |
| - | - | - |
| 1 | Deadlock khi signal lồng nhau | Tái hiện trên 07eb03c (treo, test timeout 3 s), pass trên 47aaeee. `CancellationFlag.set()` chỉ gán bool; đột biến quay lại `Event` hoặc thêm lock đều bị test bắt. |
| 2 | Ghi đè SIG_IGN/nohup | Tái hiện trên 07eb03c, đã sửa. CLI thật: SIGHUP bị ignore thì vẫn PASS, SIGHUP thường thì exit 130. |
| 3 | rc=0 nhưng có `Exception ignored`/ResourceWarning/Traceback | Gate có ở runner và test; 0 marker trong mọi log thành công, kể cả các lượt trước. |
| 4 | Lỗi init/cleanup/provenance lộ traceback | Init nằm trong `try`, `main()` có chốt INTERNAL_ERROR. Fuzz hơn 30.000 provenance index không rò exception ngoài ValueError. |
| 5 | Cleanup lỗi vs CANCELLED/TIMEOUT | Cleanup lỗi thì FAIL. Signal đến sau khi request xong chỉ bị hấp thụ, kết quả PASS giữ nguyên. Chính sách nhất quán và có test; đây là quyết định thiết kế, không phải lỗi. |
| 6 | Reason registry, PASS cần resource evidence | 3 mã mới có trong enum schema và AST test; PASS yêu cầu samples>0 và RSS>0. |
| 7 | Runner: archive, scope, fingerprint, đường dẫn | Chạy lại toàn bộ runner: PASS, khớp packet từng run. 43/43 fingerprint khớp file đã commit; log và artifact của packet không có đường dẫn tuyệt đối. |
| 8 | Test artifact độc lập, atomic | Lỗi chèn vào 2 open, 2 fsync và rename (OSError, KeyboardInterrupt) đều dọn staging; burst signal trong cleanup/ghi file vẫn ra kết quả đã commit. |

**Phạm vi đã kiểm** (HEAD của `main` khi clone đúng là 47aaeee91739c2f09ea30538e40c66e853653543):

- **Toàn vẹn packet:** `round2.patch` áp lên 07eb03c và `review.patch` áp lên 2cb9168 đều ra đúng 23 file của 47aaeee. `CURRENT_SOURCE.md` khớp nội dung và hash với 28 file, `SHA256SUMS` 171/171 OK. Hai lượt evidence FAIL trước đó vẫn được giữ nguyên như handoff nói.
- **Chạy lại:** suite 106/106 ba lượt liên tiếp (Python 3.12.3, psutil 7.2.2; packet dùng 3.12.14), 0 marker. Thêm 6 lượt các test signal/cleanup dưới tải CPU, 6/6 pass.
- **Đột biến tự làm:** 14 điểm trong bản sửa, 14/14 bị đúng test mục tiêu bắt.
- **CLI thật:**
  - SIGTERM giữa request: exit 130 sau khoảng 0,04 s, artifact đủ.
  - SIGKILL CLI: mock tự thoát trong khoảng 0,15 s.
  - Burst 6 signal: exit 130, không traceback.
  - 6 scenario mock cho đúng mã thoát.
  - Sau tất cả không còn process mock hay thư mục scratch.
- **Artifact dry-run đã commit:** qua validator của repo, hash khớp, `SYNTHETIC`/`NOT_RUN`, không API call, phase metric `null`.

**Giới hạn còn lại:**

- **Windows chưa xác minh:** Job Object, `socket.shutdown` đánh thức recv, Ctrl+C console, SIGBREAK, rename thư mục, GetPerformanceInfo. Các test signal chỉ chạy trên POSIX.
- **Model thật chưa chạy:** mọi số là synthetic, latency 0,7 ms không nói gì về hiệu năng thật.
- **Hai "minor" chưa đối chiếu:** packet không nêu tên và mình không có văn bản review vòng hai gốc. Verdict chỉ bao phủ 8 mục trên.
- **Test deadlock dựa trên trace của CPython:** bảo đảm thật là cấu trúc (không lock trong `set()`), không chứng minh cho interpreter hay OS khác.
- **Giới hạn của log gate và ghi file:** gate chỉ thấy output được thu thập (stdout/stderr của mock đi vào DEVNULL). SIGKILL giữa lúc ghi vẫn có thể để lại staging, không fsync thư mục.
- **B1:** worker connect bị chặn có thể sống tới `timeout_s`, nhưng theo code đó là daemon thread nên không giữ CLI lại. Chỉ đáng kể nếu nhúng như thư viện.

**Ghi chú nhỏ, không chặn:**

- `validate_record` ném `OverflowError` thay vì ValueError khi metrics là số nguyên cực lớn (`math.isfinite(10**400)`). Không đạt được từ CLI vì metrics do harness tự tính, và `main()` sẽ chặn thành INTERNAL_ERROR. `config.py` đã bắt OverflowError, `record.py` thì chưa.
- Hai test `test_a4_existing_committed_evidence_remains_valid` và `test_a4_run_schema_rejects_bad_reason_time_token_and_id` đọc evidence đã commit, nên chạy suite trên bản copy không có `task004/evidence/` sẽ fail 2 test. Handoff đã nói đây là chủ đích; mình gặp khi tự chạy đột biến.

Nếu bạn dán văn bản review vòng hai gốc, mình sẽ đối chiếu từng dòng, gồm cả hai minor.
