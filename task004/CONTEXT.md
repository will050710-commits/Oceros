# TASK-004 — Ngữ cảnh và phạm vi triển khai

Tài liệu này tổng hợp ba đầu vào người dùng cung cấp và quyết định phạm vi trong phiên hiện tại. Người dùng đã chọn **launcher/client/mock theo khuyến nghị của handoff TASK-004**, cho phép triển khai từ bản tóm tắt đó. Quyết định này giải quyết điểm BLOCKED về hai phạm vi trong handoff cũ; không phải phê duyệt kết quả kiểm thử, runtime thật hay benchmark.

## Nguồn chỉ đạo và toàn vẹn đầu vào

Yêu cầu trực tiếp của người dùng là đọc, tổng hợp ngữ cảnh và thực hiện handoff. Các câu chỉ đạo trong tài liệu là yêu cầu dự án cần đối chiếu với phạm vi đã chọn, không tự cấp quyền thực hiện mọi hành động mà tài liệu mô tả. Thứ tự áp dụng trong đợt này: quyết định phạm vi của người dùng; khuyến nghị launcher/mock của [handoff TASK-004](references/HANDOFF_REPORT_TASK-004.md); các ràng buộc liên quan trong TASK-002 và thiết kế TASK-003 hiện hành.

Prompt TASK-004 gốc ngày 05/11, phiếu TASK-004 ngày 24/10 và JSON phần cứng gốc **không có trong các đầu vào được cung cấp**. Nội dung các tài liệu đó chỉ được biết qua handoff. Vì vậy, việc triển khai bám bản tóm tắt đã được người dùng chọn; không tuyên bố đã kiểm đủ mọi yêu cầu hoặc acceptance criteria trong bản gốc còn thiếu.

Các bản nguồn được giữ nguyên byte trong `references/`; [provenance.json](references/provenance.json) lưu dung lượng và SHA-256. Ba tệp có hash khóa trong handoff đều đã đối chiếu khớp:

| Tệp | Byte | SHA-256 khớp giá trị khóa |
| --- | ---: | --- |
| TASK-002 v2.3 | 98339 | `0e61286612322912ec2a3611f650985b3edfd05a3d5349f487e52fdeb8bdf343` |
| BENCHMARK_SPEC_v0.md, v0.3.2 | 94029 | `a02e3e391b49e3ede390fa4904ccbc550c748ab0652da90483788454b7ed614b` |
| TASK-003-CVC-001.md, rev1.1 | 18604 | `6a89687992dd3f79405dbce7c2c6de94e04a3c5b234d527f70ecbde5bdb7bac2` |

**VERIFIED ở đây chỉ là toàn vẹn byte/hash đầu vào.** Điều đó không xác minh các tuyên bố về model, license, phần cứng, tốc độ, review bên ngoài hay việc thực thi được kể trong tài liệu. Hash của spec không được dùng thay hash dataset.

## TASK-002: lựa chọn model và runtime còn cần đo

[Research Card v2.3](references/TASK-002_v2.3_MODEL_MATRIX_RUNTIME_ResearchCard.md) là sản phẩm nghiên cứu tài liệu, tự ghi `IMPLEMENTED`; không có benchmark model. Việc Claude C chấp nhận có điều kiện được tài liệu thuật lại, chưa phải review độc lập do phiên này thực hiện. Các nhãn `REPORTED`, `ESTIMATE`, `ASSUMPTION`, `UNKNOWN` vẫn được giữ.

