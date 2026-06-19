"""
Gemini 生图后端 —— ian-xiaohei-illustrations skill 用

替代原 skill 假设的内置 `image_gen` 工具。通过逆向 gemini.google.com
网页接口调用 Nano Banana 生图能力（需账号已开通生图），生成后下载到本地。

鉴权依赖两个 cookie，从环境变量或 .env 文件读取：
    GEMINI_1PSID      = __Secure-1PSID
    GEMINI_1PSIDTS    = __Secure-1PSIDTS

获取方式见 README“配置鉴权”一节。
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model


# ============== 默认配置 ==============
SKILL_ROOT = Path(__file__).resolve().parent.parent
# 默认输出目录：优先读 .env 的 IMAGE_OUTPUT_DIR，没配就用固定路径
DEFAULT_OUTPUT_DIR = Path(
    os.getenv("IMAGE_OUTPUT_DIR") or r"D:\data\images\Article-illustrations"
)
DEFAULT_MODEL = Model.BASIC_PRO   # gemini-3-pro，免费档即可生图
REQUEST_TIMEOUT = 120
MAX_RETRY = 2
# ====================================


class GeminiAuthError(RuntimeError):
    """cookie 未配置或为空时抛出。"""


def _load_cookies_from_chrome(verbose: bool = False) -> tuple[str, str]:
    """
    从本地 Chrome 自动读取 gemini.google.com 的两个鉴权 cookie。
    需要先用 Chrome 登录过 Gemini，且 Chrome 没在运行（Windows 上
    Chrome 运行时会锁住 cookie 文件，读到的可能是旧值）。
    """
    try:
        import browser_cookie3 as bc
    except ImportError:
        raise GeminiAuthError(
            "未安装 browser-cookie3。运行：pip install \"gemini_webapi[browser]\""
        )

    try:
        cj = bc.chrome(domain_name="gemini.google.com")
    except Exception as e:
        raise GeminiAuthError(f"读取 Chrome cookie 失败: {e}\n")

    sid = sidts = ""
    for c in cj:
        if c.name == "__Secure-1PSID":
            sid = c.value
        elif c.name == "__Secure-1PSIDTS":
            sidts = c.value
    if not sid:
        raise GeminiAuthError(
            "Chrome 里没读到 __Secure-1PSID。请确认已用 Chrome 登录过 gemini.google.com。"
        )
    if verbose:
        print(f"[i] 已从 Chrome 自动读取 cookie（1PSIDTS={'有' if sidts else '无'}）")
    return sid, sidts


def _get_cookies(verbose: bool = True) -> tuple[str, str]:
    """
    获取 Gemini 鉴权 cookie，优先级：
      1. .env 里的 GEMINI_1PSID / GEMINI_1PSIDTS（显式配置，最可控）
      2. AUTO_READ_CHROME=1 时，从本地 Chrome 自动读（省去手动复制）
      3. 都没有就抛错
    """
    sid = os.getenv("GEMINI_1PSID", "").strip()
    sidts = os.getenv("GEMINI_1PSIDTS", "").strip()

    # 路径 1+2：.env 配了，直接用
    if sid and sidts:
        return sid, sidts

    # 路径 2：开启自动读 Chrome
    if os.getenv("AUTO_READ_CHROME", "0").strip() == "1":
        return _load_cookies_from_chrome(verbose=verbose)

    # 路径 3：都没有
    raise GeminiAuthError(
        "缺少 Gemini cookie。两种解决方式：\n"
        "  方式A（推荐，一劳永逸）：在 .env 里设 AUTO_READ_CHROME=1，\n"
        "    脚本会自动从 Chrome 读取（需先用 Chrome 登录 gemini.google.com）。\n"
        "  方式B（手动）：在 .env 设置\n"
        "    GEMINI_1PSID=__Secure-1PSID 的值\n"
        "    GEMINI_1PSIDTS=__Secure-1PSIDTS 的值\n"
        "获取方式：浏览器登录 gemini.google.com → F12 → Application → "
        "Cookies → 复制这两个 cookie 值。"
    )


# ============== PicGo 上传 ==============
def _picgo_enabled() -> bool:
    return os.getenv("PICGO_AUTO_UPLOAD", "0").strip() == "1"


def upload_to_picgo(image_path: Path | str, verbose: bool = True) -> str | None:
    """
    调用本地 PicGo 客户端的 HTTP 接口上传图片，返回外网 URL。

    前提：PicGo 客户端正在运行，且在「设置 → 设置 Server」里开启了 Server。
    上传走的是 PicGo 当前选中的图床，所以请先在客户端里选好目标图床。

    Args:
        image_path: 本地图片路径（必须是绝对路径，PicGo 不认相对路径）。
        verbose:   是否打印进度。

    Returns:
        上传成功返回外网 URL 字符串，失败返回 None。
    """
    import json
    import urllib.request
    import urllib.error

    image_path = Path(image_path).resolve()
    if not image_path.is_file():
        if verbose:
            print(f"[X] PicGo 上传跳过：文件不存在 {image_path}")
        return None

    server = os.getenv("PICGO_SERVER", "http://127.0.0.1:36677").strip().rstrip("/")
    token = os.getenv("PICGO_TOKEN", "").strip()

    payload = json.dumps({"list": [str(image_path)]}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-PicGo-Token"] = token

    if verbose:
        print(f"[>] 上传到 PicGo ({server}): {image_path.name}")

    try:
        req = urllib.request.Request(f"{server}/upload", data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        msg = str(e.reason) if hasattr(e, "reason") else str(e)
        print(f"[X] PicGo 连接失败（确认客户端已开启 Server？）: {msg}")
        return None
    except Exception as e:
        print(f"[X] PicGo 上传异常: {e}")
        return None

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print(f"[X] PicGo 返回非 JSON: {body[:200]}")
        return None

    if not data.get("success"):
        print(f"[X] PicGo 上传失败: {data}")
        return None

    result = data.get("result") or []
    if not result:
        print(f"[X] PicGo 未返回 URL: {data}")
        return None

    url = result[0] if isinstance(result, list) else result
    if verbose:
        print(f"[OK] 外链: {url}")
    return url


async def _build_client(verbose: bool = True) -> GeminiClient:
    sid, sidts = _get_cookies(verbose=verbose)
    client = GeminiClient(sid, sidts)
    await client.init(
        timeout=REQUEST_TIMEOUT,
        auto_close=False,
        auto_refresh=True,
    )
    return client


def _ensure_generate_keyword(prompt: str) -> str:
    """Gemini 只在 prompt 含 generate 类字眼时才返回 AI 生成图，
    否则会返回网图（WebImage）。这里做兜底。"""
    keywords = ("generate", "draw", "生成", "画", "创建", "绘制")
    if any(kw in prompt.lower() for kw in keywords):
        return prompt
    return "Generate one image. " + prompt


async def generate_image(
    prompt: str,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    filename: str | None = None,
    model=DEFAULT_MODEL,
    max_retry: int = MAX_RETRY,
    verbose: bool = True,
) -> list[Path]:
    """
    用 Gemini 生成图片并保存到本地。

    Args:
        prompt:    生图提示词（建议直接套 references/prompt-template.md）。
        output_dir: 保存目录，不存在自动创建。
        filename:  文件名。None 则按时间戳自动生成。
        model:     gemini_webapi 模型常量，默认 Model.BASIC_PRO。
        max_retry: 生图失败时的重试次数。
        verbose:   是否打印进度。

    Returns:
        已保存文件路径列表（一张请求可能返回多张图）。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt = _ensure_generate_keyword(prompt)
    client = await _build_client()

    last_err: Exception | None = None
    for attempt in range(1, max_retry + 2):
        try:
            if verbose:
                print(f"[>] 第 {attempt}/{max_retry + 1} 次请求生图...")
            resp = await client.generate_content(prompt, model=model)
            break
        except Exception as e:
            last_err = e
            if verbose:
                print(f"[!] 第 {attempt} 次失败: {e}")
            if attempt <= max_retry:
                await asyncio.sleep(2 * attempt)
    else:
        raise RuntimeError(f"生图重试 {max_retry + 1} 次仍失败: {last_err}")

    if not resp.images:
        msg = resp.text or "(空)"
        print(f"[!] 本次未返回图片。模型文本回复:\n{msg[:500]}")
        return []

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved: list[Path] = []
    for i, img in enumerate(resp.images):
        fname = filename if (filename and len(resp.images) == 1) else f"{ts}_{i}.png"
        if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
            fname += ".png"
        try:
            returned = await img.save(path=str(output_dir), filename=fname, verbose=verbose)
            p = Path(returned)
            saved.append(p)
            if verbose:
                print(f"[OK] 已保存: {p}")
            if _picgo_enabled():
                upload_to_picgo(p, verbose=verbose)
        except Exception as e:
            print(f"[X] 第 {i} 张保存失败: {e}")
    return saved


