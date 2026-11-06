# TASK-004 — review vòng hai

Đọc trực tiếp các file sau; tất cả nằm cùng thư mục để tránh chỉ nhận directory listing.

- [Source đầy đủ, gồm watchdog/config/schema/client/tests](CURRENT_SOURCE.md)
- [Diff cộng dồn từ 2cb9168](review.patch)
- [Diff riêng vòng hai từ 07eb03c](round2.patch)
- [Validation summary tự sinh](validation.json)
- [Handoff 17 trường](../../HANDOFF_REPORT_TASK-004.md)
- [Baseline A1](baseline-A1.log), [A2](baseline-A2.log), [A3](baseline-A3.log), [A4](baseline-A4.log)
- [Deadlock trên 07eb03c](review-baseline-test_nested_signal_cannot_deadlock_handler.log)
- [SIGHUP ignore trên 07eb03c](review-baseline-test_inherited_ignore_is_preserved.log)
- [Suite 1](suite-1.log), [suite 2](suite-2.log), [suite 3](suite-3.log)
- [Mutation A5 bị test mới bắt](mutation-A5.log), [test cũ bỏ lọt mutation](baseline-mutant-A5-undetected.log)

Expected-failure logs có traceback chủ đích. Fixed/suite/dry-run logs không được có marker cảnh báo bị chặn. Source mới đã chạy trên Linux, Windows và model thật chưa được xác minh. Các đường dẫn local trong log đã được chuẩn hóa; không chỉnh nội dung assertion để làm test qua.