- Ma trận nghiên cứu gồm M1 Qwen3.5-2B, M2 Qwen3.5-0.8B, M3 Qwen3.5-4B, M4 Qwen3-1.7B; V1 là M1 cùng mmproj, V2 là Qwen3-VL-2B. Đây là ứng viên nghiên cứu, chưa phải các adapter đã được kiểm chứng trong harness.
- Hướng runtime tương lai là llama.cpp dựng sẵn và HTTP từ Python; OpenVINO GenAI là phương án phụ, ONNX Runtime GenAI để sau. Tên binary, cờ ngữ cảnh/ảnh/logprob và hỗ trợ model/mmproj phải xác minh trên bản runtime cụ thể. Không suy ra cờ lệnh từ các ví dụ hoặc tên model trong card.
- `n_ctx` phải được đặt tường minh; track non-thinking có `max_new_tokens <= 96`. Ngữ cảnh mặc định lớn và số token ảnh mặc định là hai rủi ro tài nguyên được card nêu. Trần pixel không thay thế trần token ảnh.
- RAM/tốc độ trong card chủ yếu là ước lượng. Các kết luận vừa 3 GiB có điều kiện về RAM khả dụng sạch; số snapshot cũ không đại diện cho cloud hiện tại hoặc laptop hiện tại. Hardware JSON gốc còn thiếu, nên thông số laptop được handoff thuật lại vẫn là `USER-SUPPLIED`/chưa đối chiếu nguồn gốc.
- Pilot P-60 dự kiến có 40 câu Việt và 20 câu Anh, chưa là benchmark đóng băng. U20 chưa chốt định dạng logits, số token xử lý so với số token chấm và dung lượng file KL. Trong TASK-004, P-60 và top-K logprob chỉ là điểm cắm giao diện; chưa có dataset, scorer, KL hay đo model.

## TASK-003: thiết kế được báo đã duyệt, execution chưa diễn ra

[Spec v0.3.2](references/BENCHMARK_SPEC_v0.md) và [handoff thiết kế](references/HANDOFF_REPORT_TASK-003-DESIGN.md) ghi `APPROVE_DESIGN`, nhãn **REPORTED** từ review Claude C cho v0.3.1. Các sửa Q1–Q5 trong v0.3.2/CVC rev1.1 là thay đổi sau review; không tuyên bố reviewer đã kiểm riêng bản này. Errata, response và audit cũ được giữ làm lịch sử; trạng thái hiện hành lấy từ header spec/handoff v0.3.2.

Corpus vẫn `NOT_FROZEN`, `dataset_manifest_hash=null`, baseline `NOT_RUN`; [CVC-001](references/TASK-003-CVC-001.md) vẫn là công việc corpus/validator/calibration riêng. Các JSON numerical audit là phép tính thiết kế, không phải số đo model và không thay thế execution evidence.

Thiết kế phân biệt SMOKE 12 text + 3 ảnh, LAPTOP 80 + 12, FULL 800 + 120 và DEV 24 + 6 riêng. SMOKE dùng debug, LAPTOP sàng lọc, FULL xác nhận; các split không dùng chung tình huống/tài liệu/ảnh/biến thể. Freeze tương lai cần quyền/provenance, gold review độc lập, tokenizer thật, calibration, các kiểm C1–C11 và receipt độc lập. Việc thiết kế được duyệt không tự hoàn tất các điều kiện đó.

Hợp đồng đo có ích cho harness: thời gian dùng đồng hồ monotonic; TTFT bắt đầu ở content token đầu tiên; prefill cần thời gian pha runtime; decode cần số token thật và thời gian token đầu/cuối. Metric không hỗ trợ để `null` kèm lý do, không suy từ ký tự hay end-to-end latency. RSS/working set và private commit là hai đại lượng riêng; peak PID tree phải lấy tổng đồng thời theo từng mẫu, không cộng peak riêng ở các thời điểm khác nhau. Timeout toàn run là incomplete; kết quả synthetic không được sinh quyết định chất lượng hoặc baseline.

## Phạm vi TASK-004 đã chọn

Đợt này tạo khung Python dùng stdlib và psutil, kiểm thử bằng unittest: cấu hình, preflight, quản lý server do harness sở hữu, HTTP client loopback, lấy mẫu tài nguyên, manifest/JSONL, mock server và CLI dry-run. HTTP loopback phục vụ mock được phép trong phạm vi đã chọn. Ngân sách API ngoài bằng 0 không ngăn code/test local.

