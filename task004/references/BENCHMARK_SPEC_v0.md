# BENCHMARK_SPEC_v0 - General LLM + VLM

| Thuộc tính | Giá trị |
| --- | --- |
| Task | TASK-003 - Benchmark Architecture |
| Revision | 0.3.2, ngày 2026-11-04; sửa nhỏ Q1-Q2 và ghi nhận duyệt thiết kế, không mở vòng thiết kế mới |
| Owner | ChatGPT trong phiên Work, Role D; có dùng công cụ tính cloud, không gọi API model trả phí |
| Reviewer dự kiến | Claude C, phiên độc lập do chủ dự án chuyển tài liệu |
| Trạng thái | APPROVE_DESIGN (REPORTED từ Claude C sau ACCEPT_ERRATA v0.3.1); Q1-Q5 đã xử lý trong tài liệu; NOT_FROZEN |
| Phạm vi | Thiết kế, công thức, schema, quy tắc chấm, pseudocode; không triển khai harness |
| Ngân sách | Không gọi API model, không tải model, không chạy Colab; chi phí API phát sinh $0 |
| Đầu vào quyết định | TASK_TICKETS_2026-10-24(2).md, phần TASK-003 và context package |

## 0. Kết luận thiết kế và cách đọc

Đề xuất ba tầng **SMOKE 12 text + 3 ảnh**, **LAPTOP 80 text + 12 ảnh**, **FULL 800 text + 120 ảnh**. Ảnh là phần mở rộng chỉ áp dụng khi đánh giá cấu hình có thị giác. CORE-TEXT có điểm riêng; một LLM không nhận ảnh không được gọi là đã đạt baseline VLM.

SMOKE dùng để debug; LAPTOP để sàng lọc; FULL là tập xác nhận chưa lộ. Ba tầng **không dùng chung item, tài liệu nguồn, ảnh hoặc biến thể cùng tình huống**. Không cộng kết quả lặp hay kết quả SMOKE vào cỡ mẫu xác nhận.

Với giả định tốc độ của ticket và ngân sách token ở mục 3, LAPTOP text ước tính 51.84 phút, text + ảnh 64.20 phút. SMOKE đã sửa cap là 9.06 phút; SMOKE cộng LAPTOP có ảnh là 73.26 phút. Đây là **ESTIMATE có điều kiện**, không phải số đo laptop hay cam kết chạy xong. VLM phải qua hiệu chuẩn vì chi phí mã hóa và số token ảnh chưa biết.

**HYPOTHESIS: NOT SUPPORTED cho LAPTOP** nếu hiểu là phát hiện chênh 10 pp với power 80% trong các kịch bản q của ticket; chỉ dùng LAPTOP để sàng lọc. Với N=80, tỷ lệ bất đồng q=0.30, kiểm định McNemar chính xác có power khoảng 29.5% ở chênh 10 điểm; MDE cho power 80% là khoảng 17.62 điểm. Mục 5 cho công thức và độ nhạy.

**Bằng chứng:** giữ các nhãn của ticket. Nguồn được diễn giải dưới nhãn REPORTED, kèm bằng chứng đã mở; không biến việc mở trang thành xác nhận toàn bộ quyền pháp lý. Phép tính v0.2-v0.3: tự tính, Claude C báo đã tái tạo ở các vòng review. Phép tính v0.3.1: tự tính độc lập từ định nghĩa cổng; Claude C báo đã tái tạo các bảng exact và mô phỏng độc lập10 profile, chỉ spot-check audit JSON. Không dùng script của reviewer; không nâng giới hạn spot-check thành kiểm từng bản ghi. ESTIMATE là dự báo, ASSUMPTION là giả định/chính sách, UNKNOWN là thiếu dữ kiện. Hardware vẫn là “VERIFIED user-run theo ticket”, không nâng nhãn bằng suy luận trong phiên này.

### 0.1 Baseline, review và giới hạn hai vòng

Ticket gốc SHA-256 `27cb47fed77b5af6f300c6f3000f360c2505d84fc088684b0fe2f91b7d98a3c0`, 32133 byte. **F14 đóng theo review vòng 2:** Claude C báo full SHA của bản reviewer trùng khớp; hậu tố filename "(2)" không làm khác nội dung. Đây là đối chiếu hash hai bên được REPORTED, không phải tác giả trực tiếp truy cập máy reviewer.

v0.2 SHA-256 `89ec037b8a371d1d786b42ac91cf10912a209db0cdb6274a114e4ac4ccf352c5` nhận REQUEST_CHANGES. v0.3 SHA-256 `27081c85020e4526ca9b1a1dab3941e2f6a340b0709528fe7f5a0d5bb2675037`, 79084 byte, 613 dòng nhận **APPROVE_DESIGN_WITH_EXECUTION_CHECKS có điều kiện** trong review vòng 2 do chủ dự án cung cấp. Sau đó Claude C kiểm nhanh v0.3.1 SHA-256 `380be7cf340fb22961dc3f36d383dc04a3f68180e2a549e8471720e96be87ead` (91350 byte,695 dòng), kết luận **ACCEPT_ERRATA** và nâng TASK-003 lên **APPROVE_DESIGN**. Quyết định được ghi nhận theo review chủ dự án cung cấp ngày2026-11-04; reviewer báo E1-E4 và số đã kiểm đều tái tạo được. Đây là duyệt thiết kế, không phải FROZEN hay đã chạy baseline.

v0.3.2 ghi nhận quyết định đó, sửa nhỏ Q1 và làm rõ Q2; Q3-Q5 được áp vào `TASK-003-CVC-001.md`. Không mở vòng thiết kế thứ ba, không đổi ngưỡng hay bảng xác suất đã duyệt. `TASK003_v032_Q1-Q5_Closure.md` ghi các thay đổi sau duyệt; không tuyên bố reviewer đã đọc v0.3.2. `ERRATA_TASK003_v0.3.1.md` giữ nguyên byte làm lịch sử, gồm trạng thái chờ kiểm ở thời điểm phát hành; các trạng thái hiện hành lấy ở header này và handoff mới.

Thay đổi chính: cổng nhóm ở LAPTOP chuyển sang chẩn đoán; quyết định có stage, run_status và reason_code rõ; SMOKE tăng cap cho JSON; thêm bridge FULL/laptop, kiểm gold toàn bộ, đo tài nguyên A/B ba lần mỗi bên, workload xây corpus và notice có hash. Sau audit bootstrap nhỏ mẫu, **McNemar exact trở thành phép kiểm so sánh cặp chính cho thiết kế một item/một cluster; bootstrap chỉ mô tả/chẩn đoán**. Chi tiết đáp ứng F1-F15 nằm trong `RESPONSE_TO_CLAUDE_REVIEW_v03.md`.

Thiết kế, số câu và quyền triển khai tách biệt: sửa tài liệu không tự cho phép freeze, tải model, gọi API, chạy Colab hay mở rộng TASK-004.

## 1. Phân bổ tác vụ, trọng số và ngôn ngữ

| Mã | Năng lực và nội dung | Trọng số CORE-TEXT | SMOKE | LAPTOP | FULL |
| --- | --- | ---: | ---: | ---: | ---: |
| GR | Suy luận đời thường, quan hệ, trình tự, nguyên nhân, đồng tham chiếu; không toán chuyên sâu | 20% | 2 | 16 | 160 |
| IF | Tuân thủ 2-3 ràng buộc nội dung/định dạng kiểm tra được | 15% | 2 | 12 | 120 |
| BI | Đọc hiểu VI/EN, phủ định, thực thể, ý nghĩa; đáp án hữu hạn | 15% | 2 | 12 | 120 |
| GQ | QA từ ngữ cảnh được cung cấp, trả lời ngắn kèm trích dẫn đúng câu | 20% | 2 | 16 | 160 |
| SO | JSON đúng schema và đúng nghĩa; tool-call giả lập có tên/đối số hợp lệ | 15% | 2 | 12 | 120 |
| HC | Không bịa; biết trả lời, abstain hoặc từ chối đúng trường hợp | 15% | 2 | 12 | 120 |
| Tổng text | | 100% | 12 | 80 | 800 |
| MM-VQA | Nhận dạng đối tượng, màu, vị trí, quan hệ trong ảnh tự dựng | Riêng | 1 | 4 | 40 |
| MM-OCR | Đọc tài liệu giả lập VI/EN, chọn trường hoặc chép chuỗi ngắn | Riêng | 1 | 4 | 40 |
| MM-CHART | Đọc nhãn, cực trị, xu hướng, giá trị trực tiếp trên biểu đồ | Riêng | 1 | 4 | 40 |
| Tổng có ảnh | | | 15 | 92 | 920 |

GR và GQ có trọng số cao hơn vì phản ánh suy luận tổng quát và độ tin cậy khi dùng tài liệu. Bốn nhóm còn lại giữ vai trò quan trọng ngang nhau. Đây là lựa chọn sản phẩm đặt trước, không phải trọng số suy ra từ kết quả model.

Với pass_i trong {0,1}, p_g = số pass / số item dự kiến của nhóm:

```text
S_text = .20*p_GR + .15*p_IF + .15*p_BI + .20*p_GQ + .15*p_SO + .15*p_HC
S_mm   = (p_VQA + p_OCR + p_CHART) / 3
S_vlm  = .75*S_text + .25*S_mm
```

S_text trùng accuracy gộp ở LAPTOP/FULL do phân bổ tỷ lệ. Tuy vậy, mẫu phân tầng không tự nhiên trở thành mẫu Bernoulli i.i.d.; dùng bound cho biến độc lập không đồng phân phối ở cổng FULL và điều kiện kiểm định cặp trong mục 5. Không tính S_vlm khi thiếu phần ảnh; không đổi mẫu số hoặc tái chuẩn hóa trọng số để che phần không hỗ trợ.

**Song ngữ:** mỗi nhóm text LAPTOP/FULL có đúng 50% VI, 50% EN; mỗi nhóm ảnh cũng vậy. SMOKE text có 1 VI + 1 EN mỗi nhóm; 3 ảnh phủ cả hai ngôn ngữ, không tính parity. Mỗi item của điểm chính phải là một cluster tình huống riêng, không lặp tài liệu/ảnh/biến thể. Tránh bản dịch song sinh; family dùng để kiểm bias nhưng không được chứa các câu chỉ đổi tên thực thể. Báo p_VI, p_EN và chênh lệch cùng CI; không gọi đó là tác động nhân quả của ngôn ngữ vì câu hỏi khác nhau. BI chỉ đo các kỹ năng hẹp trên đây, không chứng minh năng lực dịch/văn phong tổng quát.

**Cấu trúc nội bộ bắt buộc:** GQ có 12 câu có đáp án + 4 câu thiếu dữ kiện ở LAPTOP, FULL nhân 10. SO có 6 extraction + 6 tool-call, FULL nhân 10. HC gồm 6 câu trả lời được và 6 câu không nên trả lời trực tiếp: 4 thiếu dữ kiện/tiền đề sai, 2 vi phạm quy tắc công cụ giả lập nêu rõ. FULL nhân 10. Các nhóm HC cân bằng VI/EN; tình huống độc lập, không chỉ đổi tên trong cùng mẫu.

## 2. Vai trò các tầng và nguồn dữ liệu

### 2.1 Tách dữ liệu từ trước

| Tập | Vai trò | Được xem gold khi phát triển? | Điều kiện dùng kết quả |
| --- | --- | --- | --- |
| SMOKE | Kiểm loader, ảnh, JSON, scorer và đường đo | Có | Không dùng để xếp hạng hay chọn baseline |
| DEV | 24 text + 6 ảnh riêng, dùng hiệu chuẩn rubric và token; không là tầng benchmark | Có | Không cộng vào N chính; chuẩn bị một lần trước campaign |
| LAPTOP | 80 + 12, sàng lọc với cấu hình đã đăng ký | Chỉ người giữ gold và scorer | Nếu dùng lỗi item để sửa prompt/model, đánh dấu tập này là development từ thời điểm đó |
| FULL | 800 + 120 mới, xác nhận ngoài laptop | Giữ kín đến lúc khóa ứng viên | Không trộn 80 câu LAPTOP vào số 800 xác nhận |

FULL không cần chạy trong Task 3. Chỉ chọn môi trường sau này khi được phép, có đủ tài nguyên và không phát sinh chi phí chưa duyệt. Không giả định có Colab Pro được duyệt, API credits hay GPU miễn phí khả dụng.

Nguồn mặc định cho các tập chính là **tình huống mới tự biên soạn**, tài liệu hư cấu, JSON giả lập, sơ đồ và biểu đồ có dữ liệu tự tạo. Mỗi item có đáp án và chứng cứ do người biên soạn kiểm lại. Không đưa bộ 60 câu Toán, raw_data, prompt, lời giải hay tài liệu chưa rõ quyền của repo cũ vào quá trình xây dựng.

### 2.2 License, nguồn công khai và notice

