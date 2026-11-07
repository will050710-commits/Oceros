# TASK-004-WIN-MOCK — xác minh launcher/client/mock trên Windows

Ngày lập: 07/11/2026 (Asia/Bangkok). Đây là ticket trong repo; chưa tạo issue ở tracker ngoài, chưa giao cho người thực thi.

| Trường | Giá trị |
| --- | --- |
| STATUS | READY_FOR_ASSIGNMENT / NOT_RUN |
| OWNER | TBD — người có máy Windows được chủ dự án giao |
| Implementation cần xác minh | `47aaeee91739c2f09ea30538e40c66e853653543` |
| Mốc hồ sơ khi lập ticket | `c45347100e763fbbb1efb537b457c73f115dcaf0` — chỉ bổ sung tài liệu so với implementation được chấp nhận |
| Môi trường đích | Windows 11 x64; CPython 3.14 là đích cần xác minh, phiên bản khác phải báo thành ô ma trận riêng |
| Dependency | stdlib + `psutil==7.2.2`; tests dùng unittest |
| Ngân sách/quyền | Chỉ code/test và HTTP mock loopback trên máy được giao; không API model trả phí, model weights, training, Colab/GPU hoặc host mới |

## Mục tiêu và ranh giới

Xác minh các đường cài đặt, CLI, HTTP, hủy, dọn tiến trình, đo tài nguyên và ghi artifact của **mock** trên Windows thật. Kết quả Linux đã được chấp nhận không thay chứng cứ Windows. Ticket này không triển khai bộ ticket/ledger/costlog theo phiếu 24/10, không mở CVC/corpus/scorer và không bật adapter model thật.

Đầu vào cần có trước khi chạy: checkout đầy đủ (gồm `task004/evidence/` cho hai test compatibility), quyền dùng máy đích, Python đích, thư mục output có quyền ghi và người thực thi xác nhận đây là máy cần đo. Không dùng ZIP triển khai cũ `2cb9168`. Ghi full Git SHA và trạng thái working tree; không reset thay đổi của người dùng để khớp một revision. Nếu source khác 47aaeee, ghi diff và không gọi đó là xác minh nguyên bản 47aaeee.

Nếu cần sửa để tương thích Windows, thực hiện thành commit riêng nối tiếp baseline, giữ hồi quy Linux và trình reviewer xác nhận đúng commit mới. Verdict Linux tại 47aaeee không tự áp cho code đã sửa.

## Chuẩn bị trên máy đích

Các lệnh sau là hướng dẫn dự kiến, **chưa được chạy trên Windows**. Mở PowerShell tại thư mục gốc checkout Oceros; không dùng `task004/setup.sh` có đường dẫn cloud. Không đổi execution policy chỉ để activate venv; gọi Python trong venv trực tiếp.

```powershell
git rev-parse HEAD
git status --short
py -3.14 --version
py -3.14 -m venv task004/.venv
$taskPython = ".\task004\.venv\Scripts\python.exe"
& $taskPython -m pip install --only-binary=:all: -r task004/requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& $taskPython -c "import platform, psutil; print(platform.python_version()); print(psutil.__version__)"
& $taskPython -m task004.cli validate-config
& $taskPython -m task004.cli preflight --output-dir task004/runs/windows-intake
& $taskPython -m task004.cli dry-run --output-dir task004/runs/windows-intake/smoke
```

Ghi exit code ngay sau từng lệnh native, trước khi chạy lệnh tiếp theo. Nếu Python 3.14 hoặc wheel psutil 7.2.2 không có/không cài được, lưu lỗi đã bỏ thông tin cá nhân và đánh dấu BLOCKED cho ô môi trường đó; không âm thầm dùng Python khác hoặc build package không kiểm chứng. Giữ TLS/proxy và kiểm tra package bình thường. Không cần token ứng dụng.

## Snapshot phần cứng và RAM sạch

Đo trên Windows đích; không lấy số RAM cloud hay snapshot cũ làm số hiện tại. Người thực thi đóng các ứng dụng không cần thiết bằng thao tác thông thường, chờ máy ổn định và ghi điều kiện đo; không tự dừng dịch vụ/tiến trình không thuộc harness. Đọc ít nhất ba mẫu RAM khả dụng tại thời điểm trước test, ghi thời điểm UTC và khoảng cách mẫu. Số này chỉ mô tả điều kiện máy, không chứng minh đủ RAM cho model.

Ví dụ lấy một snapshot chỉ đọc, không có username/hostname/serial/đường dẫn cá nhân:

