#!/usr/bin/env python3
"""
微信消息发送 CLI 工具
通过命令行参数或 stdin 接收消息内容，调用 ClipboardSender 发送到微信。

用法:
  # 发送文本到指定联系人
  echo "你好" | python wechat_send_cli.py --target=张三
  python wechat_send_cli.py --target=张三 "你好"

  # 发送文本并 @群成员
  echo "收到" | python wechat_send_cli.py --target=群名 --atuser=李四

  # 发送图片
  python wechat_send_cli.py --target=张三 --image=C:/path/to/image.png

  # 发送文件/音频
  python wechat_send_cli.py --target=张三 --file=C:/path/to/audio.mp3

  # 发送到当前窗口
  echo "你好" | python wechat_send_cli.py
"""
import sys
import os
from pathlib import Path

try:
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import functools
print = functools.partial(print, flush=True)

# 优先尝试导入修复版的 ClipboardSender
ClipboardSender = None
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from wechat_sender_fixed import ClipboardSender
    print("[wechat_send_cli] 使用修复版 wechat_sender_fixed.py")
except Exception as e:
    print(f"[wechat_send_cli] 尝试导入修复版失败: {e}", file=sys.stderr)
    try:
        from wechat_sender import ClipboardSender
        print("[wechat_send_cli] 使用原版 wechat_sender.py")
    except Exception as e:
        print(f"[wechat_send_cli] import failed: {e}", file=sys.stderr)


def main():
    # 解析参数：支持 --target=<sessionId>、--atuser=<displayName>、--image=<filepath>、--file=<filepath>、--keyboard-at、--voice-text=<text>、--audio-path=<filepath>
    target = None
    at_user = None
    image_path = None
    file_path = None
    keyboard_at = False
    voice_text = None
    audio_path = None
    args = []
    for a in sys.argv[1:]:
        if a.startswith('--target='):
            target = a.split('=', 1)[1]
        elif a.startswith('--atuser='):
            at_user = a.split('=', 1)[1]
        elif a.startswith('--image='):
            image_path = a.split('=', 1)[1]
        elif a.startswith('--file='):
            file_path = a.split('=', 1)[1]
        elif a.startswith('--voice-text='):
            voice_text = a.split('=', 1)[1]
        elif a.startswith('--audio-path='):
            audio_path = a.split('=', 1)[1]
        elif a == '--keyboard-at':
            keyboard_at = True
        else:
            args.append(a)

    if ClipboardSender is None:
        print("[wechat_send_cli] ClipboardSender not available", file=sys.stderr)
        sys.exit(3)

    sender = ClipboardSender()

    # 文件模式（包括音频）
    if file_path:
        # 解析相对路径为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        if not os.path.isfile(file_path):
            print(f"[wechat_send_cli] 文件不存在: {file_path}", file=sys.stderr)
            sys.exit(5)
        if not os.access(file_path, os.R_OK):
            print(f"[wechat_send_cli] 文件不可读（权限不足）: {file_path}", file=sys.stderr)
            sys.exit(5)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        ext = os.path.splitext(file_path)[1].lower()
        print(f"[wechat_send_cli] 文件: {os.path.basename(file_path)} ({ext or '无扩展名'}, {file_size_mb:.2f}MB)")
        if file_size_mb > 200:
            print(f"[wechat_send_cli] 警告: 文件超过 200MB，微信可能拒绝接收", file=sys.stderr)
        if target:
            try:
                ok = sender.send_file_to_target(str(file_path), target, at_user)
            except Exception as e:
                print(f"[wechat_send_cli] 发送失败: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.exit(4)
        else:
            print("[wechat_send_cli] file mode requires --target", file=sys.stderr)
            sys.exit(2)
        if ok:
            print("[wechat_send_cli] file sent")
            sys.exit(0)
        else:
            print("[wechat_send_cli] file send failed", file=sys.stderr)
            sys.exit(4)

    # 图片模式
    if image_path:
        # 解析相对路径为绝对路径
        if not os.path.isabs(image_path):
            image_path = os.path.abspath(image_path)
        if not os.path.isfile(image_path):
            print(f"[wechat_send_cli] image file not found: {image_path}", file=sys.stderr)
            sys.exit(5)
        if target:
            ok = sender.send_image_to_target(str(image_path), target, at_user)
        else:
            ok = sender.send_image(str(image_path), ensure_focus=True)
        if ok:
            print("[wechat_send_cli] image sent")
            sys.exit(0)
        else:
            print("[wechat_send_cli] image send failed", file=sys.stderr)
            sys.exit(4)

    # 语音模式
    if voice_text is not None:
        if not target:
            print("[wechat_send_cli] voice mode requires --target", file=sys.stderr)
            sys.exit(2)
        # 复用前面已创建的 sender 实例（避免重复创建 + 减少日志噪音）
        ok = sender.send_voice_to_target(voice_text, target, at_user, audio_path)
        if ok:
            print("[wechat_send_cli] voice sent")
            sys.exit(0)
        else:
            print("[wechat_send_cli] voice send failed", file=sys.stderr)
            sys.exit(4)

    # 文本模式：优先从 argv 获取文本，其次从 stdin
    text = None
    if len(args) > 0:
        text = " ".join(args)
    else:
        try:
            raw = sys.stdin.buffer.read()
            if raw and raw.strip():
                try:
                    text = raw.decode('utf-8')
                except UnicodeDecodeError:
                    text = raw.decode(sys.stdin.encoding or 'utf-8', errors='replace')
        except Exception:
            text = None

    if not text:
        print("[wechat_send_cli] no text provided", file=sys.stderr)
        sys.exit(2)

    if target:
        ok = sender.send_to_target(str(text), target, at_user, keyboard_at)
    else:
        ok = sender.send(str(text), ensure_focus=True)
    if ok:
        print("[wechat_send_cli] sent")
        sys.exit(0)
    else:
        print("[wechat_send_cli] send failed", file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()