| Nguồn | Bằng chứng được ghi nhận | Vai trò v0.3 | Quyết định nhập |
| --- | --- | --- | --- |
| Nội dung nguyên gốc của dự án | Notice riêng + contributor permission record | Tập chính | Chỉ nhập khi người đóng góp có quyền và đã đồng ý notice |
| CommonsenseQA (CSQA) | REPORTED MIT: Jonathan Herzig, comment 2020-09-25 tại issue #5 [S3]; thẻ TAU ghi MIT [S4] | Nguồn nghiên cứu/chẩn đoán dự kiến, không phải corpus mặc định | HOLD, không có trong manifest freeze cho đến khi registry xử lý đủ notice và nguồn gốc |
| WinoGrande | Repo phân biệt code Apache-2.0 và dataset CC-BY nhưng chưa chốt version [S5] | Tham khảo | HOLD |
| Noto Fonts | File LICENSE ghi SIL OFL 1.1 [S6] | Font OCR ứng viên | Pin font bytes, license và hash; không suy quyền font sang ảnh bên thứ ba |

**Xung đột CSQA:** phiên này mở lại được [S3], thấy comment của chủ repo xác nhận MIT, ngày 2020-09-25; URL bền vững: https://github.com/jonathanherzig/commonsenseqa/issues/5 . ACCORD, phụ lục I.1 [S9], lại báo không thấy license trên trang chủ/repo tính đến 2024-10-14 và nêu ConceptNet CC-BY-SA-4.0. Hai ghi nhận cùng được lưu; không kết luận công cụ reviewer không mở được trang nghĩa là comment không tồn tại, cũng không coi comment tự giải quyết mọi quyền của dữ liệu dẫn xuất. Chưa tìm được permalink comment-ID riêng nên dùng issue URL + tác giả/ngày; không bịa ID. Không nhập CSQA ở vòng này.

CSQA là tiếng Anh, **5 lựa chọn A-E**, khác MC A-D của tập chính. Nếu sau này thông qua nguồn, dùng một report phụ A-E đo generalization sang câu hỏi tự nhiên và độ nhạy context/counterfactual; giữ đủ 5 đáp án, báo chance=20%, không trộn vào S_text. Một score công khai cao không phải phép chứng minh contamination.

Notice: file `GB0_INTERNAL_NOTICE_v1.txt`, SHA-256 `39510d0f581c3db835465afd95e3a0d0a799cb657d2189c7fd3ff1ca4013eb9e`. Item dùng `notice_ref` là đường dẫn file này và `notice_sha256` như trên, không dùng anchor tiếng Việt vào spec có thể đổi. Notice là điều kiện cho đóng góp **mới**; không tự cấp lại quyền tài liệu hiện hữu hoặc nội dung người khác. Contributor permission record còn thiếu thì corpus freeze bị chặn. Không phát hành công khai trong task.

AC2 hiện có chính sách quyền rõ cho nguồn mới và font; nhập corpus/license từng item vẫn là việc chưa thực hiện. HOLD của nguồn công khai không được đổi thành “license verified” để làm đẹp AC.

### 2.3 Soạn item, độ khó và chất lượng gold

Mỗi nhóm text LAPTOP có ít nhất 4 family, FULL ít nhất 12; không chỉ thay tên/số trong template. Mỗi tình huống, ảnh, tài liệu của điểm chính chỉ sinh **một** item. Biến thể đi DEV hoặc report chẩn đoán, không tăng N độc lập.

Schema bắt buộc `difficulty` ∈ easy/medium/hard; `difficulty_basis` giải thích thao tác nhận thức dự kiến; không gán nhãn khó bằng điểm model. Mục tiêu 30/50/20, phân bổ integer theo largest-remainder, tie theo easy/medium/hard. Áp cùng quota cho từng cặp (task,language), nên GR/GQ LAPTOP mỗi ngôn ngữ 8 câu là 2/4/2, các nhóm 6 câu là 2/3/1; sai khác tỷ lệ toàn tập do làm tròn phải báo, không ghi “đúng 30/50/20” khi không đúng. FULL mỗi ngôn ngữ GR/GQ 80 câu là 24/40/16, các nhóm 60 câu là 18/30/12. Cân bằng nhãn đúng A-D trong từng nhóm và ngôn ngữ, chênh tối đa 1; ngẫu nhiên vị trí theo seed.

**Hai người và gold:** người A biên soạn + giải có bằng chứng; người B giải độc lập khi chưa thấy gold A, kiểm 100% text và ảnh ở cả LAPTOP lẫn FULL. Tranh chấp cần người C adjudicate hoặc loại trước freeze. Không thay kiểm FULL toàn bộ bằng spot-check 20%. Hai người có thể bất đồng; chỉ item đã giải quyết và có evidence mới vào freeze.

Ghi agreement A/B trước adjudication, số lỗi gold/rubric/ảnh, theo nhóm/ngôn ngữ/độ khó. Yêu cầu trước freeze: agreement≥95% tổng, ≥90% mỗi nhóm chính; unresolved=0; mọi correction có audit trail; human B đạt ≥95% so với gold A ban đầu hoặc từng lỗi được chứng minh do gold A sai. Nếu không đạt agreement hoặc chạm ngưỡng đếm lỗi/mơ hồ của batch định nghĩa ngay dưới: dừng batch, sửa family/rubric, người B review lại 100% phần bị ảnh hưởng, tối đa một lượt sửa; vẫn không đạt thì BLOCKED_GOLD_QUALITY, không hạ chuẩn. Với nhóm rất ít câu, báo số nguyên và dùng kiểm toàn bộ thay suy luận từ tỷ lệ.

**Batch và số đếm (P4):** khóa danh sách batch trước khi B chấm, không trộn split. Mỗi batch mục tiêu 100 item theo thứ tự manifest; tail <50 gộp batch trước (tối đa149); split có <100 item dùng toàn split. Trigger sửa batch khi số item có lỗi gold ≥max(2, floor(.02*n)+1), hoặc số item có mơ hồ scorer thực chất ≥max(2, floor(.01*n)+1). n=100 tương ứng 3 lỗi gold hoặc 2 mơ hồ; n=15/30/92 tương ứng 2 hoặc 2. Đây là điều chỉnh số đếm cho batch nhỏ, không gọi chính xác là quy tắc >2%/>1% ở mọi n. Đếm item, không đếm nhiều lỗi trên cùng item thành nhiều mẫu. Mọi lỗi đều phải sửa trước freeze dù chưa chạm trigger; chỉ một lỗi leakage/quyền sử dụng/asset không đọc được cũng chặn item và phần liên quan ngay. Không chia/gộp batch sau khi thấy kết quả để né trigger. Agreement tổng/nhóm vẫn giữ nguyên.

Người B là tham chiếu mạnh từ phía trên: tỷ lệ giải được và lý do sai phải chỉ ra sàn có thể đạt bằng lời giải hợp lệ. Không dùng chính gold sau sửa để tuyên bố human “100%” mà che agreement ban đầu. DEV 24+6 chỉ kiểm kỹ thuật, **không đủ để ước lượng quality population hoặc chọn sàn**. FULL có thể chưa xây nếu thiếu người review.

SMOKE phủ mỗi scorer với input/output gọn riêng, không buộc tái dùng nguyên ví dụ DEV có schema dài. Negative fixtures (JSON sai, ảnh hỏng, Unicode) phục vụ kiểm scorer/loader ngoài item quality; thời gian kiểm nằm trong khoản cố định và phải đo.

### 2.4 Khối lượng và người phụ trách

Tổng kế hoạch: 1057 item = 137 ở SMOKE+DEV+LAPTOP và 920 FULL; gồm 916 text, 141 ảnh. Stage A xây 116 text + 21 ảnh trước; Stage B mới xây 800 text + 120 ảnh sau khi thiết kế được duyệt và có người giữ gold. $0 là tiền API, **không phải lao động bằng 0**.

ESTIMATE khối lượng: text soạn 4-8 phút + review độc lập 2-4 phút/item; ảnh soạn 10-20 phút + review 4-8 phút/item; thêm 15-25% adjudication/đóng gói. Tổng khoảng **143-311 giờ-người**; Stage A khoảng **19-41 giờ-người**. Đây là giả định kế hoạch, đo bằng batch pilot trước khi hứa lịch. Nếu không có người/giờ, dừng ở Stage A và giữ FULL_NOT_READY; không giảm âm thầm N.

Chủ dự án phân công A soạn, B giữ gold/giải độc lập, C xử tranh chấp; không có ai được tự động liên hệ. LLM miễn phí có thể hỗ trợ soạn DEV/SMOKE khi điều khoản phù hợp, phải ghi model/tool/ngày, prompt provenance, vai trò hỗ trợ, người sửa, family và terms review. Không để chính candidate cuối tạo toàn bộ tập đánh giá cho mình. Người giữ FULL không đưa prompt/gold FULL vào tài khoản/model dùng tuning; không giả định output LLM luôn nguyên gốc. Chia family giữa người soạn/nguồn hỗ trợ và báo hiệu ứng nguồn; nếu quyền hoặc blind separation không bảo đảm thì không nhập.

## 3. Ngân sách thời gian và khả thi trên laptop

### 3.1 Token và công thức

Gọi r_p là tốc độ prefill và r_d là tốc độ decode. Dùng dải **ASSUMPTION từ ticket**: r_p=10-40 tok/s, r_d=3-8 tok/s. Token là token thật của tokenizer ứng viên, bao gồm system prompt, chat template, context, schema và special token. Không đổi ký tự hay “token tương đương tiếng Anh” thành token thật bằng một hằng số chưa đo.

| Nhóm text | N | Trần input/item | Trần output/item | Tổng input | Tổng output |
| --- | ---: | ---: | ---: | ---: | ---: |
| GR | 16 | 128 | 8 | 2048 | 128 |
| IF | 12 | 128 | 40 | 1536 | 480 |
| BI | 12 | 192 | 40 | 2304 | 480 |
| GQ | 16 | 320 | 48 | 5120 | 768 |
| SO | 12 | 192 | 48 | 2304 | 576 |
| HC | 12 | 192 | 32 | 2304 | 384 |
| Tổng | 80 | | | **15616** | **2816** |

Input cap là điều kiện chọn corpus trước khi đóng băng, không cho phép cắt câu hỏi khi chấm. Kiểm bằng tất cả tokenizer trong shortlist được đăng ký. Gold hợp lệ cũng phải nằm trong output cap. Candidate mới vượt cap cần báo non-comparable hoặc một revision ngân sách/corpus mới chung cho các candidate; không lặng lẽ cắt bớt riêng nó.

Với batch=1, một request đồng thời, không cache prefix xuyên item:

```text
T_text = F + sum_i(L_i/r_p + O_i/r_d + h_i)
F = 450 s = 180 s tải/warm-up + 90 s kiểm/ghi/đo + 180 s cho 6 probe tài nguyên
h_i = 2 s/item
T_text_slow = 450 + 15616/10 + 2816/3 + 80*2
            = 3110.27 s = 51.84 phút
```

Sáu probe riêng có input ≤128, output ≤32; theo dải chậm, tổng ≤6*(12.8+10.667+2)=152.8 s, nằm trong khoản 180 s. Probe không có gold chất lượng và không tăng N. Chi phí tải, kiểm, overhead đều là khoản dự trù ASSUMPTION, phải thay bằng số đo khi hiệu chuẩn.

### 3.2 Phần ảnh có điều kiện

Ảnh tự dựng một khung, PNG, cạnh dài ≤512 px; tài liệu OCR dùng crop ngắn đọc được, không nén cả trang A4 thành chữ không đọc nổi. Ngân sách mỗi request ảnh: text input ≤96 token, output ≤48; **visual tokens hữu hiệu ≤192**, tiền xử lý + encode ≤15 s, overhead 2 s. Giới hạn pixel **không bảo đảm** giới hạn visual token.

```text
T_mm = 12*(96/r_p + 192/r_p + 48/r_d + 15 + 2)
T_mm_slow = 12*(9.6 + 19.2 + 16 + 15 + 2) = 741.6 s
T_laptop_vlm_slow = (3110.27 + 741.6)/60 = 64.20 phút
```

Số 192 và 15 s là giả định thiết kế có thể sai với VLM cụ thể. Phải đo bằng 3 ảnh DEV, đọc processor config và số token thực. Model dùng cross-attention không có visual token tương đương phải thay hai hạng `192/r_p + encode` bằng thời gian visual path đo được, không ép công thức sai. Mỗi ảnh phải đo end-to-end để tránh đếm encode hai lần. Nếu adapter không tách được pha, phase metric = UNKNOWN và chỉ dùng số end-to-end.

Không đạt ngân sách ảnh thì VLM = RETRY để đổi cấu hình **trước khi khóa campaign**; nếu cấu hình đã hiệu chuẩn vẫn vượt giới hạn trong lượt hợp lệ, xử lý không phù hợp resource envelope theo mục 6. LLM text vẫn có báo cáo riêng, không được suy thành VLM đạt.

### 3.3 SMOKE sửa cap và tổng campaign

SMOKE 12 text chia hai ngân sách: 6 câu GR/IF/BI ngắn có input≤96, output≤8; 6 câu GQ/SO/HC cần JSON có input≤128, output≤48. Ba câu ảnh giữ text≤96, visual≤192, output≤16, encode≤15 s. Dự trù load/kiểm 120 s:

```text
T_smoke_slow = 120 + 6*(96/10+8/3+2)
                    + 6*(128/10+48/3+2)
                    + 3*(96/10+192/10+16/3+15+2)
             = 543.8 s = 9.06 phút < 10 phút
```

