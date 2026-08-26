#!/usr/bin/env python3
"""校验站点完整性。

三类检查（CI 和「提交前自检」共用）：

1. **精讲完整性**：扫描 docs/archive/*.html，任何缺少精讲核心区块
   （变量语义三句法 / 模拟答题者思考 / 落码步骤）的页面都会导致失败（退出码 1）。
   这样可从机制上保证：不会再发布只有题面 + 官方代码的占位页（方案 A 的兜底防线）。

2. **首页一致性**：docs/index.html 与 data/history.json 对齐——
   - 首页出现的每个归档链接都有对应页面文件；
   - 每条历史记录都能在首页找到归档链接；
   - 首页「按题型归类」区块的每类数量与 history.json 聚合一致。

3. **题型配色完整性**：scripts/generate.py 的 TYPE_CLASS_MAP 中每个 class
   都在 docs/style.css 有对应的 .tag-xxx 样式定义，防止新题型标签无配色。

用法：
  python3 scripts/check_pages.py             # 全部三类校验
  python3 scripts/check_pages.py 2026-07-15  # 只校验指定日期的精讲完整性
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.generate import TYPE_CLASS_MAP

DOCS = ROOT / "docs"
ARCHIVE = DOCS / "archive"
DATA = ROOT / "data"
HISTORY_FILE = DATA / "history.json"
INDEX_FILE = DOCS / "index.html"
STYLE_FILE = DOCS / "style.css"

# 完整精讲页必须包含的核心区块标记（占位/自动出页会缺失这些）
REQUIRED = {
    "变量语义三句法": 'class="var-semantics"',
    "模拟答题者思考": 'class="thinking-steps"',
    "落码步骤": 'class="code-steps"',
}


def check_page(html: str) -> list:
    """返回缺失的精讲区块名列表（空列表表示完整）。"""
    return [name for name, marker in REQUIRED.items() if marker not in html]


def check_index_consistency(history: list) -> list:
    """首页一致性校验，返回 [(日期/题型, 问题描述)]。"""
    problems = []
    if not INDEX_FILE.exists():
        return [("index.html", "首页文件不存在")]

    index_html = INDEX_FILE.read_text(encoding="utf-8")

    # 1) 首页所有归档链接指向的文件必须存在
    for date_str in sorted(set(re.findall(r"archive/(\d{4}-\d{2}-\d{2})\.html", index_html))):
        if not (ARCHIVE / f"{date_str}.html").exists():
            problems.append((date_str, f"首页链接指向的 archive/{date_str}.html 不存在"))

    # 2) 每条历史记录都有归档页文件 + 首页链接
    for item in history:
        date_str = item.get("date", "")
        if not date_str:
            continue
        if not (ARCHIVE / f"{date_str}.html").exists():
            problems.append((date_str, f"归档页 archive/{date_str}.html 不存在"))
        if f"archive/{date_str}.html" not in index_html:
            problems.append((date_str, "首页缺少该题的归档链接"))

    # 3) 「按题型归类」区块数量与 history 聚合一致
    cards = re.findall(
        r'class="problem-type tag-[\w-]+">([^<]+)</span>\s*<span class="type-count">(\d+) 题</span>',
        index_html,
    )
    actual_counts = {name.strip(): int(count) for name, count in cards}
    expected_counts = Counter(item.get("type") or "未分类" for item in history)
    for tname in sorted(set(expected_counts) | set(actual_counts)):
        exp, act = expected_counts.get(tname, 0), actual_counts.get(tname, 0)
        if exp != act:
            problems.append((tname, f"归类数量不一致：首页 {act} 题，history {exp} 题"))

    return problems


def check_type_colors() -> list:
    """题型配色校验，返回 [(题型名, 问题描述)]。"""
    if not STYLE_FILE.exists():
        return [("style.css", "样式文件不存在")]
    css = STYLE_FILE.read_text(encoding="utf-8")
    return [
        (tname, f"样式缺失 .tag-{cls}")
        for tname, cls in TYPE_CLASS_MAP.items()
        if f".tag-{cls}" not in css
    ]


def main(argv: list) -> int:
    wanted = set(argv)
    failures = []
    pages = []

    # 1) 精讲完整性
    if not ARCHIVE.exists():
        print(f"未找到归档目录：{ARCHIVE}")
    else:
        pages = sorted(
            p for p in ARCHIVE.glob("*.html")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem)
            and (not wanted or p.stem in wanted)
        )
        for p in pages:
            missing = check_page(p.read_text(encoding="utf-8"))
            if missing:
                failures.append((p.name, "缺 " + ", ".join(missing)))

    # 2) 首页一致性 + 题型配色（仅全量校验，指定日期时跳过）
    if not wanted:
        history = None
        if HISTORY_FILE.exists():
            try:
                history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                failures.append(("history.json", f"JSON 解析失败：{e}"))
        else:
            failures.append(("history.json", "文件不存在，无法校验首页一致性"))

        if history is not None:
            failures.extend(check_index_consistency(history))
        failures.extend(check_type_colors())

    if failures:
        print(f"✗ 校验失败：{len(failures)} 个问题")
        for name, msg in failures:
            print(f"  - {name}：{msg}")
        print("\n请修复后重新运行 scripts/check_pages.py。")
        return 1

    msg = f"✓ 校验通过：{len(pages)} 个归档页均为完整「变量语义法」精讲。"
    if not wanted:
        msg += " 首页一致性 + 题型配色校验通过。"
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
