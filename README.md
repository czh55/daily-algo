# daily-algo - 每日算法题推荐网站

## 概述

基于 Cursor Automations 的全自动算法题推荐网站，每天早上 8:00 自动生成一道高频算法题，用**变量语义法**（Var-Semantics）讲解，部署到 GitHub Pages。

## 讲解方法论

每道题按 [COACH-VAR-SEMANTICS.md](https://github.com/chenzhiheng/bear_cursor/blob/main/algo-restore-2026/COACH-VAR-SEMANTICS.md) 结构输出：
1. **认型** — 题型 + 输入参数 + 核心变量列表
2. **模拟答题者思考** — 暴力 → 找重复 → 优化动机
3. **变量语义三句** — 定义/维护/更新
4. **落码步骤** — 编号清单
5. **代码实现** — Python + C++ 双语言
6. **常见坑 + 边界 Case**

## 项目结构

```
daily-algo/
├── docs/                   # GitHub Pages 根目录
│   ├── index.html          # 主页（今日推荐 + 归档列表）
│   ├── archive/            # 往期题目页面 (YYYY-MM-DD.html)
│   ├── style.css           # 样式表
│   └── .nojekyll           # 禁用 Jekyll
├── scripts/
│   ├── generate.py         # 主生成脚本（选题 + 渲染 HTML）
│   └── leetcode_api.py     # LeetCode GraphQL API 封装
├── data/
│   ├── problem_pool.json   # 候选题库：LeetCode 前 200 题（选题去重轮换来源）
│   ├── bank.json           # 13 道核心题型的元数据
│   └── history.json        # 推荐历史记录
├── templates/
│   └── problem.html        # 题目页面 HTML 模板
└── .github/workflows/
    └── pages.yml           # 备用 CI 部署
```

## 使用方式

### 本地生成

```bash
# 生成今日题目（从题库选）
python3 scripts/generate.py --bank

# 预览（不写入文件）
python3 scripts/generate.py --bank --dry-run

# 列出所有题库题目
python3 scripts/generate.py --list

# 指定题目
python3 scripts/generate.py --slug=two-sum
```

### Cursor Automation（推荐）

Automation 配置每天 8:00 AM 触发 Agent，Agent 执行：
1. 运行 `python3 scripts/generate.py --bank` 生成今日题目
2. `git add -A && git commit -m "daily: YYYY-MM-DD 算法推荐"`
3. `git push origin main`

GitHub Pages 自动构建并更新网站。

## 题库

候选题库是 **LeetCode 前 200 题**（`data/problem_pool.json`）。脚本按题号顺序每天推荐一道没讲过的题，约 200 天内不重复；全部讲完后按「最久未推荐」轮换。

其中 13 道核心题型已内置完整的「变量语义法」精讲（见下表）；其余题目在被选中时会实时拉取 LeetCode 官方中文题面 + 官方代码自动出页。

13 道核心题型（覆盖全部变量语义方法）：

| # | 题目 | 题型 | 难度 |
|---|------|------|------|
| 560 | 和为 K 的子数组 | 前缀和+哈希 | 中等 |
| 239 | 滑动窗口最大值 | 固定滑窗最值 | 困难 |
| 76 | 最小覆盖子串 | 可变滑窗 | 困难 |
| 42 | 接雨水 | 单调栈 | 困难 |
| 206 | 反转链表 | 链表指针 | 简单 |
| 146 | LRU 缓存 | 设计题 | 中等 |
| 72 | 编辑距离 | 二维DP | 中等 |
| 236 | 二叉树的最近公共祖先 | 树后序递归 | 中等 |
| 547 | 省份数量 | 并查集 | 中等 |
| 200 | 岛屿数量 | 网格搜索 | 中等 |
| 207 | 课程表 | 拓扑排序 | 中等 |
| 15 | 三数之和 | 排序+双指针 | 中等 |
| 98 | 验证二叉搜索树 | BST验证 | 中等 |
