# -*- coding: utf-8 -*-
"""
独立的右Alt按键脚本
被 wechat_sender_fixed.py 调用，以独立进程方式执行按键
避免 Electron 子进程会话导致 keybd_event 无法注入前台窗口
"""
import sys
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

# 必须设置 argtypes，否则64位系统 dwFlags 参数被截断
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
VK_RMENU = 0xA5

def press_ralt(down=True):
    flags = KEYEVENTF_EXTENDEDKEY
    if not down:
        flags |= KEYEVENTF_KEYUP
    user32.keybd_event(VK_RMENU, 0, flags, 0)

if __name__ == '__main__':
    # 参数：down/up
    action = sys.argv[1] if len(sys.argv) > 1 else 'down'
    if action == 'down':
        press_ralt(down=True)
    elif action == 'up':
        press_ralt(down=False)
    # 静默退出，不输出日志
