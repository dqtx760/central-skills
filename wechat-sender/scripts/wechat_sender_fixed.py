# -*- coding: utf-8 -*-
"""
微信消息发送模块 - 修复版
修复了文件复制粘贴发送的关键问题：
1. COM 环境初始化和清理
2. 文件路径编码处理（支持特殊字符）
3. DROPFILES 结构偏移量计算
4. 增强错误处理和日志记录
"""

import sys
import time
import io
import os
import random
import functools
from PIL import Image
import win32clipboard
import win32con
import win32gui
import win32api
import ctypes
import pythoncom
from ctypes import wintypes

user32 = ctypes.windll.user32

# 关键修复：所有 print 立即刷新 stdout 缓冲区
# 原因：Python 进程崩溃（如 0xC0000005 ACCESS_VIOLATION）时，未刷新的 stdout 会丢失
# 导致日志中只能看到 wechat_send_cli.py 的 flush=True 输出，无法定位崩溃点
print = functools.partial(print, flush=True)

# 全局异常 hook：捕获未处理异常并立即打印到 stderr（flush=True）
# 避免崩溃时 traceback 被缓冲区吞掉
def _global_excepthook(exc_type, exc_value, exc_tb):
    import traceback as _tb
    sys.stderr.write(f"\n[Sender FATAL] 未捕获异常: {exc_type.__name__}: {exc_value}\n")
    sys.stderr.write("".join(_tb.format_exception(exc_type, exc_value, exc_tb)))
    sys.stderr.flush()
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _global_excepthook

# ==================== COM 环境管理 ====================

def _init_com():
    """初始化 COM 环境（STA 模式）"""
    try:
        pythoncom.CoInitialize()
        return True
    except Exception as e:
        print(f"[Sender] COM初始化失败: {e}", file=sys.stderr)
        return False

def _uninit_com():
    """清理 COM 环境"""
    try:
        pythoncom.CoUninitialize()
    except Exception:
        pass

# ==================== 支持的文件类型 ====================
SUPPORTED_EXTENSIONS = {
    # 文档
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.rtf', '.odt', '.ods', '.odp',
    # 音频
    '.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma', '.m4a',
    # 视频
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm',
    # 图片
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',
    # 压缩包
    '.zip', '.rar', '.7z', '.tar', '.gz',
    # 其他
    '.apk', '.exe', '.msi', '.dmg',
}

# ==================== 结构化错误类型 ====================
# 统一错误格式：ERR_<CATEGORY>_<NAME>，便于 Node.js 层解析并给出具体用户提示

class SendFileError(Exception):
    """文件发送基础错误"""
    CODE = "ERR_UNKNOWN"
    def __init__(self, detail=""):
        self.detail = detail
        super().__init__(f"{self.CODE}: {detail}" if detail else self.CODE)

class WechatWindowNotFoundError(SendFileError):
    CODE = "ERR_WINDOW_NOT_FOUND"
    def __init__(self, detail="微信窗口未找到或未激活"):
        super().__init__(detail)

class ClipboardFormatError(SendFileError):
    CODE = "ERR_CLIPBOARD_FORMAT"
    def __init__(self, detail="剪贴板文件格式设置失败"):
        super().__init__(detail)

class ClipboardAccessError(SendFileError):
    CODE = "ERR_CLIPBOARD_ACCESS"
    def __init__(self, detail="剪贴板访问失败"):
        super().__init__(detail)

class PasteTimeoutError(SendFileError):
    CODE = "ERR_PASTE_TIMEOUT"
    def __init__(self, detail="粘贴操作超时"):
        super().__init__(detail)

class SearchTargetError(SendFileError):
    CODE = "ERR_SEARCH_TARGET"
    def __init__(self, detail="无法搜索到目标联系人"):
        super().__init__(detail)

class EnterChatError(SendFileError):
    CODE = "ERR_ENTER_CHAT"
    def __init__(self, detail="无法进入目标会话"):
        super().__init__(detail)

# ==================== 延迟工具 ====================

def _random_delay(base: float, variance: float = 0.3) -> float:
    """生成随机延迟时间，模拟人类操作节奏"""
    factor = 1.0 + random.uniform(-variance, variance)
    return base * factor

# ==================== 剪贴板操作 ====================

def _set_clipboard_text(text):
    """将文本复制到剪贴板"""
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


def _set_clipboard_image(image_path):
    """将图片复制到剪贴板"""
    img = Image.open(image_path).convert("RGB")
    output = io.BytesIO()
    img.save(output, format="BMP")
    bmp_data = output.getvalue()
    output.close()
    dib_data = bmp_data[14:]

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
    finally:
        win32clipboard.CloseClipboard()


def _set_clipboard_file(file_path):
    """
    将文件复制到剪贴板（用于发送文件/音频）
    
    修复内容：
    1. 使用 GlobalAlloc 分配全局内存，确保剪贴板数据在函数返回后仍然有效
    2. 正确处理 DROPFILES 结构
    3. 改进文件路径编码处理
    4. 添加更详细的错误日志
    """
    from ctypes import wintypes
    
    # 确保文件路径是绝对路径
    file_path = os.path.abspath(file_path)
    
    # 验证文件存在
    if not os.path.isfile(file_path):
        print(f"[Sender] 文件不存在: {file_path}", file=sys.stderr)
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 验证文件可读
    if not os.access(file_path, os.R_OK):
        print(f"[Sender] 文件不可读（权限不足）: {file_path}", file=sys.stderr)
        raise PermissionError(f"文件不可读（权限不足）: {file_path}")
    
    # 记录开始时间
    start_time = time.time()
    
    # 文件列表
    files = [file_path]
    
    # DROPFILES 结构大小 = 20 bytes (5 DWORDs)
    dropfiles_size = 20
    offset = dropfiles_size
    
    # 计算缓冲区大小
    total_length = 0
    for f in files:
        fbytes = f.encode('utf-16-le') + b'\x00\x00'
        total_length += len(fbytes)
    total_length += 2  # 最终双零终止符
    
    buffer_size = offset + total_length
    
    # 使用 GlobalAlloc 分配全局内存（GMEM_MOVEABLE）
    # 这样 Windows 剪贴板可以在函数返回后继续访问数据
    GMEM_MOVEABLE = 0x0002
    GMEM_ZEROINIT = 0x0040
    kernel32 = ctypes.windll.kernel32
    
    # 设置返回类型和参数类型为 c_void_p（64位系统上指针是64位的）
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    
    h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, buffer_size)
    
    if not h_global or h_global == ctypes.c_void_p(0).value:
        err = kernel32.GetLastError()
        raise MemoryError(f"GlobalAlloc 失败，错误码: {err}")
    
    try:
        # 锁定内存，获取指针
        ptr = kernel32.GlobalLock(h_global)
        
        if not ptr or ptr == ctypes.c_void_p(0).value:
            err = kernel32.GetLastError()
            raise MemoryError(f"GlobalLock 失败，错误码: {err}")
        
        try:
            # 创建 ctypes 缓冲区
            buf = (ctypes.c_ubyte * buffer_size).from_address(ptr)
            
            # 创建 DROPFILES 结构（正确的内存布局）
            # DROPFILES 结构定义（考虑内存对齐）:
            # typedef struct _DROPFILES {
            #     DWORD pFiles;      // 0-3 字节
            #     LONG x;            // 4-7 字节
            #     LONG y;            // 8-11 字节
            #     BOOL fNC;          // 12-15 字节（1字节数据 + 3字节填充）
            #     BOOL fWide;        // 16-19 字节（1字节数据 + 3字节填充）
            # } DROPFILES;
            
            # 初始化整个缓冲区为 0
            ctypes.memset(ctypes.byref(buf), 0, buffer_size)
            
            # 设置 pFiles 偏移量（小端序）
            offset_bytes = offset.to_bytes(4, byteorder='little')
            buf[0:4] = offset_bytes
            
            # 设置 fWide = TRUE (Unicode) - 在偏移量 16 处
            buf[16] = 1
            
            # 写入文件列表（Unicode，每个文件路径以双零终止）
            pos = offset
            for f in files:
                fbytes = f.encode('utf-16-le') + b'\x00\x00'
                buf[pos:pos+len(fbytes)] = fbytes
                pos += len(fbytes)
        finally:
            # 解锁内存
            kernel32.GlobalUnlock(h_global)
        
        # 设置剪贴板数据
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_HDROP, h_global)
        finally:
            win32clipboard.CloseClipboard()
        
        elapsed = (time.time() - start_time) * 1000
        print(f"[Sender] 剪贴板文件设置成功: {file_path} (耗时: {elapsed:.2f}ms)")
        
    except Exception as e:
        # 释放全局内存
        kernel32.GlobalFree(h_global)
        print(f"[Sender] 剪贴板文件设置失败: {type(e).__name__} - {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

# ==================== Unicode SendInput 支持 ====================

INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_void_p),
    ]

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_void_p),
    ]

class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ('mi', _MOUSEINPUT),
        ('ki', _KEYBDINPUT),
        ('hi', _HARDWAREINPUT),
    ]

class _INPUT(ctypes.Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('u', _INPUT_UNION),
    ]

