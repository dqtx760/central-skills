# -*- coding: utf-8 -*-
"""
微信消息发送模块
通过 Windows API 模拟键盘操作实现微信消息的自动发送。

完整发送流程：
1. 激活微信窗口 Ctrl+Alt+W
2. 打开搜索框 Ctrl+F
3. 输入目标名称（键盘输入）
4. 进入聊天 Enter*2
5. 确保输入框焦点 Ctrl+End
6. @用户（可选）Shift+2 → 用户名 → Space*2
7. 输入消息内容（键盘输入）
8. 发送消息 Enter
9. 隐藏窗口 Ctrl+Alt+W
"""
import sys
import time
import io
import os
import random
from PIL import Image
import win32clipboard
import win32con
import win32gui
import win32api
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

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
    """将文件复制到剪贴板（用于发送文件/音频）"""
    import pythoncom
    from ctypes import wintypes
    
    # 关键修复：初始化 COM 环境
    try:
        pythoncom.CoInitialize()
    except Exception:
        # COM 可能已经初始化
        pass
    
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
    
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        # 设置文件拖放列表
        files = [file_path]
        # 使用 DROPFILES 结构
        offset = 20  # sizeof(DROPFILES) = 20 bytes
        length = sum(len(f.encode('utf-16-le')) + 2 for f in files) + 2
        buf = (ctypes.c_ubyte * (offset + length))()
        
        # DROPFILES header
        ctypes.memset(buf, 0, offset)
        # fWide = TRUE (Unicode)
        buf[4] = 1
        
        # 文件列表
        ptr = offset
        for f in files:
            fbytes = f.encode('utf-16-le') + b'\x00\x00'
            buf[ptr:ptr+len(fbytes)] = fbytes
            ptr += len(fbytes)
        # 终止符
        buf[ptr:ptr+2] = b'\x00\x00'
        
        win32clipboard.SetClipboardData(win32con.CF_HDROP, buf)
        print(f"[Sender] 剪贴板文件设置成功: {file_path}")
    except Exception as e:
        print(f"[Sender] 剪贴板文件设置失败: {e}", file=sys.stderr)
        raise
    finally:
        win32clipboard.CloseClipboard()

# ==================== Unicode SendInput 支持 ====================
# 使用 SendInput + KEYEVENTF_UNICODE 直接通过码点注入字符，绕过 IME
# 完整定义 INPUT 联合体（含 MOUSEINPUT/KEYBDINPUT/HARDWAREINPUT）以确保正确大小

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

def _send_unicode_char(ch):
    """通过 SendInput + KEYEVENTF_UNICODE 发送单个 Unicode 字符"""
    code = ord(ch)
    # Build key-down INPUT
    ki_down = _KEYBDINPUT(0, code, KEYEVENTF_UNICODE, 0, None)
    u_down = _INPUT_UNION()
    u_down.ki = ki_down
    inp_down = _INPUT(INPUT_KEYBOARD, u_down)
    # Build key-up INPUT
    ki_up = _KEYBDINPUT(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)
    u_up = _INPUT_UNION()
    u_up.ki = ki_up
    inp_up = _INPUT(INPUT_KEYBOARD, u_up)
    _sendinput(1, ctypes.byref(inp_down), ctypes.sizeof(_INPUT))
    _sendinput(1, ctypes.byref(inp_up), ctypes.sizeof(_INPUT))


def _type_human_like(text):
    """模拟人类键盘输入文本，支持全 Unicode（中文/日文等）"""
    import random
    # 逐字符使用 SendInput + KEYEVENTF_UNICODE
    # 异常时静默回退（不会发送测试字符）
    for ch in text:
        try:
            _send_unicode_char(ch)
        except Exception:
            # Fallback: COM WScript.Shell.SendKeys
            try:
                from win32com.client import Dispatch
                wsh = Dispatch("WScript.Shell")
                wsh.SendKeys(ch)
            except Exception:
                # keybd_event（仅 ASCII）
                vk = ord(ch.upper()) if ch.isalpha() else ord(ch)
                user32.keybd_event(vk, 0, 0, 0)
                time.sleep(0.02)
                user32.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(random.uniform(0.01, 0.03))


# ==================== 虚拟键码操作 ====================

