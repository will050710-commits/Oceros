# TASK-004 — Handoff review vòng hai

Ngày 07/11/2026 (Asia/Bangkok); timestamp artifact dùng UTC. Báo cáo này thay handoff 06/11; các nguồn và evidence đã commit được giữ nguyên.

## TASK_ID

TASK-004.

## OWNER

Codex. Một agent hỗ trợ sửa record/provenance; agent chính hoàn tất code/tests/runner. Không giả nhận review chấp thuận độc lập. Nội dung review người dùng gửi là nguồn yêu cầu, các thí nghiệm reviewer báo được tái kiểm khi nêu dưới đây.

## STATUS

**IMPLEMENTED / READY_FOR_REVIEW — Linux-verified trong phạm vi mock.** Đã sửa hoặc xác định chính sách và kiểm thử cả mục 1–8 cùng hai minor. Ba lượt suite release PASS, log gate PASS. Windows UNVERIFIED; model thật NOT_RUN.

## BASELINE_REVISION

Review dựa trên `07eb03cd0f01d16feef6f090cd5ed74c4c075eeb`; baseline ban đầu cho A1–A5 là `2cb916803cef6c2c52f03107fddeb866c407ae27`. Đã đối chiếu 4/4 prefix SHA reviewer cung cấp cho cli.py, record.py, test_hardening_record.py và validate_hardening.py: khớp revision 07eb03c. Code ở GitHub trước phiên đúng bản được reviewer đọc.

## FILES_READ

Đọc toàn bộ review dán, source/tests/runner/schema và evidence của bản 07eb03c; đối chiếu handoff/context. Không tái nghiên cứu model hoặc xác minh lại claims hardware/license trong tài liệu nguồn. References và evidence cũ không sửa.

## FILES_CHANGED

Thêm cancellation.py, unit fixture builder và tests review CLI/record/runner. Sửa cli.py, record.py, run schema, tests artifact/workflow và runner. Cập nhật README/HANDOFF/SHA256SUMS; thêm evidence review vòng hai, cumulative review.patch, round2.patch và CURRENT_SOURCE.md để reviewer đọc đầy đủ source. Dependency vẫn stdlib + psutil 7.2.2.

## WORK_COMPLETED

1. Thay Event trong CLI bằng CancellationFlag đơn điệu: set chỉ gán boolean, is_set đọc boolean, wait polling/time.sleep, không lock hoặc clear. Test ép tín hiệu thứ hai vào đúng dòng Event.set giữ lock làm baseline treo có timeout kiểm soát; bản sửa hoàn tất.
2. Giữ nguyên inherited SIG_IGN (gồm nohup/SIGHUP). Không cài đè handler mà Python báo None, vì không thể phục hồi None bằng signal.signal. Các handler đã thay đều được phục hồi.
3. Runner không chỉ tin rc=0: fixed/suite/dry-run bị fail khi có Exception ignored, ResourceWarning hoặc Traceback. PYTHONWARNINGS truyền vào subprocess test/CLI; tests giữ stderr của CLI cũng kiểm ba marker. Test riêng sinh socket leak finalizer trả rc=0 để chứng minh gate bắt được.
4. Preflight/server init vào try, có fallback metadata null khi chưa đo; sampler/server cleanup bắt Exception; main có last-resort JSON INTERNAL_ERROR không lộ nội dung exception. Provenance index kiểm shape/path/type/hash và báo ValueError có mã an toàn.
5. **Chính sách cleanup:** lỗi sampler/server cleanup ưu tiên hơn CANCELLED/TIMEOUT → FAIL/MEMORY_SAMPLING_FAILED hoặc CLEANUP_FAILED, exit 1. Không âm thầm gọi cleanup thất bại là hủy thành công. Signal đến sau request đã hoàn tất chỉ được hấp thụ để hoàn tất cleanup/ghi artifact, không đổi kết quả PASS đã hoàn tất. Có test cho cả hai chính sách.
6. Bổ sung NON_LOOPBACK_ENDPOINT, SERVER_NOT_STARTED, SERVER_ALREADY_STARTED vào reason registry/schema. AST test kiểm các literal ClientError/ServerError phát ra đều được đăng ký. PASS yêu cầu samples>0 và RSS dương trong validate_record, không chỉ CLI.
7. Temp archive destination được resolve trước khi kiểm containment. Scope dựa vào platform thực, không hardcode Linux. Fingerprint thêm mock_config, requirements/setup và toàn bộ references. Command/cwd dùng placeholder; log chỉ chuẩn hóa các prefix đường dẫn local đã biết để tránh username, giữ nguyên chẩn đoán.
8. Artifact unit tests dựng fixture riêng, không lấy immutable runtime evidence. Chèn OSError/KeyboardInterrupt tại hai open, hai fsync và rename; tất cả dọn staging. Signal subprocess chờ marker request-phase thay sleep đoán pha; test riêng đưa burst signal đúng trong cleanup và ghi file. Pre-set cancel đã có test ngăn spawn.

