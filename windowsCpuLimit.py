"""Optional Windows job-wide CPU limit, installed before workers are created."""

import os

_job_handle = None


def apply_cpu_limit(percent):
    """Limit this process and inherited child processes; fail if not enforceable.

    The handle stays open for the application lifetime. No breakaway flags are
    enabled. A nested job's percentage is relative to its parent's allocation.
    This limits scheduling CPU cycles, not temperature or power consumption.
    """
    global _job_handle
    if type(percent) is not int or not 1 <= percent <= 100:
        raise ValueError("CPU percentage must be an integer from 1 to 100")
    if os.name != "nt":
        raise RuntimeError("--cpu-percent requires Windows; use --host-workers here")
    if _job_handle is not None:
        raise RuntimeError("CPU limit is already installed; restart to change it")
    import ctypes
    from ctypes import wintypes

    class CpuRateInfo(ctypes.Structure):
        _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
    ]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = CpuRateInfo(0x1 | 0x4, percent * 100)
        if not kernel.SetInformationJobObject(handle, 15, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
    except BaseException:
        kernel.CloseHandle(handle)
        raise
    _job_handle = handle
    os.environ["POUW_CPU_PERCENT"] = str(percent)