def _press_key(vk_code, delay=0.05):
    """按下并释放一个虚拟键码"""
    user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.02)
    user32.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(delay)


def _press_key_down(vk_code):
    """按下键（不释放）"""
    user32.keybd_event(vk_code, 0, 0, 0)


def _press_key_up(vk_code):
    """释放键"""
    user32.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)


# ==================== 微信操作 ====================

def _activate_wechat():
    """步骤1：激活微信窗口 Ctrl+Alt+W"""
    print("[Sender] [步骤1] 激活微信窗口 Ctrl+Alt+W")
    _press_key_down(win32con.VK_CONTROL)
    _press_key_down(win32con.VK_MENU)
    _press_key(0x57)  # W
    _press_key_up(win32con.VK_MENU)
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.8))


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
    """步骤3：键盘输入目标名称"""
    preview = target_name[:60] + '...' if len(target_name) > 60 else target_name
    print(f"[Sender] [步骤3] 键盘输入目标名称（Unicode SendInput）: {preview}（共{len(target_name)}字符）")
    _type_human_like(target_name)
    time.sleep(_random_delay(0.5))
    print("[Sender] [步骤3] 目标名称已输入")


def _select_first_search_result():
    """选择搜索结果中的第一个项目（向下箭头）"""
    print("[Sender] [步骤3.5] 选择第一个搜索结果（向下箭头）")
    _press_key(win32con.VK_DOWN, 0.3)
    time.sleep(_random_delay(0.5))


def _enter_chat():
    """步骤4：进入聊天 Enter x2"""
    print("[Sender] [步骤4] 进入聊天 Enter x2")
    _press_key(win32con.VK_RETURN, 0.3)
    time.sleep(0.4)
    _press_key(win32con.VK_RETURN, 0.3)
    time.sleep(_random_delay(1.2))


def _ensure_input_focus():
    """步骤5：确保输入框焦点 Ctrl+End"""
    print("[Sender] [步骤5] 确保输入框焦点 Ctrl+End")
    _press_key_down(win32con.VK_CONTROL)
    _press_key(0x23)  # End key
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.3))
    print("[Sender] [步骤5] 输入框焦点已确认")


def _at_user(display_name):
    """步骤6：@用户 Shift+2 → 用户名 → Space*2（剪贴板粘贴方式）"""
    print(f"[Sender] [步骤6] @用户: {display_name}（剪贴板粘贴）")
    # 输入 @ 符号（Shift+2）
    _press_key_down(win32con.VK_SHIFT)
    _press_key(0x32)  # 2
    _press_key_up(win32con.VK_SHIFT)
    time.sleep(_random_delay(0.1))
    
    # 输入用户名（使用剪贴板粘贴）
    _set_clipboard_text(display_name)
    _press_key_down(win32con.VK_CONTROL)
    _press_key(0x56)  # V
    _press_key_up(win32con.VK_CONTROL)
    time.sleep(_random_delay(0.3))
    
    # 输入空格分隔
    _press_key(0x20, 0.1)  # Space
    _press_key(0x20, 0.1)  # Space
    print("[Sender] [步骤6] @用户完成")


def _at_user_keyboard(display_name):
    """步骤6（键盘输入方式）：@用户 Shift+2 → 等待200ms → 输入昵称 → 等待500ms → Enter
    
    模拟真实的键盘输入流程：
    1. 按下 Shift+2 输入 @ 符号
    2. 等待 200ms 让微信弹出 @ 选择列表
    3. 逐字符键盘输入昵称
    4. 等待 500ms 让微信匹配并选中用户
    5. 按 Enter 确认选择
    
    相比剪贴板粘贴方式，这种方式更接近真实用户操作，
    能更好地触发微信的 @ 提醒功能。
    """
    print(f"[Sender] [步骤6] @用户: {display_name}（模拟键盘输入）")
    
    # 1. 输入 @ 符号（Shift+2）
    _press_key_down(win32con.VK_SHIFT)
    _press_key(0x32)  # 2
    _press_key_up(win32con.VK_SHIFT)
    
    # 2. 等待 200ms 让微信弹出 @ 选择列表
    time.sleep(0.2)
    
    # 3. 逐字符键盘输入昵称（模拟人类输入节奏）
    _type_human_like(display_name)
    
    # 4. 等待 500ms 让微信匹配并选中用户
    time.sleep(0.5)
    
    # 5. 按 Enter 确认选择
    _press_key(win32con.VK_RETURN, 0.1)
    
    print("[Sender] [步骤6] @用户完成")