async def edit_image(
    edit_prompt: str,
    source_image: Path | str,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    filename: str | None = None,
    model=DEFAULT_MODEL,
    verbose: bool = True,
) -> list[Path]:
    """
    上传一张本地图片，让 Gemini 按指令编辑后下载。
    用于 skill 的“去标题 / 增强怪诞感”局部编辑流程。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    src = str(source_image)
    if not Path(src).is_file():
        raise FileNotFoundError(f"源图不存在: {src}")

    client = await _build_client()
    resp = await client.generate_content(edit_prompt, files=[src], model=model)

    saved: list[Path] = []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, img in enumerate(resp.images):
        fname = filename if (filename and len(resp.images) == 1) else f"{ts}_edit_{i}.png"
        if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
            fname += ".png"
        returned = await img.save(path=str(output_dir), filename=fname, verbose=verbose)
        p = Path(returned)
        saved.append(p)
        if verbose:
            print(f"[OK] 已保存: {p}")
        if _picgo_enabled():
            upload_to_picgo(p, verbose=verbose)
    return saved


# ============== 命令行入口 ==============
async def _cli():
    import argparse

    p = argparse.ArgumentParser(
        description="ian-xiaohei-illustrations 的 Gemini 生图后端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            '  python gemini_image_gen.py gen "生成一只赛博朋克猫"\n'
            '  python gemini_image_gen.py gen prompt.txt -o ./out\n'
            '  python gemini_image_gen.py edit "去掉左上角标题" -i old.png'
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("gen", help="文生图")
    p_gen.add_argument("prompt", help='生图提示词，或用 @文件路径 从文件读取')
    p_gen.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT_DIR), help="保存目录")
    p_gen.add_argument("--name", default=None, help="自定义文件名(不含扩展名)")

    p_edit = sub.add_parser("edit", help="图生图(局部编辑)")
    p_edit.add_argument("prompt", help="编辑指令")
    p_edit.add_argument("-i", "--input", required=True, help="源图路径")
    p_edit.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT_DIR), help="保存目录")
    p_edit.add_argument("--name", default=None, help="自定义文件名(不含扩展名)")

    p_up = sub.add_parser("upload", help="单独把本地图片传 PicGo（不生图）")
    p_up.add_argument("image", help="本地图片路径")
    p_up.add_argument("--server", default=None, help="覆盖 .env 里的 PICGO_SERVER")
    p_up.add_argument("--token", default=None, help="覆盖 .env 里的 PICGO_TOKEN")

    args = p.parse_args()

    # 支持 @file 形式从文件读 prompt（skill 生成的提示词通常较长）
    def resolve_prompt(s: str) -> str:
        if s.startswith("@") and Path(s[1:]).is_file():
            return Path(s[1:]).read_text(encoding="utf-8").strip()
        return s

    if args.cmd == "gen":
        await generate_image(
            resolve_prompt(args.prompt),
            output_dir=args.output,
            filename=args.name,
        )
    elif args.cmd == "edit":
        await edit_image(
            resolve_prompt(args.prompt),
            source_image=args.input,
            output_dir=args.output,
            filename=args.name,
        )
    elif args.cmd == "upload":
        if args.server:
            os.environ["PICGO_SERVER"] = args.server
        if args.token is not None:
            os.environ["PICGO_TOKEN"] = args.token
        upload_to_picgo(args.image)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        sys.argv.extend(["--help"])
    asyncio.run(_cli())
