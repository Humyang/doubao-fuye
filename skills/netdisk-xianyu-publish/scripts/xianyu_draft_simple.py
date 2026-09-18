#!/usr/bin/env python3
"""闲鱼草稿（简化版）：上传封面图（传满）+ 填描述 + 填价格，保持窗口存活。

不处理商品分类、不点二维码——发布动作由用户完成。

用法:
  <XIANYU_MCP_ROOT>/.venv/bin/python xianyu_draft_simple.py \
      --project-root <XIANYU_MCP_ROOT> \
      --poster "/path/主图.png,/path/细节图1.png,/path/细节图2.png" \
      --description-file /path/description.txt \
      --price 2.99

参数:
  --project-root      xianyu-mcp 项目根目录（含 server.py / .venv / tools），必填或用环境变量 XIANYU_MCP_ROOT
  --poster            商品图片绝对路径，逗号分隔多张（尽量凑满 9 张），必填
  --description       描述文本；更推荐 --description-file
  --description-file  描述文本文件（UTF-8，整文件内容作为描述）
  --price             售价，默认 2.99
  --cookies           登录 Cookie 文件，默认 <project-root>/.cache/cookies/xianyu_cookies.json
  --no-keep-alive     不保持窗口存活（默认保持）
"""
import argparse
import os
import sys
import time
from pathlib import Path


def _detect_project_root(argv) -> Path:
    """优先 --project-root 参数，其次环境变量 XIANYU_MCP_ROOT。"""
    if "--project-root" in argv:
        i = argv.index("--project-root")
        if i + 1 < len(argv):
            return Path(argv[i + 1])
    env_root = os.environ.get("XIANYU_MCP_ROOT")
    if env_root:
        return Path(env_root)
    # 兜底：脚本与 server.py 同目录时，脚本在 <skill>/scripts/，向上两级找
    here = Path(__file__).resolve()
    for candidate in [here.parent.parent.parent, here.parent.parent]:
        if (candidate / "server.py").exists() and (candidate / "tools").exists():
            return candidate
    return Path.cwd()


def _ensure_venv_python(root: Path) -> None:
    venv_py = root / ".venv/bin/python"
    if venv_py.exists() and Path(venv_py).resolve() != Path(sys.executable).resolve():
        os.execv(str(venv_py), [str(venv_py)] + sys.argv)


def log(msg):
    print(f"[draft] {msg}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="闲鱼草稿（封面图传满+描述+价格）")
    ap.add_argument("--poster", required=True, help="商品图片绝对路径，逗号分隔多张")
    ap.add_argument("--description", default="", help="描述文本")
    ap.add_argument("--description-file", default="", help="描述文本文件（优先于 --description）")
    ap.add_argument("--price", type=float, default=2.99, help="售价，默认 2.99")
    ap.add_argument("--project-root", default="", help="xianyu-mcp 项目根目录")
    ap.add_argument("--cookies", default="", help="登录 Cookie 文件路径")
    ap.add_argument("--no-keep-alive", action="store_true", help="不保持窗口存活")
    args = ap.parse_args()

    root = Path(args.project_root) if args.project_root else _detect_project_root(sys.argv[1:])
    _ensure_venv_python(root)

    cookies = args.cookies or str(root / ".cache/cookies/xianyu_cookies.json")

    if args.description_file:
        description = Path(args.description_file).read_text(encoding="utf-8")
    else:
        description = args.description

    posters = [p.strip() for p in args.poster.split(",") if p.strip()]
    if not posters:
        log("未提供任何图片路径")
        return 1
    log(f"待上传图片数: {len(posters)}")

    sys.path.insert(0, str(root))
    from tools.xianyu_tools import FishClawTools  # noqa: E402

    log(f"项目根: {root}")
    log(f"Cookie 路径: {cookies}")
    t = FishClawTools(cookies_path=cookies)

    auth = t._ensure_logged_in()
    if auth is not None:
        log(f"进入登录流程: {auth}")
        if "成功" not in auth and "已登录" not in auth:
            log("登录未完成，退出")
            return 1
    log("登录态 OK")

    page = t._get_page()
    ok, msg, page = t._navigate_to_publish(page)
    log(f"进入发布页: {ok} {msg[:60]}")
    if not ok:
        return 1
    t._page = page

    # 上传全部封面图（传满）
    ok, msg = t._upload_image(page, posters)
    log(f"上传封面图: {ok} {msg[:80]}")
    if not ok:
        log("上传失败，继续（供排查）")

    # 填写描述（不处理分类、不点二维码）
    time.sleep(1.5)
    ok, msg = t._fill_text_field(page, description, mode="replace")
    log(f"填写描述: {ok} {msg[:60]}")

    ok, msg = t._fill_price(page, args.price)
    log(f"填写价格: {ok} {msg[:60]}")

    time.sleep(3)
    shot = t._take_screenshot(page, label="draft_item")
    log(f"截图: {shot}")

    if args.no_keep_alive:
        return 0

    try:
        while True:
            time.sleep(30)
            if not t._browser.is_connected():
                log("浏览器已关闭，退出")
                break
            if page.is_closed():
                log("页面已关闭，退出")
                break
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