```powershell
New-Item -ItemType Directory -Force task004/runs/windows-intake | Out-Null
@'
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, platform, shutil, psutil
from task004.preflight import windows_system_commit
observed = datetime.now(timezone.utc)
data = {
    "observed_at_utc": observed.isoformat(),
    "measurement_scope": "CURRENT_WINDOWS_HOST",
    "os": platform.system(), "os_version": platform.version(),
    "architecture": platform.machine(), "python_version": platform.python_version(),
    "psutil_version": psutil.__version__,
    "ram_total_bytes": psutil.virtual_memory().total,
    "ram_available_bytes": psutil.virtual_memory().available,
    "output_volume_free_bytes": shutil.disk_usage(Path.cwd()).free,
    "system_commit": windows_system_commit()
}
path = Path("task004/runs/windows-intake") / ("hardware-" + observed.strftime("%Y%m%dT%H%M%S%fZ") + ".json")
raw = (json.dumps(data, indent=2) + "\n").encode("utf-8")
with path.open("xb") as output:
    output.write(raw)
print(path.as_posix())
print(hashlib.sha256(raw).hexdigest())
'@ | & $taskPython -
```

Đặt mỗi mẫu vào file mới, không ghi đè mẫu cũ khi lặp. Lưu hash và đường dẫn tương đối của snapshot trong báo cáo Windows, liên kết với run IDs. Manifest hiện tại có `hardware_reference=null`; không sửa tay manifest hay evidence đã sinh để lấp trường này. Nếu cần thay hợp đồng manifest, mở thay đổi có schema/tests riêng. Ngưỡng mock 64 MiB/10 MiB không phải bảng preflight theo model.

## Khảo sát suite hiện có và báo cáo skip

```powershell
$env:PYTHONWARNINGS = "error::ResourceWarning"
& $taskPython -W error::ResourceWarning -m unittest discover -s task004/tests -v
$suiteExit = $LASTEXITCODE
```

Lưu stdout/stderr, exit code và số test thực tế; bỏ prefix đường dẫn cá nhân trước khi đưa log lên repo. `ResourceWarning` trong finalizer vẫn có thể trả rc=0: kiểm cả `Exception ignored`, `ResourceWarning`, `Traceback`. Test giữ output của CLI con phải kiểm output đó, không chỉ log outer suite. Không dump process environment hoặc credential.

Đây là bước **khảo sát**, không tự tạo verdict Windows. Suite hiện có chứa test POSIX/Linux (process groups, SIGKILL/SIGHUP, signal phase, Linux backlog và child environ), có thể skip trên Windows. Symlink và integer-digit-limit có skip theo khả năng interpreter. Ghi từng skip cùng lý do; không gọi skip là PASS hoặc bỏ assertion để đạt số đẹp. Test không có marker skip nhưng fail trên Windows phải được chẩn đoán như defect/setup gap.

**Không dùng `validate_hardening.py` nguyên trạng làm cổng acceptance Windows.** Runner hiện yêu cầu `skipped == 0` và chạy hồi quy baseline POSIX; do đó không thể hứa toàn runner PASS trên Windows. Nếu bổ sung runner/profile Windows trong ticket, profile phải liệt kê rõ test bắt buộc Windows, skip được giải thích và kết quả thiếu; giữ profile Linux hiện có. Không đổi quy tắc chung thành “bỏ qua mọi skip”. Số 106 là số suite Linux tại revision được chấp nhận, không phải chỉ tiêu số test Windows.

## Kiểm thử bắt buộc trên Windows thật

