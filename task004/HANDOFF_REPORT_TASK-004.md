# TASK-004 — Handoff hardening A1–A5 / B1–B4

Ngày 06/11/2026 (Asia/Bangkok). Artifact/log dùng UTC. Báo cáo này thay báo cáo implementation ban đầu; nguồn handoff lịch sử trong references/ và evidence đã commit giữ nguyên byte.

## TASK_ID

TASK-004.

## OWNER

Codex; các agent hỗ trợ triển khai và rà soát. Không giả nhận review chấp thuận của Claude C. Brief sửa và số 75 test dựng thử do người dùng cung cấp là REPORTED, không phải evidence của lượt này.

## STATUS

**IMPLEMENTED / READY_FOR_REVIEW — Linux-verified, chỉ launcher/client/mock.** A1–A5 và B1–B4 đã xử lý; toàn bộ suite chạy ba lần liên tiếp PASS. Windows UNVERIFIED, model thật NOT_RUN.

## BASELINE_REVISION

`2cb916803cef6c2c52f03107fddeb866c407ae27`, đã commit/push lên GitHub ở đợt trước. Bản sửa hiện hành được đóng gói cùng code, tests, báo cáo và evidence để review. Nguồn yêu cầu là brief A1–A5/B1–B4 người dùng gửi trong phiên 06/11. Giữ quyết định scope launcher/mock; không gộp ticket/ledger/CVC.

## FILES_READ

Đối chiếu baseline, brief review, code/tests hiện hành, README, handoff trước, hai schema và evidence cũ. Context/task nguồn giữ trong CONTEXT.md/references; không nghiên cứu lại model hay xác minh những claim trong nguồn. Hai schema version 1 mới vẫn nhận manifest/record đã commit.

## FILES_CHANGED

Sửa cli/client/config/mock_server/record/sampler/schema/server, hai JSON schema, test loopback cũ. Thêm bốn module test_hardening_*, runner `tools/validate_hardening.py`, log kiểm thử/mutation/baseline, dry-run mới, diff review và cập nhật README/HANDOFF/SHA256SUMS. Các tệp evidence cũ và references không bị sửa. Không thay dependency: chỉ stdlib + psutil==7.2.2.

## WORK_COMPLETED

- A1: mock nhận parent PID và lifetime=startup_timeout+timeout+30; watchdog daemon giữ psutil Process identity, thoát khi cha mất/zombie hoặc hết hạn; xóa scratch riêng khi cha mất. Không tạo được parent Process thì thoát ngay.
- A2: các signal có hỗ trợ SIGINT/SIGTERM/SIGHUP/SIGBREAK chỉ đặt cancel Event, hấp thụ lặp; khôi phục handlers. Giữ KeyboardInterrupt cho library. Artifact được validate/encode trước; ghi/fsync JSONL rồi manifest trong staging; một rename công bố thư mục. Mọi BaseException trong ghi/rename dọn staging; không ghi đè run có sẵn.
- A3: timeout/startup/delay tối đa 3600 giây; sample interval 0.01–60. Cấu hình 1e10/1e300 bị chặn trước runtime.
- A4: schema có cận số, anchored patterns, reason enum, timestamp shape, integer/null token. check_schema đệ quy fail-closed với keyword hoặc cấu trúc không hỗ trợ. Version giữ 1. Quan hệ status↔reason ở validate_record; pairing ảnh ở Config.
- A5: test endpoint chặn đúng NON_LOOPBACK_ENDPOINT và không tạo HTTPConnection; bằng chứng mutation cũ/mới được lưu.
- B1: cleanup không đè primary cancellation/KeyboardInterrupt. B2: không signal process group rỗng. B3: env allowlist PATH/SYSTEMROOT/TEMP/TMP/LANG/LC_ALL. B4: CONFIG_ONLY, phân biệt commit unavailable do thiếu sample/platform, ValueError artifact ra JSON INTERNAL_ERROR thay traceback.

## EVIDENCE

Evidence hiện hành: `evidence/hardening-20261106-final/validation.json`; sinh tự động bằng runner, cùng raw logs từng subprocess. Bắt đầu `2026-11-06T11:30:09.259824+00:00`, kết thúc `2026-11-06T11:30:46.999551+00:00`. Python 3.12.14, psutil 7.2.2. File này chứa command, exit codes, số test và SHA-256 của source/test/schema/runner lúc chạy; xác nhận source không đổi trong suốt lượt kiểm.

- `baseline-A1.log` … `baseline-A4.log`: assertions thất bại trên production baseline; `fixed-A1.log` … `fixed-A4.log`: cùng test qua code mới. Không dùng import error làm bằng chứng hồi quy.
- A5 là sửa độ mạnh của test, không sửa guard production vốn đã tồn tại. Vì vậy functional test A5 vẫn PASS trên baseline. `baseline-mutant-A5-undetected.log` cho thấy test cũ PASS dù bỏ guard; `mutation-A5.log` cho thấy test mới FAIL với cùng mutation. `mutation-A5-removed-guard.txt` ghi block đã xóa. Không tuyên bố A5 functional test fail trên baseline nguyên bản.
- Dry-run mới ID `c728f4bfa7ee4ac9b85067c8f8c222ea`, exit 0, PASS/OK/SYNTHETIC; manifest/JSONL trong `dry-run/c728f4bfa7ee4ac9b85067c8f8c222ea/`.
- `review.patch` là diff source/tests/tools/docs so với baseline; không chứa evidence/checksum để tránh vòng tự tham chiếu. SHA256SUMS bao toàn bộ bộ bàn giao, gồm logs và diff.
- Giữ cả lượt kiểm ban đầu `evidence/hardening-20261106/`: ba suite đã PASS, nhưng runner đánh dấu FAIL vì cơ chế injection A2 không bắt cách Path.open dùng keyword ở baseline và vì mong nhầm functional A5 phải fail. Sau sửa test/runner, lượt final ở trên xác minh lại toàn bộ. Không chỉnh tay hoặc thay thế log của lượt đó.

