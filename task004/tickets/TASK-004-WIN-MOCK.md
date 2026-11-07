# TASK-004-WIN-MOCK — xác minh launcher/client/mock trên Windows

Ngày lập/cập nhật: 07/11/2026 (Asia/Bangkok). Ticket trong repo; đã nhận intake do người dùng chuyển tiếp, chưa tạo issue ở tracker ngoài.

| Trường | Giá trị |
| --- | --- |
| STATUS | SURVEY_FAILED_REPORTED / NOT_VERIFIED; BLOCKED_ON_REPORTED_DEFECT_AND_WINDOWS_TEST_GAPS |
| OWNER | Lượt intake do người dùng chuyển tiếp; owner bản vá/kiểm tiếp chưa phân công, do chủ dự án chỉ định |
| Implementation cần xác minh | `47aaeee91739c2f09ea30538e40c66e853653543` |
| Mốc hồ sơ khi lập ticket | `c45347100e763fbbb1efb537b457c73f115dcaf0` — chỉ bổ sung tài liệu so với implementation được chấp nhận |
| Môi trường đích | Windows 11 x64; CPython 3.14 là đích cần xác minh, phiên bản khác phải báo thành ô ma trận riêng |
| Dependency | stdlib + `psutil==7.2.2`; tests dùng unittest |
| Ngân sách/quyền | Chỉ code/test và HTTP mock loopback trên máy được giao; không API model trả phí, model weights, training, Colab/GPU hoặc host mới |

## Mục tiêu và ranh giới

Xác minh các đường cài đặt, CLI, HTTP, hủy, dọn tiến trình, đo tài nguyên và ghi artifact của **mock** trên Windows thật. Kết quả Linux đã được chấp nhận không thay chứng cứ Windows. Ticket này không triển khai bộ ticket/ledger/costlog theo phiếu 24/10, không mở CVC/corpus/scorer và không bật adapter model thật.

Đầu vào cần có trước khi chạy: bản clone hoặc ZIP giải nén đầy đủ (gồm `task004/evidence/` cho hai test compatibility), quyền dùng máy đích, Python đích, thư mục output có quyền ghi và người thực thi xác nhận đây là máy cần đo. Không dùng ZIP triển khai cũ `2cb9168`. Với Git, ghi full SHA và trạng thái working tree; với ZIP, ghi commit trong comment, SHA-256 archive và kết quả kiểm tệp bên dưới. Không reset thay đổi của người dùng để khớp revision. Nếu source khác 47aaeee, ghi diff và không gọi đó là xác minh nguyên bản 47aaeee.

[ACK packet 879dcfa](../reviews/2026-11-07/ORCHESTRATOR_ACK.md) ghi trạng thái READY_FOR_ASSIGNMENT / NOT_RUN tại thời điểm đó. Sau ACK đã nhận [Windows intake](../evidence/windows-intake-20261107/README.md): bốn artifact khớp hash/validator; smoke PASS/SYNTHETIC được báo, suite 106 test = 92 pass + 1 failure + 13 skip. Log survey và script/output chẩn đoán chưa nhận; Windows vẫn NOT_VERIFIED. Finding worker còn sống sau cancel được theo dõi ở [TASK-004-WIN-CLIENT-CANCEL](TASK-004-WIN-CLIENT-CANCEL.md), chưa triển khai bản vá.

Nếu cần sửa để tương thích Windows, thực hiện thành commit riêng nối tiếp baseline, giữ hồi quy Linux và trình reviewer xác nhận đúng commit mới. Verdict Linux tại 47aaeee không tự áp cho code đã sửa.

## Chuẩn bị trên máy đích

Các bước intake/smoke/survey dưới đây đã được người dùng báo chạy trên Windows; implementer chỉ kiểm artifact ngoại tuyến, chưa chạy lại Windows. Giữ hướng dẫn để tái lập, không yêu cầu người đã chạy làm lại từ đầu khi còn giữ log. Dùng PowerShell; không dùng `task004/setup.sh` có đường dẫn cloud. Không đổi execution policy chỉ để activate venv; gọi Python trong venv trực tiếp. Dừng ở lệnh báo lỗi và giữ output để chẩn đoán, không tiếp tục bằng interpreter/dependency khác.

### 1. Kiểm tra Python

```powershell
py -3.14 --version
```

