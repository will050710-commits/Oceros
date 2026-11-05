# TASK-004 — Bàn giao launcher/client/mock

Ngày 05/11/2026 (Asia/Bangkok). Thời gian máy và artifact dùng UTC.

## TASK_ID

TASK-004.

## OWNER

Codex trong phiên hiện tại; có các agent hỗ trợ đọc nguồn, triển khai config/preflight và rà soát code. Đây không phải review bên ngoài của Claude C.

## STATUS

**IMPLEMENTED — phạm vi launcher/client/mock đã được người dùng chọn; Linux mock validation PASS.** Sẵn sàng review mã. Windows/model thật/benchmark chưa thực thi. Không tuyên bố đạt mọi AC của prompt gốc chưa được cung cấp hoặc phiếu ticket/ledger cũ.

## BASELINE_REVISION

- Kho `/workspace/Oceros`, HEAD ban đầu `241af99ed0fd0d26f393281c78864c75f90fd192` (Initial commit). Thay đổi mới còn ở working tree; chưa commit/push.
- Người dùng đã chọn “launcher/client/mock theo khuyến nghị handoff” trong phiên; điểm BLOCKED về lựa chọn phạm vi trong handoff cũ đã được giải quyết.
- Ba hash khóa TASK-002 v2.3/spec v0.3.2/CVC rev1.1 đều MATCH; xem `CONTEXT.md` và `references/provenance.json`.
- Prompt gốc 05/11, phiếu gốc 24/10 và hardware JSON không có trong đầu vào. Thiết kế áp dụng theo bản tóm tắt handoff đã được người dùng chọn.

## FILES_READ

Đọc card TASK-002 v2.3, toàn bộ handoff TASK-004 được gửi, spec TASK-003 v0.3.2, CVC rev1.1, handoff/closure thiết kế, errata/review lịch sử và notice. Đọc cấu trúc/metadata hai JSON numerical audit; không tái chạy mô phỏng thiết kế. Đối chiếu SHA-256 và byte của 11 tệp nguồn lưu trong `references/`.

## FILES_CHANGED

- Thêm `.gitignore`, package `task004/`: config, preflight, server, client, sampler, record, mock_server, cli, schema và interfaces tương lai.
- Thêm 4 module unittest, hai JSON schema, config mẫu, `requirements.txt`, `setup.sh`, README, CONTEXT và báo cáo này.
- Thêm bản sao nguyên byte các nguồn, chỉ mục provenance, evidence dry-run/validation và `SHA256SUMS`.
- README gốc và các tệp tracked trước phiên không thay đổi. Không sửa nguồn đầu vào hay ghi đè handoff lịch sử.
- Đã lưu draft môi trường: `install_script`, `start_skill`. Công cụ xác nhận `saved`, `requires_publish=true`; chưa publish, chưa xác minh restore trong task mới.

## WORK_COMPLETED

1. Tổng hợp context; giải quyết scope qua lựa chọn trực tiếp của người dùng; giữ ranh giới TASK-003 CVC và nhiệm vụ quản lý nghiên cứu cũ.
2. Cài venv riêng `/workspace/.venvs/oceros-task004` với psutil 7.2.2, kiểm chạy lại setup idempotent.
3. Triển khai cấu hình strict: mock-only, n_ctx bắt buộc, non-thinking, output 1–96, ảnh ≤768 cùng token cap, kiểu số/JSON hợp lệ.
4. Preflight RAM available/đĩa hiện tại; Windows commit qua ctypes hoặc null kèm lý do. Ngưỡng mẫu chỉ dành cho mock.
5. Launcher mock loopback port động, health readiness, HTTP client bounded, tổng deadline/cancel, xử lý lỗi HTTP/JSON/connection và giới hạn kích thước response.
6. POSIX session sở hữu riêng và cleanup kể cả cha đã thoát/con chống TERM; kiểm giữ tiến trình không liên quan. HTTP worker được hủy khi body stall/trickle; không còn worker sau timeout/cancel đã kiểm.
7. RSS tổng đồng thời theo cây; commit/phase metric không đo được để null. Ghi manifest/JSONL có schema và checksum, nhãn SYNTHETIC, không raw prompt/response/env/secrets.
8. Chạy bộ kiểm thử và CLI thực trong venv; giữ dry-run riêng làm bằng chứng; lưu cấu hình tái sử dụng.

## EVIDENCE

- Test run hiện hành: **59 tests, 0 failures, 0 errors, 0 skipped**, hoàn thành 5.729 giây, Python 3.12.14/Linux, psutil 7.2.2. Kết quả tóm tắt trong `evidence/validation.json` là bản ghi từ kết quả runner, không giả là log stdout nguyên bản.
- Dry-run CLI: `evidence/dry-run/e1979d42784948cfbeb13b44cbc6044a/manifest.json` và `runs.jsonl`, PASS/OK/SYNTHETIC. Manifest ghi hash JSONL và cấu hình, provenance 11 nguồn MATCH.
- RSS mock quan sát: 14,528,512 byte; tổng thời gian lượt 0.055799752 giây; request 0.000623560 giây. Đây là một fixture tổng hợp, không phải hiệu năng model/laptop hoặc baseline. Có 2 mẫu RSS; không đo startup và có thể bỏ lỡ đỉnh giữa các mẫu.
- Kiểm GitHub read-only bằng proxy/xác thực sẵn có thành công, remote HEAD khớp HEAD ban đầu. Lỗi kết nối trước đó ở sandbox mặc định không phải bằng chứng thiếu token.
- `git diff --exit-code` và `git diff --check` đều thành công cho các tệp tracked cũ; sản phẩm mới vẫn untracked để người dùng review.

