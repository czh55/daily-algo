#!/usr/bin/env python3
"""校验所有已发布的题目页都是完整「变量语义法」精讲页。

用途：CI 和「提交前自检」。扫描 docs/archive/*.html，任何缺少精讲核心区块
（变量语义三句法 / 模拟答题者思考 / 落码步骤）的页面都会导致检查失败（退出码 1）。
这样可从机制上保证：不会再发布只有题面 + 官方代码的占位页（方案 A 的兜底防线）。

用法：
  python3 scripts/check_pages.py            # 校验全部归档页
  python3 scripts/check_pages.py 2026-07-15 # 只校验指定日期
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "docs" / "archive"

# 完整精讲页必须包含的核心区块标记（占位/自动出页会缺失这些）
REQUIRED = {
    "变量语义三句法": 'class="var-semantics"',
    "模拟答题者思考": 'class="thinking-steps"',
    "落码步骤": 'class="code-steps"',
}


def check_page(html: str) -> list:
    """返回缺失的精讲区块名列表（空列表表示完整）。"""
    return [name for name, marker in REQUIRED.items() if marker not in html]


def main(argv: list) -> int:
    if not ARCHIVE.exists():
        print(f"未找到归档目录：{ARCHIVE}")
        return 0

    wanted = set(argv)
    pages = sorted(
        p for p in ARCHIVE.glob("*.html")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem)
        and (not wanted or p.stem in wanted)
    )
    if not pages:
        print("没有可校验的归档页。")
        return 0

    failures = []
    for p in pages:
        missing = check_page(p.read_text(encoding="utf-8"))
        if missing:
            failures.append((p.name, missing))

    if failures:
        print(f"✗ 校验失败：{len(failures)}/{len(pages)} 个页面缺少「变量语义法」精讲区块：")
        for name, missing in failures:
            print(f"  - {name}：缺 {', '.join(missing)}")
        print("\n请按 COACH-VAR-SEMANTICS.md 为对应题目在 scripts/generate.py 的")
        print("VAR_SEMANTICS_DATA 补齐精讲后，用 --slug ... --force 重新生成该页。")
        return 1

    print(f"✓ 校验通过：{len(pages)} 个归档页均为完整「变量语义法」精讲。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
