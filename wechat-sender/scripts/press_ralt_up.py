# -*- coding: utf-8 -*-
"""
独立的右Alt按键脚本 - 松开
使用 keybd_event + KEYEVENTF_EXTENDEDKEY + KEYEVENTF_KEYUP
通过 os.startfile 调用，完全脱离 Electron 进程树
"""
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# 必须设置 argtypes，否则64位系统 dwFlags 参数被截断
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
VK_RMENU = 0xA5

# 松开右Alt键（带 extended flag + keyup flag）
flags = KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP
user32.keybd_event(VK_RMENU, 0, flags, 0)
