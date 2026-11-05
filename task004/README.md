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

`setup.sh` có thể chạy lại và không thay dependency declarations/lockfiles. Venv ở ngoài checkout. Để chạy trên máy khác: tạo venv bằng Python sẵn có, cài `-r task004/requirements.txt`, rồi chạy các lệnh `python -m task004.cli` từ thư mục gốc repo. Đường dẫn cloud trong `setup.sh` chỉ dành cho môi trường này. Windows 11/Python 3.14 chưa được kiểm thử.

## CLI và cấu hình

Ba lệnh `validate-config`, `preflight`, `dry-run` nhận `--config` (mặc định `task004/mock_config.json`) và `--output-dir` (mặc định `task004/runs`). Mỗi dry-run tạo thư mục run ID mới chứa `manifest.json` và một dòng `runs.jsonl`; không ghi đè lượt trước. Exit code: PASS=0, lỗi lượt chạy=1, cấu hình sai=2, preflight fail=3, timeout=124, hủy=130. Ctrl+C/SIGTERM đi qua đường dọn tiến trình.

- `n_ctx` phải khai báo tường minh và là số nguyên dương; 4096 trong ví dụ chỉ là cấu hình mock.
- `runtime` chỉ nhận `mock`, `thinking` chỉ nhận `false`, `max_new_tokens` nằm trong 1–96.
- Điểm cắm ảnh: `image_long_edge_px` trong 1–768 và `max_image_tokens` nguyên dương phải được khai báo cùng nhau. Chưa đọc ảnh, tokenize ảnh hay chứng minh cap thực tế. Benchmark TASK-003 có giới hạn riêng ≤512 px/192 visual tokens.
- Timeout dương hữu hạn; sampling tối thiểu 0,01 giây, cấu hình mẫu dùng 0,1 giây.
- Mặc định RAM khả dụng ≥64 MiB, đĩa trống ≥10 MiB là guard cho mock. Đây không phải ngưỡng cho model thật hay chứng cứ laptop đạt yêu cầu.
- `mock_scenario`: `success`, `malformed_json`, `http_error`, `disconnect`, `slow`, `health_failure`. Có `mock_delay_s` để thử delay. Mock slow chờ ít nhất 2 giây; đặt `timeout_s` thấp hơn để kiểm timeout.
- Từ chối khóa lạ, duplicate key, boolean giả số nguyên, NaN/Infinity, đường dẫn model, URL/API tùy ý và lệnh subprocess tùy ý.

## Hợp đồng kết quả

Mọi artifact mang `evidence_label=SYNTHETIC`, `benchmark_status=NOT_RUN`, dataset/hardware reference chưa có là `null`. `PASS` chỉ chứng minh một request mock hợp lệ; không có quyết định PROMOTE hay baseline. Schema đầy đủ trong `schemas/`; bộ kiểm tra stdlib chỉ hỗ trợ các keyword thực sự dùng tại đây, không phải JSON Schema engine tổng quát.

`request_latency_s` là thời gian request/response tổng bằng monotonic clock. `ttft_s`, prefill và decode tok/s đều `null` vì mock không streaming và không có phase timer. Không thay TTFT bằng latency tổng. RSS là peak của tổng đồng thời cây tiến trình mock từ sau health readiness đến trước cleanup; không gồm startup hay harness. Sampling có thể bỏ lỡ đỉnh ngắn. Linux commit=`null` với lý do; không dùng VMS thay commit. Windows có điểm đo `GetPerformanceInfo` và private bytes nhưng chưa xác minh thực thi.

Manifest chỉ ghi cấu hình allowlist, hash cấu hình chuẩn hóa, phiên bản runtime, preflight của máy đang chạy, nguồn đo và hash nguồn đầu vào. Không ghi raw prompt/response, environment, secrets hay nội dung exception/HTTP body. Các chuỗi request/response trong mã chỉ là fixture tổng hợp cố định. Artifact không đọc hoặc ghi dataset thật.

POSIX dùng session/process group sở hữu riêng: TERM, chờ tối đa 1 giây, KILL khi cần, kiểm không còn tiến trình hoạt động; đã kiểm trường hợp cha thoát trước con, con chống TERM và giữ tiến trình không liên quan. Windows dùng psutil khi cây cha còn sống; chưa có Windows Job Object hay kiểm chứng cleanup sau cha chết. Mock cố định không tạo daemon tách session. Không khẳng định bắt được tiến trình cố ý thoát session. Không có dịch vụ cần để chạy nền sau dry-run; tiến trình không phải trạng thái được snapshot.

## Phạm vi còn lại

`interfaces.py` chỉ định nghĩa điểm cắm P-60/top-K và adapter thật bị khóa. Chưa triển khai tokenizer, llama.cpp flags, model/mmproj, KL, corpus, scorer/CVC, ticket/ledger/costlog. Không tải model, gọi API model trả phí, training, sửa BingMath/DUOMATH hay publish. Lượt kiểm thử Linux không cấp quyền chạy những phần này.

Tài liệu gốc được giữ nguyên byte trong `references/`, gồm handoff cũ; báo cáo mới ở thư mục `task004/` để phân biệt. `references/provenance.json` và `SHA256SUMS` kiểm toàn vẹn tệp; hash khớp không nâng các nhận định REPORTED/ESTIMATE/ASSUMPTION thành bằng chứng thực nghiệm.