## EVIDENCE

Evidence release: `evidence/review2-20261107-release/validation.json`; bắt đầu 2026-11-06T17:48:18.633107+00:00, kết thúc 2026-11-06T17:48:59.673773+00:00. Python 3.12.14, psutil 7.2.2. Summary sinh tự động từ subprocess; fingerprint source/tests/schema/config/references được kiểm không đổi trong suốt lượt.

- `review-baseline-test_nested_signal_cannot_deadlock_handler.log`: lỗi deadlock tái hiện trên 07eb03c, timeout được test chuyển thành assertion đúng lỗi. `fixed-review-*.log`: bản sửa PASS.
- `review-baseline-test_inherited_ignore_is_preserved.log`: tái hiện inherited ignored SIGHUP bị đổi thành yêu cầu hủy; fixed PASS.
- `baseline-A1.log` … `baseline-A4.log`: runner yêu cầu từng FAIL block đúng method và fragment assertion của defect, không chấp nhận một assertion bất kỳ hoặc import error. Baseline lỗi có chủ đích vẫn được giữ traceback để review.
- `baseline-mutant-A5-undetected.log` và `mutation-A5.log`: test cũ bỏ lọt guard bị xóa, test mới bắt được. A5 functional test vẫn PASS baseline nguyên bản vì guard đã tồn tại.
- Dry-run `552dd6b3afe24dda8421ceb2d550e28d`: PASS/OK/SYNTHETIC, exit 0, log gate sạch. Manifest/JSONL trong dry-run/ của thư mục release.
- Log vòng trước hardening-20261106-final không có Exception ignored/ResourceWarning. Đây chỉ là kiểm nội dung log, không chứng minh tất cả tiến trình chưa từng leak.
- Lượt `review2-20261107` có suite PASS nhưng summary FAIL vì matcher A4 ban đầu chỉ nhận schema assertion, chưa nhận config assertion cùng kiểm biên. Lượt `review2-20261107-final` PASS trước khi thêm gate stderr trong test giữ output của CLI. Release đã chạy lại đầy đủ sau thay đổi cuối. Giữ nguyên các evidence đó, không chỉnh tay số liệu.

## TESTS_EXECUTED

Từ repo root:

```bash
/workspace/.venvs/oceros-task004/bin/python task004/tools/validate_hardening.py --output task004/evidence/review2-new-run
```

Runner lấy Git archive của hai baseline, chạy selected regressions trên cũ/mới, mutation cũ/mới, rồi `python -W error::ResourceWarning -m unittest discover -s task004/tests -v` ba lần liên tiếp và dry-run. Không sửa working source, không tạo worktree. Lệnh socket/tín hiệu dùng quyền executor cho loopback. Test leak finalizer là fixture cố ý, output được test đưa qua gate thay vì để cảnh báo ẩn.

## TEST_RESULTS

| Lượt | Tests | Failures | Errors | Skipped | Wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| suite-1 | 106 | 0 | 0 | 0 | 10.372 |
| suite-2 | 106 | 0 | 0 | 0 | 10.299 |
| suite-3 | 106 | 0 | 0 | 0 | 10.326 |