## TESTS_EXECUTED

Lệnh tái tạo từ repo root (output cần mới):

```bash
/workspace/.venvs/oceros-task004/bin/python task004/tools/validate_hardening.py --output task004/evidence/hardening-new-run
```

Runner thực thi `python -W error::ResourceWarning -m unittest discover -s task004/tests -v` ba lần liên tiếp. Baseline lấy bằng git archive vào thư mục tạm; mutation chạy trên bản sao; không sửa working source hoặc tạo worktree. Dùng require_escalated cho socket loopback/tín hiệu test do sandbox mặc định chặn socket.

## TEST_RESULTS

| Lượt | Tests | Failures | Errors | Skipped | Wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| suite-1 | 87 | 0 | 0 | 0 | 10.300 |
| suite-2 | 87 | 0 | 0 | 0 | 10.375 |
| suite-3 | 87 | 0 | 0 | 0 | 10.386 |

Số test thực tế ba lượt: 87, 87, 87; khác số 75 trong bản dựng thử của reviewer vì bộ test ở đây chia thành các method khác. Không có lỗi/skip ở suite hiện hành. Cả SIGINT/SIGTERM/SIGHUP đơn lẻ, burst SIGINT/SIGTERM khoảng cách 0/1/3 ms, SIGKILL watchdog, staging OSError/KeyboardInterrupt, bounds/schema và real Linux blocked-connect đã thực thi. Không coi expected baseline/mutant failure là lỗi suite mới.

## BENCHMARK_RESULTS

**NOT_RUN.** Dry-run chỉ SYNTHETIC. Không model inference, TTFT thật, prefill/decode, corpus/scorer/CVC hoặc baseline campaign. Metric phase giữ null; dataset chưa freeze; không PROMOTE.

## COST_OR_RESOURCE_USAGE

Không gọi API model trả phí, tải model, training, Colab/GPU hay mua dịch vụ. Runtime psutil đã có. Thời gian test trong bảng lấy từ runner thật; không đo tổng CPU/RAM hoặc chi phí/token phiên ChatGPT. Resource samples trong dry-run chỉ thuộc mock trên máy cloud.

## KNOWN_LIMITATIONS

- **Windows UNVERIFIED**: chưa có Job Object; chưa kiểm socket.shutdown đánh thức recv từ thread khác, Ctrl+C phát toàn console, SIGBREAK, os.rename thư mục, SYSTEMROOT allowlist, GetPerformanceInfo/private bytes, wheel psutil==7.2.2 cho CPython 3.14. Chỉ ghi POSIX changes là Linux-verified.
- B1 giữ primary cancellation nhưng connect worker daemon có thể còn tới socket timeout (cận 3600 giây). Chưa chuyển connect sang nonblocking; không khẳng định mọi cancel dừng mọi worker ngay.
- Signal handler chỉ yêu cầu hủy; tín hiệu đến sau khi chương trình đã kết thúc nằm ngoài hợp đồng. SIGKILL không thể ghi artifact hoặc chạy finally; watchdog ngăn mock tiếp tục sống. SIGKILL giữa các lần ghi có thể để lại staging chưa công bố.
- Atomic rename là công bố cả thư mục cùng lúc, không chứng minh crash/power-loss durability; không fsync thư mục. Output directories giả định nằm trong workspace tin cậy, không chống đối thủ đồng thời thay path.
- Fixed mock không daemonize hoặc spawn model; process group không bắt tiến trình cố ý tách session. Watchdog có độ trễ polling và lifetime dự phòng.
- Sampling không bao startup/harness và có thể bỏ lỡ peak ngắn. Pixel/token config chưa tokenize ảnh thật. Schema chỉ hỗ trợ tập keyword công bố, không phải engine JSON Schema đầy đủ.
- Model/runtime flags/hardware laptop và quyền corpus vẫn chưa xác minh. Không publish môi trường trong lượt sửa này.

## RISKS

Nhầm SYNTHETIC thành benchmark; nhầm Linux-verified thành Windows-verified; dùng config guard mock làm ngân sách model; coi hash input là bằng chứng runtime/license. Các cổng model thật giữ khóa. Expected-failure logs phải được đọc cùng validation.json, không đánh đồng với suite mới fail.

## RECOMMENDATION

Review diff, log final và nguồn tests để quyết định chấp nhận bản hardening. Tách Windows/model thật/CVC thành đợt có điều kiện riêng. Review nội bộ của agent không thay review chấp thuận độc lập của Claude C.

## NEXT_ACTION

Chuyển commit/diff và thư mục evidence final cho reviewer; dùng các link GitHub của bản cập nhật để đọc trực tiếp. Sau chấp nhận, kiểm Windows với các giới hạn nêu trên trước khi nối runtime thật. Không tự mở calibration/model/corpus từ mock PASS.

## UNVERIFIED_CLAIMS

Windows, model thật, hardware laptop, model/mmproj/flags/license, corpus/gold/tokenizer/DEV/bridge/CVC, freeze, review độc lập mới và restore/publish môi trường. Kết quả 75/75 của bản dựng thử là USER-REPORTED; số trong báo cáo hiện hành lấy từ runner thực thi mới.