| Kịch bản giả định | r_p / r_d | LAPTOP text | LAPTOP text+ảnh | SMOKE có ảnh | SMOKE+LAPTOP có ảnh |
| --- | --- | ---: | ---: | ---: | ---: |
| Chậm | 10 / 3 | 51.84 phút | 64.20 phút | 9.06 phút | 73.26 phút |
| Giữa dải | 20 / 5 | 32.57 phút | 40.77 phút | 6.37 phút | 47.14 phút |
| Nhanh | 40 / 8 | 22.54 phút | 28.58 phút | 4.97 phút | 33.55 phút |

**Token feasibility vẫn OPEN:** chưa có shortlist/tokenizer hash của TASK-002; môi trường hiện không có tokenizers/transformers/tiktoken/sentencepiece. Không lấy 57 ký tự chia một hằng số để giả nhận 18/48 token. Khi có tokenizer thật, đếm toàn prompt đã render và gold từng item, lưu `token_feasibility.json` (model/tokenizer/template hash, counts, caps, pass); chỉ tokenizer không phải trọng số model. Gold hoặc input không vừa cap => sửa SMOKE trên DEV trước freeze; chưa có báo cáo này thì không gọi SMOKE runnable/đã đạt AC1 thực nghiệm. Biên 56.2 s là dự phòng có điều kiện, không bảo đảm tokenizer/VLM chưa chọn.

Stress LAPTOP +25% input = **4328.67 s = 72.14 phút**. SMOKE+LAPTOP mới = **4395.67 s = 73.26 phút**, hai đại lượng khác nhau. Số 72.14 trùng của v0.2 không còn dùng cho campaign mới. FULL phần request theo tốc độ chậm khoảng 9.45 giờ trên laptop, không đưa vào lượt 90 phút.

SMOKE hard deadline 600 s; LAPTOP 5400 s từ lúc load, projection trước LAPTOP≤4590 s (15% dự phòng). Quy tắc dự phòng 15% chỉ áp LAPTOP, không áp SMOKE. SMOKE 543.8 s còn 56.2 s; stress +25% input là599.0 s, chỉ còn1.0 s, nên chưa thể coi feasibility thực đã đạt. Trước freeze phải đo tokenizer/DEV, đặc biệt gold IF≤8 và OCR tiếng Việt có dấu≤16 output token; nếu không vừa thì sửa cap/item trước campaign và tính lại deadline, không cắt đáp án. Timeout item text 90 s, ảnh 120 s. Không cắt prompt, bỏ câu, đổi cap/order sau khi thấy khó. Deadline/incomplete đi qua bảng quyết định mục 6.3.

**DEV/bridge/lặp tài nguyên có budget riêng:** một lượt DEV 24 text + 6 ảnh dùng cận input text320/output48, ảnh như LAPTOP, fixed180 s: tối đa dự kiến 29.18/18.14/12.42 phút ở ba kịch bản. Không gộp lượt DEV vào tuyên bố “mỗi LAPTOP≤90 phút”. Bridge ngoài laptop và resource campaign 3 lần/A/B là các phiên riêng được đăng ký, không giả vờ nằm trong 64 phút.

### 3.4 Điều kiện laptop trước khi đo

Target là i7-8665U, 8 GiB RAM, UHD 620, Windows 11 theo ticket. RAM khả dụng sạch, disk thực và throttling vẫn UNKNOWN. Không suy ra “mọi model từ 0.5B đều không chạy” chỉ từ snapshot RAM 0.7 GiB.

- Đóng ứng dụng cạnh tranh, cắm sạc, cố định power mode, threads=4 làm mặc định thử nghiệm; runtime có thể chọn cấu hình khác trên DEV rồi khóa. CPU-only; iGPU là một cấu hình thí nghiệm riêng.
- Ngân sách process tree model + vision encoder + runtime + KV cache ≤3 GiB là ASSUMPTION; trước tải cần RAM khả dụng ≥ ngân sách peak dự kiến + 1 GiB dự phòng. Harness và logger phải được tính thêm trong kiểm khả dụng hệ thống.
- Chờ TASK-001 để xác định headroom; không tự tải model khi đĩa chỉ khoảng 4 GiB. Preflight yêu cầu dung lượng đáp ứng file model, runtime, cache và log, đồng thời tuân thủ mục tiêu ≥12 GiB trống của TASK-001 nếu áp dụng.
- Ghi nhiệt độ phòng nếu biết, CPU temperature nếu sensor có, nguồn AC, power mode, tần số CPU, RAM nền, thời gian idle và tiến trình cạnh tranh; trường không có sensor ghi UNKNOWN. Không coi nhiệt độ không đọc được là 0°C.
- Throttling bền vững của chính laptop là một kết quả tài nguyên cần báo; không xóa run chậm chỉ vì máy nóng. Mất AC, app nền chen vào hoặc meter lỗi mới là nguyên nhân RETRY về môi trường.

## 4. Quy tắc chấm và metric

### 4.1 Điểm chính tất định, một lần trả lời

Mọi prompt chỉ chứa input công khai; gold và lời giải nằm ngoài candidate. temperature=0/greedy, seed=1729, n=1. **Tắt thinking/reasoning mode** ở track trả lời thẳng; backend không tắt được phải sang track riêng có ngân sách tính toàn bộ reasoning token, không so với cap GR 8 token. Không self-consistency, sửa JSON, retry câu sai hoặc LLM-judge. Chỉ chấp nhận chuẩn hóa được khai báo trước, không thêm alias sau khi xem output.

| Nhóm | Điều kiện pass chính | Metric phụ |
| --- | --- | --- |
| GR | Một nhãn A-D đúng; trim khoảng trắng đầu/cuối, không chấp nhận giải thích thừa nếu prompt cấm | Accuracy theo subtype |
| IF | Đúng nội dung và mọi ràng buộc đã khai báo | Pass từng ràng buộc để tìm lỗi |
| BI | Ý nghĩa đúng theo đáp án hữu hạn; bảo toàn phủ định/thực thể | p_VI, p_EN; không dùng nhận diện ngôn ngữ tự động làm gold |
| GQ | Đúng answer + bộ citation đủ và đúng quan hệ entailment; câu không đáp án phải abstain | Answer EM, citation precision/recall, số trả lời không có hỗ trợ |
| SO | Parse toàn output JSON, không fence/text thừa; đúng schema, tên tool, kiểu và toàn bộ giá trị | JSON parse rate, schema rate, field accuracy, tool/argument accuracy |
| HC | Quyết định answer/abstain/refuse đúng; nếu answer thì nội dung đúng | False assertion, unnecessary refusal, Brier |
| VQA | Đáp án đúng từ ảnh, tên màu/đối tượng có alias khóa sẵn | Accuracy theo subtype |
| OCR | Exact match sau NFC và xử lý khoảng trắng đã nêu trong item | CER, có giữ dấu VI và chữ số |
| CHART | Đọc đúng nhãn/xu hướng/giá trị trực tiếp từ ảnh | Accuracy theo dạng biểu đồ |

GQ yêu cầu answer là span trích nguyên văn từ context, có vị trí span/alias đã khóa; không dùng câu trả lời tự do rồi phạt mọi paraphrase hợp nghĩa. GQ không coi “có chuỗi đáp án trong câu được trích” là đủ: câu đó có thể phủ định đáp án. Gold lưu `allowed_answer_citation_sets`, gồm các cặp đáp án và tập câu chứng minh. Toàn bộ citation phải thuộc một tập hợp lệ, không thưởng việc trích mọi câu. Câu unanswerable có answer=null và citations=[]; không thêm ngữ cảnh ngoài. `unsupported_answer_rate_all` = số item có khẳng định không được context hỗ trợ / **toàn bộ N_GQ** (16/160), dù question answerable hay không; `false_answer_unanswerable_rate` có mẫu số riêng 4/40. Không tráo hai mẫu số; cổng ≤1/16 hoặc ≤10/160 dùng rate_all.

SO chỉ mô phỏng tool call bằng JSON. Không gửi thư, gọi công cụ thật, mở URL hay thực thi đoạn code trong output. Reject key trùng, NaN/Infinity, bool thay cho integer và key ngoài schema khi `additionalProperties=false`. Parse hợp lệ không đồng nghĩa đúng nhiệm vụ.

OCR: CER = (substitution + deletion + insertion)/số Unicode code point của gold sau NFC; gold không rỗng; không chặn CER ở 1 vì insertion có thể làm CER>1. Không bỏ dấu, không đổi 0/O hoặc 1/l trừ khi item nói rõ. Biểu đồ dùng tolerance tuyệt đối/đơn vị đặt trước nếu không thể yêu cầu exact value; không để scorer tự chọn tolerance.

IF đếm “token cách nhau bởi khoảng trắng” khi cần độ dài, nói rõ trong prompt; không gọi đó là số từ ngữ nghĩa tiếng Việt. Không dùng checker EN cho tiếng Việt mà chưa kiểm fixture.

### 4.2 Hallucination và calibration

HC yêu cầu output nhỏ theo schema với decision, answer và confidence trong [0,1]. Confidence là mức model tự khai cho **quyết định answer/abstain/refuse của mình**, không phải xác suất đã được hiệu chuẩn. Gold định nghĩa quyết định chuẩn và đáp án, tránh nhập nhằng giữa “không đủ dữ kiện” và “bị cấm theo policy giả lập”.

```text
false_assertion_rate = số đưa khẳng định đáp án ở câu phải abstain/refuse / số câu phải abstain/refuse
unnecessary_refusal_rate = số abstain/refuse ở câu trả lời được / số câu trả lời được
Brier = mean((confidence - correct_decision)^2)
```

Confidence thiếu/không hợp lệ làm item fail nếu trường này được yêu cầu. Brier của phần hợp lệ phải đi cùng coverage; không âm thầm loại lỗi rồi báo calibration tốt. Với LAPTOP N=12, chỉ dùng Brier mô tả. FULL báo thêm reliability bins cố định 5 khoảng bằng nhau, ECE và risk-coverage có số mẫu mỗi bin; bin ít không đủ bằng chứng calibration. Không có logprob vẫn chạy được benchmark. Không biến benchmark này thành chứng nhận an toàn ngoài các policy được mô phỏng.

### 4.3 Độ trễ và tài nguyên

| Metric | Định nghĩa và cách báo |
| --- | --- |
| TTFT end-to-end | t_first_content_token - t_submit, đồng hồ monotonic; gồm tiền xử lý, encode và prefill. Không tính callback header rỗng là token đầu |
| Prefill tok/s | số input token chưa cache / thời gian pha prefill từ runtime; không lấy input/TTFT nếu TTFT chứa encode/queue. Không đo được thì UNKNOWN |
| Decode tok/s | (N_output-1)/(t_last_token-t_first_token), chỉ khi N_output≥2; token gồm cả reasoning ẩn nếu runtime thực sự sinh và cung cấp số đếm |
| Phân vị | TTFT, latency, prefill/decode báo p50 và p95; throughput thêm p05 vì p95 là đầu nhanh. Công thức nearest-rank: x_sorted[ceil(p*N)-1] |
| Peak working set | max theo thời gian của tổng working set các tiến trình thuộc model/runtime/encoder; lấy mẫu 100 ms, ghi phương pháp và PID tree |
| Peak private commit | đỉnh tổng private committed bytes cùng PID tree; báo riêng với working set và available RAM toàn máy |
| Tổng thời gian | từ load bắt đầu đến kết quả/scoring hoàn tất; tách load, warm-up, requests, probes, scoring, flush |
| Điều kiện nhiệt/điện | đầu/giữa/cuối: AC, power mode, tần số, nhiệt nếu đọc được, first/last probe ratio; không dùng TDP làm năng lượng tiêu thụ đo được |
| Disk | model, runtime, image processor, corpus, cache/log theo byte; tách GB và GiB |

Working set chứa trang resident, private commit là bộ nhớ đã commit; không cộng hai đại lượng thành “RAM” và không dùng mỗi private memory để bỏ sót file-mapped weights [S8]. Tổng working set có thể đếm trùng trang shared giữa process; ghi rõ đây là phép cộng bảo thủ. Không cộng peak riêng của các process ở các thời điểm khác nhau thành peak đồng thời. Sampling có thể bỏ lỡ đỉnh ngắn; lưu cả high-water mark process nếu có. Không lấy peak của toàn bộ Python trước lúc run làm peak riêng model.

Sáu probe tài nguyên độc lập nội dung, cùng request dài ≤128 input/≤32 output, đặt 2 ở đầu, 2 giữa, 2 cuối. Không dừng sớm EOS chỉ để làm speed đẹp; ghi số token thực và không dùng throughput không xác định. Latency chính đo trên mọi item; metric probe chỉ hỗ trợ so ổn định theo thời gian. Cỡ mẫu nhỏ thì p95 gần max, phải nêu N. Batch=1 và cache mode cố định. Warm-up không chấm quality nhưng có tính vào thời gian/peak run.

**Lỗi và timeout:** timeout riêng do candidate trên run hợp lệ = fail, giữ mẫu số; ghi latency bị kiểm duyệt tại timeout, không báo p95 thành công như p95 mọi request. Crash model = lỗi candidate nếu môi trường đạt; mất điện, meter lỗi, hash sai, gold lỗi = run không hợp lệ và RETRY. Timeout toàn run hoặc dừng vì an toàn RAM = incomplete, không đủ điều kiện PROMOTE.