## TESTS_EXECUTED

Từ `/workspace/Oceros`:

```bash
/workspace/.venvs/oceros-task004/bin/python -W error::ResourceWarning -m unittest discover -s task004/tests -v
bash task004/setup.sh
/workspace/.venvs/oceros-task004/bin/python -m task004.cli preflight
/workspace/.venvs/oceros-task004/bin/python -m task004.cli dry-run --output-dir task004/evidence/dry-run
```

Các lệnh có socket chạy qua `require_escalated` được chấp thuận cho loopback. Sandbox mặc định đã được chẩn đoán là chặn socket. Không tắt TLS, sửa checksum package hay bypass chính sách mạng.

## TEST_RESULTS

PASS: 25 config/preflight, 13 server/lifecycle, 3 HTTP body/deadline, 18 workflow/artifact/CLI = 59. Bao gồm test biên số/cap/RAM/đĩa, malformed config, health failure, mock faults, cancellation trước/trong startup/request, tree cleanup, parent-exit, SIGTERM-resistant child, safe errors, schema nested, checksum, log không chứa secret marker, repeated runs, adapter thật disabled.

Setup chạy lại giữ psutil đúng phiên bản; validate-config PASS; preflight ready; dry-run exit 0. Rà soát đã phát hiện và sửa lỗi cleanup sau cha thoát, socket HTTP/1.0 đang đọc body và JSON integer vượt giới hạn parser; các regression tương ứng đều PASS. Không có test đang fail hoặc bị bỏ qua trong lượt Linux này.

## BENCHMARK_RESULTS

**NOT_RUN.** Không có model inference, TTFT thật, prefill/decode tok/s, baseline, P-60, corpus/scorer/CVC execution hoặc dataset freeze. Metric phase và dataset hash giữ null; không có PROMOTE.

## COST_OR_RESOURCE_USAGE

Không gọi API model trả phí độc lập, tải weights, training, Colab/GPU hoặc mua dịch vụ. Dependency psutil được tải qua package registry. Chi phí/token toàn phiên ChatGPT không được công cụ cung cấp nên UNKNOWN. Không đo tổng CPU/RAM toàn phiên. Số mock trong EVIDENCE chỉ mô tả lượt đã lưu.

## KNOWN_LIMITATIONS

- Chưa chạy Windows 11/Python 3.14; ctypes system commit/private bytes và cleanup Windows UNVERIFIED. Windows live-tree fallback chưa bảo đảm giữ được con sau khi cha chết; chưa có Job Object. Fixed mock không sinh con.
- POSIX đã kiểm process group sở hữu; không hỗ trợ tiến trình cố ý daemonize/tách session. Không dùng adapter này cho binary tùy ý.
- Sampling từ sau health readiness, không bao startup/harness; không khẳng định bắt mọi đỉnh RAM. Ngưỡng mock 64 MiB/10 MiB không thay yêu cầu hardware/model.
- Image config chỉ kiểm khai báo; chưa đọc/tokenize ảnh. P-60/top-K chỉ interface. Không sinh llama.cpp flags chưa kiểm chứng.
- Source hash xác minh byte, không xác minh model/license/review/hardware claims. Prompt/ticket/hardware gốc còn thiếu.
- Code chưa commit/push; draft chưa publish/restore-test. Cấu hình saved không tự đưa source lên GitHub.

## RISKS

Nhầm PASS mock thành model/benchmark PASS; nhầm RAM cloud với laptop; dùng cap generic 768 thay cap benchmark 512/192; coi schema hash là dataset freeze; triển khai runtime thật từ cờ chưa kiểm chứng. Những phần này được tách rõ và model adapter vẫn bị khóa.

## RECOMMENDATION

Review package launcher/mock hiện tại. Đọc `CONTEXT.md` trước khi nối runtime thật hoặc nhận CVC. Giữ trạng thái thiết kế/corpus/model theo nguồn; không nâng bằng chứng vì mock chạy được.

## NEXT_ACTION

1. Người dùng/reviewer kiểm code, báo cáo và checksum; chưa có review chấp nhận từ Claude C trong phiên này.
2. Để tái sử dụng snapshot cloud: xem và lưu thay đổi trong Environment Settings, rồi Publish khi muốn kích hoạt cấu hình. Đây là thao tác còn lại do giao diện môi trường quản lý, chưa được thực hiện trong phiên.
3. Windows và adapter/model thật là đợt xác minh riêng: cần nguồn hardware, binary/version/flags và các điều kiện/quyền của đợt đó. CVC/corpus vẫn là công việc riêng, không tự tiếp tục từ mock PASS.

## UNVERIFIED_CLAIMS

Windows, hardware laptop, Qwen/mmproj/runtime hỗ trợ, ngưỡng/token ảnh thật, model performance, license/corpus/gold, tokenizer/DEV/bridge/CVC, independent review mới, dataset freeze, publish/restore của môi trường. Các nguồn TASK-002/003 giữ nguyên nhãn REPORTED/ESTIMATE/ASSUMPTION/UNKNOWN; những nội dung được thuật lại không được nâng thành VERIFIED trong báo cáo này.
