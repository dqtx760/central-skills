---
name: "wechat-sender"
description: "通过 Python 脚本自动发送微信消息（文本/图片/文件/语音）到指定联系人或群组。当用户要求发送微信消息、通知微信联系人、@群成员、推送文件/图片/语音到微信时调用。"
---

# 微信消息发送器 (WeChat Sender)

基于 `wechat_sender_fixed.py` + `wechat_send_cli.py` 的微信自动化发送能力。通过模拟键盘快捷键 (Ctrl+Alt+W / Ctrl+F / Ctrl+V / 右Alt 等) + 剪贴板操作驱动 PC 微信客户端完成消息发送。

## 适用场景 (When to Invoke)

当用户出现以下意图时调用本 SKILL：
- "给 XXX 发微信说 ……" / "微信通知 XXX" / "发消息到 XXX 群"
- "把这份文件/图片发到微信" / "微信传文件给 XXX"
- "@ XXX 群里的 XXX" / "群内 at 某人"
- "发一条语音到微信" / "用微信语音播报 ……"

## 前置条件 (Prerequisites)

- **操作系统**：仅支持 Windows（依赖 win32 API、ctypes、SAPI）
- **微信客户端**：PC 版微信已登录，且快捷键 `Ctrl+Alt+W`（呼出/隐藏主窗口）、`Ctrl+F`（搜索）保持默认未改动
- **Python 环境**：已安装 `pywin32`、`Pillow`；发送语音还需 `pycaw` + 已安装 **VB-Cable 虚拟声卡**
- **脚本位置**：`wechat_sender_fixed.py` 与 `wechat_send_cli.py` 必须在同一目录
- **运行上下文**：必须在桌面会话中运行（不能在 service/无桌面环境），否则窗口激活与按键模拟都会失败

## 核心脚本路径

```
<项目根目录>/wechat_sender_fixed.py   # 核心发送类 ClipboardSender
<项目根目录>/wechat_send_cli.py       # 命令行入口
```

调用时用 `python wechat_send_cli.py` 即可，无需直接调用 `wechat_sender_fixed.py`。

## 命令行调用方式 (CLI Usage)

工作目录需切换到脚本所在目录，或使用绝对路径。下文用 `python wechat_send_cli.py` 代指。

### 1. 发送文本消息

```bash
# 发送到指定联系人/群（推荐）
python wechat_send_cli.py --target="张三" "你好，请尽快回复"

# 通过 stdin 传入消息内容（适合长文本/含特殊字符）
echo "你好" | python wechat_send_cli.py --target="张三"

# 发送到当前已打开的聊天窗口（不搜索联系人）
python wechat_send_cli.py "你好"
```

### 2. 文本消息 + @群成员

```bash
# 默认剪贴板粘贴 @ 用户名（推荐，兼容中文输入法）
python wechat_send_cli.py --target="项目组" --atuser="李四" "收到通知"

# 退化用键盘逐字输入 @ 用户名（仅在剪贴板 @ 失败时使用）
python wechat_send_cli.py --target="项目组" --atuser="李四" --keyboard-at "收到通知"
```

### 3. 发送图片

```bash
python wechat_send_cli.py --target="张三" --image="C:/path/to/image.png"

# 发送到当前窗口
python wechat_send_cli.py --image="C:/path/to/image.png"
```

支持格式：jpg/jpeg/png/gif/bmp/webp/tiff。大图会按文件大小自动延长粘贴等待时间。

### 4. 发送文件（文档/音频/视频/压缩包等）

```bash
python wechat_send_cli.py --target="张三" --file="C:/path/to/report.pdf"
```

支持的扩展名（见 `SUPPORTED_EXTENSIONS`）：
- **文档**：pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv, rtf, odt, ods, odp
- **音频**：mp3, wav, aac, flac, ogg, wma, m4a
- **视频**：mp4, avi, mov, mkv, wmv, flv, webm
- **图片**：jpg, jpeg, png, gif, bmp, webp, tiff
- **压缩包**：zip, rar, 7z, tar, gz
- **其他**：apk, exe, msi, dmg

注意：文件超过 100MB 会提示发送较慢；超过 200MB 微信可能拒绝。`--file` 模式必须配合 `--target` 使用。

### 5. 发送语音消息

```bash
# 用 Windows SAPI TTS 生成中文语音并发送
python wechat_send_cli.py --target="张三" --voice-text="您好，这是一条语音提醒"

# 使用自定义 WAV 音频文件发送（跳过 TTS）
python wechat_send_cli.py --target="张三" --voice-text="占位文本" --audio-path="C:/path/to/voice.wav"
```

语音发送原理：通过 `pycaw` 临时把默认录音设备切到 **CABLE Output**，按住右 Alt 触发微信"按住说话"，再用 winmm 把音频播到 **CABLE Input**，微信即从 CABLE Output 录到该音频。发送完毕自动切回原录音设备。

**语音模式必须配合 `--target`**。要求：已安装 VB-Cable 虚拟声卡 + `pycaw` 包。

## 关键实现细节 (Important Implementation Notes)

调用方/二次开发者必读，避免踩坑：

