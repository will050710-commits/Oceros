# TASK-004 — launcher/client/mock

Harness Python chỉ chạy HTTP mock trên `127.0.0.1`, dữ liệu tổng hợp. Người dùng đã chọn phạm vi này theo đề xuất của handoff ngày 05/11/2026. Bản tổng hợp nguồn và các giới hạn ở [CONTEXT.md](CONTEXT.md); kết quả bàn giao ở [HANDOFF_REPORT_TASK-004.md](HANDOFF_REPORT_TASK-004.md).

## Cài đặt và chạy trên cloud

Từ checkout `/workspace/Oceros`, dùng Python ≥3.10; đã kiểm trên Linux/Python 3.12.14 với `psutil==7.2.2`:

```bash
cd /workspace/Oceros
bash task004/setup.sh
/workspace/.venvs/oceros-task004/bin/python -m task004.cli preflight
/workspace/.venvs/oceros-task004/bin/python -m task004.cli dry-run
/workspace/.venvs/oceros-task004/bin/python -W error::ResourceWarning -m unittest discover -s task004/tests -v
```

Trong phiên Codex cloud này, sandbox mặc định chặn socket. Các lệnh dry-run/test cần cơ chế `require_escalated` của executor cho HTTP loopback đã được cho phép; không tắt proxy/TLS hoặc đổi chính sách mạng. Trình quản lý gói sử dụng HTTPS/proxy của môi trường. Không cần token hay credential ứng dụng. Mỗi task cloud đã cô lập; dùng checkout hiện có, không tạo worktree trừ khi người dùng yêu cầu.

`setup.sh` có thể chạy lại và không thay dependency declarations/lockfiles. Venv ở ngoài checkout. Để chạy trên máy khác: tạo venv bằng Python sẵn có, cài `-r task004/requirements.txt`, rồi chạy các lệnh `python -m task004.cli` từ thư mục gốc repo. Đường dẫn cloud trong `setup.sh` chỉ dành cho môi trường này. Windows 11/Python 3.14 vẫn UNVERIFIED; các thay đổi POSIX chỉ được ghi Linux-verified.

## CLI và cấu hình

Ba lệnh `validate-config`, `preflight`, `dry-run` nhận `--config` (mặc định `task004/mock_config.json`) và `--output-dir` (mặc định `task004/runs`). Mỗi dry-run tạo thư mục run ID mới chứa `manifest.json` và một dòng `runs.jsonl`; không ghi đè lượt trước. Exit code: PASS=0, lỗi lượt chạy=1, cấu hình sai=2, preflight fail=3, timeout=124, hủy=130. SIGINT/SIGTERM/SIGHUP/SIGBREAK (nếu có) chỉ đặt yêu cầu hủy qua Event; tín hiệu lặp bị hấp thụ trong lúc cleanup/ghi artifact. CLI trả CANCELLED/130 khi xử lý hủy. SIGKILL không thể ghi artifact; watchdog của mock xử lý tiến trình còn lại.

- `n_ctx` phải khai báo tường minh và là số nguyên dương; 4096 trong ví dụ chỉ là cấu hình mock.
- `runtime` chỉ nhận `mock`, `thinking` chỉ nhận `false`, `max_new_tokens` nằm trong 1–96.
- Điểm cắm ảnh: `image_long_edge_px` trong 1–768 và `max_image_tokens` nguyên dương phải được khai báo cùng nhau. Chưa đọc ảnh, tokenize ảnh hay chứng minh cap thực tế. Benchmark TASK-003 có giới hạn riêng ≤512 px/192 visual tokens.
- Timeout/startup timeout trong (0, 3600] giây; mock_delay_s trong [0, 3600]; sampling trong [0,01, 60] giây, cấu hình mẫu dùng 0,1 giây. Các cận này được kiểm ngay ở validate-config (scope=CONFIG_ONLY).
- Mặc định RAM khả dụng ≥64 MiB, đĩa trống ≥10 MiB là guard cho mock. Đây không phải ngưỡng cho model thật hay chứng cứ laptop đạt yêu cầu.
- `mock_scenario`: `success`, `malformed_json`, `http_error`, `disconnect`, `slow`, `health_failure`. Có `mock_delay_s` để thử delay. Mock slow chờ ít nhất 2 giây; đặt `timeout_s` thấp hơn để kiểm timeout.
- Từ chối khóa lạ, duplicate key, boolean giả số nguyên, NaN/Infinity, đường dẫn model, URL/API tùy ý và lệnh subprocess tùy ý.

## Hợp đồng kết quả

Mọi artifact mang `evidence_label=SYNTHETIC`, `benchmark_status=NOT_RUN`, dataset/hardware reference chưa có là `null`. `PASS` chỉ chứng minh một request mock hợp lệ; không có quyết định PROMOTE hay baseline. Schema trong `schemas/` vẫn version 1 và nhận evidence đã commit. Validator fail-closed với keyword lạ ở mọi tầng, hỗ trợ minimum/maximum/exclusiveMinimum. Quan hệ status↔reason_code nằm ở `validate_record`; schema chỉ ép enum reason chung. Ghép cặp hai trường ảnh là quy tắc Config; schema ép kiểu và biên số. Đây không phải JSON Schema engine tổng quát.

