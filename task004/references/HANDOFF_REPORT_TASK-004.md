# TASK-004 - Báo cáo kiểm tra trước triển khai

Ngày 05/11/2026. Báo cáo này ghi nhận kiểm tra đầu vào và quyết định phạm vi còn thiếu; không phải báo cáo hoàn thành harness.

## TASK_ID

TASK-004.

## OWNER

Codex, phiên ChatGPT Work hiện tại: kiểm tra đầu vào và đối chiếu phạm vi. Chưa triển khai mã nguồn. Owner OpenCode trong phiếu cũ là thông tin của phiếu, không phải người thực hiện báo cáo này.

## STATUS

**BLOCKED - cần chốt nguồn chỉ đạo cho phạm vi triển khai.**

Prompt ngày 05/11 cấp CONDITIONAL_GO cho khung launcher/client/mock nhưng mục 4 yêu cầu lấy phiếu TASK-004 làm nguồn chính nếu tìm thấy; mục 10 yêu cầu dừng và hỏi khi gặp mâu thuẫn. Đã tìm được phiếu với mục tiêu và sản phẩm khác đáng kể. Chưa có quyết định thay thế các mục này.

Đây là vướng mắc trong tài liệu dự án, không phải yêu cầu mở ngân sách trả phí. CONDITIONAL_GO đã cho phép mock theo prompt mới; không cần xin lại quyền đó nếu chủ dự án chốt prompt mới là nguồn chính.

## BASELINE_REVISION

- Prompt khởi động TASK-004 ngày 05/11/2026, tệp đính kèm hiện tại.
- Phiếu TASK-004 trong `TASK_TICKETS_2026-10-24(2).md`, dòng 207-278. Bản `TASK_TICKETS_2026-10-24.md` có cùng SHA-256 và cùng 32.133 byte.
- Spec TASK-003 v0.3.2 và CVC-001 rev 1.1: đã đối chiếu byte/hash, đều khớp giá trị khóa trong prompt.
- Chưa tạo repo/branch/commit; git revision của harness: N/A.

## FILES_READ

| Tài liệu | Mức đọc/kiểm tra | Kết quả |
| --- | --- | --- |
| `Prompt khởi động TASK-004 harness tối thiểu.md` | Đọc toàn bộ; hash tệp gốc đính kèm | VERIFIED về nội dung được cung cấp và hash, không xác nhận các tuyên bố bên trong |
| `TASK_TICKETS_2026-10-24(2).md` | Đọc phần TASK-004, dòng 207-278; hash toàn tệp | VERIFIED về nội dung phiếu và hash |
| `TASK_TICKETS_2026-10-24.md` | Hash toàn tệp và đối chiếu byte với bản (2) | VERIFIED: hai bản giống nhau |
| `BENCHMARK_SPEC_v0.md` | Đọc phần đầu, dòng 1-18; hash toàn tệp | VERIFIED: hash khớp; trạng thái duyệt thiết kế vẫn REPORTED |
| `TASK-003-CVC-001.md` | Đọc phần đầu, dòng 1-18; hash toàn tệp | VERIFIED: hash khớp; không xác nhận execution |
| Card TASK-002 v2.3 | Chưa tìm được tệp gốc sau các truy vấn tên/nội dung liên quan | UNVERIFIED; không suy đoán nội dung card |
| Hồ sơ phần cứng `2026-11-05T11:25:22Z` | Chưa tìm được JSON gốc | USER-SUPPLIED theo prompt; nguồn gốc và hash UNVERIFIED |

Tệp đối chiếu được đọc từ bản sao để kiểm tra. Không sửa các tài liệu đầu vào.

## FILES_CHANGED

Tạo duy nhất sản phẩm bàn giao: `task004/HANDOFF_REPORT_TASK-004.md`. Các bản sao đầu vào và công cụ chuyển tệp là dữ liệu làm việc tạm thời, không phải mã harness.

Mã nguồn/tests/benchmark/BingMath: không thay đổi. Diff stat của harness: N/A, chưa có repo hoặc diff mã nguồn.

## WORK_COMPLETED

1. Đọc prompt và kiểm tra môi trường phát triển.
2. Tìm và đọc phiếu TASK-004, đối chiếu với prompt hiện tại.
3. Tính SHA-256 của prompt, hai bản phiếu, spec và CVC-001.
4. Ghi rõ các điểm lệch và chuẩn bị đề xuất phạm vi có thể duyệt trong RECOMMENDATION.

