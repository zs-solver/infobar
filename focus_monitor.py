"""
前台窗口监控 - 基于 WinEventHook 事件驱动
当前台窗口为终端时发出信号，否则发出另一信号。
"""
import ctypes
import ctypes.wintypes
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

# ── 配置常量 ──────────────────────────────────────────────
# 兜底定时器：应对 Alt+Tab 等场景下 EVENT_SYSTEM_FOREGROUND 不触发的问题
# 设为 0 或 None 表示关闭；设为正整数（毫秒）表示开启，推荐值 3000
FALLBACK_POLL_INTERVAL_MS = 0
# ─────────────────────────────────────────────────────────

# WinEvent 常量
EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000

# 回调函数类型
WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,   # hWinEventHook
    ctypes.wintypes.DWORD,    # event
    ctypes.wintypes.HWND,     # hwnd
    ctypes.wintypes.LONG,     # idObject
    ctypes.wintypes.LONG,     # idChild
    ctypes.wintypes.DWORD,    # idEventThread
    ctypes.wintypes.DWORD,    # dwmsEventTime
)

# 默认终端进程名集合
DEFAULT_TERMINAL_PROCESSES = {
    "windowsterminal.exe",
    "cmd.exe",
    "powershell.exe",
    "pwsh.exe",
    "mintty.exe",          # Git Bash
    "conemu64.exe",
    "conemu.exe",
    "alacritty.exe",
    "wezterm-gui.exe",
    "hyper.exe",
    "terminus.exe",
    "wt.exe",
}


def _get_process_name(hwnd):
    """根据窗口句柄获取进程名（小写）"""
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == 0:
        return ""

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""

    try:
        buf = (ctypes.c_wchar * 260)()
        size = ctypes.wintypes.DWORD(260)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            # 取文件名部分
            full_path = buf.value
            return full_path.rsplit("\\", 1)[-1].lower()
        return ""
    finally:
        kernel32.CloseHandle(handle)


class FocusMonitor(QObject):
    """监控前台窗口切换，判断是否为终端进程"""

    terminal_activated = pyqtSignal()    # 前台切换到终端
    terminal_deactivated = pyqtSignal()  # 前台切换到非终端

    def __init__(self, own_hwnd_func, terminal_processes=None, parent=None):
        """
        Args:
            own_hwnd_func: 返回 InfoBar 自身窗口句柄的可调用对象
            terminal_processes: 终端进程名集合（小写），None 则用默认集
        """
        super().__init__(parent)
        self._own_hwnd_func = own_hwnd_func
        self._terminals = terminal_processes or DEFAULT_TERMINAL_PROCESSES
        self._hook = None
        self._last_is_terminal = None  # 上次判断结果，用于兜底去重

        # 必须持有回调引用防止被 GC
        self._callback = WinEventProcType(self._on_foreground_change)

        # 兜底定时器
        self._fallback_timer = None
        if FALLBACK_POLL_INTERVAL_MS:
            self._fallback_timer = QTimer(self)
            self._fallback_timer.setInterval(FALLBACK_POLL_INTERVAL_MS)
            self._fallback_timer.timeout.connect(self._poll_foreground)

    def start(self):
        """注册 WinEventHook"""
        self._hook = user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_FOREGROUND,
            0,
            self._callback,
            0, 0,
            WINEVENT_OUTOFCONTEXT,
        )
        if self._fallback_timer:
            self._fallback_timer.start()

    def stop(self):
        """注销 Hook"""
        if self._hook:
            user32.UnhookWinEvent(self._hook)
            self._hook = None
        if self._fallback_timer:
            self._fallback_timer.stop()

    def _on_foreground_change(self, hook, event, hwnd, id_object, id_child, thread_id, time):
        """前台窗口切换回调（不信任 hwnd 参数，主动查询实际前台窗口）"""
        try:
            self._check_and_emit()
        except Exception:
            pass  # ctypes 回调中异常必须吞掉，否则会导致进程崩溃

    def _poll_foreground(self):
        """兜底定时器回调"""
        self._check_and_emit()

    def _check_and_emit(self):
        """查询实际前台窗口并发出信号（带去重）"""
        fg_hwnd = user32.GetForegroundWindow()
        if not fg_hwnd:
            return

        # 忽略 InfoBar 自身获得焦点
        try:
            own_hwnd = self._own_hwnd_func()
            if fg_hwnd == own_hwnd:
                return
        except Exception:
            pass

        proc_name = _get_process_name(fg_hwnd)
        is_terminal = proc_name in self._terminals

        # 去重：状态未变化时不重复发信号
        if is_terminal == self._last_is_terminal:
            return
        self._last_is_terminal = is_terminal

        if is_terminal:
            self.terminal_activated.emit()
        else:
            self.terminal_deactivated.emit()

    def check_now(self):
        """立即检查当前前台窗口状态（用于启动时判断）"""
        self._check_and_emit()