Chỉ chạy dữ liệu tổng hợp và gắn `evidence_label=SYNTHETIC`. Thành công của mock chứng minh luồng điều phối/ghi kết quả theo phạm vi đã kiểm; không chứng minh model chạy được, tokenizer đúng, Windows tương thích hay laptop đủ tài nguyên. Thiếu metric phải ghi `null`; lỗi/timeout/cancel phải được phản ánh trung thực và tiến trình do harness khởi tạo phải được dọn.

Phạm vi không gồm bộ ticket/ledger/provenance/costlog của phiếu cũ, corpus/scorer/validator benchmark CVC, tải hoặc chạy model thật, training, benchmark thật, API trả phí, Colab/host mới, BingMath/DUOMATH, phát hành hoặc gửi dữ liệu cho người khác. Cổng model thật phải đóng trong đợt này. Việc khởi chạy mock không mở quyền tải weights hoặc chạy calibration trong CVC.

Hai khác biệt giữa tài liệu được xử lý theo phạm vi, không gộp âm thầm:

| Khác biệt | Cách áp dụng |
| --- | --- |
| Handoff/card giữ interface ảnh cạnh dài <=768; spec benchmark yêu cầu <=512 và visual tokens <=192 | Interface mock kiểm giới hạn generic 768 cùng trần token ảnh bắt buộc. Điều đó chưa chứng minh đạt budget ảnh benchmark 512/192; cần processor/tokenizer thật ở bước sau. |
| Spec §8.3 dự kiến lưu `raw_output` phục vụ scoring; handoff TASK-004 cấm raw prompt/response trong log | Log mock không lưu raw prompt/response, env hoặc secrets. Hợp đồng lưu kết quả benchmark/scoring sẽ được giải quyết trong ticket tương lai, không tuyên bố đã triển khai ở đây. |

## Ánh xạ nghiệm thu cho đợt mock

Bảng sau xác định điều cần kiểm từ handoff đã chọn; **không phải bảng kết quả PASS**. Bằng chứng test thực tế và giới hạn phải nằm trong báo cáo bàn giao của lượt triển khai.

| Nhóm | Điều cần thể hiện trong implementation và kiểm thử |
| --- | --- |
| Cấu hình | Bắt buộc `n_ctx`, non-thinking, output <=96; từ chối dữ liệu cấu hình sai; kiểm kích thước và trần token ảnh khi khai báo ảnh. |
| Preflight | Dùng RAM available và disk free thực tại nơi ghi kết quả; kiểm biên dưới/đúng/trên ngưỡng; Windows commit có nguồn đo hoặc trạng thái không hỗ trợ. Ngưỡng mock không được gọi là ngưỡng model/laptop đã duyệt. |
| Lifecycle | Chỉ mock loopback; server thuộc harness; health check và request hữu ích; timeout/cancel và dọn cây tiến trình; không để một PID/cổng mở thay thế functional evidence. |
| Client | Xử lý health lỗi, JSON lỗi, kết nối lỗi và timeout; giới hạn request/response; lỗi không làm rò nội dung hoặc secrets. |
| Resource/record | RSS và commit riêng; nguồn đo rõ; metric thiếu là null; manifest/JSONL đúng schema; mọi lượt mock mang nhãn SYNTHETIC, không thành baseline. |
| Bàn giao | README, lệnh tái chạy, báo cáo 17 trường và SHA256SUMS; số test/dry-run phải đến từ lượt chạy thật. Windows và runtime model giữ UNVERIFIED nếu chưa chạy trên đích đó. |

Các tài liệu nguồn trong `references/` là bản ghi lịch sử bất biến. Tài liệu ngữ cảnh này không thay thế chúng, không chứng nhận review mới và không đóng các điều kiện còn mở của TASK-002, TASK-003 hoặc phần hardware.