### 4.4 Bridge FULL/laptop và HYBRID

Trước khi gắn quality ngoài laptop với resources local, pin weights/quant, tokenizer/template/processor, decoding/thinking flag, context cap, scorer và prompt payload. GPU FP16 khác CPU Q4 là hai cấu hình, không bridge bằng tên model.

**Pilot bridge (P3):** trước khi khóa candidate/campaign, chạy DEV cùng cấu hình trên laptop và host dự kiến để đo tỷ lệ khác canonical answer, pass vector, stop reason và timing. DEV không tăng N benchmark, không bảo đảm FULL tương đương. Chỉ giữ đường chuyển bằng chứng nếu pilot hỗ trợ; nếu không đạt thì dùng đường FULL shard trên laptop trong ticket riêng hoặc giữ claim quality ở host FULL. Không hạ chuẩn bridge sau khi xem FULL.

**Bridge đăng ký trước:** sau khi khóa candidate, chạy đúng 80 text + 12 ảnh LAPTOP (hoặc 80 text nếu chỉ text) ở host FULL, cùng seed/input bytes/config. Lưu output từng item và đối chiếu với run laptop. Bridge pass yêu cầu 100% item cùng pass/fail, cùng decision/citation/tool arguments và cùng canonical task answer sau đúng normalization đã khóa; score vector, cap, stop reason không có khác biệt ảnh hưởng chấm. Raw whitespace chỉ được bỏ qua nếu scorer vốn cho phép. Không tune theo các item sai bridge rồi giữ nguyên campaign.

Bridge đạt => nhãn `FULL_HOST_VALIDATED_BRIDGE_PASSED`; chưa chứng minh mọi output trên 920 item sẽ giống laptop. Báo host FULL và resource host riêng; không gọi “FULL đã chạy trên laptop”. Bridge không đạt hoặc thiếu => quality chỉ thuộc host FULL, candidate local giữ KEEP_EXPERIMENTAL; có thể chạy FULL theo shard trên laptop ở ticket riêng để bỏ nhu cầu chuyển bằng chứng. Bridge không tăng N thống kê.

HYBRID chỉ thiết kế, chưa chạy. Cùng item/gold; router, retry, cache, fallback cố định. Tổng USD gồm mọi attempt lỗi và verification, mẫu số chỉ task gốc pass:
`cost_per_verified_success=total_actual_USD/verified_success_count`.
Mẫu số 0: +infinity nếu có chi phí, undefined nếu 0/0. Báo tokens/API calls/API route rate/e2e latency. Không dùng giá chưa tra hay credits giả định làm số thực.

### 4.5 Xác nhận lợi ích tài nguyên

Lượt LAPTOP đơn và 6 probe đủ kiểm feasibility sơ bộ, **không đủ để xác nhận tiết kiệm 15-20%**. Đường resource promotion bắt buộc 3 lượt hoàn chỉnh cho A và 3 cho B: order **A1, B1, B2, A2, A3, B3** hoặc đảo A/B bằng seed đã đăng ký; ba block đối chiếu là (A1,B1), (A2,B2), (A3,B3). Tất cả dùng cùng workload, power, threads, cache mode; mỗi run vẫn≤90 phút.

Trước mỗi run idle ít nhất 10 phút và nhiệt CPU về trong ±2°C mức ban đầu nếu sensor có; nếu không có sensor thì cùng idle protocol và ghi UNKNOWN. Không loại run nóng chỉ vì kết quả xấu. Fixed hardware/power, không tải nền; lỗi khách quan theo §6.3. Sáu lượt có ngân sách tối đa 9 giờ chạy cộng thời gian nghỉ, **ngoài** phiên LAPTOP sàng lọc. Chỉ làm sau shortlist, không thực hiện trong Task 3.

Báo từng run, median/min/max, CV của log latency hoặc tỷ lệ paired, memory peak và thermal drift; 3 lượt không chứng minh phân phối hay CI chắc chắn. Để claim resource gain, **cả ba block** phải đạt memory ratio≤.85 hoặc latency ratio≤.80; metric còn lại không tệ quá 10% ở bất kỳ block. Tất cả cổng memory/deadline vẫn đạt. Nếu chỉ median đẹp, block không nhất quán hoặc spread ratio>10% quanh median => KEEP_EXPERIMENTAL, không rerun tìm may. Đây là rule tái lập thận trọng, không gọi là p<.05 của cải thiện resource.

## 5. Thống kê, MDE, seed và số lượt

### 5.1 Wilson cho tỷ lệ nhị phân

Với k pass trên n, p=k/n, z=1.95996398454 cho CI hai phía 95% [S1]:

```text
center = (p + z²/(2n)) / (1 + z²/n)
half   = z*sqrt(p*(1-p)/n + z²/(4n²)) / (1 + z²/n)
CI     = [center-half, center+half]
```

Wilson là xấp xỉ score interval, không phải exact binomial interval. Dùng cho từng tỷ lệ nhị phân khi độc lập là hợp lý. Trên corpus cố định, điểm đã biết không có “sai số đo accuracy”; CI mô tả bất định khi khái quát sang tình huống lấy mẫu tương tự. Dữ liệu biên soạn thủ công giới hạn ý nghĩa suy rộng này.

Ví dụ tính toán, không phải model results: 48/80=60% có Wilson [49.05%,70.04%]; 57/80=71.25% có [60.54%,80.01%]. 9/12=75% vẫn có [46.77%,91.11%]. Vì phân tầng và có thể có cụm, không dùng các ví dụ Wilson gộp như điều kiện bảo đảm exact cho S_text.

### 5.2 Phương pháp chính khớp power plan

**Đơn vị thiết kế bắt buộc:** một item = một cluster tình huống trong điểm chính. Không có hai câu dùng cùng tài liệu/ảnh hoặc chỉ thay entity; nếu không thỏa, corpus phải sửa trước freeze hoặc đăng ký một statistical plan mới. Không lấy bảng MDE độc lập cho N hàng khi thực có ít cluster hơn.

**Cổng absolute quality:** LAPTOP chỉ sàng lọc bằng số đếm đặt trước (§6), không chứng nhận population floor bằng CI nhỏ mẫu. FULL dùng lower bound một phía 95% Hoeffding cho trung bình các biến độc lập trong [0,1], không cần cùng xác suất [S10]:
`L=max(0,S-sqrt(log(20)/(2*N)))`.
Vì weights text/ảnh tỷ lệ số item trong từng score, công thức áp riêng S_text N=800 và S_mm N=120; không áp N=920 cho S_vlm. Margin tương ứng .04327 và .11172. Lỗi giả định độc lập không được khắc phục bằng đổi tên cluster; nếu independence audit không đạt thì chưa có xác nhận.

**So sánh candidate với baseline:** McNemar exact hai phía là phép kiểm chính, phù hợp bảng MDE §5.3. Gọi b=A đúng/B sai, c=A sai/B đúng, m=b+c:
```text
p_value = 1 nếu m=0
p_value = min(1,2*sum_{j=0}^{min(b,c)} choose(m,j)*0.5^m) nếu m>0
delta = (b-c)/N
```
Điều kiện exact: các cặp độc lập và dưới null các dấu bất đồng có xác suất hai chiều bằng nhau (exchangeability). Không giả định exact cho mọi null tổng hợp dị biệt theo stratum; báo hạn chế và dùng plan khác nếu giả định không phù hợp. Bảng power là mô hình q đồng nhất đăng ký trước, không performance của corpus chưa có.

**Bootstrap chẩn đoán:** vẫn dùng paired stratified percentile bootstrap 10000 lần, seed20261102, giữ A/B cùng chỉ số và resample cluster trong (task,language); quantile nearest-rank .025/.975. Báo CI để xem sensitivity/heterogeneity nhưng **không dùng nó làm p-value chính hoặc cổng PROMOTE nhỏ mẫu**. Nếu CI bootstrap mâu thuẫn McNemar hoặc thấy phụ thuộc, KEEP_EXPERIMENTAL để review, không chọn phép kiểm thuận lợi. Cổng mâu thuẫn này làm power quyết định cuối có thể thấp hơn bảng power của phép kiểm.

Audit mới ở §5.5 cho thấy bootstrap percentile nhỏ mẫu có thể lệch alpha; đó là lý do thay vai trò, không phải chọn test sau khi nhìn model outputs. Chưa chạy model nào.

### 5.3 MDE và power

Đăng ký alpha=0.05 hai phía, power=0.80, so một candidate với một baseline đã định trước. q=P(A và B bất đồng). Xấp xỉ lập kế hoạch:

```text
MDE ≈ (1.959964 + 0.841621)*sqrt(q/N)
N ≈ ceil(7.84888*q/delta²)
```

Không chỉ dựa xấp xỉ ở N nhỏ. Các số “exact planning” dưới đây được tính bằng tổng hữu hạn: D~Binomial(N,q); B|D=d~Binomial(d,(q+delta)/(2q)); cộng xác suất hai đuôi vượt vùng bác bỏ McNemar exact, rồi tìm delta nhỏ nhất có power≥0.80. Điều kiện khả thi |delta|≤q. Đây là **phép tính tự làm ở v0.2, Claude C báo đã tái tạo**, không phải performance của model.

| Tầng/phần | N độc lập danh nghĩa | MDE q=.20 | MDE q=.30 | MDE q=.50 |
| --- | ---: | ---: | ---: | ---: |
| SMOKE text | 12 | Không đạt power 80% | Không đạt power 80% | Không đạt power 80% |
| SMOKE ảnh | 3 | Không thể bác bỏ ở alpha .05 | Như bên | Như bên |
| LAPTOP text | 80 | 14.19 pp | 17.62 pp | 22.69 pp |
| LAPTOP ảnh | 12 | Không đạt power 80% | Không đạt power 80% | Không đạt power 80% |
| FULL text | 800 | 4.53 pp | 5.53 pp | 7.11 pp |
| FULL ảnh | 120 | 11.76 pp | 14.44 pp | 18.52 pp |

pp = điểm phần trăm. Với N=12, ngay delta=q tối đa thì power chỉ 1.94%, 11.78%, 61.28% tương ứng q=.20/.30/.50. Vì vậy không điền MDE ngoại suy không khả thi thành khả năng thật của SMOKE. N=80, delta=.10 có power lần lượt 43.68%, 29.49%, 19.83%.

N xấp xỉ để phát hiện 10 pp: 157/236/393 câu cho q=.20/.30/.50; cho 5 pp: 628/942/1570. Cỡ mẫu exact, phân tầng, nhiều so sánh và cluster có thể cần lớn hơn. FULL 800 text chưa bảo đảm phát hiện 5 pp khi q=.30 hoặc cao hơn. Tầng ảnh 120 không đủ để tuyên bố các cải thiện nhỏ. Không lấy N=920 để giả định đủ power cho từng năng lực ảnh hoặc điểm S_vlm có trọng số.

Nếu trung bình m câu/cluster và tương quan nội cụm rho, độ nhạy thô `N_eff≈N/[1+(m-1)*rho]`. Ví dụ m=2,rho=.5 thì N_eff≈N/1.5, MDE tăng khoảng sqrt(1.5). Đây là ESTIMATE, không thay bootstrap cụm. Báo số tình huống và số cluster thật cùng số item.

### 5.4 Lượt chạy, seed và nhiều so sánh

Selection seed20261102, order4242, generation1729, bootstrap20261102; pin PRNG version hoặc lưu indices. Một lượt quality/candidate/tầng; tối đa 3 cấu hình đăng ký ở LAPTOP. Chọn **một** candidate cùng baseline cho FULL mới. Không nhìn FULL rồi đổi ứng viên. Nếu phải xác nhận nhiều so sánh, Holm alpha .05 và tính lại power; bảng hiện tại chưa tính multiplicity.

Sáu probe và các lượt lặp resource §4.5 không tăng N quality. Stochastic decoding ngoài track chính; muốn dùng phải đăng ký 3 seed và ngân sách riêng, gộp theo item. Không lấy lượt tốt nhất. RETRY chỉ do nguyên nhân khách quan có log và giới hạn ở §6.3.

### 5.5 Audit bootstrap và đặc tính vận hành

Phép tính mới **tự tính, chờ Claude C tái tạo**. 5000 outer datasets mỗi kịch bản; q=.30; mỗi item có dấu +1/-1/0 với xác suất (q+delta)/2, (q-delta)/2, 1-q. Có 12 strata nhóm×ngôn ngữ, sizes [8,6,6,8,6,6] lặp 2 ở N=80, nhân 10 ở N=800. Case cluster=2 dùng hai item hoàn toàn tương quan/cluster, chỉ còn 40/400 đơn vị. Bootstrap vẫn resample đúng cluster. Cỡ nominal CI95%, B=10000, cùng thuật toán §5.2.