| Điểm cần chốt | Phiếu TASK-004 cũ | Prompt 05/11 | Tác động |
| --- | --- | --- | --- |
| Mục tiêu | Quản lý ticket, ledger thí nghiệm, nguồn và ngân sách; dòng 218 | Khung chạy/đo model local trong tương lai; hiện chỉ mock; mục 1, 6 | Hai tập chức năng khác nhau; làm một bên không tự đáp ứng bên còn lại |
| Module bắt buộc | tickets, ledger, provenance, costlog, runner, cli; dòng 226-231 | config, preflight, server, client, sampler, record, mock_server, cli; mục 9 | Phiếu cấm tự thêm scope; không thể âm thầm gộp hai bộ |
| HTTP/server | Cấm gọi mạng và watcher/dev server; dòng 224 | Client HTTP và mock server là yêu cầu; mục 6 | Cần ghi ngoại lệ HTTP loopback phục vụ mock nếu chọn prompt mới |
| Dependency | Runtime stdlib/PyYAML tùy chọn; pytest dev; AC4. Runner lại cho psutil tùy chọn; dòng 224, 230, 232, 234 | Chỉ stdlib và psutil; mục 6 | Phiếu có điểm chưa thống nhất nội bộ về psutil; pytest không thuộc danh sách mới |
| Đầu ra CLI | validate-ticket, new-experiment, log-cost, status; dòng 231 | Cấu hình model, preflight, launcher và dry-run; mục 6, 9 | Cần chọn giao diện thuộc đợt này |
| Kiểm thử/AC | Ít nhất 25 pytest; luồng ticket → 3 nguồn → ledger → cost log; chặn VERIFIED/PROMOTE; dòng 234 | Schema manifest/JSONL, giới hạn cấu hình, preflight, timeout/cancel, xử lý lỗi mock, lọc secrets; mục 11 | Không dùng bộ test mới để tuyên bố đạt AC cũ |
| Đo tài nguyên mock | RSS <150 MB và <10 giây; dòng 234 | Ghi RSS/commit/latency và nhãn SYNTHETIC; chưa có giới hạn này; mục 6, 9, 11 | Nếu giữ ngưỡng cũ phải nêu rõ AC; số mock không được thành baseline model |
| Trạng thái | PLANNED…RELEASED là vòng đời ticket; dòng 226 | PASS/FAIL/TIMEOUT… là trạng thái lượt chạy; mục 9 | Hai loại trạng thái không tương đương; không tái dùng máy móc một enum |
| Nơi bàn giao | Repo local, nhánh m1-harness; dòng 223, 239 | Thư mục task004 và SHA256SUMS; mục 13 | Chọn một cấu trúc chính, tránh tạo hai bộ sản phẩm độc lập |
| Phụ thuộc | Không phụ thuộc TASK-002/003; dòng 238 | Đầu vào khóa TASK-002/003 và hardware; mục 4 | Chốt việc cho phép tiếp tục mock với tài liệu thiếu mang nhãn UNVERIFIED |
| Ngân sách/quyền chạy | API_BUDGET trống hoặc 0 = không chạy; dòng 210, 236 | CONDITIONAL_GO cho code/test/mock; mục 1 | Cần hiểu $0 là không gọi API trả phí; không mặc nhiên bắt chủ dự án cấp tiền để test local |
| Owner/review | OpenCode; Cline → Claude C; dòng 215-216 | Agent thực thi; Claude C review harness; mục 1, 12 | Báo đúng người thực hiện; không giả có review bên ngoài |
| Phần cứng/nhãn chứng cứ | Snapshot 24/10: RAM 0,68-0,76 GiB, đĩa 4,01 GiB; gọi hardware VERIFIED; dòng 247-252 | Snapshot 05/11: RAM 0,98 GiB, đĩa 31,68 GiB; USER-SUPPLIED; mục 3, 5 | Khác thời điểm, chưa chứng minh mâu thuẫn đo đạc; không nâng nhãn theo phiếu cũ |

Tóm tắt bàn giao:

- **CURRENT STATE:** BLOCKED trước bước triển khai vì chưa thống nhất scope.
- **WORK DONE:** kiểm tra môi trường, hash và đối chiếu phiếu.
- **EVIDENCE:** hai hash TASK-003 khớp; phiếu cũ có nội dung khác prompt mới.
- **BLOCKERS:** quyết định nguồn chỉ đạo; psutil chưa có trong hai Python đã kiểm tra.
- **METRICS:** 0 test harness, 0 dry-run, 0 model run; 2/2 hash khóa có tệp để kiểm đều khớp.
- **NEXT 1–3 ACTIONS:** chốt scope; xử lý môi trường psutil trong phạm vi đã chọn; triển khai và kiểm thử mock.