def _type_message(text):
    """步骤7：键盘输入消息内容"""
    preview = text[:80] + '...' if len(text) > 80 else text
    print(f"[Sender] [步骤7] 键盘输入消息内容（Unicode SendInput）: {preview}（共{len(text)}字符）")
    _type_human_like(text)
    time.sleep(_random_delay(0.5))


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
    微信消息发送器
    通过剪贴板 + 模拟键盘操作实现微信消息的自动发送。
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        print("[Sender] ClipboardSender 初始化完成")

    def send(self, text, ensure_focus=True):
        """
        发送文本消息到当前微信聊天窗口。

        Args:
            text: 要发送的文本内容
            ensure_focus: 是否先激活微信窗口

        Returns:
            bool: 发送是否成功
        """
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
            print(f"[Sender] send failed: {e}", file=sys.stderr)
            return False

    def send_to_target(self, text, target_name, at_user=None, keyboard_at=False):
        """
        发送文本消息到指定微信联系人/群组。

        完整流程：
        1. 激活微信窗口 Ctrl+Alt+W
        2. 打开搜索框 Ctrl+F
        3. 输入目标名称
        4. 进入聊天 Enter
        5. 确保输入框焦点 Ctrl+End
        6. @用户（可选）- 支持剪贴板粘贴或键盘输入方式
        7. 输入消息内容
        8. 发送消息 Enter
        9. 隐藏窗口 Ctrl+Alt+W

        Args:
            text: 要发送的文本内容
            target_name: 目标联系人名称或群名
            at_user: 可选，群聊中要 @的用户显示名
            keyboard_at: 可选，是否使用键盘输入方式@用户（Shift+2→等待200ms→输入昵称→等待500ms→Enter）

        Returns:
            bool: 发送是否成功
        """
        for attempt in range(self.max_retries + 1):
            try:
                print("[Sender] ========== 开始发送流程 ==========")
                print(f"[Sender] 目标: {target_name}, AT用户: {at_user}, 键盘@: {keyboard_at}")
                print(f"[Sender] 消息内容: {text[:50]}{'...' if len(text) > 50 else ''}")
                print(f"[Sender] --- 尝试 {attempt+1}/{self.max_retries+1} ---")

                # 关闭弹窗
                _close_popups()
                time.sleep(_random_delay(0.3))

                # 步骤1：激活微信窗口
                _activate_wechat()

                # 步骤2：打开搜索框
                _open_search()

                # 步骤3：输入目标名称
                _type_target_name(target_name)
                # 等待搜索结果加载完成
                time.sleep(_random_delay(1.5))

                # 步骤4：进入聊天 Enter
                _enter_chat()
                # 等待聊天窗口加载
                time.sleep(_random_delay(1.0))

                # 步骤5：确保输入框焦点
                _ensure_input_focus()

                # 步骤6：@用户（可选）
                if at_user and str(at_user).strip():
                    if keyboard_at:
                        _at_user_keyboard(str(at_user).strip())
                    else:
                        _at_user(str(at_user).strip())

                # 步骤7：输入消息内容
                _type_message(text)

                # 步骤8：发送消息
                _send_message()

                # 步骤9：隐藏窗口
                _hide_wechat()

                print("[Sender] ========== 发送成功 ==========")
                print(f"[Sender] 发送到目标会话: {target_name}")
                return True

            except Exception as e:
                print(f"[Sender] !! 异常 (attempt {attempt+1}): {e}")
                time.sleep(_random_delay(0.5))

        print("[Sender] !! 所有重试次数耗尽，发送失败")
        return False

    def send_image(self, image_path, ensure_focus=True):
        """
        发送图片到当前微信聊天窗口。

        Args:
            image_path: 图片文件路径
            ensure_focus: 是否先激活微信窗口

        Returns:
            bool: 发送是否成功
        """
        try:
            if not os.path.isfile(image_path):
                print(f"[Sender] 图片文件不存在: {image_path}", file=sys.stderr)
                return False

            print("[Sender] ========== 开始发送图片 ==========")
            print(f"[Sender] 图片路径: {image_path}")

            if ensure_focus:
                _activate_wechat()

            _ensure_input_focus()

            # 设置剪贴板图片
            print("[Sender] 设置剪贴板图片...")
            _set_clipboard_image(image_path)
            time.sleep(_random_delay(0.3))

            # Ctrl+V 粘贴
            print("[Sender] 粘贴图片 Ctrl+V")
            _press_key_down(win32con.VK_CONTROL)
            _press_key(0x56)  # V
            _press_key_up(win32con.VK_CONTROL)
            time.sleep(_random_delay(0.5))

            # 发送
            _send_message()
            _hide_wechat()

            print("[Sender] ========== 图片发送成功 ==========")
            return True
        except Exception as e:
            print(f"[Sender] send_image failed: {e}", file=sys.stderr)
            return False

    def send_image_to_target(self, image_path, target_name, at_user=None, delay_before_send=0, delay_after_open=0):
        """
        发送图片到指定微信联系人/群组。

        Args:
            image_path: 图片文件路径
            target_name: 目标联系人名称或群名
            at_user: 可选，群聊中要 @的用户显示名
            delay_before_send: 粘贴后发送前的延迟（秒）
            delay_after_open: 打开聊天窗口后的延迟（秒）

        Returns:
            bool: 发送是否成功
        """
        for attempt in range(self.max_retries + 1):
            try:
                if not os.path.isfile(image_path):
                    print(f"[Sender] 图片文件不存在: {image_path}", file=sys.stderr)
                    return False

                print("[Sender] ========== 开始发送图片 ==========")
                print(f"[Sender] 目标: {target_name}, AT用户: {at_user}")
                print(f"[Sender] 图片路径: {image_path}")
                print(f"[Sender] --- 尝试 {attempt+1}/{self.max_retries+1} ---")

                # 关闭弹窗
                _close_popups()
                time.sleep(_random_delay(0.3))

                # 步骤1：激活微信窗口
                _activate_wechat()

                # 步骤2：打开搜索框
                _open_search()

                # 步骤3：输入目标名称
                _type_target_name(target_name)
                # 等待搜索结果加载完成
                time.sleep(_random_delay(1.5))

                # 步骤4：进入聊天 Enter
                _enter_chat()
                # 等待聊天窗口加载
                time.sleep(_random_delay(1.0))

                if delay_after_open > 0:
                    time.sleep(delay_after_open)

                # 步骤5：确保输入框焦点
                _ensure_input_focus()
                time.sleep(_random_delay(0.3))

                # 获取图片大小，根据文件大小动态调整等待时间
                image_size = os.path.getsize(image_path)
                image_size_mb = image_size / (1024 * 1024)
                print(f"[Sender] 图片大小: {image_size_mb:.2f}MB")
                
                # 设置剪贴板图片
                print("[Sender] 设置剪贴板图片...")
                _set_clipboard_image(image_path)
                # 根据文件大小调整等待时间：每MB增加0.5秒，至少0.5秒
                copy_wait = max(0.5, image_size_mb * 0.5)
                time.sleep(_random_delay(copy_wait))

                # Ctrl+V 粘贴
                print("[Sender] 粘贴图片 Ctrl+V")
                _press_key_down(win32con.VK_CONTROL)
                _press_key(0x56)  # V
                _press_key_up(win32con.VK_CONTROL)
                # 粘贴后等待时间：每MB增加1秒，至少1.5秒
                paste_wait = max(1.5, image_size_mb * 1.0)
                time.sleep(_random_delay(paste_wait))  # 根据文件大小动态调整等待时间

                # 然后@用户（如果需要）
                if at_user and str(at_user).strip():
                    print("[Sender] @用户...")
                    # 先输入一个空格
                    _press_key(0x20)  # Space
                    time.sleep(_random_delay(0.1))
                    _at_user(str(at_user).strip())
                    time.sleep(_random_delay(0.3))

                if delay_before_send > 0:
                    time.sleep(delay_before_send)

                # 发送
                _send_message()
                _hide_wechat()

                print("[Sender] ========== 图片发送成功 ==========")
                return True

            except Exception as e:
                print(f"[Sender] !! 异常 (attempt {attempt+1}): {e}")
                time.sleep(_random_delay(0.5))

        print("[Sender] !! 所有重试次数耗尽，图片发送失败")
        return False

    def send_file_to_target(self, file_path, target_name, at_user=None):
        """
        发送文件（包括音频）到指定微信联系人/群组。

        Args:
            file_path: 文件路径
            target_name: 目标联系人名称或群名
            at_user: 可选，群聊中要 @的用户显示名

        Returns:
            bool: 发送是否成功
        """
        # 发送前验证文件
        if not os.path.isfile(file_path):
            print(f"[Sender] 文件不存在: {file_path}", file=sys.stderr)
            return False

        # 检查文件可读性
        if not os.access(file_path, os.R_OK):
            print(f"[Sender] 文件不可读（权限不足）: {file_path}", file=sys.stderr)
            return False

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        ext = os.path.splitext(file_path)[1].lower()

        # 文件类型提示
        if ext and ext not in SUPPORTED_EXTENSIONS:
            print(f"[Sender] 警告: 文件类型 {ext} 可能不被微信支持，尝试发送中...")

        # 大文件警告
        if file_size_mb > 100:
            print(f"[Sender] 警告: 文件较大 ({file_size_mb:.1f}MB)，微信可能拒绝接收")

        print(f"[Sender] 文件类型: {ext or '未知'}, 大小: {file_size_mb:.2f}MB")

        for attempt in range(self.max_retries + 1):
            try:
                print("[Sender] ========== 开始发送文件 ==========")
                print(f"[Sender] 目标: {target_name}, AT用户: {at_user}")
                print(f"[Sender] 文件路径: {file_path}")
                print(f"[Sender] --- 尝试 {attempt+1}/{self.max_retries+1} ---")

                # 关闭弹窗
                _close_popups()
                time.sleep(_random_delay(0.3))

                # 步骤1：激活微信窗口
                _activate_wechat()

                # 步骤2：打开搜索框
                _open_search()

                # 步骤3：输入目标名称
                _type_target_name(target_name)
                # 等待搜索结果加载完成
                time.sleep(_random_delay(1.5))

                # 步骤4：进入聊天 Enter
                _enter_chat()
                # 等待聊天窗口加载
                time.sleep(_random_delay(1.0))

                # 步骤5：确保输入框焦点
                _ensure_input_focus()
                time.sleep(_random_delay(0.3))

                # 【重要】先不@用户，只发送文件，确保文件能正确发送
                print(f"[Sender] 文件大小: {file_size_mb:.2f}MB")
                
                # 设置剪贴板文件
                print("[Sender] 设置剪贴板文件...")
                _set_clipboard_file(file_path)
                # 根据文件大小调整等待时间：每MB增加0.5秒，至少0.5秒
                copy_wait = max(0.5, file_size_mb * 0.5)
                time.sleep(_random_delay(copy_wait))

                # Ctrl+V 粘贴文件
                print("[Sender] 粘贴文件 Ctrl+V")
                _press_key_down(win32con.VK_CONTROL)
                _press_key(0x56)  # V
                _press_key_up(win32con.VK_CONTROL)
                # 粘贴后等待时间：每MB增加1秒，至少1.5秒
                paste_wait = max(1.5, file_size_mb * 1.0)
                time.sleep(_random_delay(paste_wait))  # 根据文件大小动态调整等待时间

                # 然后@用户（如果需要）
                if at_user and str(at_user).strip():
                    print("[Sender] @用户...")
                    # 先输入一个空格
                    _press_key(0x20)  # Space
                    time.sleep(_random_delay(0.1))
                    _at_user(str(at_user).strip())
                    time.sleep(_random_delay(0.3))

                # 发送
                _send_message()
                _hide_wechat()

                print("[Sender] ========== 文件发送成功 ==========")
                return True

            except Exception as e:
                print(f"[Sender] !! 异常 (attempt {attempt+1}): {e}")
                time.sleep(_random_delay(0.5))

        print("[Sender] !! 所有重试次数耗尽，文件发送失败")
        return False


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