| N hàng / cluster size | Delta | Power bác bỏ hai phía bootstrap | Monte Carlo SE |
| --- | ---: | ---: | ---: |
| 80 / 1 | 0 | 5.83% (test size) | 0.33 pp |
| 80 / 1 | 10 pp | 41.72% | 0.69 pp |
| 80 / 1 | 15 pp | 74.74% | 0.61 pp |
| 80 / 1 | 16 pp | 80.07% | 0.56 pp |
| 80 / 1 | 17 pp | 85.00% | 0.50 pp |
| 80 / 2 | 0 | 9.10% (test size) | 0.40 pp |
| 80 / 2 | 17.6 pp | 65.46% | 0.67 pp |
| 80 / 2 | 22 pp | 84.66% | 0.50 pp |
| 800 / 1 | 0 | 5.06% (test size) | 0.30 pp |
| 800 / 1 | 5.25 pp | 77.03% | 0.59 pp |
| 800 / 1 | 5.50 pp | 80.07% | 0.56 pp |
| 800 / 1 | 5.75 pp | 84.92% | 0.50 pp |
| 800 / 2 | 7.5 pp | 77.85% | 0.58 pp |
| 800 / 2 | 8.0 pp | 83.84% | 0.51 pp |

MDE bootstrap theo grid khoảng16 pp (80 singleton) và5.5 pp (800 singleton); cần interval/grid refinement để nói chính xác hơn, **không gọi MDE exact ở alpha .05** vì test size thực khác .05. Stress cluster=2 làm khoảng MDE tăng, đồng thời type-I error xấu hơn ở N=80. Kết quả khác số reviewer do dùng 12 strata với quantile rule xác định; không coi đó là bác bỏ review.

Tái tạo không cần chạy model: sinh outer multinomial counts bằng NumPy Generator PCG64; tính distribution bootstrap của tổng dấu bằng tích đa thức trinomial theo strata; dùng convolution/DFT không alias (length≥2N_eff+1). Với F0=P_boot(D≤0), Fminus=P_boot(D<0), xác suất hữu hạn B=10000 CI loại 0 là BinCDF(249;B,F0)+BinSF(9749;B,Fminus). Trung bình trên 5000 datasets; SE=s.d. các xác suất/sqrt(5000). Đây là tích phân conditional bootstrap để tránh sinh hàng triệu ma trận, cùng percentile decision ở trên. JSON audit kèm raw aggregate, seeds và parameters; không giao implementation harness.

Các giá trị này là power của phép kiểm/CI, **không phải** xác suất qua mọi cổng quality/resource/bridge. Các gate có thể làm xác suất cuối thấp hơn; phải báo riêng.

## 6. Quality floor và quyết định đặt trước

### 6.1 Tách sàng lọc khỏi xác nhận

LAPTOP đủ tìm lỗi lớn và chọn hướng, không đủ vừa chứng nhận mọi subgroup vừa giữ power chấp nhận được. **Sàn nhóm thông thường, ngôn ngữ và auxiliary rates ở LAPTOP là chẩn đoán**; chỉ veto sụp cực đoan ở §6.2.2 chặn provisional, không là cổng cứng khiến model không bao giờ được lên FULL. Point screen để baseline local tạm thời: **≥57/80** (71.25%); đây là ngưỡng sàng lọc chọn trước, không tuyên bố đã chứng nhận population floor≥60%. Wilson vẫn báo như thông tin mô tả.

| Cổng | LAPTOP | FULL, trước PROMOTE confirmed | Lý do chính sách |
| --- | --- | --- | --- |
| Tổng text | ≤39/80 REJECT nếu run hợp lệ/hoàn chỉnh; ≥57/80 và không veto cho provisional; ≥48/80 xem xét FULL | S_text≥.70; Hoeffding L≥.60 | Tách screening từ certification; FULL có đủ N cho bound bảo thủ |
| GR | Báo p và lỗi; mốc8/16 là cảnh báo | ≥80/160 | MC4: sàn50% cao hơn chance25%, vẫn chỉ là năng lực tối thiểu |
| IF | Chẩn đoán, mốc9/12 | ≥90/120 | Muốn ít nhất75% nhiệm vụ đúng tất cả constraint |
| BI | Chẩn đoán, mốc6/12 | ≥60/120 | Sàn50% cho MC4/finite answer, không chứng minh năng lực ngôn ngữ rộng |
| GQ | Chẩn đoán10/16; unsupported riêng | ≥100/160; unsupported_rate_all≤10/160 | Ưu tiên hỗ trợ bằng evidence, không cho bịa được bù bởi task khác |
| SO | Chẩn đoán10/12 strict,11/12 parse | **≥96/120 strict**; parse≥110/120 | JSON đúng nghĩa cần cao hơn chance; parse lỗi ảnh hưởng tích hợp |
| HC | Chẩn đoán9/12, false assertion và refusal | ≥90/120; false assertion≤10/60; unnecessary refusal≤20/60 | Khống chế cả bịa và từ chối thừa, không thưởng always-abstain |
| Ngôn ngữ | Báo riêng p_VI,p_EN và độ khó/token | p_VI≥.60 và p_EN≥.60 | Tránh bỏ hẳn một ngôn ngữ; không diễn giải chênh như hiệu ứng nhân quả |
| Resource | Peak tree≤3 GiB; no OOM;≤90 phút; decode p50≥3, prefill p50≥10 | Phải có resource laptop hợp lệ đúng config | Envelope của ticket, cần calibration trước campaign |
| TTFT/timeout | p95 TTFT text≤45s/ảnh≤90s; timeout≤5% số item | Giữ cùng điều kiện laptop | Mục tiêu feasibility đề xuất, không số đo sẵn |

Resource thresholds là ASSUMPTION, phải chốt từ TASK-001/DEV trước run chính. Prefill phase không đo được => resource status UNKNOWN và không PROMOTE local; không thay input/TTFT để lấp ô trống.

Các tỷ lệ FULL là policy mô tả năng lực mong muốn; không phải khoảng tin cậy đồng thời cho mọi subgroup. Errata hạ SO-strict từ100/120 xuống96/120 (80%), giữ parse110/120. Lý do và trade-off được định lượng ở §6.2.3; đây là policy chọn từ kịch bản thiết kế trước khi có model score, không phải suy từ candidate thắng. Human reference và kiểm corpus vẫn phải làm trước freeze.

**P5:** cổng text Hoeffding L≥.60 không ràng buộc thêm khi S_text≥.70 và N=800 (L≥.65673). Giữ để báo cùng dạng bound tuyệt đối và làm rõ claim population; không tính nó như một bằng chứng độc lập thứ hai. Cổng ảnh L_mm≥.65 có ràng buộc và làm sàn thực tế92/120.

VLM provisional cần text≥57/80, không veto text/HC và image≥9/12, nhưng mốc2/4 từng nhóm ảnh chỉ là cảnh báo. Nhãn `provisional_vlm_research_only`; không tự thực thi tool, không khẳng định OCR/ảnh đã xác nhận. VLM confirmed cần toàn cổng text FULL, S_mm≥.75 và Hoeffding L_mm≥.65, mỗi nhóm ảnh≥.60. Với N_mm=120, margin .11172 khiến điều kiện thực tế ít nhất **92/120**; ghi số nguyên này để không che ngưỡng thực. S_vlm không thay cổng thành phần.

### 6.2 Đặc tính vận hành và hiệu chỉnh

#### 6.2.1 Tái tạo độc lập bảng LAPTOP v0.3

Tính lại từ định nghĩa cổng, không dùng script của Claude C. Mô hình độc lập, strict accuracy p đồng đều ở mọi task/ngôn ngữ. Cổng v0.2 là nhóm≥[8,9,6,10,10,9], VI/EN≥24/40, tổng≥57/80. Bảng v0.3 cũ ghi Monte Carlo200000/p; cột mới gồm exact convolution và MC500000/p. Các số point/eligibility dùng đuôi nhị thức. Không gồm resource, bridge, image hay baseline-comparison.

| p đồng đều | v0.3 công bố: mọi gate v0.2 (MC) | Tái tạo exact mọi gate v0.2 | MC mới (500000) | Point≥57 exact | FULL≥48 exact | Point + veto cuối exact |
| --- | --- | --- | --- | --- | --- | --- |
| 0.70 | 4.53% | 4.55% | 4.49% | 45.791% | 97.88607% | 45.732% |
| 0.75 | 14.81% | 14.71% | 14.66% | 81.805% | 99.89567% | 81.742% |
| 0.80 | 34.22% | 34.11% | 34.02% | 97.833% | 99.99885% | 97.806% |
| 0.85 | 60.28% | 60.25% | 60.18% | 99.951% | 100.00000% | 99.946% |
| 0.90 | 84.32% | 84.37% | 84.31% | 100.000% | 100.00000% | 100.000% |

Exact gate cũ: với mỗi task có h item/ngôn ngữ, lập đa thức hai biến hệ số BinPMF(a;h,p)*BinPMF(b;h,p), bỏ a+b dưới sàn nhóm, nhân sáu đa thức; cộng hệ số a≥24,b≥24,a+b≥57. Exact point+veto dùng convolution các PMF bị cắt theo sàn veto, riêng HC liệt kê hai nhánh Bin(6,p). MC cũ mới đều phù hợp phân phối exact; không cần viện dẫn số của reviewer làm ground truth. Số làm tròn100% không có nghĩa xác suất đúng bằng1. Chi tiết seeds/counts/MCSE trong `TASK003_NUMERICAL_AUDIT_v031.json`.

#### 6.2.2 E1: REJECT chất lượng; E2: veto sụp cực đoan

**E1:** chỉ áp LAPTOP có đủ80 text, input/scorer hợp lệ, không incomplete/external/cause-unresolved. Dùng Wilson upper hai phía95% với z=1.959963984540054 để chọn ngưỡng số đếm đặt trước: U<.60 tương đương **k≤39/80**; U(39)=.59506666, U(40)=.60702585. Sau các hàng lỗi ưu tiên1-4, decision là REJECT / COMPLETE_FOR_CONFIG, reason `QUALITY_BELOW_FLOOR`; không đòi đã đủ bằng chứng resource. Q1: thiếu phase timer nhưng đủ80 quality outputs hợp lệ không tự làm run thành CAUSE_UNRESOLVED; chất lượng vẫn có thể bị REJECT. Nếu output/input/scorer không hợp lệ, incomplete hoặc nguyên nhân sự cố thật chưa rõ thì các hàng lỗi trước vẫn ưu tiên. Không REJECT chất lượng từ một run thiếu item. Wilson gộp không được quảng cáo là CI exact dưới dị biệt phân tầng; bảng sau chỉ là operating characteristic của quy tắc k≤39 trong mô hình đồng đều độc lập.

| p thật đồng đều | P(REJECT), exact |
| --- | --- |
| 0.25 | 99.999869% |
| 0.40 | 95.550294% |
| 0.50 | 45.553606% |
| 0.60 | 2.712356% |
| 0.70 | 0.005673% |
| 0.75 | 0.00004174% |
| 0.80 | 0.00000005% |

Ở p=.70, xác suất loại nhầm0.00567268%, dưới0.01%. 40-47/80 giữ KEEP_EXPERIMENTAL / NO_FULL_SLOT_CURRENT_CAMPAIGN; từ48 đủ điểm xét FULL nếu các điều kiện feasibility đạt.

**E2, veto cuối:** (a) bất kỳ trong sáu nhóm text có strict accuracy<1/3, tức GR/GQ≤5/16 hoặc IF/BI/SO/HC≤3/12; **hoặc** (b) HC có0/6 strict pass ở nhánh trả lời được hay0/6 ở nhánh không nên trả lời trực tiếp. Nhánh HC dùng strict pass của rubric đã khóa, không nhầm với chỉ parse/decision đúng. Veto chỉ chặn PROMOTE provisional, ghi `CATASTROPHIC_SUBGROUP`; không chặn FULL_ELIGIBLE khi text≥48 và resource đạt. Không áp <1/3 vào nhóm ảnh4 câu. Sàn nhóm thông thường vẫn chỉ là chẩn đoán ở LAPTOP.

Phần(b) là bổ sung cần thiết so với ví dụ ngưỡng của reviewer: always-answer có HC6/12, nên một mình (a) không chặn được; cả always-answer và always-abstain bị chặn khi nhánh tương ứng0/6. SO0/12 bị(a) chặn. Không dùng ngưỡng<50% vì false veto lớn.

| p đồng đều | Chỉ nhóm <1/3 | Cuối: thêm HC 0/6 | Nếu dùng nhóm <1/2 |
| --- | --- | --- | --- |
| 0.70 | 0.9859% | 1.0935% | 18.8994% |
| 0.75 | 0.2135% | 0.2540% | 6.9857% |
| 0.80 | 0.0314% | 0.0429% | 1.8425% |
| 0.85 | 0.0026% | 0.0047% | 0.3005% |
| 0.90 | 0.0001% | 0.0003% | 0.0213% |

Các tỷ lệ trên là **xác suất veto vô điều kiện**, không phải xác suất mất provisional sau khi đã qua point screen. Với B_n~Bin(n,p), no-veto(a) là P(B16≥6)^2*P(B12≥4)^4. No-veto cuối thay một thừa số HC bằng tổng P(A=a)P(U=u) trên a,u≥1 và a+u≥4, A,U~Bin(6,p) độc lập. Đây là công thức exact, không cộng hai rủi ro chồng nhau. Cột point+veto ở bảng LAPTOP là xác suất kết hợp thực sự; tại p=.70 nó là45.732%, so với point-only45.791%.

#### 6.2.3 E3: FULL, cổng chính và phụ