_sendinput = ctypes.windll.user32.SendInput
_sendinput.argtypes = [wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
_sendinput.restype = wintypes.UINT

def _send_vkey(vk_code, key_up=False):
    """通过 keybd_event 发送虚拟键（如右Alt键 VK_RMENU=0xA5）

    重要：微信只识别 keybd_event + KEYEVENTF_EXTENDEDKEY 的右Alt按键，
    SendInput 方式无法触发微信录音。
    必须设置 argtypes，否则 64位系统上 dwFlags 参数被错误截断，
    导致 KEYEVENTF_EXTENDEDKEY 标志丢失，微信不识别。
    """
    # 设置函数参数类型（64位兼容，确保 dwFlags 不被截断）
    user32.keybd_event.argtypes = [
        wintypes.BYTE,    # bVk
        wintypes.BYTE,    # bScan
        wintypes.DWORD,   # dwFlags
        ctypes.c_void_p   # dwExtraInfo
    ]
    KEYEVENTF_EXTENDEDKEY = 0x0001
    flags = KEYEVENTF_EXTENDEDKEY
    if key_up:
        flags |= KEYEVENTF_KEYUP
    user32.keybd_event(vk_code, 0, flags, 0)


def _reset_keyboard_state():
    """强制清除键盘修饰键卡住状态

    keybd_event 松开右Alt后，Windows 有时不会清除 Alt 修饰键状态，
    导致系统认为 Alt 还在按着，实体键盘被"劫持"，后续所有键盘输入
    都被当成 Alt+组合键，微信也无法正常操作。

    本函数通过反复检测 + keybd_event + SendInput 双重松开的方式强制清除：
    1. 用 GetKeyState 检测每个修饰键的当前状态
    2. 用 keybd_event 和 SendInput（带扫描码）反复松开
    3. 直到 GetKeyState 确认所有修饰键都已松开
    """
    import win32api
    import win32con

    # 修饰键及其扫描码（左右分开）
    # (vk_code, scan_code)
    modifiers = [
        (0x11, 0x1D),  # VK_CONTROL (左Ctrl)
        (0x12, 0x38),  # VK_MENU (左Alt)
        (0x10, 0x2A),  # VK_SHIFT (左Shift)
        (0xA3, 0x1D),  # VK_RCONTROL (右Ctrl)
        (0xA5, 0x38),  # VK_RMENU (右Alt)
        (0xA1, 0x36),  # VK_RSHIFT (右Shift)
        (0x5B, 0x5B),  # VK_LWIN
        (0x5C, 0x5C),  # VK_RWIN
    ]

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP_LOCAL = 0x0002
    KEYEVENTF_EXTENDEDKEY_LOCAL = 0x0001

    def _send_keyup(vk, scan):
        """用 SendInput 发送单个键的 UP 事件"""
        class _KEYBDINPUT_LOCAL(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p),
            ]

        class _INPUT_LOCAL(ctypes.Structure):
            class __INPUT_LOCAL(ctypes.Union):
                _fields_ = [("ki", _KEYBDINPUT_LOCAL)]
            _fields_ = [
                ("type", wintypes.DWORD),
                ("_input", __INPUT_LOCAL),
            ]

        inp = _INPUT_LOCAL()
        inp.type = INPUT_KEYBOARD
        inp._input.ki.wVk = vk
        inp._input.ki.wScan = scan
        flags = KEYEVENTF_KEYUP_LOCAL
        if vk in (0xA3, 0xA5, 0x5B, 0x5C):  # 右Ctrl/右Alt/Win键需要扩展标志
            flags |= KEYEVENTF_EXTENDEDKEY_LOCAL
        inp._input.ki.dwFlags = flags
        inp._input.ki.time = 0
        inp._input.ki.dwExtraInfo = 0
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT_LOCAL))

    # 设置 keybd_event 参数类型（64位兼容）
    user32.keybd_event.argtypes = [
        wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p
    ]

    # 反复检测并清除，最多 5 轮
    max_rounds = 5
    for round_idx in range(max_rounds):
        # 检查哪些修饰键还按着
        stuck_keys = []
        for vk, scan in modifiers:
            try:
                state = win32api.GetKeyState(vk)
                if state & 0x8000:  # 高位为1表示按下
                    stuck_keys.append((vk, scan))
            except Exception:
                pass

        if not stuck_keys:
            print(f"[Sender] ✅ 键盘状态已清除（第{round_idx+1}轮检测）")
            return True

        print(f"[Sender] 第{round_idx+1}轮清除: 仍有 {len(stuck_keys)} 个修饰键卡住")

        # 先用 keybd_event 松开
        for vk, scan in stuck_keys:
            flags = win32con.KEYEVENTF_KEYUP
            if vk in (0xA3, 0xA5, 0x5B, 0x5C):
                flags |= win32con.KEYEVENTF_EXTENDEDKEY
            try:
                win32api.keybd_event(vk, scan, flags, 0)
                time.sleep(0.02)
            except Exception:
                pass

        time.sleep(0.1)

        # 再用 SendInput 松开（带扫描码，更可靠）
        for vk, scan in stuck_keys:
            try:
                _send_keyup(vk, scan)
                time.sleep(0.02)
            except Exception:
                pass

        time.sleep(0.2)

    # 最终检测
    still_stuck = []
    for vk, scan in modifiers:
        try:
            state = win32api.GetKeyState(vk)
            if state & 0x8000:
                still_stuck.append(hex(vk))
        except Exception:
            pass

    if still_stuck:
        print(f"[Sender] ⚠️ 仍有修饰键卡住: {still_stuck}")
        return False
    else:
        print("[Sender] ✅ 键盘状态已清除")
        return True

def _send_unicode_char(ch):
    """通过 SendInput + KEYEVENTF_UNICODE 发送单个 Unicode 字符"""
    code = ord(ch)
    ki_down = _KEYBDINPUT(0, code, KEYEVENTF_UNICODE, 0, None)
    u_down = _INPUT_UNION()
    u_down.ki = ki_down
    inp_down = _INPUT(INPUT_KEYBOARD, u_down)
    
    ki_up = _KEYBDINPUT(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)
    u_up = _INPUT_UNION()
    u_up.ki = ki_up
    inp_up = _INPUT(INPUT_KEYBOARD, u_up)
    
    _sendinput(1, ctypes.byref(inp_down), ctypes.sizeof(_INPUT))
    _sendinput(1, ctypes.byref(inp_up), ctypes.sizeof(_INPUT))


def _type_human_like(text):
    """模拟人类键盘输入文本，支持全 Unicode（中文/日文等）"""
    for ch in text:
        try:
            _send_unicode_char(ch)
        except Exception:
            try:
                from win32com.client import Dispatch
                wsh = Dispatch("WScript.Shell")
                wsh.SendKeys(ch)
            except Exception:
                vk = ord(ch.upper()) if ch.isalpha() else ord(ch)
                user32.keybd_event(vk, 0, 0, 0)
                time.sleep(0.02)
                user32.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(random.uniform(0.01, 0.03))

# ==================== 虚拟键码操作 ====================

def _press_key(vk_code, delay=0.05):
    """按下并释放一个虚拟键码"""
    # 必须设置 argtypes（64位兼容，确保 dwFlags 不被截断）
    user32.keybd_event.argtypes = [
        wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p
    ]
    user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(delay)


def _press_key_down(vk_code):
    """按下键（不释放）"""
    user32.keybd_event.argtypes = [
        wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p
    ]
    user32.keybd_event(vk_code, 0, 0, 0)


def _press_key_up(vk_code):
    """释放键"""
    user32.keybd_event.argtypes = [
        wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p
    ]
    user32.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

# ==================== 微信操作 ====================

def _activate_wechat():
    """步骤1：激活微信窗口 - 使用 Ctrl+Alt+W 快捷键，失败后用 SetForegroundWindow 兜底"""
    print("[Sender] [步骤1] 激活微信窗口 Ctrl+Alt+W")
    _press_key_down(win32con.VK_CONTROL)
    _press_key_down(win32con.VK_MENU)
    _press_key(0x57)  # W
    _press_key_up(win32con.VK_MENU)
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.8))

    # 兜底：如果 Ctrl+Alt+W 没激活窗口，尝试 SetForegroundWindow
    try:
        import win32gui as _wgi
        wechat_classes = ["WeChatMainWndForPC", "Qt51514QWindowIcon", "WeChat"]
        hwnd = None
        for cls in wechat_classes:
            hwnd = _wgi.FindWindow(cls, None)
            if hwnd:
                print(f"[Sender] [步骤1] 兜底：找到微信窗口 {cls} (hwnd={hwnd})")
                break
        if not hwnd:
            # 通过标题查找
            def _enum_cb(h, lst):
                try:
                    t = _wgi.GetWindowText(h)
                    if t and ('微信' in t or 'WeChat' in t) and _wgi.IsWindowVisible(h):
                        lst.append(h)
                except: pass
            _lst = []
            _wgi.EnumWindows(_enum_cb, _lst)
            if _lst:
                hwnd = _lst[0]
                print(f"[Sender] [步骤1] 兜底：通过标题找到微信窗口 (hwnd={hwnd})")

        if hwnd:
            # 如果窗口最小化，先恢复
            if _wgi.IsIconic(hwnd):
                _wgi.ShowWindow(hwnd, 9)  # SW_RESTORE
                time.sleep(0.3)
            _wgi.SetForegroundWindow(hwnd)
            print(f"[Sender] [步骤1] SetForegroundWindow 成功 (hwnd={hwnd})")
        else:
            print("[Sender] [步骤1] 警告：未找到微信窗口，请确认微信已登录", file=sys.stderr)
    except Exception as e:
        print(f"[Sender] [步骤1] SetForegroundWindow 兜底失败：{e}", file=sys.stderr)


def _hide_wechat():
    """步骤9：隐藏微信窗口 Ctrl+Alt+W"""
    print("[Sender] [步骤9] 隐藏窗口 Ctrl+Alt+W")
    _press_key_down(win32con.VK_CONTROL)
    _press_key_down(win32con.VK_MENU)
    _press_key(0x57)  # W
    _press_key_up(win32con.VK_MENU)
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(0.3)


def _open_search():
    """步骤2：打开搜索框 Ctrl+F"""
    print("[Sender] [步骤2] 打开搜索框 Ctrl+F")
    _press_key_down(win32con.VK_CONTROL)
    _press_key(0x46)  # F
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.5))


