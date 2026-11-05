"""Read-only host checks. These observations describe this host, not a laptop."""

import ctypes
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import shutil

import psutil

from .config import Config


def windows_system_commit():
    """Return Windows system commit, never substitute RSS, VMS or swap on Linux."""
    result = {
        "total_bytes": None,
        "limit_bytes": None,
        "available_bytes": None,
        "source": "GetPerformanceInfo" if os.name == "nt" else None,
        "unavailable_reason": None,
    }
    if os.name != "nt":
        result["unavailable_reason"] = "WINDOWS_ONLY"
        return result

    from ctypes import wintypes

    class PerformanceInformation(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("CommitTotal", ctypes.c_size_t),
            ("CommitLimit", ctypes.c_size_t),
            ("CommitPeak", ctypes.c_size_t),
            ("PhysicalTotal", ctypes.c_size_t),
            ("PhysicalAvailable", ctypes.c_size_t),
            ("SystemCache", ctypes.c_size_t),
            ("KernelTotal", ctypes.c_size_t),
            ("KernelPaged", ctypes.c_size_t),
            ("KernelNonpaged", ctypes.c_size_t),
            ("PageSize", ctypes.c_size_t),
            ("HandleCount", wintypes.DWORD),
            ("ProcessCount", wintypes.DWORD),
            ("ThreadCount", wintypes.DWORD),
        ]

    try:
        api = ctypes.WinDLL("psapi", use_last_error=True).GetPerformanceInfo
        api.argtypes = [ctypes.POINTER(PerformanceInformation), wintypes.DWORD]
        api.restype = wintypes.BOOL
        info = PerformanceInformation()
        info.cb = ctypes.sizeof(info)
        if not api(ctypes.byref(info), info.cb) or not info.PageSize:
            result["unavailable_reason"] = "GET_PERFORMANCE_INFO_FAILED"
            return result
        result["total_bytes"] = info.CommitTotal * info.PageSize
        result["limit_bytes"] = info.CommitLimit * info.PageSize
        result["available_bytes"] = max(0, result["limit_bytes"] - result["total_bytes"])
    except (OSError, AttributeError):
        result["unavailable_reason"] = "GET_PERFORMANCE_INFO_UNAVAILABLE"
    return result


def check_preflight(config: Config, output_dir: Path):
    """Check thresholds inclusively; never create directories or touch outputs."""
    # Frozen config has already enforced the mock-only contract.
    checks = []
    available_ram = None
    free_disk = None
    try:
        available_ram = psutil.virtual_memory().available
        checks.append({
            "name": "available_ram", "passed": available_ram >= config.min_available_ram_bytes,
            "measured_bytes": available_ram, "required_bytes": config.min_available_ram_bytes,
            "source": "psutil.virtual_memory.available", "unavailable_reason": None,
        })
    except (OSError, psutil.Error):
        checks.append({"name": "available_ram", "passed": False,
                       "measured_bytes": None, "required_bytes": config.min_available_ram_bytes,
                       "source": "psutil.virtual_memory.available", "unavailable_reason": "RAM_READ_FAILED"})

    try:
        target = Path(output_dir).absolute()
        ancestor = target
        while not ancestor.exists() and ancestor != ancestor.parent:
            ancestor = ancestor.parent
        output_is_directory = ancestor.is_dir()
        checks.append({"name": "output_path", "passed": output_is_directory})
        # A pre-existing file is not accepted as an output directory or ancestor.
        if output_is_directory:
            free_disk = shutil.disk_usage(ancestor).free
        checks.append({
            "name": "free_disk", "passed": free_disk is not None and free_disk >= config.min_free_disk_bytes,
            "measured_bytes": free_disk, "required_bytes": config.min_free_disk_bytes,
            "source": "shutil.disk_usage.free",
            "unavailable_reason": None if free_disk is not None else "OUTPUT_PATH_NOT_DIRECTORY",
        })
    except OSError:
        checks.append({"name": "free_disk", "passed": False,
                       "measured_bytes": None, "required_bytes": config.min_free_disk_bytes,
                       "source": "shutil.disk_usage.free", "unavailable_reason": "DISK_READ_FAILED"})

    return {
        "ready": all(check["passed"] for check in checks),
        "checks": checks,
        "available_ram_bytes": available_ram,
        "free_disk_bytes": free_disk,
        "system_commit": windows_system_commit(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "measurement_scope": "CURRENT_HOST",
    }