Các cổng chính FULL v0.3 là nhóm≥[80,90,60,100,100,90], v0.3.1 đổi duy nhất SO thành96. Tổng≥560/800, VI/EN≥240/400. Ảnh tổng≥92/120 và mỗi nhóm≥24/40. Bảng sau tính exact theo nhị thức và tích xác suất các nhóm độc lập; cột “mọi sàn nhóm” chưa bao gồm tổng/ngôn ngữ/cổng phụ. Ở p=.85, mọi nhóm cũ là74.222%, SO riêng74.432%; không gộp hai con số này thành cùng74.4%.

| p đồng đều | Text≥560/800 | Mọi sàn nhóm v0.3 | SO≥100/120 | Mọi sàn nhóm v0.3.1 | SO≥96/120 | Ảnh≥92/120 | Ảnh92 + mỗi nhóm24/40 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.70 | 51.743% | 0.001% | 0.060% | 0.017% | 0.911% | 6.512% | 6.505% |
| 0.75 | 99.941% | 0.583% | 1.934% | 3.664% | 12.166% | 38.207% | 38.180% |
| 0.80 | 100.000% | 18.480% | 21.464% | 47.726% | 55.434% | 84.770% | 84.745% |
| 0.85 | 100.000% | 74.222% | 74.432% | 94.453% | 94.720% | 99.444% | 99.441% |
| 0.90 | 100.000% | 99.206% | 99.206% | 99.969% | 99.969% | 99.999% | 99.999% |

**Accuracy p một mình không xác định cổng phụ.** Profile tham chiếu R là ASSUMPTION: mọi strict pass có xác suất p; SO parse=.98, GQ unsupported=.02 trên toàn160 câu, HC false assertion=.03 trên60 câu không nên trả lời, unnecessary refusal=.03 trên60 câu trả lời được. Sinh item đa thức ba loại: strict-pass p, lỗi phụ e, fail khác1-p-e; SO lỗi phụ là1-parse. Lỗi phụ là tập con strict-fail, không sinh các cổng độc lập trái logic. Mỗi nhóm/language đúng số item; HC có30 câu mỗi nhánh mỗi ngôn ngữ. Các item/nhóm/ảnh độc lập trong kịch bản này. GQ thiếu dữ kiện vẫn dùng cùng p/e trong phép tính mô tả; corpus thật có thể khác.

MC500000 datasets/kịch bản; lần lượt kiểm cả tổng, ngôn ngữ, nhóm, SO parse≥110, GQ unsupported≤10, HC false assertion≤10 và unnecessary refusal≤20. Bảng mới “text+ảnh” gồm cả ba nhóm ảnh, không chỉ tổng ảnh.

| p strict | Text chính + ngôn ngữ cũ / mới | Text mọi gate cũ / mới | Text + ảnh mọi gate mới |
| --- | --- | --- | --- |
| 0.70 | 0.001% / 0.013% | 0.001% / 0.013% | 0.001% |
| 0.75 | 0.583% / 3.662% | 0.582% / 3.660% | 1.371% |
| 0.80 | 18.448% / 47.841% | 18.440% / 47.823% | 40.567% |
| 0.85 | 74.246% / 94.462% | 74.214% / 94.421% | 93.880% |
| 0.90 | 99.193% / 99.967% | 99.151% / 99.924% | 99.923% |

Tỷ lệ MC có SE tối đa0.07071 điểm phần trăm, khoảng95% tối đa xấp xỉ±0.139 pp; trường hợp hiếm dùng khoảng Wilson, không suy xác suất0 từ zero-count. Tại p=.85, text mọi gate mới94.421% (MC Wilson95% [94.357%,94.484%]); text+ảnh93.880% ([93.813%,93.946%]). Đây là bất định số học của mô phỏng, không phải CI năng lực model/corpus thật.

Độ nhạy giữ p=.85 và thay lỗi phụ, không coi R là bảo đảm chung:

| Thay đổi tại p=.85, còn lại như R | Text mọi gate mới | Text + ảnh mọi gate mới |
| --- | --- | --- |
| parse=.90 | 33.497% | 33.299% |
| parse=.95 | 91.834% | 91.317% |
| unsupported=.10 | 6.357% | 6.323% |
| false assertion=.15 | 67.773% | 67.396% |
| parse=.90, unsupported=.10, false assertion=.15 | 1.612% | 1.603% |

**Tiêu chí chấp nhận thiết kế:** ở p=.85, cả CORE-TEXT và VLM quality phải có xác suất qua≥90% trong R và sensitivity parse=.95; lower95% của mô phỏng500000 phải≥90% để tránh kết luận do nhiễu MC. Các cổng v0.3.1 đạt tiêu chí này trong phép tính (parse=.95: text91.834%, text+ảnh91.317%). SO96/120 giữ một sàn semantic80% rõ ràng và khoảng dự phòng khi parse giảm; SO100/120 không đạt. Đây là nghiệm thu mô hình xác suất đã ghi, chưa phải nghiệm thu corpus. Profile lỗi phụ xấu hơn được báo như stress, không phải mục tiêu cần nới cổng để cho qua. Cần human/reference và profile dị biệt task/ngôn ngữ ở ticket CVC trước freeze. Không chọn lại profile R từ kết quả candidate.

**Q2, design point có chủ đích:** “sàn tổng70%” không mô tả đủ độ khó để được confirmed. Trong R đồng đều, p=.75 qua point screen LAPTOP81.805% (point+veto81.742%), nhưng chỉ qua FULL text3.660% hoặc text+ảnh1.371%; p=.80 có FULL text47.823%, p=.85 có94.421%. Provisional là sàng lọc dễ hơn rõ rệt so với confirmed. Mục tiêu xác suất qua≥90% tại p=.85 là lựa chọn chính sách đặt trước, không phải kết quả suy ra từ sàn70%, cũng không chứng minh model≤3B có thể đạt. Khả năng đạt của shortlist vẫn UNKNOWN; human reference kiểm khả năng giải/corpus, không thay số đo candidate.

Trong các profile đồng đều đã xét, sàn nhóm chi phối đường cong; không phát biểu cổng tổng “không bao giờ ràng buộc” cho mọi profile. Phản ví dụ: đúng bằng các sàn nhóm [80,90,60,100,96,90] cho tổng516/800=.645, có thể chia đều258/400 mỗi ngôn ngữ, nên vẫn trượt tổng560/800. C7 của CVC phải báo p50 và p90 (p tại đó xác suất qua toàn cổng quality đạt50%/90%) riêng cho CORE/VLM trong R và parse95%, kèm bracket, độ phân giải và bất định MC. Bảng grid hiện có chưa xác định chính xác hai điểm này; không dùng xấp xỉ “.80/.85” như nghiệm đã tính, không đổi target để candidate thắng.

Các bảng **không** là xác suất PROMOTE cuối: chưa gồm license/gold/input-validity, runtime/resources, bridge, exposure, điều kiện so baseline McNemar/bootstrap hay NI. MC seed=20261104; LAPTOP seed+100+i, FULL R seed+200+i, stress seed+300+i; thứ tự và phiên bản NumPy/SciPy trong JSON. Thuật toán: sinh counts mỗi stratum, tính conjunction boolean của các ngưỡng trên, cộng số pass; đối chiếu marginal nhị thức và exact convolution. Không chạy model, không coi số này là benchmark results.

Hiệu chỉnh trước freeze: kiểm null policies (A/B/C/D, copy, {}, always-answer/abstain), human reference độc lập (§2.3), gold quality, task mix, tokenizer và real-resource DEV. Floor là policy đã ghi lý do, không được học từ model test score.

Sau số đo thật, trigger revision nếu token/time projection vi phạm; human agreement/gold error không đạt; floor/ceiling trên profile tham chiếu; ≥2/3 candidate không qua chỉ do cổng phụ đã cho thấy false rejection cao; hoặc task không đại diện use case. Giữ kết quả dưới criteria cũ, mở ticket tiếp nối và cần FULL chưa lộ mới nếu thay policy sau khi xem test. Không hạ floor để candidate thắng. LAPTOP đã dùng sửa model trở thành development.

### 6.3 Quyết định không mâu thuẫn, có giới hạn retry

Mỗi record chứa `stage`, `run_status`, `decision`, `reason_code`, `campaign_status`, `attempt_index`. Decision vẫn chỉ bốn giá trị của ticket. BLOCKED là campaign_status, không thêm giá trị trái schema ledger.

`external_failure` chỉ ghi khi có log: AC đổi, tiến trình ngoài whitelist vượt mức RAM/CPU đã đăng ký, OS/runtime lỗi độc lập model, meter/hash/scorer sai. Nếu không đủ bằng chứng quy lỗi môi trường hay candidate => `CAUSE_UNRESOLVED`, không phỏng đoán. `candidate_resource_failure` cần preflight pass, meter/log đầy đủ, không sự kiện ngoài và OOM/crash/deadline do chính execution. Chậm vì nhiệt bền vững trên laptop thuộc kết quả resource.

| Ưu tiên | Điều kiện | Decision / campaign_status | Bước tiếp |
| --- | --- | --- | --- |
| 1 | Input/hash/license/gold/scorer không hợp lệ; chưa có tokenizer feasibility/permission | RETRY / BLOCKED_INPUT_OR_DESIGN | Chỉ mở lại khi artifact thiếu đã được sửa, không tự chạy model |
| 2 | Preflight thiếu RAM/disk hoặc không đạt hardware | RETRY / RETRY_PENDING lần đầu; BLOCKED_BY_HARDWARE sau lần hai | Tối đa 1 lần tái kiểm sau khắc phục có bằng chứng; không vòng retry tự động |
| 3 | External failure hoặc cause unresolved, kể cả incomplete | RETRY / RETRY_PENDING, sau tối đa1 retry thì BLOCKED_ENVIRONMENT hoặc BLOCKED_UNRESOLVED | Giữ cả log; không chọn run tốt nhất |
| 4 | Candidate resource failure đã xác định, ở bất kỳ stage kể cả SMOKE | REJECT / COMPLETE_FOR_CONFIG | Loại cấu hình trong envelope hiện tại; không kết luận mọi họ model |
| 5 | Run SMOKE hoàn chỉnh, không lỗi hard | KEEP_EXPERIMENTAL / READY_FOR_LAPTOP | SMOKE không PROMOTE theo quality |
| 6 | LAPTOP có đủ80 quality outputs hợp lệ, text≤39/80, đã qua phân loại lỗi hàng1-4 | REJECT / COMPLETE_FOR_CONFIG | QUALITY_BELOW_FLOOR; không cần resource metrics đầy đủ |
| 7 | LAPTOP đầy đủ, chưa bị loại chất lượng ở hàng6, nhưng resource metric/cổng chưa đủ | KEEP_EXPERIMENTAL / LOCAL_EVIDENCE_INCOMPLETE | Sửa phép đo ở DEV/ticket riêng, không rerun chọn may |
| 8 | LAPTOP đủ resource, text40-47/80 | KEEP_EXPERIMENTAL / NO_FULL_SLOT_CURRENT_CAMPAIGN | Không tự động cấp slot FULL |
| 9 | LAPTOP đủ resource, text≥48/80 nhưng chưa đạt point/image screen hoặc có veto sụp cực đoan | KEEP_EXPERIMENTAL / FULL_ELIGIBLE | Vào hàng chọn FULL theo quy tắc dưới |
| 10 | LAPTOP đủ resource, point/image screen và không veto, chưa có baseline cần thay | PROMOTE / PROVISIONAL_LOCAL_BASELINE | FULL_NOT_RUN là hợp lệ cho phạm vi provisional; không rơi vào “thiếu FULL” trước đó |
| 11 | LAPTOP đủ resource, point/image screen và không veto nhưng đang thay baseline hiện hữu | KEEP_EXPERIMENTAL / FULL_ELIGIBLE | Chờ xác nhận so sánh, không thay baseline từ LAPTOP |
| 12 | FULL hợp lệ nhưng quality gate fail hoặc bridge chưa pass | KEEP_EXPERIMENTAL / FULL_NOT_CONFIRMED_FOR_LOCAL | Báo đúng host; không đổi ngưỡng sau kết quả |
| 13 | FULL đạt gates, bridge pass; baseline đầu tiên hoặc điều kiện thay baseline §6.4 đạt | PROMOTE / CONFIRMED_RESEARCH_BASELINE_TRANSFER_CHECKED | Báo FULL host, bridge sample và resource local riêng |
| 14 | Trường hợp đầy đủ còn lại | KEEP_EXPERIMENTAL / NEEDS_NEW_EVIDENCE | Nêu thiếu chính xác; không tạo retry vô hạn |

**Đường KEEP_EXPERIMENTAL lên FULL:** ≥48/80 text, valid complete run, resource feasibility đạt, không gold/license/exposure blocker; VLM muốn xác nhận thêm cần image≥6/12 để chi FULL ảnh, nếu thấp hơn chỉ FULL text. Các subgroup thấp **không chặn eligibility**. Chọn tối đa một candidate trong ≤3 đăng ký: S_text cao nhất, hòa thì S_mm nếu xét VLM, rồi median latency thấp hơn, rồi config_hash theo thứ tự từ điển. Chủ dự án có thể chọn tạm hoãn vì chưa có người/môi trường FULL; khi đó FULL_NOT_READY, không gọi thất bại model. Không thay candidate sau khi nhìn FULL.

