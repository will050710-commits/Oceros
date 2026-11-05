# TASK-003-CVC-001: Corpus, validator và calibration

TASK_ID: TASK-003-CVC-001, mã ticket tiếp nối cục bộ; chưa gán vào tracker ngoài.

MILESTONE: M0 → M2, chuẩn bị bằng chứng trước freeze/campaign.

OWNER: Chưa chỉ định implementer/người A; chủ dự án phân công. Người B giải độc lập, người C phân xử; danh tính và khả dụng chưa xác nhận.

REVIEWER: Claude C dự kiến kiểm nhanh errata và review execution evidence. Chủ dự án chuyển tài liệu; không tự liên hệ.

PRIORITY: P1. STATUS: PLANNED / READY_FOR_ASSIGNMENT, NOT_STARTED. Revision1.1 ngày2026-11-04, áp Q2-Q5 sau ACCEPT_ERRATA. Tạo ticket không đồng nghĩa đã giao hay chạy task.

OBJECTIVE: Tạo corpus, validator/scorer và calibration evidence theo spec v0.3.2; kiểm P1-P5, quyền, gold và feasibility. Chỉ đủ điều kiện freeze khi checklist hoàn tất. Chưa chạy baseline trong công việc thiết kế hiện tại.

CURRENT_BASELINE: Claude C đã ACCEPT_ERRATA v0.3.1 và APPROVE_DESIGN cho TASK-003 (REPORTED từ review chủ dự án cung cấp). Spec v0.3.2 sửa nhỏ Q1 và làm rõ Q2, không đổi ngưỡng hay bảng số. Dataset manifest=null, NOT_FROZEN; không có baseline hoặc số đo tokenizer/runtime. TASK-004 vẫn là harness tối thiểu, không ngầm mở rộng.

INPUT_FILES: BENCHMARK_SPEC_v0.md; ERRATA_TASK003_v0.3.1.md; TASK003_NUMERICAL_AUDIT_v031.json; GB0_INTERNAL_NOTICE_v1.txt; TASK-001/TASK-002 và model/tokenizer shortlist khi có; review vòng2 và kiểm nhanh ACCEPT_ERRATA do chủ dự án cung cấp; TASK003_v032_Q1-Q5_Closure.md. Giữ audit v03/RESPONSE v03 làm lịch sử.

RELEVANT_CONTEXT: General LLM+VLM độc lập với BingMath/DUOMATH. Dự kiến1057 item =916 text+141 ảnh. Stage A: SMOKE15+DEV30+LAPTOP92=137; Stage B: FULL920. Tổng labor143-311 giờ-người, Stage A19-41 giờ-người là ESTIMATE, cần pilot xác nhận và chưa bao gồm mọi calibration/runtime. API_BUDGET=$0; không giả định GPU/Colab hoặc permission đã đủ.

HYPOTHESIS: Corpus singleton có gold độc lập và cổng v0.3.2 vượt các kiểm feasibility/operating-target đã đăng ký. Đây là giả thuyết cần execution evidence.

ALLOWED_ACTIONS: Khi ticket được giao triển khai, biên soạn dữ liệu mới; hoàn thiện schema, validator và scorer fixtures; giải gold độc lập; tải và chạy weights/tokenizer/processor đúng shortlist TASK-002, revisions/hashes đã khóa, trong ngân sách disk/RAM/thời gian/host đã duyệt để đo token feasibility, DEV/SMOKE và pilot bridge; tái tạo statistical audit; chuẩn bị freeze manifest/receipt. Thực hiện Stage A trước; Stage B chỉ khi đủ nguồn lực và Stage A đạt.

FORBIDDEN_ACTIONS: Không dùng corpus Toán/raw_data cũ. Không tải/chạy model ngoài shortlist TASK-002 hoặc ngoài cấu hình, môi trường và ngân sách đã duyệt; không API trả phí. Không tự mở thêm host/Colab hoặc mua dịch vụ. Validator/scorer nằm trong phạm vi CVC khi được giao, không bị cấm bởi giới hạn thiết kế TASK-003. Không publish hoặc tự gửi dữ liệu/receipt cho người khác. Không dùng FULL để tune, đổi ngưỡng sau khi xem score, hay gọi mô phỏng là model results. Không freeze khi còn blocker; calibration không cấp quyền chạy baseline campaign trước freeze.

EXPECTED_OUTPUT:

