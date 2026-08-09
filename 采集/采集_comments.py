#!/usr/bin/env python
"""
采集_comments.py — 短视频评论采集工具
用法: python 采集_comments.py <短视频链接>
输出: 同目录下 comments_{video_id}_{timestamp}.txt
"""

import re, sys, time, random
from datetime import datetime
from pathlib import Path

def parse_douyin_url(text: str) -> str | None:
    ok = re.search(r'video/(\d{19})', text)
    if ok: return ok.group(1)
    ok = re.search(r'(\d{19})', text)
    return ok.group(1) if ok else None

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("请先安装: pip install playwright && playwright install chromium")
    sys.exit(1)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def _fetch_comments(page, video_id, max_pages=30):
    """通过平台公开接口获取评论数据"""
    all_comments, seen = [], set()
    page.goto(f"https://www.douyin.com/video/{video_id}", wait_until="domcontentloaded", timeout=20000)
    time.sleep(random.uniform(2, 4))
    page.evaluate("window.scrollBy(0, 600)")
    time.sleep(random.uniform(1, 2))
    cursor, per_page = 0, 20
    for pg in range(max_pages):
        result = page.evaluate("""args => {
            const url = '/aweme/v1/web/comment/list/?aweme_id=' + args.id
                + '&cursor=' + args.cursor + '&count=' + args.count
                + '&item_type=0&version_code=170400&language=zh-Hans';
            return fetch(url, {credentials:'include'}).then(r => r.ok ? r.json() : null).catch(() => null);
        }""", {"id": video_id, "cursor": cursor, "count": per_page})
        if not result or result.get("status_code") != 0:
            break
        for c in (result.get("comments") or []):
            cid = str(c.get("cid", ""))
            if cid and cid not in seen:
                seen.add(cid)
                text = (c.get("text", "") or "").strip()
                if text and len(text) >= 2:
                    nick = (c.get("user") or {}).get("nickname", "")
                    digg = c.get("digg_count", 0) or 0
                    all_comments.append({"text": text, "user": nick, "digg": digg, "cid": cid})
        has_more = result.get("has_more", 0)
        cursor = result.get("cursor", cursor + per_page)
        if not has_more: break
        time.sleep(random.uniform(0.8, 2.0))
    return all_comments

def _fetch_dom(page, video_id, max_scrolls=20):
    """兜底：从 DOM 提取评论"""
    if f"/video/{video_id}" not in (page.url or ""):
        page.goto(f"https://www.douyin.com/video/{video_id}", wait_until="domcontentloaded", timeout=20000)
        time.sleep(random.uniform(2, 4))
    page.evaluate("window.scrollBy(0, 600)")
    time.sleep(1)
    seen, comments = set(), []
    for _ in range(max_scrolls):
        items = page.evaluate("""() => {
            const els = document.querySelectorAll('[class*="LqTo7UJT"], [class*="Sbe6bqNb"]');
            return Array.from(els).map(e => e.textContent.trim()).filter(t => t.length > 2);
        }""") or []
        for t in items:
            if t[:60] not in seen:
                seen.add(t[:60])
                comments.append({"text": t, "user": "", "digg": 0, "cid": f"dom_{hash(t) & 0xFFFFFFFF:08x}"})
        page.evaluate("window.scrollBy(0, 400)")
        time.sleep(random.uniform(1, 2))
    return comments

def main():
    if len(sys.argv) < 2:
        print("用法: python 采集_comments.py <短视频链接>")
        sys.exit(1)
    url = sys.argv[1]
    video_id = parse_douyin_url(url)
    if not video_id:
        print("无法解析视频ID")
        sys.exit(1)
    print(f"正在采集: {video_id}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800}, locale="zh-CN")
        ctx.add_init_script("""
            Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
            Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});
        """)
        page = ctx.new_page()
        comments = _fetch_comments(page, video_id)
        if len(comments) < 5:
            comments = _fetch_dom(page, video_id)
        browser.close()
    if not comments:
        print("未采集到评论")
        sys.exit(1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = Path.cwd() / f"comments_{video_id}_{timestamp}.txt"
    lines = [f"短视频评论 | {video_id} | 共 {len(comments)} 条 | 采集时间 {datetime.now().isoformat()}", ""]
    for c in comments:
        text = c.get("text", "")
        lines.append(text)
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"已保存到: {out_file}")
    print(f"共 {len(comments)} 条评论")

if __name__ == "__main__":
    main()
