# TASK-004 — sổ trạng thái phạm vi

Ngày cập nhật: 07/11/2026 (Asia/Bangkok). Đây là hồ sơ quản lý phạm vi dự án; không phải implementation module ledger/tickets của phiếu 24/10.

> TASK-004 launcher/client/mock Linux tại `47aaeee`: **ACCEPTED**. Phạm vi thay phiếu 24/10: **USER-DECIDED**. Phần ticket/ledger/costlog: **chưa làm**.

| Phạm vi / quyết định | Trạng thái | Bằng chứng và giới hạn |
| --- | --- | --- |
| Launcher/client/mock trên Linux | ACCEPTED tại `47aaeee91739c2f09ea30538e40c66e853653543` | [Verdict do người dùng chuyển tiếp](reviews/2026-11-07/ACCEPT_REVIEW.md); evidence implementer 106/106 × 3. Chỉ scope mock. |
| Thay phạm vi triển khai của đợt này | USER-DECIDED | Người dùng chọn “launcher/client/mock theo khuyến nghị handoff” trong chat, sau khi được hỏi lựa chọn giữa hai phạm vi. Không tự gộp hai bộ AC. |
| TASK-004 theo phiếu gốc 24/10: ticket/ledger/provenance/costlog/runner/CLI | NOT_IMPLEMENTED; DISPOSITION_PENDING | Chưa có implementation tương ứng. Chọn launcher/mock không đồng nghĩa tự động hủy nghĩa vụ của phiếu cũ. Đang chờ người dùng chọn tách ticket riêng hoặc chính thức bỏ. |
| Kiểm mock trên Windows | READY_FOR_ASSIGNMENT / NOT_RUN | [TASK-004-WIN-MOCK](tickets/TASK-004-WIN-MOCK.md), phiếu trong repo; chưa giao người thực hiện, chưa chạy trên Windows. |
| Adapter llama-server thật | NOT_IMPLEMENTED / NOT_AUTHORIZED_TO_RUN | `real_model_adapter` chủ động chặn; config chỉ nhận mock. |
| Bảng preflight theo model | NOT_IMPLEMENTED / GATED_FOLLOWUP | Hiện chỉ có guard tài nguyên mock, không có test “0,98 GiB từ chối cả bốn model”. |
| Hardware reference trong manifest | NULL / NO_VERIFIED_REFERENCE | Chưa có JSON phần cứng gốc được xác minh để gắn nguồn. Không dùng RAM cloud thay cho laptop. |
| Model inference / benchmark / CVC / freeze | NOT_RUN / NOT_FROZEN | ACCEPT Linux mock không mở những scope này. |
| Chuyển cho orchestrator | PACKET_READY; NO_ACK_RECORDED | Có [bản bàn giao](ORCHESTRATOR_HANDOFF.md), chưa gửi qua messaging/tracker hoặc ghi nhận acknowledgment trong phiên này. |

## Cách hiểu ba khoảng trống so với prompt được nhắc lại

Adapter thật, bảng ngưỡng theo model và hardware reference vẫn chưa có, đúng như kiểm bổ sung nêu. Không gọi đó là đã hoàn thành chỉ vì mock PASS; cũng không coi ACCEPT Linux mock là chấp thuận các phần này. Prompt gốc và phiếu 24/10 vẫn chưa được cung cấp nguyên bản trong repo; chỉ có bản thuật lại trong handoff và lời người dùng. Trước khi nhận scope mới phải đối chiếu nguồn nguyên bản/AC đã chốt.

Các mức 1,21 / 1,90 / 2,01–2,67 / 3,45 GiB trong bản kiểm bổ sung là thông số được người dùng thuật lại từ prompt, chưa phải policy đã được triển khai. Cần nguồn, ánh xạ model/config, đơn vị và biên an toàn được duyệt trước khi đưa vào code. Không tự suy ra mapping.

## Cổng cho bước tiếp theo

1. Ghi nhận quyết định về phiếu cũ: tách ticket hoặc chính thức bỏ; chưa có câu trả lời thì giữ NOT_IMPLEMENTED / DISPOSITION_PENDING.
2. Thực hiện ticket Windows mock trên máy Windows thật và lưu bằng chứng của máy đó.
3. Đo lại RAM khả dụng khi máy sạch, đĩa và commit; cung cấp nguồn hardware có kiểm toàn vẹn. Snapshot không tự trở thành model benchmark.
4. Sau khi người dùng duyệt phần cứng/phạm vi, mới mở ticket bảng preflight theo model + adapter llama.cpp. Không mở/chạy model trước cổng này.

## Bản bàn giao được dùng

- Mã được chấp nhận: [snapshot 47aaeee](https://github.com/will050710-commits/Oceros/tree/47aaeee91739c2f09ea30538e40c66e853653543/task004).
- HEAD `c453471` lúc nhận bản kiểm bổ sung chỉ thêm 8 tệp hồ sơ/checksum so với 47aaeee; code/tests/schema/config/references không đổi. Các commit hồ sơ sau đó cũng phải giữ riêng với commit implementation được chấp nhận.
- **Không dùng `Oceros_TASK004_mock_handoff.zip` cũ để review bản đã chấp nhận.** Bản ZIP cục bộ từng tạo đã được đối chiếu byte và khớp các tệp của `2cb9168`, SHA-256 `f7bdc888726aca844255081e28058e95ff92dd77376bac2c8deff613e689adbe`. Giữ như artifact lịch sử, không thay nhãn thành bản mới.

## Tách nguồn bằng chứng

Kiểm bổ sung do người dùng chuyển tiếp có [bản ghi riêng](reviews/2026-11-07/ADDITIONAL_SCOPE_AUDIT.md). Các lượt 106/106 × 3 và 5 mutation của người kiểm bổ sung là REPORTED; không gộp chúng với 14 mutation/30.000 fuzz/6 lượt tải của reviewer trước. Reviewer vẫn chưa xác nhận đối chiếu riêng hai minor; test và đối chiếu của implementer không thay thế xác nhận đó.