**E4:** đã bỏ hàng “incomplete khác” vốn trùng hàng3. Run hết90 phút nhưng không đủ bằng chứng quy nguyên nhân đi hàng3: attempt0 => RETRY / RETRY_PENDING; chỉ chạy lại sau khắc phục/đo bổ sung có bằng chứng, tối đa một retry. Nếu attempt1 vẫn unresolved => RETRY / BLOCKED_UNRESOLVED; không retry lần ba. Incomplete không được chấm như run hoàn chỉnh.

Retry budget chỉ áp cùng configuration/corpus/campaign; đổi weights/prompt/scorer là config/revision mới và chịu giới hạn candidate, không lách retry. Không dùng BLOCKED_BY_HARDWARE để tự tạo cam kết mua phần cứng.

### 6.4 Điều kiện thay baseline

Đạt floor FULL, bridge và resource local; đăng ký **một** mục tiêu trước khi xem FULL:

1. **Chất lượng:** delta_text≥.05 và McNemar exact p≤.05 đúng chiều; không subgroup point giảm quá .10 hoặc phá HC/GQ/SO gate. Nếu bootstrap sensitivity mâu thuẫn hay independence audit thất bại, KEEP_EXPERIMENTAL. MDE §5.3 là của test, không bảo đảm power của toàn conjunction.
2. **Tiết kiệm tài nguyên:** phải qua cả ba block resource §4.5 và non-inferiority margin -.03. Với thiết kế độc lập có thể khác xác suất theo item, dùng bound một phía bảo thủ cho D_i∈[-1,1]: `L_delta=delta-sqrt(2*log(20)/N)`; cần L_delta>-.03. Không dùng “p không đáng kể” để kết luận tương đương. N=800 có margin .08654, nên delta=0 chưa đủ chứng minh NI3pp; để margin≤.03 cần ít nhất6658 item độc lập, tức ticket xác nhận lớn hơn. Nếu không có đủ bằng chứng, giữ claim resource là **experimental**; không làm như benchmark hiện tại đã đủ power cho đường này.

**P1, ticket tiếp nối:** nghiên cứu phép NI cặp dùng phương sai/score (Tango/Newcombe hoặc phương pháp thích hợp), đăng ký rõ null tại delta=-.03, kiểm type-I error/power với q=.2/.3/.5, dị biệt strata và cấu trúc phụ thuộc trước khi chọn. Các xấp xỉ phương sai reviewer đưa là REPORTED, chưa thay statistical plan. Nếu đổi margin4-5pp phải có lý do sản phẩm và khóa trước data, không đổi sau kết quả. Mặc định tiếp tục bound hiện tại cho tới khi phương pháp thay thế được hiệu chuẩn và duyệt.

Bound bảo thủ có chi phí cỡ mẫu rõ; không lén dùng bootstrap nhỏ mẫu để làm đường resource dễ vượt. PROMOTE luôn kèm criteria_hash, dataset_manifest_hash, config_hash, scope, evidence_paths. Không triển khai production.

## 7. Chống contamination và quy trình đóng băng

### 7.1 Ngăn rò rỉ

1. Tạo corpus mới trong workspace nghiên cứu riêng. Không nhập file, raw_data, lời giải hay prompt của bộ Toán cũ. Manifest denylist ghi nguồn cũ bị cấm, không cần đọc nội dung cũ.
2. Chia theo situation/source_document/template family trước sinh biến thể; mọi bản dịch, crop, paraphrase cùng tình huống vào một split. Đổi tên thực thể không làm câu trở nên độc lập.
3. So hash exact và fingerprint NFC/casefold/space; word 5-gram Jaccard≥.80 chỉ là một cờ. Thêm signature bỏ entity/số, source_document/ảnh/family IDs, paraphrase map và kiểm tay các template gần nghĩa; kiểm câu ngắn 100%. Không có match n-gram không chứng minh không trùng. Với ảnh dùng hash bytes và perceptual similarity chỉ làm cờ; gold ảnh không nằm trong filename, EXIF hay alt text gửi model.
4. So với training, tuning, RAG corpus và prompt/example của project nếu có danh mục được phép. Nếu không có manifest bộ Toán cũ, ghi `old_math_overlap_check=UNKNOWN`; không tuyên bố giao bằng rỗng. Không truy xuất raw_data cũ để khép bằng chứng trái ticket.
5. Dataset công khai có thể đã xuất hiện trong pretraining. Synthetic cũng có thể giống template hoặc lộ qua generator; không khẳng định contamination bằng 0. Ghi provenance tác giả/model hỗ trợ nếu có, ngày, family, và đánh giá bởi người khác.
6. Giữ gold ngoài runtime candidate, retrieval index và ví dụ prompt. Tắt web/RAG ngoài ngữ cảnh cho trước trong CORE chính; cấu hình RAG mở rộng là campaign riêng.
7. Giữ sổ exposure: ai/công cụ nào thấy prompt/gold, mục đích, thời điểm. Nếu dùng gold test để tune, tập đó bị đánh dấu đã lộ; không dùng làm xác nhận độc lập nữa.

Hash chứng minh byte không đổi so với bản đã cam kết; hash **không chứng minh** model chưa thấy dữ liệu và không bảo mật gold. Phân quyền tệp và cách vận hành mới giữ được gold kín.

### 7.2 Đóng băng corpus, schema, scorer và tiêu chí

Chưa có corpus nên `dataset_manifest_hash=null`, `freeze_state=NOT_FROZEN`. Hash của tài liệu trong HANDOFF chỉ xác định revision đặc tả, không được dùng thay dataset hash.

Quy trình triển khai sau này:

1. Khóa taxonomy, số lượng, seed, license, notice, input/output caps, thresholds và statistical plan.
2. Xây DEV/SMOKE/LAPTOP/FULL riêng, review gold, kiểm cân bằng và nguồn; pin processor/font version.
3. Canonical JSON: UTF-8 không BOM, Unicode NFC, LF, key sắp tăng, không key trùng/NaN/Infinity. Số decimal dùng chuỗi chuẩn nếu cần để tránh serializer khác nhau; criteria dùng basis points/số nguyên. Quy tắc này phải có ID và test vector khi triển khai.
4. `item_hash=SHA256(canonical payload)` không chứa chính hash; payload gồm input, gold, rubric và asset hash. `asset_hash=SHA256(raw bytes)` cho từng ảnh/font đi kèm.
5. Manifest ghi path tương đối an toàn, byte size, raw SHA-256 từng JSONL/asset/notice/scorer/criteria, số item theo split/stratum, nguồn và phiên bản. Sort danh sách path; manifest không chứa root hash của chính mình.
6. `root_hash=SHA256(canonical manifest bytes)`; lưu `FREEZE.json` bên ngoài manifest với root_hash, ngày UTC, owner/reviewer và `criteria_hash`. Không tạo vòng tự tham chiếu.
7. Người giữ gold gửi root_hash + criteria_hash + config shortlist + timestamp UTC cho reviewer trước run đầu; reviewer giữ receipt/tệp chỉ đọc và timestamp nhận độc lập. Git signed tag chỉ xác nhận người ký/integrity, không tự chứng minh thời điểm. Có thể dùng dịch vụ timestamp tin cậy nếu sẵn và được phép, không bắt mua. Chưa có receipt/neo độc lập => FREEZE_UNATTESTED, không confirmed PROMOTE. Task này chỉ thiết kế, không gửi tin thay chủ dự án.
8. Trước mỗi run kiểm toàn bộ hash, IDs, schema, gold không nằm trong prompt, file list không thiếu/thừa, notice bytes và config. Bất kỳ mismatch => RETRY, không chấm rồi bỏ qua.

Nếu phát hiện câu lỗi sau freeze: ghi issue; đánh dấu run affected không đủ xác nhận; sửa corpus tăng revision và rerun mọi model được so sánh. Không xóa riêng câu model mình sai, không giữ cùng hash/version sau sửa. Giữ bản cũ để đối chiếu.

## 8. Schema JSONL và hợp đồng triển khai

### 8.1 Một dòng, một item

Đây là schema thiết kế có kiểu và bất biến, không phải validator đã triển khai. Không có đoạn Python/harness hoàn chỉnh trong deliverable.

| Trường bắt buộc | Kiểu/giới hạn |
| --- | --- |
| schema_version, item_id | string; item_id duy nhất toàn corpus |
| split | dev / smoke / laptop / full, đúng một giá trị |
| task, subtype, language | GR/IF/BI/GQ/SO/HC/MM; subtype có taxonomy; language vi/en |
| cluster_id, family_id | string; điểm chính một item/cluster; mọi biến thể vào cùng split ngoài điểm chính |
| difficulty, difficulty_basis | easy/medium/hard và lý do gán trước model; quota theo task×language |
| input | object: prompt, context[] với sid/text; assets[] với path, SHA-256, MIME, dimensions; tool_schema hoặc null |
| gold | object: scorer_id, answer, accepted_answers, allowed_answer_citation_sets, constraints, decision, output_schema, tolerance; chỉ dùng trường phù hợp scorer |
| limits | input_tokens_max, output_tokens_max, timeout_s là integer dương |
| provenance | origin, author, source_url hoặc null, source_revision hoặc null, source_item_id hoặc null, created_utc, retrieved_utc hoặc null, license_id, notice_ref, notice_sha256, contributor_permission_ref, assistance_provenance, derivative_of[] |
| review | gold_status, reviewer_ref, ambiguity_status; tập chính phải approved/clear |
| content_sha256 | null ở design example; 64 hex trong corpus freeze |

Bất biến: điểm chính phải có singleton cluster, difficulty quotas VI/EN và option-balance; permission/notice hash hợp lệ. Task text không có ảnh; MM có ít nhất một ảnh; đường asset không tuyệt đối/không `..`; context sid duy nhất; gold citations tồn tại; output schema cụ thể với required fields; giới hạn thích hợp tầng; null hash/revision review không được đi vào freeze. Không gửi object `gold` hoặc toàn dòng JSONL tới model.

### 8.2 Hai ví dụ minh họa đã lộ, chỉ dành DEV

Hai dòng dưới là nội dung mới, không phải câu test giữ kín. Review=unreviewed, contributor_permission_ref=null và content_sha256=null là có chủ đích, nên chưa đủ điều kiện đóng băng. Schema input chỉ là hợp đồng dữ liệu; prompt renderer phải thêm hướng dẫn output và giới hạn theo task, được pin/hash riêng và kiểm token.

```jsonl
{"schema_version":"gb0-0.3","item_id":"DEV-GQ-VI-001","split":"dev","task":"GQ","subtype":"supported_qa","language":"vi","cluster_id":"dev-kho-01","family_id":"dev-direct-evidence","input":{"prompt":"Hộp mẫu được chuyển tới kho nào? Trích nguyên văn span trong context. Trả JSON với answer và citations.","context":[{"sid":"S1","text":"Hộp mẫu được chuyển tới kho Lam."},{"sid":"S2","text":"Kho Đỏ đang đóng cửa."}],"assets":[],"tool_schema":null},"gold":{"scorer_id":"grounded_exact_v1","answer":"kho Lam","accepted_answers":["kho Lam"],"allowed_answer_citation_sets":[{"answer":"kho Lam","citations":["S1"]}],"constraints":[],"decision":"answer","output_schema":{"type":"object","required":["answer","citations"],"properties":{"answer":{"type":"string"},"citations":{"type":"array","items":{"type":"string"}}},"additionalProperties":false},"tolerance":null},"limits":{"input_tokens_max":320,"output_tokens_max":48,"timeout_s":90},"provenance":{"origin":"project_original","author":"TASK-003 Role D","source_url":null,"source_revision":null,"source_item_id":null,"created_utc":"2026-11-02T00:00:00Z","retrieved_utc":null,"license_id":"LicenseRef-GB0-Internal-v0","notice_ref":"GB0_INTERNAL_NOTICE_v1.txt","derivative_of":[],"notice_sha256":"39510d0f581c3db835465afd95e3a0d0a799cb657d2189c7fd3ff1ca4013eb9e","contributor_permission_ref":null,"assistance_provenance":{"tool":"ChatGPT Work","role":"draft_example","human_editor":null,"terms_review":"pending"}},"review":{"gold_status":"unreviewed","reviewer_ref":null,"ambiguity_status":"unreviewed"},"content_sha256":null,"difficulty":"easy","difficulty_basis":"Trích xuất trực tiếp một dữ kiện; không cần suy luận nhiều bước."}
{"schema_version":"gb0-0.3","item_id":"DEV-SO-EN-001","split":"dev","task":"SO","subtype":"mock_tool_call","language":"en","cluster_id":"dev-lamp-01","family_id":"dev-device","input":{"prompt":"Set lamp L2 to off. Return only a JSON tool call. Do not execute anything.","context":[],"assets":[],"tool_schema":{"name":"set_lamp","parameters":{"type":"object","required":["id","state"],"properties":{"id":{"type":"string","enum":["L2"]},"state":{"type":"string","enum":["on","off"]}},"additionalProperties":false}}},"gold":{"scorer_id":"json_exact_v1","answer":{"name":"set_lamp","arguments":{"id":"L2","state":"off"}},"accepted_answers":[],"allowed_answer_citation_sets":[],"constraints":[],"decision":"answer","output_schema":{"type":"object","required":["name","arguments"],"properties":{"name":{"const":"set_lamp"},"arguments":{"type":"object","required":["id","state"],"properties":{"id":{"type":"string","enum":["L2"]},"state":{"type":"string","enum":["on","off"]}},"additionalProperties":false}},"additionalProperties":false},"tolerance":null},"limits":{"input_tokens_max":192,"output_tokens_max":48,"timeout_s":90},"provenance":{"origin":"project_original","author":"TASK-003 Role D","source_url":null,"source_revision":null,"source_item_id":null,"created_utc":"2026-11-02T00:00:00Z","retrieved_utc":null,"license_id":"LicenseRef-GB0-Internal-v0","notice_ref":"GB0_INTERNAL_NOTICE_v1.txt","derivative_of":[],"notice_sha256":"39510d0f581c3db835465afd95e3a0d0a799cb657d2189c7fd3ff1ca4013eb9e","contributor_permission_ref":null,"assistance_provenance":{"tool":"ChatGPT Work","role":"draft_example","human_editor":null,"terms_review":"pending"}},"review":{"gold_status":"unreviewed","reviewer_ref":null,"ambiguity_status":"unreviewed"},"content_sha256":null,"difficulty":"easy","difficulty_basis":"Trích xuất trực tiếp một dữ kiện; không cần suy luận nhiều bước."}
```