`request_latency_s` là thời gian request/response tổng bằng monotonic clock. `ttft_s`, prefill và decode tok/s đều `null` vì mock không streaming và không có phase timer. Không thay TTFT bằng latency tổng. RSS là peak của tổng đồng thời cây tiến trình mock từ sau health readiness đến trước cleanup; không gồm startup hay harness. Sampling có thể bỏ lỡ đỉnh ngắn. Linux commit=`null` với lý do; không dùng VMS thay commit. Windows có điểm đo `GetPerformanceInfo` và private bytes nhưng chưa xác minh thực thi.

Manifest chỉ ghi cấu hình allowlist, hash cấu hình chuẩn hóa, phiên bản runtime, preflight của máy đang chạy, nguồn đo và hash nguồn đầu vào. Không ghi raw prompt/response, environment, secrets hay nội dung exception/HTTP body. Các chuỗi request/response trong mã chỉ là fixture tổng hợp cố định. Artifact không đọc hoặc ghi dataset thật.

POSIX dùng session/process group sở hữu riêng: TERM, chờ tối đa 1 giây, KILL khi cần, kiểm không còn tiến trình hoạt động; đã kiểm trường hợp cha thoát trước con, con chống TERM và giữ tiến trình không liên quan. Windows dùng psutil khi cây cha còn sống; chưa có Windows Job Object hay kiểm chứng cleanup sau cha chết. Mock cố định không tạo daemon tách session. Không khẳng định bắt được tiến trình cố ý thoát session. Không có dịch vụ cần để chạy nền sau dry-run; tiến trình không phải trạng thái được snapshot.

## Phạm vi còn lại

`interfaces.py` chỉ định nghĩa điểm cắm P-60/top-K và adapter thật bị khóa. Chưa triển khai tokenizer, llama.cpp flags, model/mmproj, KL, corpus, scorer/CVC, ticket/ledger/costlog. Không tải model, gọi API model trả phí, training, sửa BingMath/DUOMATH hay publish. Lượt kiểm thử Linux không cấp quyền chạy những phần này.

Tài liệu gốc được giữ nguyên byte trong `references/`, gồm handoff cũ; báo cáo mới ở thư mục `task004/` để phân biệt. `references/provenance.json` và `SHA256SUMS` kiểm toàn vẹn tệp; hash khớp không nâng các nhận định REPORTED/ESTIMATE/ASSUMPTION thành bằng chứng thực nghiệm.

## Hardening sau review A1–A5/B1–B4

- Mock nhận PID cha và lifetime = startup_timeout_s + timeout_s + 30 giây. Watchdog daemon kiểm mỗi 0,25 giây; cha mất/zombie thì xóa scratch riêng và thoát; hết lifetime cũng thoát. Không tạo được psutil Process cho cha lúc khởi động thì thoát ngay.
- Mock chỉ nhận environment allowlist `PATH, SYSTEMROOT, TEMP, TMP, LANG, LC_ALL`. Các credential của harness không được truyền qua environment. Process group đã trống không nhận signal.
- Artifact được tính/validate trước, ghi và fsync cả hai file trong `<output>/.<run_id>.tmp`, rồi một `os.rename` sang run dir. Lỗi OSError hoặc BaseException xóa staging; đích có sẵn bị từ chối. Đây là tính nguyên tử khi công bố thư mục, không phải bảo đảm phục hồi sau mất điện; SIGKILL trong lúc ghi có thể để lại staging vì không chạy được cleanup.
- Khi connect bị chặn, cleanup không được đè CANCELLED/KeyboardInterrupt bằng CLIENT_CLEANUP_FAILED. Worker daemon có thể còn tới socket timeout (tối đa 3600 giây); chưa triển khai connect nonblocking. Không khẳng định mọi hủy đều kết thúc worker ngay.
- Windows UNVERIFIED: chưa có Job Object; chưa kiểm socket.shutdown đánh thức recv từ thread khác, Ctrl+C phát toàn console, SIGBREAK, os.rename thư mục, SYSTEMROOT allowlist, GetPerformanceInfo/private bytes hay wheel psutil 7.2.2 trên CPython 3.14. Model thật vẫn NOT_RUN.

Tạo bộ chứng cứ bằng lệnh sau (đường dẫn output phải mới):

```bash
/workspace/.venvs/oceros-task004/bin/python task004/tools/validate_hardening.py --output task004/evidence/hardening-new-run
```

Runner lấy baseline từ Git archive vào thư mục tạm, chạy hồi quy A1–A4 trên cũ/mới, kiểm A5 bằng mutation trên test cũ/mới, chạy toàn bộ suite ba lần liên tiếp rồi dry-run thật. Không sửa working source, không tạo worktree, không sửa evidence cũ. Các số đếm và log được lấy trực tiếp từ subprocess. A5 functional test có thể qua baseline vì guard vốn tồn tại; bằng chứng là test cũ không bắt được mutation còn test mới bắt được.

Lượt bàn giao hiện hành: **87/87 test, ba lần liên tiếp, không failure/error/skip** trên Linux/Python 3.12.14. Xem [validation.json](evidence/hardening-20261106-final/validation.json), các `suite-*.log`, [mutation A5](evidence/hardening-20261106-final/mutation-A5.log) và [handoff](HANDOFF_REPORT_TASK-004.md). Số liệu được lấy từ runner, không từ số dựng thử trong brief.