1. Corpus Stage A tách split, assets sạch và provenance/permission đầy đủ. Stage B riêng biệt chỉ sau khi được giao và đủ nguồn lực. Có item/cluster/family/source ledger, difficulty quotas, VI/EN, option balance và exposure ledger.
2. Validator/scorer contract và implementation trong phạm vi ticket được giao: schema checks, leakage flags kèm manual audit, strict/parse/decision/citation scoring, manifest/hash, output cap handling và decision fixtures. Không thay JSON Schema validation bằng vài regex.
3. `token_feasibility` report gắn tokenizer/processor/config hashes, rendered payload và gold output từng item. Không truncation để làm pass. Các report ở đây là output dự kiến, chưa tồn tại.
4. `DEV_CALIBRATION` report về resource/time, biên SMOKE, pilot bridge và các lỗi/hạn chế. Đo laptop thật khi claim local; host FULL báo riêng.
5. Lời giải A/B độc lập, adjudication C và permission records. Freeze manifest, criteria/config hashes và receipt chỉ tạo khi mọi checklist đạt.
6. Handoff đúng17 trường, test evidence và unresolved blockers. Baseline campaign là bước sau freeze, không nằm trong việc soạn ticket này.

ACCEPTANCE_CRITERIA:

| ID | Kiểm bắt buộc | PASS / blocker |
| --- | --- | --- |
| C1 input/rights | Mọi item có provenance, notice hash, permission record và quyền asset/source rõ | Missing/HOLD source không vào freeze; CSQA vẫn HOLD |
| C2 counts/isolation | Đúng counts/splits/VI-EN/subtypes/difficulty, singleton tình huống; audit template, near-duplicate và ảnh | Overlap hoặc N bị thổi phồng chặn freeze; không chỉ tin cluster_id |
| C3 gold | B giải100% khi chưa thấy gold A; C phân xử; agreement≥95% tổng, ≥90% nhóm; unresolved=0 | Mọi lỗi sửa và có trail; batch/count theo P4; không thay bằng spot-check |
| C4 tokens (P2) | Đếm rendered input+schema+template và gold output từng item bằng tokenizer/processor thật | IF SMOKE≤8, OCR VI≤16 output; mọi cap đạt hoặc sửa trước campaign và tính lại budget |
| C5 runtime (P2) | TASK-001 clean boot, memory/disk; DEV/SMOKE đủ phase timers, decode/prefill/TTFT/vision | SMOKE≤600s; LAPTOP projection≤4590s và hard≤5400s; 15% reserve chỉ LAPTOP; báo SMOKE stress599s |
| C6 gates (E1-E4/Q1/Q5) | Mọi cổng số nguyên ở biên±1, cả chất lượng/cổng phụ/coverage/retry/batch; registry và danh sách chi tiết dưới | Đúng inequalities và ưu tiên; thiếu phase timer vẫn REJECT nếu quality≤39/80 hợp lệ; không REJECT quality từ incomplete; veto chỉ provisional |
| C7 operating characteristics (Q2/Q5) | Tái tạo exact LAPTOP/REJECT/veto, FULL gồm cổng phụ theo hợp đồng phân bổ lỗi dưới; báo p50/p90 riêng CORE/VLM, R/parse95% | Giữ target p=.85 với lower95% MC≥90%, ≥500000 dataset/profile; p50/p90 có bracket và bất định, không học design point từ candidate |
| C8 bridge (P3) | DEV cùng config trên2 host trước khi khóa; pin weights/quant/tokenizer/template/processor/scorer | Log mismatch; bridge LAPTOP80/92 canonical+pass vector100%, hoặc FULL shard laptop; DEV không chứng minh equivalence |
| C9 NI (P1) | Chọn trước plan bảo thủ hiện tại hoặc phương pháp cặp đã hiệu chuẩn | Thiếu bằng chứng NI: resource claim experimental, không PROMOTE nhờ p>.05 |
| C10 freeze | C1-C9 và C11 đạt; chốt criteria_hash, config shortlist, corpus/manifest hash, review signatures và timestamp UTC | Reviewer receipt độc lập; thiếu => FREEZE_UNATTESTED. Không lấy spec hash thay dataset hash |
| C11 null policies (Q4) | Chạy A/B/C/D cố định, copy, {}, always-answer, always-abstain qua scorer thật trên LAPTOP và FULL khi chuẩn bị freeze; khóa policy trước chấm | Mỗi policy không được qua tổ hợp quality cho PROMOTE provisional hoặc confirmed; k≤39/80 hợp lệ phải REJECT, còn lại KEEP theo matrix. FULL_ELIGIBLE hoặc qua một cổng đơn lẻ không tự làm C11 fail |