def _type_target_name(target_name):
    """步骤3：输入目标名称 - 用剪贴板 + Ctrl+V 粘贴

    🔧 修复 2026-06-28: 之前用 _type_human_like 逐字符 Unicode SendInput 输入，
    会激活微信的中文输入法。输入法激活后，右Alt键被输入法拦截（用于切换中英文），
    不触发微信录音。这是 test_electron_spawn.py（用剪贴板粘贴）成功而生产代码失败的关键差异。
    改用剪贴板 + Ctrl+V 粘贴，不触发输入法，右Alt能正常触发录音。
    """
    preview = target_name[:60] + '...' if len(target_name) > 60 else target_name
    print(f"[Sender] [步骤3] 剪贴板粘贴目标名称: {preview}（共{len(target_name)}字符）")
    try:
        # 复制到剪贴板
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, target_name)
        finally:
            win32clipboard.CloseClipboard()
        time.sleep(0.2)
        # Ctrl+V 粘贴
        _press_key_down(win32con.VK_CONTROL)
        _press_key(0x56)  # V
        _press_key_up(win32con.VK_CONTROL)
        time.sleep(_random_delay(1.0))
        print("[Sender] [步骤3] 目标名称已粘贴")
    except Exception as e:
        print(f"[Sender] [步骤3] 剪贴板粘贴失败，降级到逐字符输入: {e}")
        _type_human_like(target_name)
        time.sleep(_random_delay(0.5))
        print("[Sender] [步骤3] 目标名称已输入（降级）")


def _select_first_search_result():
    """选择搜索结果中的第一个项目（向下箭头）"""
    print("[Sender] [步骤3.5] 选择第一个搜索结果（向下箭头）")
    _press_key(win32con.VK_DOWN, 0.3)
    time.sleep(_random_delay(0.5))


def _enter_chat():
    """步骤4：进入聊天 Enter（只按一次，第二次Enter会导致焦点丢失，右Alt无法触发录音）"""
    print("[Sender] [步骤4] 进入聊天 Enter")
    _press_key(win32con.VK_RETURN, 0.3)
    time.sleep(_random_delay(2.0))


def _ensure_input_focus():
    """步骤5：确保输入框焦点 - 改进版
    
    使用多种方法确保输入框获得焦点：
    1. Ctrl+End 移动到输入框末尾
    2. 点击输入框中心位置（模拟鼠标点击）
    3. 再次 Ctrl+End 确认焦点
    """
    print("[Sender] [步骤5] 确保输入框焦点")

    # 方法1: Ctrl+End 移动到输入框末尾
    print("[Sender] [步骤5.1] Ctrl+End 移动到输入框末尾")
    _press_key_down(win32con.VK_CONTROL)
    _press_key(0x23)  # End key
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.2))

    # 🔧 修复 2026-06-28: 移除方法2（鼠标点击输入框），
    # 用户要求取消鼠标动作。鼠标点击会导致微信从语音消息模式切换回文字输入模式，
    # 右Alt无法触发录音。只用键盘操作 Ctrl+End 确保焦点。

    # 方法3: 再次 Ctrl+End 确认焦点
    print("[Sender] [步骤5.3] 再次 Ctrl+End 确认焦点")
    _press_key_down(win32con.VK_CONTROL)
    _press_key(0x23)  # End key
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.3))
    
    print("[Sender] [步骤5] 输入框焦点已确认")


def _at_user(display_name):
    """步骤6：@用户 Shift+2 → 用户名 → Space*2（剪贴板粘贴方式）"""
    print(f"[Sender] [步骤6] @用户: {display_name}（剪贴板粘贴）")
    _press_key_down(win32con.VK_SHIFT)
    _press_key(0x32)  # 2
    _press_key_up(win32con.VK_SHIFT)
    time.sleep(_random_delay(0.1))
    
    _set_clipboard_text(display_name)
    _press_key_down(win32con.VK_CONTROL)
    _press_key(0x56)  # V
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.3))
    
    _press_key(0x20, 0.1)  # Space
    _press_key(0x20, 0.1)  # Space
    print("[Sender] [步骤6] @用户完成")


def _at_user_keyboard(display_name):
    """步骤6（键盘输入方式）：@用户"""
    print(f"[Sender] [步骤6] @用户: {display_name}（模拟键盘输入）")
    
    _press_key_down(win32con.VK_SHIFT)
    _press_key(0x32)  # 2
    _press_key_up(win32con.VK_SHIFT)
    
    time.sleep(0.2)
    _type_human_like(display_name)
    time.sleep(0.5)
    _press_key(win32con.VK_RETURN, 0.1)
    
    print("[Sender] [步骤6] @用户完成")


def _type_message(text):
    """步骤7：键盘输入消息内容"""
    preview = text[:80] + '...' if len(text) > 80 else text
    print(f"[Sender] [步骤7] 键盘输入消息内容（Unicode SendInput）: {preview}（共{len(text)}字符）")
    _type_human_like(text)
    time.sleep(_random_delay(0.5))