| Nhóm | Điều phải chạy và chứng cứ cần có |
| --- | --- |
| Cài đặt/CLI | Xác minh đúng Python/wheel; config hợp lệ và cấu hình sai exit 2; preflight fail exit 3. Sáu scenario mock cho status/exit code đúng, đầy đủ manifest/JSONL; không raw prompt/response/env/secrets. |
| HTTP/deadline | Success, JSON lỗi, HTTP lỗi, disconnect, body stall/trickle, timeout và hủy. Đo monotonic; `socket.shutdown()` từ thread khác có đánh thức recv thật không; worker/PID còn lại phải được kiểm. Với connect bị chặn, tách giới hạn worker daemon sống tới socket timeout khỏi cleanup leak. |
| Console/cancellation | Console thật và subprocess group do test sở hữu: Ctrl+C, Ctrl+Break/SIGBREAK nếu hỗ trợ, tín hiệu lặp trong request/cleanup/ghi file. Xác minh handler không deadlock, không traceback, status theo chính sách đã chọn. `Popen.terminate()` trên Windows là kết thúc cưỡng bức, không thay thế phép thử Ctrl+C/SIGBREAK. |
| Cha chết/watchdog | Kết thúc cưỡng bức đúng CLI do test tạo; theo dõi mock bằng PID và identity, không tìm bằng substring của dòng lệnh shell. Mock/scratch của lượt đó phải được dọn trong ngưỡng watchdog test đã khai báo trước. Ghi latency thật; không suy từ lần đo Linux. |
| Cleanup tree | Test cây tiến trình do test sở hữu, cha thoát trước con, con còn sống và tiến trình không liên quan vẫn sống. Windows chưa có Job Object; nếu fallback không đáp ứng tình huống bắt buộc, ghi FAIL/BLOCKED và sửa trong commit riêng hoặc xin quyết định scope cụ thể. Không đánh dấu toàn bộ Windows VERIFIED chỉ vì fixed mock hiện không sinh con. |
| Ghi artifact | Hai open, hai fsync, rename: chèn OSError/KeyboardInterrupt, kiểm staging được dọn; destination tồn tại không bị ghi đè. Kiểm `os.rename` thư mục trên filesystem Windows thực, lock file/open handle và quyền ghi; không suy power-loss durability vì chưa directory fsync. |
| Tài nguyên | `GetPerformanceInfo` system commit và psutil private bytes có giá trị hợp lệ, nguồn rõ; đo RSS tổng đồng thời của cây. Thiếu phép đo ghi null+lý do, không thay bằng VMS/RSS. Phân biệt system commit và private bytes của process, không cộng hai đại lượng. |
| Environment | `SYSTEMROOT`/TEMP/TMP/locale cần thiết hoạt động với allowlist; token giả của harness không được truyền vào mock. Chỉ kiểm tên/presence, không log biến môi trường thật. |
| Regression/labels | PASS yêu cầu resource evidence; reason/schema không drift. Mọi artifact vẫn SYNTHETIC/NOT_RUN; runtime thật vẫn bị khóa. Đối chiếu hash nguồn và artifact với revision thực thi. |

Các test signal/process phải tự dọn mọi tiến trình do chúng tạo ngay cả khi assertion fail. Không kill theo tên chung hoặc dừng tiến trình không thuộc test. Một PID/cổng mở không thay cho functional request.

## Acceptance và sản phẩm bàn giao

Chỉ đề nghị ACCEPT cho **Windows mock trên đúng OS/interpreter/build đã đo** sau khi có đủ:

1. Ma trận môi trường thực, full commit/diff, dependency versions và snapshot phần cứng/hash; bản gốc log giữ riêng nếu có đường dẫn cá nhân, bản chia sẻ nêu rõ cách chuẩn hóa.
2. Bộ test bắt buộc Windows ở trên thực thi, không missing/skip các đường Windows cần xác minh; ba lượt liên tiếp để kiểm độ ổn định signal/cleanup, báo riêng passed/failed/skipped/unrun. Không yêu cầu POSIX-only test chạy giả trên Windows.
3. Dry-run thật tạo manifest/JSONL qua validator/hash, kiểm không còn tiến trình/scratch thuộc lượt; cleanup failure không được che bằng CANCELLED/PASS. Không có marker cảnh báo bất ngờ trong output đã thu thập.
4. Nếu sửa code: test hồi quy cho lỗi đã phát hiện, kiểm Linux liên quan vẫn qua, evidence sinh tự động và checksum mới; không sửa evidence cũ hoặc source đã chấp nhận để giả giữ hash.
5. Handoff 17 trường ghi phạm vi Windows cụ thể, findings còn mở, mọi giới hạn và verdict reviewer. Không tuyên bố Windows VERIFIED nếu còn đường bắt buộc chưa chạy hoặc chỉ có mô phỏng trên Linux.

Output dự kiến: `task004/evidence/windows-<run-id>/` với validation summary, log đã chuẩn hóa, hardware snapshots và hashes, dry-run artifacts, test/skip matrix và handoff. Dùng đường dẫn tương đối; không ghi hostname/username/secrets. Việc lập ticket này không tạo các artifact đó và không chứng minh bất kỳ test Windows nào đã chạy.

## Cổng trước bước model thật

Sau Windows mock, đo lại RAM khả dụng sạch và đĩa trên máy đích, lưu nguồn hardware JSON/hash; chủ dự án xác nhận shortlist/model/quant/context/image budget và cho phép bước tiếp. Khi đó mới mở ticket riêng cho **bảng preflight theo model** và **adapter llama.cpp**. Các số RAM được nhắc trong prompt khác chỉ là đầu vào cần xác minh và ánh xạ model, không tự chép thành ngưỡng đã duyệt trong ticket này.

Ticket tiếp theo phải chốt revision/binary/cờ runtime bằng nguồn thực, cách dùng hardware_reference và tiêu chí từ chối mỗi model. Model downloads/runs, API trả phí, training, corpus/CVC và benchmark vẫn ngoài scope hiện tại; ACCEPT Windows mock không tự mở những quyền đó.