EVALUATION_METHOD:

- Stage A trước: xây137 item, pilot labor, token/rubric/resources; sửa tối đa một lượt batch gold theo spec. Thiếu người B/C hoặc permission thì ghi BLOCKED.
- Ngoài R, audit phải thêm profile task/ngôn ngữ không đồng đều, SO/HC failure modes và phụ thuộc tình huống phát hiện được. Mô phỏng độc lập không chứng minh independence của corpus.
- P1: nếu đề xuất variance/score NI, đăng ký công thức và cách xử lý nuisance trước chạy. Kiểm null boundary delta=-.03 tại q=.2/.3/.5, N800 và N đề xuất; thêm strata/cluster stress. Ít nhất200000 lượt/case; báo MCSE/CI, type-I error và power. Mục tiêu một phía alpha=.05: empirical≤.05+2MCSE và upper95%≤.055. Nếu không đạt, giữ bound bảo thủ hoặc đổi plan qua review. Chỉ claim đủ power khi đạt≥80% ở alternative đã đăng ký. Các xấp xỉ900/2060 tại q=.3 trong review chưa là bảo đảm hữu hạn mẫu. Margin4-5pp cần lý do sản phẩm và khóa trước data.
- P4: batch mục tiêu100, tail<50 gộp trước; split<100 dùng toàn split; khóa trước B review. Trigger gold≥max(2,floor(.02n)+1), ambiguity≥max(2,floor(.01n)+1), đồng thời giữ agreement thresholds. Một lỗi nghiêm trọng về quyền/leakage/asset chặn ngay; mọi lỗi khác vẫn phải sửa dù chưa chạm trigger.
- Kiểm code theo hành vi: malformed JSON, Unicode, unsupported citation, duplicate key, output cap/timeout, corrupted hash và permission missing phải có fixtures. Không dùng test chỉ lặp lại implementation.
- Người B/C độc lập và reviewer kiểm receipt trước mọi baseline. Không mở review thiết kế TASK-003 vòng3; thay đổi lớn cần ticket tiếp nối riêng.


### C6: registry ngưỡng và fixtures biên

Mọi ngưỡng nguyên `>=t` phải có t-1/t/t+1; ngưỡng `<=m` có m-1/m/m+1. Nếu ngoài miền hợp lệ (ví dụ count=-1), dùng fixture invalid-input, không coi là quality count hợp lệ. Registry phải đối chiếu toàn bộ spec, không chỉ danh sách ví dụ:

| Cổng | Counts bắt buộc |
| --- | --- |
| LAPTOP quality REJECT | 38/39/40 trên80 |
| LAPTOP FULL eligibility / point screen | 47/48/49 và56/57/58 trên80 |
| LAPTOP veto nhóm / HC nhánh | GR/GQ5/6/7 trên16; IF/BI/SO/HC3/4/5 trên12; HC0/1/2 trên6, thêm invalid count=-1 |
| LAPTOP image eligibility / provisional | 5/6/7 và8/9/10 trên12 |
| FULL tổng text / ngôn ngữ | 559/560/561 trên800; VI vàEN239/240/241 trên400 |
| FULL GR / IF / BI | 79/80/81 trên160; 89/90/91 trên120; 59/60/61 trên120 |
| FULL GQ / SO-strict / HC | 99/100/101 trên160; 95/96/97 trên120; 89/90/91 trên120 |
| FULL SO parse | 109/110/111 trên120; invalid parse9/10/11 nhất quán với mẫu số120 |
| FULL GQ unsupported / HC false assertion / HC refusal | 9/10/11 trên160; 9/10/11 trên60; 19/20/21 trên60 |
| FULL ảnh tổng / từng nhóm | 91/92/93 trên120; 23/24/25 trên40 cho cả VQA/OCR/CHART |
| Retry, coverage, gold batch và timeout count | attempt0/1, attempt2 phải bị từ chối; thiếu/đủ/thừa item; trigger P4±1 tại n=15/30/92/100 và tail; timeout floor(.05*N)±1 cho N áp dụng |