Cả ba lượt 106/106; không diagnostic marker bị chặn, không failed expectation. Kiểm A1–A5 và hai hồi quy mới đạt kết quả mong đợi. Generated metadata hiện dùng placeholder thay đường dẫn interpreter/cwd cá nhân. Source schema/artifact integrity được đối chiếu riêng sau validation.

## BENCHMARK_RESULTS

NOT_RUN. Không model thật, TTFT/prefill/decode thật, corpus/scorer/CVC, freeze hay PROMOTE. Các artifact runtime chỉ SYNTHETIC; metric không hỗ trợ để null.

## COST_OR_RESOURCE_USAGE

Không API model trả phí, model downloads, training, Colab/GPU hay mua dịch vụ. Chi phí/token phiên ChatGPT không được cung cấp; UNKNOWN. Thời gian subprocess test trong bảng là quan sát thực; không đo tổng tài nguyên phiên.

## KNOWN_LIMITATIONS

- Windows UNVERIFIED: chưa có Job Object; chưa kiểm socket.shutdown đánh thức recv từ thread khác, Ctrl+C toàn console, SIGBREAK, directory rename, SYSTEMROOT allowlist, GetPerformanceInfo/private bytes hay wheel psutil 7.2.2 CPython 3.14. Test simulating platform label không xác minh Windows runtime.
- B1 ở client giữ primary cancellation nhưng worker connect bị chặn có thể tồn tại tới socket timeout (cận 3600s). Chưa dùng nonblocking connect. Cleanup thất bại ở cấp run có chính sách FAIL riêng như trên.
- CancellationFlag là cờ đơn điệu tối thiểu, không phải Event tổng quát; không clear/reset. Test reentrancy tại Python handler không phải bằng chứng cho mọi interpreter/OS.
- Signals sau khi CLI hoàn tất/khôi phục handler thuộc hành vi OS; SIGKILL không thể tạo artifact/finally. Watchdog dọn mock, nhưng SIGKILL giữa ghi có thể để staging. Không directory fsync/power-loss guarantee.
- Log gate phát hiện marker trong output đã thu thập; không chứng minh không có leak ở output đã bị devnull, bị cắt hoặc tiến trình ngoài phạm vi. Mock server vẫn quiet theo thiết kế. Chuẩn hóa prefix local không phải bộ lọc mọi PII tùy ý; không ghi secrets/raw nội dung ứng dụng.
- Fixture compatibility riêng của schema vẫn đọc evidence lịch sử có chủ đích; atomic unit tests đã tách dependency đó. Source reference integrity không xác minh model/license/hardware claims.

## RISKS

Nhầm test PASS với leak-free tuyệt đối, Linux với Windows, mock với model; nhầm expected baseline traceback là lỗi release. Cần đọc validation.json cùng log và các giới hạn. Top-level safe error có thể không có artifact nếu chính việc ghi artifact hoặc metadata nguồn bị hỏng; khi đó CLI báo FAIL/INTERNAL_ERROR hoặc ARTIFACT_WRITE_FAILED thay traceback, không tuyên bố đã lưu kết quả.

## RECOMMENDATION

Reviewer đọc CURRENT_SOURCE.md, cumulative review.patch, round2.patch, validation.json và các baseline logs được gửi đầy đủ trong release directory. Không coi review vòng trước giới hạn tập file là review đầy đủ source. Tiếp tục giữ runtime thật khóa tới khi review/điều kiện môi trường riêng được chốt.

## NEXT_ACTION

Gửi commit và release review packet cho reviewer để đưa verdict mới. Nếu chấp nhận, Windows là bước xác minh riêng; không tự mở model thật hoặc CVC. GitHub có source và log để người dùng đọc trực tiếp, không cần tải ZIP.

## UNVERIFIED_CLAIMS

Windows/model thật/hardware laptop/model flags/license/corpus/gold/tokenizer/DEV/bridge/CVC/freeze, review chấp thuận mới và publish/restore môi trường. Thí nghiệm reviewer báo giữ REPORTED ngoại trừ những lỗi đã tái hiện cụ thể trong log của phiên này.