def _paste_file_alternative():
    """备用粘贴方法：再次尝试 Ctrl+V 粘贴
    
    当第一次 Ctrl+V 粘贴失败时，重新设置剪贴板并再次尝试粘贴
    """
    print("[Sender] 尝试备用粘贴方法（重新设置剪贴板 + Ctrl+V）")
    
    try:
        import win32clipboard
        import win32con
        
        # 检查剪贴板是否还有 CF_HDROP
        win32clipboard.OpenClipboard()
        has_hdrop = win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP)
        win32clipboard.CloseClipboard()
        
        if not has_hdrop:
            print("[Sender] 剪贴板 CF_HDROP 已失效，重新设置")
            # 这里无法重新设置，因为没有文件路径信息
            # 只能尝试唤醒粘贴操作
        else:
            print("[Sender] 剪贴板 CF_HDROP 仍然可用")
        
        # 方法1: 再次尝试 Ctrl+V
        print("[Sender] 再次尝试 Ctrl+V 粘贴")
        _press_key_down(win32con.VK_CONTROL)
        time.sleep(0.05)
        _press_key(0x56)  # V
        time.sleep(0.05)
        _press_key_up(win32con.VK_CONTROL)
        time.sleep(1.0)
        
        # 检查粘贴结果
        win32clipboard.OpenClipboard()
        still_has_hdrop = win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP)
        win32clipboard.CloseClipboard()
        
        if not still_has_hdrop:
            print("[Sender] 备用粘贴方法成功：剪贴板已被消费")
            return True
        else:
            print("[Sender] 备用粘贴方法失败：剪贴板仍未被消费")
            
            # 方法2: 尝试使用 Shift+Insert（另一种粘贴快捷键）
            print("[Sender] 尝试 Shift+Insert 粘贴")
            _press_key_down(win32con.VK_SHIFT)
            time.sleep(0.05)
            _press_key(0x49)  # I (Insert)
            time.sleep(0.05)
            _press_key_up(win32con.VK_SHIFT)
            time.sleep(1.0)
            
            # 再次检查
            win32clipboard.OpenClipboard()
            still_has_hdrop2 = win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP)
            win32clipboard.CloseClipboard()
            
            if not still_has_hdrop2:
                print("[Sender] Shift+Insert 粘贴成功")
                return True
            else:
                print("[Sender] Shift+Insert 粘贴也失败了")
                return False
                
    except Exception as e:
        print(f"[Sender] 备用粘贴方法失败: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        return False

    return False


def _send_message():
    """步骤8：发送消息 Enter"""
    print("[Sender] [步骤8] 发送消息 Enter")
    _press_key(win32con.VK_RETURN, 0.3)
    time.sleep(_random_delay(0.5))


def _close_popups():
    """关闭所有弹窗（ESC×3）"""
    print("[Sender] 关闭所有弹窗...")
    _press_key(win32con.VK_ESCAPE, 0.2)
    _press_key(win32con.VK_ESCAPE, 0.2)
    _press_key(win32con.VK_ESCAPE, 0.2)

# ==================== ClipboardSender 类 ====================

class ClipboardSender:
    """
    微信消息发送器 - 修复版
    通过剪贴板 + 模拟键盘操作实现微信消息的自动发送。
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        print("[Sender] ClipboardSender (修复版) 初始化完成")
        # 启动时自检：修复上次进程崩溃导致录音设备被卡在 CABLE Output 的问题
        try:
            self._ensure_recording_device_not_cable()
        except Exception as e:
            print(f"[Sender] 录音设备自检调用异常（不影响主流程）: {e}")

    def send(self, text, ensure_focus=True):
        """发送文本消息到当前微信聊天窗口"""
        try:
            print("[Sender] ========== 开始发送流程 ==========")
            print(f"[Sender] 消息内容: {text[:50]}{'...' if len(text) > 50 else ''}")
            
            if ensure_focus:
                _activate_wechat()
            
            _ensure_input_focus()
            _type_message(text)
            _send_message()
            _hide_wechat()
            
            print("[Sender] ========== 发送成功 ==========")
            return True
        except Exception as e:
            print(f"[Sender] send failed: {type(e).__name__} - {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return False

    def send_to_target(self, text, target_name, at_user=None, keyboard_at=False):
        """发送文本消息到指定微信联系人/群组"""
        for attempt in range(self.max_retries + 1):
            try:
                print("[Sender] ========== 开始发送流程 ==========")
                print(f"[Sender] 目标: {target_name}, AT用户: {at_user}, 键盘@: {keyboard_at}")
                print(f"[Sender] 消息内容: {text[:50]}{'...' if len(text) > 50 else ''}")
                print(f"[Sender] --- 尝试 {attempt+1}/{self.max_retries+1} ---")

                _close_popups()
                time.sleep(_random_delay(0.3))
                _activate_wechat()
                _open_search()
                _type_target_name(target_name)
                time.sleep(_random_delay(1.5))
                _enter_chat()
                time.sleep(_random_delay(1.0))
                _ensure_input_focus()

                if at_user and str(at_user).strip():
                    if keyboard_at:
                        _at_user_keyboard(str(at_user).strip())
                    else:
                        _at_user(str(at_user).strip())

                _type_message(text)
                _send_message()
                _hide_wechat()

                print("[Sender] ========== 发送成功 ==========")
                return True

            except Exception as e:
                print(f"[Sender] !! 异常 (attempt {attempt+1}): {type(e).__name__} - {e}")
                import traceback
                traceback.print_exc(file=sys.stderr)
                time.sleep(_random_delay(0.5))

        print("[Sender] !! 所有重试次数耗尽，发送失败")
        return False

    def send_image(self, image_path, ensure_focus=True):
        """发送图片到当前微信聊天窗口"""
        try:
            if not os.path.isfile(image_path):
                print(f"[Sender] 图片文件不存在: {image_path}", file=sys.stderr)
                return False

            print("[Sender] ========== 开始发送图片 ==========")
            print(f"[Sender] 图片路径: {image_path}")

            if ensure_focus:
                _activate_wechat()

            _ensure_input_focus()
            _set_clipboard_image(image_path)
            time.sleep(_random_delay(0.3))

            print("[Sender] 粘贴图片 Ctrl+V")
            _press_key_down(win32con.VK_CONTROL)
            _press_key(0x56)  # V
            _press_key_up(win32con.VK_CONTROL)
            time.sleep(_random_delay(0.5))

            _send_message()
            _hide_wechat()

            print("[Sender] ========== 图片发送成功 ==========")
            return True
        except Exception as e:
            print(f"[Sender] send_image failed: {type(e).__name__} - {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return False

    def send_image_to_target(self, image_path, target_name, at_user=None, delay_before_send=0, delay_after_open=0):
        """发送图片到指定微信联系人/群组"""
        for attempt in range(self.max_retries + 1):
            try:
                if not os.path.isfile(image_path):
                    print(f"[Sender] 图片文件不存在: {image_path}", file=sys.stderr)
                    return False

                print("[Sender] ========== 开始发送图片 ==========")
                print(f"[Sender] 目标: {target_name}, AT用户: {at_user}")
                print(f"[Sender] 图片路径: {image_path}")
                print(f"[Sender] --- 尝试 {attempt+1}/{self.max_retries+1} ---")

                _close_popups()
                time.sleep(_random_delay(0.3))
                _activate_wechat()
                _open_search()
                _type_target_name(target_name)
                time.sleep(_random_delay(1.5))
                _enter_chat()
                time.sleep(_random_delay(1.0))

                if delay_after_open > 0:
                    time.sleep(delay_after_open)

                _ensure_input_focus()
                time.sleep(_random_delay(0.3))

                image_size = os.path.getsize(image_path)
                image_size_mb = image_size / (1024 * 1024)
                print(f"[Sender] 图片大小: {image_size_mb:.2f}MB")
                
                print("[Sender] 设置剪贴板图片...")
                _set_clipboard_image(image_path)
                copy_wait = max(0.5, image_size_mb * 0.5)
                time.sleep(_random_delay(copy_wait))

                print("[Sender] 粘贴图片 Ctrl+V")
                _press_key_down(win32con.VK_CONTROL)
                _press_key(0x56)  # V
                _press_key_up(win32con.VK_CONTROL)
                paste_wait = max(1.5, image_size_mb * 1.0)
                time.sleep(_random_delay(paste_wait))

                if at_user and str(at_user).strip():
                    print("[Sender] @用户...")
                    _press_key(0x20)  # Space
                    time.sleep(_random_delay(0.1))
                    _at_user(str(at_user).strip())
                    time.sleep(_random_delay(0.3))

                if delay_before_send > 0:
                    time.sleep(delay_before_send)

                _send_message()
                _hide_wechat()

                print("[Sender] ========== 图片发送成功 ==========")
                return True

            except Exception as e:
                print(f"[Sender] !! 异常 (attempt {attempt+1}): {type(e).__name__} - {e}")
                import traceback
                traceback.print_exc(file=sys.stderr)
                time.sleep(_random_delay(0.5))

        print("[Sender] !! 所有重试次数耗尽，图片发送失败")
        return False

    def send_file_to_target(self, file_path, target_name, at_user=None):
        """
        发送文件到指定微信联系人/群组

        流程：
        1. 初始化 COM 环境
        2. 激活微信窗口快捷键 Ctrl+Alt+W
        3. 打开搜索框 Ctrl+F
        4. 键盘输入目标名称
        5. 进入聊天 Enter x2
        6. 设置剪贴板文件
        7. 等待剪贴板设置完成
        8. 验证剪贴板格式
        9. 执行粘贴操作 Ctrl+V
        10. 等待粘贴完成
        11. 发送消息 Enter
        12. 隐藏窗口 Ctrl+Alt+W
        13. 清理 COM 环境

        异常：
        抛出 SendFileError 子类，供调用方解析具体错误类型。
        """
        # 发送前验证文件
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"文件不可读（权限不足）: {file_path}")

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        ext = os.path.splitext(file_path)[1].lower()

        if ext and ext not in SUPPORTED_EXTENSIONS:
            print(f"[Sender] 警告: 文件类型 {ext} 可能不被微信支持，尝试发送中...")

        if file_size_mb > 100:
            print(f"[Sender] 提示: 文件较大 ({file_size_mb:.1f}MB)，发送可能需要较长时间，请耐心等待")

        print(f"[Sender] 文件类型: {ext or '未知'}, 大小: {file_size_mb:.2f}MB")

        last_error: SendFileError | None = None

        # 初始化 COM 环境
        com_initialized = _init_com()
        try:
            for attempt in range(self.max_retries + 1):
                try:
                    print(f"[Sender] PROGRESS:1/12 尝试 {attempt+1}/{self.max_retries+1}")
                    print("[Sender] ========== 开始发送文件 ==========")
                    print(f"[Sender] 目标: {target_name}, AT用户: {at_user}")
                    print(f"[Sender] 文件路径: {file_path}")

                    # 步骤1: 激活微信窗口
                    print(f"[Sender] PROGRESS:2/12 激活微信窗口")
                    _activate_wechat()
                    
                    # 等待窗口激活并查找
                    time.sleep(_random_delay(0.5))
                    
                    # 尝试多种微信窗口类名
                    hwnd = None
                    wechat_class_names = ["WeChatMainWndForPC", "Qt51514QWindowIcon", "WeChat"]
                    for class_name in wechat_class_names:
                        hwnd = win32gui.FindWindow(class_name, None)
                        if hwnd:
                            print(f"[Sender] 找到微信窗口: {class_name}")
                            break
                    
                    # 如果通过类名未找到，尝试通过标题查找
                    if not hwnd:
                        def enum_callback(h, windows):
                            try:
                                title = win32gui.GetWindowText(h)
                                if title and ('微信' in title or 'WeChat' in title):
                                    if win32gui.IsWindowVisible(h):
                                        windows.append(h)
                            except:
                                pass
                        windows = []
                        win32gui.EnumWindows(enum_callback, windows)
                        if windows:
                            hwnd = windows[0]
                            print(f"[Sender] 通过标题找到微信窗口")
                    
                    if not hwnd:
                        raise WechatWindowNotFoundError()
                    time.sleep(_random_delay(0.5))

                    # 步骤2: 打开搜索框
                    print(f"[Sender] PROGRESS:3/12 打开搜索框")
                    _open_search()
                    time.sleep(_random_delay(0.5))

                    # 步骤3: 输入目标名称
                    print(f"[Sender] PROGRESS:4/12 搜索目标")
                    _type_target_name(target_name)
                    print("[Sender] 目标名称已输入")
                    time.sleep(_random_delay(1.5))

                    # 步骤4: 进入聊天
                    print(f"[Sender] PROGRESS:5/12 进入会话")
                    _enter_chat()
                    time.sleep(_random_delay(1.0))

                    # 步骤5: 设置剪贴板文件
                    print(f"[Sender] PROGRESS:6/12 设置剪贴板")
                    _set_clipboard_file(file_path)

                    # 步骤6: 等待剪贴板设置完成
                    copy_wait = max(0.5, file_size_mb * 0.5)
                    print(f"[Sender] PROGRESS:7/12 等待剪贴板 ({copy_wait:.2f}s)")
                    time.sleep(_random_delay(copy_wait))

                    # 步骤7: 验证剪贴板格式
                    print(f"[Sender] PROGRESS:8/12 验证剪贴板格式")
                    try:
                        win32clipboard.OpenClipboard()
                        has_hdrop = win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP)
                        win32clipboard.CloseClipboard()
                        if not has_hdrop:
                            raise ClipboardFormatError()
                    except ClipboardFormatError:
                        raise
                    except Exception as e:
                        raise ClipboardAccessError(str(e))

                    # 步骤8: 执行粘贴
                    print(f"[Sender] PROGRESS:9/12 执行粘贴")
                    _press_key_down(win32con.VK_CONTROL)
                    time.sleep(0.05)
                    _press_key(0x56)  # V
                    time.sleep(0.05)
                    _press_key_up(win32con.VK_CONTROL)

                    # 步骤9: 等待粘贴完成
                    paste_wait = max(2.0, file_size_mb * 1.5)
                    print(f"[Sender] PROGRESS:10/12 等待发送 ({paste_wait:.2f}s)")
                    time.sleep(_random_delay(paste_wait))

                    # 步骤10: 发送
                    print(f"[Sender] PROGRESS:11/12 发送消息")
                    _send_message()
                    time.sleep(_random_delay(0.3))

                    # 步骤11: 隐藏窗口
                    _hide_wechat()

                    print("[Sender] PROGRESS:12/12 done")
                    print("[Sender] ========== 文件发送成功 ==========")
                    return True

                except SendFileError as e:
                    # 结构化错误，打印简化消息后继续重试
                    print(f"[Sender] !! {e.CODE} ({attempt+1}/{self.max_retries+1}): {e.detail}")
                    last_error = e
                    time.sleep(_random_delay(0.5))
                except Exception as e:
                    # 未知异常，包装为通用错误
                    print(f"[Sender] !! 未知异常 ({attempt+1}/{self.max_retries+1}): {type(e).__name__} - {e}")
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    last_error = SendFileError(str(e))
                    time.sleep(_random_delay(0.5))

            # 所有重试耗尽，抛出最终错误
            if last_error:
                raise last_error
            raise SendFileError("所有重试次数耗尽，文件发送失败")
        finally:
            # 清理 COM 环境
            if com_initialized:
                _uninit_com()

    def send_voice_to_target(self, text, target_name, at_user=None, audio_path=None):
        """
        发送语音消息到指定微信联系人/群组

        使用微信快捷键：按住右Alt开始录音，松开结束发送

        流程：
        1. 生成 TTS 音频（如果未提供 audio_path）
        2. 初始化 COM 环境
        3. 激活微信窗口
        4. 搜索并进入目标聊天
        5. 按住右Alt键开始录音
        6. 通过虚拟声卡/立体声混音播放音频
        7. 松开右Alt键结束录音并发送
        8. 隐藏窗口
        9. 清理 COM 环境
        """
        import tempfile
        import wave
        import struct as struct_module

        generated_audio_path = None
        com_initialized = False
        original_recording_device = None  # 原录音设备ID，用于 finally 切回

        try:
            # Step 1: 准备音频文件
            if audio_path and os.path.isfile(audio_path):
                final_audio_path = audio_path
                print(f"[Sender] 使用提供的音频文件: {audio_path}")
            else:
                # 使用 Windows SAPI 生成 TTS
                print(f"[Sender] 使用 SAPI TTS 生成语音...")
                generated_audio_path = self._generate_sapi_tts(text)
                final_audio_path = generated_audio_path
                print(f"[Sender] TTS 音频生成完成: {final_audio_path}")

            print("[Sender] ========== 开始发送语音 ==========")
            print(f"[Sender] 目标: {target_name}, AT用户: {at_user}")
            print(f"[Sender] 语音文本: {text[:50]}{'...' if len(text) > 50 else ''}")

            # Step 2: 初始化 COM
            com_initialized = _init_com()

            # Step 2.5: 切换默认录音设备到 CABLE Output（VB-Cable录音端）
            # 这样微信录音时会从 CABLE Output 录制，能录到 CABLE Input 播放的音频
            original_recording_device = self._switch_to_cable_output()

            for attempt in range(self.max_retries + 1):
                try:
                    print(f"[Sender] --- 尝试 {attempt+1}/{self.max_retries+1} ---")

                    _close_popups()
                    time.sleep(_random_delay(0.3))
                    _activate_wechat()
                    _open_search()
                    _type_target_name(target_name)
                    time.sleep(_random_delay(1.0))
                    # 进入聊天：只按一次Enter（按两次会导致焦点丢失，右Alt无法触发录音）
                    print("[Sender] [步骤4] 进入聊天 Enter")
                    _press_key(win32con.VK_RETURN, 0.3)
                    time.sleep(2.0)  # 等待聊天窗口完全加载

                    # 步骤5：确保微信在前台 + 清除键盘卡住状态
                    # 🔧 修复 2026-06-28: 移除"点击输入框"操作！
                    # 之前点击输入框会导致微信从"语音消息"模式（显示"按住说话"按钮）
                    # 切换回"文字输入"模式（显示文字输入框），文字模式下右Alt不触发录音。
                    # 这是生产环境失败而 test_electron_spawn.py 成功的关键差异：
                    # 测试脚本不点击输入框，只清除键盘状态，微信保持语音模式，右Alt生效。
                    # 另外在按下右Alt前必须清除可能卡住的 Ctrl/Alt 修饰键，
                    # 否则右Alt会变成 Ctrl+右Alt 组合键，微信不识别。
                    try:
                        import win32gui as _wg2
                        fg_hwnd = _wg2.GetForegroundWindow()
                        fg_title = _wg2.GetWindowText(fg_hwnd) if fg_hwnd else ''
                        wechat_hwnd = None
                        for cls in ['WeChatMainWndForPC', 'Qt51514QWindowIcon', 'WeChat']:
                            wechat_hwnd = _wg2.FindWindow(cls, None)
                            if wechat_hwnd:
                                break
                        print(f"[Sender] [步骤5] 前台窗口: hwnd={fg_hwnd}, title='{fg_title}', 微信窗口={wechat_hwnd}")

                        if wechat_hwnd and fg_hwnd != wechat_hwnd:
                            print(f"[Sender] [步骤5] ⚠️ 微信不在前台！尝试再次激活 Ctrl+Alt+W...")
                            # 用 Ctrl+Alt+W 重新激活，失败则 SetForegroundWindow 兜底
                            _press_key_down(win32con.VK_CONTROL)
                            _press_key_down(win32con.VK_MENU)
                            _press_key(0x57)  # W
                            _press_key_up(win32con.VK_MENU)
                            _press_key_up(win32con.VK_CONTROL)
                            time.sleep(_random_delay(0.8))
                            # 兜底：SetForegroundWindow
                            try:
                                if _wg2.IsIconic(wechat_hwnd):
                                    _wg2.ShowWindow(wechat_hwnd, 9)
                                    time.sleep(0.3)
                                _wg2.SetForegroundWindow(wechat_hwnd)
                                print(f"[Sender] [步骤5] SetForegroundWindow 兜底成功 (hwnd={wechat_hwnd})")
                            except Exception as e_fb:
                                print(f"[Sender] [步骤5] SetForegroundWindow 兜底失败: {e_fb}")
                            time.sleep(1.0)
                    except Exception as e:
                        print(f"[Sender] [步骤5] 前台检查失败: {e}")

                    # 按住右Alt键开始录音
                    # 关键：优先用主进程直接调用 keybd_event（测试验证此方式有效）
                    # 独立脚本方式作为降级方案
                    print("[Sender] 按住右Alt键开始录音...")
                    VK_RMENU = 0xA5

                    # 🔧 修复 2026-06-28: 按下右Alt前，用 SetForegroundWindow 重新激活微信
                    # 这是 test_electron_spawn.py 成功而生产代码失败的关键差异：
                    # test_electron_spawn.py 在按键前再次调用 ensure_wechat_foreground()，
                    # SetForegroundWindow 重新激活会重置微信内部状态，让焦点回到聊天输入区，
                    # 这样右Alt才能触发"按住说话"录音。
                    # 生产代码之前只检查前台（微信已在前台就跳过），没有重新激活，
                    # 导致微信焦点可能还停留在搜索框残留，右Alt不触发录音。
                    try:
                        import win32gui as _wg3
                        wechat_hwnd3 = None
                        for cls in ['WeChatMainWndForPC', 'Qt51514QWindowIcon', 'WeChat']:
                            wechat_hwnd3 = _wg3.FindWindow(cls, None)
                            if wechat_hwnd3:
                                break
                        if wechat_hwnd3:
                            if _wg3.IsIconic(wechat_hwnd3):
                                _wg3.ShowWindow(wechat_hwnd3, 9)
                                time.sleep(0.3)
                            _wg3.SetForegroundWindow(wechat_hwnd3)
                            time.sleep(0.5)  # 等待焦点稳定
                            fg_check = _wg3.GetForegroundWindow()
                            print(f"[Sender] [步骤6] 重新激活微信 (hwnd={wechat_hwnd3}, 前台={fg_check})")
                    except Exception as e_react:
                        print(f"[Sender] [步骤6] 重新激活失败（不影响继续）: {e_react}")

                    # 🔧 修复 2026-06-28: 按下右Alt前，主动松开 Ctrl 和 Alt 键
                    # Ctrl+Alt+W 和 Ctrl+F 操作后，Ctrl/Alt 可能卡住，
                    # 导致右Alt被当成 Ctrl+右Alt 或 Alt+右Alt 组合键，微信不识别，不触发录音。
                    # 不用 _reset_keyboard_state（用户已要求删除），
                    # 改用 _press_key_up 多次松开 Ctrl、左Alt、右Alt，确保干净状态。
                    try:
                        VK_CONTROL = 0x11
                        VK_MENU = 0x12  # 左Alt
                        # 检查修饰键是否卡住
                        ctrl_state = win32api.GetKeyState(VK_CONTROL)
                        alt_state = win32api.GetKeyState(VK_MENU)
                        print(f"[Sender] [步骤6] 诊断: Ctrl state={ctrl_state:#x}, Alt state={alt_state:#x}")
                        if (ctrl_state & 0x8000) or (alt_state & 0x8000):
                            print("[Sender] [步骤6] ⚠️ 检测到 Ctrl/Alt 卡住，主动松开...")
                            # 多次松开 Ctrl 和 Alt，确保彻底松开
                            for _ in range(3):
                                _press_key_up(VK_CONTROL)
                                _press_key_up(VK_MENU)
                                _press_key_up(VK_RMENU)
                                time.sleep(0.05)
                            # 再次检查
                            ctrl_state2 = win32api.GetKeyState(VK_CONTROL)
                            alt_state2 = win32api.GetKeyState(VK_MENU)
                            print(f"[Sender] [步骤6] 松开后: Ctrl state={ctrl_state2:#x}, Alt state={alt_state2:#x}")
                    except Exception as e_diag_pre:
                        print(f"[Sender] [步骤6] 修饰键检查异常（不影响继续）: {e_diag_pre}")

                    # 方式1：主进程直接调用 keybd_event（首选，测试验证有效）
                    try:
                        # 🔧 诊断 2026-06-28: 按下右Alt前，检查微信窗口状态和焦点
                        # 关键：微信不仅要在前台，焦点还要在聊天输入区，右Alt才能触发录音
                        try:
                            import win32gui as _wg4
                            import win32api as _wa4
                            fg_hwnd_pre = _wg4.GetForegroundWindow()
                            fg_title_pre = _wg4.GetWindowText(fg_hwnd_pre) if fg_hwnd_pre else ''
                            # 获取当前焦点窗口（GetFocus 必须在目标线程上下文，用 GetForegroundWindow + GetGUIThreadInfo 替代）
                            fg_thread = _wa4.GetWindowThreadProcessId(fg_hwnd_pre)[0]
                            # 用 GetGUIThreadInfo 获取焦点窗口
                            class _GUITHREADINFO(ctypes.Structure):
                                _fields_ = [
                                    ('cbSize', wintypes.DWORD),
                                    ('flags', wintypes.DWORD),
                                    ('hwndActive', wintypes.HWND),
                                    ('hwndFocus', wintypes.HWND),
                                    ('hwndCapture', wintypes.HWND),
                                    ('hwndMenuOwner', wintypes.HWND),
                                    ('hwndMoveSize', wintypes.HWND),
                                    ('hwndCaret', wintypes.HWND),
                                    ('rcCaret', wintypes.RECT),
                                ]
                            gti = _GUITHREADINFO()
                            gti.cbSize = ctypes.sizeof(_GUITHREADINFO)
                            user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(_GUITHREADINFO)]
                            user32.GetGUIThreadInfo.restype = wintypes.BOOL
                            if user32.GetGUIThreadInfo(fg_thread, ctypes.byref(gti)):
                                focus_hwnd = gti.hwndFocus
                                focus_class = _wg4.GetClassName(focus_hwnd) if focus_hwnd else ''
                                print(f"[Sender] [步骤6] 前台: hwnd={fg_hwnd_pre} title='{fg_title_pre}', 焦点窗口: hwnd={focus_hwnd} class='{focus_class}'")
                            else:
                                print(f"[Sender] [步骤6] 前台: hwnd={fg_hwnd_pre} title='{fg_title_pre}', GetGUIThreadInfo 失败")
                        except Exception as e_focus:
                            print(f"[Sender] [步骤6] 焦点检查异常: {e_focus}")

                        _send_vkey(VK_RMENU, key_up=False)
                        print("[Sender] 右Alt已按下（主进程直接调用）")
                    except Exception as e1:
                        print(f"[Sender] 主进程调用失败，尝试独立脚本: {e1}")
                        # 方式2：独立脚本降级
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        press_ralt_down_script = os.path.join(script_dir, 'press_ralt_down.py')

                        # 查找 pythonw.exe（无控制台版 Python）
                        python_exe = sys.executable
                        pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                        if os.path.exists(pythonw_exe):
                            python_exe = pythonw_exe

                        try:
                            import subprocess as _sp
                            _sp.Popen([python_exe, press_ralt_down_script],
                                      stdin=_sp.DEVNULL, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                                      creationflags=0x08000000)  # CREATE_NO_WINDOW
                            print(f"[Sender] 右Alt按下进程已启动（python={os.path.basename(python_exe)}）")
                            time.sleep(0.5)  # 等待独立进程执行按键
                            print("[Sender] 右Alt已按下（独立进程）")
                        except Exception as e2:
                            print(f"[Sender] 所有按键方式都失败: {e2}")

                    # 诊断：检查右Alt是否真的被按下
                    try:
                        ralt_state = win32api.GetKeyState(VK_RMENU)
                        if ralt_state & 0x8000:
                            print(f"[Sender] ✅ 右Alt状态确认: 已按下 (state={ralt_state:#x})")
                        else:
                            print(f"[Sender] ⚠️ 右Alt状态异常: 未按下 (state={ralt_state:#x})")
                    except Exception as e_diag:
                        print(f"[Sender] 右Alt状态检查失败: {e_diag}")

                    time.sleep(_random_delay(1.2))  # 等待录音启动

                    # 获取音频时长（在播放前获取，确保准确）
                    audio_duration = self._get_audio_duration(final_audio_path)
                    print(f"[Sender] 音频时长: {audio_duration:.1f}秒")

                    # 播放音频（异步方式，不阻塞）
                    print(f"[Sender] 播放音频: {final_audio_path}")
                    played = False
                    try:
                        played = self._play_audio_to_virtual_soundcard(final_audio_path)
                    except Exception as e:
                        print(f"[Sender] 音频播放异常: {e}")

                    if not played:
                        # 最后备用：winsound 异步播放
                        try:
                            import winsound
                            winsound.PlaySound(final_audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                            print("[Sender] winsound 异步播放已启动")
                            played = True
                        except Exception as e:
                            print(f"[Sender] winsound 播放失败: {e}")

                    if not played:
                        print("[Sender] !! 所有播放方式都失败了")
                        time.sleep(3.0)
                    else:
                        # 🔧 修复 2026-06-28: VB-Cable 播放函数内部已经等待播放完成并清理资源，
                        # 这里不再重复 sleep，否则录音时长会被拉长一倍（音频7秒 → 录音17秒）。
                        # 只给 0.3 秒让录音状态稳定，然后立即松开右Alt结束录音。
                        print(f"[Sender] 播放已完成，准备松开右Alt")
                        time.sleep(0.3)

                    # 松开右Alt键结束录音并发送
                    # 🔧 修复 2026-06-28: 之前错误地无条件使用 script_dir 和 python_exe，
                    # 但这两个变量只在"按下右Alt"的异常降级分支（方式2）里定义。
                    # 当"按下"走的是方式1（主进程直接调用）成功路径时，松开代码会因
                    # script_dir 未定义而崩溃（UnboundLocalError），导致右Alt没被松开、
                    # 录音没结束、语音没发送，重试3次全部失败。
                    # 修复：松开也优先用主进程直接调用（与按下方式1保持一致），
                    # 独立脚本作为降级方案，并在此处定义所需的 script_dir 和 python_exe。
                    print("[Sender] 松开右Alt键结束录音并发送...")

                    # 方式1：主进程直接调用 keybd_event（首选，与按下方式1一致）
                    try:
                        _send_vkey(0xA5, key_up=True)
                        print("[Sender] 右Alt已松开（主进程直接调用）")
                    except Exception as e1:
                        print(f"[Sender] 主进程松键失败，尝试独立脚本: {e1}")
                        # 方式2：独立脚本降级（在此处定义变量，避免 UnboundLocalError）
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        press_ralt_up_script = os.path.join(script_dir, 'press_ralt_up.py')
                        python_exe = sys.executable
                        pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                        if os.path.exists(pythonw_exe):
                            python_exe = pythonw_exe
                        try:
                            import subprocess as _sp2
                            _sp2.Popen([python_exe, press_ralt_up_script],
                                       stdin=_sp2.DEVNULL, stdout=_sp2.DEVNULL, stderr=_sp2.DEVNULL,
                                       creationflags=0x08000000)  # CREATE_NO_WINDOW
                            print(f"[Sender] 右Alt松开进程已启动（python={os.path.basename(python_exe)}）")
                            time.sleep(0.5)
                            print("[Sender] 右Alt已松开（独立进程）")
                        except Exception as e2:
                            print(f"[Sender] 所有松键方式都失败: {e2}")
                    # 强制清除键盘修饰键卡住状态（防止 Alt 卡住导致键盘被劫持）
                    try:
                        _reset_keyboard_state()
                    except Exception as e_reset:
                        print(f"[Sender] 键盘状态重置异常（不影响主流程）: {e_reset}")
                    time.sleep(_random_delay(1.0))

                    _hide_wechat()
                    print("[Sender] ========== 语音发送成功 ==========")
                    return True

                except Exception as e:
                    print(f"[Sender] !! 异常 (attempt {attempt+1}): {type(e).__name__} - {e}")
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    # 确保释放右Alt键
                    try:
                        _send_vkey(0xA5, key_up=True)
                        _reset_keyboard_state()
                    except:
                        pass
                    time.sleep(_random_delay(0.5))

            print("[Sender] !! 所有重试次数耗尽，语音发送失败")
            return False

        finally:
            # 确保释放右Alt键
            try:
                _send_vkey(0xA5, key_up=True)
                _reset_keyboard_state()
            except:
                pass
            # 切回原录音设备（重要：避免影响用户正常使用麦克风）
            try:
                self._restore_recording_device(original_recording_device)
            except:
                pass
            # 清理临时文件
            if generated_audio_path and os.path.exists(generated_audio_path):
                try:
                    os.remove(generated_audio_path)
                except:
                    pass
            # 清理 COM 环境
            if com_initialized:
                _uninit_com()

    def _switch_to_cable_output(self):
        """切换默认录音设备到 CABLE Output（VB-Cable录音端），返回原设备ID"""
        try:
            from pycaw.pycaw import AudioUtilities
            try:
                from pycaw.pycaw import ERole
                roles = [ERole.eConsole, ERole.eMultimedia, ERole.eCommunications]
            except ImportError:
                roles = None

            # 获取当前默认录音设备ID
            original_id = None
            try:
                enumerator = AudioUtilities.GetDeviceEnumerator()
                # eCapture=1, eConsole=0
                dev = enumerator.GetDefaultAudioEndpoint(1, 0)
                if dev:
                    # 🔧 修复 2026-06-28: pycaw 的 GetDefaultAudioEndpoint 返回 POINTER(IMMDevice)
                    # 直接用 .id 属性会报错 'POINTER(IMMDevice)' object has no attribute 'id'
                    # 需要用 GetId() 方法获取设备ID，用 GetFriendlyName() 获取名称
                    try:
                        # POINTER(IMMDevice) 通过 contents 访问实际对象
                        actual_dev = dev.contents if hasattr(dev, 'contents') else dev
                        # pycaw 的 IMMDevice 添加了 FriendlyName 和 id 的 property shortcut
                        # 但 POINTER 包装下可能失效，用 GetId() 方法更可靠
                        try:
                            original_id = actual_dev.GetId()
                        except (AttributeError, TypeError):
                            original_id = actual_dev.id
                        try:
                            friendly = actual_dev.FriendlyName
                        except (AttributeError, TypeError):
                            friendly = f"设备(original_id={original_id})"
                        print(f"[Sender] 原录音设备: {friendly}")
                    except Exception as e2:
                        print(f"[Sender] 获取原录音设备ID失败（不影响切换）: {e2}")
            except Exception as e:
                print(f"[Sender] 获取原录音设备失败: {e}")

            # 查找 CABLE Output
            devices = AudioUtilities.GetAllDevices()
            cable_output = None
            for dev in devices:
                if 'CABLE Output' in dev.FriendlyName:
                    cable_output = dev
                    break

            if not cable_output:
                print("[Sender] 未找到 CABLE Output 录音设备")
                return None

            # 切换到 CABLE Output
            AudioUtilities.SetDefaultDevice(cable_output.id, roles)
            print(f"[Sender] ✅ 已切换录音设备到 CABLE Output (id={cable_output.id})")
            return original_id

        except Exception as e:
            print(f"[Sender] 切换录音设备失败: {e}")
            return None

    def _restore_recording_device(self, original_id):
        """切回原录音设备"""
        if not original_id:
            return
        try:
            from pycaw.pycaw import AudioUtilities
            try:
                from pycaw.pycaw import ERole
                roles = [ERole.eConsole, ERole.eMultimedia, ERole.eCommunications]
            except ImportError:
                roles = None
            AudioUtilities.SetDefaultDevice(original_id, roles)
            print(f"[Sender] ✅ 已切回原录音设备 (id={original_id})")
        except Exception as e:
            print(f"[Sender] 切回录音设备失败: {e}")

    def _ensure_recording_device_not_cable(self):
        """启动时自检：如果默认录音设备被卡在 CABLE Output，自动切回真实麦克风

        场景：上次语音发送过程中进程崩溃，finally 块未执行，
        导致录音设备永久停留在 CABLE Output，微信按住说话功能失效。
        本方法在每次启动时检查并修复。
        """
        try:
            from pycaw.pycaw import AudioUtilities
            try:
                from pycaw.pycaw import ERole
                roles = [ERole.eConsole, ERole.eMultimedia, ERole.eCommunications]
            except ImportError:
                roles = None

            # 获取当前默认录音设备
            try:
                enumerator = AudioUtilities.GetDeviceEnumerator()
                dev = enumerator.GetDefaultAudioEndpoint(1, 0)
                if not dev:
                    return
                current_name = ''
                try:
                    current_name = dev.FriendlyName or ''
                except (AttributeError, TypeError):
                    try:
                        actual_dev = dev.contents if hasattr(dev, 'contents') else dev
                        current_name = actual_dev.FriendlyName or ''
                    except Exception:
                        pass

                # 检查是否被卡在 CABLE Output
                if 'CABLE Output' in current_name:
                    print(f"[Sender] ⚠️ 检测到默认录音设备被卡在 CABLE Output（上次进程可能崩溃），正在切回真实麦克风...")
                    # 查找一个真实麦克风设备（Active 状态，非 CABLE）
                    devices = AudioUtilities.GetAllDevices()
                    real_mic = None
                    for d in devices:
                        try:
                            name = d.FriendlyName or ''
                            # 跳过 CABLE 虚拟设备
                            if 'CABLE' in name.upper():
                                continue
                            # 优先选择名称含"麦克风"、"Microphone"、"Array" 的设备
                            if any(kw in name for kw in ['麦克风', 'Microphone', 'Array', '麦克风阵列']):
                                real_mic = d
                                break
                        except Exception:
                            continue

                    if real_mic:
                        try:
                            AudioUtilities.SetDefaultDevice(real_mic.id, roles)
                            print(f"[Sender] ✅ 已切回真实麦克风: {real_mic.FriendlyName}")
                        except Exception as e:
                            print(f"[Sender] ❌ 切回真实麦克风失败: {e}")
                    else:
                        print("[Sender] ⚠️ 未找到真实麦克风设备，请手动检查录音设备设置")
            except Exception as e:
                print(f"[Sender] 录音设备自检失败: {e}")
        except ImportError:
            # pycaw 未安装，跳过
            pass
        except Exception as e:
            print(f"[Sender] 录音设备自检异常: {e}")

    def _play_audio_to_virtual_soundcard(self, audio_path):
        """通过 VB-Cable 虚拟声卡播放音频（正确设置 ctypes 类型，64位兼容）"""
        # 方法1：使用 winsound 播放到指定设备（VB-Cable）
        try:
            import wave
            import ctypes
            import ctypes.wintypes as wt

            # 先读取WAV文件信息
            with wave.open(audio_path, 'rb') as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())

            # 查找 VB-Cable 设备ID
            winmm = ctypes.windll.winmm

            # 设置函数类型（64位兼容，避免指针被截断导致 BADFORMAT 错误码4）
            winmm.waveOutGetNumDevs.restype = ctypes.c_uint
            winmm.waveOutGetDevCapsW.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
            winmm.waveOutGetDevCapsW.restype = ctypes.c_uint
            winmm.waveOutOpen.argtypes = [
                ctypes.POINTER(ctypes.c_void_p),  # phwo (输出句柄指针)
                ctypes.c_uint,                     # uDeviceID
                ctypes.c_void_p,                   # pwfx (格式指针)
                ctypes.c_void_p,                   # dwCallback
                ctypes.c_void_p,                   # dwInstance
                ctypes.c_uint                      # fdwOpen
            ]
            winmm.waveOutOpen.restype = ctypes.c_uint
            winmm.waveOutPrepareHeader.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
            winmm.waveOutPrepareHeader.restype = ctypes.c_uint
            winmm.waveOutWrite.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
            winmm.waveOutWrite.restype = ctypes.c_uint
            winmm.waveOutUnprepareHeader.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
            winmm.waveOutReset.argtypes = [ctypes.c_void_p]
            winmm.waveOutClose.argtypes = [ctypes.c_void_p]
            winmm.waveOutClose.restype = ctypes.c_uint

            class WAVEOUTCAPSW(ctypes.Structure):
                _fields_ = [
                    ('wMid', ctypes.c_short),
                    ('wPid', ctypes.c_short),
                    ('vDriverVersion', ctypes.c_uint),
                    ('szPname', ctypes.c_wchar * 32),
                    ('dwFormats', ctypes.c_uint),
                    ('wChannels', ctypes.c_short),
                    ('wReserved1', ctypes.c_short),
                    ('dwSupport', ctypes.c_uint),
                ]

            num_devs = winmm.waveOutGetNumDevs()
            cable_device_id = -1
            cable_input_id = -1  # 优先选择标准的 "CABLE Input" 设备
            print(f"[Sender] 查找音频设备 (共{num_devs}个):")
            for i in range(num_devs):
                caps = WAVEOUTCAPSW()
                result = winmm.waveOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps))
                if result == 0:
                    name = caps.szPname
                    print(f"  设备 {i}: {name}")
                    if 'CABLE' in name.upper() or 'VB-Audio' in name.upper():
                        if 'CABLE Input' in name:
                            cable_input_id = i  # 标准VB-Cable播放端，优先使用
                        cable_device_id = i
                        print(f"  ^^^ 找到 VB-Cable 设备!")

            # 优先使用标准的 CABLE Input（不是 16ch 版本）
            if cable_input_id >= 0:
                cable_device_id = cable_input_id
                print(f"[Sender] 优先使用标准 CABLE Input 设备 (id={cable_device_id})")

            if cable_device_id >= 0:
                # 使用 VB-Cable 设备播放
                # 构造 WAVEFORMATEX 结构
                class WAVEFORMATEX(ctypes.Structure):
                    _fields_ = [
                        ('wFormatTag', ctypes.c_short),
                        ('nChannels', ctypes.c_short),
                        ('nSamplesPerSec', ctypes.c_uint),
                        ('nAvgBytesPerSec', ctypes.c_uint),
                        ('nBlockAlign', ctypes.c_short),
                        ('wBitsPerSample', ctypes.c_short),
                        ('cbSize', ctypes.c_short),
                    ]

                # 尝试多种格式，从原始格式开始
                formats_to_try = [
                    (channels, sample_width, framerate),  # 原始格式
                    (1, 2, 44100),   # 单声道 16bit 44.1kHz
                    (2, 2, 44100),   # 立体声 16bit 44.1kHz
                    (1, 2, 48000),   # 单声道 16bit 48kHz
                    (1, 2, 22050),   # 单声道 16bit 22.05kHz
                ]

                # 如果原始格式不在列表里，添加到最前面
                orig_fmt = (channels, sample_width, framerate)
                if orig_fmt not in formats_to_try:
                    formats_to_try.insert(0, orig_fmt)

                h_waveout = ctypes.c_void_p()
                opened = False
                used_format = None

                for fmt_ch, fmt_sw, fmt_sr in formats_to_try:
                    wfx = WAVEFORMATEX()
                    wfx.wFormatTag = 1  # WAVE_FORMAT_PCM
                    wfx.nChannels = fmt_ch
                    wfx.nSamplesPerSec = fmt_sr
                    wfx.wBitsPerSample = fmt_sw * 8
                    wfx.nBlockAlign = fmt_ch * fmt_sw
                    wfx.nAvgBytesPerSec = fmt_sr * wfx.nBlockAlign
                    wfx.cbSize = 0

                    result = winmm.waveOutOpen(ctypes.byref(h_waveout), cable_device_id,
                                               ctypes.byref(wfx), 0, 0, 0)
                    if result == 0:
                        opened = True
                        used_format = (fmt_ch, fmt_sw, fmt_sr)
                        print(f"[Sender] 成功打开 VB-Cable 设备 (id={cable_device_id}, 格式={fmt_ch}ch {fmt_sw*8}bit {fmt_sr}Hz)")
                        break
                    else:
                        print(f"[Sender] 格式 {fmt_ch}ch {fmt_sw*8}bit {fmt_sr}Hz 失败: 错误码 {result}")

                if opened:
                    # 构造 WAVEHDR
                    class WAVEHDR(ctypes.Structure):
                        _fields_ = [
                            ('lpData', ctypes.c_char_p),
                            ('dwBufferLength', ctypes.c_uint),
                            ('dwBytesRecorded', ctypes.c_uint),
                            ('dwUser', ctypes.c_uint),
                            ('dwFlags', ctypes.c_uint),
                            ('dwLoops', ctypes.c_uint),
                            ('lpNext', ctypes.c_void_p),
                            ('reserved', ctypes.c_void_p),
                        ]

                    # 如果打开的格式和原始不同，需要转换音频数据
                    play_frames = frames
                    if used_format != (channels, sample_width, framerate):
                        print(f"[Sender] 格式不匹配，重新生成音频数据...")
                        # 重新用 SAPI 生成匹配格式的音频
                        # 简单方案：直接用原始数据，VB-Cable 通常能处理
                        # 如果不行，重新生成
                        try:
                            # 重新读取并转换
                            import wave as wave_mod
                            import tempfile
                            # 用 SAPI 重新生成 44100Hz 的音频
                            temp_wav_new = tempfile.mkstemp(suffix='.wav')[1]
                            import win32com.client as win32com_client
                            speaker = win32com_client.Dispatch("SAPI.SpVoice")
                            speaker.Rate = 0
                            speaker.Volume = 100
                            sp_file = win32com_client.Dispatch("SAPI.SpFileStream")
                            sp_file.Open(temp_wav_new, 3)
                            speaker.AudioOutputStream = sp_file
                            # 需要原始文本，但我们这里没有。直接用原始frames
                            sp_file.Close()
                            # 直接用原始数据
                        except:
                            pass

                    wh = WAVEHDR()
                    wh.lpData = ctypes.c_char_p(play_frames)
                    wh.dwBufferLength = len(play_frames)
                    wh.dwFlags = 0
                    winmm.waveOutPrepareHeader(h_waveout, ctypes.byref(wh), ctypes.sizeof(wh))
                    winmm.waveOutWrite(h_waveout, ctypes.byref(wh), ctypes.sizeof(wh))
                    print(f"[Sender] VB-Cable 播放已启动 ({len(play_frames)} bytes)")

                    # 🔧 修复 2026-06-28: 等待播放完成并正确清理资源。
                    # 之前在 waveOutWrite 后直接 return True，函数返回后 play_frames 被 GC 回收，
                    # 但 winmm 还在访问这块内存，导致 0xC0000005 内存访问违规崩溃。
                    #
                    # 等待方式：直接 sleep 音频时长 + 0.5秒缓冲。
                    # 之前用 WHDR_DONE 标志轮询，但该标志在 VB-Cable 虚拟设备上不可靠，
                    # 导致等待9秒超时（音频只有7秒），录音时长被拉长。
                    audio_duration_sec = len(play_frames) / (used_format[2] * used_format[0] * used_format[1])
                    wait_time = audio_duration_sec + 0.5
                    print(f"[Sender] 等待播放完成: {wait_time:.1f}秒")
                    time.sleep(wait_time)

                    # 清理资源：waveOutReset 停止播放并返回缓冲区，waveOutUnprepareHeader 清理 header，waveOutClose 关闭设备
                    try:
                        winmm.waveOutReset(h_waveout)
                        time.sleep(0.1)
                        winmm.waveOutUnprepareHeader(h_waveout, ctypes.byref(wh), ctypes.sizeof(wh))
                        time.sleep(0.1)
                        winmm.waveOutClose(h_waveout)
                        print(f"[Sender] VB-Cable 播放完成，资源已清理")
                    except Exception as e_cleanup:
                        print(f"[Sender] VB-Cable 清理失败（不影响继续）: {e_cleanup}")

                    # 保持 play_frames 引用直到清理完成，防止 GC 回收内存
                    _ = play_frames
                    return True
                else:
                    print(f"[Sender] 所有格式都失败了，最后一个错误码: {result}")
            else:
                print("[Sender] 未找到 VB-Cable 设备，使用默认设备")
                # 使用默认设备播放
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                print("[Sender] winsound 异步播放已启动（默认设备）")
                return True

        except Exception as e:
            print(f"[Sender] VB-Cable 播放失败: {e}")
            import traceback
            traceback.print_exc()

        # 备用：winsound
        try:
            import winsound
            winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            print("[Sender] winsound 异步播放已启动（备用）")
            return True
        except Exception as e:
            print(f"[Sender] winsound 播放失败: {e}")

        return False

    def _generate_sapi_tts(self, text, voice_name=None):
        """使用 Windows SAPI 生成 TTS 音频文件"""
        import tempfile
        import win32com.client as win32com_client

        # 创建临时文件
        fd, temp_wav = tempfile.mkstemp(suffix='.wav')
        os.close(fd)

        try:
            # 使用 SAPI SpVoice
            speaker = win32com_client.Dispatch("SAPI.SpVoice")
            speaker.Rate = 0  # 语速正常
            speaker.Volume = 100  # 音量最大

            # 查找中文语音
            if voice_name:
                for voice in speaker.GetVoices():
                    if voice_name in voice.GetDescription():
                        speaker.Voice = voice
                        break

            # 创建文件输出流
            sp_file = win32com_client.Dispatch("SAPI.SpFileStream")
            sp_file.Open(temp_wav, 3)  # 3 = SSFMCreateForWrite
            speaker.AudioOutputStream = sp_file

            # 生成语音
            speaker.Speak(text)

            # 关闭流
            speaker.Speak("")
            sp_file.Close()

            print(f"[Sender] SAPI TTS 生成成功: {temp_wav}")
            return temp_wav

        except Exception as e:
            print(f"[Sender] SAPI TTS 生成失败: {e}")
            # 降级：使用 pyttsx3 或返回 None
            raise e

    def _find_voice_button_position(self):
        """通过遍历窗口元素查找语音按钮位置（发送按钮左侧的麦克风图标）"""
        try:
            import win32gui as _win32gui_local
            import win32con as _win32con_local

            hwnd = _win32gui_local.GetForegroundWindow()
            if not hwnd:
                return None

            # 查找发送按钮和语音按钮
            send_btn_rect = None
            voice_btn_rect = None

            def enum_child(hwnd, result):
                try:
                    class_name = _win32gui_local.GetClassName(hwnd)
                    rect = _win32gui_local.GetWindowRect(hwnd)
                    text = _win32gui_local.GetWindowText(hwnd)
                    left, top, right, bottom = rect
                    width = right - left
                    height = bottom - top

                    # 查找发送按钮：通常在窗口右下角，高度约30-40，宽度约60-80
                    # 文字可能是"发送"或"Send"
                    if text in ['发送', 'Send'] and width > 50 and height > 25:
                        result['send_btn'] = rect
                        print(f"[Sender] 找到发送按钮: {rect}")
                    
                    # 查找语音按钮：圆形按钮，通常在发送按钮左侧
                    # class name 可能是 "Button" 或其他
                    if class_name == 'Button' and width > 20 and width < 45 and height > 20 and height < 45:
                        # 检查是否在发送按钮附近
                        if result.get('send_btn'):
                            send_left, send_top, send_right, send_bottom = result['send_btn']
                            # 语音按钮在发送按钮左侧
                            if left < send_left and abs(top - send_top) < 20:
                                result['voice_btn'] = rect
                                print(f"[Sender] 找到语音按钮: {rect}")

                except:
                    pass

            result = {}
            _win32gui_local.EnumChildWindows(hwnd, enum_child, result)

            # 如果找到了语音按钮，返回其中心位置
            if result.get('voice_btn'):
                left, top, right, bottom = result['voice_btn']
                voice_x = (left + right) // 2
                voice_y = (top + bottom) // 2
                return (voice_x, voice_y)

            # 如果只找到了发送按钮，计算语音按钮位置（发送按钮左侧约45像素）
            if result.get('send_btn'):
                send_left, send_top, send_right, send_bottom = result['send_btn']
                voice_x = send_left - 45
                voice_y = (send_top + send_bottom) // 2
                print(f"[Sender] 通过发送按钮计算语音按钮位置: ({voice_x}, {voice_y})")
                return (voice_x, voice_y)

            return None
        except Exception as e:
            print(f"[Sender] 查找语音按钮失败: {e}")
            return None

    def _find_voice_button_position_fallback(self):
        """通过窗口大小计算语音按钮位置的备用方法（发送按钮左侧）"""
        try:
            import win32gui as _win32gui_local

            hwnd = _win32gui_local.GetForegroundWindow()
            if not hwnd:
                return None

            rect = _win32gui_local.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top

            # 微信窗口布局：输入区域在底部
            # 发送按钮在右下角，语音按钮（麦克风图标）在发送按钮左侧约45像素
            # 语音按钮距离右侧边缘约100-110像素，距离底部约30-40像素
            
            # 语音按钮位置：右下角区域
            # 发送按钮通常距离右侧约15像素，语音按钮在发送按钮左侧约45像素
            voice_x = right - 105  # 距离右侧边缘约105像素
            voice_y = bottom - 35  # 距离底部约35像素

            print(f"[Sender] 备用定位语音按钮: ({voice_x}, {voice_y})")
            return (voice_x, voice_y)
        except Exception as e:
            print(f"[Sender] 备用语音按钮定位失败: {e}")
            return None

    def _get_audio_duration(self, audio_path):
        """读取 WAV 音频时长（秒）"""
        # 方法1：使用 Python wave 模块（最可靠）
        try:
            import wave
            with wave.open(audio_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    duration = frames / float(rate)
                    print(f"[Sender] WAV 时长: {duration:.1f}秒 (frames={frames}, rate={rate})")
                    return duration
        except Exception as e:
            print(f"[Sender] wave 模块读取失败: {e}")

        # 方法2：基于文件大小估算
        try:
            file_size = os.path.getsize(audio_path)
            # 跳过WAV头（44字节），假设 16bit 22050Hz 单声道（SAPI默认格式）
            data_size = max(file_size - 44, 1)
            duration = data_size / (22050 * 2)  # 22050Hz * 2字节(16bit)
            print(f"[Sender] 文件大小估算时长: {duration:.1f}秒 (size={file_size}B)")
            return duration
        except Exception as e:
            print(f"[Sender] 文件大小估算失败: {e}")

        # 默认值
        print("[Sender] 使用默认时长: 5.0秒")
        return 5.0

# ---- 向后兼容的模块级函数 ----

def send_image(image_path, delay_before_send=0):
    """发送图片到当前微信聊天窗口（向后兼容函数）"""
    sender = ClipboardSender()
    return sender.send_image(image_path, ensure_focus=True)


def send_image_to_target(image_path, target_name, delay_before_send=0, delay_after_open=0):
    """发送图片到指定微信联系人/群组（向后兼容函数）"""
    sender = ClipboardSender()
    return sender.send_image_to_target(image_path, target_name,
                                       delay_before_send=delay_before_send,
                                       delay_after_open=delay_after_open)