## EVIDENCE

Các giá trị sau được tính từ byte tệp bằng `hashlib.sha256(Path(...).read_bytes())`, không tính lại từ văn bản trích xuất.

| Tệp | Byte | SHA-256 tính được | Đối chiếu |
| --- | ---: | --- | --- |
| Prompt TASK-004 đính kèm | 12676 | `e05acd6ecb8286d7e6ee507662b6236b851e062dde6034dea7db88bfb6e4d9bf` | Chưa có hash kỳ vọng; ghi nhận định danh |
| TASK_TICKETS bản (2) | 32133 | `27cb47fed77b5af6f300c6f3000f360c2505d84fc088684b0fe2f91b7d98a3c0` | Giống bản không hậu tố |
| TASK_TICKETS bản không hậu tố | 32133 | `27cb47fed77b5af6f300c6f3000f360c2505d84fc088684b0fe2f91b7d98a3c0` | Giống bản (2) |
| BENCHMARK_SPEC_v0.md | 94029 | `a02e3e391b49e3ede390fa4904ccbc550c748ab0652da90483788454b7ed614b` | MATCH giá trị khóa |
| TASK-003-CVC-001.md | 18604 | `6a89687992dd3f79405dbce7c2c6de94e04a3c5b234d527f70ecbde5bdb7bac2` | MATCH giá trị khóa |

Card v2.3 có hash kỳ vọng `0e61286612322912ec2a3611f650985b3edfd05a3d5349f487e52fdeb8bdf343`; actual=null vì chưa có tệp. Không coi một hash được ghi trong prompt là bằng chứng đã kiểm card.

Môi trường phát triển quan sát được: Python 3.12.14; Linux x86_64, kernel 6.18.57. `importlib.util.find_spec('psutil')` trả về False ở Python mặc định. Python của primary runtime báo `ModuleNotFoundError: No module named 'psutil'`. Đây là bằng chứng về môi trường cloud hiện tại, không phải laptop người dùng. Chưa cài thêm gói.

## TESTS_EXECUTED

Harness: **NOT_RUN**. Chỉ chạy kiểm tra byte/hash và truy vấn Python/platform/psutil. Không có pytest, unittest, mock server, launcher hoặc benchmark được thực thi.

## TEST_RESULTS

- Kiểm tra toàn vẹn đầu vào: VERIFIED, spec và CVC đều MATCH.
- Kiểm tra hai bản phiếu: VERIFIED, cùng nội dung byte.
- Đối chiếu phạm vi: VERIFIED về sự khác nhau giữa các yêu cầu được đọc; quyết định ưu tiên thay thế còn chờ chủ dự án.
- Môi trường psutil: chưa đáp ứng yêu cầu chạy mock/sampler theo prompt mới trong hai interpreter đã kiểm tra.
- AC harness: NOT_RUN, không tuyên bố PASS.

## BENCHMARK_RESULTS

**Không có. Không chạy phép đo hiệu năng model thật; cũng chưa chạy dry-run mock.** Không có baseline, TTFT, tok/s, RSS peak hay commit peak của harness.

## COST_OR_RESOURCE_USAGE

Không gọi API model trả phí độc lập; không tải model, không chạy Colab hoặc training. Không mua dịch vụ. Việc sử dụng phiên ChatGPT hiện tại không có bảng token/chi phí đo được trong công cụ, nên không bịa số token hoặc tổng giá phiên.

Chỉ xử lý các tệp Markdown nhỏ và kiểm tra interpreter. Chưa đo tổng CPU/RAM/thời gian của phiên; không dùng số này làm kết quả harness.

## KNOWN_LIMITATIONS

- Chưa có mã nguồn để chạy test hoặc review diff.
- Chưa chạy trên Windows 11/Python 3.14; tính tương thích Windows UNVERIFIED.
- Chưa có card v2.3 và hardware JSON gốc; việc không tìm thấy không chứng minh các tệp không tồn tại ở nơi khác.
- Chỉ đọc phần đầu spec/CVC phục vụ định danh/trạng thái và hash toàn tệp; không thực hiện lại audit thống kê hoặc review thiết kế TASK-003.
- Các cờ llama.cpp/logprob, hỗ trợ model/mmproj và định dạng U20 chưa kiểm tra. Chưa gọi llama-server hoặc tra cứu cờ thật vì chưa triển khai runtime adapter.
- Không đánh giá lại số RAM/đĩa trong prompt trên máy người dùng.