Kiểm từng gate độc lập bằng count fixture, rồi kiểm conjunction bằng vector **khả thi** cùng raw outputs/flags; không tạo strict-pass đồng thời invalid-parse/unsupported. Giữ các gate khác đạt khi kiểm gate có thể cô lập; nếu bị gate khác che do phụ thuộc logic, ghi rõ và vẫn test unit predicate. Với bound dư (text L≥.60) kiểm cả report và quan hệ với tổng, không dựng joint PASS bất khả thi. Metric liên tục (RAM, latency, throughput) kiểm ở dưới/đúng/trên ngưỡng theo precision đã đăng ký.

Q1 walkthrough bắt buộc: đủ80 outputs hợp lệ, k20 hoặc39 và thiếu phase timer => REJECT/QUALITY_BELOW_FLOOR; k40 và thiếu timer => KEEP/LOCAL_EVIDENCE_INCOMPLETE; incomplete hoặc scorer sai vẫn đi hàng lỗi trước. Thiếu timer đơn thuần không đồng nghĩa có sự cố CAUSE_UNRESOLVED.

### C7: design point và phân bổ lỗi phụ

Target p=.85 là quyết định chính sách cho confirmed; không gọi đây là “model chỉ cần70%”. R,p=.75 có point screen81.805% nhưng FULL text3.660%, text+ảnh1.371%. Khả năng shortlist≤3B đạt target vẫn UNKNOWN; human reference không thay số đo candidate. Sàn tổng vẫn có thể ràng buộc ở profile lệch: các sàn nhóm cộng516<560.

Định nghĩa p50/p90 là giá trị p nhỏ nhất có P(qua toàn cổng quality | profile,p)≥.50/.90; báo riêng CORE và VLM cho R và parse95%. Bắt đầu grid đã có, thu hẹp bracket giao điểm tới bước p≤.001; dùng≥500000 datasets tại mỗi điểm bổ sung và lưu seed/counts/CI. Nếu MC không phân biệt được hai phía thì báo bracket rộng hơn hoặc tăng số lượt đã đăng ký; không nội suy rồi gọi là nghiệm exact. Ghi cả bracket do grid và bất định MC. Báo xác suất LAPTOP tại cùng p để chủ dự án thấy khoảng cách provisional/confirmed. Việc báo p50/p90 không đổi target hay ngưỡng đã duyệt.

**Hợp đồng mô phỏng R:** item độc lập; mỗi item có một category duy nhất. Strict-pass, lỗi phụ đang xét, và fail khác có xác suất [p,e,1-p-e]. Lỗi phụ là xác suất **vô điều kiện** trên mẫu số dưới, không phải xác suất có điều kiện trong số item sai; khi strict-fail đã sinh trước thì phải dùng e/(1-p). Với SO, e=1-parse. Phải có p+e≤1; profile không hợp lệ phải bị từ chối.

| Stratum mỗi ngôn ngữ FULL | N | p/e trong R | Flag và mẫu số toàn bộ |
| --- | --- | --- | --- |
| GQ answerable / thiếu dữ kiện | 60 / 20 | p / .02 ở cả hai subtype | unsupported trên toàn160 GQ, không chỉ40 câu thiếu dữ kiện |
| SO extraction / tool-call | 30 / 30 | p / .02 invalid parse; e=.05 trong sensitivity parse95% | strict-pass luôn parse-valid; strict-fail khác vẫn parse-valid; parse trên120 SO |
| HC answerable | 30 | p / .03 unnecessary refusal | Chỉ nhánh answerable; toàn60 câu |
| HC phải abstain / phải refuse theo policy giả lập | 20 / 10 | p / .03 false assertion ở cả hai subtype | Chỉ nhánh không nên trả lời; toàn60 câu |

GR80/IF60/BI60 mỗi ngôn ngữ sinh Bernoulli(p). Ảnh20 item/ngôn ngữ/nhóm sinh Bernoulli(p), độc lập text. Trong R, sai không mang flag phụ thuộc category “fail khác”, không được âm thầm chuyển sang auxiliary error. Với dữ liệu thực, scorer phải suy flag từ output/evidence đúng §4.1-4.2, tuyệt đối không phân bổ lỗi để ép giống R.