Nếu chưa có Python 3.14, cài bản CPython Windows x64 từ [python.org](https://www.python.org/downloads/windows/), mở lại PowerShell rồi kiểm tra lại. Python phiên bản khác là ô môi trường khác, không thay thế phép kiểm 3.14.

### 2. Chọn một cách lấy và nhận diện mã nguồn

**Nếu dùng bản clone có Git:** mở PowerShell ở thư mục chứa `task004` và `.git`, chạy hai lệnh này rồi sang bước 3. Ghi nhận thay đổi local, không dùng reset để xóa chúng.

```powershell
git rev-parse HEAD
git status --short
```

**Nếu không có Git hoặc dùng ZIP:**

1. Tải [ZIP GitHub ghim commit 47aaeee](https://github.com/will050710-commits/Oceros/archive/47aaeee91739c2f09ea30538e40c66e853653543.zip). Giữ nguyên tệp ZIP để ghi provenance; tài liệu hướng dẫn mới đọc ở main, mã thực thi lấy từ snapshot này.
2. Dùng **Extract All / Giải nén tất cả** vào thư mục mới. Mở thư mục con `Oceros-47aaeee...` chứa `task004`; mở PowerShell tại đó. Không chép đè lên bản cũ.
3. Chạy nguyên khối dưới đây; khi được hỏi, dán đường dẫn đầy đủ tới ZIP vừa tải, không kèm dấu ngoặc kép. Khối này chỉ đọc ZIP và các tệp đã giải nén, rồi ghi biên nhận mới trong `task004/runs/windows-intake/`.

```powershell
$taskZip = Read-Host "Duong dan day du toi ZIP vua tai (khong kem dau ngoac kep)"
@'
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, sys

expected_commit = "47aaeee91739c2f09ea30538e40c66e853653543"
expected_sums_sha256 = "a4bf0983852c26a46e6a047b2829dfc6a60112fc88437c753d518879b50acef8"
archive = Path(sys.argv[1])
with ZipFile(archive) as bundle:
    commit = bundle.comment.decode("ascii").strip()
    if commit != expected_commit:
        raise SystemExit("STOP: ZIP comment missing or wrong commit; keep this ZIP for diagnosis")
    sums_members = [n for n in bundle.namelist() if n.endswith("/task004/SHA256SUMS")]
    if len(sums_members) != 1:
        raise SystemExit("STOP: unexpected ZIP layout")
    sums_name = sums_members[0]
    prefix = sums_name[:-len("task004/SHA256SUMS")]
    raw_sums = bundle.read(sums_name)
    if hashlib.sha256(raw_sums).hexdigest() != expected_sums_sha256:
        raise SystemExit("STOP: SHA256SUMS differs from the accepted snapshot")
    if Path("task004/SHA256SUMS").read_bytes() != raw_sums:
        raise SystemExit("STOP: wrong extracted folder or changed SHA256SUMS")
    lines = raw_sums.decode("utf-8").splitlines()
    for line in lines:
        expected, relative = line.split("  ", 1)
        for raw in (bundle.read(prefix + relative), Path(relative).read_bytes()):
            if hashlib.sha256(raw).hexdigest() != expected:
                raise SystemExit("STOP: checksum mismatch: " + relative)

observed = datetime.now(timezone.utc)
receipt = {
    "observed_at_utc": observed.isoformat(),
    "source_kind": "GITHUB_ZIP", "archive_commit": commit,
    "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "checksum_file_sha256": expected_sums_sha256,
    "verified_entries": len(lines), "verification_scope": "SHA256SUMS_ENTRIES_ONLY"
}
out = Path("task004/runs/windows-intake")
out.mkdir(parents=True, exist_ok=True)
path = out / ("source-" + observed.strftime("%Y%m%dT%H%M%S%fZ") + ".json")
with path.open("x", encoding="utf-8") as target:
    target.write(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt, indent=2))
print("Saved: " + path.as_posix())
'@ | py -3.14 - $taskZip
if ($LASTEXITCODE -ne 0) { throw "Source verification failed; stop here" }
```

Kết quả đúng có `archive_commit=47aaeee...` và `verified_entries=171`. Comment ZIP chỉ là metadata; SHA-256 ZIP định danh archive tải về, không tự chứng minh nguồn tin cậy. Khối trên còn so SHA256SUMS với hash đã ghim từ commit được chấp nhận và kiểm các tệp được liệt kê trong cả ZIP lẫn thư mục giải nén. README ở gốc và tệp ngoài danh sách không thuộc phép kiểm này. Nếu GitHub trả archive không có comment hoặc kiểm thất bại, giữ tệp và output để đối chiếu; không sửa comment/checksum hoặc bỏ kiểm. Không cần Git cho đường ZIP.

### 3. Tạo môi trường và kiểm cấu hình

Từ cùng thư mục chứa `task004`:

```powershell
py -3.14 -m venv task004/.venv
if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed" }
$taskPython = ".\task004\.venv\Scripts\python.exe"
& $taskPython -m pip install --only-binary=:all: -r task004/requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& $taskPython -c "import platform, psutil; print(platform.python_version()); print(psutil.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Dependency import failed" }
& $taskPython -m task004.cli validate-config
if ($LASTEXITCODE -ne 0) { throw "Config validation failed" }
```

Ghi exit code ngay sau từng lệnh native, trước khi chạy lệnh tiếp theo. Nếu Python 3.14 hoặc wheel psutil 7.2.2 không có/không cài được, lưu lỗi đã bỏ thông tin cá nhân và đánh dấu BLOCKED cho ô môi trường đó; không âm thầm dùng Python khác hoặc build package không kiểm chứng. Giữ TLS/proxy và kiểm tra package bình thường. Không cần token ứng dụng.

## Snapshot phần cứng và RAM sạch

**Snapshot dưới đây chỉ ghi RAM/đĩa/commit phục vụ mock, chưa tương đương hồ sơ TASK-001.** Đã nhận [ba mẫu từ lượt intake](../evidence/windows-intake-20261107/hardware-20261107T103556669197Z.json), hash khớp báo cáo. Chưa có điều kiện clean boot/Best performance hoặc CPU/GFLOPS/băng thông/power plan đi kèm. Thông tin i7-8665U/94 GFLOPS hiện là USER_REPORTED; chưa có JSON TASK-001/probe gốc để xác minh phương pháp hoặc tái lập. Không điền lại 94 GFLOPS vào JSON mới như một phép đo.

Để tái lập hồ sơ ban đầu khi có probe: giữ JSON cũ và mã probe nguyên byte, ghi SHA-256 bằng `Get-FileHash -Algorithm SHA256 <file>`, ghi phiên bản/tham số probe, đơn vị và điều kiện đo. Sau khi lưu công việc, chủ máy khởi động lại Windows và đặt **Settings → System → Power & battery → Power mode → Best performance** nếu máy hỗ trợ; ghi trạng thái thực tế nếu tùy chọn không có. Ghi nguồn điện AC/pin, thời gian từ lúc boot và thời gian chờ ổn định. Lưu thêm kết quả `powercfg /getactivescheme`; active power plan và Power mode của Windows có thể khác nhau, không suy cái này từ cái kia. CPU có thể đọc bằng `Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors`. GFLOPS và băng thông phải dùng đúng probe/phương pháp gốc, chưa có probe thì giữ NOT_MEASURED.

Đo trên Windows đích; không lấy số RAM cloud hay snapshot cũ làm số hiện tại. Người thực thi đóng các ứng dụng không cần thiết bằng thao tác thông thường, chờ máy ổn định và ghi điều kiện đo; không tự dừng dịch vụ/tiến trình không thuộc harness. Lấy ba mẫu RAM khả dụng cách nhau 5 giây tại thời điểm trước test bằng khối dưới đây; ghi thời điểm UTC và điều kiện đo. Có thể lấy snapshot giới hạn này để khảo sát mock trong khi chờ nguồn TASK-001; nguồn phần cứng đầy đủ cho bước model vẫn chưa có. Nếu mở lại PowerShell sau reboot, đặt lại `$taskPython = ".\task004\.venv\Scripts\python.exe"` từ thư mục chứa `task004`.

Ví dụ lấy một snapshot chỉ đọc, không có username/hostname/serial/đường dẫn cá nhân:

```powershell
New-Item -ItemType Directory -Force task004/runs/windows-intake | Out-Null
@'
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, platform, shutil, time, psutil
from task004.preflight import windows_system_commit
if platform.system() != "Windows":
    raise SystemExit("This snapshot must be collected on the target Windows host")
observed = datetime.now(timezone.utc)
samples = []
for index in range(3):
    if index:
        time.sleep(5)
    memory = psutil.virtual_memory()
    samples.append({
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "ram_total_bytes": memory.total,
        "ram_available_bytes": memory.available,
        "output_volume_free_bytes": shutil.disk_usage(Path.cwd()).free,
        "system_commit": windows_system_commit()
    })
data = {
    "observed_at_utc": observed.isoformat(),
    "measurement_scope": "WINDOWS_MOCK_RESOURCE_SNAPSHOT_ONLY",
    "task001_equivalent": False,
    "os": platform.system(), "os_version": platform.version(),
    "architecture": platform.machine(), "python_version": platform.python_version(),
    "psutil_version": psutil.__version__,
    "sample_interval_s": 5,
    "samples": samples
}
path = Path("task004/runs/windows-intake") / ("hardware-" + observed.strftime("%Y%m%dT%H%M%S%fZ") + ".json")
raw = (json.dumps(data, indent=2) + "\n").encode("utf-8")
with path.open("xb") as output:
    output.write(raw)
print(path.as_posix())
print(hashlib.sha256(raw).hexdigest())
'@ | & $taskPython -
if ($LASTEXITCODE -ne 0) { throw "Hardware snapshot failed" }
```

Mỗi lần chạy tạo một file mới chứa ba mẫu, không ghi đè lượt cũ. Lưu hash và đường dẫn tương đối của snapshot trong báo cáo Windows, liên kết với run IDs. Manifest hiện tại có `hardware_reference=null`; không sửa tay manifest hay evidence đã sinh để lấp trường này. Nếu cần thay hợp đồng manifest, mở thay đổi có schema/tests riêng. Ngưỡng mock 64 MiB/10 MiB không phải bảng preflight theo model.

## Chạy thử mock sau khi lấy snapshot

```powershell
& $taskPython -m task004.cli preflight --output-dir task004/runs/windows-intake
if ($LASTEXITCODE -ne 0) { throw "Preflight failed; keep output and stop here" }
& $taskPython -m task004.cli dry-run --output-dir task004/runs/windows-intake/smoke
$smokeExit = $LASTEXITCODE
Write-Output "dry_run_exit=$smokeExit"
```

Gửi output và thư mục run được tạo để đối chiếu. Một smoke PASS phải có nhãn SYNTHETIC, benchmark NOT_RUN và đủ manifest/JSONL; nó chưa thay thế các phép thử Windows bắt buộc dưới đây. Nếu có lỗi, giữ nguyên artifact/log và chẩn đoán trước khi lặp.

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

1. Ma trận môi trường thực, full commit/diff hoặc biên nhận ZIP (comment commit, archive SHA-256, kiểm các tệp giải nén), dependency versions và snapshot phần cứng/hash; ghi rõ snapshot giới hạn hay hồ sơ đầy đủ TASK-001. Bản gốc log giữ riêng nếu có đường dẫn cá nhân, bản chia sẻ nêu rõ cách chuẩn hóa.
2. Bộ test bắt buộc Windows ở trên thực thi, không missing/skip các đường Windows cần xác minh; ba lượt liên tiếp để kiểm độ ổn định signal/cleanup, báo riêng passed/failed/skipped/unrun. Không yêu cầu POSIX-only test chạy giả trên Windows.
3. Dry-run thật tạo manifest/JSONL qua validator/hash, kiểm không còn tiến trình/scratch thuộc lượt; cleanup failure không được che bằng CANCELLED/PASS. Không có marker cảnh báo bất ngờ trong output đã thu thập.
4. Nếu sửa code: test hồi quy cho lỗi đã phát hiện, kiểm Linux liên quan vẫn qua, evidence sinh tự động và checksum mới; không sửa evidence cũ hoặc source đã chấp nhận để giả giữ hash.
5. Handoff 17 trường ghi phạm vi Windows cụ thể, findings còn mở, mọi giới hạn và verdict reviewer. Không tuyên bố Windows VERIFIED nếu còn đường bắt buộc chưa chạy hoặc chỉ có mô phỏng trên Linux.

Output dự kiến: `task004/evidence/windows-<run-id>/` với validation summary, log đã chuẩn hóa, hardware snapshots và hashes, dry-run artifacts, test/skip matrix và handoff. Dùng đường dẫn tương đối; không ghi hostname/username/secrets. Việc lập ticket này không tạo các artifact đó và không chứng minh bất kỳ test Windows nào đã chạy.

## Cổng trước bước model thật

Sau Windows mock, đo lại RAM khả dụng sạch và đĩa trên máy đích, lưu nguồn hardware JSON/hash; chủ dự án xác nhận shortlist/model/quant/context/image budget và cho phép bước tiếp. Khi đó mới mở ticket riêng cho **bảng preflight theo model** và **adapter llama.cpp**. Các số RAM được nhắc trong prompt khác chỉ là đầu vào cần xác minh và ánh xạ model, không tự chép thành ngưỡng đã duyệt trong ticket này.

Ticket tiếp theo phải chốt revision/binary/cờ runtime bằng nguồn thực, cách dùng hardware_reference và tiêu chí từ chối mỗi model. Model downloads/runs, API trả phí, training, corpus/CVC và benchmark vẫn ngoài scope hiện tại; ACCEPT Windows mock không tự mở những quyền đó.