## RISKS

Tự chọn một bộ yêu cầu có thể tạo sản phẩm mang nhãn TASK-004 nhưng không đạt AC của phiếu được prompt chỉ định là nguồn chính. Tự gộp cả hai bộ sẽ mở rộng scope bị cấm. Gắn số synthetic vào baseline hoặc gọi hardware USER-SUPPLIED là VERIFIED sẽ làm sai hồ sơ chứng cứ.

## RECOMMENDATION

**Đề xuất để chủ dự án chốt:** lấy prompt ngày 05/11 làm nguồn chính cho đợt này, thay các mục scope/module/AC/dependency/network/trạng thái lượt chạy/nơi bàn giao không tương thích trong phiếu 24/10. Giữ nguyên các giới hạn không model, không benchmark thật, không training, không BingMath, không publish và không API trả phí. Không ngầm gộp bộ quản lý nghiên cứu cũ vào đợt launcher/mock này.

Bản thiết kế dự kiến, chưa triển khai, dưới một trang:

- Cấu trúc `task004/`: các module config, preflight, server, client, sampler, record, mock_server, cli và tests; chỉ stdlib + psutil, test dùng unittest của stdlib.
- Config JSON bắt buộc n_ctx; kiểm non-thinking, max_new_tokens≤96; điểm cắm ảnh kiểm cạnh dài≤768 và bắt buộc trần token ảnh. Ngưỡng RAM/đĩa và provenance nằm trong config; các giá trị của prompt vẫn là đề xuất, không suy ra card chưa đọc.
- Preflight dùng psutil.available; Windows commit qua ctypes khi có. CLI chỉ mở luồng mock; chặn luồng model thật trong đợt này. Bộ trạng thái lượt chạy riêng, không mượn enum vòng đời ticket.
- Server do harness sở hữu, bind loopback; subprocess timeout/cancel và dọn cây qua psutil. HTTP client dùng stdlib; mẫu log JSONL/manifest có nguồn đo, lỗi, thiếu metric=null và evidence_label=SYNTHETIC.
- Không ghi raw prompt/response, env hoặc secrets vào log. Pilot P-60 và top-K logprob chỉ có interface; không chứa dataset, không phát sinh cờ llama.cpp chưa xác minh.
- Kiểm thử cấu hình, biên RAM/đĩa, lỗi health/JSON/connection, timeout/cancel và orphan cleanup; dry-run từ CLI tạo manifest/JSONL. Bàn giao README, báo cáo 17 trường và SHA256SUMS. Windows chỉ được ghi VERIFIED sau khi chạy trên Windows.

Các giả định cần giữ rõ khi chốt: mock chỉ dùng dữ liệu tổng hợp; HTTP loopback phục vụ test được phép; ngân sách API ngoài bằng 0 không cấm code/test local; psutil là dependency được phép; tài liệu thiếu giữ UNVERIFIED theo mục 4 của prompt. Ngưỡng n_ctx chưa rõ cho model cụ thể không được tự suy ra để mở chạy model thật.

## NEXT_ACTION

1. Chủ dự án chốt một lựa chọn: dùng prompt 05/11 làm nguồn chính cho đợt launcher/mock (đề xuất), hoặc giữ nguyên phiếu 24/10 cho đợt ticket/ledger/costlog.
2. Sau khi chốt prompt mới, chuẩn bị môi trường psutil bằng gói được phép; nếu môi trường không cung cấp/cài được thì báo đúng trở ngại, không dùng mock giả psutil để tuyên bố đã kiểm dọn cây tiến trình.
3. Viết code và chạy bộ kiểm thử/dry-run đúng scope đã chọn. Không mở cổng chạy model; bước tải/đo thật cần các điều kiện riêng tại mục 12 của prompt.

## UNVERIFIED_CLAIMS

- Nội dung gốc card TASK-002 v2.3, review Claude C và provenance hardware.
- Các thông số máy người dùng, RAM sạch và băng thông bền vững; mọi ước lượng hiệu năng.
- Các nhận định Qwen/model/mmproj và cờ runtime còn mở trong prompt.
- CVC execution, dataset freeze, benchmark và baseline: chưa xác nhận đã chạy.
- Windows compatibility, timeout/cancel cleanup, lọc secrets, schema và dry-run: chưa có mã hoặc kết quả test.
- Phạm vi mới thay thế phiếu cũ: mới là đề xuất, chưa có quyết định của chủ dự án.