Audit v0.3.1 gộp các subtype có cùng p/e (GQ80, SO60, HC30+30 mỗi ngôn ngữ); tách subtype như bảng không đổi luật phân phối, nhưng có thể đổi chuỗi số ngẫu nhiên. Implementer phải ghi thứ tự task/language/subtype/item, PRNG+version+seed, event labels và mapping flags; lưu một fixture item-level cố định cùng output của scorer và counts kỳ vọng để hai implementation so byte-for-byte. Mô phỏng độc lập khác seed/draw order so xác suất trong sai số MC, không bắt output giống byte. Lệch0.1-0.2 pp tự nó chưa chứng minh khác cách phân bổ lỗi.

### C11: null policy không được PROMOTE

Khóa nội dung policy, serializer và version trước khi xem gold; không đọc gold hay dùng model ứng viên để dựng policy. Bốn policy nhãn A/B/C/D là bốn lần kiểm riêng; copy phải khóa trường/vị trí copy; {} xuất object rỗng; always-answer luôn chọn answer với payload cố định/được quy định trước; always-abstain luôn chọn abstain. Định nghĩa output cho mọi task, không bỏ câu khó hay chỉ chấm MC. Đi qua renderer/parser/scorer thật và giữ mọi item, parse errors tính theo spec.

Người giữ gold chạy các policy offline trên từng split dự kiến freeze; DEV/SMOKE chỉ chẩn đoán. LAPTOP/FULL cần report theo task/ngôn ngữ, flags, counts và gate vector. Mỗi policy phải REJECT nếu k≤39/80 hợp lệ, hoặc KEEP khi không đạt tổ hợp quality để PROMOTE. Không được dùng việc thiếu resource, license hay bridge để che một null policy đã qua quality conjunction. Một cổng parse/nhóm riêng có thể PASS; FULL_ELIGIBLE không đồng nghĩa PROMOTE và không bị cấm. Chưa có FULL thì phần confirmed ghi NOT_RUN, không ký C11 cho FULL.

Fixture “các nhóm khác hoàn hảo, HC một nhánh0/6” chỉ kiểm decision/veto có chủ đích, không phải kết quả null policy thực trên corpus. Nếu null policy thật đạt tổ hợp provisional hoặc confirmed: chặn freeze, audit leakage/scorer/nhãn/corpus; sửa qua quy trình version, không hạ tiêu chí để che lỗi. C10 chỉ đóng sau khi C11 đạt cho tập cần freeze.

RESOURCE_BUDGET: API trả phí$0. Chưa cấp ngân sách host FULL hay giờ-người; chủ dự án phân công trước execution. DEV29.18/18.14/12.42 phút mỗi lượt theo giả định v0.3; bridge/resource repetitions có budget riêng. Không tự mua dịch vụ; chỉ tải/chạy trọng số và tokenizer/processor trong shortlist, môi trường và ngân sách được duyệt nêu ở ALLOWED_ACTIONS.

TIME_OR_ITERATION_LIMIT: Stage A19-41 giờ-người là ESTIMATE; cập nhật bằng pilot trước Stage B. Mỗi batch gold tối đa một lượt sửa; retry run tối đa1 theo spec và giữ mọi log. Vượt nguồn lực hoặc cần sửa thiết kế lớn thì BLOCKED/ticket mới.

DEPENDENCIES: Chủ dự án giao implementer/B/C và quyền môi trường; TASK-001 hardware; TASK-002 shortlist/config/tokenizer; ACCEPT_ERRATA / APPROVE_DESIGN của Claude C đã nhận; permission và người giữ gold. TASK-004 không tự nhận thêm corpus/validator scope.

DELIVERABLE_LOCATION: Artifact có version/hash riêng trong workspace dự án được giao; không sửa BingMath/DUOMATH. Nơi lưu corpus kín và người giữ FULL phải chốt trước biên soạn FULL.

HANDOFF_INSTRUCTIONS: Đúng17 trường TASK_ID, OWNER, STATUS, BASELINE_REVISION, FILES_READ, FILES_CHANGED, WORK_COMPLETED, EVIDENCE, TESTS_EXECUTED, TEST_RESULTS, BENCHMARK_RESULTS, COST_OR_RESOURCE_USAGE, KNOWN_LIMITATIONS, RISKS, RECOMMENDATION, NEXT_ACTION, UNVERIFIED_CLAIMS. Ghi rõ NOT_RUN/UNKNOWN và blockers; tách actual model results khỏi phép tính. Chỉ ghi FROZEN khi có receipt đủ.