Timestamp ví dụ là mốc ngày minh họa, không phải audit timestamp thực của generator; builder phải ghi thời điểm tạo thật. Giá trị `state=on` parse/schema vẫn hợp lệ nhưng phải fail semantics. Đáp án kho Lam với citation S2 phải fail. Điều này tránh scorer chỉ kiểm hình thức.

### 8.3 Manifest và run record

Manifest thiết kế cần: benchmark_id/revision, freeze_state, task counts, language counts, weights_basis_points, source/notice registry, file hashes/bytes, tokenizer/processor compatibility, split/exposure policy, seeds, thresholds, scorer/renderer revisions, reviewer và ngày. Không bịa SHA cho file chưa tồn tại.

Run header cần: run_id, task_id, timestamp UTC, spec_hash, dataset_manifest_hash, criteria_hash, config_hash, hardware_profile_ref, model_weights_hash, quant, tokenizer/chat_template/processor hashes, runtime version/build, CPU threads, decoding, context/output caps, cache policy, seed, OS, power/thermal conditions, phase_timer_support và budget.

Mỗi result cần thêm stage/run_status/reason_code/campaign_status/attempt_index, retry_evidence_ref, thinking_mode và token_feasibility_ref. Mỗi result cần: run_id/item_id, prompt_payload_hash, raw_output, output hash, input/visual/output token counts thực, timestamps các pha hoặc null, status, timeout/crash detail, pass, scorer_id, evidence_refs. Aggregate cần toàn bộ mẫu số, missing/censored counts, CI/method/seed/cluster count, paired table b/c, resources, decision, scope, criteria_ref và limitations. Không ghi credential, đường dẫn cá nhân hoặc dữ liệu người thật vào log.

### 8.4 Pseudocode luồng đánh giá

```text
ĐỌC spec, manifest, criteria và config đã đăng ký
NẾU chưa freeze, hash sai, license thiếu hoặc preflight không đạt:
    GHI RETRY với nguyên nhân; KHÔNG khởi chạy candidate
KIỂM time projection và deadline; tạo run_id, giữ scorer/gold ngoài candidate
TẢI candidate; warm-up; bắt đầu/duy trì meter
CHO mỗi item theo order đã khóa:
    NẾU deadline toàn run đến: GHI incomplete; DỪNG
    RENDER chỉ input; kiểm token caps; đối chiếu prompt payload hash
    GỬI một request; giữ nguyên output/status/timestamps
    CHẤM bằng scorer và gold tách biệt; không sửa output hoặc retry câu sai
    GHI append-only result; probe tài nguyên ở vị trí đã định
KIỂM đủ item và meter hợp lệ; tính scores, uncertainty và paired comparison
ÁP dụng decision matrix theo stage và ưu tiên; chặn incomplete và enforce retry budget; gắn scope/criteria_hash
XUẤT report, raw result và provenance; không publish
```

### 8.5 Kiểm thử cần giao cho bước triển khai, chưa chạy ở Task 3

- Gold đúng pass; JSON đúng schema nhưng sai nghĩa fail; duplicate key fail; câu trích dẫn phủ định hoặc sai sid fail.
- UTF-8/NFC/LF và SHA giống nhau theo canonical rule; sửa một byte asset khiến verify fail; không gửi gold tới candidate.
- Split leakage: paraphrase/bản dịch/crop chung cluster không được sang split khác; item thiếu license bị chặn.
- Fake clock kiểm TTFT/decode có công thức đúng, N_output=1 là N/A; timeout giữ mẫu số; process con được meter theo dõi.
- Tái tạo bảng thời gian, Wilson và exact power trong spec trong sai số làm tròn; thử m=0 McNemar; paired resampling giữ chỉ số A/B.
- Decision cases: SMOKE hoàn chỉnh chỉ KEEP_EXPERIMENTAL; SMOKE OOM xác định do candidate là REJECT; hash lỗi RETRY; incomplete không PROMOTE; 2 lần preflight fail => BLOCKED_BY_HARDWARE; đạt LAPTOP nhưng chưa FULL vẫn được provisional; KEEP có≥48/80/resource đạt => FULL_ELIGIBLE; PROMOTE thiếu criteria_hash/receipt bị chặn.

## 9. Rủi ro validity, overfitting và việc còn mở

### 9.1 Overfitting và construct validity

| Rủi ro | Kiểm soát và giới hạn kết luận |
| --- | --- |
| Dùng test để tune/chọn lại nhiều lần | DEV riêng, exposure ledger, tối đa3 candidate LAPTOP, một candidate FULL, retire tập đã lộ |
| Token cap VI/EN bằng nhau nhưng tokenizer khác hiệu quả | Không cắt text để fit; cân bằng nội dung/độ khó, báo tokens/ký tự/ngữ nghĩa theo ngôn ngữ; nếu VI không vừa, revision chung trước freeze. p_VI/p_EN không là phép đo language bias thuần |
| GR cap8 không đo reasoning có thinking dài | Track direct-answer, thinking off được ghi; thinking-only model sang track riêng có ngân sách tất cả token |
| Vị trí đáp án dễ bị đoán | Cân bằng A-D theo task×language; permute trước freeze, không sửa sau run |
| Nhạy prompt renderer ở model nhỏ | Trên DEV dùng renderer chính và một paraphrase tương đương, không chọn bản tốt riêng từng model; difference>10pp trên DEV là cờ cần mở rộng DEV hoặc báo limitation. Main vẫn một renderer đã khóa |
| GQ exact-match phạt paraphrase đúng | Prompt yêu cầu span nguyên văn, gold có offsets/aliases đã khóa; adjudication trước freeze |
| OCR VI có dấu bị mất do resolution/192 visual tokens | Người B phải đọc đúng gold từ chính ảnh cuối sau resize; kiểm dấu tại kích thước thực. Không đọc được => asset fail; budget không đáp ứng => VLM configuration unsuitable, không gọi model kém OCR tổng quát |
| Gold/source/tool-assisted bias | Hai người giải độc lập 100%, family/source ledger, quyền rõ, không để candidate tạo toàn tập |
| Template overlap vượt n-gram check | Signature entity-stripped + source/family audit + kiểm nghĩa thủ công |
| Bootstrap nhỏ mẫu anti-conservative | Chỉ chẩn đoán; primary test/power khớp; singleton clusters bắt buộc |
| Chọn ngưỡng theo model thắng | Trigger revision rõ, lưu kết quả criteria cũ, FULL mới chưa lộ |
| Nhiệt/nguồn và host mismatch | Logged preflight, retry hữu hạn, bridge và 3 run mỗi bên khi claim resource |

### 9.2 Điều còn thiếu trước freeze hoặc execution

- Tokenizer/model shortlist + token_feasibility thật: **UNKNOWN**, F3 chưa khép phần đo.
- Clean-boot RAM/disk/throughput, time/vision calibration, phase timer: cần TASK-001/TASK-002 và DEV.
- Corpus, permission records, independent gold solutions, scorer/validator và receipt freeze: chưa có. F14 full ticket SHA đã đóng theo review vòng2.
- Môi trường và người giữ FULL, ngân sách thời gian/labor: chưa phân công. Không tự chạy Colab/API hoặc liên hệ người khác.
- v0.3.1 đã nhận ACCEPT_ERRATA / APPROVE_DESIGN (REPORTED). Q1-Q5 đã áp vào tài liệu v0.3.2/CVC; P1-P5 và execution checks còn mở. Chưa FROZEN, chưa baseline.

### 9.3 Đối chiếu AC sau REQUEST_CHANGES

| AC | Đã sửa ở đâu | Trạng thái trung thực |
| --- | --- | --- |
| AC1 thời gian | §3.3 cap JSON, SMOKE9.06 phút; DEV tách budget | Phép tính thiết kế; actual tokenizer/vision check còn mở |
| AC2 quyền dữ liệu | §2.2 notice file/hash, CSQA HOLD và hai bằng chứng | Policy/registry rõ hơn; chưa có corpus permission đủ |
| AC3 hash/leakage | §7 difficulty/notice/cluster/receipt trước run | Đã thiết kế; chưa thực hiện freeze |
| AC4 MDE | §5 primary McNemar khớp bảng, bootstrap audit và singleton units | Reviewer báo tái tạo bảng v0.3.1; audit JSON chỉ spot-check, không kiểm từng bản ghi |
| AC5 floor/decision | §6 point screen, eligibility, thứ tự/terminal statuses, gate operating table | ACCEPT_ERRATA / APPROVE_DESIGN theo reviewer; Q1 sửa thứ tự, Q2 làm rõ policy; execution còn mở |
| AC6 không API trả phí | Offline scorers, HYBRID chỉ thiết kế | Không phát sinh model API trong task |

Kiểm nhanh errata đã kết thúc với ACCEPT_ERRATA / APPROVE_DESIGN. Chủ dự án giao `TASK-003-CVC-001.md` đã cập nhật Q2-Q5 cho implementer/người B/C khi đủ nhân sự, quyền và môi trường. Ticket vẫn PLANNED; chưa giao tự động, chưa execution. Chỉ freeze khi C1-C11 và receipt đầy đủ. TASK-004 vẫn là harness tối thiểu.

## 10. Nguồn và phạm vi hỗ trợ

S1-S8 được mở ở vòng v0.2 ngày 2026-11-02; S3 được mở lại ngày 2026-11-03, S9-S10 bổ sung ngày 2026-11-03; diễn giải ngắn, không sao chép dataset. Phép tính, số lượng, trọng số, sàn và chính sách là thiết kế của tài liệu, không gán cho các nguồn này.

- **S1. NIST, Confidence intervals:** công thức Wilson và giới hạn của normal interval. https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm
- **S2. statsmodels, McNemar:** kiểm định exact dùng phân phối nhị thức và ý nghĩa bảng cặp. https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html
- **S3. CommonsenseQA, REPORTED MIT trong comment Jonathan Herzig ngày 2020-09-25; xem xung đột và HOLD §2.2:** https://github.com/jonathanherzig/commonsenseqa/issues/5
- **S4. TAU CommonsenseQA dataset card:** MIT, cấu trúc và split. https://huggingface.co/datasets/tau/commonsense_qa/blob/main/README.md
- **S5. AllenAI WinoGrande README:** phân biệt license code Apache-2.0 với dataset CC-BY. https://github.com/allenai/winogrande
- **S6. Noto Fonts LICENSE:** SIL OFL 1.1 cho font. https://github.com/notofonts/noto-fonts/blob/main/LICENSE
- **S7. SciPy bootstrap documentation:** resampling, CI và chỉ số paired; cách phân tầng/cluster trong spec là thiết kế bổ sung. https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html
- **S8. Microsoft PROCESS_MEMORY_COUNTERS_EX:** WorkingSetSize, PeakWorkingSetSize và PrivateUsage/commit. https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex

- **S9. ACCORD, phụ lục I.1 (trang PDF29):** ghi nhận thiếu license CSQA tính đến2024-10-14 và license ConceptNet. https://aclanthology.org/2025.naacl-long.193.pdf
- **S10. Hoeffding (1963), Probability Inequalities for Sums of Bounded Random Variables:** bound cho tổng biến độc lập bị chặn, DOI10.1080/01621459.1963.10500830; bản tác phẩm tại https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf

## 11. Tình trạng thực hiện trung thực

Đã nhận ACCEPT_ERRATA và APPROVE_DESIGN cho TASK-003 theo kiểm nhanh v0.3.1 của Claude C (REPORTED). v0.3.2 áp các sửa nhỏ Q1-Q5 và chuẩn bị CVC để giao; không mở vòng thiết kế mới, không chạy lại mô phỏng hay đổi số đã duyệt. Chưa có tokenizer thực, corpus freeze hay baseline.

Các phép toán chỉ chạy trong môi trường cloud của phiên ChatGPT Work, không gọi API inference có phí, không dùng Colab/GPU, không tải model. Không khẳng định môi trường cloud của sản phẩm có chi phí bằng0 với nhà cung cấp; usage/billing nội bộ UNKNOWN. Không có khoản mua dịch vụ được tạo. Do ticket cấm code triển khai ngoài pseudocode, gói chỉ có đặc tả, pseudocode, bảng/JSON numerical audit và notice; scratch arithmetic không là code harness giao triển khai.