1. **目标名称输入用剪贴板粘贴而非逐字符 SendInput**
   逐字符 Unicode SendInput 会激活微信中文输入法，导致右 Alt 被输入法拦截、无法触发语音录音。`_type_target_name` 已改用剪贴板 + Ctrl+V。

2. **进入聊天只按一次 Enter**
   按两次 Enter 会导致焦点丢失，右 Alt 无法触发录音。`_enter_chat` 只发一次 VK_RETURN。

3. **语音发送前必须重新 SetForegroundWindow**
   只检查前台不够，必须再次 `SetForegroundWindow` 重置微信内部焦点状态，右 Alt 才能触发"按住说话"。

4. **右 Alt 必须用 keybd_event + KEYEVENTF_EXTENDEDKEY**
   SendInput 方式不触发微信录音。`_send_vkey` 已强制设置 argtypes（64 位兼容，避免 dwFlags 被截断）。

5. **修饰键卡住会劫持键盘**
   Ctrl+Alt+W / Ctrl+F 之后 Ctrl/Alt 可能卡住，会让右 Alt 变成组合键。`_reset_keyboard_state` 用 keybd_event + SendInput 双重松开，最多 5 轮强制清除。

6. **VB-Cable 播放必须等待完成并清理资源**
   waveOutWrite 后若立即返回，`play_frames` 被 GC 回收会导致 0xC0000005 崩溃。`_play_audio_to_virtual_soundcard` 已 sleep 音频时长 + 0.5s 并按 reset → unprepare → close 顺序清理。

7. **启动自检录音设备**
   `ClipboardSender.__init__` 会调用 `_ensure_recording_device_not_cable`：若上次进程崩溃导致录音设备卡在 CABLE Output，自动切回真实麦克风。

8. **所有 print 强制 flush=True**
   防止进程崩溃时 stdout 缓冲区吞掉日志，已用 `functools.partial(print, flush=True)` 覆盖，并安装 `sys.excepthook` 捕获未处理异常。

9. **结构化错误码**
   文件发送抛出 `SendFileError` 子类，错误码格式 `ERR_<CATEGORY>_<NAME>`：
   - `ERR_WINDOW_NOT_FOUND` - 微信窗口未找到/未激活
   - `ERR_CLIPBOARD_FORMAT` - 剪贴板 CF_HDROP 格式设置失败
   - `ERR_CLIPBOARD_ACCESS` - 剪贴板访问失败
   - `ERR_PASTE_TIMEOUT` - 粘贴超时
   - `ERR_SEARCH_TARGET` - 搜不到目标联系人
   - `ERR_ENTER_CHAT` - 无法进入目标会话

   上层可据此给用户精确提示。

## 退出码 (Exit Codes)

| 退出码 | 含义 |
|--------|------|
| 0 | 发送成功 |
| 2 | 参数错误（缺 `--target` 或未提供文本） |
| 3 | ClipboardSender 导入失败（环境问题） |
| 4 | 发送失败（重试耗尽 / 微信未响应 / 异常） |
| 5 | 文件不存在或不可读 |

## Python 直接调用方式

如需在 Python 代码中直接调用（而非 CLI）：

```python
import sys
sys.path.insert(0, r"<脚本所在目录>")
from wechat_sender_fixed import ClipboardSender

sender = ClipboardSender(max_retries=2)

# 文本
sender.send_to_target("你好", "张三")
sender.send_to_target("收到", "项目组", at_user="李四")

# 图片
sender.send_image_to_target(r"C:\path\to\img.png", "张三")

# 文件
sender.send_file_to_target(r"C:\path\to\report.pdf", "张三")

# 语音（TTS）
sender.send_voice_to_target("这是一条语音提醒", "张三")

# 发送到当前已打开窗口
sender.send("你好", ensure_focus=True)
```

## 常见故障排查

| 现象 | 可能原因 | 处理 |
|------|---------|------|
| `ERR_WINDOW_NOT_FOUND` | 微信未登录/未启动 | 启动微信并登录后重试 |
| 文本发送成功但语音不录音 | 右 Alt 被输入法拦截 / 焦点不在输入框 | 确认微信快捷键默认；脚本已自动 SetForegroundWindow，若仍失败可手动点一下聊天窗口再试 |
| 发送后键盘失灵（所有输入变 Alt+组合） | 修饰键卡住 | 脚本已自动 `_reset_keyboard_state`；若仍卡住，按一下物理左 Alt/左 Ctrl 通常可解锁 |
| 语音变成空音频/环境音 | 录音设备未切到 CABLE Output | 检查 VB-Cable 是否安装；重启脚本会自检切回真实麦克风 |
| 文件粘贴不上 | 剪贴板 CF_HDROP 失效 | 检查文件路径是否含特殊字符；脚本用 GlobalAlloc 全局内存，正常情况下不会失效 |
| 进程崩溃 0xC0000005 | 多数发生在语音播放后未清理 winmm 资源 | 已修复，确保不私自删掉 `_play_audio_to_virtual_soundcard` 中的清理代码 |

## 依赖安装

```bash
pip install pywin32 Pillow pycaw
```

语音功能还需安装 [VB-Cable](https://vb-audio.com/Cable/) 虚拟声卡。
