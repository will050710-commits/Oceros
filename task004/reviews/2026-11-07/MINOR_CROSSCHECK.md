# Đối chiếu hai minor với review vòng hai gốc

Đối chiếu bởi Codex ngày 07/11/2026; không phải verdict mới của reviewer. Commit mã được đối chiếu vẫn là `47aaeee91739c2f09ea30538e40c66e853653543`.

Nguồn: [ROUND2_REVIEW_ORIGINAL.txt](ROUND2_REVIEW_ORIGINAL.txt), dòng 50–52. Tệp được sao chép nguyên byte từ attachment đã gửi trước đó, SHA-256 `d4b1000f402c6bb6d4f234ab91692274548019b802f572542fb48933123bb2d4`.

| Minor trong review gốc | Cách xử lý đã có ở commit được chấp nhận | Kiểm tra hiện tại |
| --- | --- | --- |
| “Handler restore skips a `None` previous value, which leaves the lambda installed.” | [cli.py dòng 110](https://github.com/will050710-commits/Oceros/blob/47aaeee91739c2f09ea30538e40c66e853653543/task004/cli.py#L110) bỏ qua cài handler nếu `old is None` hoặc `SIG_IGN`; mọi handler đã thay được lưu và phục hồi. | `test_unknown_previous_handler_is_never_replaced` PASS. |
| “`validate_record` doesn't enforce "PASS requires resources"; only `cli.py` does.” | [record.py dòng 69](https://github.com/will050710-commits/Oceros/blob/47aaeee91739c2f09ea30538e40c66e853653543/task004/record.py#L69) kiểm resource khác null, samples nguyên dương, RSS nguyên dương cho PASS. | `test_pass_requires_positive_resource_evidence` PASS. |

Đã chạy lại riêng hai test trên; log được thu trực tiếp trong [minor-check.log](minor-check.log). Lệnh từ repo root:

```bash
/workspace/.venvs/oceros-task004/bin/python -W error::ResourceWarning -m unittest task004.tests.test_review_cli.ReviewCliTests.test_unknown_previous_handler_is_never_replaced task004.tests.test_review_record.ReviewRecordTests.test_pass_requires_positive_resource_evidence -v
```

Không chạy lại toàn bộ suite trong bước ghi nhận verdict vì source/tests/schema/config/references không đổi. Kết quả 106/106 × 3 của implementer vẫn thuộc evidence tại commit 47aaeee; các lượt reviewer tự chạy là REPORTED từ verdict.

## Ghi chú không chặn cần theo dõi

- **Metric nguyên cực lớn:** Codex đã tái hiện với fixture unit-test, đặt `record['metrics']['run_elapsed_s'] = 10**400` rồi gọi `validate_record`; exception thực tế là `OverflowError`. Không sửa implementation trong commit ghi nhận acceptance này. Nếu mở việc chuẩn hóa thành ValueError, tạo thay đổi và hồi quy riêng; verdict hiện tại vẫn gắn đúng mã 47aaeee.
- **Hai test đọc evidence lịch sử:** giữ thiết kế compatibility guard. Khi chạy suite/đột biến trên bản sao phải giữ `task004/evidence/`, hoặc chạy đúng các test mục tiêu. Không xóa fixture evidence để làm suite tự “qua”.

Reviewer đã nêu ACCEPT chỉ bao phủ 8 finding chính và chưa đối chiếu riêng hai minor. Có thể gửi tài liệu này cùng review gốc để reviewer bổ sung xác nhận; không suy diễn rằng họ đã xác nhận bổ sung.
