#!/usr/bin/env python3
"""
每日算法题网站生成脚本
================================
用法：
  python generate.py           # 选择今日题目并生成 HTML
  python generate.py --bank    # 只从本地题库选
  python generate.py --api     # 只从 LeetCode API 选
  python generate.py --dry-run # 预览但不写入文件
  python generate.py --slug=two-sum  # 指定题目 slug
"""

import json
import re
import sys
import os
from pathlib import Path
from datetime import date, datetime
from argparse import ArgumentParser
from typing import Optional

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DOCS = ROOT / "docs"
ARCHIVE = DOCS / "archive"
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
# 候选题库：LeetCode 前 200 题（frontendId 1..200）。选题从这个池里去重轮换。
POOL_FILE = DATA / "problem_pool.json"

# 题型 → CSS class 映射
TYPE_CLASS_MAP = {
    "前缀和+哈希": "prefix-hash",
    "固定滑窗最值": "sliding-fixed",
    "可变滑窗": "sliding-var",
    "单调栈": "mono-stack",
    "链表指针": "linked-list",
    "设计题": "design",
    "二维DP": "dp",
    "一维DP": "dp",
    "树后序递归": "tree",
    "并查集": "union-find",
    "网格搜索": "grid",
    "拓扑排序": "topo",
    "排序+双指针": "two-pointer",
    "双指针": "two-pointer",
    "BST验证": "bst",
    "哈希表": "hash",
    "二分查找": "binary-search",
    "中心扩展": "center-expand",
    "字符串模拟": "string-sim",
    "数学模拟": "math-sim",
    "回溯": "backtrack",
    "栈": "stack",
    "堆（优先队列）": "heap",
    "数组原地哈希": "inplace-hash",
    "贪心": "greedy",
    "矩阵操作": "matrix",
    "区间合并": "interval",
}

# ─── Variable Semantics Data for Core Problem Types ───
# Each entry follows COACH-VAR-SEMANTICS.md structure

VAR_SEMANTICS_DATA = {
    "subarray-sum-equals-k": {
        "type": "前缀和+哈希",
        "difficulty": "中等",
        "frontend_id": "560",
        "title": "和为 K 的子数组",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "description": """<p>给你一个整数数组 <code>nums</code> 和一个整数 <code>k</code>，请你统计并返回该数组中和为 <code>k</code> 的<b>连续子数组</b>的个数。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,1,1], k = 2</div>
    <div class="example-output">输出：2</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [1,2,3], k = 3</div>
    <div class="example-output">输出：2</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>pre</code></td><td>int</td><td><b>定义</b>：扫到当前位置的前缀和<br><b>维护</b>：每轮后 pre = sum(nums[0..i])<br><b>更新</b>：当扫过 nums[i] 时，pre += nums[i]</td></tr>
    <tr><td><code>cnt[s]</code></td><td>map&lt;int,int&gt;</td><td><b>定义</b>：历史上前缀和为 s 的出现次数<br><b>维护</b>：每轮后 cnt 中 pre 的计数已加 1<br><b>更新</b>：统计完 ans 后 cnt[pre]++</td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：和为 k 的连续子数组个数<br><b>维护</b>：累计所有满足 pre[r] - pre[l-1] = k 的 (l,r) 对数<br><b>更新</b>：每轮 ans += cnt[pre - k]</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先写暴力：枚举 (l,r)，算 sum(l..r) 是否为 k，O(n²)。</p>
<p class="thinking-step">2. 重复在哪里？每个 r 都在重复找「哪些 l 可行」。</p>
<p class="thinking-step">3. 我想把「找 l」变成查表：pre[r] - pre[l-1] = k → pre[l-1] = pre[r] - k。</p>
<p class="thinking-step">4. 所以扫到 r 时，只要知道历史上 pre[r]-k 出现几次即可。</p>""",
        "code_steps": """<p class="code-step">1. <code>cnt[0] = 1</code> （空前缀，对应左端点在 index=0 之前）</p>
<p class="code-step">2. 遍历 <code>nums</code>，更新 <code>pre += nums[i]</code></p>
<p class="code-step">3. <code>ans += cnt[pre - k]</code> （查历史中有多少合法左端点）</p>
<p class="code-step">4. <code>cnt[pre]++</code> （将当前前缀和记入历史，<b>必须在统计 ans 之后</b>）</p>""",
        "code_python": """class Solution:
    def subarraySum(self, nums: list[int], k: int) -> int:
        # cnt[s]：历史上前缀和等于 s 的出现次数
        cnt = {0: 1}  # 空前缀 pre=0 已出现 1 次
        pre = 0       # 扫到当前位置的前缀和
        ans = 0       # 和为 k 的连续子数组个数

        for x in nums:
            pre += x
            # pre[r] - pre[l-1] = k  =>  查 pre-k 历史出现几次
            ans += cnt.get(pre - k, 0)
            # 必须把当前 pre 记入历史；若先 cnt[pre]++ 再统计，会多算含当前点的子数组
            cnt[pre] = cnt.get(pre, 0) + 1

        return ans""",
        "code_cpp": """class Solution {
public:
    int subarraySum(vector<int>& nums, int k) {
        // cnt[s]：历史上前缀和等于 s 的出现次数
        unordered_map<int, int> cnt;
        // 空前缀 pre=0 已出现 1 次，对应左端点在 index 0 之前的子数组
        cnt[0] = 1;

        int pre = 0;  // 扫到当前位置的前缀和
        int ans = 0;  // 和为 k 的连续子数组个数

        for (int x : nums) {
            pre += x;
            // pre[r] - pre[l-1] = k  =>  pre[l-1] = pre - k
            // 查历史上 pre-k 出现几次，即有多少个合法左端点
            ans += cnt[pre - k];
            // 必须把当前 pre 记入历史；若先 cnt[pre]++ 再统计，会多算含当前点的子数组
            cnt[pre]++;
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 顺序错误：必须先 <code>ans += cnt[pre-k]</code>，再 <code>cnt[pre]++</code>，否则会把当前点也算进去。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记 <code>cnt[0]=1</code>：空前缀的计数至关重要，否则从 index=0 开始的合法子数组会被漏掉。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 把「连续子数组」误当「组合求和」：本题是统计连续段的个数，不需要回溯或 DP。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：k=0 且有零元素</div>
    <code>nums = [0,0,0], k = 0 → 输出 6（空前缀 + 各种组合）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全部元素都是正数但和为 k</div>
    <code>nums = [1,2,3], k = 6 → 输出 1（[1,2,3]）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：单元素数组</div>
    <code>nums = [5], k = 5 → 输出 1</code>
</div>""",
    },

    "sliding-window-maximum": {
        "type": "固定滑窗最值",
        "difficulty": "困难",
        "frontend_id": "239",
        "title": "滑动窗口最大值",
        "time_complexity": "O(n)",
        "space_complexity": "O(k)",
        "description": """<p>给你一个整数数组 <code>nums</code>，有一个大小为 <code>k</code> 的滑动窗口从数组的最左侧移动到最右侧。你只可以看到在滑动窗口内的 <code>k</code> 个数字。滑动窗口每次只向右移动一位。返回 <b>滑动窗口中的最大值</b>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,3,-1,-3,5,3,6,7], k = 3</div>
    <div class="example-output">输出：[3,3,5,5,6,7]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dq</code></td><td>deque&lt;int&gt;</td><td><b>定义</b>：候选最大值下标队列（值单调递减）<br><b>维护</b>：队首始终是当前窗口的最大值下标<br><b>更新</b>：入队时弹出所有 ≤ nums[i] 的旧元素；窗口右移时若队首滑出窗口则弹出</td></tr>
    <tr><td><code>i - k + 1</code></td><td>int</td><td><b>定义</b>：当前窗口的左边界下标<br><b>维护</b>：随 i 递增<br><b>更新</b>：每轮右移窗口时 +1</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 暴力法：对每个窗口遍历找最大值，O(nk)。问题：k 接近 n 时太慢。</p>
<p class="thinking-step">2. 重复劳动在哪？相邻窗口共享 k-1 个元素，只有一个出队一个入队。每次重新扫太浪费。</p>
<p class="thinking-step">3. 我需要一个能快速获取最大值、支持滑动更新的结构 → 单调队列：维护候选最大值的递减序列。</p>
<p class="thinking-step">4. 单调队列的妙处：新元素入队时，比它小的「旧元素」永远不可能成为答案，直接弹出。队首一定最大。</p>""",
        "code_steps": """<p class="code-step">1. 初始化双端队列 <code>dq</code>（存下标）</p>
<p class="code-step">2. 遍历 <code>nums</code>，先弹出窗口外元素：<code>while dq[0] <= i - k: dq.popleft()</code></p>
<p class="code-step">3. 维护单调递减：<code>while dq and nums[dq[-1]] <= nums[i]: dq.pop()</code></p>
<p class="code-step">4. <code>dq.append(i)</code>（新下标入队）</p>
<p class="code-step">5. 当 <code>i >= k-1</code>（窗口形成），<code>ans.append(nums[dq[0]])</code></p>""",
        "code_python": """from collections import deque

class Solution:
    def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:
        dq = deque()  # 存下标，值单调递减
        ans = []

        for i in range(len(nums)):
            # 1. 弹出滑出窗口的下标
            if dq and dq[0] <= i - k:
                dq.popleft()

            # 2. 维护单调递减：弹出所有 ≤ nums[i] 的旧元素
            while dq and nums[dq[-1]] <= nums[i]:
                dq.pop()

            # 3. 新下标入队
            dq.append(i)

            # 4. 窗口形成后，队首就是当前窗口最大值
            if i >= k - 1:
                ans.append(nums[dq[0]])

        return ans""",
        "code_cpp": """class Solution {
public:
    vector<int> maxSlidingWindow(vector<int>& nums, int k) {
        deque<int> dq;  // 存下标，值单调递减
        vector<int> ans;

        for (int i = 0; i < nums.size(); i++) {
            // 1. 弹出滑出窗口的下标
            if (!dq.empty() && dq.front() <= i - k)
                dq.pop_front();

            // 2. 维护单调递减：弹出所有 <= nums[i] 的旧元素
            while (!dq.empty() && nums[dq.back()] <= nums[i])
                dq.pop_back();

            // 3. 新下标入队
            dq.push_back(i);

            // 4. 窗口形成后，队首就是当前窗口最大值
            if (i >= k - 1)
                ans.push_back(nums[dq.front()]);
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(k)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 弹出顺序：必须先弹出窗口外元素（<code>dq[0] <= i-k</code>），再维护单调性。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 维护单调性要用 <code><=</code> 而非 <code><</code>：遇到相等值也要弹出旧元素，保证队首是「最近」的最大值（虽然不影响本题结果，但更规范）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记窗口还没形成时不能记录答案：只有当 <code>i >= k-1</code> 时才把队首加入结果。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：k=1</div>
    <code>nums = [1,-1,2], k = 1 → 输出 [1,-1,2]（每个窗口就是单个元素）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：k=n</div>
    <code>nums = [3,1,2], k = 3 → 输出 [3]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：单调递减数组</div>
    <code>nums = [5,4,3,2,1], k = 3 → 输出 [5,4,3]</code>
</div>""",
    },

    "minimum-window-substring": {
        "type": "可变滑窗",
        "difficulty": "困难",
        "frontend_id": "76",
        "title": "最小覆盖子串",
        "time_complexity": "O(m+n)",
        "space_complexity": "O(|Σ|)",
        "description": """<p>给你一个字符串 <code>s</code>、一个字符串 <code>t</code>。返回 <code>s</code> 中涵盖 <code>t</code> 所有字符的最小子串。如果 <code>s</code> 中不存在涵盖 <code>t</code> 所有字符的子串，则返回空字符串 <code>""</code>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "ADOBECODEBANC", t = "ABC"</div>
    <div class="example-output">输出："BANC"</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>need[c]</code></td><td>map&lt;char,int&gt;</td><td><b>定义</b>：目标串 t 对字符 c 的需求次数<br><b>维护</b>：不变量，初始化为 t 的字符频率<br><b>更新</b>：不更新</td></tr>
    <tr><td><code>window[c]</code></td><td>map&lt;char,int&gt;</td><td><b>定义</b>：当前窗口内字符 c 的计数<br><b>维护</b>：随窗口滑动实时反映窗口内容<br><b>更新</b>：窗口右扩时 window[c]++，左缩时 window[c]--</td></tr>
    <tr><td><code>valid</code></td><td>int</td><td><b>定义</b>：已满足需求的字符种类数<br><b>维护</b>：每轮后 valid = 满足 window[c] >= need[c] 的字符 c 的数量<br><b>更新</b>：当 window[c] 刚好等于 need[c]（从 < 变成 =）时 valid++</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 暴力：枚举所有子串检查是否覆盖 t。要滑动窗口就必须回答「可行」（cover）→「比长度」。</p>
<p class="thinking-step">2. 右指针 r 扩张到覆盖为止，一旦覆盖就尝试收左指针 l 缩到最短。</p>
<p class="thinking-step">3. 需要 O(1) 判断是否覆盖，所以引入计数表 need/window 和 valid 计数。</p>
<p class="thinking-step">4. 当 valid == distinct_chars_in_t 时，当前窗口 [l,r) 是一个可行解，尝试缩小 l 找更短。</p>""",
        "code_steps": """<p class="code-step">1. 统计 <code>need</code>：遍历 t，对每个字符 need[c]++</p>
<p class="code-step">2. 右指针 <code>r</code> 扩张：window[s[r]]++，若 window[s[r]] == need[s[r]] 则 valid++</p>
<p class="code-step">3. 当 <code>valid == len(need)</code>（全部满足），循环收缩左指针：更新答案，window[s[l]]--，若 window[s[l]] < need[s[l]] 则 valid--，l++</p>
<p class="code-step">4. 返回最短子串或空串</p>""",
        "code_python": """from collections import Counter

class Solution:
    def minWindow(self, s: str, t: str) -> str:
        need = Counter(t)
        need_types = len(need)
        window = Counter()
        valid = 0
        l = 0
        start, min_len = 0, float('inf')

        for r in range(len(s)):
            c = s[r]
            window[c] += 1
            if window[c] == need[c]:
                valid += 1

            while valid == need_types:
                if r - l + 1 < min_len:
                    start, min_len = l, r - l + 1

                d = s[l]
                if window[d] == need[d]:
                    valid -= 1
                window[d] -= 1
                l += 1

        return s[start:start+min_len] if min_len != float('inf') else ''""",
        "code_cpp": """class Solution {
public:
    string minWindow(string s, string t) {
        unordered_map<char, int> need, window;
        for (char c : t) need[c]++;

        int valid = 0;
        int l = 0, start = 0, min_len = INT_MAX;

        for (int r = 0; r < s.size(); r++) {
            char c = s[r];
            window[c]++;
            if (need.count(c) && window[c] == need[c])
                valid++;

            while (valid == need.size()) {
                if (r - l + 1 < min_len) {
                    start = l;
                    min_len = r - l + 1;
                }
                char d = s[l];
                if (need.count(d) && window[d] == need[d])
                    valid--;
                window[d]--;
                l++;
            }
        }
        return min_len == INT_MAX ? "" : s.substr(start, min_len);
    }
};
// 时间 O(m+n)，空间 O(|Σ|)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> valid 计数逻辑：必须 window[c] <b>刚好等于</b> need[c] 时才 valid++，超过不算（否则重复字符会虚增 valid）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 收缩时更新顺序：先判断 window[d]==need[d] 再 window[d]--，和扩张时顺序相同。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回空串的判断：min_len 仍是 INF 说明从未形成合法窗口。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：s 和 t 相同</div>
    <code>s = "ABC", t = "ABC" → 输出 "ABC"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：t 比 s 长</div>
    <code>s = "A", t = "AB" → 输出 ""</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：t 有重复字符</div>
    <code>s = "AAB", t = "AA" → 输出 "AA"</code>
</div>""",
    },

    "trapping-rain-water": {
        "type": "单调栈",
        "difficulty": "困难",
        "frontend_id": "42",
        "title": "接雨水",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "description": """<p>给定 <code>n</code> 个非负整数表示每个宽度为 <code>1</code> 的柱子的高度图，计算按此排列的柱子，下雨之后能接多少雨水。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：height = [0,1,0,2,1,0,1,3,2,1,2,1]</div>
    <div class="example-output">输出：6</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>st</code></td><td>stack&lt;int&gt;</td><td><b>定义</b>：存下标，栈内高度单调递减<br><b>维护</b>：栈底到栈顶对应的高度严格递减<br><b>更新</b>：当前高度 >= 栈顶高度时弹出栈顶并结算雨水；然后将当前下标压入</td></tr>
    <tr><td><code>mid</code></td><td>int</td><td><b>定义</b>：被弹出的低谷位置（即栈顶）<br><b>维护</b>：每次弹出时取值<br><b>更新</b>：st.pop() 得到</td></tr>
    <tr><td><code>left</code></td><td>int</td><td><b>定义</b>：弹出后新栈顶，作为接雨水的左边界<br><b>维护</b>：mid 弹出后 st.top()（若栈非空）<br><b>更新</b>：结算宽度 = i - left - 1</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 问题本质：每根柱子能接多少水 = min(左边最高, 右边最高) - 自身高度。</p>
<p class="thinking-step">2. 双指针法（按列算）：维护 leftMax / rightMax，谁小就处理谁那侧的柱子。</p>
<p class="thinking-step">3. 单调栈法（按行算）：遇到一个上升的柱子，它和左侧柱子形成的「凹槽」可以存水。</p>
<p class="thinking-step">4. 每次弹出时，以 mid 为底，left 和 i 为两壁，高度差 × 宽度就是这层的水量。</p>""",
        "code_steps": """<p class="code-step">1. 初始化空栈 <code>st</code>，<code>ans = 0</code></p>
<p class="code-step">2. 遍历 <code>height</code>，当前高度 >= 栈顶高度时循环结算</p>
<p class="code-step">3. <code>mid = st.pop()</code>（谷底），若栈非空则 <code>left = st[-1]</code></p>
<p class="code-step">4. <code>h = min(height[left], height[i]) - height[mid]</code>，<code>w = i - left - 1</code></p>
<p class="code-step">5. <code>ans += h * w</code>，最后 <code>st.append(i)</code></p>""",
        "code_python": """class Solution:
    def trap(self, height: list[int]) -> int:
        st = []  # 单调递减栈，存下标
        ans = 0

        for i in range(len(height)):
            while st and height[i] >= height[st[-1]]:
                mid = st.pop()
                if not st:
                    break
                left = st[-1]
                h = min(height[left], height[i]) - height[mid]
                w = i - left - 1
                ans += h * w
            st.append(i)

        return ans

# 双指针优化版（O(1) 空间）：
class Solution:
    def trap(self, height: list[int]) -> int:
        l, r = 0, len(height) - 1
        left_max = right_max = 0
        ans = 0
        while l < r:
            left_max = max(left_max, height[l])
            right_max = max(right_max, height[r])
            if left_max < right_max:
                ans += left_max - height[l]
                l += 1
            else:
                ans += right_max - height[r]
                r -= 1
        return ans""",
        "code_cpp": """class Solution {
public:
    int trap(vector<int>& height) {
        stack<int> st;  // 单调递减栈，存下标
        int ans = 0;

        for (int i = 0; i < height.size(); i++) {
            while (!st.empty() && height[i] >= height[st.top()]) {
                int mid = st.top(); st.pop();
                if (st.empty()) break;
                int left = st.top();
                int h = min(height[left], height[i]) - height[mid];
                int w = i - left - 1;
                ans += h * w;
            }
            st.push(i);
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(n)
// 双指针优化版可达 O(1) 空间""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 单调栈要求 <code>height[i] >= height[st[-1]]</code>（而非 >）：相等时也要弹出，否则会重复计算。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 弹出 mid 后栈为空：说明当前柱子高过所有左侧柱，无法形成凹槽，直接 break。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 双指针法只适用于算「每列能接多少」，单调栈法算「每行（水平层）能接多少」——两种思路完全不同。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单调递增</div>
    <code>height = [1,2,3,4] → 输出 0（无凹槽）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：V 形</div>
    <code>height = [3,0,3] → 输出 3</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：空数组</div>
    <code>height = [] → 输出 0</code>
</div>""",
    },

    "reverse-linked-list": {
        "type": "链表指针",
        "difficulty": "简单",
        "frontend_id": "206",
        "title": "反转链表",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你单链表的头节点 <code>head</code> ，请你反转链表，并返回反转后的链表。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：head = [1,2,3,4,5]</div>
    <div class="example-output">输出：[5,4,3,2,1]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>pre</code></td><td>ListNode*</td><td><b>定义</b>：已反转部分的头节点<br><b>维护</b>：始终指向已反转链表的首节点<br><b>更新</b>：每轮 pre = cur（cur 被接入反转链表头部）</td></tr>
    <tr><td><code>cur</code></td><td>ListNode*</td><td><b>定义</b>：当前正在处理的节点<br><b>维护</b>：指向原链表中下一个待反转的节点<br><b>更新</b>：每轮 cur = nxt（移到下一个）</td></tr>
    <tr><td><code>nxt</code></td><td>ListNode*</td><td><b>定义</b>：cur 的原后继（改指针前先保存，防断链）<br><b>维护</b>：每轮保存 cur.next<br><b>更新</b>：nxt = cur.next（在 cur.next 被改写之前）</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 直观想法：我需要把每个节点的 next 指针反过来指向前一个节点。</p>
<p class="thinking-step">2. 关键问题：改了 cur.next 之后，我就找不到原来的下一个节点了——所以在改之前必须用 nxt 保存。</p>
<p class="thinking-step">3. 初始状态：第 0 个位置是 null（pre = None），第 1 个是 head（cur = head）。</p>
<p class="thinking-step">4. 循环结束后 pre 就指向了新的头节点（原链表的尾）。</p>""",
        "code_steps": """<p class="code-step">1. <code>pre = None, cur = head</code></p>
<p class="code-step">2. 循环：<code>nxt = cur.next</code>（保存后继，防断链）</p>
<p class="code-step">3. <code>cur.next = pre</code>（反转指针）</p>
<p class="code-step">4. <code>pre = cur; cur = nxt</code>（两指针前移）</p>
<p class="code-step">5. 返回 <code>pre</code></p>""",
        "code_python": """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        pre = None  # 已反转部分的头节点
        cur = head  # 当前正在处理的节点

        while cur:
            nxt = cur.next  # 先保存后继，防断链
            cur.next = pre  # 反转指针
            pre = cur       # pre 前移
            cur = nxt       # cur 前移

        return pre""",
        "code_cpp": """class Solution {
public:
    ListNode* reverseList(ListNode* head) {
        ListNode* pre = nullptr;  // 已反转部分的头节点
        ListNode* cur = head;     // 当前正在处理的节点

        while (cur) {
            ListNode* nxt = cur->next;  // 先保存后继，防断链
            cur->next = pre;            // 反转指针
            pre = cur;                  // pre 前移
            cur = nxt;                  // cur 前移
        }
        return pre;
    }
};
// 时间 O(n)，空间 O(1)
// 递归版：reverseList(head.next) 后 head.next.next = head; head.next = null;""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 顺序！必须先 <code>nxt = cur.next</code> 保存，再修改 <code>cur.next</code>。反过来就会「断链」——丢失后续所有节点。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回值是 <code>pre</code> 不是 <code>cur</code>：循环结束时 cur 是 None，pre 才是新头。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空链表 / 单节点：while 直接跳过，返回 pre（null 或 head），行为正确。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空链表</div>
    <code>head = null → 输出 null</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单节点</div>
    <code>head = [1] → 输出 [1]</code>
</div>""",
    },

    "lru-cache": {
        "type": "设计题",
        "difficulty": "中等",
        "frontend_id": "146",
        "title": "LRU 缓存",
        "time_complexity": "O(1) per operation",
        "space_complexity": "O(capacity)",
        "description": """<p>请你设计并实现一个满足 LRU（最近最少使用）缓存约束的数据结构。</p>
<p>实现 <code>LRUCache</code> 类：</p>
<ul>
<li><code>LRUCache(int capacity)</code> 以正整数作为容量初始化 LRU 缓存</li>
<li><code>int get(int key)</code> 如果关键字存在于缓存中则返回值，否则返回 -1</li>
<li><code>void put(int key, int value)</code> 插入或更新键值，超出容量则逐出最久未使用的</li>
</ul>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">LRUCache lRUCache = new LRUCache(2); lRUCache.put(1,1); lRUCache.put(2,2); lRUCache.get(1); lRUCache.put(3,3); lRUCache.get(2); lRUCache.put(4,4); lRUCache.get(1); lRUCache.get(3); lRUCache.get(4);</div>
    <div class="example-output">[null,null,null,1,null,-1,null,-1,3,4]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>cache[key]</code></td><td>map&lt;int, iterator&gt;</td><td><b>定义</b>：key 到链表节点的迭代器（用于 O(1) 定位）<br><b>维护</b>：与链表节点保持同步<br><b>更新</b>：put 时写入（或覆盖），淘汰时删除</td></tr>
    <tr><td><code>lst</code></td><td>双向链表</td><td><b>定义</b>：头部最新、尾部最旧的访问顺序<br><b>维护</b>：get/put 命中时移到头部<br><b>更新</b>：新节点插入头部，淘汰时删尾部</td></tr>
    <tr><td><code>cap</code></td><td>int</td><td><b>定义</b>：缓存容量上限<br><b>维护</b>：不变量<br><b>更新</b>：不更新</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 需求拆解：O(1) 查找 → 哈希表；O(1) 淘汰最旧的 → 有序结构；O(1) 更新访问时间 → 链表移动。</p>
<p class="thinking-step">2. 哈希 + 双向链表经典组合：哈希表存 key→节点迭代器，链表存访问顺序。</p>
<p class="thinking-step">3. get 时：查哈希 → 命中则移到链表头 → 返回值。</p>
<p class="thinking-step">4. put 时：更新则移到头；新增则插入头，超容量则删链表尾 + 删哈希。</p>""",
        "code_steps": """<p class="code-step">1. 维护 <code>dict&lt;int, iterator&gt; cache</code> + <code>list&lt;(int,int)&gt; lst</code>（Python）</p>
<p class="code-step">2. get(key)：若 key 在 cache 中，调 splice 移到头部，返回值</p>
<p class="code-step">3. put(key,value)：若存在则更新值并移到头部；否则插入头部</p>
<p class="code-step">4. 若插入后 len > cap，删除链表尾 + 删除 cache 中的对应 key</p>""",
        "code_python": """from collections import OrderedDict

# 方法一：OrderedDict（Python 内置，最简单）
class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.cap:
            self.cache.popitem(last=False)

# 方法二：手动双向链表 + 哈希
class DLinkedNode:
    __slots__ = ('prev', 'next', 'key', 'value')
    def __init__(self, k=0, v=0):
        self.key = k; self.value = v
        self.prev = self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache = {}
        self.head = DLinkedNode()
        self.tail = DLinkedNode()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_head(self, node):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._remove(node)
        self._add_to_head(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            self._remove(node)
            self._add_to_head(node)
        else:
            node = DLinkedNode(key, value)
            self.cache[key] = node
            self._add_to_head(node)
            if len(self.cache) > self.cap:
                removed = self.tail.prev
                self._remove(removed)
                del self.cache[removed.key]""",
        "code_cpp": """class LRUCache {
    int cap;
    list<pair<int, int>> lst;
    unordered_map<int, list<pair<int, int>>::iterator> cache;

public:
    LRUCache(int capacity) : cap(capacity) {}

    int get(int key) {
        auto it = cache.find(key);
        if (it == cache.end()) return -1;
        lst.splice(lst.begin(), lst, it->second);
        return it->second->second;
    }

    void put(int key, int value) {
        auto it = cache.find(key);
        if (it != cache.end()) {
            it->second->second = value;
            lst.splice(lst.begin(), lst, it->second);
            return;
        }
        if (cache.size() == cap) {
            int oldest_key = lst.back().first;
            lst.pop_back();
            cache.erase(oldest_key);
        }
        lst.emplace_front(key, value);
        cache[key] = lst.begin();
    }
};
// 每操作 O(1)，空间 O(capacity)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> Python 的 OrderedDict.move_to_end(key) 默认为 last=True（移到尾部当最新），要用来做 LRU 需确认语义。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 手动双向链表时：头尾 dummy 节点的连接不能忘，移节点时要同时更新前后节点的指针。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 覆盖值（key 已存在）时不要忘记移动位置——访问时间需要更新。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：capacity=1</div>
    <code>put(1,1) → put(2,2) → get(1) 返回 -1 → get(2) 返回 2</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：重复 put 同一 key</div>
    <code>put(1,1) → put(1,100) → get(1) 返回 100</code>
</div>""",
    },

    "edit-distance": {
        "type": "二维DP",
        "difficulty": "中等",
        "frontend_id": "72",
        "title": "编辑距离",
        "time_complexity": "O(mn)",
        "space_complexity": "O(mn) / O(n)",
        "description": """<p>给你两个单词 <code>word1</code> 和 <code>word2</code>，请返回将 <code>word1</code> 转换成 <code>word2</code> 所使用的最少操作数。你可以对一个单词进行如下三种操作：插入一个字符、删除一个字符、替换一个字符。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：word1 = "horse", word2 = "ros"</div>
    <div class="example-output">输出：3（horse → rorse → rose → ros）</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dp[i][j]</code></td><td>int[][]</td><td><b>定义</b>：word1 的前 i 个字符变成 word2 的前 j 个字符的最少操作数<br><b>维护</b>：满足最优子结构：dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)<br><b>更新</b>：按 i/j 递增顺序计算，当 word1[i-1]==word2[j-1] 时 cost=0 否则 cost=1</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 两串问题 → 尝试「前 i 个」和「前 j 个」的子问题定义，自然导向二维 DP。</p>
<p class="thinking-step">2. 三种操作的意义：删除=跳过 word1 的字符（i-1, j）；插入=跳过 word2 的字符（i, j-1）；替换=同时消耗两个字符（i-1, j-1）。</p>
<p class="thinking-step">3. 字符相等时（word1[i-1]==word2[j-1]）不需要替换，直接继承 dp[i-1][j-1]。</p>
<p class="thinking-step">4. 边界：dp[i][0]=i（全删），dp[0][j]=j（全插）。</p>""",
        "code_steps": """<p class="code-step">1. <code>dp[i][0] = i, dp[0][j] = j</code>（边界初始化）</p>
<p class="code-step">2. 双重循环遍历 i,j，若 <code>word1[i-1]==word2[j-1]</code>：<code>dp[i][j] = dp[i-1][j-1]</code></p>
<p class="code-step">3. 否则：<code>dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])</code></p>
<p class="code-step">4. 返回 <code>dp[m][n]</code></p>""",
        "code_python": """class Solution:
    def minDistance(self, word1: str, word2: str) -> int:
        m, n = len(word1), len(word2)
        # dp[i][j]：word1 前 i 个 → word2 前 j 个的最少操作数
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = i  # 全删
        for j in range(n + 1):
            dp[0][j] = j  # 全插

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if word1[i-1] == word2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # 删除 word1[i-1]
                        dp[i][j-1],    # 插入 word2[j-1]
                        dp[i-1][j-1]   # 替换
                    )
        return dp[m][n]

# 空间优化到 O(n)：
class Solution:
    def minDistance(self, word1: str, word2: str) -> int:
        m, n = len(word1), len(word2)
        prev = list(range(n + 1))
        for i in range(1, m + 1):
            cur = [i] + [0] * n
            for j in range(1, n + 1):
                if word1[i-1] == word2[j-1]:
                    cur[j] = prev[j-1]
                else:
                    cur[j] = 1 + min(prev[j], cur[j-1], prev[j-1])
            prev = cur
        return prev[n]""",
        "code_cpp": """class Solution {
public:
    int minDistance(string word1, string word2) {
        int m = word1.size(), n = word2.size();
        vector<vector<int>> dp(m + 1, vector<int>(n + 1));

        for (int i = 0; i <= m; i++) dp[i][0] = i;
        for (int j = 0; j <= n; j++) dp[0][j] = j;

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (word1[i-1] == word2[j-1])
                    dp[i][j] = dp[i-1][j-1];
                else
                    dp[i][j] = 1 + min({dp[i-1][j], dp[i][j-1], dp[i-1][j-1]});
            }
        }
        return dp[m][n];
    }
};
// 时间 O(mn)，空间 O(mn)，可优化到 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 边界初始化：dp[i][0]=i 不是默认的 0——从 word1 到空串需要 i 次删除。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 字符相等时是 dp[i-1][j-1]（无代价），不是 +1 再 min。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 三种操作（删插替）中「插入」对应 dp[i][j-1]，很多人这里搞反。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：一个为空</div>
    <code>word1 = "", word2 = "abc" → 输出 3（全部插入）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：完全相同</div>
    <code>word1 = "abc", word2 = "abc" → 输出 0</code>
</div>""",
    },

    "lowest-common-ancestor-of-a-binary-tree": {
        "type": "树后序递归",
        "difficulty": "中等",
        "frontend_id": "236",
        "title": "二叉树的最近公共祖先",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "description": """<p>给定一个二叉树, 找到该树中两个指定节点的最近公共祖先（LCA）。</p>
<p>最近公共祖先的定义为：「对于有根树 T 的两个节点 p、q，最近公共祖先表示为一个节点 x，满足 x 是 p、q 的祖先且 x 的深度尽可能大（一个节点也可以是它自己的祖先）。」</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1</div>
    <div class="example-output">输出：3</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>L</code></td><td>TreeNode*</td><td><b>定义</b>：左子树的递归返回值<br><b>维护</b>：若左子树包含 p 或 q 则返回该节点，否则返回 null<br><b>更新</b>：L = dfs(root.left, p, q)</td></tr>
    <tr><td><code>R</code></td><td>TreeNode*</td><td><b>定义</b>：右子树的递归返回值<br><b>维护</b>：若右子树包含 p 或 q 则返回该节点，否则返回 null<br><b>更新</b>：R = dfs(root.right, p, q)</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. LCA 的本质：从下往上找「第一个同时拥有 p 和 q 的节点」。</p>
<p class="thinking-step">2. 后序遍历：先拿到左右子树的结果，再决定当前节点是不是答案。</p>
<p class="thinking-step">3. 三种情况：(a) L 和 R 都非空 → root 就是 LCA；(b) 只有一个非空 → 把非空的传上去；(c) 都空 → 返回 null。</p>
<p class="thinking-step">4. 特殊：当前节点 == p 或 q 时直接返回自己（不必再看子树）。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>root == null or root == p or root == q</code>，返回 root</p>
<p class="code-step">2. <code>L = dfs(root.left)</code>，<code>R = dfs(root.right)</code></p>
<p class="code-step">3. 若 <code>L != null and R != null</code>，返回 root（此时 root 就是 LCA）</p>
<p class="code-step">4. 否则返回 <code>L or R</code>（把找到的 p/q 向上传）</p>""",
        "code_python": """class Solution:
    def lowestCommonAncestor(
        self, root: TreeNode, p: TreeNode, q: TreeNode
    ) -> TreeNode:
        if not root or root == p or root == q:
            return root

        L = self.lowestCommonAncestor(root.left, p, q)
        R = self.lowestCommonAncestor(root.right, p, q)

        if L and R:
            return root  # p 和 q 分别在左右子树中
        return L or R   # p 和 q 在同一个子树中，或都未找到""",
        "code_cpp": """class Solution {
public:
    TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
        if (!root || root == p || root == q)
            return root;

        TreeNode* L = lowestCommonAncestor(root->left, p, q);
        TreeNode* R = lowestCommonAncestor(root->right, p, q);

        if (L && R) return root;  // p 和 q 分别在左右子树
        return L ? L : R;         // p 和 q 在同一子树，或都未找到
    }
};
// 时间 O(n)，空间 O(n)（递归栈）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 判断 L 和 R 都非空才返回 root——这是 LCA 的唯一判定条件，不要过早返回。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 当前节点等于 p 或 q 时直接返回当前节点：因为一个节点可以是自己的祖先。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> BST 版本（LC235）可以用值比较剪枝，普通二叉树必须遍历整棵树。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：p 是 q 的祖先</div>
    <code>root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 4 → 输出 5</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：p 和 q 相同</div>
    <code>p == q → 输出 p</code>
</div>""",
    },

    "number-of-provinces": {
        "type": "并查集",
        "difficulty": "中等",
        "frontend_id": "547",
        "title": "省份数量",
        "time_complexity": "O(n²·α(n)) 近似 O(n²)",
        "space_complexity": "O(n)",
        "description": """<p>有 <code>n</code> 个城市，其中一些彼此相连，另一些没有相连。如果城市 a 与 b 直接相连，且 b 与 c 直接相连，那么 a 与 c 间接相连。省份是一组直接或间接相连的城市。给你一个 n×n 的矩阵 <code>isConnected</code>，<code>isConnected[i][j]=1</code> 表示 i、j 直接相连。返回省份数量。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">isConnected = [[1,1,0],[1,1,0],[0,0,1]]</div>
    <div class="example-output">输出：2</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>fa[x]</code></td><td>int[]</td><td><b>定义</b>：元素 x 的父节点<br><b>维护</b>：初始 fa[x]=x（每个元素是一个独立的集合）<br><b>更新</b>：合并时 fa[find(x)] = find(y)</td></tr>
    <tr><td><code>find(x)</code></td><td>int</td><td><b>定义</b>：x 所属集合的代表元<br><b>维护</b>：路径压缩，返回 fa[x] 的代表元<br><b>更新</b>：递归 find(fa[x])，并 fa[x]=结果</td></tr>
    <tr><td><code>count</code></td><td>int</td><td><b>定义</b>：当前连通分量（省份）数量<br><b>维护</b>：初始 count=n<br><b>更新</b>：每次成功合并两个集合时 count--</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 问题是「连通分量计数」——天然适合并查集（Union-Find）。</p>
<p class="thinking-step">2. 并查集核心操作：find（找代表元+路径压缩）、union（合并两个集合）。</p>
<p class="thinking-step">3. 遍历邻接矩阵的上三角（i < j），如果 isConnected[i][j]=1 且 find(i) != find(j)，则合并，count--。</p>
<p class="thinking-step">4. 最终 count 就是省份数量。</p>""",
        "code_steps": """<p class="code-step">1. 初始化：<code>fa[i]=i</code>，<code>count=n</code></p>
<p class="code-step">2. 遍历 i < j：若 <code>isConnected[i][j]==1 and find(i)!=find(j)</code> 则合并</p>
<p class="code-step">3. 合并：<code>fa[find(i)] = find(j)</code>，<code>count--</code></p>
<p class="code-step">4. 返回 <code>count</code></p>""",
        "code_python": """class Solution:
    def findCircleNum(self, isConnected: list[list[int]]) -> int:
        n = len(isConnected)
        fa = list(range(n))
        count = n

        def find(x):
            if fa[x] != x:
                fa[x] = find(fa[x])
            return fa[x]

        for i in range(n):
            for j in range(i + 1, n):
                if isConnected[i][j] and find(i) != find(j):
                    fa[find(i)] = find(j)
                    count -= 1

        return count""",
        "code_cpp": """class Solution {
    vector<int> fa;
    int count;

    int find(int x) {
        if (fa[x] != x)
            fa[x] = find(fa[x]);
        return fa[x];
    }

public:
    int findCircleNum(vector<vector<int>>& isConnected) {
        int n = isConnected.size();
        fa.resize(n);
        iota(fa.begin(), fa.end(), 0);
        count = n;

        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (isConnected[i][j] && find(i) != find(j)) {
                    fa[find(i)] = find(j);
                    count--;
                }
            }
        }
        return count;
    }
};
// 时间 O(n²·α(n))，空间 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 合并前必须检查 find(i) != find(j)，否则会重复计数 count--。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 合并方向不重要（fa[find(i)]=find(j) 或反过来都可以）——没有按秩合并时尤其无所谓。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 只遍历上三角即可（i < j），因为矩阵对称且对角线都是 1（自连接）。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：全不连通</div>
    <code>isConnected = [[1,0,0],[0,1,0],[0,0,1]] → 输出 3</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全连通</div>
    <code>isConnected = [[1,1,1],[1,1,1],[1,1,1]] → 输出 1</code>
</div>""",
    },

    "number-of-islands": {
        "type": "网格搜索",
        "difficulty": "中等",
        "frontend_id": "200",
        "title": "岛屿数量",
        "time_complexity": "O(mn)",
        "space_complexity": "O(mn)（DFS 栈）/ O(min(m,n))（BFS 队列）",
        "description": """<p>给你一个由 <code>'1'</code>（陆地）和 <code>'0'</code>（水）组成的二维网格，请你计算网格中岛屿的数量。岛屿总是被水包围，并且每座岛屿只能由水平方向和/或竖直方向上相邻的陆地连接形成。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">grid = [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]</div>
    <div class="example-output">输出：1</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>grid[r][c]</code></td><td>char</td><td><b>定义</b>：当前位置的地形（'1'=未访问陆地, '0'=水 或 已访问）<br><b>维护</b>：访问陆地后置为 '0'（原地标记）<br><b>更新</b>：每次 DFS/BFS 进入时 grid[r][c] = '0'</td></tr>
    <tr><td><code>dirs</code></td><td>int[][]</td><td><b>定义</b>：四方向偏移量<br><b>维护</b>：不变量 <code>[(0,1),(0,-1),(1,0),(-1,0)]</code><br><b>更新</b>：不更新</td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：岛屿总数<br><b>维护</b>：每次发现未访问陆地时 ans++<br><b>更新</b>：DFS/BFS 启动时 ans++</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 遍历每个格子，遇到 '1' 就启动一次 DFS/BFS 把整个岛「淹没」。</p>
<p class="thinking-step">2. 淹没操作：从该点出发向四个方向递归，把遇到的 '1' 都改成 '0'。</p>
<p class="thinking-step">3. 每启动一次淹没就 ans++，因为这说明发现了一个新岛屿。</p>
<p class="thinking-step">4. 原地修改 grid 代替 visited 数组，节省空间。</p>""",
        "code_steps": """<p class="code-step">1. 双重循环遍历 grid，遇到 '1' 时 ans++ 并启动 DFS</p>
<p class="code-step">2. DFS(r,c)：若越界或 grid[r][c] != '1'，直接返回</p>
<p class="code-step">3. <code>grid[r][c] = '0'</code>（标记已访问）</p>
<p class="code-step">4. 对四个方向递归 DFS</p>""",
        "code_python": """class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        m, n = len(grid), len(grid[0])
        ans = 0

        def dfs(r, c):
            if r < 0 or r >= m or c < 0 or c >= n:
                return
            if grid[r][c] != '1':
                return
            grid[r][c] = '0'  # 淹没
            dfs(r + 1, c)
            dfs(r - 1, c)
            dfs(r, c + 1)
            dfs(r, c - 1)

        for r in range(m):
            for c in range(n):
                if grid[r][c] == '1':
                    ans += 1
                    dfs(r, c)

        return ans""",
        "code_cpp": """class Solution {
    int m, n;
public:
    int numIslands(vector<vector<char>>& grid) {
        m = grid.size(), n = grid[0].size();
        int ans = 0;
        for (int r = 0; r < m; r++) {
            for (int c = 0; c < n; c++) {
                if (grid[r][c] == '1') {
                    ans++;
                    dfs(grid, r, c);
                }
            }
        }
        return ans;
    }

    void dfs(vector<vector<char>>& grid, int r, int c) {
        if (r < 0 || r >= m || c < 0 || c >= n || grid[r][c] != '1')
            return;
        grid[r][c] = '0';
        dfs(grid, r + 1, c);
        dfs(grid, r - 1, c);
        dfs(grid, r, c + 1);
        dfs(grid, r, c - 1);
    }
};
// 时间 O(mn)，空间 O(mn)（递归栈）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> DFS 越界检查必须在 grid[r][c] 检查之前，否则会越界访问。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 原地修改 grid 后要确认题目是否允许修改输入。如果不允许，需要额外 visited 数组。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> Java/C++ 递归可能栈溢出（特别大的岛屿），改用 BFS 或迭代栈。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空网格</div>
    <code>grid = [] → 输出 0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全是水</div>
    <code>grid = [["0","0"],["0","0"]] → 输出 0</code>
</div>""",
    },
    "course-schedule": {
        "type": "拓扑排序",
        "difficulty": "中等",
        "frontend_id": "207",
        "title": "课程表",
        "time_complexity": "O(V + E)",
        "space_complexity": "O(V + E)",
        "description": """<p>你这个学期必须选修 <code>numCourses</code> 门课程，记为 <code>0</code> 到 <code>numCourses - 1</code>。在选修某些课程之前需要一些先修课程。先修课程按数组 <code>prerequisites</code> 给出，其中 <code>prerequisites[i] = [a<sub>i</sub>, b<sub>i</sub>]</code>，表示如果要学习课程 <code>a<sub>i</sub></code> 则<b>必须先学习课程 b<sub>i</sub></b>。请你判断是否可能完成所有课程的学习？</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：numCourses = 2, prerequisites = [[1,0]]</div>
    <div class="example-output">输出：true</div>
    <div class="example-explain">先修关系：0 → 1，无环，可以学完。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：numCourses = 2, prerequisites = [[1,0],[0,1]]</div>
    <div class="example-output">输出：false</div>
    <div class="example-explain">0 和 1 互相依赖，形成环，无法完成。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>graph[u]</code></td><td>list&lt;int&gt;[]</td><td><b>定义</b>：先修图，边 b→a 表示学完 b 才能学 a<br><b>维护</b>：建图后不变，graph[b] 存所有依赖 b 的课程<br><b>更新</b>：遍历 prerequisites 时 graph[b].append(a)</td></tr>
    <tr><td><code>indeg[v]</code></td><td>int[]</td><td><b>定义</b>：课程 v 还剩多少门先修课未满足<br><b>维护</b>：每门课被「学完」时，其邻居 indeg--<br><b>更新</b>：建边 b→a 时 indeg[a]++；从队列弹出 u 时对每个 v∈graph[u] 执行 indeg[v]--</td></tr>
    <tr><td><code>queue</code></td><td>queue&lt;int&gt;</td><td><b>定义</b>：当前所有先修已满足、可以立即选修的课程<br><b>维护</b>：弹出学完的课程，把新满足条件的课程入队<br><b>更新</b>：初始化时入队所有 indeg==0 的课；每轮 indeg[v] 变 0 时 v 入队</td></tr>
    <tr><td><code>taken</code></td><td>int</td><td><b>定义</b>：已成功选修的课程数<br><b>维护</b>：每从队列弹出一门课 taken++<br><b>更新</b>：taken == numCourses 则无环，否则有环</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想：能不能学完所有课，等价于先修关系有没有形成环。</p>
<p class="thinking-step">2. 有环就永远卡在某个互相等待的圈子里，返回 false。</p>
<p class="thinking-step">3. 拓扑排序的思路：每次选一门「没有未满足先修」的课来学，学完就解锁后续课程。</p>
<p class="thinking-step">4. 用入度数组 + 队列（Kahn 算法）：indeg==0 的课先入队，弹出后给邻居 indeg--，新变 0 的再入队。</p>
<p class="thinking-step">5. 最终 taken == numCourses 说明所有课都排进了合法顺序，无环。</p>""",
        "code_steps": """<p class="code-step">1. 建图：对每条 [a,b]，添加边 b→a，indeg[a]++</p>
<p class="code-step">2. 将所有 indeg==0 的课程入队</p>
<p class="code-step">3. 循环：弹出 u，taken++，对 graph[u] 中每个 v 执行 indeg[v]--，若变 0 则入队</p>
<p class="code-step">4. 返回 taken == numCourses</p>""",
        "code_python": """class Solution:
    def canFinish(self, numCourses: int, prerequisites: list[list[int]]) -> bool:
        graph = [[] for _ in range(numCourses)]
        indeg = [0] * numCourses

        for a, b in prerequisites:
            graph[b].append(a)  # 先学 b，再学 a
            indeg[a] += 1

        queue = [i for i in range(numCourses) if indeg[i] == 0]
        taken = 0

        while queue:
            u = queue.pop()
            taken += 1
            for v in graph[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    queue.append(v)

        return taken == numCourses""",
        "code_cpp": """class Solution {
public:
    bool canFinish(int numCourses, vector<vector<int>>& prerequisites) {
        vector<vector<int>> graph(numCourses);
        vector<int> indeg(numCourses, 0);

        for (auto& p : prerequisites) {
            int a = p[0], b = p[1];
            graph[b].push_back(a);
            indeg[a]++;
        }

        queue<int> q;
        for (int i = 0; i < numCourses; i++)
            if (indeg[i] == 0) q.push(i);

        int taken = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            taken++;
            for (int v : graph[u]) {
                if (--indeg[v] == 0)
                    q.push(v);
            }
        }
        return taken == numCourses;
    }
};
// 时间 O(V+E)，空间 O(V+E)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 建边方向搞反：prerequisites[i]=[a,b] 表示 b 是 a 的先修，应建边 b→a，不是 a→b。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 用 DFS 判环时状态要分三种（未访问/访问中/已完成），只分两种会漏判。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 有环时 Kahn 算法 taken &lt; numCourses，不能只检查队列是否为空就返回 true。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：无先修要求</div>
    <code>numCourses = 3, prerequisites = [] → true</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：自环</div>
    <code>numCourses = 1, prerequisites = [[0,0]] → false</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：长链无环</div>
    <code>numCourses = 4, prerequisites = [[1,0],[2,1],[3,2]] → true</code>
</div>""",
    },

    "3sum": {
        "type": "排序+双指针",
        "difficulty": "中等",
        "frontend_id": "15",
        "title": "三数之和",
        "time_complexity": "O(n²)",
        "space_complexity": "O(1)（不计排序）",
        "description": """<p>给你一个整数数组 <code>nums</code>，判断是否存在三元组 <code>[nums[i], nums[j], nums[k]]</code> 满足 <code>i != j</code>、<code>i != k</code> 且 <code>j != k</code>，同时还满足 <code>nums[i] + nums[j] + nums[k] == 0</code>。请你返回所有和为 0 且<b>不重复</b>的三元组。</p>
<p>注意：答案中不可以包含重复的三元组。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [-1,0,1,2,-1,-4]</div>
    <div class="example-output">输出：[[-1,-1,2],[-1,0,1]]</div>
    <div class="example-explain">nums[0] + nums[1] + nums[2] = (-1) + 0 + 1 = 0；nums[1] + nums[2] + nums[4] = 0 + 1 + (-1) = 0。不重复三元组是 [-1,0,1] 和 [-1,-1,2]。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [0,1,1]</div>
    <div class="example-output">输出：[]</div>
    <div class="example-explain">唯一可能的三元组和不为 0。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [0,0,0]</div>
    <div class="example-output">输出：[[0,0,0]]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：固定三元组中第一个数的位置（排序后最小值）<br><b>维护</b>：每轮 i 向右移动，跳过与前一个相同的 nums[i]<br><b>更新</b>：for i in range(n-2)，若 nums[i]==nums[i-1] 则 continue</td></tr>
    <tr><td><code>l</code></td><td>int</td><td><b>定义</b>：在 i 右侧区间内指向较小候选值的左指针<br><b>维护</b>：和太小时右移，找到答案后右移跳过重复<br><b>更新</b>：初始 l=i+1；sum&lt;0 时 l++；命中后 while nums[l]==nums[l-1] 则 l++</td></tr>
    <tr><td><code>r</code></td><td>int</td><td><b>定义</b>：在 i 右侧区间内指向较大候选值的右指针<br><b>维护</b>：和太大时左移，找到答案后左移跳过重复<br><b>更新</b>：初始 r=n-1；sum&gt;0 时 r--；命中后 while nums[r]==nums[r+1] 则 r--</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&gt;</td><td><b>定义</b>：所有不重复的三元组答案<br><b>维护</b>：每当 nums[i]+nums[l]+nums[r]==0 时追加 [nums[i],nums[l],nums[r]]<br><b>更新</b>：命中后 l、r 同时内缩并各自跳过重复值</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先写暴力：三重循环枚举 (i,j,k)，判断和是否为 0，O(n³)，还要额外去重。</p>
<p class="thinking-step">2. 重复在哪里？固定一个数后，「在剩余数组里找两数之和为 -nums[i]」是经典子问题。</p>
<p class="thinking-step">3. 排序后，两数之和可以用双指针：和小了 l++，和大了 r--，O(n)。</p>
<p class="thinking-step">4. 外层固定 i，内层双指针找 complement = -nums[i]，整体 O(n²)。</p>
<p class="thinking-step">5. 去重关键：排序后，i、l、r 三个位置都要跳过与前一个相同的值，否则会输出重复三元组。</p>""",
        "code_steps": """<p class="code-step">1. 对 <code>nums</code> 升序排序</p>
<p class="code-step">2. 外层 <code>for i in range(n-2)</code>，若 <code>nums[i]==nums[i-1]</code> 则跳过（i 去重）</p>
<p class="code-step">3. 设 <code>l=i+1, r=n-1</code>，当 <code>l&lt;r</code> 时计算 <code>s=nums[i]+nums[l]+nums[r]</code></p>
<p class="code-step">4. <code>s&lt;0</code> 则 <code>l++</code>；<code>s&gt;0</code> 则 <code>r--</code>；<code>s==0</code> 则记录答案，l、r 内缩并各自跳过重复</p>
<p class="code-step">5. 返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def threeSum(self, nums: list[int]) -> list[list[int]]:
        nums.sort()
        n = len(nums)
        ans = []

        for i in range(n - 2):
            # 固定第一个数，跳过重复
            if i > 0 and nums[i] == nums[i - 1]:
                continue

            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    ans.append([nums[i], nums[l], nums[r]])
                    l += 1
                    r -= 1
                    # 跳过 l、r 侧的重复值
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
                    while l < r and nums[r] == nums[r + 1]:
                        r -= 1

        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<int>> threeSum(vector<int>& nums) {
        sort(nums.begin(), nums.end());
        int n = nums.size();
        vector<vector<int>> ans;

        for (int i = 0; i < n - 2; i++) {
            // 固定第一个数，跳过重复
            if (i > 0 && nums[i] == nums[i - 1]) continue;

            int l = i + 1, r = n - 1;
            while (l < r) {
                int s = nums[i] + nums[l] + nums[r];
                if (s < 0) l++;
                else if (s > 0) r--;
                else {
                    ans.push_back({nums[i], nums[l], nums[r]});
                    l++; r--;
                    // 跳过 l、r 侧的重复值
                    while (l < r && nums[l] == nums[l - 1]) l++;
                    while (l < r && nums[r] == nums[r + 1]) r--;
                }
            }
        }
        return ans;
    }
};
// 时间 O(n²)，空间 O(1)（不计排序）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记排序：不排序就无法用双指针单调移动，也无法方便地去重。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 只在一处去重：i、l、r 三个位置都可能产生重复三元组，三处都要跳过相同值。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 命中后忘记移动指针：找到一组答案后必须 l++、r--，否则会死循环在同一组 (l,r) 上。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：全零</div>
    <code>nums = [0,0,0] → [[0,0,0]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：不足三个元素</div>
    <code>nums = [1,2] → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：大量重复值</div>
    <code>nums = [-1,-1,0,1,1] → [[-1,0,1]]（只输出一组）</code>
</div>""",
    },

    "3sum-closest": {
        "type": "排序+双指针",
        "difficulty": "中等",
        "frontend_id": "16",
        "title": "最接近的三数之和",
        "time_complexity": "O(n²)",
        "space_complexity": "O(1)（不计排序）",
        "description": """<p>给你一个长度为 <code>n</code> 的整数数组 <code>nums</code> 和一个目标值 <code>target</code>。请你从 <code>nums</code> 中选出三个在<b>不同下标位置</b>的整数，使它们的和与 <code>target</code> 最接近。</p>
<p>返回这三个数的和。</p>
<p>假定每组输入只存在恰好一个解。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [-1,2,1,-4], target = 1</div>
    <div class="example-output">输出：2</div>
    <div class="example-explain">与 target 最接近的和是 2（-1 + 2 + 1 = 2）。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [0,0,0], target = 1</div>
    <div class="example-output">输出：0</div>
    <div class="example-explain">与 target 最接近的和是 0（0 + 0 + 0 = 0）。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：固定三元组中第一个数的位置（排序后作为最小候选）<br><b>维护</b>：外层枚举，每轮锁定 <code>nums[i]</code> 后在内层找最优的 (l,r)<br><b>更新</b>：<code>for i in range(n-2)</code>，每轮结束后 <code>i++</code></td></tr>
    <tr><td><code>l</code></td><td>int</td><td><b>定义</b>：在 i 右侧区间内指向较小候选值的左指针<br><b>维护</b>：当前三数和偏小则右移，以增大总和<br><b>更新</b>：初始 <code>l=i+1</code>；当 <code>s &lt; target</code> 时 <code>l++</code></td></tr>
    <tr><td><code>r</code></td><td>int</td><td><b>定义</b>：在 i 右侧区间内指向较大候选值的右指针<br><b>维护</b>：当前三数和偏大则左移，以减小总和<br><b>更新</b>：初始 <code>r=n-1</code>；当 <code>s &gt; target</code> 时 <code>r--</code></td></tr>
    <tr><td><code>best</code></td><td>int</td><td><b>定义</b>：截至目前与 <code>target</code> 最接近的三数之和<br><b>维护</b>：每算出一组 <code>s</code>，若 <code>|s-target|</code> 更小则刷新<br><b>更新</b>：初始可用前三项之和；遍历中 <code>if abs(s-target) &lt; abs(best-target): best=s</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先写暴力：三重循环枚举三个不同下标，计算和与 target 的差，取最小——O(n³)，能过但太慢。</p>
<p class="thinking-step">2. 重复在哪里？固定第一个数 <code>nums[i]</code> 后，问题变成「在剩余数组里找两数，使三数之和尽量接近 target」。</p>
<p class="thinking-step">3. 排序后，两数之和可以用双指针：和小了 <code>l++</code>，和大了 <code>r--</code>，每步都在缩小与 target 的差距方向移动。</p>
<p class="thinking-step">4. 与 #15 三数之和不同：本题只要一个最接近的和，不需要收集全部三元组，也<b>不必做 i/l/r 去重</b>（题目保证唯一解）。</p>
<p class="thinking-step">5. 若某次 <code>s == target</code>，已不可能更优，可直接返回 <code>s</code>；否则遍历完所有 i 后返回 <code>best</code>。</p>""",
        "code_steps": """<p class="code-step">1. 对 <code>nums</code> 升序排序</p>
<p class="code-step">2. 初始化 <code>best = nums[0]+nums[1]+nums[2]</code>（或第一个合法三数和）</p>
<p class="code-step">3. 外层 <code>for i in range(n-2)</code>，设 <code>l=i+1, r=n-1</code></p>
<p class="code-step">4. 当 <code>l&lt;r</code>：计算 <code>s=nums[i]+nums[l]+nums[r]</code>，用 <code>|s-target|</code> 更新 <code>best</code></p>
<p class="code-step">5. <code>s==target</code> 直接返回；<code>s&lt;target</code> 则 <code>l++</code>，否则 <code>r--</code></p>
<p class="code-step">6. 全部 i 枚举完毕，返回 <code>best</code></p>""",
        "code_python": """class Solution:
    def threeSumClosest(self, nums: list[int], target: int) -> int:
        nums.sort()
        n = len(nums)
        best = nums[0] + nums[1] + nums[2]

        for i in range(n - 2):
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if abs(s - target) < abs(best - target):
                    best = s
                if s == target:
                    return s
                elif s < target:
                    l += 1
                else:
                    r -= 1

        return best""",
        "code_cpp": """class Solution {
public:
    int threeSumClosest(vector<int>& nums, int target) {
        sort(nums.begin(), nums.end());
        int n = nums.size();
        int best = nums[0] + nums[1] + nums[2];

        for (int i = 0; i < n - 2; i++) {
            int l = i + 1, r = n - 1;
            while (l < r) {
                int s = nums[i] + nums[l] + nums[r];
                if (abs(s - target) < abs(best - target))
                    best = s;
                if (s == target) return s;
                else if (s < target) l++;
                else r--;
            }
        }
        return best;
    }
};
// 时间 O(n²)，空间 O(1)（不计排序）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记排序：不排序就无法保证双指针单调移动，可能漏掉最优解。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 照搬三数之和的去重逻辑：本题只返回一个最接近的和，且保证唯一解，<b>不需要</b>跳过重复的 i/l/r。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>s==target</code> 时仍继续循环：已命中最优，应立刻返回，否则浪费时间。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：恰好命中 target</div>
    <code>nums = [1,2,3], target = 6 → 6（1+2+3）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全零</div>
    <code>nums = [0,0,0], target = 1 → 0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：最小长度 n=3</div>
    <code>nums = [-1,2,1], target = 1 → 2（只有一组三元组）</code>
</div>""",
    },

    "validate-binary-search-tree": {
        "type": "BST验证",
        "difficulty": "中等",
        "frontend_id": "98",
        "title": "验证二叉搜索树",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)（递归栈）",
        "description": """<p>给你一个二叉树的根节点 <code>root</code>，判断其是否是一个<b>有效的二叉搜索树（BST）</b>。</p>
<p>有效 BST 定义如下：</p>
<ul>
<li>节点的左子树只包含<b>严格小于</b>当前节点的值</li>
<li>节点的右子树只包含<b>严格大于</b>当前节点的值</li>
<li>所有左子树和右子树自身必须也是二叉搜索树</li>
</ul>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：root = [2,1,3]</div>
    <div class="example-output">输出：true</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：root = [5,1,4,null,null,3,6]</div>
    <div class="example-output">输出：false</div>
    <div class="example-explain">根节点 5，右子树中节点 4 小于 5，违反 BST 性质。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>low</code></td><td>int / long</td><td><b>定义</b>：当前子树所有节点值的下界（不含）<br><b>维护</b>：进入左子树时不变；进入右子树时更新为 <code>root.val</code><br><b>更新</b>：递归右子树传 <code>low=root.val</code></td></tr>
    <tr><td><code>high</code></td><td>int / long</td><td><b>定义</b>：当前子树所有节点值的上界（不含）<br><b>维护</b>：进入右子树时不变；进入左子树时更新为 <code>root.val</code><br><b>更新</b>：递归左子树传 <code>high=root.val</code></td></tr>
    <tr><td><code>root.val</code></td><td>int</td><td><b>定义</b>：当前节点的值<br><b>维护</b>：必须满足 <code>low &lt; root.val &lt; high</code><br><b>更新</b>：不满足则整棵子树无效，立即返回 false</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想：只比较「当前节点和直接子节点」够不够？不够——比如 [5,1,4,null,null,3,6] 中 3 在 5 的右子树里，但 3 &lt; 5。</p>
<p class="thinking-step">2. 重复在哪里？每个节点不仅要大于左孩子、小于右孩子，还要落在「祖先链」允许的区间内。</p>
<p class="thinking-step">3. 优化：DFS 时携带合法区间 (low, high)，当前值必须在开区间内。</p>
<p class="thinking-step">4. 递归左子树时上界收紧为 root.val；递归右子树时下界收紧为 root.val。</p>
<p class="thinking-step">5. 空节点视为合法；任一子树不合法则整棵树不合法。</p>""",
        "code_steps": """<p class="code-step">1. 定义 <code>dfs(node, low, high)</code>：空节点返回 true</p>
<p class="code-step">2. 若 <code>node.val &lt;= low</code> 或 <code>node.val &gt;= high</code>，返回 false</p>
<p class="code-step">3. 左子树传 <code>(low, node.val)</code>，右子树传 <code>(node.val, high)</code></p>
<p class="code-step">4. 左右子树都合法才返回 true</p>
<p class="code-step">5. 入口调用 <code>dfs(root, -∞, +∞)</code>，注意用 long 避免 INT_MIN/INT_MAX 边界溢出</p>""",
        "code_python": """class Solution:
    def isValidBST(self, root: TreeNode) -> bool:
        def dfs(node, low, high):
            if not node:
                return True
            if not (low < node.val < high):
                return False
            return (
                dfs(node.left, low, node.val)
                and dfs(node.right, node.val, high)
            )

        return dfs(root, float("-inf"), float("inf"))""",
        "code_cpp": """class Solution {
public:
    bool isValidBST(TreeNode* root) {
        return dfs(root, LONG_MIN, LONG_MAX);
    }

    bool dfs(TreeNode* node, long low, long high) {
        if (!node) return true;
        if (node->val <= low || node->val >= high)
            return false;
        return dfs(node->left, low, node->val)
            && dfs(node->right, node->val, high);
    }
};
// 时间 O(n)，空间 O(n)（递归栈）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 只比较父子节点：右子树里可能出现小于根的值（经典反例 [5,1,4,null,null,3,6]）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 边界用 <code>&lt;=</code> / <code>&gt;=</code> 判非法：BST 要求<b>严格</b>小于/大于，相等也不合法。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> C++ 用 <code>INT_MIN/INT_MAX</code> 作初始边界时，节点值等于边界会溢出比较；应使用 <code>long</code> 或中序遍历 + <code>prev</code>。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单节点</div>
    <code>root = [1] → true</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：相等值</div>
    <code>root = [2,2,2] → false（左孩子等于根）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：INT 边界</div>
    <code>root = [2147483647] → true（long 边界不会误判）</code>
</div>""",
    },

    "two-sum": {
        "type": "哈希表",
        "difficulty": "简单",
        "frontend_id": "1",
        "title": "两数之和",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "description": """<p>给定一个整数数组 <code>nums</code> 和一个整数目标值 <code>target</code>，请你在该数组中找出<b>和为目标值</b> <code>target</code> 的那<b>两个</b>整数，并返回它们的数组下标。你可以假设每种输入只会对应一个答案，且同一个元素不能使用两遍。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [2,7,11,15], target = 9</div>
    <div class="example-output">输出：[0,1]（因为 nums[0] + nums[1] == 9）</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [3,2,4], target = 6</div>
    <div class="example-output">输出：[1,2]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>seen</code></td><td>map&lt;int,int&gt;</td><td><b>定义</b>：已扫描过的「值 → 下标」映射<br><b>维护</b>：每轮结束后，seen 里存着 nums[0..i] 每个值最后出现的下标<br><b>更新</b>：处理完 nums[i] 后 seen[nums[i]] = i</td></tr>
    <tr><td><code>target - x</code></td><td>int</td><td><b>定义</b>：当前元素 x 需要的「另一半」<br><b>维护</b>：随 x 变化<br><b>更新</b>：每轮用它去 seen 里查是否出现过</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 暴力：双重循环枚举所有 (i, j) 看和是否为 target，O(n²)。</p>
<p class="thinking-step">2. 重复在哪？对每个 x 都在「重新遍历」找 target - x，其实只要知道它之前是否出现过。</p>
<p class="thinking-step">3. 把「找另一半」变成查表：用哈希表存已扫过的值到下标，查找变 O(1)。</p>
<p class="thinking-step">4. 边扫边存：先查 target - x 是否在表里，再把 x 存入，保证不会用到自己。</p>""",
        "code_steps": """<p class="code-step">1. 初始化空哈希表 <code>seen</code></p>
<p class="code-step">2. 遍历数组，对每个 <code>x = nums[i]</code>：先查 <code>target - x</code> 是否在 seen 中</p>
<p class="code-step">3. 若在，返回 <code>[seen[target-x], i]</code></p>
<p class="code-step">4. 否则把 <code>seen[x] = i</code> 记入历史</p>""",
        "code_python": """class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}  # 值 -> 下标
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
        return []""",
        "code_cpp": """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> seen;  // 值 -> 下标
        for (int i = 0; i < nums.size(); i++) {
            auto it = seen.find(target - nums[i]);
            if (it != seen.end()) return {it->second, i};
            seen[nums[i]] = i;
        }
        return {};
    }
};
// 时间 O(n)，空间 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 必须「先查后存」：如果先把 x 存进表再查，可能会把自己当成另一半（当 target = 2*x 时）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回的是下标不是值；题目保证恰有一个答案，无需继续遍历。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 有重复值时哈希表会覆盖旧下标，但因为答案唯一，不影响正确性。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：包含负数</div>
    <code>nums = [-3,4,3,90], target = 0 → [0,2]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：两个相同值</div>
    <code>nums = [3,3], target = 6 → [0,1]</code>
</div>""",
    },

    "add-two-numbers": {
        "type": "链表指针",
        "difficulty": "中等",
        "frontend_id": "2",
        "title": "两数相加",
        "time_complexity": "O(max(m,n))",
        "space_complexity": "O(max(m,n))",
        "description": """<p>给你两个<b>非空</b>的链表，表示两个非负整数。它们每位数字都是按照<b>逆序</b>的方式存储的，并且每个节点只能存储一位数字。请你将两个数相加，并以相同形式返回一个表示和的链表。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：l1 = [2,4,3], l2 = [5,6,4]（即 342 + 465）</div>
    <div class="example-output">输出：[7,0,8]（即 807）</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dummy</code></td><td>ListNode*</td><td><b>定义</b>：哑结点，其 next 永远指向结果链表真正的头<br><b>维护</b>：不变，最后返回 dummy.next<br><b>更新</b>：不更新</td></tr>
    <tr><td><code>cur</code></td><td>ListNode*</td><td><b>定义</b>：结果链表的尾指针<br><b>维护</b>：始终指向已建好部分的最后一个节点<br><b>更新</b>：每接一个新节点后 cur = cur.next</td></tr>
    <tr><td><code>carry</code></td><td>int</td><td><b>定义</b>：进位（0 或 1）<br><b>维护</b>：等于上一位相加结果整除 10<br><b>更新</b>：carry = 当前位和 // 10</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 逆序存储正好模拟竖式加法：从个位开始逐位相加。</p>
<p class="thinking-step">2. 每位的和 = l1 当前位 + l2 当前位 + 进位；结果位是和对 10 取余，新进位是和整除 10。</p>
<p class="thinking-step">3. 用哑结点简化头节点的处理，避免单独判断第一个节点。</p>
<p class="thinking-step">4. 循环条件要包含 carry：两链表都走完但还有进位时（如 5+5）也要再建一个节点。</p>""",
        "code_steps": """<p class="code-step">1. 建哑结点 <code>dummy</code>，<code>cur = dummy</code>，<code>carry = 0</code></p>
<p class="code-step">2. 当 <code>l1</code> 或 <code>l2</code> 或 <code>carry</code> 非空时循环</p>
<p class="code-step">3. 求和 <code>s = carry + (l1?) + (l2?)</code>，同时后移 l1/l2</p>
<p class="code-step">4. <code>carry, digit = divmod(s, 10)</code>，新建节点接到 cur 后，cur 前移</p>
<p class="code-step">5. 返回 <code>dummy.next</code></p>""",
        "code_python": """# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def addTwoNumbers(self, l1: ListNode, l2: ListNode) -> ListNode:
        dummy = ListNode()   # 哑结点，dummy.next 是结果头
        cur = dummy          # 结果链表尾指针
        carry = 0            # 进位
        while l1 or l2 or carry:
            s = carry
            if l1:
                s += l1.val
                l1 = l1.next
            if l2:
                s += l2.val
                l2 = l2.next
            carry, digit = divmod(s, 10)
            cur.next = ListNode(digit)
            cur = cur.next
        return dummy.next""",
        "code_cpp": """class Solution {
public:
    ListNode* addTwoNumbers(ListNode* l1, ListNode* l2) {
        ListNode dummy;          // 哑结点
        ListNode* cur = &dummy;  // 结果链表尾指针
        int carry = 0;           // 进位
        while (l1 || l2 || carry) {
            int s = carry;
            if (l1) { s += l1->val; l1 = l1->next; }
            if (l2) { s += l2->val; l2 = l2->next; }
            carry = s / 10;
            cur->next = new ListNode(s % 10);
            cur = cur->next;
        }
        return dummy.next;
    }
};
// 时间 O(max(m,n))，空间 O(max(m,n))""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 循环条件别忘了 <code>carry</code>：最高位相加产生进位时还要补一个节点。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 两链表长度可能不同，取值前要判空。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 用哑结点避免「结果头节点」的特殊处理，最后返回 dummy.next 而不是 dummy。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：进位到新位</div>
    <code>l1 = [5], l2 = [5] → [0,1]（5+5=10）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：长度不等</div>
    <code>l1 = [9,9,9], l2 = [1] → [0,0,0,1]</code>
</div>""",
    },

    "longest-substring-without-repeating-characters": {
        "type": "可变滑窗",
        "difficulty": "中等",
        "frontend_id": "3",
        "title": "无重复字符的最长子串",
        "time_complexity": "O(n)",
        "space_complexity": "O(|Σ|)",
        "description": """<p>给定一个字符串 <code>s</code>，请你找出其中不含有重复字符的<b>最长子串</b>的长度。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "abcabcbb"</div>
    <div class="example-output">输出：3（最长子串是 "abc"）</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "pwwkew"</div>
    <div class="example-output">输出：3（最长子串是 "wke"）</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>left</code></td><td>int</td><td><b>定义</b>：当前无重复窗口的左边界<br><b>维护</b>：窗口 [left, right] 内永远无重复字符<br><b>更新</b>：遇到重复字符时，跳到该字符上次出现位置的右侧</td></tr>
    <tr><td><code>last[c]</code></td><td>map&lt;char,int&gt;</td><td><b>定义</b>：字符 c 最近一次出现的下标<br><b>维护</b>：随扫描实时更新<br><b>更新</b>：每轮 last[s[right]] = right</td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：无重复子串的最大长度<br><b>维护</b>：所有合法窗口长度的最大值<br><b>更新</b>：ans = max(ans, right - left + 1)</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 暴力：枚举所有子串再判断是否有重复，O(n³) 或 O(n²)。</p>
<p class="thinking-step">2. 重复在哪？right 右移时，其实只有「新加入的字符」可能造成重复。</p>
<p class="thinking-step">3. 用滑动窗口：right 不断右扩，一旦 s[right] 在窗口内出现过，就把 left 跳过去。</p>
<p class="thinking-step">4. 关键：记录每个字符最近的下标，跳 left 时只能往右（用 max/判断 last[c] >= left），不能倒退。</p>""",
        "code_steps": """<p class="code-step">1. <code>last = {}</code>，<code>left = 0</code>，<code>ans = 0</code></p>
<p class="code-step">2. 遍历 <code>right</code>：若 <code>s[right]</code> 在 last 中且 <code>last[c] >= left</code>，则 <code>left = last[c] + 1</code></p>
<p class="code-step">3. 更新 <code>last[s[right]] = right</code></p>
<p class="code-step">4. <code>ans = max(ans, right - left + 1)</code></p>""",
        "code_python": """class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        last = {}   # 字符 -> 最近一次出现的下标
        left = 0    # 当前窗口左边界
        ans = 0
        for right, c in enumerate(s):
            if c in last and last[c] >= left:
                left = last[c] + 1   # 左边界跳到重复字符右侧
            last[c] = right
            ans = max(ans, right - left + 1)
        return ans""",
        "code_cpp": """class Solution {
public:
    int lengthOfLongestSubstring(string s) {
        unordered_map<char, int> last;  // 字符 -> 最近下标
        int left = 0, ans = 0;
        for (int right = 0; right < (int)s.size(); right++) {
            char c = s[right];
            auto it = last.find(c);
            if (it != last.end() && it->second >= left)
                left = it->second + 1;
            last[c] = right;
            ans = max(ans, right - left + 1);
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(|Σ|)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 跳 left 前必须判断 <code>last[c] >= left</code>：字符虽出现过但若在窗口左侧之外，不能把 left 往回拉。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 先跳 left 再更新 last[c]，顺序不能反。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 窗口长度是 <code>right - left + 1</code>，不要漏掉 +1。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空串</div>
    <code>s = "" → 0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全相同</div>
    <code>s = "bbbb" → 1</code>
</div>""",
    },

    "median-of-two-sorted-arrays": {
        "type": "二分查找",
        "difficulty": "困难",
        "frontend_id": "4",
        "title": "寻找两个正序数组的中位数",
        "time_complexity": "O(log(min(m,n)))",
        "space_complexity": "O(1)",
        "description": """<p>给定两个大小分别为 <code>m</code> 和 <code>n</code> 的正序（从小到大）数组 <code>nums1</code> 和 <code>nums2</code>，请你找出并返回这两个正序数组的<b>中位数</b>。要求算法的时间复杂度为 O(log(m+n))。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums1 = [1,3], nums2 = [2]</div>
    <div class="example-output">输出：2.0（合并后 [1,2,3]，中位数 2）</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums1 = [1,2], nums2 = [3,4]</div>
    <div class="example-output">输出：2.5（合并后 [1,2,3,4]，中位数 (2+3)/2）</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：较短数组 nums1 划入「左半部分」的元素个数<br><b>维护</b>：二分范围 [0, m]<br><b>更新</b>：切分不合法时 i 左移或右移</td></tr>
    <tr><td><code>j</code></td><td>int</td><td><b>定义</b>：nums2 划入左半部分的个数，由 i 决定<br><b>维护</b>：始终满足 i + j = 左半部分总数<br><b>更新</b>：j = total_left - i</td></tr>
    <tr><td><code>L1,R1,L2,R2</code></td><td>int</td><td><b>定义</b>：两数组在切分处的左/右边界值（越界用 ±∞）<br><b>维护</b>：合法切分需 L1&le;R2 且 L2&le;R1<br><b>更新</b>：随 i,j 取值</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 暴力：合并两数组再取中位数，O(m+n)，但题目要 O(log)。</p>
<p class="thinking-step">2. 中位数的本质：把两数组切成「左右两半」，左半所有数 &le; 右半所有数，且左半元素个数固定。</p>
<p class="thinking-step">3. 只要确定 nums1 在哪切（切 i 个），nums2 的切法 j 就唯一确定（i + j = 左半总数）。</p>
<p class="thinking-step">4. 对较短数组二分 i：若 L1 &gt; R2 说明 i 太大，左移；若 L2 &gt; R1 说明 i 太小，右移。</p>""",
        "code_steps": """<p class="code-step">1. 保证在较短数组上二分（必要时交换）</p>
<p class="code-step">2. <code>total_left = (m + n + 1) // 2</code>，二分 <code>i</code> 于 [0, m]</p>
<p class="code-step">3. <code>j = total_left - i</code>，取四个边界 L1/R1/L2/R2（越界用 ±∞）</p>
<p class="code-step">4. 若 <code>L1 &le; R2 且 L2 &le; R1</code>：奇数返回 max(L1,L2)，偶数返回 (max(L1,L2)+min(R1,R2))/2</p>
<p class="code-step">5. 否则据 <code>L1 &gt; R2</code> 调整二分区间</p>""",
        "code_python": """class Solution:
    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:
        if len(nums1) > len(nums2):      # 保证在较短数组上二分
            nums1, nums2 = nums2, nums1
        m, n = len(nums1), len(nums2)
        total_left = (m + n + 1) // 2
        INF = float('inf')
        lo, hi = 0, m
        while lo <= hi:
            i = (lo + hi) // 2           # nums1 左边放 i 个
            j = total_left - i           # nums2 左边放 j 个
            L1 = nums1[i - 1] if i > 0 else -INF
            R1 = nums1[i]     if i < m else INF
            L2 = nums2[j - 1] if j > 0 else -INF
            R2 = nums2[j]     if j < n else INF
            if L1 <= R2 and L2 <= R1:    # 找到正确切分
                if (m + n) % 2 == 1:
                    return float(max(L1, L2))
                return (max(L1, L2) + min(R1, R2)) / 2
            elif L1 > R2:
                hi = i - 1               # i 太大
            else:
                lo = i + 1               # i 太小
        return 0.0""",
        "code_cpp": """class Solution {
public:
    double findMedianSortedArrays(vector<int>& a, vector<int>& b) {
        if (a.size() > b.size()) swap(a, b);
        int m = a.size(), n = b.size();
        int total_left = (m + n + 1) / 2;
        const long INF = LONG_MAX;
        int lo = 0, hi = m;
        while (lo <= hi) {
            int i = (lo + hi) / 2;       // a 左边放 i 个
            int j = total_left - i;      // b 左边放 j 个
            long L1 = (i > 0) ? a[i - 1] : -INF;
            long R1 = (i < m) ? a[i]     :  INF;
            long L2 = (j > 0) ? b[j - 1] : -INF;
            long R2 = (j < n) ? b[j]     :  INF;
            if (L1 <= R2 && L2 <= R1) {
                if ((m + n) % 2) return max(L1, L2);
                return (max(L1, L2) + min(R1, R2)) / 2.0;
            } else if (L1 > R2) hi = i - 1;
            else lo = i + 1;
        }
        return 0.0;
    }
};
// 时间 O(log(min(m,n)))，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 一定在<b>较短</b>数组上二分，否则 j 可能为负越界。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 切分越界处用 ±∞ 兜底，避免访问 nums[-1] 或 nums[m]。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>total_left</code> 用 <code>(m+n+1)//2</code>，奇偶统一，奇数时中位数落在左半最大值。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：一个数组为空</div>
    <code>nums1 = [], nums2 = [1] → 1.0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：不重叠</div>
    <code>nums1 = [1,2], nums2 = [3,4] → 2.5</code>
</div>""",
    },

    "longest-palindromic-substring": {
        "type": "中心扩展",
        "difficulty": "中等",
        "frontend_id": "5",
        "title": "最长回文子串",
        "time_complexity": "O(n²)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个字符串 <code>s</code>，找到 <code>s</code> 中最长的<b>回文子串</b>。回文是指正着读和反着读都一样的字符串。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "babad"</div>
    <div class="example-output">输出："bab"（"aba" 也是有效答案）</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "cbbd"</div>
    <div class="example-output">输出："bb"</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>l, r</code></td><td>int</td><td><b>定义</b>：从某中心向两侧扩展时的左右指针<br><b>维护</b>：扩展过程中 s[l..r] 始终是回文<br><b>更新</b>：只要 s[l]==s[r] 就 l--、r++</td></tr>
    <tr><td><code>start,end</code></td><td>int</td><td><b>定义</b>：目前发现的最长回文子串区间<br><b>维护</b>：始终记录最长的一段<br><b>更新</b>：某次扩展得到更长回文时更新</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 暴力：枚举所有子串再逐个判断是否回文，O(n³)。</p>
<p class="thinking-step">2. 回文有对称性：从中心往两边扩展，天然是回文，不必重复判断。</p>
<p class="thinking-step">3. 中心有两类：奇数长度以单个字符为中心，偶数长度以两个字符之间为中心。</p>
<p class="thinking-step">4. 枚举每个中心（共 2n-1 个）向外扩展，取最长的一段，O(n²) 时间、O(1) 空间。</p>""",
        "code_steps": """<p class="code-step">1. 写一个 <code>expand(l, r)</code>：当 <code>s[l]==s[r]</code> 时 l--、r++，返回最长回文区间</p>
<p class="code-step">2. 遍历每个 <code>i</code>：以 (i, i) 为中心求奇数回文</p>
<p class="code-step">3. 以 (i, i+1) 为中心求偶数回文</p>
<p class="code-step">4. 用更长者更新 <code>start, end</code>，最后返回 <code>s[start:end+1]</code></p>""",
        "code_python": """class Solution:
    def longestPalindrome(self, s: str) -> str:
        start, end = 0, 0   # 最长回文区间 [start, end]

        def expand(l: int, r: int):
            # 从中心向两侧扩展，返回最长回文的 (左, 右)
            while l >= 0 and r < len(s) and s[l] == s[r]:
                l -= 1
                r += 1
            return l + 1, r - 1

        for i in range(len(s)):
            l1, r1 = expand(i, i)       # 奇数长度中心
            if r1 - l1 > end - start:
                start, end = l1, r1
            l2, r2 = expand(i, i + 1)   # 偶数长度中心
            if r2 - l2 > end - start:
                start, end = l2, r2
        return s[start:end + 1]""",
        "code_cpp": """class Solution {
public:
    string longestPalindrome(string s) {
        int start = 0, maxLen = 1;
        auto expand = [&](int l, int r) {
            while (l >= 0 && r < (int)s.size() && s[l] == s[r]) { l--; r++; }
            if (r - l - 1 > maxLen) { maxLen = r - l - 1; start = l + 1; }
        };
        for (int i = 0; i < (int)s.size(); i++) {
            expand(i, i);       // 奇数长度
            expand(i, i + 1);   // 偶数长度
        }
        return s.substr(start, maxLen);
    }
};
// 时间 O(n²)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 别漏掉偶数长度中心 (i, i+1)，否则 "bb" 这类会漏解。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 扩展结束时循环多走了一步，真正的回文区间是 <code>[l+1, r-1]</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空串或单字符要能正确返回（maxLen 初始设 1，空串单独处理）。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：整体回文</div>
    <code>s = "aba" → "aba"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：无长回文</div>
    <code>s = "abc" → "a"（任意单字符）</code>
</div>""",
    },

    "zigzag-conversion": {
        "type": "字符串模拟",
        "difficulty": "中等",
        "frontend_id": "6",
        "title": "Z 字形变换",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "description": """<p>将一个给定字符串 <code>s</code> 根据给定的行数 <code>numRows</code>，以从上往下、从左到右进行 Z 字形排列后，按行读取拼接成新字符串并返回。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "PAYPALISHIRING", numRows = 3</div>
    <div class="example-output">输出："PAHNAPLSIIGYIR"</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "PAYPALISHIRING", numRows = 4</div>
    <div class="example-output">输出："PINALSIGYAHRPI"</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>rows</code></td><td>string[]</td><td><b>定义</b>：每一行按顺序累积的字符<br><b>维护</b>：第 r 行拿到所有落在该行的字符<br><b>更新</b>：每个字符追加到 rows[当前行]</td></tr>
    <tr><td><code>r</code></td><td>int</td><td><b>定义</b>：当前字符应放的行号<br><b>维护</b>：在 0 和 numRows-1 之间来回<br><b>更新</b>：r += step</td></tr>
    <tr><td><code>step</code></td><td>int</td><td><b>定义</b>：行号移动方向（+1 向下 / -1 向上）<br><b>维护</b>：到顶或到底时翻转<br><b>更新</b>：r==0 时置 +1，r==numRows-1 时置 -1</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 与其去推每个字符在 Z 形里的坐标公式，不如直接模拟「走 Z 字」的过程。</p>
<p class="thinking-step">2. 一个指针在行号上下移动：到第 0 行就向下走，到最后一行就向上走。</p>
<p class="thinking-step">3. 把每个字符按当前行号追加到对应行的缓冲区。</p>
<p class="thinking-step">4. 最后把所有行拼起来即可。numRows == 1 时没有折返，直接返回原串。</p>""",
        "code_steps": """<p class="code-step">1. 特判 <code>numRows == 1</code> 直接返回 s</p>
<p class="code-step">2. 建 <code>rows</code> 数组，<code>r = 0</code>，<code>step = 1</code></p>
<p class="code-step">3. 遍历每个字符，追加到 <code>rows[r]</code></p>
<p class="code-step">4. 到边界翻转方向：<code>r==0 → step=1</code>，<code>r==numRows-1 → step=-1</code>；然后 <code>r += step</code></p>
<p class="code-step">5. 拼接所有行返回</p>""",
        "code_python": """class Solution:
    def convert(self, s: str, numRows: int) -> str:
        if numRows == 1:
            return s
        rows = [''] * numRows   # 每一行累积的字符
        r = 0                   # 当前行号
        step = 1                # 方向：+1 向下，-1 向上
        for c in s:
            rows[r] += c
            if r == 0:
                step = 1
            elif r == numRows - 1:
                step = -1
            r += step
        return ''.join(rows)""",
        "code_cpp": """class Solution {
public:
    string convert(string s, int numRows) {
        if (numRows == 1) return s;
        vector<string> rows(numRows);
        int r = 0, step = 1;
        for (char c : s) {
            rows[r] += c;
            if (r == 0) step = 1;
            else if (r == numRows - 1) step = -1;
            r += step;
        }
        string ans;
        for (auto& row : rows) ans += row;
        return ans;
    }
};
// 时间 O(n)，空间 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 必须特判 <code>numRows == 1</code>，否则 step 永远翻转不了会死循环/越界。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 翻转方向的判断要在移动 r 之前做。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 直接模拟比推坐标公式更不易错，代码更短。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单行</div>
    <code>s = "ABCD", numRows = 1 → "ABCD"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：行数大于长度</div>
    <code>s = "AB", numRows = 5 → "AB"</code>
</div>""",
    },

    "reverse-integer": {
        "type": "数学模拟",
        "difficulty": "中等",
        "frontend_id": "7",
        "title": "整数反转",
        "time_complexity": "O(log|x|)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个 32 位的有符号整数 <code>x</code>，返回将 <code>x</code> 中的数字部分反转后的结果。如果反转后整数超过 32 位有符号整数的范围 [−2³¹, 2³¹−1]，就返回 <code>0</code>。假设环境不允许存储 64 位整数。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：x = 123</div>
    <div class="example-output">输出：321</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：x = -123</div>
    <div class="example-output">输出：-321</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：x = 120</div>
    <div class="example-output">输出：21</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>rev</code></td><td>int</td><td><b>定义</b>：已经反转好的部分<br><b>维护</b>：每弹出 x 的一位就接到 rev 末尾<br><b>更新</b>：rev = rev * 10 + digit</td></tr>
    <tr><td><code>digit</code></td><td>int</td><td><b>定义</b>：x 当前的最低位<br><b>维护</b>：每轮取 x % 10<br><b>更新</b>：取完后 x //= 10</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 反转数字就是不断「弹出 x 的最低位、推到结果 rev 的最低位」。</p>
<p class="thinking-step">2. 难点是 32 位溢出：不能先算完再判断，因为中间就可能溢出。</p>
<p class="thinking-step">3. 在 <code>rev = rev*10 + digit</code> 之前先判断：若 rev 已经超过 INT_MAX/10，或等于且下一位过大，就必然溢出，返回 0。</p>
<p class="thinking-step">4. Python 没有溢出，但仍按题意在结果超出 32 位范围时返回 0。</p>""",
        "code_steps": """<p class="code-step">1. 取符号，转成绝对值处理（Python）；C++ 用带符号取模</p>
<p class="code-step">2. 循环：<code>digit = x % 10</code>，<code>x //= 10</code></p>
<p class="code-step">3. 更新前先做溢出判断，安全后 <code>rev = rev*10 + digit</code></p>
<p class="code-step">4. 返回 rev（越界返回 0）</p>""",
        "code_python": """class Solution:
    def reverse(self, x: int) -> int:
        INT_MIN, INT_MAX = -2**31, 2**31 - 1
        sign = -1 if x < 0 else 1
        x = abs(x)
        rev = 0
        while x:
            rev = rev * 10 + x % 10
            x //= 10
        rev *= sign
        return rev if INT_MIN <= rev <= INT_MAX else 0""",
        "code_cpp": """class Solution {
public:
    int reverse(int x) {
        int rev = 0;
        while (x != 0) {
            int digit = x % 10;   // C++ 对负数取模结果为负，符号自然保留
            x /= 10;
            // 溢出判断必须在更新之前
            if (rev > INT_MAX / 10 || (rev == INT_MAX / 10 && digit > 7)) return 0;
            if (rev < INT_MIN / 10 || (rev == INT_MIN / 10 && digit < -8)) return 0;
            rev = rev * 10 + digit;
        }
        return rev;
    }
};
// 时间 O(log|x|)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 溢出判断必须在 <code>rev*10+digit</code> 之前，否则中间结果已经溢出（题设不许用 64 位）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> INT_MAX 末位是 7、INT_MIN 末位是 8，边界时要单独比较最后一位。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 末尾有 0 会自然消失（120 → 21），无需特殊处理。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：反转后溢出</div>
    <code>x = 1534236469 → 0（超过 INT_MAX）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：末尾为 0</div>
    <code>x = 120 → 21</code>
</div>""",
    },

    "string-to-integer-atoi": {
        "type": "字符串模拟",
        "difficulty": "中等",
        "frontend_id": "8",
        "title": "字符串转换整数 (atoi)",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>请你实现一个 <code>myAtoi(string s)</code> 函数，将字符串转换成一个 32 位有符号整数。规则：先丢弃前导空格；然后可选地读取一个正负号；接着尽可能多地读取连续数字；将结果限制在 [−2³¹, 2³¹−1] 内，越界则取边界值。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "42"</div>
    <div class="example-output">输出：42</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "   -42 abc"</div>
    <div class="example-output">输出：-42</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：s = "words and 987"</div>
    <div class="example-output">输出：0（第一个非空字符不是数字或符号）</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：当前扫描到的位置<br><b>维护</b>：依次跳过空格、符号、数字<br><b>更新</b>：每处理一个字符 i++</td></tr>
    <tr><td><code>sign</code></td><td>int</td><td><b>定义</b>：正负号（+1 / -1）<br><b>维护</b>：只在符号位设置一次<br><b>更新</b>：遇到 '-' 置 -1，'+' 置 +1</td></tr>
    <tr><td><code>num</code></td><td>int</td><td><b>定义</b>：目前累积的数字（绝对值）<br><b>维护</b>：每读一位 num = num*10 + 该位<br><b>更新</b>：累积后立即用 sign*num 判断是否越界并截断</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 这是一道模拟题，关键是严格按「空格 → 符号 → 数字」的顺序处理，遇到非法就停。</p>
<p class="thinking-step">2. 只在开头跳一次前导空格；符号最多一个；数字一直读到非数字为止。</p>
<p class="thinking-step">3. 溢出处理：每累加一位就检查 sign*num 是否已超出 32 位范围，超了直接返回边界值。</p>
<p class="thinking-step">4. 首个有效字符若不是数字或符号，直接返回 0。</p>""",
        "code_steps": """<p class="code-step">1. <code>i = 0</code>，跳过所有前导空格</p>
<p class="code-step">2. 若当前是 '+'/'-'，记录 <code>sign</code> 并 i++</p>
<p class="code-step">3. 循环读数字：<code>num = num*10 + (c - '0')</code></p>
<p class="code-step">4. 每步判断 <code>sign*num</code> 是否 &le; INT_MIN 或 &ge; INT_MAX，越界返回边界</p>
<p class="code-step">5. 返回 <code>sign * num</code></p>""",
        "code_python": """class Solution:
    def myAtoi(self, s: str) -> int:
        INT_MIN, INT_MAX = -2**31, 2**31 - 1
        i, n = 0, len(s)
        while i < n and s[i] == ' ':      # 1. 跳过前导空格
            i += 1
        sign = 1
        if i < n and s[i] in '+-':        # 2. 处理符号
            sign = -1 if s[i] == '-' else 1
            i += 1
        num = 0
        while i < n and s[i].isdigit():   # 3. 逐位累积
            num = num * 10 + int(s[i])
            i += 1
            if sign * num <= INT_MIN:     # 4. 提前判溢出并截断
                return INT_MIN
            if sign * num >= INT_MAX:
                return INT_MAX
        return sign * num""",
        "code_cpp": """class Solution {
public:
    int myAtoi(string s) {
        int i = 0, n = s.size();
        while (i < n && s[i] == ' ') i++;        // 1. 跳过空格
        int sign = 1;
        if (i < n && (s[i] == '+' || s[i] == '-')) {
            sign = (s[i] == '-') ? -1 : 1;       // 2. 符号
            i++;
        }
        long num = 0;                            // 用 long 累积防溢出
        while (i < n && isdigit(s[i])) {
            num = num * 10 + (s[i] - '0');       // 3. 累积
            i++;
            if (sign * num <= INT_MIN) return INT_MIN;   // 4. 截断
            if (sign * num >= INT_MAX) return INT_MAX;
        }
        return (int)(sign * num);
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 前导空格只在最开头跳；数字中间或之后的空格意味着结束。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 符号最多一个，"+-2" 这类第二个符号即非法，停止读取。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 边累积边判溢出并截断到 INT_MIN/INT_MAX，不要等全部读完再判。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：仅空格</div>
    <code>s = "   " → 0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：正溢出</div>
    <code>s = "91283472332" → 2147483647</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：符号后无数字</div>
    <code>s = "+" → 0</code>
</div>""",
    },

    "palindrome-number": {
        "type": "数学模拟",
        "difficulty": "简单",
        "frontend_id": "9",
        "title": "回文数",
        "time_complexity": "O(log₁₀ n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个整数 <code>x</code>，如果 <code>x</code> 是一个<b>回文整数</b>，返回 <code>true</code>；否则返回 <code>false</code>。回文数是指正序（从左向右）和倒序（从右向左）读都一样的整数。例如 <code>121</code> 是回文，而 <code>123</code> 不是。<b>进阶：能不能把整数转为字符串来解决？</b></p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：x = 121</div>
    <div class="example-output">输出：true</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：x = -121</div>
    <div class="example-output">输出：false（从右往左读是 121-，不是回文）</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：x = 10</div>
    <div class="example-output">输出：false（从右往左读是 01）</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>reverted</code></td><td>int</td><td><b>定义</b>：数字<b>后半部分</b>反转后的值<br><b>维护</b>：每轮把 x 的当前末位接到 reverted 末尾<br><b>更新</b>：reverted = reverted * 10 + x % 10</td></tr>
    <tr><td><code>x</code></td><td>int</td><td><b>定义</b>：尚未处理的<b>前半部分</b><br><b>维护</b>：每轮去掉一个末位<br><b>更新</b>：x //= 10，当 x &le; reverted 时循环停止（已过半）</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：把整数转成字符串，判断是否与其反转相等——但进阶要求不借助字符串。</p>
<p class="thinking-step">2. 反转整个数字再比较？可能溢出。观察到：只需反转「后半部分」，再和「前半部分」比即可。</p>
<p class="thinking-step">3. 负数一定不是回文；末位是 0 且本身非 0 的数（如 10、100）也不是（首位不能是 0）。</p>
<p class="thinking-step">4. 一边砍掉 x 的末位、一边拼到 reverted，当 reverted 追上或超过 x 时正好过半，停止。</p>""",
        "code_steps": """<p class="code-step">1. 特判：<code>x &lt; 0</code> 或 <code>(x % 10 == 0 且 x != 0)</code> 直接返回 false</p>
<p class="code-step">2. 循环 <code>while x &gt; reverted</code>：<code>reverted = reverted*10 + x%10</code>，<code>x //= 10</code></p>
<p class="code-step">3. 偶数位：<code>x == reverted</code>；奇数位：中间位在 reverted 上，用 <code>x == reverted // 10</code> 去掉它</p>
<p class="code-step">4. 两者任一成立即为回文</p>""",
        "code_python": """class Solution:
    def isPalindrome(self, x: int) -> bool:
        # 负数，或末位为 0 但本身非 0（如 10），都不是回文
        if x < 0 or (x % 10 == 0 and x != 0):
            return False
        reverted = 0  # 后半部分反转值
        while x > reverted:
            reverted = reverted * 10 + x % 10
            x //= 10
        # 偶数位长度 x == reverted；奇数位长度去掉中间位 reverted // 10
        return x == reverted or x == reverted // 10""",
        "code_cpp": """class Solution {
public:
    bool isPalindrome(int x) {
        // 负数，或末位为 0 但本身非 0，都不是回文
        if (x < 0 || (x % 10 == 0 && x != 0)) return false;
        int reverted = 0;  // 后半部分反转值
        while (x > reverted) {
            reverted = reverted * 10 + x % 10;
            x /= 10;
        }
        // 偶数位 x == reverted；奇数位去掉中间位 reverted / 10
        return x == reverted || x == reverted / 10;
    }
};
// 时间 O(log₁₀ n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 负数不是回文；末位为 0 且非 0 的数（10、120）也不是，必须先特判。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 只反转一半可避免整型溢出，比反转整个数字更稳。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 奇数位时中间那位落在 reverted 上，比较时要用 <code>reverted // 10</code> 去掉。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单个数字</div>
    <code>x = 0 → true</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：奇数位回文</div>
    <code>x = 12321 → true（reverted=123，x=12，12==123//10）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：末位为 0</div>
    <code>x = 10 → false</code>
</div>""",
    },

    "regular-expression-matching": {
        "type": "二维DP",
        "difficulty": "困难",
        "frontend_id": "10",
        "title": "正则表达式匹配",
        "time_complexity": "O(mn)",
        "space_complexity": "O(mn) / O(n)",
        "description": """<p>给你一个字符串 <code>s</code> 和一个字符规律 <code>p</code>，请你来实现一个支持 <code>'.'</code> 和 <code>'*'</code> 的正则表达式匹配。</p>
<ul>
<li><code>'.'</code> 匹配任意单个字符</li>
<li><code>'*'</code> 匹配零个或多个前面的那一个元素</li>
</ul>
<p>返回一个布尔值，表示匹配是否覆盖整个输入字符串（而非部分）。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "aa", p = "a"</div>
    <div class="example-output">输出：false</div>
    <div class="example-explain">"a" 无法匹配 "aa" 整个字符串。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "aa", p = "a*"</div>
    <div class="example-output">输出：true</div>
    <div class="example-explain">因为 '*' 代表可以匹配零个或多个前面的那一个元素，在这里前面的元素就是 'a'。因此，字符串 "aa" 可被视为 'a' 重复了一次。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：s = "ab", p = ".*"</div>
    <div class="example-output">输出：true</div>
    <div class="example-explain">".*" 表示可匹配零个或多个（'*'）任意字符（'.'）。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dp[i][j]</code></td><td>bool[][]</td><td><b>定义</b>：<code>s</code> 的前 <code>i</code> 个字符能否被 <code>p</code> 的前 <code>j</code> 个字符<b>完整</b>匹配<br><b>维护</b>：只依赖更小的子问题 <code>dp[i-1][j-1]</code>、<code>dp[i][j-2]</code>、<code>dp[i-1][j]</code><br><b>更新</b>：若 <code>p[j-1]</code> 是普通字符或 <code>'.'</code>，看当前位能否对上并继承 <code>dp[i-1][j-1]</code>；若是 <code>'*'</code>，先尝试「匹配 0 次」(<code>dp[i][j-2]</code>)，再尝试「多匹配 1 个」(<code>dp[i-1][j]</code>)</td></tr>
    <tr><td><code>i, j</code></td><td>int</td><td><b>定义</b>：分别表示已消耗的 <code>s</code> 前缀长度、<code>p</code> 前缀长度<br><b>维护</b>：<code>i</code> 从 0 到 <code>m</code>，<code>j</code> 从 0 到 <code>n</code> 递增填表<br><b>更新</b>：答案在 <code>dp[m][n]</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：遇到 <code>'*'</code> 就递归枚举「匹配 0 次 / 1 次 / 2 次…」，指数级回溯，<code>s=20, p=20</code> 也会超时。</p>
<p class="thinking-step">2. 重复在哪里？同样的 <code>(i, j)</code>（还剩多少 <code>s</code>、还剩多少 <code>p</code>）会被反复访问——典型重叠子问题。</p>
<p class="thinking-step">3. 子问题定义：「<code>s</code> 的前 <code>i</code> 个能否被 <code>p</code> 的前 <code>j</code> 个完整匹配？」自然落到二维 DP。</p>
<p class="thinking-step">4. 难点在 <code>'*'</code>：它永远跟在「前一个字符」后面，可以吃掉 0 个（直接看 <code>dp[i][j-2]</code>），也可以再多吃 1 个当前字符（看 <code>dp[i-1][j]</code> 且 <code>s[i-1]</code> 与 <code>p[j-2]</code> 能匹配）。</p>
<p class="thinking-step">5. 边界：<code>dp[0][0]=true</code>；空串匹配 <code>a*b*c*</code> 这类模式时，只有遇到 <code>'*'</code> 才能跳过一对字符：<code>dp[0][j] = dp[0][j-2]</code>。</p>""",
        "code_steps": """<p class="code-step">1. 建表 <code>dp[(m+1)][(n+1)]</code>，<code>dp[0][0]=true</code></p>
<p class="code-step">2. 初始化第 0 行：若 <code>p[j-1]=='*'</code>，则 <code>dp[0][j] = dp[0][j-2]</code>（空串吃掉 <code>x*</code>）</p>
<p class="code-step">3. 双重循环填表：若 <code>p[j-1]=='*'</code>，先 <code>dp[i][j]=dp[i][j-2]</code>，再若 <code>s[i-1]</code> 与 <code>p[j-2]</code> 匹配则 <code>dp[i][j] |= dp[i-1][j]</code></p>
<p class="code-step">4. 否则若当前字符能匹配，<code>dp[i][j] = dp[i-1][j-1]</code></p>
<p class="code-step">5. 返回 <code>dp[m][n]</code></p>""",
        "code_python": """class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        m, n = len(s), len(p)
        # dp[i][j]：s 前 i 个字符能否被 p 前 j 个完整匹配
        dp = [[False] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = True

        # 空串匹配 a*b*、.* 等：只有 '*' 能跳过前一个字符
        for j in range(2, n + 1):
            if p[j - 1] == '*':
                dp[0][j] = dp[0][j - 2]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if p[j - 1] == '*':
                    # 匹配 0 次：直接跳过 "x*"
                    dp[i][j] = dp[i][j - 2]
                    # 多匹配 1 个：s[i-1] 与 p[j-2] 能对上
                    if p[j - 2] == '.' or s[i - 1] == p[j - 2]:
                        dp[i][j] = dp[i][j] or dp[i - 1][j]
                elif p[j - 1] == '.' or s[i - 1] == p[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]

        return dp[m][n]""",
        "code_cpp": """class Solution {
public:
    bool isMatch(string s, string p) {
        int m = s.size(), n = p.size();
        vector<vector<bool>> dp(m + 1, vector<bool>(n + 1, false));
        dp[0][0] = true;

        for (int j = 2; j <= n; j++) {
            if (p[j - 1] == '*')
                dp[0][j] = dp[0][j - 2];
        }

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (p[j - 1] == '*') {
                    dp[i][j] = dp[i][j - 2];
                    if (p[j - 2] == '.' || s[i - 1] == p[j - 2])
                        dp[i][j] = dp[i][j] || dp[i - 1][j];
                } else if (p[j - 1] == '.' || s[i - 1] == p[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1];
                }
            }
        }
        return dp[m][n];
    }
};
// 时间 O(mn)，空间 O(mn)，可滚动数组优化到 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>'*'</code> 永远绑定它<b>前面</b>的那个字符，转移时看的是 <code>p[j-2]</code>，不是 <code>p[j-1]</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 遇到 <code>'*'</code> 要先处理「匹配 0 次」(<code>dp[i][j-2]</code>)，再考虑「多吃一个」；顺序写反容易漏状态。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空串行初始化不能漏：像 <code>"a*b*"</code>、<code>".*"</code> 对空串也应为 true，只有 <code>p[j-1]=='*'</code> 时才能 <code>dp[0][j]=dp[0][j-2]</code>。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：模式比串长</div>
    <code>s = "a", p = "aa" → false</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：.* 通吃</div>
    <code>s = "mississippi", p = "mis*is*p*." → false（* 不能跨字符乱配）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：空串 + 纯星号模式</div>
    <code>s = "", p = "a*b*" → true</code>
</div>""",
    },
    "container-with-most-water": {
        "type": "双指针",
        "difficulty": "中等",
        "frontend_id": "11",
        "title": "盛最多水的容器",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给定一个长度为 <code>n</code> 的整数数组 <code>height</code>。有 <code>n</code> 条垂线，第 <code>i</code> 条线的两个端点是 <code>(i, 0)</code> 和 <code>(i, height[i])</code>。</p>
<p>找出其中的两条线，使得它们与 <code>x</code> 轴共同构成的容器可以容纳最多的水。</p>
<p>返回容器可以储存的最大水量。</p>
<p><strong>说明：</strong>你不能倾斜容器。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：height = [1,8,6,2,5,4,8,3,7]</div>
    <div class="example-output">输出：49</div>
    <div class="example-explain">垂直线代表输入数组 [1,8,6,2,5,4,8,3,7]。在此情况下，容器能够容纳水（表示为蓝色部分）的最大值为 49（索引 1 和 8 之间，min(8,7)×7=49）。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：height = [1,1]</div>
    <div class="example-output">输出：1</div>
    <div class="example-explain">两条线高度均为 1，宽度为 1，面积为 1。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>l, r</code></td><td>int</td><td><b>定义</b>：左右两条候选垂线的下标，当前考虑的容器边界<br><b>维护</b>：初始 <code>l=0, r=n-1</code>，每次向内移动<b>较短</b>一侧的指针<br><b>更新</b>：当 <code>height[l] &lt;= height[r]</code> 时 <code>l++</code>，否则 <code>r--</code></td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：遍历过程中见过的最大容器面积<br><b>维护</b>：每轮用当前 <code>(l, r)</code> 计算面积并与 <code>ans</code> 取 max<br><b>更新</b>：<code>ans = max(ans, min(height[l], height[r]) * (r - l))</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：枚举所有线对 <code>(i, j)</code>，面积 <code>min(height[i], height[j]) × (j-i)</code>，双重循环 O(n²)，<code>n=10⁵</code> 会超时。</p>
<p class="thinking-step">2. 重复在哪里？固定 <code>l</code> 时从右往左扫 <code>r</code>，和固定 <code>r</code> 从左往右扫 <code>l</code> 本质一样——都在暴力枚举宽度。</p>
<p class="thinking-step">3. 双指针：从两端出发，宽度最大；要尝试更大面积只能缩宽度，所以每次必须移动一侧指针。</p>
<p class="thinking-step">4. 贪心关键：移动<b>较短</b>的那一侧。较短边是当前容器的「短板」，留着它面积不可能变大（宽度还变小了）；移走短板才有机会遇到更高的线。</p>
<p class="thinking-step">5. 正确性直觉：若移走较长边，宽度 -1 且高度仍受短板限制，面积一定不比现在大，可以安全丢弃这一侧的所有配对。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>l=0, r=n-1, ans=0</code></p>
<p class="code-step">2. 当 <code>l &lt; r</code>：计算 <code>area = min(height[l], height[r]) * (r - l)</code>，更新 <code>ans</code></p>
<p class="code-step">3. 若 <code>height[l] &lt;= height[r]</code>，<code>l++</code>；否则 <code>r--</code></p>
<p class="code-step">4. 循环结束返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def maxArea(self, height: List[int]) -> int:
        l, r = 0, len(height) - 1
        ans = 0
        while l < r:
            # 当前容器面积：短板高度 × 宽度
            h = min(height[l], height[r])
            ans = max(ans, h * (r - l))
            # 移动较短一侧，才可能找到更大面积
            if height[l] <= height[r]:
                l += 1
            else:
                r -= 1
        return ans""",
        "code_cpp": """class Solution {
public:
    int maxArea(vector<int>& height) {
        int l = 0, r = height.size() - 1;
        int ans = 0;
        while (l < r) {
            int h = min(height[l], height[r]);
            ans = max(ans, h * (r - l));
            if (height[l] <= height[r])
                l++;
            else
                r--;
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 面积公式是 <code>min(左高, 右高) × 宽度</code>，不是 <code>max</code> 或两高之和。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 移动指针时应移<b>较短</b>一侧（相等时移哪边都行，习惯 <code>l++</code>）；移较长一侧会漏掉更优解。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 循环条件是 <code>l &lt; r</code> 而非 <code>l &lt;= r</code>，至少两条线才能构成容器。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：最短数组</div>
    <code>height = [1, 1] → 1</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单调递增</div>
    <code>height = [1, 2, 3, 4, 5] → 6</code>（首尾 min(1,5)×4=4，但中间 2 和 5 可得 6）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：含零高度</div>
    <code>height = [0, 2, 0] → 0</code>（与 0 高度线构成的容器面积为 0）
</div>""",
    },

    "integer-to-roman": {
        "type": "数学模拟",
        "difficulty": "中等",
        "frontend_id": "12",
        "title": "整数转罗马数字",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
        "description": """<p>七个不同的符号代表罗马数字，其值如下：</p>
<table>
<thead><tr><th>符号</th><th>值</th></tr></thead>
<tbody>
<tr><td>I</td><td>1</td></tr>
<tr><td>V</td><td>5</td></tr>
<tr><td>X</td><td>10</td></tr>
<tr><td>L</td><td>50</td></tr>
<tr><td>C</td><td>100</td></tr>
<tr><td>D</td><td>500</td></tr>
<tr><td>M</td><td>1000</td></tr>
</tbody>
</table>
<p>罗马数字通过从最高到最低的小数位值转换形成。规则如下：</p>
<ul>
<li>若该值不是以 4 或 9 开头，选择可从输入中减去的最大符号，附加到结果并减去其值。</li>
<li>若该值以 4 或 9 开头，使用减法形式（如 4=IV，9=IX，40=XL，90=XC，400=CD，900=CM）。</li>
<li>符号 I、X、C、M 最多连续出现 3 次；V、L、D 不能连续出现。</li>
</ul>
<p>给定一个整数，将其转换为罗马数字。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：num = 3749</div>
    <div class="example-output">输出："MMMDCCXLIX"</div>
    <div class="example-explain">3000=MMM，700=DCC，40=XL，9=IX。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：num = 58</div>
    <div class="example-output">输出："LVIII"</div>
    <div class="example-explain">50=L，8=VIII。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：num = 1994</div>
    <div class="example-output">输出："MCMXCIV"</div>
    <div class="example-explain">1000=M，900=CM，90=XC，4=IV。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>vals, syms</code></td><td>int[], string[]</td><td><b>定义</b>：预置的「数值-符号」对，按从大到小排列，含减法形式（900=CM 等）<br><b>维护</b>：固定不变，覆盖 1~3999 所有合法片段<br><b>更新</b>：无需更新，遍历时按下标 <code>i</code> 依次尝试</td></tr>
    <tr><td><code>num</code></td><td>int</td><td><b>定义</b>：待转换的剩余整数值<br><b>维护</b>：每拼出一个符号就从 <code>num</code> 中减去对应数值<br><b>更新</b>：<code>num -= vals[i]</code>，直到 <code>num == 0</code></td></tr>
    <tr><td><code>res</code></td><td>string</td><td><b>定义</b>：已拼接的罗马数字结果<br><b>维护</b>：每次确定一个符号后追加到末尾<br><b>更新</b>：<code>res += syms[i]</code></td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：当前尝试的「数值-符号」对下标<br><b>维护</b>：从 0 遍历到末尾；同一 <code>i</code> 可重复使用（如 3000 拼三次 M）<br><b>更新</b>：当 <code>num &lt; vals[i]</code> 时 <code>i++</code> 尝试更小的值</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：把 1~3999 每个数都预转成罗马串存哈希表，查询 O(1)——可行但毫无算法味，也学不到转换规则。</p>
<p class="thinking-step">2. 按位拆分？个位、十位、百位、千位分别映射——可以，但要手写 4×10 种情况（含 4、9 的减法形式），代码冗长易错。</p>
<p class="thinking-step">3. 关键观察：罗马数字是<b>贪心</b>的——每次取不超过当前 <code>num</code> 的最大「合法片段」（1000/900/500/400/.../1），拼上对应符号，减去该值，重复直到 <code>num=0</code>。</p>
<p class="thinking-step">4. 为什么贪心正确？合法片段集合固定且有序，每次取最大片段等价于从高位到低位逐段分解，与手工转换一致。</p>
<p class="thinking-step">5. 实现技巧：把减法形式（900、400、90、40、9、4）也放进值数组，这样内层只需 <code>while num &gt;= vals[i]</code> 循环，无需特判 4 和 9。</p>""",
        "code_steps": """<p class="code-step">1. 预置 <code>vals = [1000,900,500,400,100,90,50,40,10,9,5,4,1]</code> 和对应 <code>syms</code></p>
<p class="code-step">2. 初始化空字符串 <code>res</code>，<code>i = 0</code></p>
<p class="code-step">3. 当 <code>num &gt; 0</code>：若 <code>num &gt;= vals[i]</code>，则 <code>res += syms[i]</code>，<code>num -= vals[i]</code>；否则 <code>i++</code></p>
<p class="code-step">4. <code>num == 0</code> 时返回 <code>res</code></p>""",
        "code_python": """class Solution:
    def intToRoman(self, num: int) -> str:
        vals = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        res = []
        i = 0
        while num > 0:
            # 当前值能拼就拼，同一符号可重复（如 3000 → MMM）
            while num >= vals[i]:
                res.append(syms[i])
                num -= vals[i]
            i += 1
        return "".join(res)""",
        "code_cpp": """class Solution {
public:
    string intToRoman(int num) {
        vector<int> vals = {1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1};
        vector<string> syms = {"M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"};
        string res;
        for (int i = 0; num > 0; ++i) {
            while (num >= vals[i]) {
                res += syms[i];
                num -= vals[i];
            }
        }
        return res;
    }
};
// 时间 O(1)（最多 15 次外层 + 常数次内层），空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 值数组必须包含减法形式（900、400、90、40、9、4），否则 4 和 9 无法正确表示。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 内层用 <code>while num &gt;= vals[i]</code> 而非 <code>if</code>，否则 3000 只能拼一个 M。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 值数组必须从大到小排列；从小到大会导致先拼 I 再拼 V，结果错误。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：最小值</div>
    <code>num = 1 → "I"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：减法形式 4 和 9</div>
    <code>num = 4 → "IV"</code>，<code>num = 9 → "IX"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：最大值</div>
    <code>num = 3999 → "MMMCMXCIX"</code>（含 900、90、9 三种减法形式）
</div>""",
    },

    "roman-to-integer": {
        "type": "数学模拟",
        "difficulty": "简单",
        "frontend_id": "13",
        "title": "罗马数字转整数",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>罗马数字包含以下七种字符：<code>I</code>、<code>V</code>、<code>X</code>、<code>L</code>、<code>C</code>、<code>D</code> 和 <code>M</code>。</p>
<table>
<thead><tr><th>字符</th><th>数值</th></tr></thead>
<tbody>
<tr><td>I</td><td>1</td></tr>
<tr><td>V</td><td>5</td></tr>
<tr><td>X</td><td>10</td></tr>
<tr><td>L</td><td>50</td></tr>
<tr><td>C</td><td>100</td></tr>
<tr><td>D</td><td>500</td></tr>
<tr><td>M</td><td>1000</td></tr>
</tbody>
</table>
<p>通常情况下，小的数字在大的数字右边；但若小的数字在大的数字左边，则表示减去该值（如 <code>IV</code>=4，<code>IX</code>=9）。该减法规则仅适用于六种情况：<code>I</code> 在 <code>V/X</code> 前、<code>X</code> 在 <code>L/C</code> 前、<code>C</code> 在 <code>D/M</code> 前。</p>
<p>给定一个罗马数字，将其转换成整数。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "III"</div>
    <div class="example-output">输出：3</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "IV"</div>
    <div class="example-output">输出：4</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：s = "IX"</div>
    <div class="example-output">输出：9</div>
</div>
<div class="example-block">
    <h4>示例 4</h4>
    <div class="example-input">输入：s = "LVIII"</div>
    <div class="example-output">输出：58</div>
    <div class="example-explain">L = 50，V = 5，III = 3。</div>
</div>
<div class="example-block">
    <h4>示例 5</h4>
    <div class="example-input">输入：s = "MCMXCIV"</div>
    <div class="example-output">输出：1994</div>
    <div class="example-explain">M = 1000，CM = 900，XC = 90，IV = 4。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>roman</code></td><td>dict</td><td><b>定义</b>：字符到数值的映射表（I→1, V→5, …, M→1000）<br><b>维护</b>：固定不变，覆盖全部 7 种符号<br><b>更新</b>：无需更新，查询 <code>roman[s[i]]</code> 即可</td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：从左到右扫描后累计的整数值<br><b>维护</b>：每处理一个字符，按「加或减」规则更新<br><b>更新</b>：若当前字符值 &lt; 下一字符值则 <code>ans -= val</code>，否则 <code>ans += val</code></td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：当前扫描到的字符下标<br><b>维护</b>：从 0 遍历到 <code>len(s)-1</code>，每次右移一位<br><b>更新</b>：<code>i++</code>；判断减法时需偷看 <code>s[i+1]</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：把每个字符的值查表直接相加——<code>IV</code> 会变成 1+5=6，显然错了。</p>
<p class="thinking-step">2. 找重复：减法形式都是「小字符在大字符左边」，如 <code>I</code> 在 <code>V</code> 前表示 5-1=4。只需处理这 6 种特例？可以，但要写一堆 <code>if s[i:i+2] in ...</code>，冗长且难维护。</p>
<p class="thinking-step">3. 统一规则：从左到右扫，若 <code>roman[s[i]] &lt; roman[s[i+1]]</code>，说明当前位被「借走」做减法，<code>ans -= roman[s[i]]</code>；否则正常累加。这样 <code>IV</code>、<code>IX</code>、<code>CM</code> 等全部自动处理。</p>
<p class="thinking-step">4. 另一种等价写法是从右往左扫：若当前值 &lt; 已处理的右边值就减，否则加——思路相同，选一种写顺手的即可。</p>
<p class="thinking-step">5. 复杂度：字符串最长 15，一次线性扫描 O(n)，哈希表 O(1) 空间，足够高效。</p>""",
        "code_steps": """<p class="code-step">1. 建立 <code>roman</code> 字符→数值映射表</p>
<p class="code-step">2. 初始化 <code>ans = 0</code>，从左到右遍历下标 <code>i</code></p>
<p class="code-step">3. 取 <code>val = roman[s[i]]</code>；若 <code>i+1 &lt; len(s)</code> 且 <code>val &lt; roman[s[i+1]]</code>，则 <code>ans -= val</code>，否则 <code>ans += val</code></p>
<p class="code-step">4. 遍历结束返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def romanToInt(self, s: str) -> int:
        roman = {"I": 1, "V": 5, "X": 10, "L": 50,
                 "C": 100, "D": 500, "M": 1000}
        ans = 0
        for i in range(len(s)):
            val = roman[s[i]]
            # 当前位比右边小 → 减法形式（如 I 在 V 前）
            if i + 1 < len(s) and val < roman[s[i + 1]]:
                ans -= val
            else:
                ans += val
        return ans""",
        "code_cpp": """class Solution {
public:
    int romanToInt(string s) {
        unordered_map<char, int> roman = {
            {'I', 1}, {'V', 5}, {'X', 10}, {'L', 50},
            {'C', 100}, {'D', 500}, {'M', 1000}
        };
        int ans = 0;
        for (int i = 0; i < (int)s.size(); ++i) {
            int val = roman[s[i]];
            if (i + 1 < (int)s.size() && val < roman[s[i + 1]]) {
                ans -= val;
            } else {
                ans += val;
            }
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 不能对所有字符直接求和，否则 <code>IV</code> 会得到 6 而非 4。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 判断减法时要比较<b>数值</b>而非字符 ASCII（虽然本题数据下碰巧一致，但语义上应查表比较）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 遍历时注意边界：最后一位没有「下一字符」，永远做加法。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：纯加法</div>
    <code>s = "III" → 3</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单位减法</div>
    <code>s = "IV" → 4</code>，<code>s = "IX" → 9</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：复合串</div>
    <code>s = "MCMXCIV" → 1994</code>（同时含 CM、XC、IV 三种减法形式）
</div>""",
    },

    "longest-common-prefix": {
        "type": "字符串模拟",
        "difficulty": "简单",
        "frontend_id": "14",
        "title": "最长公共前缀",
        "time_complexity": "O(S)",
        "space_complexity": "O(1)",
        "description": """<p>编写一个函数来查找字符串数组中的最长公共前缀。</p>
<p>如果不存在公共前缀，返回空字符串 <code>""</code>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：strs = ["flower","flow","flight"]</div>
    <div class="example-output">输出："fl"</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：strs = ["dog","racecar","car"]</div>
    <div class="example-output">输出：""</div>
    <div class="example-explain">输入不存在公共前缀。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>prefix</code></td><td>str</td><td><b>定义</b>：当前已确认、所有已处理字符串共同拥有的前缀<br><b>维护</b>：初始为 <code>strs[0]</code>，每引入一个新串就按需缩短<br><b>更新</b>：若 <code>s</code> 不以 <code>prefix</code> 开头，则 <code>prefix = prefix[:-1]</code> 直到匹配或为空</td></tr>
    <tr><td><code>s</code></td><td>str</td><td><b>定义</b>：当前正在与 <code>prefix</code> 比对的字符串<br><b>维护</b>：按顺序遍历 <code>strs[1:]</code><br><b>更新</b>：每轮取下一个字符串；若 <code>prefix</code> 已空可提前结束</td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>（纵向扫描写法）：当前比对的字符列下标<br><b>维护</b>：从 0 开始，以 <code>strs[0][i]</code> 为基准字符<br><b>更新</b>：所有串在位置 <code>i</code> 字符一致则 <code>i++</code>，否则停止；答案为 <code>strs[0][:i]</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 暴力：枚举所有可能的前缀长度，对每个长度检查是否每个字符串都以该前缀开头——能过，但重复比较很多。</p>
<p class="thinking-step">2. 找重复：公共前缀就是「所有串开头相同的最长一段」，每多一个串，只需看当前候选前缀还能不能匹配。</p>
<p class="thinking-step">3. 横向扫描：用 <code>strs[0]</code> 当初始 <code>prefix</code>，依次与后面每个串比对；不匹配就不断砍掉 <code>prefix</code> 最后一位，直到匹配或变空。</p>
<p class="thinking-step">4. 另一种等价思路是纵向扫描：固定列下标 <code>i</code>，看所有串第 <code>i</code> 个字符是否都与 <code>strs[0][i]</code> 相同，一旦某串更短或字符不同就停。</p>
<p class="thinking-step">5. 还可排序后只比首尾串，或建字典树；本题数据规模下横向/纵向扫描 O(S)（S 为所有字符总数）最直观。</p>""",
        "code_steps": """<p class="code-step">1. 特判空数组；令 <code>prefix = strs[0]</code></p>
<p class="code-step">2. 遍历 <code>strs[1:]</code> 中每个字符串 <code>s</code></p>
<p class="code-step">3. 当 <code>prefix</code> 非空且 <code>s</code> 不以 <code>prefix</code> 开头时，<code>prefix = prefix[:-1]</code></p>
<p class="code-step">4. 若 <code>prefix</code> 已空，提前返回 <code>""</code></p>
<p class="code-step">5. 全部比对完毕，返回 <code>prefix</code></p>""",
        "code_python": """class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        if not strs:
            return ""
        prefix = strs[0]          # 当前公共前缀候选
        for s in strs[1:]:
            # 不匹配就缩短前缀，直到 s 以 prefix 开头或 prefix 为空
            while prefix and not s.startswith(prefix):
                prefix = prefix[:-1]
            if not prefix:
                return ""
        return prefix""",
        "code_cpp": """class Solution {
public:
    string longestCommonPrefix(vector<string>& strs) {
        if (strs.empty()) return "";
        string prefix = strs[0];
        for (int k = 1; k < (int)strs.size(); ++k) {
            const string& s = strs[k];
            while (!prefix.empty() && s.compare(0, prefix.size(), prefix) != 0) {
                prefix.pop_back();
            }
            if (prefix.empty()) return "";
        }
        return prefix;
    }
};
// 时间 O(S)，空间 O(1)（不计输入）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 不能用 <code>min(len(strs))</code> 直接当答案长度——还要保证每个位置字符都相同，不能只比长度。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 纵向扫描时注意某串长度不足时 <code>i</code> 会越界，应先判断 <code>i &lt; len(s)</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空数组要返回 <code>""</code>；单元素数组应返回该元素本身（即整个字符串）。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：有公共前缀</div>
    <code>["flower","flow","flight"] → "fl"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：无公共前缀</div>
    <code>["dog","racecar","car"] → ""</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：单元素 / 空前缀</div>
    <code>["a"] → "a"</code>；<code>["ab","a"] → "a"</code>（较短串决定上限）
</div>""",
    },

    "letter-combinations-of-a-phone-number": {
        "type": "回溯",
        "difficulty": "中等",
        "frontend_id": "17",
        "title": "电话号码的字母组合",
        "time_complexity": "O(4^n · n)",
        "space_complexity": "O(n)（递归栈，不计输出）",
        "description": """<p>给定一个仅包含数字 <code>2-9</code> 的字符串，返回所有它能表示的字母组合。答案可以按 <b>任意顺序</b> 返回。</p>
<p>给出数字到字母的映射如下（与电话按键相同）。注意 1 不对应任何字母。</p>
<ul>
<li><code>2</code> → <code>abc</code></li>
<li><code>3</code> → <code>def</code></li>
<li><code>4</code> → <code>ghi</code></li>
<li><code>5</code> → <code>jkl</code></li>
<li><code>6</code> → <code>mno</code></li>
<li><code>7</code> → <code>pqrs</code></li>
<li><code>8</code> → <code>tuv</code></li>
<li><code>9</code> → <code>wxyz</code></li>
</ul>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：digits = "23"</div>
    <div class="example-output">输出：["ad","ae","af","bd","be","bf","cd","ce","cf"]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：digits = "2"</div>
    <div class="example-output">输出：["a","b","c"]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>path</code></td><td>str / list</td><td><b>定义</b>：当前已选字母拼成的部分组合（前缀）<br><b>维护</b>：每处理一位数字，从映射中选一个字母追加到末尾<br><b>更新</b>：递归前 <code>path += ch</code>；回溯时撤销（<code>pop</code> 或切片还原）</td></tr>
    <tr><td><code>idx</code></td><td>int</td><td><b>定义</b>：当前要处理 <code>digits</code> 中的第几位（下标）<br><b>维护</b>：每选定一个字母并递归返回后，进入下一位<br><b>更新</b>：初始为 0；每轮枚举完当前位所有字母后 <code>idx++</code>（由递归参数传递）</td></tr>
    <tr><td><code>mapping</code></td><td>dict / array</td><td><b>定义</b>：数字键到对应字母串的固定映射表<br><b>维护</b>：程序启动时一次性建好，全程只读<br><b>更新</b>：不更新；用 <code>digits[idx]</code> 查表得到候选字母集合</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;str&gt;</td><td><b>定义</b>：所有长度等于 <code>len(digits)</code> 的合法组合<br><b>维护</b>：当 <code>idx == len(digits)</code> 时，将当前 <code>path</code> 的副本加入<br><b>更新</b>：每到达叶子层追加一次；不在中途追加半成品</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：对每一位数字，枚举它映射里的每个字母，笛卡尔积式地拼出所有串——思路对，但要写出「逐位扩展」的结构。</p>
<p class="thinking-step">2. 重复在哪里？每多处理一位，就是在已有前缀后面接一个新字母；子问题变成「从第 idx 位开始，把剩余位数补全」。</p>
<p class="thinking-step">3. 优化成回溯：固定 <code>path</code> 表示当前前缀，<code>idx</code> 表示处理到第几位；对 <code>digits[idx]</code> 的每个候选字母递归下一层。</p>
<p class="thinking-step">4. 终止条件：<code>idx == len(digits)</code> 时 <code>path</code> 已是完整组合，加入 <code>ans</code>；否则枚举当前位字母，选、递归、撤销。</p>
<p class="thinking-step">5. 特判 <code>digits == ""</code> 应返回空列表；最多 4 位、每位最多 4 个字母，回溯深度 ≤ 4，非常安全。</p>""",
        "code_steps": """<p class="code-step">1. 建立 <code>2-9</code> 到字母串的映射表 <code>mapping</code></p>
<p class="code-step">2. 若 <code>digits</code> 为空，直接返回 <code>[]</code></p>
<p class="code-step">3. 定义 DFS <code>backtrack(idx, path)</code>：若 <code>idx == len(digits)</code>，将 <code>path</code> 加入 <code>ans</code> 并返回</p>
<p class="code-step">4. 取 <code>letters = mapping[digits[idx]]</code>，对每个字母 <code>ch</code>：追加到 <code>path</code>，递归 <code>backtrack(idx+1, path)</code>，再撤销追加</p>
<p class="code-step">5. 从 <code>backtrack(0, "")</code> 启动，返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def letterCombinations(self, digits: str) -> list[str]:
        if not digits:
            return []

        mapping = {
            "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
            "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
        }
        ans: list[str] = []

        def backtrack(idx: int, path: list[str]) -> None:
            if idx == len(digits):
                ans.append("".join(path))
                return
            for ch in mapping[digits[idx]]:
                path.append(ch)
                backtrack(idx + 1, path)
                path.pop()

        backtrack(0, [])
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<string> letterCombinations(string digits) {
        if (digits.empty()) return {};

        static const vector<string> mapping = {
            "", "", "abc", "def", "ghi", "jkl",
            "mno", "pqrs", "tuv", "wxyz"
        };
        vector<string> ans;
        string path;

        function<void(int)> dfs = [&](int idx) {
            if (idx == (int)digits.size()) {
                ans.push_back(path);
                return;
            }
            int d = digits[idx] - '0';
            for (char ch : mapping[d]) {
                path.push_back(ch);
                dfs(idx + 1);
                path.pop_back();
            }
        };

        dfs(0);
        return ans;
    }
};
// 时间 O(4^n · n)，空间 O(n)（递归栈，不计输出）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记空串特判：<code>digits = ""</code> 时必须返回 <code>[]</code>，不能返回 <code>[""]</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 回溯不撤销：选完字母递归后必须 <code>pop</code>，否则 <code>path</code> 会越积越长，污染兄弟分支。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 把数字当数组下标直接用：<code>'2'</code> 的 ASCII 是 50，应使用 <code>digits[idx] - '0'</code> 或映射字典查表。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空输入</div>
    <code>digits = "" → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单个数字</div>
    <code>digits = "2" → ["a","b","c"]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：四位全满（每位 4 字母）</div>
    <code>digits = "79" → 16 种组合（7 有 4 个字母，9 有 4 个字母）</code>
</div>""",
    },

    "4sum": {
        "type": "排序+双指针",
        "difficulty": "中等",
        "frontend_id": "18",
        "title": "四数之和",
        "time_complexity": "O(n³)",
        "space_complexity": "O(1)（不计排序）",
        "description": """<p>给你一个由 <code>n</code> 个整数组成的数组 <code>nums</code>，和一个目标值 <code>target</code>。请你找出并返回满足下述全部条件且<b>不重复</b>的四元组 <code>[nums[a], nums[b], nums[c], nums[d]]</code>（若两个四元组元素一一对应，则认为两个四元组重复）：</p>
<ul>
<li><code>0 &lt;= a, b, c, d &lt; n</code></li>
<li><code>a</code>、<code>b</code>、<code>c</code> 和 <code>d</code> <b>互不相同</b></li>
<li><code>nums[a] + nums[b] + nums[c] + nums[d] == target</code></li>
</ul>
<p>你可以按 <b>任意顺序</b> 返回答案。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,0,-1,0,-2,2], target = 0</div>
    <div class="example-output">输出：[[-2,-1,1,2],[-2,0,0,2],[-1,0,0,1]]</div>
    <div class="example-explain">四元组之和均为 0，且每组四个数下标互不相同；排序去重后得到上述三组不重复答案。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [2,2,2,2], target = 8</div>
    <div class="example-output">输出：[[2,2,2,2]]</div>
    <div class="example-explain">四个 2 恰好凑成 target=8，只输出一组。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：四元组中第一个固定数在排序数组中的下标（最小候选）<br><b>维护</b>：外层枚举，每轮锁定 <code>nums[i]</code> 后在内层继续找 (j,l,r)<br><b>更新</b>：<code>for i in range(n-3)</code>；若 <code>nums[i]==nums[i-1]</code> 则 continue 去重</td></tr>
    <tr><td><code>j</code></td><td>int</td><td><b>定义</b>：四元组中第二个固定数在 <code>i</code> 右侧的下标<br><b>维护</b>：在 <code>(i, n-2]</code> 区间枚举，与 <code>i</code> 一起把问题降为「两数之和 = target-nums[i]-nums[j]」<br><b>更新</b>：<code>for j in range(i+1, n-2)</code>；若 <code>j&gt;i+1</code> 且 <code>nums[j]==nums[j-1]</code> 则 continue 去重</td></tr>
    <tr><td><code>l</code></td><td>int</td><td><b>定义</b>：在 <code>j</code> 右侧区间内指向较小候选值的左指针<br><b>维护</b>：当前四数和偏小则右移，命中后跳过重复值<br><b>更新</b>：初始 <code>l=j+1</code>；<code>s&lt;target</code> 时 <code>l++</code>；命中后 while 跳过相同 <code>nums[l]</code></td></tr>
    <tr><td><code>r</code></td><td>int</td><td><b>定义</b>：在 <code>j</code> 右侧区间内指向较大候选值的右指针<br><b>维护</b>：当前四数和偏大则左移，命中后跳过重复值<br><b>更新</b>：初始 <code>r=n-1</code>；<code>s&gt;target</code> 时 <code>r--</code>；命中后 while 跳过相同 <code>nums[r]</code></td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&gt;</td><td><b>定义</b>：所有不重复的四元组答案<br><b>维护</b>：每当 <code>nums[i]+nums[j]+nums[l]+nums[r]==target</code> 时追加一组<br><b>更新</b>：命中后 <code>l、r</code> 同时内缩并各自跳过重复，避免死循环与重复答案</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先写暴力：四重循环枚举 (i,j,l,r)，判断四数之和是否等于 target——O(n⁴)，还要额外去重，肯定超时。</p>
<p class="thinking-step">2. 重复在哪里？固定前两个数 <code>nums[i]</code>、<code>nums[j]</code> 后，问题变成「在剩余数组里找两数，使四数之和等于 target」，即两数之和 = <code>target - nums[i] - nums[j]</code>。</p>
<p class="thinking-step">3. 这和 #15 三数之和一脉相承：排序后，两数之和可用双指针——和小了 <code>l++</code>，和大了 <code>r--</code>，O(n)。</p>
<p class="thinking-step">4. 整体结构：排序 → 外层固定 <code>i</code> → 中层固定 <code>j</code> → 内层双指针找 complement，复杂度 O(n³)。</p>
<p class="thinking-step">5. 去重关键：排序后 <code>i、j、l、r</code> 四个位置都要跳过与前一个相同的值；另外 C++ 里求和要用 <code>long long</code> 防溢出。</p>""",
        "code_steps": """<p class="code-step">1. 对 <code>nums</code> 升序排序；若 <code>n&lt;4</code> 直接返回空列表</p>
<p class="code-step">2. 外层 <code>for i in range(n-3)</code>，若 <code>nums[i]==nums[i-1]</code> 则跳过（i 去重）</p>
<p class="code-step">3. 中层 <code>for j in range(i+1, n-2)</code>，若 <code>nums[j]==nums[j-1]</code> 且 <code>j&gt;i+1</code> 则跳过（j 去重）</p>
<p class="code-step">4. 设 <code>l=j+1, r=n-1</code>，当 <code>l&lt;r</code> 时计算 <code>s=nums[i]+nums[j]+nums[l]+nums[r]</code></p>
<p class="code-step">5. <code>s&lt;target</code> 则 <code>l++</code>；<code>s&gt;target</code> 则 <code>r--</code>；<code>s==target</code> 则记录答案，l、r 内缩并各自跳过重复</p>
<p class="code-step">6. 返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def fourSum(self, nums: list[int], target: int) -> list[list[int]]:
        nums.sort()
        n = len(nums)
        ans = []

        for i in range(n - 3):
            # 固定第一个数，跳过重复
            if i > 0 and nums[i] == nums[i - 1]:
                continue

            for j in range(i + 1, n - 2):
                # 固定第二个数，跳过重复
                if j > i + 1 and nums[j] == nums[j - 1]:
                    continue

                l, r = j + 1, n - 1
                while l < r:
                    s = nums[i] + nums[j] + nums[l] + nums[r]
                    if s < target:
                        l += 1
                    elif s > target:
                        r -= 1
                    else:
                        ans.append([nums[i], nums[j], nums[l], nums[r]])
                        l += 1
                        r -= 1
                        while l < r and nums[l] == nums[l - 1]:
                            l += 1
                        while l < r and nums[r] == nums[r + 1]:
                            r -= 1

        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<int>> fourSum(vector<int>& nums, int target) {
        sort(nums.begin(), nums.end());
        int n = nums.size();
        vector<vector<int>> ans;
        long long t = target;

        for (int i = 0; i < n - 3; i++) {
            // 固定第一个数，跳过重复
            if (i > 0 && nums[i] == nums[i - 1]) continue;

            for (int j = i + 1; j < n - 2; j++) {
                // 固定第二个数，跳过重复
                if (j > i + 1 && nums[j] == nums[j - 1]) continue;

                int l = j + 1, r = n - 1;
                while (l < r) {
                    long long s = (long long)nums[i] + nums[j] + nums[l] + nums[r];
                    if (s < t) l++;
                    else if (s > t) r--;
                    else {
                        ans.push_back({nums[i], nums[j], nums[l], nums[r]});
                        l++; r--;
                        while (l < r && nums[l] == nums[l - 1]) l++;
                        while (l < r && nums[r] == nums[r + 1]) r--;
                    }
                }
            }
        }
        return ans;
    }
};
// 时间 O(n³)，空间 O(1)（不计排序）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 只做 i 去重、忘记 j 去重：第二个固定数相同会产出重复四元组，<code>j</code> 处也要 <code>continue</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> C++ 用 <code>int</code> 直接相加：四个数各可达 10⁹，和会溢出，求和应转 <code>long long</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 命中后忘记移动 <code>l、r</code>：找到一组答案后必须双指针内缩并跳过重复，否则会死循环或重复收集。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：元素不足四个</div>
    <code>nums = [1,2], target = 3 → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：四个相同数恰好命中</div>
    <code>nums = [2,2,2,2], target = 8 → [[2,2,2,2]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：大量重复值</div>
    <code>nums = [1,0,-1,0,-2,2], target = 0 → 三组不重复四元组（见示例 1）</code>
</div>""",
    },

    "remove-nth-node-from-end-of-list": {
        "type": "链表指针",
        "difficulty": "中等",
        "frontend_id": "19",
        "title": "删除链表的倒数第 N 个结点",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个链表，删除链表的倒数第 <code>n</code> 个结点，并且返回链表的头结点。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：head = [1,2,3,4,5], n = 2</div>
    <div class="example-output">输出：[1,2,3,5]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：head = [1], n = 1</div>
    <div class="example-output">输出：[]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：head = [1,2], n = 1</div>
    <div class="example-output">输出：[1]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dummy</code></td><td>ListNode*</td><td><b>定义</b>：哨兵头节点，<code>dummy.next = head</code><br><b>维护</b>：始终位于真实头节点之前，统一处理「删掉头节点」的边界<br><b>更新</b>：创建后不再移动，最终返回 <code>dummy.next</code></td></tr>
    <tr><td><code>fast</code></td><td>ListNode*</td><td><b>定义</b>：快指针，先向前走 <code>n</code> 步<br><b>维护</b>：与 <code>slow</code> 保持「快指针比慢指针超前 n 个节点」的间距<br><b>更新</b>：先单独走 n 步，再与 slow 同步每次 <code>fast = fast.next</code></td></tr>
    <tr><td><code>slow</code></td><td>ListNode*</td><td><b>定义</b>：慢指针，从 dummy 出发<br><b>维护</b>：当 fast 到达链表末尾时，slow 恰好停在「待删节点的前驱」<br><b>更新</b>：与 fast 同步每次 <code>slow = slow.next</code>，最后执行 <code>slow.next = slow.next.next</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先写暴力：第一遍遍历数出链表长度 <code>L</code>，第二遍找到正数第 <code>L - n</code> 个节点的前驱并删除——能过，但要扫两遍。</p>
<p class="thinking-step">2. 重复在哪里？两遍扫描本质都是在「定位待删节点的前驱」；如果能让两个指针保持固定间距 n，一遍就能同时完成定位。</p>
<p class="thinking-step">3. 快指针先走 n 步，再和慢指针同步前进：当 fast 走到最后一个节点时，slow 正好在倒数第 n+1 个节点（即待删节点的前驱）。</p>
<p class="thinking-step">4. 边界：若 n 等于链表长度，删的是头节点——没有前驱可改。加 <code>dummy</code> 哨兵后，slow 会停在 dummy，统一用 <code>slow.next = slow.next.next</code> 删除。</p>
<p class="thinking-step">5. 循环条件是 <code>while fast.next</code> 而非 <code>while fast</code>：保证 fast 停在最后一个节点，slow 才恰好落在前驱位置。</p>""",
        "code_steps": """<p class="code-step">1. 创建哨兵 <code>dummy = ListNode(0, head)</code>，<code>fast = slow = dummy</code></p>
<p class="code-step">2. 快指针先走 n 步：<code>for _ in range(n): fast = fast.next</code></p>
<p class="code-step">3. 双指针同步前进：<code>while fast.next: fast = fast.next; slow = slow.next</code></p>
<p class="code-step">4. 删除节点：<code>slow.next = slow.next.next</code></p>
<p class="code-step">5. 返回 <code>dummy.next</code>（新头节点）</p>""",
        "code_python": """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)  # 哨兵，统一处理删头节点
        fast = slow = dummy

        for _ in range(n):           # 快指针先走 n 步
            fast = fast.next

        while fast.next:            # 同步前进，fast 到末尾时 slow 在前驱
            fast = fast.next
            slow = slow.next

        slow.next = slow.next.next  # 跳过待删节点
        return dummy.next""",
        "code_cpp": """class Solution {
public:
    ListNode* removeNthFromEnd(ListNode* head, int n) {
        ListNode dummy(0, head);  // 哨兵，统一处理删头节点
        ListNode* fast = &dummy;
        ListNode* slow = &dummy;

        for (int i = 0; i < n; i++)  // 快指针先走 n 步
            fast = fast->next;

        while (fast->next) {         // 同步前进，fast 到末尾时 slow 在前驱
            fast = fast->next;
            slow = slow->next;
        }

        slow->next = slow->next->next;  // 跳过待删节点
        return dummy.next;
    }
};
// 时间 O(n)，空间 O(1)
// 两遍法：先数长度 L，再走到第 L-n 个节点的前驱删除""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记 <code>dummy</code> 哨兵：当 <code>n == 链表长度</code> 时要删头节点，没有前驱可改 <code>next</code>，必须用哨兵统一处理。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 循环条件写成 <code>while fast</code>：fast 会走出链表，slow 停在错误位置；应是 <code>while fast.next</code>，让 fast 停在最后一个节点。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 快指针少走或多走一步：先走恰好 n 步（不是 n-1 也不是 n+1），间距错了 slow 就对不准前驱。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：删除头节点（n 等于链表长度）</div>
    <code>head = [1], n = 1 → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：删除尾节点</div>
    <code>head = [1,2], n = 1 → [1]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：单节点中间删除</div>
    <code>head = [1,2,3,4,5], n = 2 → [1,2,3,5]（删倒数第 2 个即 4）</code>
</div>""",
    },
    "valid-parentheses": {
        "type": "栈",
        "difficulty": "简单",
        "frontend_id": "20",
        "title": "有效的括号",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "description": """<p>给定一个只包括 <code>'('</code>、<code>')'</code>、<code>'{'</code>、<code>'}'</code>、<code>'['</code>、<code>']'</code> 的字符串 <code>s</code>，判断字符串是否有效。</p>
<p>有效字符串需满足：</p>
<ol>
<li>左括号必须用相同类型的右括号闭合。</li>
<li>左括号必须以正确的顺序闭合。</li>
<li>每个右括号都有一个对应的相同类型的左括号。</li>
</ol>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "()"</div>
    <div class="example-output">输出：true</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "()[]{}"</div>
    <div class="example-output">输出：true</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：s = "(]"</div>
    <div class="example-output">输出：false</div>
</div>
<div class="example-block">
    <h4>示例 4</h4>
    <div class="example-input">输入：s = "([])"</div>
    <div class="example-output">输出：true</div>
</div>
<div class="example-block">
    <h4>示例 5</h4>
    <div class="example-input">输入：s = "([)]"</div>
    <div class="example-output">输出：false</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>stk</code></td><td>list / stack</td><td><b>定义</b>：存放尚未被匹配的左括号<br><b>维护</b>：栈底到栈顶对应「从外到内、尚未闭合」的左括号序列<br><b>更新</b>：遇左括号 <code>push</code>；遇右括号且匹配成功则 <code>pop</code>，否则直接判无效</td></tr>
    <tr><td><code>pairs</code></td><td>dict</td><td><b>定义</b>：右括号到左括号的映射（<code>')'→'('</code> 等）<br><b>维护</b>：固定不变，覆盖三种括号对<br><b>更新</b>：无需更新，用 <code>pairs[c]</code> 查期望的栈顶左括号</td></tr>
    <tr><td><code>c</code></td><td>char</td><td><b>定义</b>：当前扫描到的字符<br><b>维护</b>：从左到右依次处理每个括号<br><b>更新</b>：每轮循环取下一个字符，按左/右分支更新栈或提前返回 <code>False</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先写暴力：对每个右括号，向前找最近一个未匹配的左括号，看类型是否一致——能判断，但要反复扫描、标记已用字符，实现又慢又乱。</p>
<p class="thinking-step">2. 重复在哪里？每次匹配的都是「离当前右括号最近、且尚未闭合」的左括号——这正是后进先出（LIFO）的结构。</p>
<p class="thinking-step">3. 用栈：遇左括号压栈；遇右括号看栈顶是否是与之配对的左括号，是则弹出，否则无效。扫完后栈空才有效。</p>
<p class="thinking-step">4. 细节：右括号来时栈不能为空；类型必须严格匹配，<code>(]</code>、<code>([)]</code> 都会在匹配阶段失败。</p>
<p class="thinking-step">5. 复杂度：每个字符最多入栈出栈各一次，时间 O(n)；最坏全是左括号时栈长 O(n)。</p>""",
        "code_steps": """<p class="code-step">1. 建立右→左括号映射 <code>pairs = {')':'(', ']':'[', '}':'{'}</code></p>
<p class="code-step">2. 初始化空栈 <code>stk = []</code>，从左到右遍历每个字符 <code>c</code></p>
<p class="code-step">3. 若 <code>c</code> 是左括号（不在 pairs 的 key 中），<code>stk.append(c)</code></p>
<p class="code-step">4. 若 <code>c</code> 是右括号：栈空或 <code>stk[-1] != pairs[c]</code> 则返回 <code>False</code>，否则 <code>stk.pop()</code></p>
<p class="code-step">5. 遍历结束，返回 <code>len(stk) == 0</code></p>""",
        "code_python": """class Solution:
    def isValid(self, s: str) -> bool:
        pairs = {')': '(', ']': '[', '}': '{'}
        stk = []
        for c in s:
            if c not in pairs:          # 左括号，等待匹配
                stk.append(c)
            elif not stk or stk[-1] != pairs[c]:  # 右括号无法配对
                return False
            else:
                stk.pop()
        return not stk""",
        "code_cpp": """class Solution {
public:
    bool isValid(string s) {
        unordered_map<char, char> pairs = {
            {')', '('}, {']', '['}, {'}', '{'}
        };
        vector<char> stk;
        for (char c : s) {
            if (!pairs.count(c)) {       // 左括号，等待匹配
                stk.push_back(c);
            } else if (stk.empty() || stk.back() != pairs[c]) {
                return false;            // 右括号无法配对
            } else {
                stk.pop_back();
            }
        }
        return stk.empty();
    }
};
// 时间 O(n)，空间 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 右括号来时忘记检查栈空：如 <code>")"</code>、<code>"]"</code> 会直接访问空栈顶导致错误。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 只判断「栈非空」不判断类型：<code>(]</code> 栈顶是 <code>(</code> 却遇到 <code>]</code>，必须返回 <code>False</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 遍历结束后忘记检查栈是否为空：<code>"("</code>、<code>"([("</code> 等左括号未闭合应判无效。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单个左括号未闭合</div>
    <code>s = "(" → false</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单个右括号无匹配</div>
    <code>s = ")" → false</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：嵌套与交叉</div>
    <code>s = "([])" → true；s = "([)]" → false</code>
</div>""",
    },
    "merge-two-sorted-lists": {
        "type": "链表指针",
        "difficulty": "简单",
        "frontend_id": "21",
        "title": "合并两个有序链表",
        "time_complexity": "O(m + n)",
        "space_complexity": "O(1)",
        "description": """<p>将两个升序链表合并为一个新的 <strong>升序</strong> 链表并返回。新链表是通过拼接给定的两个链表的所有节点组成的。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：l1 = [1,2,4], l2 = [1,3,4]</div>
    <div class="example-output">输出：[1,1,2,3,4,4]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：l1 = [], l2 = []</div>
    <div class="example-output">输出：[]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：l1 = [], l2 = [0]</div>
    <div class="example-output">输出：[0]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dummy</code></td><td>ListNode*</td><td><b>定义</b>：哨兵头节点，不存放有效值<br><b>维护</b>：始终位于合并结果链表的最前端，统一处理「结果为空」等边界<br><b>更新</b>：创建后不再移动，最终返回 <code>dummy.next</code></td></tr>
    <tr><td><code>curr</code></td><td>ListNode*</td><td><b>定义</b>：合并结果链表的尾指针<br><b>维护</b>：指向已拼接部分的最后一个节点，新节点总是接在 <code>curr.next</code><br><b>更新</b>：每选中一个较小节点后 <code>curr = curr.next</code>，尾指针前移</td></tr>
    <tr><td><code>l1 / l2</code></td><td>ListNode*</td><td><b>定义</b>：两条输入链表当前待比较的节点<br><b>维护</b>：各自沿 next 前进，始终指向「尚未接入结果」的最小候选<br><b>更新</b>：谁被接入结果谁就 <code>l1 = l1.next</code> 或 <code>l2 = l2.next</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先写暴力：把两条链表所有节点值收集到数组，排序后再逐个新建节点串起来——能过，但白白丢弃了「已有序」这一条件，还多用了 O(m+n) 额外空间。</p>
<p class="thinking-step">2. 重复在哪里？每次只需要在两条链表的「当前头节点」里取较小者接到结果尾部，然后该链表的指针前移——这和合并两个有序数组的双指针一模一样，只是用指针代替下标。</p>
<p class="thinking-step">3. 用哨兵 <code>dummy</code> + 尾指针 <code>curr</code>：比较 <code>l1.val</code> 与 <code>l2.val</code>，较小者挂到 <code>curr.next</code>，对应指针后移，<code>curr</code> 跟进。</p>
<p class="thinking-step">4. 当其中一条链表耗尽，另一条剩余部分已经有序，直接 <code>curr.next = l1 or l2</code> 一次性接上，无需再逐个比较。</p>
<p class="thinking-step">5. 复杂度：每个节点恰好被访问一次，时间 O(m+n)；只用到常数个指针，空间 O(1)（不计返回链表本身）。</p>""",
        "code_steps": """<p class="code-step">1. 创建哨兵 <code>dummy = ListNode(0)</code>，<code>curr = dummy</code></p>
<p class="code-step">2. 当 <code>l1</code> 和 <code>l2</code> 均非空：比较值，较小者挂到 <code>curr.next</code>，对应指针后移，<code>curr = curr.next</code></p>
<p class="code-step">3. 一条链表耗尽后，将另一条剩余部分直接接到 <code>curr.next</code></p>
<p class="code-step">4. 返回 <code>dummy.next</code>（合并后的真实头节点）</p>""",
        "code_python": """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode(0)   # 哨兵，简化头节点处理
        curr = dummy          # 结果链表的尾指针
        l1, l2 = list1, list2

        while l1 and l2:
            if l1.val <= l2.val:
                curr.next = l1
                l1 = l1.next
            else:
                curr.next = l2
                l2 = l2.next
            curr = curr.next

        curr.next = l1 or l2    # 接上剩余有序段
        return dummy.next""",
        "code_cpp": """class Solution {
public:
    ListNode* mergeTwoLists(ListNode* list1, ListNode* list2) {
        ListNode dummy(0);        // 哨兵，简化头节点处理
        ListNode* curr = &dummy;  // 结果链表的尾指针

        while (list1 && list2) {
            if (list1->val <= list2->val) {
                curr->next = list1;
                list1 = list1->next;
            } else {
                curr->next = list2;
                list2 = list2->next;
            }
            curr = curr->next;
        }
        curr->next = list1 ? list1 : list2;  // 接上剩余有序段
        return dummy.next;
    }
};
// 时间 O(m+n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记移动 <code>curr</code>：只改了 <code>curr.next</code> 却不 <code>curr = curr.next</code>，会导致所有节点叠在同一位置、链表成环或断裂。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 一条链表耗尽后仍继续 while 比较：剩余段已经有序，应直接 <code>curr.next = l1 ? l1 : l2</code>，否则多余循环且可能访问空指针。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回 <code>dummy</code> 而非 <code>dummy.next</code>：哨兵节点不应出现在最终结果中。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：两条链表均为空</div>
    <code>l1 = [], l2 = [] → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：其中一条为空</div>
    <code>l1 = [], l2 = [0] → [0]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：等值节点交叉出现</div>
    <code>l1 = [1,2,4], l2 = [1,3,4] → [1,1,2,3,4,4]（相等时取 l1 即可）</code>
</div>""",
    },

    "generate-parentheses": {
        "type": "回溯",
        "difficulty": "中等",
        "frontend_id": "22",
        "title": "括号生成",
        "time_complexity": "O(4^n / √n)",
        "space_complexity": "O(n)（递归栈，不计输出）",
        "description": """<p>数字 <code>n</code> 代表生成括号的对数，请你设计一个函数，用于能够生成所有可能的并且 <strong>有效的</strong> 括号组合。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：n = 3</div>
    <div class="example-output">输出：["((()))","(()())","(())()","()(())","()()()"]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：n = 1</div>
    <div class="example-output">输出：["()"]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>path</code></td><td>str / list</td><td><b>定义</b>：当前已拼接的括号前缀<br><b>维护</b>：每次递归尝试在末尾追加 <code>'('</code> 或 <code>')'</code><br><b>更新</b>：选左括号时追加并递归；回溯时撤销（<code>pop</code> 或切片还原）</td></tr>
    <tr><td><code>open</code></td><td>int</td><td><b>定义</b>：<code>path</code> 中已使用的左括号 <code>'('</code> 个数<br><b>维护</b>：只有 <code>open &lt; n</code> 时才允许再追加左括号<br><b>更新</b>：追加 <code>'('</code> 时 <code>open++</code>；回溯返回后恢复</td></tr>
    <tr><td><code>close</code></td><td>int</td><td><b>定义</b>：<code>path</code> 中已使用的右括号 <code>')'</code> 个数<br><b>维护</b>：只有 <code>close &lt; open</code> 时才允许追加右括号（保证任意前缀合法）<br><b>更新</b>：追加 <code>')'</code> 时 <code>close++</code>；回溯返回后恢复</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;str&gt;</td><td><b>定义</b>：所有长度为 <code>2n</code> 的合法括号串<br><b>维护</b>：当 <code>len(path) == 2n</code> 时，将当前 <code>path</code> 的副本加入<br><b>更新</b>：每到达叶子层追加一次；中途不收集半成品</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：枚举所有长度为 <code>2n</code> 的 <code>'('</code>/<code>')'</code> 组合，再逐个用栈判断是否合法——思路对，但组合数高达 <code>2^{2n}</code>，大量无效串被白白生成。</p>
<p class="thinking-step">2. 重复在哪里？每多放一个括号，子问题变成「在已有前缀上继续补全剩余括号」；无效分支的共同特征是：某一时刻右括号比左括号多，或左括号已经用完却还在放左括号。</p>
<p class="thinking-step">3. 优化成回溯剪枝：用 <code>open</code>、<code>close</code> 记录已用括号数；能放 <code>'('</code> 当且仅当 <code>open &lt; n</code>，能放 <code>')'</code> 当且仅当 <code>close &lt; open</code>。</p>
<p class="thinking-step">4. 终止条件：<code>len(path) == 2n</code> 时得到一棵完整合法串，加入 <code>ans</code>；否则按「先尝试左、再尝试右」递归，每次选择后撤销。</p>
<p class="thinking-step">5. <code>n = 1</code> 只有 <code>"()"</code>；<code>n</code> 最大为 8，回溯深度 ≤ 16，剪枝后实际访问节点远少于全枚举。</p>""",
        "code_steps": """<p class="code-step">1. 初始化结果列表 <code>ans</code>，定义 DFS <code>backtrack(path, open, close)</code></p>
<p class="code-step">2. 若 <code>len(path) == 2 * n</code>，将 <code>path</code> 加入 <code>ans</code> 并返回</p>
<p class="code-step">3. 若 <code>open &lt; n</code>：追加 <code>'('</code>，递归 <code>backtrack(..., open+1, close)</code>，再撤销</p>
<p class="code-step">4. 若 <code>close &lt; open</code>：追加 <code>')'</code>，递归 <code>backtrack(..., open, close+1)</code>，再撤销</p>
<p class="code-step">5. 从 <code>backtrack([], 0, 0)</code> 启动，返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def generateParenthesis(self, n: int) -> list[str]:
        ans: list[str] = []

        def backtrack(path: list[str], open_cnt: int, close_cnt: int) -> None:
            if len(path) == 2 * n:
                ans.append("".join(path))
                return
            if open_cnt < n:
                path.append("(")
                backtrack(path, open_cnt + 1, close_cnt)
                path.pop()
            if close_cnt < open_cnt:
                path.append(")")
                backtrack(path, open_cnt, close_cnt + 1)
                path.pop()

        backtrack([], 0, 0)
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<string> generateParenthesis(int n) {
        vector<string> ans;
        string path;

        function<void(int, int)> dfs = [&](int open, int close) {
            if ((int)path.size() == 2 * n) {
                ans.push_back(path);
                return;
            }
            if (open < n) {
                path.push_back('(');
                dfs(open + 1, close);
                path.pop_back();
            }
            if (close < open) {
                path.push_back(')');
                dfs(open, close + 1);
                path.pop_back();
            }
        };

        dfs(0, 0);
        return ans;
    }
};
// 时间 O(4^n / √n)，空间 O(n)（递归栈，不计输出）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 右括号放太早：必须满足 <code>close &lt; open</code> 才能追加 <code>')'</code>，否则会出现 <code>")("</code> 这类非法前缀。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 回溯不撤销：追加括号后递归返回，必须 <code>pop</code>，否则 <code>path</code> 会污染兄弟分支。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 终止条件写错：应判断 <code>len(path) == 2*n</code>（或 <code>open == close == n</code>），不能只判断 <code>open == n</code> 就收集——那时右括号还没补全。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：n = 1</div>
    <code>n = 1 → ["()"]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：n = 2</div>
    <code>n = 2 → ["(())","()()"]</code>（共 2 种）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：n = 3</div>
    <code>n = 3 → 5 种合法串</code>（卡特兰数 C₃ = 5）
</div>""",
    },

    "merge-k-sorted-lists": {
        "type": "堆（优先队列）",
        "difficulty": "困难",
        "frontend_id": "23",
        "title": "合并 K 个升序链表",
        "time_complexity": "O(N log k)",
        "space_complexity": "O(k)（堆大小）",
        "description": """<p>给你一个链表数组，每个链表都已经按升序排列。</p>
<p>请你将所有链表合并到一个升序链表中，返回合并后的链表。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：lists = [[1,4,5],[1,3,4],[2,6]]</div>
    <div class="example-output">输出：[1,1,2,3,4,4,5,6]</div>
    <div class="example-explain">链表数组如下：
[
  1-&gt;4-&gt;5,
  1-&gt;3-&gt;4,
  2-&gt;6
]
将它们合并到一个有序链表中得到 1-&gt;1-&gt;2-&gt;3-&gt;4-&gt;4-&gt;5-&gt;6。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：lists = []</div>
    <div class="example-output">输出：[]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：lists = [[]]</div>
    <div class="example-output">输出：[]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dummy</code></td><td>ListNode*</td><td><b>定义</b>：哨兵头节点，不存放有效值<br><b>维护</b>：始终位于合并结果链表的最前端，统一处理「结果为空」等边界<br><b>更新</b>：创建后不再移动，最终返回 <code>dummy.next</code></td></tr>
    <tr><td><code>curr</code></td><td>ListNode*</td><td><b>定义</b>：合并结果链表的尾指针<br><b>维护</b>：指向已拼接部分的最后一个节点，新节点总是接在 <code>curr.next</code><br><b>更新</b>：每从堆中取出节点并接入后 <code>curr = curr.next</code></td></tr>
    <tr><td><code>heap</code></td><td>min-heap</td><td><b>定义</b>：存放各链表当前头节点的最小堆，堆顶始终是全局最小值<br><b>维护</b>：初始化时把每条非空链表的头节点入堆；每弹出一个节点后，若该节点还有后继则把后继入堆<br><b>更新</b>：<code>heappop</code> 取出最小节点；<code>heappush(node.next)</code> 补充下一位候选</td></tr>
    <tr><td><code>(val, i, node)</code></td><td>tuple</td><td><b>定义</b>：堆元素的排序键——节点值、链表编号、节点指针<br><b>维护</b>：值相等时用编号 <code>i</code> 打破平局，避免 Python 比较两个 <code>ListNode</code> 对象<br><b>更新</b>：每次入堆时按当前头节点的三元组构造</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：把所有节点值收集到数组里排序，再逐个新建节点串起来——能过，但完全没用「每条链表已有序」这一条件，时间 O(N log N)、额外空间 O(N)。</p>
<p class="thinking-step">2. 重复在哪里？每次只需要在 k 条链表的「当前头节点」里找全局最小者接到结果尾部，然后该链表指针前移——这和合并两个有序链表一样，只是候选从 2 个变成 k 个。</p>
<p class="thinking-step">3. 朴素做法：依次把 lists[0] 与 lists[1] 合并、再与 lists[2] 合并……复用 #21 的双指针合并，最坏时间 O(kN)（N 为总节点数），k 很大时偏慢。</p>
<p class="thinking-step">4. 优化成最小堆：把 k 个头节点放入堆，每次弹出堆顶（全局最小）接到 <code>curr.next</code>，若该节点有后继则把后继入堆——每个节点恰好入堆、出堆一次，时间 O(N log k)。</p>
<p class="thinking-step">5. 另一种 O(N log k) 是分治：两两归并像归并排序，但堆解法更直观，且 k 条链表头随时变化时堆天然适配。</p>""",
        "code_steps": """<p class="code-step">1. 创建哨兵 <code>dummy</code>，<code>curr = dummy</code>；初始化空堆 <code>heap</code></p>
<p class="code-step">2. 遍历 <code>lists</code>：对每条非空链表，将 <code>(node.val, i, node)</code> 入堆</p>
<p class="code-step">3. 当堆非空：弹出最小元 <code>(val, i, node)</code>，挂到 <code>curr.next</code>，<code>curr = curr.next</code></p>
<p class="code-step">4. 若 <code>node.next</code> 非空，将 <code>(node.next.val, i, node.next)</code> 入堆</p>
<p class="code-step">5. 返回 <code>dummy.next</code></p>""",
        "code_python": """import heapq
from typing import List, Optional

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        dummy = ListNode(0)   # 哨兵，简化头节点处理
        curr = dummy          # 结果链表的尾指针
        heap: list[tuple[int, int, ListNode]] = []

        for i, node in enumerate(lists):
            if node:
                heapq.heappush(heap, (node.val, i, node))

        while heap:
            _, i, node = heapq.heappop(heap)
            curr.next = node
            curr = curr.next
            nxt = node.next
            if nxt:
                heapq.heappush(heap, (nxt.val, i, nxt))

        return dummy.next""",
        "code_cpp": """class Solution {
public:
    ListNode* mergeKLists(vector<ListNode*>& lists) {
        auto cmp = [](ListNode* a, ListNode* b) { return a->val > b->val; };
        priority_queue<ListNode*, vector<ListNode*>, decltype(cmp)> pq(cmp);

        for (ListNode* head : lists) {
            if (head) pq.push(head);
        }

        ListNode dummy(0);
        ListNode* curr = &dummy;

        while (!pq.empty()) {
            ListNode* node = pq.top();
            pq.pop();
            curr->next = node;
            curr = curr->next;
            if (node->next) pq.push(node->next);
        }
        return dummy.next;
    }
};
// 时间 O(N log k)，空间 O(k)（堆大小）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> Python 堆直接存 <code>ListNode</code>：值相等时会比较两个节点对象并报错——必须用 <code>(val, i, node)</code> 元组，用编号 <code>i</code> 打破平局。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记移动 <code>curr</code>：只设置 <code>curr.next</code> 却不 <code>curr = curr.next</code>，会导致节点叠在同一位置或成环。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空链表未过滤：初始化时须跳过 <code>null</code> 头节点，否则堆中混入空指针；<code>lists = []</code> 或 <code>[[]]</code> 应直接返回空链表。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：lists 为空数组</div>
    <code>lists = [] → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：仅含空链表</div>
    <code>lists = [[]] → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：多条链表等值头节点</div>
    <code>lists = [[1,4,5],[1,3,4],[2,6]] → [1,1,2,3,4,4,5,6]</code>（堆须正确处理值相等）
</div>""",
    },

    "swap-nodes-in-pairs": {
        "type": "链表指针",
        "difficulty": "中等",
        "frontend_id": "24",
        "title": "两两交换链表中的节点",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个链表，两两交换其中相邻的节点，并返回交换后链表的头节点。你必须在不修改节点内部的值的情况下完成本题（即，只能进行节点交换）。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：head = [1,2,3,4]</div>
    <div class="example-output">输出：[2,1,4,3]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：head = []</div>
    <div class="example-output">输出：[]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：head = [1]</div>
    <div class="example-output">输出：[1]</div>
</div>
<div class="example-block">
    <h4>示例 4</h4>
    <div class="example-input">输入：head = [1,2,3]</div>
    <div class="example-output">输出：[2,1,3]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dummy</code></td><td>ListNode*</td><td><b>定义</b>：哨兵头节点，<code>dummy.next = head</code><br><b>维护</b>：始终位于真实头节点之前，统一处理「第一对交换后新头节点」的边界<br><b>更新</b>：创建后不再移动，最终返回 <code>dummy.next</code></td></tr>
    <tr><td><code>prev</code></td><td>ListNode*</td><td><b>定义</b>：待交换相邻两节点的前驱指针<br><b>维护</b>：每轮交换完成后，<code>prev</code> 应停在「刚交换完的那一对」的第二个节点（即原 first）<br><b>更新</b>：交换一对后 <code>prev = first</code>，下一轮从 <code>prev.next</code> 继续</td></tr>
    <tr><td><code>first</code></td><td>ListNode*</td><td><b>定义</b>：当前待交换对中的第一个节点（<code>prev.next</code>）<br><b>维护</b>：与 <code>second</code> 构成相邻一对；交换后 <code>first</code> 成为该对的尾节点<br><b>更新</b>：每轮从 <code>prev.next</code> 读取；交换后通过 <code>prev = first</code> 进入下一对</td></tr>
    <tr><td><code>second</code></td><td>ListNode*</td><td><b>定义</b>：当前待交换对中的第二个节点（<code>first.next</code>）<br><b>维护</b>：交换后 <code>second</code> 成为该对的新头，并接到 <code>prev.next</code><br><b>更新</b>：每轮从 <code>first.next</code> 读取；若不存在则不足一对，循环结束</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：把节点值复制到数组，两两交换数组元素再重建链表——能过，但题目要求「只能进行节点交换」，且多用了 O(n) 额外空间。</p>
<p class="thinking-step">2. 重复在哪里？每次操作都是「把相邻两个节点的指针关系翻转」；下一对的前驱，恰好是「上一对交换后的尾节点」。</p>
<p class="thinking-step">3. 设前驱 <code>prev</code>、待换对 <code>first</code>、<code>second</code>：三步翻转——<code>prev.next = second</code>，<code>first.next = second.next</code>，<code>second.next = first</code>；然后 <code>prev = first</code> 处理下一对。</p>
<p class="thinking-step">4. 边界：链表为空或只有一个节点时无需交换；奇数个节点时最后一对只有 <code>first</code>，当 <code>first.next</code> 为空应直接退出。</p>
<p class="thinking-step">5. 第一对交换会改变头节点——加 <code>dummy</code> 哨兵后，<code>prev</code> 从 <code>dummy</code> 出发，与删头节点、合并链表等题同一套路。</p>""",
        "code_steps": """<p class="code-step">1. 创建哨兵 <code>dummy = ListNode(0, head)</code>，<code>prev = dummy</code></p>
<p class="code-step">2. 当 <code>prev.next</code> 与 <code>prev.next.next</code> 均非空时进入循环（保证有一对可换）</p>
<p class="code-step">3. 令 <code>first = prev.next</code>，<code>second = first.next</code></p>
<p class="code-step">4. 翻转这一对：<code>prev.next = second</code>；<code>first.next = second.next</code>；<code>second.next = first</code></p>
<p class="code-step">5. 更新 <code>prev = first</code>，继续下一对；返回 <code>dummy.next</code></p>""",
        "code_python": """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:
        dummy = ListNode(0, head)   # 哨兵，统一处理头节点交换
        prev = dummy

        while prev.next and prev.next.next:
            first = prev.next
            second = first.next

            prev.next = second          # 前驱接到新头 second
            first.next = second.next    # first 接到后续链表
            second.next = first         # second 指向 first，完成翻转

            prev = first                # prev 移到本对尾节点，准备下一对

        return dummy.next""",
        "code_cpp": """class Solution {
public:
    ListNode* swapPairs(ListNode* head) {
        ListNode dummy(0, head);  // 哨兵，统一处理头节点交换
        ListNode* prev = &dummy;

        while (prev->next && prev->next->next) {
            ListNode* first = prev->next;
            ListNode* second = first->next;

            prev->next = second;         // 前驱接到新头 second
            first->next = second->next;  // first 接到后续链表
            second->next = first;        // second 指向 first，完成翻转

            prev = first;                // prev 移到本对尾节点，准备下一对
        }
        return dummy.next;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记 <code>dummy</code> 哨兵：第一对 <code>1↔2</code> 交换后新头是 2，没有哨兵时很难统一修改「头指针的前驱」。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 翻转顺序写错：必须先让 <code>prev.next = second</code>，再改 <code>first.next</code>，最后 <code>second.next = first</code>；若先改 <code>first.next</code> 可能丢失 <code>second</code> 的引用。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 循环后忘记 <code>prev = first</code>：否则 <code>prev</code> 仍指向已处理节点，会反复交换同一对或成环。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空链表</div>
    <code>head = [] → []</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单节点</div>
    <code>head = [1] → [1]</code>（不足一对，原样返回）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：奇数个节点</div>
    <code>head = [1,2,3] → [2,1,3]</code>（最后一对只有 3，不参与交换）
</div>""",
    },
    "reverse-nodes-in-k-group": {
        "type": "链表指针",
        "difficulty": "困难",
        "frontend_id": "25",
        "title": "K 个一组翻转链表",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你链表的头节点 <code>head</code>，每 <code>k</code> 个节点一组进行翻转，请你返回修改后的链表。</p>
<p><code>k</code> 是一个正整数，它的值小于或等于链表的长度。如果节点总数不是 <code>k</code> 的整数倍，那么请将最后剩余的节点保持原有顺序。</p>
<p>你不能只是单纯的改变节点内部的值，而是需要实际进行节点交换。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：head = [1,2,3,4,5], k = 2</div>
    <div class="example-output">输出：[2,1,4,3,5]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：head = [1,2,3,4,5], k = 3</div>
    <div class="example-output">输出：[3,2,1,4,5]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：head = [1], k = 1</div>
    <div class="example-output">输出：[1]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dummy</code></td><td>ListNode*</td><td><b>定义</b>：哨兵头节点，<code>dummy.next = head</code><br><b>维护</b>：始终位于真实头节点之前，统一处理「第一组翻转后新头节点」的边界<br><b>更新</b>：创建后不再移动，最终返回 <code>dummy.next</code></td></tr>
    <tr><td><code>group_prev</code></td><td>ListNode*</td><td><b>定义</b>：当前待翻转 <code>k</code> 组的前驱指针<br><b>维护</b>：每组翻转完成后，<code>group_prev</code> 应停在「刚翻转完的那一组的尾节点」（即翻转前的组头）<br><b>更新</b>：翻转一组后 <code>group_prev = group_start</code>（原组头变尾），下一轮从 <code>group_prev.next</code> 继续</td></tr>
    <tr><td><code>kth</code></td><td>ListNode*</td><td><b>定义</b>：从 <code>group_prev</code> 出发向后走 <code>k</code> 步得到的节点，即当前组的尾节点<br><b>维护</b>：若 <code>kth</code> 为 <code>null</code>，说明剩余不足 <code>k</code> 个节点，整题结束<br><b>更新</b>：每轮用 <code>getKth(group_prev, k)</code> 重新计算</td></tr>
    <tr><td><code>group_next</code></td><td>ListNode*</td><td><b>定义</b>：当前组尾节点 <code>kth</code> 的下一个节点，即下一组的起点<br><b>维护</b>：翻转时作为内层反转循环的终止边界（<code>curr != group_next</code>）<br><b>更新</b>：每轮在确认 <code>kth</code> 存在后令 <code>group_next = kth.next</code></td></tr>
    <tr><td><code>prev / curr</code></td><td>ListNode*</td><td><b>定义</b>：组内局部反转的双指针，<code>prev</code> 初始为 <code>group_next</code>，<code>curr</code> 初始为 <code>group_prev.next</code><br><b>维护</b>：标准单链表反转：保存 <code>tmp = curr.next</code>，<code>curr.next = prev</code>，前移 <code>prev</code> 与 <code>curr</code><br><b>更新</b>：当 <code>curr == group_next</code> 时本组反转完成；此时 <code>kth</code> 成为新组头，<code>group_start</code> 成为新组尾</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：把节点值复制到数组，按每 <code>k</code> 个一组反转数组片段再重建链表——能过，但题目要求「实际进行节点交换」，且多用了 O(n) 额外空间。</p>
<p class="thinking-step">2. 重复在哪里？#24 两两交换是 <code>k=2</code> 的特例；核心仍是「确定一组边界 → 局部反转 → 把反转后的组接回主链 → 前驱移到本组尾节点」。</p>
<p class="thinking-step">3. 难点是边界：剩余节点不足 <code>k</code> 个时不翻转。因此每轮先从 <code>group_prev</code> 走 <code>k</code> 步找 <code>kth</code>；找不到就直接结束。</p>
<p class="thinking-step">4. 找到 <code>kth</code> 后，在 <code>[group_prev.next, kth]</code> 闭区间内做标准链表反转，反转边界是 <code>group_next = kth.next</code>。反转完把 <code>group_prev.next</code> 指向新头 <code>kth</code>，再令 <code>group_prev = 原组头</code> 处理下一组。</p>
<p class="thinking-step">5. 第一组翻转会改变头节点——加 <code>dummy</code> 哨兵后，<code>group_prev</code> 从 <code>dummy</code> 出发，与 #24、合并链表等题同一套路；整体时间 O(n)，每个节点最多被访问常数次。</p>""",
        "code_steps": """<p class="code-step">1. 创建哨兵 <code>dummy = ListNode(0, head)</code>，<code>group_prev = dummy</code></p>
<p class="code-step">2. 循环：调用 <code>getKth(group_prev, k)</code> 找当前组尾 <code>kth</code>；若为 <code>null</code> 则剩余不足 <code>k</code> 个，跳出循环</p>
<p class="code-step">3. 记录 <code>group_next = kth.next</code>，<code>group_start = group_prev.next</code>（翻转后将变成本组尾）</p>
<p class="code-step">4. 在 <code>[group_start, kth]</code> 内局部反转：<code>prev = group_next</code>，<code>curr = group_start</code>，标准三指针翻转直到 <code>curr == group_next</code></p>
<p class="code-step">5. 接回主链：<code>group_prev.next = kth</code>（新组头），<code>group_prev = group_start</code>（新组尾作下轮前驱）；返回 <code>dummy.next</code></p>""",
        "code_python": """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        dummy = ListNode(0, head)   # 哨兵，统一处理头节点变化
        group_prev = dummy

        while True:
            kth = self.getKth(group_prev, k)
            if not kth:
                break

            group_next = kth.next
            group_start = group_prev.next

            # 在 [group_start, kth] 内局部反转，边界为 group_next
            prev, curr = group_next, group_start
            while curr != group_next:
                tmp = curr.next
                curr.next = prev
                prev = curr
                curr = tmp

            group_prev.next = kth          # 前驱接到翻转后的新头
            group_prev = group_start       # 原组头变尾，作为下一组前驱

        return dummy.next

    def getKth(self, curr: ListNode, k: int) -> Optional[ListNode]:
        while curr and k > 0:
            curr = curr.next
            k -= 1
        return curr""",
        "code_cpp": """class Solution {
public:
    ListNode* reverseKGroup(ListNode* head, int k) {
        ListNode dummy(0, head);  // 哨兵，统一处理头节点变化
        ListNode* group_prev = &dummy;

        while (true) {
            ListNode* kth = getKth(group_prev, k);
            if (!kth) break;

            ListNode* group_next = kth->next;
            ListNode* group_start = group_prev->next;

            // 在 [group_start, kth] 内局部反转，边界为 group_next
            ListNode* prev = group_next;
            ListNode* curr = group_start;
            while (curr != group_next) {
                ListNode* tmp = curr->next;
                curr->next = prev;
                prev = curr;
                curr = tmp;
            }

            group_prev->next = kth;       // 前驱接到翻转后的新头
            group_prev = group_start;     // 原组头变尾，作为下一组前驱
        }
        return dummy.next;
    }

private:
    ListNode* getKth(ListNode* curr, int k) {
        while (curr && k > 0) {
            curr = curr->next;
            k--;
        }
        return curr;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记先检查剩余是否足 <code>k</code> 个：不足时应保持原顺序直接结束，不能强行翻转。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 局部反转边界写错：<code>prev</code> 应初始化为 <code>group_next</code>（不是 <code>null</code>），否则翻转后无法与后续链表正确衔接。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 翻转后忘记更新 <code>group_prev</code>：应移到原组头（现组尾），否则下一轮会从已翻转区域重复操作或断链。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：k = 1</div>
    <code>head = [1,2,3], k = 1 → [1,2,3]</code>（每组 1 个，等价于不翻转）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：节点数恰为 k 的倍数</div>
    <code>head = [1,2,3,4], k = 2 → [2,1,4,3]</code>（全部参与翻转）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：尾部不足 k 个</div>
    <code>head = [1,2,3,4,5], k = 3 → [3,2,1,4,5]</code>（最后 4、5 保持原序）
</div>""",
    },

    "remove-duplicates-from-sorted-array": {
        "type": "双指针",
        "difficulty": "简单",
        "frontend_id": "26",
        "title": "删除有序数组中的重复项",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个 <strong>非严格递增排列</strong> 的数组 <code>nums</code>，请你<strong>原地</strong>删除重复出现的元素，使每个元素 <strong>只出现一次</strong>，返回删除后数组的新长度。元素的 <strong>相对顺序</strong> 应该保持 <strong>一致</strong>。</p>
<p>考虑 <code>nums</code> 的唯一元素的数量为 <code>k</code>。去重后，返回唯一元素的数量 <code>k</code>。<code>nums</code> 的前 <code>k</code> 个元素应包含排序后的唯一数字，下标 <code>k - 1</code> 之后的剩余元素可以忽略。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,1,2]</div>
    <div class="example-output">输出：2, nums = [1,2,_]</div>
    <div class="example-explain">函数应返回新长度 2，原数组前两个元素被修改为 1, 2。不需要考虑超出新长度后面的元素。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [0,0,1,1,1,2,2,3,3,4]</div>
    <div class="example-output">输出：5, nums = [0,1,2,3,4,_,_,_,_,_]</div>
    <div class="example-explain">函数应返回新长度 5，原数组前五个元素被修改为 0, 1, 2, 3, 4。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>slow</code></td><td>int</td><td><b>定义</b>：已写入去重结果区的<b>最后一个</b>唯一元素下标，即 <code>nums[0..slow]</code> 为当前已确认的唯一前缀<br><b>维护</b>：初始 <code>slow = 0</code>（第一个元素天然唯一）；每发现新值时先 <code>slow++</code> 再写入<br><b>更新</b>：当 <code>nums[fast] != nums[slow]</code> 时，<code>slow += 1; nums[slow] = nums[fast]</code></td></tr>
    <tr><td><code>fast</code></td><td>int</td><td><b>定义</b>：扫描指针，从 <code>1</code> 到 <code>n-1</code> 遍历整个数组<br><b>维护</b>：每次只与 <code>nums[slow]</code> 比较（有序数组下重复项必相邻，无需回看更早位置）<br><b>更新</b>：每轮循环末尾 <code>fast++</code>，直到遍历完所有元素</td></tr>
    <tr><td><code>k</code>（返回值）</td><td>int</td><td><b>定义</b>：去重后唯一元素个数<br><b>维护</b>：等于 <code>slow + 1</code>（下标从 0 起，长度 = 最后下标 + 1）<br><b>更新</b>：循环结束后直接返回，无需额外计数器</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：开一个新数组 <code>res</code>，从左到右扫 <code>nums</code>，遇到与 <code>res</code> 末尾不同的就 <code>append</code>——逻辑对，但用了 O(n) 额外空间，题目要求原地修改。</p>
<p class="thinking-step">2. 重复在哪里？数组已排序，相同元素一定挨在一起。去重时只需关心「当前已写入的最后一个唯一值」，不必与前面所有元素逐一比较。</p>
<p class="thinking-step">3. 双指针：用 <code>slow</code> 标记「去重结果区」的末尾，用 <code>fast</code> 从 <code>1</code> 开始扫描。若 <code>nums[fast] != nums[slow]</code>，说明遇到新唯一值，扩展结果区并写入。</p>
<p class="thinking-step">4. 为什么只比 <code>nums[slow]</code>？有序性保证：若 <code>nums[fast]</code> 与 <code>nums[slow]</code> 相等，则 <code>nums[fast]</code> 一定是重复；若不等，则 <code>nums[fast]</code> 一定大于 <code>nums[slow]</code>，是新唯一值。</p>
<p class="thinking-step">5. 最终 <code>nums[0..slow]</code> 即为去重结果，返回 <code>slow + 1</code>。每个元素最多被访问一次，时间 O(n)，仅用两个下标，空间 O(1)。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>nums</code> 为空，直接返回 0；否则令 <code>slow = 0</code>（<code>nums[0]</code> 作为第一个唯一元素）</p>
<p class="code-step">2. <code>for fast in range(1, len(nums))</code>：若 <code>nums[fast] != nums[slow]</code>，则 <code>slow += 1</code>，<code>nums[slow] = nums[fast]</code></p>
<p class="code-step">3. 循环结束，<code>nums[0..slow]</code> 为去重后的唯一前缀</p>
<p class="code-step">4. 返回 <code>slow + 1</code> 作为唯一元素个数 <code>k</code></p>""",
        "code_python": """class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        if not nums:
            return 0

        slow = 0  # nums[0..slow] 为当前已确认的唯一前缀
        for fast in range(1, len(nums)):
            if nums[fast] != nums[slow]:
                slow += 1
                nums[slow] = nums[fast]

        return slow + 1""",
        "code_cpp": """class Solution {
public:
    int removeDuplicates(vector<int>& nums) {
        if (nums.empty()) return 0;

        int slow = 0;  // nums[0..slow] 为当前已确认的唯一前缀
        for (int fast = 1; fast < nums.size(); fast++) {
            if (nums[fast] != nums[slow]) {
                slow++;
                nums[slow] = nums[fast];
            }
        }
        return slow + 1;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回值是 <code>slow + 1</code> 而不是 <code>slow</code>：下标从 0 开始，长度 = 最后下标 + 1。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 写入顺序错误：应先 <code>slow++</code> 再赋值 <code>nums[slow] = nums[fast]</code>，否则会覆盖尚未保留的唯一元素。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>fast</code> 应从 1 开始而非 0：<code>nums[0]</code> 已作为初始唯一元素，从 0 开始会把自己与自己比较，逻辑冗余且易错。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单元素</div>
    <code>nums = [1] → 1, nums = [1]</code>（无需去重，直接返回 1）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全部相同</div>
    <code>nums = [2,2,2,2] → 1, nums = [2,_,_,_]</code>（<code>fast</code> 扫完无新值，<code>slow</code> 始终为 0）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：无重复</div>
    <code>nums = [1,2,3,4] → 4, nums = [1,2,3,4]</code>（每个元素都被写入，<code>slow</code> 最终为 3）
</div>""",
    },
    "remove-element": {
        "type": "双指针",
        "difficulty": "简单",
        "frontend_id": "27",
        "title": "移除元素",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个数组 <code>nums</code> 和一个值 <code>val</code>，你需要 <strong>原地</strong> 移除所有数值等于 <code>val</code> 的元素。元素的顺序可能发生改变。然后返回 <code>nums</code> 中与 <code>val</code> 不同的元素的数量。</p>
<p>假设 <code>nums</code> 中不等于 <code>val</code> 的元素数量为 <code>k</code>，要通过此题，您需要执行以下操作：</p>
<ul>
<li>更改 <code>nums</code> 数组，使 <code>nums</code> 的前 <code>k</code> 个元素包含不等于 <code>val</code> 的元素。<code>nums</code> 的其余元素和 <code>nums</code> 的大小并不重要。</li>
<li>返回 <code>k</code>。</li>
</ul>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [3,2,2,3], val = 3</div>
    <div class="example-output">输出：2, nums = [2,2,_,_]</div>
    <div class="example-explain">函数应返回 k = 2，并且 nums 中的前两个元素均为 2。返回的 k 个元素之外留下什么并不重要。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [0,1,2,2,3,0,4,2], val = 2</div>
    <div class="example-output">输出：5, nums = [0,1,4,0,3,_,_,_]</div>
    <div class="example-explain">函数应返回 k = 5，并且 nums 中的前五个元素为 0,0,1,3,4（顺序可任意）。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>slow</code></td><td>int</td><td><b>定义</b>：下一个「保留元素」应写入的下标，也是当前已保留元素个数<br><b>维护</b>：初始 <code>slow = 0</code>；<code>nums[0..slow-1]</code> 均为不等于 <code>val</code> 的元素<br><b>更新</b>：当 <code>nums[fast] != val</code> 时，执行 <code>nums[slow] = nums[fast]; slow++</code></td></tr>
    <tr><td><code>fast</code></td><td>int</td><td><b>定义</b>：扫描指针，从 <code>0</code> 到 <code>n-1</code> 遍历整个数组<br><b>维护</b>：每轮检查 <code>nums[fast]</code> 是否等于 <code>val</code>，等于则跳过（不写），不等于则复制到保留区<br><b>更新</b>：每轮循环末尾 <code>fast++</code>，直到遍历完所有元素</td></tr>
    <tr><td><code>k</code>（返回值）</td><td>int</td><td><b>定义</b>：数组中不等于 <code>val</code> 的元素个数<br><b>维护</b>：等于循环结束后的 <code>slow</code>（每保留一个元素 <code>slow</code> 就 +1）<br><b>更新</b>：循环结束后直接返回 <code>slow</code>，无需额外计数器</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：开一个新数组 <code>res</code>，从左到右扫 <code>nums</code>，遇到不等于 <code>val</code> 的就 <code>append</code>——逻辑对，但用了 O(n) 额外空间，题目要求原地修改。</p>
<p class="thinking-step">2. 重复在哪里？每个元素只需判断一次「要不要保留」，保留的元素要紧凑写到数组前部。我不需要真正「删除」，只需把要保留的值覆盖到前面即可。</p>
<p class="thinking-step">3. 双指针：用 <code>slow</code> 标记下一个写入位置（也是已保留个数），用 <code>fast</code> 从 <code>0</code> 开始扫描。若 <code>nums[fast] != val</code>，就把它写到 <code>nums[slow]</code> 并 <code>slow++</code>。</p>
<p class="thinking-step">4. 为什么可以覆盖？<code>slow</code> 永远 ≤ <code>fast</code>：每遇到一个要移除的元素，<code>slow</code> 不动而 <code>fast</code> 前进，所以写入位置不会越过当前扫描位置，不会覆盖尚未处理的元素。</p>
<p class="thinking-step">5. 最终 <code>nums[0..slow-1]</code> 即为保留结果，返回 <code>slow</code>。每个元素访问一次，时间 O(n)，仅用两个下标，空间 O(1)。本题不要求保持原顺序，此写法最直观。</p>""",
        "code_steps": """<p class="code-step">1. 令 <code>slow = 0</code>，表示保留区下一个写入位置</p>
<p class="code-step">2. <code>for fast in range(len(nums))</code>：若 <code>nums[fast] != val</code>，则 <code>nums[slow] = nums[fast]</code>，<code>slow += 1</code></p>
<p class="code-step">3. 循环结束，<code>nums[0..slow-1]</code> 为所有不等于 <code>val</code> 的元素</p>
<p class="code-step">4. 返回 <code>slow</code> 作为保留元素个数 <code>k</code></p>""",
        "code_python": """class Solution:
    def removeElement(self, nums: List[int], val: int) -> int:
        slow = 0  # nums[0..slow-1] 为已保留的元素
        for fast in range(len(nums)):
            if nums[fast] != val:
                nums[slow] = nums[fast]
                slow += 1
        return slow""",
        "code_cpp": """class Solution {
public:
    int removeElement(vector<int>& nums, int val) {
        int slow = 0;  // nums[0..slow-1] 为已保留的元素
        for (int fast = 0; fast < nums.size(); fast++) {
            if (nums[fast] != val) {
                nums[slow] = nums[fast];
                slow++;
            }
        }
        return slow;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回值是 <code>slow</code> 而不是 <code>slow - 1</code>：本题 <code>slow</code> 表示「已保留个数」，与 #26 去重题（<code>slow</code> 是最后下标）语义不同。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 写入顺序错误：应先判断 <code>nums[fast] != val</code> 再写入并 <code>slow++</code>，遇到 <code>val</code> 时 <code>slow</code> 不能动。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 误以为必须保持原顺序：本题允许打乱顺序，从左到右覆盖即可；若强行保持顺序需更复杂的双指针写法，此处不必。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空数组</div>
    <code>nums = [], val = 1 → 0</code>（循环不执行，直接返回 0）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全部为 val</div>
    <code>nums = [3,3,3], val = 3 → 0</code>（无元素被保留，<code>slow</code> 始终为 0）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：无 val</div>
    <code>nums = [1,2,3], val = 4 → 3, nums = [1,2,3]</code>（每个元素都被保留，<code>slow</code> 最终为 3）
</div>""",
    },

    "find-the-index-of-the-first-occurrence-in-a-string": {
        "type": "字符串模拟",
        "difficulty": "简单",
        "frontend_id": "28",
        "title": "找出字符串中第一个匹配项的下标",
        "time_complexity": "O(n·m)",
        "space_complexity": "O(1)",
        "description": """<p>给你两个字符串 <code>haystack</code> 和 <code>needle</code>，请你在 <code>haystack</code> 字符串中找出 <code>needle</code> 字符串的第一个匹配项的下标（下标从 0 开始）。如果 <code>needle</code> 不是 <code>haystack</code> 的一部分，则返回 <code>-1</code>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：haystack = "sadbutsad", needle = "sad"</div>
    <div class="example-output">输出：0</div>
    <div class="example-explain">"sad" 在下标 0 和 6 处匹配，第一个匹配项的下标是 0。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：haystack = "leetcode", needle = "leeto"</div>
    <div class="example-output">输出：-1</div>
    <div class="example-explain">"leeto" 没有在 "leetcode" 中出现。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：<code>haystack</code> 中尝试作为匹配起点的下标<br><b>维护</b>：从 <code>0</code> 到 <code>n - m</code> 枚举每个可能起点<br><b>更新</b>：每轮外层循环 <code>i++</code>，直到找到匹配或枚举完毕</td></tr>
    <tr><td><code>j</code></td><td>int</td><td><b>定义</b>：当前正在比对的 <code>needle</code> 内偏移量<br><b>维护</b>：当 <code>haystack[i+j] == needle[j]</code> 时同步前进，否则本轮起点 <code>i</code> 失败<br><b>更新</b>：匹配成功则 <code>j++</code>；若 <code>j == m</code> 说明整段 <code>needle</code> 匹配完成</td></tr>
    <tr><td><code>m</code></td><td>int</td><td><b>定义</b>：<code>needle</code> 的长度<br><b>维护</b>：循环中用于判断「从 <code>i</code> 起是否还能放下整段 <code>needle</code>」以及「<code>j</code> 是否已扫完 <code>needle</code>」<br><b>更新</b>：初始化时 <code>m = len(needle)</code>，循环中不变</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：在 <code>haystack</code> 的每个下标 <code>i</code> 尝试把 <code>needle</code> 对齐上去，逐字符比较——逻辑直接，但最坏要试 O(n) 个起点、每次比 O(m) 个字符。</p>
<p class="thinking-step">2. 重复在哪里？每个起点 <code>i</code> 都在做同一件事：检查 <code>haystack[i..i+m-1]</code> 是否等于 <code>needle</code>。一旦某字符不等就可以立刻放弃当前 <code>i</code>。</p>
<p class="thinking-step">3. 优化起点范围：若 <code>i + m &gt; n</code>，后面再也放不下整段 <code>needle</code>，所以 <code>i</code> 只需从 <code>0</code> 到 <code>n - m</code>（<code>n</code> 为 <code>haystack</code> 长度）。</p>
<p class="thinking-step">4. 内层用 <code>j</code> 从 <code>0</code> 到 <code>m-1</code> 比较 <code>haystack[i+j]</code> 与 <code>needle[j]</code>；若全程相等则返回 <code>i</code>，否则继续下一个起点。</p>
<p class="thinking-step">5. 全部起点都失败则返回 <code>-1</code>。本题数据规模下暴力足够；KMP 等算法可把均摊复杂度降到 O(n+m)，但实现更重，简单题先掌握双下标模拟即可。</p>""",
        "code_steps": """<p class="code-step">1. 令 <code>n = len(haystack)</code>，<code>m = len(needle)</code></p>
<p class="code-step">2. 外层 <code>for i in range(n - m + 1)</code>：以 <code>i</code> 为起点尝试匹配</p>
<p class="code-step">3. 内层 <code>j</code> 从 <code>0</code> 到 <code>m-1</code>：若 <code>haystack[i+j] != needle[j]</code> 则跳出内层，换下一个 <code>i</code></p>
<p class="code-step">4. 若内层未提前跳出（<code>j == m</code>），说明匹配成功，返回 <code>i</code></p>
<p class="code-step">5. 所有起点均失败，返回 <code>-1</code></p>""",
        "code_python": """class Solution:
    def strStr(self, haystack: str, needle: str) -> int:
        n, m = len(haystack), len(needle)
        for i in range(n - m + 1):          # 枚举每个可能的起点
            j = 0
            while j < m and haystack[i + j] == needle[j]:
                j += 1                      # 逐字符对齐 needle
            if j == m:                      # 整段 needle 匹配完成
                return i
        return -1""",
        "code_cpp": """class Solution {
public:
    int strStr(string haystack, string needle) {
        int n = haystack.size(), m = needle.size();
        for (int i = 0; i <= n - m; i++) {  // 枚举每个可能的起点
            int j = 0;
            while (j < m && haystack[i + j] == needle[j]) {
                j++;                         // 逐字符对齐 needle
            }
            if (j == m) return i;            // 整段匹配完成
        }
        return -1;
    }
};
// 时间 O(n·m)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 外层循环边界是 <code>i &lt;= n - m</code>（即 <code>range(n - m + 1)</code>），漏掉最后一个合法起点会错。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 内层比较要用 <code>haystack[i + j]</code> 而不是 <code>haystack[j]</code>，起点偏移 <code>i</code> 不能丢。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 匹配成功条件是 <code>j == m</code>（扫完整个 needle），不是 <code>j == m - 1</code>；提前 <code>return i</code> 前务必确认内层完整通过。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：needle 比 haystack 长</div>
    <code>haystack = "a", needle = "aa" → -1</code>（<code>n - m + 1 &lt;= 0</code>，外层不执行）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：完全相等</div>
    <code>haystack = "abc", needle = "abc" → 0</code>（第一个起点即匹配）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：首字符相同但后续失败</div>
    <code>haystack = "aaaaa", needle = "aab" → -1</code>（多个起点共享前缀，需在第三位发现不等）
</div>""",
    },

    "divide-two-integers": {
        "type": "数学模拟",
        "difficulty": "中等",
        "frontend_id": "29",
        "title": "两数相除",
        "time_complexity": "O(log²n)",
        "space_complexity": "O(1)",
        "description": """<p>给你两个整数，被除数 <code>dividend</code> 和除数 <code>divisor</code>。将两数相除，要求 <strong>不使用</strong> 乘法、除法和取余运算。</p>
<p>整数除法应该向零截断，也就是截去（<code>truncate</code>）其小数部分。例如，<code>8.345</code> 将被截断为 <code>8</code>，<code>-2.7335</code> 将被截断至 <code>-2</code>。</p>
<p>返回被除数 <code>dividend</code> 除以除数 <code>divisor</code> 得到的 <strong>商</strong>。</p>
<p><strong>注意：</strong>假设我们的环境只能存储 <strong>32 位</strong> 有符号整数，其数值范围是 <code>[−2<sup>31</sup>, 2<sup>31</sup> − 1]</code>。本题中，如果商 <strong>严格大于</strong> <code>2<sup>31</sup> − 1</code>，则返回 <code>2<sup>31</sup> − 1</code>；如果商 <strong>严格小于</strong> <code>-2<sup>31</sup></code>，则返回 <code>-2<sup>31</sup></code>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：dividend = 10, divisor = 3</div>
    <div class="example-output">输出：3</div>
    <div class="example-explain">10/3 = 3.33333..，向零截断后得到 3。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：dividend = 7, divisor = -3</div>
    <div class="example-output">输出：-2</div>
    <div class="example-explain">7/-3 = -2.33333..，向零截断后得到 -2。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>sign</code></td><td>int</td><td><b>定义</b>：最终商的符号，<code>+1</code> 或 <code>-1</code><br><b>维护</b>：由 <code>dividend</code> 与 <code>divisor</code> 异号则为 <code>-1</code>，同号为 <code>+1</code><br><b>更新</b>：在转绝对值之前一次性确定，循环中不变</td></tr>
    <tr><td><code>a</code></td><td>long</td><td><b>定义</b>：被除数的绝对值，表示「还剩多少没减完」<br><b>维护</b>：每轮外层循环从 <code>a</code> 中减去一块 <code>temp</code>，直到 <code>a &lt; b</code><br><b>更新</b>：初始化 <code>a = abs(dividend)</code>；每轮 <code>a -= temp</code></td></tr>
    <tr><td><code>b</code></td><td>long</td><td><b>定义</b>：除数的绝对值，作为每次「加倍试探」的基准<br><b>维护</b>：全程不变，用于判断 <code>a</code> 是否还能再减以及内层左移的上界<br><b>更新</b>：初始化 <code>b = abs(divisor)</code>，循环中不变</td></tr>
    <tr><td><code>temp</code></td><td>long</td><td><b>定义</b>：当前这一轮准备一次性减去的「块」，等于 <code>b × 2<sup>k</sup></code><br><b>维护</b>：内层循环通过左移不断加倍，直到再加倍会超过 <code>a</code><br><b>更新</b>：每轮外层开始时重置为 <code>b</code>，内层满足条件时 <code>temp &lt;&lt;= 1</code></td></tr>
    <tr><td><code>multiple</code></td><td>long</td><td><b>定义</b>：与 <code>temp</code> 同步的权重，表示本轮减去的块相当于多少个 <code>b</code><br><b>维护</b>：<code>temp</code> 每左移一位，<code>multiple</code> 也左移一位（即 ×2）<br><b>更新</b>：每轮外层重置为 <code>1</code>；减完后 <code>quotient += multiple</code></td></tr>
    <tr><td><code>quotient</code></td><td>long</td><td><b>定义</b>：累加得到的商（绝对值部分）<br><b>维护</b>：每从 <code>a</code> 减去一块 <code>temp</code>，就把对应权重 <code>multiple</code> 加入商<br><b>更新</b>：初始化 <code>0</code>；每轮 <code>quotient += multiple</code>，最后乘 <code>sign</code> 并裁剪到 32 位范围</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：用 <code>while a &gt;= b</code> 每次 <code>a -= b; quotient++</code>——逻辑对，但 <code>dividend = 2<sup>31</sup>-1, divisor = 1</code> 要循环 20 亿次，必超时。</p>
<p class="thinking-step">2. 重复在哪里？每次只减一个 <code>b</code> 太碎。其实商的本质是「<code>a</code> 里能装下多少个 <code>b</code>」，可以一次减去 <code>2b、4b、8b…</code> 这样的大块，再把对应倍数加进商。</p>
<p class="thinking-step">3. 位运算加倍：内层令 <code>temp = b</code>、<code>multiple = 1</code>，只要 <code>a &gt;= temp &lt;&lt; 1</code> 就同时左移 <code>temp</code> 和 <code>multiple</code>（等价于 ×2，不用乘法）。这样一轮能吃掉尽可能大的一块。</p>
<p class="thinking-step">4. 符号单独处理：先把 <code>dividend、divisor</code> 转绝对值到 <code>a、b</code>，用异或判断 <code>sign</code>；唯一特判 <code>INT_MIN / -1</code> 会溢出，直接返回 <code>INT_MAX</code>。</p>
<p class="thinking-step">5. 累加完乘 <code>sign</code> 后，用 <code>max(INT_MIN, min(INT_MAX, quotient))</code> 裁剪到 32 位。每轮外层减一块、内层加倍，总复杂度 O(log²n)。</p>""",
        "code_steps": """<p class="code-step">1. 特判 <code>dividend == INT_MIN and divisor == -1</code>，直接返回 <code>INT_MAX</code></p>
<p class="code-step">2. 计算 <code>sign</code>，令 <code>a = abs(dividend)</code>、<code>b = abs(divisor)</code>，<code>quotient = 0</code></p>
<p class="code-step">3. 外层 <code>while a &gt;= b</code>：重置 <code>temp = b</code>、<code>multiple = 1</code></p>
<p class="code-step">4. 内层 <code>while a &gt;= temp &lt;&lt; 1</code>：<code>temp &lt;&lt;= 1</code>，<code>multiple &lt;&lt;= 1</code>（找到本轮最大可减块）</p>
<p class="code-step">5. 执行 <code>a -= temp</code>，<code>quotient += multiple</code>，继续外层直到 <code>a &lt; b</code></p>
<p class="code-step">6. 返回 <code>sign * quotient</code> 裁剪到 <code>[INT_MIN, INT_MAX]</code></p>""",
        "code_python": """class Solution:
    def divide(self, dividend: int, divisor: int) -> int:
        INT_MAX = 2**31 - 1
        INT_MIN = -2**31
        if dividend == INT_MIN and divisor == -1:
            return INT_MAX
        sign = -1 if (dividend < 0) ^ (divisor < 0) else 1
        a, b = abs(dividend), abs(divisor)
        quotient = 0
        while a >= b:
            temp, multiple = b, 1
            while a >= temp << 1:       # 加倍试探，找本轮最大块
                temp <<= 1
                multiple <<= 1
            a -= temp
            quotient += multiple
        quotient *= sign
        return max(INT_MIN, min(INT_MAX, quotient))""",
        "code_cpp": """class Solution {
public:
    int divide(int dividend, int divisor) {
        const int INT_MAX = 0x7FFFFFFF;
        const int INT_MIN = 0x80000000;
        if (dividend == INT_MIN && divisor == -1) return INT_MAX;
        int sign = (dividend < 0) ^ (divisor < 0) ? -1 : 1;
        long a = labs((long)dividend), b = labs((long)divisor);
        long quotient = 0;
        while (a >= b) {
            long temp = b, multiple = 1;
            while (a >= (temp << 1)) {   // 加倍试探，找本轮最大块
                temp <<= 1;
                multiple <<= 1;
            }
            a -= temp;
            quotient += multiple;
        }
        quotient *= sign;
        if (quotient > INT_MAX) return INT_MAX;
        if (quotient < INT_MIN) return INT_MIN;
        return (int)quotient;
    }
};
// 时间 O(log²n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 溢出：必须用 <code>long</code> 存 <code>a、b、temp、quotient</code>；<code>INT_MIN / -1</code> 在 32 位下会溢出，需单独返回 <code>INT_MAX</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 内层条件是 <code>a &gt;= temp &lt;&lt; 1</code>（还能再翻倍才移），不是 <code>a &gt;= temp</code>；否则 <code>temp</code> 会多加一位导致减法过量。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 符号用异或 <code>(dividend &lt; 0) ^ (divisor &lt; 0)</code> 判断，转绝对值后再算；最后结果要裁剪到 32 位有符号范围。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：被除数为 0</div>
    <code>dividend = 0, divisor = 5 → 0</code>（<code>a &lt; b</code>，循环不执行）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：溢出边界</div>
    <code>dividend = -2147483648, divisor = -1 → 2147483647</code>（唯一需特判的溢出情形）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：商为 1</div>
    <code>dividend = 3, divisor = 3 → 1</code>（<code>a == b</code>，一轮减完）
</div>""",
    },
    "substring-with-concatenation-of-all-words": {
        "type": "可变滑窗",
        "difficulty": "困难",
        "frontend_id": "30",
        "title": "串联所有单词的子串",
        "time_complexity": "O(n × wordLen)",
        "space_complexity": "O(m)",
        "description": """<p>给定一个字符串 <code>s</code> 和一个字符串数组 <code>words</code>。<code>words</code> 中所有字符串 <strong>长度相同</strong>。</p>
<p><code>s</code> 中的 <strong>串联子串</strong> 是指一个包含 <code>words</code> 中所有字符串以任意顺序排列连接起来的子串。</p>
<p>返回所有串联子串在 <code>s</code> 中的开始索引。你可以以 <strong>任意顺序</strong> 返回答案。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "barfoothefoobarman", words = ["foo","bar"]</div>
    <div class="example-output">输出：[0,9]</div>
    <div class="example-explain">子串 "barfoo"（下标 0）和 "foobar"（下标 9）都是 words 的某种排列连接，长度均为 6。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "wordgoodgoodgoodbestword", words = ["word","good","best","word"]</div>
    <div class="example-output">输出：[]</div>
    <div class="example-explain">需要长度 16 的串联子串，s 中不存在满足条件的子串。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：s = "barfoofoobarthefoobarman", words = ["bar","foo","the"]</div>
    <div class="example-output">输出：[6,9,12]</div>
    <div class="example-explain">下标 6、9、12 分别对应 "foobarthe"、"barthefoo"、"thefoobar"。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>need[w]</code></td><td>map&lt;string,int&gt;</td><td><b>定义</b>：目标单词 w 在 words 中应出现的次数<br><b>维护</b>：不变量，由 words 初始化<br><b>更新</b>：不更新</td></tr>
    <tr><td><code>window[w]</code></td><td>map&lt;string,int&gt;</td><td><b>定义</b>：当前「按单词切分」的滑窗内，单词 w 的出现次数<br><b>维护</b>：随窗口在 s 上按 <code>wordLen</code> 步长滑动而增减<br><b>更新</b>：右端加入单词时 <code>window[w]++</code>；左端移出时 <code>window[w]--</code></td></tr>
    <tr><td><code>valid</code></td><td>int</td><td><b>定义</b>：窗口内已「恰好匹配」need 的单词种类数（<code>window[w] == need[w]</code>）<br><b>维护</b>：每轮后 valid 等于满足精确匹配的单词种类数<br><b>更新</b>：某词计数从 need-1 变 need 时 valid++；从 need 变 need-1 时 valid--</td></tr>
    <tr><td><code>offset</code></td><td>int</td><td><b>定义</b>：当前滑窗在 s 上的起始对齐偏移（0 到 wordLen-1）<br><b>维护</b>：每个 offset 独立跑一遍「按单词步长」的滑窗，覆盖所有可能切分<br><b>更新</b>：外层循环 <code>offset++</code>，内层从 <code>offset</code> 起按 <code>wordLen</code> 步进</td></tr>
    <tr><td><code>left / right</code></td><td>int</td><td><b>定义</b>：当前窗口在 s 中的左右边界（字符下标）<br><b>维护</b>：窗口始终覆盖连续 <code>k</code> 个单词块，总字符长 <code>k × wordLen</code><br><b>更新</b>：<code>right</code> 每次 +wordLen 加入一块；超限时 <code>left</code> 循环 +wordLen 移出</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：枚举 s 中每个起点 i，切出长度 <code>wordLen × |words|</code> 的子串，再判断是否等于 words 的某种排列——要检查所有排列或逐词匹配，复杂度爆炸。</p>
<p class="thinking-step">2. 重复在哪里？每个起点都在重新切词、重新比对。其实合法串联子串的长度固定，且每个单词长度相同，可以按「单词块」而不是单字符来滑窗。</p>
<p class="thinking-step">3. 关键观察：若按字符下标 <code>i</code> 切块，只有 <code>i % wordLen</code> 相同的起点才属于同一套切分方式。所以对 offset = 0..wordLen-1 各跑一遍滑窗即可覆盖全部可能。</p>
<p class="thinking-step">4. 滑窗逻辑类似「最小覆盖子串」：右扩加入一块单词，若某词超量就从左缩；当 <code>valid == len(need)</code> 时，<code>left</code> 即为一个合法串联子串起点。</p>
<p class="thinking-step">5. 若右端切出的块不在 need 中，当前切分方式已不可能继续匹配，直接清空窗口并把 left 跳到 right 之后。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>words</code> 为空或 <code>len(s) &lt; wordLen × wordCount</code>，直接返回空列表</p>
<p class="code-step">2. 统计 <code>need</code>：遍历 words，<code>need[w]++</code>；记 <code>wordLen</code>、<code>wordCount</code></p>
<p class="code-step">3. 对每个 <code>offset ∈ [0, wordLen)</code>：初始化 <code>left = offset</code>、<code>window = {}</code>、<code>valid = 0</code></p>
<p class="code-step">4. <code>right</code> 从 <code>offset</code> 起每次 +wordLen：切出 <code>word = s[right:right+wordLen]</code></p>
<p class="code-step">5. 若 <code>word</code> 不在 need：清空 window、valid=0，<code>left = right + wordLen</code>（整块对齐后重启）</p>
<p class="code-step">6. 否则 <code>window[word]++</code>，循环收缩：若 <code>window[word] &gt; need[word]</code>，移出 left 块并更新 valid，<code>left += wordLen</code></p>
<p class="code-step">7. 若 <code>window[word] == need[word]</code> 则 <code>valid++</code>；当 <code>valid == len(need)</code> 时把 <code>left</code> 记入结果</p>
<p class="code-step">8. 汇总所有 offset 的结果并返回</p>""",
        "code_python": """class Solution:
    def findSubstring(self, s: str, words: list[str]) -> list[int]:
        if not words:
            return []
        word_len = len(words[0])
        word_count = len(words)
        total_len = word_len * word_count
        if len(s) < total_len:
            return []

        need = {}
        for w in words:
            need[w] = need.get(w, 0) + 1

        result = []
        need_types = len(need)

        for offset in range(word_len):
            left = offset
            valid = 0
            window = {}

            right = offset
            while right + word_len <= len(s):
                word = s[right:right + word_len]

                if word not in need:
                    window.clear()
                    valid = 0
                    left = right + word_len
                else:
                    window[word] = window.get(word, 0) + 1
                    while window[word] > need[word]:
                        left_word = s[left:left + word_len]
                        if window[left_word] == need[left_word]:
                            valid -= 1
                        window[left_word] -= 1
                        left += word_len

                    if window[word] == need[word]:
                        valid += 1

                    if valid == need_types:
                        result.append(left)

                right += word_len

        return result""",
        "code_cpp": """class Solution {
public:
    vector<int> findSubstring(string s, vector<string>& words) {
        vector<int> result;
        if (words.empty()) return result;

        int wordLen = words[0].size();
        int wordCount = words.size();
        int totalLen = wordLen * wordCount;
        if (s.size() < totalLen) return result;

        unordered_map<string, int> need;
        for (const string& w : words) need[w]++;

        int needTypes = need.size();

        for (int offset = 0; offset < wordLen; offset++) {
            int left = offset, valid = 0;
            unordered_map<string, int> window;

            for (int right = offset; right + wordLen <= s.size(); right += wordLen) {
                string word = s.substr(right, wordLen);

                if (!need.count(word)) {
                    window.clear();
                    valid = 0;
                    left = right + wordLen;
                } else {
                    window[word]++;
                    while (window[word] > need[word]) {
                        string leftWord = s.substr(left, wordLen);
                        if (window[leftWord] == need[leftWord]) valid--;
                        window[leftWord]--;
                        left += wordLen;
                    }
                    if (window[word] == need[word]) valid++;
                    if (valid == needTypes) result.push_back(left);
                }
            }
        }
        return result;
    }
};
// 时间 O(n × wordLen)，空间 O(m)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 必须对每个 <code>offset ∈ [0, wordLen)</code> 单独滑窗；只从 0 开始会漏掉如 "barfoo" 与 "foobar" 这类不同对齐的合法起点。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>valid</code> 只在 <code>window[w] == need[w]</code> 时 +1，超过 need 不算；收缩时须先判断 <code>== need</code> 再 --，与最小覆盖子串一致。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 遇到不在 need 中的单词块要<strong>整块重置</strong>窗口，并把 left 跳到 right+wordLen，否则脏数据会误报合法起点。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：words 含重复词</div>
    <code>words = ["word","good","best","word"]</code>，需要窗口内 "word" 恰好出现 2 次才算 valid。
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：s 长度不足</div>
    <code>len(s) &lt; wordLen × wordCount → []</code>（无需进入滑窗）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：words 为空</div>
    <code>words = [] → []</code>（按题意通常不会出现，但实现上应直接返回）
</div>""",
    },
    "next-permutation": {
        "type": "双指针",
        "difficulty": "中等",
        "frontend_id": "31",
        "title": "下一个排列",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>整数数组的一个 <strong>排列</strong> 就是将其所有成员以序列或线性顺序排列。</p>
<p>整数数组的 <strong>下一个排列</strong> 是指其整数的下一个字典序更大的排列。更正式地，如果数组的所有排列根据其字典顺序从小到大排列在一个容器中，那么数组的 <strong>下一个排列</strong> 就是在这个有序容器中排在它后面的那个排列。如果不存在下一个更大的排列，那么这个数组必须重排为字典序最小的排列（即，其元素按升序排列）。</p>
<p>给你一个整数数组 <code>nums</code>，找出 <code>nums</code> 的下一个排列。</p>
<p>必须<strong>原地</strong>修改，只允许使用额外常数空间。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,2,3]</div>
    <div class="example-output">输出：[1,3,2]</div>
    <div class="example-explain">[1,2,3] 的下一个字典序更大排列是 [1,3,2]。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [3,2,1]</div>
    <div class="example-output">输出：[1,2,3]</div>
    <div class="example-explain">[3,2,1] 已是最大排列，下一个排列为最小排列 [1,2,3]。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [1,1,5]</div>
    <div class="example-output">输出：[1,5,1]</div>
    <div class="example-explain">将末尾 1 与 5 交换，再反转后缀 [5,1] → [1,5]。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：从右向左第一个满足 <code>nums[i] &lt; nums[i+1]</code> 的下标，即「后缀升序」被打破的位置<br><b>维护</b>：若找不到则当前已是最大排列，需整体反转<br><b>更新</b>：从 <code>n-2</code> 向左扫描，找到第一个「比右边邻居小」的元素</td></tr>
    <tr><td><code>j</code></td><td>int</td><td><b>定义</b>：在 <code>i</code> 右侧后缀中，从右向左第一个满足 <code>nums[j] &gt; nums[i]</code> 的下标<br><b>维护</b>：保证交换后 <code>nums[i]</code> 位置换成「后缀中刚好比它大的最小值」<br><b>更新</b>：从 <code>n-1</code> 向左扫描至 <code>i+1</code>，找到第一个大于 <code>nums[i]</code> 的元素</td></tr>
    <tr><td><code>left / right</code></td><td>int</td><td><b>定义</b>：交换后待反转后缀 <code>nums[i+1..n-1]</code> 的双指针边界<br><b>维护</b>：后缀经交换后仍降序，反转后变为升序，得到「刚好大一点的」最小后缀<br><b>更新</b>：<code>left = i+1</code>，<code>right = n-1</code>，双指针向中间交换直至 <code>left &gt;= right</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：生成所有排列、排序、找当前排列的下一个——能过但 O(n×n!)，完全不可接受。</p>
<p class="thinking-step">2. 重复在哪里？字典序的「下一个」有规律：从右往左看，若后缀是严格降序（如 [3,2,1]），说明没有更大的了，只能回到最小排列。</p>
<p class="thinking-step">3. 关键观察：找第一个 <code>nums[i] &lt; nums[i+1]</code>，说明 <code>i</code> 右侧是降序后缀；要让整体字典序变大，必须增大 <code>nums[i]</code>，且增幅要尽可能小。</p>
<p class="thinking-step">4. 因此在后缀中找刚好比 <code>nums[i]</code> 大的最小元素 <code>nums[j]</code>，交换 <code>nums[i]</code> 与 <code>nums[j]</code>；交换后 <code>i+1</code> 右侧仍是降序，再反转后缀得到升序，即「下一个排列」。</p>
<p class="thinking-step">5. 若找不到这样的 <code>i</code>，说明整个数组降序，直接反转全数组即可得到最小排列；全程原地 O(n) 时间、O(1) 空间。</p>""",
        "code_steps": """<p class="code-step">1. 令 <code>n = len(nums)</code>，从 <code>i = n-2</code> 向左找第一个 <code>nums[i] &lt; nums[i+1]</code></p>
<p class="code-step">2. 若找不到 <code>i</code>（<code>i &lt; 0</code>）：整个数组降序，反转 <code>nums[0..n-1]</code> 后返回</p>
<p class="code-step">3. 从 <code>j = n-1</code> 向左找第一个 <code>nums[j] &gt; nums[i]</code></p>
<p class="code-step">4. 交换 <code>nums[i]</code> 与 <code>nums[j]</code></p>
<p class="code-step">5. 双指针反转后缀 <code>nums[i+1..n-1]</code>（<code>left = i+1</code>，<code>right = n-1</code>，交换并向中间移动）</p>""",
        "code_python": """class Solution:
    def nextPermutation(self, nums: list[int]) -> None:
        n = len(nums)

        # 1. 从右向左找第一个「升序对」的左端 i
        i = n - 2
        while i >= 0 and nums[i] >= nums[i + 1]:
            i -= 1

        if i >= 0:
            # 2. 在后缀中找刚好比 nums[i] 大的元素 j
            j = n - 1
            while nums[j] <= nums[i]:
                j -= 1
            nums[i], nums[j] = nums[j], nums[i]

        # 3. 反转 i+1 到末尾（若 i<0 则反转整个数组）
        left, right = i + 1, n - 1
        while left < right:
            nums[left], nums[right] = nums[right], nums[left]
            left += 1
            right -= 1""",
        "code_cpp": """class Solution {
public:
    void nextPermutation(vector<int>& nums) {
        int n = nums.size();

        // 1. 从右向左找第一个「升序对」的左端 i
        int i = n - 2;
        while (i >= 0 && nums[i] >= nums[i + 1]) {
            i--;
        }

        if (i >= 0) {
            // 2. 在后缀中找刚好比 nums[i] 大的元素 j
            int j = n - 1;
            while (nums[j] <= nums[i]) {
                j--;
            }
            swap(nums[i], nums[j]);
        }

        // 3. 反转 i+1 到末尾（若 i<0 则反转整个数组）
        reverse(nums.begin() + i + 1, nums.end());
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 找 <code>i</code> 的条件是 <code>nums[i] &lt; nums[i+1]</code>（严格小于），不是 <code>&lt;=</code>；相等时不能停，否则重复元素会选错下一个排列。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 找 <code>j</code> 时同样用严格大于 <code>nums[i]</code>；交换后必须<strong>反转后缀</strong>，不能只交换就结束——后缀仍是降序，不反转得不到最小合法后缀。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 当 <code>i &lt; 0</code>（已是最大排列）时，跳过交换步骤，直接反转整个数组；忘记这一步会返回原数组而非最小排列。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单元素</div>
    <code>nums = [1] → [1]</code>（<code>i = -1</code>，反转自身不变）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：已是最大排列</div>
    <code>nums = [3,2,1] → [1,2,3]</code>（找不到 <code>i</code>，整体反转）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：含重复元素</div>
    <code>nums = [1,1,5] → [1,5,1]</code>（<code>i=1, j=2</code>，交换后反转后缀）
</div>""",
    },
    "longest-valid-parentheses": {
        "type": "栈",
        "difficulty": "困难",
        "frontend_id": "32",
        "title": "最长有效括号",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "description": """<p>给你一个只包含 <code>'('</code> 和 <code>')'</code> 的字符串，找出最长有效（格式正确且连续）括号 <strong>子串</strong> 的长度。</p>
<p>左右括号匹配，即每个左括号都有对应的右括号将其闭合的字符串是格式正确的，比如 <code>"(()())"</code>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "(()"</div>
    <div class="example-output">输出：2</div>
    <div class="example-explain">最长有效括号子串是 <code>"()"</code>。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = ")()())"</div>
    <div class="example-output">输出：4</div>
    <div class="example-explain">最长有效括号子串是 <code>"()()"</code>。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：s = ""</div>
    <div class="example-output">输出：0</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>stk</code></td><td>list / stack</td><td><b>定义</b>：存放「尚未被匹配的左括号下标」以及作为基准的哨兵下标<br><b>维护</b>：栈顶对应当前有效子串的「左边界前一位」；初始压入 <code>-1</code> 作为全局基准<br><b>更新</b>：遇 <code>'('</code> 压入下标 <code>i</code>；遇 <code>')'</code> 先 <code>pop</code>，栈空则压入 <code>i</code> 重置基准，否则用 <code>i - stk[-1]</code> 更新答案</td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：截至目前发现的最长有效括号子串长度<br><b>维护</b>：单调不减，记录全局最优<br><b>更新</b>：每次成功匹配右括号后，计算 <code>i - stk[-1]</code> 并与 <code>ans</code> 取 <code>max</code></td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：当前扫描到的字符下标<br><b>维护</b>：从左到右依次处理每个括号<br><b>更新</b>：每轮循环 <code>i += 1</code>，根据 <code>s[i]</code> 是左/右括号分支更新栈与答案</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：枚举所有子串，对每个子串用栈或计数判断括号是否有效，取最长——能过但 O(n³) 或 O(n²)，3×10⁴ 的数据会超时。</p>
<p class="thinking-step">2. 重复在哪里？每遇到一个 <code>')'</code>，它只能与「离它最近、尚未匹配」的 <code>'('</code> 配对——又是后进先出；但本题要的是<strong>最长连续有效子串</strong>，不是判断整串是否有效。</p>
<p class="thinking-step">3. 关键转化：栈里不存字符，存<strong>下标</strong>。压入哨兵 <code>-1</code> 表示「有效段起点的前一位」；每次 <code>')'</code> 弹出匹配的 <code>'('</code> 后，当前有效段长度 = <code>当前下标 - 栈顶下标</code>。</p>
<p class="thinking-step">4. 若弹出后栈空，说明这个 <code>')'</code> 无法配对（如开头就是 <code>')'</code>），把它压回栈作为新的「分割点」，后面的有效段从这里重新计算。</p>
<p class="thinking-step">5. 例 <code>")()())"</code>：遇到开头 <code>')'</code> 后栈只剩 <code>[2]</code> 作基准，随后 <code>()</code> 得长度 2，再 <code>()</code> 得长度 4；全程 O(n) 一遍扫描。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>stk = [-1]</code>（哨兵）、<code>ans = 0</code></p>
<p class="code-step">2. 从左到右遍历下标 <code>i</code> 与字符 <code>s[i]</code></p>
<p class="code-step">3. 若 <code>s[i] == '('</code>，将 <code>i</code> 压入栈，等待后续右括号匹配</p>
<p class="code-step">4. 若 <code>s[i] == ')'</code>：先 <code>stk.pop()</code> 弹出待匹配的左括号（或哨兵）</p>
<p class="code-step">5. 弹出后若栈空，说明当前 <code>')'</code> 无法配对，将 <code>i</code> 压栈作为新基准；否则 <code>ans = max(ans, i - stk[-1])</code></p>
<p class="code-step">6. 遍历结束返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def longestValidParentheses(self, s: str) -> int:
        stk = [-1]          # 哨兵：有效段左边界的前一位
        ans = 0
        for i, ch in enumerate(s):
            if ch == '(':
                stk.append(i)
            else:
                stk.pop()   # 匹配掉一个 '(' 或哨兵
                if not stk:
                    stk.append(i)   # 多余的 ')'，作为新分割点
                else:
                    ans = max(ans, i - stk[-1])
        return ans""",
        "code_cpp": """class Solution {
public:
    int longestValidParentheses(string s) {
        vector<int> stk = {-1};  // 哨兵：有效段左边界的前一位
        int ans = 0;
        for (int i = 0; i < (int)s.size(); i++) {
            if (s[i] == '(') {
                stk.push_back(i);
            } else {
                stk.pop_back();  // 匹配掉一个 '(' 或哨兵
                if (stk.empty()) {
                    stk.push_back(i);  // 多余的 ')'，作为新分割点
                } else {
                    ans = max(ans, i - stk.back());
                }
            }
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 栈里存字符而不是下标：无法计算子串长度，也无法在多余 <code>')'</code> 处设置分割点。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记初始哨兵 <code>-1</code>：第一个完整段 <code>"()"</code> 在 <code>i=1</code> 时栈顶为空，长度会变成 <code>1-0=1</code> 而非 2。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 弹出后栈空时忘记压入当前 <code>i</code>：后续有效段会把前面无法配对的 <code>')'</code> 也算进去，导致长度偏大。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空串</div>
    <code>s = "" → 0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：只有左括号</div>
    <code>s = "(()" → 2</code>（末尾多余 <code>'('</code> 留在栈中，不影响已算出的 <code>"()"</code>）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：以右括号开头</div>
        <code>s = ")()())" → 4</code>（开头 <code>')'</code> 触发重置基准，最长段为 <code>"()()"</code>）
</div>""",
    },

    "search-in-rotated-sorted-array": {
        "type": "二分查找",
        "difficulty": "中等",
        "frontend_id": "33",
        "title": "搜索旋转排序数组",
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)",
        "description": """<p>整数数组 <code>nums</code> 按升序排列，数组中的值 <strong>互不相同</strong>。</p>
<p>在传递给函数之前，<code>nums</code> 在预先未知的某个下标 <code>k</code>（<code>0 &lt;= k &lt; nums.length</code>）上进行了 <strong>向左旋转</strong>，使数组变为 <code>[nums[k], nums[k+1], ..., nums[n-1], nums[0], nums[1], ..., nums[k-1]]</code>。</p>
<p>给你 <strong>旋转后</strong> 的数组 <code>nums</code> 和一个整数 <code>target</code>，如果 <code>nums</code> 中存在这个目标值 <code>target</code>，则返回它的下标，否则返回 <code>-1</code>。你必须设计一个时间复杂度为 <code>O(log n)</code> 的算法。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [4,5,6,7,0,1,2], target = 0</div>
    <div class="example-output">输出：4</div>
    <div class="example-explain"><code>target = 0</code> 在下标 4 处。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [4,5,6,7,0,1,2], target = 3</div>
    <div class="example-output">输出：-1</div>
    <div class="example-explain">数组中不存在 3。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [1], target = 0</div>
    <div class="example-output">输出：-1</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>l, r</code></td><td>int</td><td><b>定义</b>：当前待搜索区间的左右边界下标<br><b>维护</b>：若 <code>target</code> 存在，其下标始终在 <code>[l, r]</code> 内<br><b>更新</b>：每轮根据哪一半有序、<code>target</code> 是否落在该有序半段，将 <code>l</code> 或 <code>r</code> 收缩一半</td></tr>
    <tr><td><code>mid</code></td><td>int</td><td><b>定义</b>：当前区间中点下标 <code>(l + r) // 2</code><br><b>维护</b>：将区间切成左段 <code>[l, mid]</code> 与右段 <code>[mid+1, r]</code>，其中<strong>至少有一段仍是升序</strong><br><b>更新</b>：每轮二分重新计算；若 <code>nums[mid] == target</code> 直接返回</td></tr>
    <tr><td><code>有序半段判定</code></td><td>bool</td><td><b>定义</b>：用 <code>nums[l] &lt;= nums[mid]</code> 判断左半是否升序，否则右半 <code>[mid+1, r]</code> 升序<br><b>维护</b>：旋转数组任意时刻都只有「断点」一侧无序，另一侧保持原升序<br><b>更新</b>：在有序半段上用普通二分条件 <code>nums[l] &lt;= target &lt; nums[mid]</code> 或 <code>nums[mid] &lt; target &lt;= nums[r]</code> 决定往哪边缩</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：从左到右线性扫描找 <code>target</code>，O(n)——能过但题目明确要求 O(log n)。</p>
<p class="thinking-step">2. 重复在哪里？原数组整体升序，旋转后只是「在某个点切开再拼接」；任意取 <code>mid</code>，左半 <code>[l,mid]</code> 与右半 <code>[mid+1,r]</code> 里<strong>至少有一段仍是严格升序</strong>（另一段可能跨过旋转断点）。</p>
<p class="thinking-step">3. 关键转化：先判断哪一半有序——若 <code>nums[l] &lt;= nums[mid]</code>，左半升序；否则右半升序。再在有序半段上做普通二分：看 <code>target</code> 是否落在这段数值范围内，是则缩到该半段，否则去另一半。</p>
<p class="thinking-step">4. 例 <code>[4,5,6,7,0,1,2], target=0</code>：首轮 <code>mid=3, nums[mid]=7</code>，左半 <code>[4,7]</code> 升序且 0 不在其中，故去右半；次轮右半 <code>[0,1,2]</code> 升序且 0 在内，最终命中下标 4。</p>
<p class="thinking-step">5. 每轮排除一半元素，整体 O(log n)；元素互不相同保证了有序半段的边界判断不会出现 <code>==</code> 歧义。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>l = 0</code>、<code>r = len(nums) - 1</code></p>
<p class="code-step">2. 当 <code>l &lt;= r</code>：取 <code>mid = (l + r) // 2</code>，若 <code>nums[mid] == target</code> 返回 <code>mid</code></p>
<p class="code-step">3. 若 <code>nums[l] &lt;= nums[mid]</code>（左半升序）：若 <code>nums[l] &lt;= target &lt; nums[mid]</code> 则 <code>r = mid - 1</code>，否则 <code>l = mid + 1</code></p>
<p class="code-step">4. 否则（右半升序）：若 <code>nums[mid] &lt; target &lt;= nums[r]</code> 则 <code>l = mid + 1</code>，否则 <code>r = mid - 1</code></p>
<p class="code-step">5. 循环结束返回 <code>-1</code></p>""",
        "code_python": """class Solution:
    def search(self, nums: list[int], target: int) -> int:
        l, r = 0, len(nums) - 1
        while l <= r:
            mid = (l + r) // 2
            if nums[mid] == target:
                return mid
            if nums[l] <= nums[mid]:          # 左半 [l, mid] 升序
                if nums[l] <= target < nums[mid]:
                    r = mid - 1
                else:
                    l = mid + 1
            else:                             # 右半 [mid+1, r] 升序
                if nums[mid] < target <= nums[r]:
                    l = mid + 1
                else:
                    r = mid - 1
        return -1""",
        "code_cpp": """class Solution {
public:
    int search(vector<int>& nums, int target) {
        int l = 0, r = (int)nums.size() - 1;
        while (l <= r) {
            int mid = l + (r - l) / 2;
            if (nums[mid] == target) return mid;
            if (nums[l] <= nums[mid]) {      // 左半 [l, mid] 升序
                if (nums[l] <= target && target < nums[mid])
                    r = mid - 1;
                else
                    l = mid + 1;
            } else {                         // 右半 [mid+1, r] 升序
                if (nums[mid] < target && target <= nums[r])
                    l = mid + 1;
                else
                    r = mid - 1;
            }
        }
        return -1;
    }
};
// 时间 O(log n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 左半有序时用 <code>nums[l] &lt;= target &lt; nums[mid]</code>（右边界不含 <code>mid</code>），右半有序时用 <code>nums[mid] &lt; target &lt;= nums[r]</code>——与已排除的 <code>nums[mid]</code> 对称，避免死循环。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 误判哪一半有序：必须比较 <code>nums[l]</code> 与 <code>nums[mid]</code>，不能只看 <code>nums[mid]</code> 与 <code>nums[r]</code> 的大小关系。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记 <code>nums[mid] == target</code> 的提前返回：虽然范围判断有时也能收敛到 <code>mid</code>，但显式判断更清晰且避免边界遗漏。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单元素且命中</div>
    <code>nums = [1], target = 1 → 0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单元素未命中</div>
    <code>nums = [1], target = 0 → -1</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：未旋转（k=0）</div>
    <code>nums = [1,3,5], target = 3 → 1</code>（退化为普通二分，左半始终升序）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：目标在旋转断点附近</div>
    <code>nums = [4,5,6,7,0,1,2], target = 0 → 4</code>（首轮排除左半升序段，次轮在右半升序段命中）
</div>""",
    },

    "find-first-and-last-position-of-element-in-sorted-array": {
        "type": "二分查找",
        "difficulty": "中等",
        "frontend_id": "34",
        "title": "在排序数组中查找元素的第一个和最后一个位置",
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个按照非递减顺序排列的整数数组 <code>nums</code>，和一个目标值 <code>target</code>。请你找出给定目标值在数组中的开始位置和结束位置。</p>
<p>如果数组中不存在目标值 <code>target</code>，返回 <code>[-1, -1]</code>。</p>
<p>你必须设计并实现时间复杂度为 <code>O(log n)</code> 的算法解决此问题。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [5,7,7,8,8,10], target = 8</div>
    <div class="example-output">输出：[3,4]</div>
    <div class="example-explain"><code>8</code> 首次出现在下标 3，末次出现在下标 4。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [5,7,7,8,8,10], target = 6</div>
    <div class="example-output">输出：[-1,-1]</div>
    <div class="example-explain">数组中不存在 6。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [], target = 0</div>
    <div class="example-output">输出：[-1,-1]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>l, r</code></td><td>int</td><td><b>定义</b>：当前待搜索区间的左右边界下标<br><b>维护</b>：若 <code>target</code> 存在，其「左边界」或「右边界」始终在 <code>[l, r]</code> 内<br><b>更新</b>：每轮二分根据 <code>nums[mid]</code> 与 <code>target</code> 的关系，将区间收缩一半；命中时按找左/右边界方向继续缩</td></tr>
    <tr><td><code>mid</code></td><td>int</td><td><b>定义</b>：当前区间中点下标 <code>(l + r) // 2</code><br><b>维护</b>：将区间切成左段 <code>[l, mid]</code> 与右段 <code>[mid+1, r]</code><br><b>更新</b>：每轮二分重新计算；若 <code>nums[mid] == target</code> 则记录为候选边界并继续向目标方向搜索</td></tr>
    <tr><td><code>bound</code></td><td>int</td><td><b>定义</b>：当前已找到的候选边界下标，初始为 <code>-1</code><br><b>维护</b>：找左边界时记录最小的等于 <code>target</code> 的下标；找右边界时记录最大的等于 <code>target</code> 的下标<br><b>更新</b>：每当 <code>nums[mid] == target</code> 时更新 <code>bound = mid</code>，并分别令 <code>r = mid - 1</code>（向左找）或 <code>l = mid + 1</code>（向右找）</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：从左到右扫描，遇到 <code>target</code> 记录首次和末次下标，O(n)——能过但题目要求 O(log n)。</p>
<p class="thinking-step">2. 重复在哪里？数组非递减，<code>target</code> 若存在必是一段<strong>连续相等区间</strong>；普通二分只找「任意一个」命中点，无法直接得到首尾。</p>
<p class="thinking-step">3. 关键转化：把问题拆成两次二分——第一次找<strong>左边界</strong>（第一个等于 <code>target</code> 的位置）：命中时仍向左缩 <code>r = mid - 1</code> 并暂存 <code>mid</code>；第二次找<strong>右边界</strong>：命中时向右缩 <code>l = mid + 1</code> 并暂存 <code>mid</code>。</p>
<p class="thinking-step">4. 例 <code>[5,7,7,8,8,10], target=8</code>：找左边界时 <code>mid=2→7</code> 缩右，<code>mid=4→8</code> 记录 4 再缩左得 3；找右边界时从 3 出发最终记录 4。</p>
<p class="thinking-step">5. 两次二分各 O(log n)，总 O(log n)；若左边界为 <code>-1</code> 说明不存在，直接返回 <code>[-1,-1]</code>。</p>""",
        "code_steps": """<p class="code-step">1. 定义辅助函数 <code>find_bound(is_first)</code>：<code>l=0, r=len(nums)-1, bound=-1</code></p>
<p class="code-step">2. 当 <code>l &lt;= r</code>：取 <code>mid</code>；若 <code>nums[mid] == target</code>，令 <code>bound = mid</code>，<code>is_first</code> 则 <code>r = mid - 1</code> 否则 <code>l = mid + 1</code></p>
<p class="code-step">3. 若 <code>nums[mid] &lt; target</code> 则 <code>l = mid + 1</code>，否则 <code>r = mid - 1</code></p>
<p class="code-step">4. 返回 <code>bound</code>；主函数先求左边界 <code>first</code>，若为 <code>-1</code> 返回 <code>[-1,-1]</code></p>
<p class="code-step">5. 再求右边界 <code>last</code>，返回 <code>[first, last]</code></p>""",
        "code_python": """class Solution:
    def searchRange(self, nums: list[int], target: int) -> list[int]:
        def find_bound(is_first: bool) -> int:
            l, r = 0, len(nums) - 1
            bound = -1
            while l <= r:
                mid = (l + r) // 2
                if nums[mid] == target:
                    bound = mid
                    if is_first:
                        r = mid - 1      # 继续向左找更小的左边界
                    else:
                        l = mid + 1      # 继续向右找更大的右边界
                elif nums[mid] < target:
                    l = mid + 1
                else:
                    r = mid - 1
            return bound

        first = find_bound(True)
        if first == -1:
            return [-1, -1]
        last = find_bound(False)
        return [first, last]""",
        "code_cpp": """class Solution {
public:
    vector<int> searchRange(vector<int>& nums, int target) {
        auto findBound = [&](bool isFirst) {
            int l = 0, r = (int)nums.size() - 1, bound = -1;
            while (l <= r) {
                int mid = l + (r - l) / 2;
                if (nums[mid] == target) {
                    bound = mid;
                    if (isFirst)
                        r = mid - 1;     // 向左找左边界
                    else
                        l = mid + 1;     // 向右找右边界
                } else if (nums[mid] < target)
                    l = mid + 1;
                else
                    r = mid - 1;
            }
            return bound;
        };

        int first = findBound(true);
        if (first == -1) return {-1, -1};
        int last = findBound(false);
        return {first, last};
    }
};
// 时间 O(log n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 找左边界时命中后必须 <code>r = mid - 1</code>（不是 <code>l = mid + 1</code>），找右边界时命中后必须 <code>l = mid + 1</code>——方向搞反会得到错误边界。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 命中时不能直接 <code>return mid</code>：数组中可能有多个 <code>target</code>，需要继续向目标方向搜索才能拿到真正的首尾。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空数组 <code>nums = []</code> 时 <code>r = -1</code>，循环不进入、<code>bound</code> 保持 <code>-1</code>，应直接返回 <code>[-1,-1]</code> 而非越界访问。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：空数组</div>
    <code>nums = [], target = 0 → [-1,-1]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：目标不存在</div>
    <code>nums = [5,7,7,8,8,10], target = 6 → [-1,-1]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：全数组均为 target</div>
    <code>nums = [2,2,2,2], target = 2 → [0,3]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：仅一个 target</div>
    <code>nums = [1,2,3], target = 2 → [1,1]</code>（左边界与右边界相同）
</div>""",
    },

    "search-insert-position": {
        "type": "二分查找",
        "difficulty": "简单",
        "frontend_id": "35",
        "title": "搜索插入位置",
        "time_complexity": "O(log n)",
        "space_complexity": "O(1)",
        "description": """<p>给定一个排序数组和一个目标值，在数组中找到目标值，并返回其索引。如果目标值不存在于数组中，返回它将会被按顺序插入的位置。</p>
<p>请必须使用时间复杂度为 <code>O(log n)</code> 的算法。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,3,5,6], target = 5</div>
    <div class="example-output">输出：2</div>
    <div class="example-explain"><code>5</code> 已存在于下标 2。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [1,3,5,6], target = 2</div>
    <div class="example-output">输出：1</div>
    <div class="example-explain"><code>2</code> 不存在，应插入到下标 1（在 1 与 3 之间）。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [1,3,5,6], target = 7</div>
    <div class="example-output">输出：4</div>
    <div class="example-explain"><code>7</code> 大于所有元素，应插入到末尾下标 4。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>l, r</code></td><td>int</td><td><b>定义</b>：当前待搜索区间的左右边界下标<br><b>维护</b>：答案下标（命中位置或插入位置）始终在 <code>[l, r+1]</code> 对应的搜索范围内<br><b>更新</b>：每轮根据 <code>nums[mid]</code> 与 <code>target</code> 的大小关系，将区间收缩一半</td></tr>
    <tr><td><code>mid</code></td><td>int</td><td><b>定义</b>：当前区间中点下标 <code>(l + r) // 2</code><br><b>维护</b>：将区间切成左段 <code>[l, mid]</code> 与右段 <code>[mid+1, r]</code><br><b>更新</b>：每轮二分重新计算；若 <code>nums[mid] == target</code> 直接返回 <code>mid</code></td></tr>
    <tr><td><code>插入位置 l</code></td><td>int</td><td><b>定义</b>：循环结束后 <code>l</code> 指向「第一个 <code>&gt;= target</code> 的元素下标」，即 lower bound<br><b>维护</b>：数组升序且无重复，<code>l</code> 左侧元素均 <code>&lt; target</code>，右侧（含 <code>l</code>）均 <code>&gt;= target</code><br><b>更新</b>：当 <code>nums[mid] &lt; target</code> 时令 <code>l = mid + 1</code>，否则令 <code>r = mid - 1</code>；未命中时返回 <code>l</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：从左到右扫描，遇到 <code>target</code> 就返回下标，否则找到第一个比 <code>target</code> 大的位置——O(n)，但题目要求 O(log n)。</p>
<p class="thinking-step">2. 重复在哪里？数组<strong>升序且无重复</strong>，任意时刻「答案」要么是 <code>target</code> 的下标，要么是第一个 <code>&gt;= target</code> 的位置——这和普通二分查找的「排除一半」结构完全一致。</p>
<p class="thinking-step">3. 关键转化：用标准二分维护 <code>[l, r]</code>；<code>nums[mid] == target</code> 直接返回；<code>nums[mid] &lt; target</code> 则答案在右半 <code>l = mid + 1</code>，否则在左半 <code>r = mid - 1</code>。循环结束时 <code>l</code> 就是插入位置（lower bound）。</p>
<p class="thinking-step">4. 例 <code>[1,3,5,6], target=2</code>：首轮 <code>mid=1, nums[mid]=3 &gt; 2</code> 缩左；次轮 <code>mid=0, nums[mid]=1 &lt; 2</code> 令 <code>l=1</code>；循环结束返回 <code>l=1</code>。</p>
<p class="thinking-step">5. 每轮排除一半，O(log n)；也可理解为在升序数组上求 <code>lower_bound(target)</code>，命中与未命中统一由 <code>l</code> 表达。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>l = 0</code>、<code>r = len(nums) - 1</code></p>
<p class="code-step">2. 当 <code>l &lt;= r</code>：取 <code>mid = (l + r) // 2</code>，若 <code>nums[mid] == target</code> 返回 <code>mid</code></p>
<p class="code-step">3. 若 <code>nums[mid] &lt; target</code>，则 <code>l = mid + 1</code>（答案在右半）</p>
<p class="code-step">4. 否则 <code>r = mid - 1</code>（答案在左半或就是 <code>mid</code> 左侧的插入位）</p>
<p class="code-step">5. 循环结束返回 <code>l</code>（第一个 <code>&gt;= target</code> 的下标，即插入位置）</p>""",
        "code_python": """class Solution:
    def searchInsert(self, nums: list[int], target: int) -> int:
        l, r = 0, len(nums) - 1
        while l <= r:
            mid = (l + r) // 2
            if nums[mid] == target:
                return mid
            if nums[mid] < target:
                l = mid + 1          # target 在右半
            else:
                r = mid - 1          # target 在左半或应插在此处
        return l                       # lower bound：第一个 >= target 的下标""",
        "code_cpp": """class Solution {
public:
    int searchInsert(vector<int>& nums, int target) {
        int l = 0, r = (int)nums.size() - 1;
        while (l <= r) {
            int mid = l + (r - l) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target)
                l = mid + 1;         // target 在右半
            else
                r = mid - 1;         // target 在左半或应插在此处
        }
        return l;                    // lower bound
    }
};
// 时间 O(log n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 未命中时必须返回 <code>l</code> 而不是 <code>r</code>：循环结束时 <code>l</code> 是第一个 <code>&gt;= target</code> 的位置，<code>r</code> 会落在其左侧。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>target</code> 大于所有元素时，<code>l</code> 会增至 <code>len(nums)</code>（如示例 3 返回 4），不要误以为越界——这正是「插入末尾」的正确答案。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 与 #34 找左右边界不同，本题元素无重复，命中时可直接 <code>return mid</code>，无需继续向两侧搜索。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：目标命中</div>
    <code>nums = [1,3,5,6], target = 5 → 2</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：插入中间</div>
    <code>nums = [1,3,5,6], target = 2 → 1</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：插入末尾</div>
    <code>nums = [1,3,5,6], target = 7 → 4</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：插入开头</div>
    <code>nums = [1,3,5,6], target = 0 → 0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：单元素数组</div>
    <code>nums = [1], target = 0 → 0</code>；<code>nums = [1], target = 2 → 1</code>
</div>""",
    },

    "valid-sudoku": {
        "type": "哈希表",
        "difficulty": "中等",
        "frontend_id": "36",
        "title": "有效的数独",
        "time_complexity": "O(1)",
        "space_complexity": "O(1)",
        "description": """<p>请你判断一个 <code>9×9</code> 的数独是否有效。只需要<strong>根据以下规则</strong>，验证已经填入的数字是否有效即可。</p>
<ol>
<li>数字 <code>1-9</code> 在每一行只能出现一次。</li>
<li>数字 <code>1-9</code> 在每一列只能出现一次。</li>
<li>数字 <code>1-9</code> 在每一个以粗实线分隔的 <code>3×3</code> 宫内只能出现一次。</li>
</ol>
<p><strong>注意：</strong>一个有效的数独（部分已被填充）不一定是可解的；只需验证已填数字是否违反规则；空白格用 <code>'.'</code> 表示。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：board =
[["5","3",".",".","7",".",".",".","."]
,["6",".",".","1","9","5",".",".","."]
,[".","9","8",".",".",".",".","6","."]
,["8",".",".",".","6",".",".",".","3"]
,["4",".",".","8",".","3",".",".","1"]
,["7",".",".",".","2",".",".",".","6"]
,[".","6",".",".",".",".","2","8","."]
,[".",".",".","4","1","9",".",".","5"]
,[".",".",".",".","8",".",".","7","9"]]</div>
    <div class="example-output">输出：true</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：board =
[["8","3",".",".","7",".",".",".","."]
,["6",".",".","1","9","5",".",".","."]
,[".","9","8",".",".",".",".","6","."]
,["8",".",".",".","6",".",".",".","3"]
,["4",".",".","8",".","3",".",".","1"]
,["7",".",".",".","2",".",".",".","6"]
,[".","6",".",".",".",".","2","8","."]
,[".",".",".","4","1","9",".",".","5"]
,[".",".",".",".","8",".",".","7","9"]]</div>
    <div class="example-output">输出：false</div>
    <div class="example-explain">左上角 <code>3×3</code> 宫内有两个 <code>8</code>，违反宫格规则。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>rows[i]</code></td><td>set&lt;char&gt; × 9</td><td><b>定义</b>：第 <code>i</code> 行已出现过的数字集合<br><b>维护</b>：扫描到 <code>(i,j)</code> 时，<code>rows[i]</code> 恰好包含该行 <code>j</code> 左侧及当前格的所有非空数字<br><b>更新</b>：遇到数字 <code>c</code> 时，若 <code>c in rows[i]</code> 则非法，否则 <code>rows[i].add(c)</code></td></tr>
    <tr><td><code>cols[j]</code></td><td>set&lt;char&gt; × 9</td><td><b>定义</b>：第 <code>j</code> 列已出现过的数字集合<br><b>维护</b>：与行对称，保证列内 <code>1-9</code> 不重复<br><b>更新</b>：同上，重复则返回 <code>false</code>，否则加入集合</td></tr>
    <tr><td><code>boxes[b]</code></td><td>set&lt;char&gt; × 9</td><td><b>定义</b>：第 <code>b</code> 个 <code>3×3</code> 宫格已出现过的数字集合，<code>b = (i//3)*3 + j//3</code><br><b>维护</b>：每个宫格独立维护，与行、列约束并行检查<br><b>更新</b>：若 <code>c in boxes[b]</code> 则非法，否则 <code>boxes[b].add(c)</code></td></tr>
    <tr><td><code>c = board[i][j]</code></td><td>char</td><td><b>定义</b>：当前格字符，<code>'.'</code> 表示空白<br><b>维护</b>：仅对 <code>'1'..'9'</code> 执行去重检查，空白格直接跳过<br><b>更新</b>：双重循环逐格推进，每遇到一个数字同时查行、列、宫三套集合</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：对每个已填数字，分别检查它所在行、列、<code>3×3</code> 宫有没有重复——每格要扫最多 9 个邻居，整体约 O(81×9)，虽能过但重复劳动多。</p>
<p class="thinking-step">2. 重复在哪里？每往右/往下扫一格，其实只是在问：「这个数字在我<strong>已经看过的</strong>同行/同列/同宫里出现过吗？」——本质是<strong>集合查重</strong>，不必每次重新遍历整行整列。</p>
<p class="thinking-step">3. 关键转化：开 9 个行集合、9 个列集合、9 个宫集合；扫到 <code>(i,j)</code> 的数字 <code>c</code> 时，算宫号 <code>b=(i//3)*3+j//3</code>，若 <code>c</code> 已在 <code>rows[i]/cols[j]/boxes[b]</code> 任一集合中则立即 <code>false</code>，否则三处都加入 <code>c</code>。</p>
<p class="thinking-step">4. 例 2 左上角宫：先记入 <code>8,3</code>，再扫到第二个 <code>8</code> 时 <code>boxes[0]</code> 已有 <code>8</code>，直接判无效——不必解完整数独。</p>
<p class="thinking-step">5. 棋盘固定 <code>9×9</code>，最多 81 格、每格 O(1) 查集合，总复杂度 O(1)；空间也是 27 个小集合的常数级。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>rows, cols, boxes</code> 为 9 个空集合</p>
<p class="code-step">2. 双重循环遍历每个格子 <code>(i, j)</code></p>
<p class="code-step">3. 若 <code>board[i][j] == '.'</code> 跳过；否则令 <code>c = board[i][j]</code>，<code>b = (i//3)*3 + j//3</code></p>
<p class="code-step">4. 若 <code>c</code> 已在 <code>rows[i]</code>、<code>cols[j]</code> 或 <code>boxes[b]</code> 中，返回 <code>false</code></p>
<p class="code-step">5. 否则将 <code>c</code> 同时加入三个集合；全部扫完返回 <code>true</code></p>""",
        "code_python": """class Solution:
    def isValidSudoku(self, board: list[list[str]]) -> bool:
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]
        for i in range(9):
            for j in range(9):
                c = board[i][j]
                if c == '.':
                    continue
                b = (i // 3) * 3 + j // 3
                if c in rows[i] or c in cols[j] or c in boxes[b]:
                    return False
                rows[i].add(c)
                cols[j].add(c)
                boxes[b].add(c)
        return True""",
        "code_cpp": """class Solution {
public:
    bool isValidSudoku(vector<vector<char>>& board) {
        vector<unordered_set<char>> rows(9), cols(9), boxes(9);
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                char c = board[i][j];
                if (c == '.') continue;
                int b = (i / 3) * 3 + j / 3;
                if (rows[i].count(c) || cols[j].count(c) || boxes[b].count(c))
                    return false;
                rows[i].insert(c);
                cols[j].insert(c);
                boxes[b].insert(c);
            }
        }
        return true;
    }
};
// 时间 O(1)，空间 O(1)（棋盘规模固定）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 宫格编号公式写错：应是 <code>(i//3)*3 + j//3</code>，不是 <code>i//3 + j//3</code> 或 <code>(i%3)*3 + j%3</code> 的误用。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 本题只<strong>验证合法性</strong>，不要求可解；看到矛盾直接 <code>false</code>，不要尝试回溯填数。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 字符类型是 <code>'1'..'9'</code> 和 <code>'.'</code>，不要当成 int；空白格必须跳过，否则会把 <code>'.'</code> 当数字处理。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：全空白盘</div>
    <code>board 全是 '.' → true</code>（无冲突可判）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：行内重复</div>
    <code>同一行两个 '5' → false</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：宫内重复（示例 2）</div>
    <code>左上角 3×3 宫两个 '8' → false</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：列内重复</div>
    <code>同一列两个 '7' → false</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：合法但不可解</div>
    <code>已填数字互不冲突即可返回 true</code>，不要求能填满全盘
</div>""",
    },

    "sudoku-solver": {
        "type": "回溯",
        "difficulty": "困难",
        "frontend_id": "37",
        "title": "解数独",
        "time_complexity": "O(9^m)",
        "space_complexity": "O(m)（递归栈，m 为空格数）",
        "description": """<p>编写一个程序，通过填充空格来解决数独问题。</p>
<p>数独的解法需<strong>遵循如下规则</strong>：</p>
<ol>
<li>数字 <code>1-9</code> 在每一行只能出现一次。</li>
<li>数字 <code>1-9</code> 在每一列只能出现一次。</li>
<li>数字 <code>1-9</code> 在每一个以粗实线分隔的 <code>3×3</code> 宫内只能出现一次。</li>
</ol>
<p>数独部分空格内已填入了数字，空白格用 <code>'.'</code> 表示。题目数据<strong>保证</strong>输入数独仅有一个解。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：board =
[["5","3",".",".","7",".",".",".","."]
,["6",".",".","1","9","5",".",".","."]
,[".","9","8",".",".",".",".","6","."]
,["8",".",".",".","6",".",".",".","3"]
,["4",".",".","8",".","3",".",".","1"]
,["7",".",".",".","2",".",".",".","6"]
,[".","6",".",".",".",".","2","8","."]
,[".",".",".","4","1","9",".",".","5"]
,[".",".",".",".","8",".",".","7","9"]]</div>
    <div class="example-output">输出：
[["5","3","4","6","7","8","9","1","2"]
,["6","7","2","1","9","5","3","4","8"]
,["1","9","8","3","4","2","5","6","7"]
,["8","5","9","7","6","1","4","2","3"]
,["4","2","6","8","5","3","7","9","1"]
,["7","1","3","9","2","4","8","5","6"]
,["9","6","1","5","3","7","2","8","4"]
,["2","8","7","4","1","9","6","3","5"]
,["3","4","5","2","8","6","1","7","9"]]</div>
    <div class="example-explain">按行、列、宫三条规则填满所有 <code>'.'</code>，得到唯一解。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>rows[i]</code></td><td>set&lt;char&gt; × 9</td><td><b>定义</b>：第 <code>i</code> 行已占用的数字集合<br><b>维护</b>：回溯过程中，<code>rows[i]</code> 始终等于当前盘上第 <code>i</code> 行所有非空格数字<br><b>更新</b>：在 <code>(r,c)</code> 填入 <code>d</code> 时 <code>rows[r].add(d)</code>；撤销时 <code>rows[r].remove(d)</code></td></tr>
    <tr><td><code>cols[j]</code></td><td>set&lt;char&gt; × 9</td><td><b>定义</b>：第 <code>j</code> 列已占用的数字集合<br><b>维护</b>：与行对称，保证列内 <code>1-9</code> 不重复<br><b>更新</b>：填数时加入、回溯时移除，与 <code>rows</code> 同步</td></tr>
    <tr><td><code>boxes[b]</code></td><td>set&lt;char&gt; × 9</td><td><b>定义</b>：第 <code>b</code> 个 <code>3×3</code> 宫已占用的数字，<code>b = (r//3)*3 + c//3</code><br><b>维护</b>：与行、列约束并行，任意时刻三套集合互不矛盾<br><b>更新</b>：尝试数字 <code>d</code> 前查 <code>d not in boxes[b]</code>；填入/撤销与行列一致</td></tr>
    <tr><td><code>(r, c)</code></td><td>int, int</td><td><b>定义</b>：当前待填空格坐标，按行优先扫描得到<br><b>维护</b>：每轮递归只处理一个空格，填完递归下一格，失败则换数字或回溯<br><b>更新</b>：<code>find_empty()</code> 返回下一个 <code>'.'</code> 的位置；无空格时回溯成功终止</td></tr>
    <tr><td><code>d</code></td><td>char</td><td><b>定义</b>：当前尝试填入的数字 <code>'1'..'9'</code><br><b>维护</b>：仅当 <code>d</code> 不在 <code>rows[r]/cols[c]/boxes[b]</code> 时才合法<br><b>更新</b>：合法则写入 <code>board[r][c]=d</code> 并递归；子调用失败则撤销并试下一个 <code>d</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：统计空格数 <code>m</code>，对每个空格枚举 <code>1-9</code>，共 <code>9^m</code> 种组合，再逐个检查行、列、宫是否合法——思路对，但无效组合占绝大多数。</p>
<p class="thinking-step">2. 重复在哪里？每填一格，子问题变成「在<strong>当前已填前缀</strong>上继续填下一个空格」；很多分支在填到一半时就会因行/列/宫冲突而注定失败，却还要把后面空格全部试完。</p>
<p class="thinking-step">3. 关键转化：用与 #36 相同的 <code>rows/cols/boxes</code> 三套集合做 O(1) 合法性判断；DFS 找到下一个 <code>'.'</code>，依次尝试 <code>1-9</code>，能放就递归，子树无解立刻撤销换数字——经典回溯剪枝。</p>
<p class="thinking-step">4. 例 1 第一格空格 <code>(0,2)</code>：先试 <code>'1'</code> 会与同行 <code>'3'</code> 冲突被剪枝，最终找到 <code>'4'</code> 合法后深入下一空格；任一路径走不通就回退改选。</p>
<p class="thinking-step">5. 题目保证唯一解，找到第一个完整合法填法即可返回；最坏 <code>O(9^m)</code>，剪枝后远好于全枚举；递归深度 ≤ 空格数 <code>m ≤ 81</code>。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>rows, cols, boxes</code> 三套集合，扫描初始盘把已有数字登记进去</p>
<p class="code-step">2. 定义 <code>find_empty()</code>：按行优先找第一个 <code>board[r][c]=='.'</code>，返回坐标；找不到说明已解完</p>
<p class="code-step">3. 定义 <code>backtrack()</code>：调用 <code>find_empty()</code>，无空格则返回 <code>True</code></p>
<p class="code-step">4. 对当前空格 <code>(r,c)</code>，令 <code>b=(r//3)*3+c//3</code>，依次尝试 <code>d='1'..'9'</code></p>
<p class="code-step">5. 若 <code>d</code> 不在三套集合中：写入 <code>board</code> 并更新集合 → 递归 <code>backtrack()</code> → 成功则返回 <code>True</code>，否则撤销填数和集合</p>
<p class="code-step">6. 九个数都失败则返回 <code>False</code>；从 <code>backtrack()</code> 启动，解直接写回原 <code>board</code></p>""",
        "code_python": """class Solution:
    def solveSudoku(self, board: list[list[str]]) -> None:
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]
        for i in range(9):
            for j in range(9):
                c = board[i][j]
                if c != '.':
                    b = (i // 3) * 3 + j // 3
                    rows[i].add(c)
                    cols[j].add(c)
                    boxes[b].add(c)

        def find_empty() -> tuple[int, int] | None:
            for i in range(9):
                for j in range(9):
                    if board[i][j] == '.':
                        return i, j
            return None

        def backtrack() -> bool:
            pos = find_empty()
            if pos is None:
                return True
            r, c = pos
            b = (r // 3) * 3 + c // 3
            for d in map(str, range(1, 10)):
                if d in rows[r] or d in cols[c] or d in boxes[b]:
                    continue
                board[r][c] = d
                rows[r].add(d)
                cols[c].add(d)
                boxes[b].add(d)
                if backtrack():
                    return True
                board[r][c] = '.'
                rows[r].remove(d)
                cols[c].remove(d)
                boxes[b].remove(d)
            return False

        backtrack()""",
        "code_cpp": """class Solution {
public:
    void solveSudoku(vector<vector<char>>& board) {
        vector<unordered_set<char>> rows(9), cols(9), boxes(9);
        for (int i = 0; i < 9; i++) {
            for (int j = 0; j < 9; j++) {
                char c = board[i][j];
                if (c == '.') continue;
                int b = (i / 3) * 3 + j / 3;
                rows[i].insert(c);
                cols[j].insert(c);
                boxes[b].insert(c);
            }
        }

        function<bool()> backtrack = [&]() -> bool {
            int r = -1, c = -1;
            for (int i = 0; i < 9; i++) {
                for (int j = 0; j < 9; j++) {
                    if (board[i][j] == '.') { r = i; c = j; break; }
                }
                if (r != -1) break;
            }
            if (r == -1) return true;

            int b = (r / 3) * 3 + c / 3;
            for (char d = '1'; d <= '9'; d++) {
                if (rows[r].count(d) || cols[c].count(d) || boxes[b].count(d))
                    continue;
                board[r][c] = d;
                rows[r].insert(d);
                cols[c].insert(d);
                boxes[b].insert(d);
                if (backtrack()) return true;
                board[r][c] = '.';
                rows[r].erase(d);
                cols[c].erase(d);
                boxes[b].erase(d);
            }
            return false;
        };

        backtrack();
    }
};
// 最坏 O(9^m)，m 为空格数；空间 O(m) 递归栈""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 回溯不撤销：填入数字后递归失败，必须把 <code>board[r][c]</code> 还原为 <code>'.'</code> 并从三套集合中 <code>remove</code>，否则污染兄弟分支。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 宫格编号公式写错：应是 <code>(r//3)*3 + c//3</code>，与 #36 有效数独相同。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回值误用：函数签名是 <code>void</code>，解直接写回 <code>board</code>，不要 <code>return board</code>；找到解后立刻返回，不必继续搜索其他可能（题目保证唯一解）。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：接近填满的盘</div>
    <code>仅剩 1-2 个 '.' → 回溯深度极浅，几乎 O(1)</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：空格较多</div>
    <code>初始盘大量 '.' → 依赖剪枝，暴力 9^m 不可接受</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：字符类型</div>
    <code>board 存 '1'..'9' 和 '.' 字符，不是 int</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：唯一解保证</div>
    <code>找到第一个完整合法填法即可停止</code>，无需枚举所有解
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：示例 1 全盘</div>
    <code>按题面输入应得到唯一输出矩阵</code>，修改原 board 而非返回新数组
</div>""",
    },

    "count-and-say": {
        "type": "字符串模拟",
        "difficulty": "中等",
        "frontend_id": "38",
        "title": "外观数列",
        "time_complexity": "O(L)（L 为各轮字符串长度之和，n≤30 时可控）",
        "space_complexity": "O(L)（存放当前轮与下一轮字符串）",
        "description": """<p>「外观数列」是一个数位字符串序列，由递归公式定义：</p>
<ul>
<li><code>countAndSay(1) = "1"</code></li>
<li><code>countAndSay(n)</code> 是 <code>countAndSay(n-1)</code> 的<strong>行程长度编码</strong>（RLE）。</li>
</ul>
<p>行程长度编码将每个<strong>最大连续相同字符组</strong>替换为「组长度 + 该字符」。例如 <code>"3322251"</code> 编码为 <code>"23321511"</code>（<code>"33"→"23"</code>，<code>"222"→"32"</code>，<code>"5"→"15"</code>，<code>"1"→"11"</code>）。</p>
<p>给定整数 <code>n</code>，返回外观数列的第 <code>n</code> 项。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：n = 4</div>
    <div class="example-output">输出："1211"</div>
    <div class="example-explain">
        <code>countAndSay(1) = "1"</code><br>
        <code>countAndSay(2) = "1" 的 RLE = "11"</code><br>
        <code>countAndSay(3) = "11" 的 RLE = "21"</code><br>
        <code>countAndSay(4) = "21" 的 RLE = "1211"</code>
    </div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：n = 1</div>
    <div class="example-output">输出："1"</div>
    <div class="example-explain">基本情况，无需编码。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>cur</code></td><td>str</td><td><b>定义</b>：当前轮的外观数列字符串，初始为 <code>"1"</code><br><b>维护</b>：每完成一轮 RLE 编码后，<code>cur</code> 被替换为新生成的字符串<br><b>更新</b>：外层循环执行 <code>n-1</code> 次后，<code>cur</code> 即为第 <code>n</code> 项答案</td></tr>
    <tr><td><code>nxt</code></td><td>str / StringBuilder</td><td><b>定义</b>：对 <code>cur</code> 做一轮行程长度编码后得到的新串<br><b>维护</b>：每轮编码前清空，扫描 <code>cur</code> 时逐段追加 <code>计数+字符</code><br><b>更新</b>：一轮扫描结束后令 <code>cur = nxt</code>，进入下一轮</td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：在 <code>cur</code> 上的扫描指针，指向当前连续段的起始位置<br><b>维护</b>：每处理完一段相同字符后，跳到该段末尾的下一位<br><b>更新</b>：内层 <code>while i &lt; len(cur)</code> 循环推进；段长由 <code>j</code> 探测得到</td></tr>
    <tr><td><code>j</code></td><td>int</td><td><b>定义</b>：从 <code>i</code> 出发，向右延伸直到字符与 <code>cur[i]</code> 不同<br><b>维护</b>：<code>cnt = j - i</code> 即为当前连续段长度<br><b>更新</b>：将 <code>str(cnt) + cur[i]</code> 追加到 <code>nxt</code> 后，令 <code>i = j</code></td></tr>
  <tr><td><code>cnt</code></td><td>int</td><td><b>定义</b>：以 <code>cur[i]</code> 为首的连续相同字符个数<br><b>维护</b>：由双指针 <code>i, j</code> 一次 O(段长) 统计，每段只算一次<br><b>更新</b>：编码为十进制数字字符串拼在字符前，如 <code>3</code> 个 <code>'2'</code> → <code>"32"</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：按定义递归 <code>countAndSay(n-1)</code> 再对其做 RLE——逻辑对，但每层都重新从头编码，函数调用栈深 <code>n</code>，且中间串反复构造。</p>
<p class="thinking-step">2. 重复在哪里？无论递归还是迭代，核心子问题都是「给定字符串 <code>s</code>，输出它的行程长度编码」；第 <code>k</code> 项只依赖第 <code>k-1</code> 项，与更早项无关。</p>
<p class="thinking-step">3. 关键转化：迭代维护 <code>cur</code>，从 <code>"1"</code> 出发做 <code>n-1</code> 轮编码；每轮用双指针扫描 <code>cur</code>，数清连续相同字符后追加 <code>计数+字符</code> 到 <code>nxt</code>。</p>
<p class="thinking-step">4. 手推 <code>n=4</code>：<code>"1"→"11"→"21"→"1211"</code>。第三轮读 <code>"21"</code>：先 <code>1</code> 个 <code>'2'</code> 得 <code>"12"</code>，再 <code>1</code> 个 <code>'1'</code> 得 <code>"11"</code>，合并 <code>"1211"</code>。</p>
<p class="thinking-step">5. <code>n=1</code> 直接返回 <code>"1"</code>，循环 0 次；<code>n≤30</code> 时串长可控，双指针每轮总扫描长度等于当前串长，整体可行。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>n == 1</code>，直接返回 <code>"1"</code></p>
<p class="code-step">2. 令 <code>cur = "1"</code>，准备执行 <code>n-1</code> 轮编码</p>
<p class="code-step">3. 每轮初始化空串 <code>nxt</code>，双指针 <code>i = 0</code> 扫描 <code>cur</code></p>
<p class="code-step">4. 固定 <code>ch = cur[i]</code>，令 <code>j = i</code> 向右扩直到 <code>cur[j] != ch</code>，<code>cnt = j - i</code></p>
<p class="code-step">5. 将 <code>str(cnt) + ch</code> 追加到 <code>nxt</code>，<code>i = j</code> 处理下一段</p>
<p class="code-step">6. 一轮结束 <code>cur = nxt</code>；全部轮次完成后返回 <code>cur</code></p>""",
        "code_python": """class Solution:
    def countAndSay(self, n: int) -> str:
        if n == 1:
            return "1"
        cur = "1"
        for _ in range(n - 1):
            nxt = []
            i = 0
            while i < len(cur):
                ch = cur[i]
                j = i
                while j < len(cur) and cur[j] == ch:
                    j += 1
                nxt.append(str(j - i))
                nxt.append(ch)
                i = j
            cur = "".join(nxt)
        return cur""",
        "code_cpp": """class Solution {
public:
    string countAndSay(int n) {
        if (n == 1) return "1";
        string cur = "1";
        for (int round = 1; round < n; ++round) {
            string nxt;
            for (int i = 0; i < (int)cur.size(); ) {
                char ch = cur[i];
                int j = i;
                while (j < (int)cur.size() && cur[j] == ch) ++j;
                nxt += to_string(j - i);
                nxt += ch;
                i = j;
            }
            cur = move(nxt);
        }
        return cur;
    }
};
// 时间 O(L)，空间 O(L)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 计数与字符拼接顺序反了：应先写<strong>个数</strong>再写<strong>字符</strong>，<code>3</code> 个 <code>'2'</code> 是 <code>"32"</code> 而非 <code>"23"</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 循环次数 off-by-one：只需编码 <code>n-1</code> 次；多跑一轮会把答案再 RLE 一次，<code>n=4</code> 会错成 <code>"111221"</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 内层扫描未正确跳段：每处理完一段必须令 <code>i = j</code>，否则会在同一字符上死循环或重复计数。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：n = 1</div>
    <code>直接返回 "1"，不进入编码循环</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：n = 4</div>
    <code>经典手推链 "1"→"11"→"21"→"1211"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：含多段相同模式</div>
    <code>"111221" 编码为 "312211"（3个1 + 2个2 + 1个1）</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：单字符段</div>
    <code>"21" 中两段长度均为 1 → "1211"</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：较大 n</div>
    <code>n = 30 时串长可达数千，仍须用 O(当前长度) 扫描，避免暴力递归重复计算</code>
</div>""",
    },

    "combination-sum": {
        "type": "回溯",
        "difficulty": "中等",
        "frontend_id": "39",
        "title": "组合总和",
        "time_complexity": "O(N^(T/min))（N 为候选数，T 为 target，min 为最小候选值；剪枝后远好于全枚举）",
        "space_complexity": "O(T/min)（递归栈深度，不计输出）",
        "description": """<p>给你一个 <strong>无重复元素</strong> 的整数数组 <code>candidates</code> 和一个目标整数 <code>target</code>，找出 <code>candidates</code> 中可以使数字和为目标数 <code>target</code> 的所有<strong>不同组合</strong>，并以列表形式返回。你可以按<strong>任意顺序</strong> 返回这些组合。</p>
<p><code>candidates</code> 中的<strong>同一个</strong> 数字可以<strong>无限制重复被选取</strong>。如果至少一个数字的被选数量不同，则两种组合是不同的。</p>
<p>对于给定的输入，保证和为 <code>target</code> 的不同组合数少于 <code>150</code> 个。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：candidates = [2,3,6,7], target = 7</div>
    <div class="example-output">输出：[[2,2,3],[7]]</div>
    <div class="example-explain">2 和 3 可以形成一组候选，2 + 2 + 3 = 7。注意 2 可以使用多次。7 也是一个候选，7 = 7。仅有这两种组合。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：candidates = [2,3,5], target = 8</div>
    <div class="example-output">输出：[[2,2,2,2],[2,3,3],[3,5]]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：candidates = [2], target = 1</div>
    <div class="example-output">输出：[]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>path</code></td><td>list&lt;int&gt;</td><td><b>定义</b>：当前正在构造的组合（已选数字序列）<br><b>维护</b>：DFS 每层在末尾追加一个候选数，回溯时 <code>pop</code> 撤销<br><b>更新</b>：尝试 <code>candidates[i]</code> 时 <code>append</code>；该分支探索完毕后 <code>pop</code></td></tr>
    <tr><td><code>remain</code></td><td>int</td><td><b>定义</b>：距离 <code>target</code> 还差多少和<br><b>维护</b>：每选一个数 <code>x</code>，子问题变为 <code>remain - x</code><br><b>更新</b>：<code>remain == 0</code> 时收集答案；<code>remain &lt; 0</code> 时剪枝返回</td></tr>
    <tr><td><code>start</code></td><td>int</td><td><b>定义</b>：本轮可选候选的起始下标（含自身）<br><b>维护</b>：只从 <code>candidates[start..]</code> 中选，保证组合不重复（如不会出现 <code>[3,2,2]</code> 与 <code>[2,2,3]</code>）<br><b>更新</b>：选 <code>candidates[i]</code> 后递归传 <code>i</code>（非 <code>i+1</code>），允许同一数重复使用</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&lt;int&gt;&gt;</td><td><b>定义</b>：所有和为 <code>target</code> 的不同组合<br><b>维护</b>：仅当 <code>remain == 0</code> 时将 <code>path</code> 的副本加入<br><b>更新</b>：每到达合法叶子追加一次；中途不收集半成品</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：从 <code>candidates</code> 中任意选若干个（可重复），枚举所有子序列，检查总和是否等于 <code>target</code>——思路对，但组合爆炸，且 <code>[2,3]</code> 与 <code>[3,2]</code> 会被当成两种答案。</p>
<p class="thinking-step">2. 重复在哪里？每多选一个数，子问题变成「在<strong>剩余目标和</strong>下继续选数」；很多分支在 <code>remain</code> 变负后仍会继续深搜，白白浪费。</p>
<p class="thinking-step">3. 关键转化：用 <code>start</code> 控制「只从当前下标往后选」，既避免 <code>[2,3]</code>/<code>[3,2]</code> 重复，又允许同一数重复用（递归传 <code>i</code> 而非 <code>i+1</code>）；<code>remain == 0</code> 收集，<code>remain &lt; 0</code> 剪枝。</p>
<p class="thinking-step">4. 例 1 <code>candidates=[2,3,6,7], target=7</code>：先试 <code>2</code>（remain=5）再试 <code>2</code>（remain=3）再试 <code>3</code>（remain=0）→ 得到 <code>[2,2,3]</code>；另一路直接选 <code>7</code> → <code>[7]</code>。</p>
<p class="thinking-step">5. 可先对 <code>candidates</code> 排序，遇到 <code>candidates[i] &gt; remain</code> 时后面更大可提前 <code>break</code>；题目保证答案 &lt; 150 组，剪枝后可行。</p>""",
        "code_steps": """<p class="code-step">1. 初始化结果 <code>ans</code>，可选对 <code>candidates</code> 排序以便剪枝</p>
<p class="code-step">2. 定义 DFS <code>backtrack(start, remain, path)</code>：若 <code>remain == 0</code>，将 <code>path[:]</code> 加入 <code>ans</code> 并返回；若 <code>remain &lt; 0</code> 则剪枝返回</p>
<p class="code-step">3. 对 <code>i</code> 从 <code>start</code> 到 <code>len(candidates)-1</code>：若 <code>candidates[i] &gt; remain</code> 可 <code>break</code>（已排序时）</p>
<p class="code-step">4. 将 <code>candidates[i]</code> 追加到 <code>path</code>，递归 <code>backtrack(i, remain - candidates[i], path)</code>（传 <code>i</code> 允许重复选）</p>
<p class="code-step">5. 回溯：从 <code>path</code> 弹出末尾元素，继续尝试下一个 <code>i</code></p>
<p class="code-step">6. 从 <code>backtrack(0, target, [])</code> 启动，返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def combinationSum(self, candidates: list[int], target: int) -> list[list[int]]:
        ans: list[list[int]] = []
        candidates.sort()

        def backtrack(start: int, remain: int, path: list[int]) -> None:
            if remain == 0:
                ans.append(path[:])
                return
            if remain < 0:
                return
            for i in range(start, len(candidates)):
                if candidates[i] > remain:
                    break
                path.append(candidates[i])
                backtrack(i, remain - candidates[i], path)
                path.pop()

        backtrack(0, target, [])
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<int>> combinationSum(vector<int>& candidates, int target) {
        vector<vector<int>> ans;
        vector<int> path;
        sort(candidates.begin(), candidates.end());

        function<void(int, int)> dfs = [&](int start, int remain) {
            if (remain == 0) {
                ans.push_back(path);
                return;
            }
            if (remain < 0) return;
            for (int i = start; i < (int)candidates.size(); i++) {
                if (candidates[i] > remain) break;
                path.push_back(candidates[i]);
                dfs(i, remain - candidates[i]);
                path.pop_back();
            }
        };

        dfs(0, target);
        return ans;
    }
};
// 时间 O(N^(T/min))，空间 O(T/min) 递归栈""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 递归下标传 <code>i+1</code>：本题允许同一数重复使用，必须传 <code>i</code>；传 <code>i+1</code> 会漏解（如 <code>[2,2,3]</code>）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 组合去重失败：若每层从 <code>0</code> 开始选会产生 <code>[2,3]</code> 与 <code>[3,2]</code> 重复，必须用 <code>start</code> 限制只往后选。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 收集答案时未拷贝 <code>path</code>：应 <code>ans.append(path[:])</code> 或 C++ 中在 <code>remain==0</code> 时 push 当前 <code>path</code> 副本，否则后续修改会污染已收集结果。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：无解</div>
    <code>candidates = [2], target = 1 → []</code>（最小候选 2 已大于 target）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单元素凑满</div>
    <code>candidates = [7], target = 7 → [[7]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：同一数多次使用</div>
    <code>candidates = [2,3,5], target = 8 → 含 [2,2,2,2]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：示例 1</div>
    <code>[2,3,6,7], target=7 → [[2,2,3],[7]]</code>，恰好两组
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：候选无序输入</div>
    <code>排序不影响正确性，但有助于 remain 剪枝</code>
</div>""",
    },
    "combination-sum-ii": {
        "type": "回溯",
        "difficulty": "中等",
        "frontend_id": "40",
        "title": "组合总和 II",
        "time_complexity": "O(2^N)（N 为候选数；排序 + 剪枝 + 同层去重后远好于全子集枚举）",
        "space_complexity": "O(N)（递归栈深度，不计输出）",
        "description": """<p>给定一个候选人编号的集合 <code>candidates</code> 和一个目标数 <code>target</code>，找出 <code>candidates</code> 中所有可以使数字和为 <code>target</code> 的组合。</p>
<p><code>candidates</code> 中的每个数字在每个组合中只能使用 <strong>一次</strong>。</p>
<p><strong>注意：</strong>解集不能包含重复的组合。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：candidates = [10,1,2,7,6,1,5], target = 8</div>
    <div class="example-output">输出：[[1,1,6],[1,2,5],[1,7],[2,6]]</div>
    <div class="example-explain">1 和 1 来自两个不同的 1，可以一起使用；1,2,5 与 2,5,1 视为同一组合，只保留一种。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：candidates = [2,5,2,1,2], target = 5</div>
    <div class="example-output">输出：[[1,2,2],[5]]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>path</code></td><td>list&lt;int&gt;</td><td><b>定义</b>：当前正在构造的组合（已选数字序列）<br><b>维护</b>：DFS 每层在末尾追加一个候选数，回溯时 <code>pop</code> 撤销<br><b>更新</b>：尝试 <code>candidates[i]</code> 时 <code>append</code>；该分支探索完毕后 <code>pop</code></td></tr>
    <tr><td><code>remain</code></td><td>int</td><td><b>定义</b>：距离 <code>target</code> 还差多少和<br><b>维护</b>：每选一个数 <code>x</code>，子问题变为 <code>remain - x</code><br><b>更新</b>：<code>remain == 0</code> 时收集答案；<code>remain &lt; 0</code> 时剪枝返回</td></tr>
    <tr><td><code>start</code></td><td>int</td><td><b>定义</b>：本轮可选候选的起始下标（含自身）<br><b>维护</b>：只从 <code>candidates[start..]</code> 中选，保证组合不重复（如不会出现 <code>[1,2,5]</code> 与 <code>[2,5,1]</code>）<br><b>更新</b>：选 <code>candidates[i]</code> 后递归传 <code>i+1</code>（每个数最多用一次）</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&lt;int&gt;&gt;</td><td><b>定义</b>：所有和为 <code>target</code> 的不同组合<br><b>维护</b>：仅当 <code>remain == 0</code> 时将 <code>path</code> 的副本加入<br><b>更新</b>：每到达合法叶子追加一次；中途不收集半成品</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：从 <code>candidates</code> 中任选若干个（每个最多一次），枚举所有子集，检查总和是否等于 <code>target</code>——思路对，但组合爆炸，且输入有重复数字时会产生重复答案（如两个 1 分别选会生成相同组合）。</p>
<p class="thinking-step">2. 重复在哪里？一是排列等价（<code>[1,2,5]</code> 与 <code>[2,5,1]</code>），用 <code>start</code> 只往后选可解决；二是相同数值的候选（如两个 1）在同一层被多次尝试，会生成重复组合。</p>
<p class="thinking-step">3. 关键转化：先对 <code>candidates</code> 排序；每层从 <code>start</code> 往后选，递归传 <code>i+1</code>（不可重复选）；同层去重：若 <code>i &gt; start</code> 且 <code>candidates[i] == candidates[i-1]</code> 则 <code>continue</code>，跳过等价分支。</p>
<p class="thinking-step">4. 例 1 排序后 <code>[1,1,2,5,6,7,10], target=8</code>：第一层选第一个 1（remain=7）→ 再选第二个 1（remain=6）→ 选 6（remain=0）→ <code>[1,1,6]</code>；另一路选 1+2+5 等。</p>
<p class="thinking-step">5. 与 #39 组合总和的区别：本题每个数只能用一次（传 <code>i+1</code>），且必须排序 + 同层去重；<code>remain &lt; 0</code> 或 <code>candidates[i] &gt; remain</code> 时剪枝。</p>""",
        "code_steps": """<p class="code-step">1. 对 <code>candidates</code> 排序，初始化结果 <code>ans</code></p>
<p class="code-step">2. 定义 DFS <code>backtrack(start, remain, path)</code>：若 <code>remain == 0</code>，将 <code>path[:]</code> 加入 <code>ans</code> 并返回；若 <code>remain &lt; 0</code> 则剪枝返回</p>
<p class="code-step">3. 对 <code>i</code> 从 <code>start</code> 到 <code>len(candidates)-1</code>：若 <code>candidates[i] &gt; remain</code> 可 <code>break</code>；若 <code>i &gt; start</code> 且 <code>candidates[i] == candidates[i-1]</code> 则 <code>continue</code>（同层去重）</p>
<p class="code-step">4. 将 <code>candidates[i]</code> 追加到 <code>path</code>，递归 <code>backtrack(i+1, remain - candidates[i], path)</code>（传 <code>i+1</code> 保证每个数最多用一次）</p>
<p class="code-step">5. 回溯：从 <code>path</code> 弹出末尾元素，继续尝试下一个 <code>i</code></p>
<p class="code-step">6. 从 <code>backtrack(0, target, [])</code> 启动，返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def combinationSum2(self, candidates: list[int], target: int) -> list[list[int]]:
        ans: list[list[int]] = []
        candidates.sort()

        def backtrack(start: int, remain: int, path: list[int]) -> None:
            if remain == 0:
                ans.append(path[:])
                return
            if remain < 0:
                return
            for i in range(start, len(candidates)):
                if candidates[i] > remain:
                    break
                if i > start and candidates[i] == candidates[i - 1]:
                    continue
                path.append(candidates[i])
                backtrack(i + 1, remain - candidates[i], path)
                path.pop()

        backtrack(0, target, [])
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<int>> combinationSum2(vector<int>& candidates, int target) {
        vector<vector<int>> ans;
        vector<int> path;
        sort(candidates.begin(), candidates.end());

        function<void(int, int)> dfs = [&](int start, int remain) {
            if (remain == 0) {
                ans.push_back(path);
                return;
            }
            if (remain < 0) return;
            for (int i = start; i < (int)candidates.size(); i++) {
                if (candidates[i] > remain) break;
                if (i > start && candidates[i] == candidates[i - 1]) continue;
                path.push_back(candidates[i]);
                dfs(i + 1, remain - candidates[i]);
                path.pop_back();
            }
        };

        dfs(0, target);
        return ans;
    }
};
// 时间 O(2^N)，空间 O(N) 递归栈""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 递归下标传 <code>i</code> 而非 <code>i+1</code>：本题每个数只能用一次，传 <code>i</code> 会重复选同一位置，产生非法组合。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记同层去重：输入 <code>[1,1,2]</code> 时，若不跳过 <code>candidates[i]==candidates[i-1]</code>（当 <code>i&gt;start</code>），会输出两个 <code>[1,2]</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 去重条件写错：应写 <code>i &gt; start</code> 时跳过，而非 <code>i &gt; 0</code>；后者会误杀跨层合法分支（如两个 1 分属不同层时都需要）。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：无解</div>
    <code>candidates = [3,4], target = 2 → []</code>（最小候选已大于 target）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单元素凑满</div>
    <code>candidates = [5,2,2,1,2], target = 5 → 含 [5]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：重复数字</div>
    <code>candidates = [10,1,2,7,6,1,5], target = 8 → 含 [1,1,6]</code>（两个 1 来自不同位置，合法）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：示例 2</div>
    <code>[2,5,2,1,2], target=5 → [[1,2,2],[5]]</code>，排序去重后恰好两组
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：target 等于某候选</div>
    <code>candidates = [1,1], target = 1 → [[1]]</code>（只选其中一个 1，同层去重保证不重复）
</div>""",
    },
    "first-missing-positive": {
        "type": "数组原地哈希",
        "difficulty": "困难",
        "frontend_id": "41",
        "title": "缺失的第一个正数",
        "time_complexity": "O(N)（每个元素最多被交换到正确位置一次）",
        "space_complexity": "O(1)（只用常数额外变量，原地修改数组）",
        "description": """<p>给你一个未排序的整数数组 <code>nums</code>，请你找出其中没有出现的最小的正整数。</p>
<p>请你实现时间复杂度为 <code>O(n)</code> 并且只使用常数级别额外空间的解决方案。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,2,0]</div>
    <div class="example-output">输出：3</div>
    <div class="example-explain">范围 [1,2] 中的数字都在数组中。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [3,4,-1,1]</div>
    <div class="example-output">输出：2</div>
    <div class="example-explain">1 在数组中，但 2 没有。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [7,8,9,11,12]</div>
    <div class="example-output">输出：1</div>
    <div class="example-explain">最小的正数 1 没有出现。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>n</code></td><td>int</td><td><b>定义</b>：数组长度，答案只可能落在 <code>[1, n+1]</code><br><b>维护</b>：有效正整数 <code>x</code> 若存在，必在 <code>1..n</code> 内（大于 <code>n</code> 的数不可能是最小缺失正数）<br><b>更新</b>：初始化后不变，用于界定「该放哪里」与最终扫描上界</td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：当前正在整理的数组下标<br><b>维护</b>：从左到右扫，保证 <code>nums[0..i-1]</code> 已就位（<code>nums[j]==j+1</code>）<br><b>更新</b>：当前位置元素归位或判定为垃圾后 <code>i++</code></td></tr>
    <tr><td><code>nums[k]</code></td><td>int</td><td><b>定义</b>：下标 <code>k</code> 处的值；语义上应存放整数 <code>k+1</code>（若该数存在于原数组）<br><b>维护</b>：把每个合法值 <code>x∈[1,n]</code> 交换到 <code>nums[x-1]</code>，形成「值 <code>x</code> 住在下标 <code>x-1</code>」的原地哈希表<br><b>更新</b>：通过 <code>swap(nums[i], nums[nums[i]-1])</code> 循环搬运，直到 <code>nums[i]</code> 不在 <code>[1,n]</code> 或已在正确位置</td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：第一个缺失的正整数<br><b>维护</b>：第二遍扫描找最小 <code>i</code> 使 <code>nums[i] != i+1</code>，则 <code>ans = i+1</code><br><b>更新</b>：若 <code>1..n</code> 全在位，<code>ans = n+1</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：用哈希集合记录 <code>nums</code> 里所有正数，再从 <code>1</code> 开始递增找第一个不在集合里的——正确，但需要 <code>O(n)</code> 额外空间，不满足题意。</p>
<p class="thinking-step">2. 重复在哪里？我们其实只关心 <code>1..n</code> 哪些出现了；大于 <code>n</code> 的数和 ≤0 的数都是噪声，可以忽略。</p>
<p class="thinking-step">3. 关键转化：把数组当成长度为 <code>n</code> 的哈希桶——值 <code>x</code>（<code>1≤x≤n</code>）应该放在下标 <code>x-1</code>。对每个位置 <code>i</code>，若 <code>nums[i]</code> 是合法值且还没在正确位置，就与 <code>nums[nums[i]-1]</code> 交换，直到当前位无法继续换。</p>
<p class="thinking-step">4. 例 2 <code>[3,4,-1,1]</code>：<code>i=0</code> 把 3 换到 index 2 → <code>[−1,4,3,1]</code>；<code>i=1</code> 把 4 换到 index 3 → <code>[−1,1,3,4]</code>；<code>i=1</code> 再把 1 换到 index 0 → <code>[1,−1,3,4]</code>。第二遍扫描：<code>nums[1]=−1≠2</code>，答案 2。</p>
<p class="thinking-step">5. 为什么 <code>while</code> 不会死循环？每次交换都让某个合法值到达最终位置，每个下标最多被「填对」一次，总交换次数 <code>O(n)</code>。</p>""",
        "code_steps": """<p class="code-step">1. 令 <code>n = len(nums)</code>，第一遍原地整理：对 <code>i</code> 从 <code>0</code> 到 <code>n-1</code></p>
<p class="code-step">2. 当 <code>1 ≤ nums[i] ≤ n</code> 且 <code>nums[i] ≠ nums[nums[i]-1]</code> 时，交换 <code>nums[i]</code> 与 <code>nums[nums[i]-1]</code>（把 <code>nums[i]</code> 送到它应在的下标）</p>
<p class="code-step">3. 内层 <code>while</code> 结束说明当前位已是垃圾值（≤0 或 &gt;n）或已就位，<code>i++</code> 处理下一位</p>
<p class="code-step">4. 第二遍扫描：找最小 <code>i</code> 使 <code>nums[i] ≠ i+1</code>，返回 <code>i+1</code></p>
<p class="code-step">5. 若 <code>1..n</code> 全部在位，返回 <code>n+1</code></p>""",
        "code_python": """class Solution:
    def firstMissingPositive(self, nums: list[int]) -> int:
        n = len(nums)
        for i in range(n):
            while 1 <= nums[i] <= n and nums[i] != nums[nums[i] - 1]:
                j = nums[i] - 1
                nums[i], nums[j] = nums[j], nums[i]
        for i in range(n):
            if nums[i] != i + 1:
                return i + 1
        return n + 1""",
        "code_cpp": """class Solution {
public:
    int firstMissingPositive(vector<int>& nums) {
        int n = nums.size();
        for (int i = 0; i < n; i++) {
            while (nums[i] >= 1 && nums[i] <= n && nums[i] != nums[nums[i] - 1]) {
                int j = nums[i] - 1;
                swap(nums[i], nums[j]);
            }
        }
        for (int i = 0; i < n; i++) {
            if (nums[i] != i + 1) return i + 1;
        }
        return n + 1;
    }
};
// 时间 O(N)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 用 <code>if</code> 只交换一次：例如 <code>[3,4,-1,1]</code> 在 <code>i=0</code> 换完后当前位仍是 3 的「错值」，必须用 <code>while</code> 持续交换直到无法继续。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记判重 <code>nums[i] != nums[nums[i]-1]</code>：若目标位已是相同值（重复数字），再交换会死循环。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 第二遍扫描条件写错：应比较 <code>nums[i] != i+1</code>，不是 <code>nums[i] != i</code>；下标从 0 开始，期望存放的是 <code>i+1</code>。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：全为负数</div>
    <code>nums = [-1,-2,-3] → 1</code>（没有任何正数，最小缺失正数为 1）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：已连续 1..n</div>
    <code>nums = [1,2,3] → 4</code>（1..n 都在，答案为 n+1）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：含重复与垃圾值</div>
    <code>nums = [3,4,-1,1] → 2</code>（-1 与重复值被留在错误位置，不影响扫描）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：全大于 n</div>
    <code>nums = [7,8,9,11,12] → 1</code>（没有任何 1..n 的有效值）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：单元素</div>
    <code>nums = [1] → 2</code>；<code>nums = [2] → 1</code>
</div>""",
    },
    "multiply-strings": {
        "type": "数学模拟",
        "difficulty": "中等",
        "frontend_id": "43",
        "title": "字符串相乘",
        "time_complexity": "O(m × n)（m、n 为两串长度，每位与每位相乘一次）",
        "space_complexity": "O(m + n)（结果数组长度最多 m+n 位）",
        "description": """<p>给定两个以字符串形式表示的非负整数 <code>num1</code> 和 <code>num2</code>，返回 <code>num1</code> 和 <code>num2</code> 的乘积，它们的乘积也表示为字符串形式。</p>
<p><strong>注意：</strong>不能使用任何内置的 BigInteger 库或直接将输入转换为整数。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：num1 = "2", num2 = "3"</div>
    <div class="example-output">输出："6"</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：num1 = "123", num2 = "456"</div>
    <div class="example-output">输出："56088"</div>
    <div class="example-explain">123 × 456 = 56088，模拟竖式乘法：每位相乘后按位累加进位。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>m, n</code></td><td>int</td><td><b>定义</b>：<code>num1</code>、<code>num2</code> 的长度<br><b>维护</b>：乘积最多 <code>m+n</code> 位，结果数组长度由此确定<br><b>更新</b>：初始化后不变</td></tr>
    <tr><td><code>res</code></td><td>int[]</td><td><b>定义</b>：长度为 <code>m+n</code> 的数位数组，<code>res[k]</code> 表示乘积从右数第 <code>k</code> 位的数字（低位在右）<br><b>维护</b>：模拟竖式乘法，<code>num1[i]×num2[j]</code> 的贡献落在 <code>res[i+j]</code> 与 <code>res[i+j+1]</code><br><b>更新</b>：每对数位相乘后 <code>res[p2] += mul</code>，再向 <code>res[p1]</code> 传递进位</td></tr>
    <tr><td><code>i, j</code></td><td>int</td><td><b>定义</b>：<code>num1</code>、<code>num2</code> 当前参与相乘的字符下标（从右向左）<br><b>维护</b>：双重循环枚举所有数位对，覆盖竖式中每一次「个位×个位、个位×十位…」<br><b>更新</b>：<code>i</code> 从 <code>m-1</code> 到 <code>0</code>，内层 <code>j</code> 从 <code>n-1</code> 到 <code>0</code></td></tr>
    <tr><td><code>mul</code></td><td>int</td><td><b>定义</b>：当前两位数字的乘积 <code>int(num1[i]) × int(num2[j])</code><br><b>维护</b>：范围 <code>0..81</code>，加上已有低位后可能产生进位<br><b>更新</b>：每对 <code>(i,j)</code> 重新计算</td></tr>
    <tr><td><code>p1, p2</code></td><td>int</td><td><b>定义</b>：<code>mul</code> 在 <code>res</code> 中对应的十位、个位下标，<code>p2 = i+j+1</code>、<code>p1 = i+j</code><br><b>维护</b>：下标 <code>i</code> 越靠左（高位）、<code>j</code> 越靠左，乘积贡献越靠高位<br><b>更新</b>：随当前 <code>(i,j)</code> 变化</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：把两个字符串转成 <code>int</code> 再相乘——题面明确禁止，且长度可达 200 位，会溢出。</p>
<p class="thinking-step">2. 重复在哪里？竖式乘法里，每一位都要与另一个数的每一位相乘，再把部分积按位对齐相加。这个「对齐 + 进位」过程可以抽象成数组操作。</p>
<p class="thinking-step">3. 关键观察：<code>num1[i] × num2[j]</code> 的结果（最多两位）应写入结果数组的 <code>res[i+j+1]</code>（个位）和 <code>res[i+j]</code>（十位进位）。开一个长度 <code>m+n</code> 的数组足够存放最终乘积。</p>
<p class="thinking-step">4. 例 <code>"123" × "456"</code>：<code>3×6=18</code> 写入 <code>res[4..5]</code>；<code>3×5=15</code>、<code>2×6=12</code> 等同理累加并进位。全部数位对处理完后，从左到右跳过前导零，拼接成字符串。</p>
<p class="thinking-step">5. 特判：任一串为 <code>"0"</code> 直接返回 <code>"0"</code>；结果全零时也要返回 <code>"0"</code> 而非空串。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>num1 == "0" or num2 == "0"</code>，返回 <code>"0"</code></p>
<p class="code-step">2. 令 <code>m, n = len(num1), len(num2)</code>，初始化 <code>res = [0] * (m + n)</code></p>
<p class="code-step">3. 双重循环：<code>i</code> 从 <code>m-1</code> 到 <code>0</code>，<code>j</code> 从 <code>n-1</code> 到 <code>0</code></p>
<p class="code-step">4. 计算 <code>mul = int(num1[i]) * int(num2[j])</code>，<code>p1 = i+j</code>、<code>p2 = i+j+1</code></p>
<p class="code-step">5. <code>sum = mul + res[p2]</code>，<code>res[p2] = sum % 10</code>，<code>res[p1] += sum // 10</code>（个位落位、进位向高位传递）</p>
<p class="code-step">6. 从左到右跳过前导零，将 <code>res</code> 剩余数位拼接为字符串返回</p>""",
        "code_python": """class Solution:
    def multiply(self, num1: str, num2: str) -> str:
        if num1 == "0" or num2 == "0":
            return "0"
        m, n = len(num1), len(num2)
        res = [0] * (m + n)
        for i in range(m - 1, -1, -1):
            for j in range(n - 1, -1, -1):
                mul = int(num1[i]) * int(num2[j])
                p1, p2 = i + j, i + j + 1
                total = mul + res[p2]
                res[p2] = total % 10
                res[p1] += total // 10
        # 跳过前导零
        start = 0
        while start < len(res) - 1 and res[start] == 0:
            start += 1
        return "".join(str(d) for d in res[start:])""",
        "code_cpp": """class Solution {
public:
    string multiply(string num1, string num2) {
        if (num1 == "0" || num2 == "0") return "0";
        int m = num1.size(), n = num2.size();
        vector<int> res(m + n, 0);
        for (int i = m - 1; i >= 0; i--) {
            for (int j = n - 1; j >= 0; j--) {
                int mul = (num1[i] - '0') * (num2[j] - '0');
                int p1 = i + j, p2 = i + j + 1;
                int total = mul + res[p2];
                res[p2] = total % 10;
                res[p1] += total / 10;
            }
        }
        int start = 0;
        while (start < (int)res.size() - 1 && res[start] == 0) start++;
        string ans;
        for (int k = start; k < (int)res.size(); k++)
            ans += char('0' + res[k]);
        return ans;
    }
};
// 时间 O(m×n)，空间 O(m+n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 下标写反：<code>num1[i]×num2[j]</code> 的个位在 <code>res[i+j+1]</code>、十位进位在 <code>res[i+j]</code>，不是 <code>res[i+j]</code> 存个位。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记累加已有值：应写 <code>total = mul + res[p2]</code>，该位可能已被之前的数位对贡献过。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 前导零处理不当：结果数组首位常为 0，需跳过；但若乘积为 0 必须返回 <code>"0"</code> 而非空字符串。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：乘数为 0</div>
    <code>num1 = "0", num2 = "12345" → "0"</code>（任一侧为 0 即返回 "0"）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单 digit</div>
    <code>num1 = "2", num2 = "3" → "6"</code>（最小非平凡输入）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：含前导零的乘积位</div>
    <code>num1 = "99", num2 = "99" → "9801"</code>（中间结果数组有前导零，输出需跳过）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：长度差大</div>
    <code>num1 = "1", num2 = "99999999999999999999" → "99999999999999999999"</code>（一位数乘大数）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：经典样例</div>
    <code>num1 = "123", num2 = "456" → "56088"</code>
</div>""",
    },
    "wildcard-matching": {
        "type": "二维DP",
        "difficulty": "困难",
        "frontend_id": "44",
        "title": "通配符匹配",
        "time_complexity": "O(m × n)（m、s 长度；n、p 长度）",
        "space_complexity": "O(m × n) / O(n)（可滚动数组优化）",
        "description": """<p>给你一个输入字符串 <code>s</code> 和一个字符模式 <code>p</code>，请你实现一个支持 <code>'?'</code> 和 <code>'*'</code> 匹配规则的通配符匹配：</p>
<ul>
<li><code>'?'</code> 可以匹配任何单个字符。</li>
<li><code>'*'</code> 可以匹配任意字符序列（包括空字符序列）。</li>
</ul>
<p>判定匹配成功的充要条件是：字符模式必须能够 <strong>完全匹配</strong> 输入字符串（而不是部分匹配）。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：s = "aa", p = "a"</div>
    <div class="example-output">输出：false</div>
    <div class="example-explain">"a" 无法匹配 "aa" 整个字符串。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：s = "aa", p = "*"</div>
    <div class="example-output">输出：true</div>
    <div class="example-explain">'*' 可以匹配任意字符串。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：s = "cb", p = "?a"</div>
    <div class="example-output">输出：false</div>
    <div class="example-explain">'?' 可以匹配 'c'，但第二个 'a' 无法匹配 'b'。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>dp[i][j]</code></td><td>bool[][]</td><td><b>定义</b>：<code>s</code> 的前 <code>i</code> 个字符能否被 <code>p</code> 的前 <code>j</code> 个字符<b>完整</b>匹配<br><b>维护</b>：只依赖更小的子问题 <code>dp[i-1][j-1]</code>、<code>dp[i][j-1]</code>、<code>dp[i-1][j]</code><br><b>更新</b>：若 <code>p[j-1]</code> 是普通字符或 <code>'?'</code>，看当前位能否对上并继承 <code>dp[i-1][j-1]</code>；若是 <code>'*'</code>，先尝试「匹配空序列」(<code>dp[i][j-1]</code>)，再尝试「多吃掉 <code>s</code> 的一个字符」(<code>dp[i-1][j]</code>)</td></tr>
    <tr><td><code>i, j</code></td><td>int</td><td><b>定义</b>：分别表示已消耗的 <code>s</code> 前缀长度、<code>p</code> 前缀长度<br><b>维护</b>：<code>i</code> 从 0 到 <code>m</code>，<code>j</code> 从 0 到 <code>n</code> 递增填表<br><b>更新</b>：答案在 <code>dp[m][n]</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：遇到 <code>'*'</code> 就递归枚举「匹配 0 个 / 1 个 / 2 个…」字符，指数级回溯，<code>s=2000, p=2000</code> 会超时。</p>
<p class="thinking-step">2. 重复在哪里？同样的 <code>(i, j)</code>（还剩多少 <code>s</code>、还剩多少 <code>p</code>）会被反复访问——典型重叠子问题。</p>
<p class="thinking-step">3. 子问题定义：「<code>s</code> 的前 <code>i</code> 个能否被 <code>p</code> 的前 <code>j</code> 个完整匹配？」自然落到二维 DP。与正则题不同，这里的 <code>'*'</code> 不绑定前一个字符，可独立匹配任意长度序列。</p>
<p class="thinking-step">4. 难点在 <code>'*'</code>：它可以匹配空（直接看 <code>dp[i][j-1]</code>，跳过这个 <code>*</code>），也可以再多吃 <code>s</code> 的一个字符（看 <code>dp[i-1][j]</code>，<code>*</code> 仍留在模式里继续匹配后续）。</p>
<p class="thinking-step">5. 边界：<code>dp[0][0]=true</code>；空串匹配纯 <code>*</code> 模式时，<code>dp[0][j] = dp[0][j-1]</code>（只有 <code>*</code> 能匹配空序列）。</p>""",
        "code_steps": """<p class="code-step">1. 建表 <code>dp[(m+1)][(n+1)]</code>，<code>dp[0][0]=true</code></p>
<p class="code-step">2. 初始化第 0 行：若 <code>p[j-1]=='*'</code>，则 <code>dp[0][j] = dp[0][j-1]</code>（空串被 <code>*</code> 吃掉）</p>
<p class="code-step">3. 双重循环填表：若 <code>p[j-1]=='*'</code>，<code>dp[i][j] = dp[i][j-1] or dp[i-1][j]</code></p>
<p class="code-step">4. 否则若 <code>p[j-1]=='?'</code> 或 <code>s[i-1]==p[j-1]</code>，<code>dp[i][j] = dp[i-1][j-1]</code></p>
<p class="code-step">5. 返回 <code>dp[m][n]</code></p>""",
        "code_python": """class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        m, n = len(s), len(p)
        # dp[i][j]：s 前 i 个字符能否被 p 前 j 个完整匹配
        dp = [[False] * (n + 1) for _ in range(m + 1)]
        dp[0][0] = True

        # 空串匹配纯 * 模式：* 可匹配空序列
        for j in range(1, n + 1):
            if p[j - 1] == '*':
                dp[0][j] = dp[0][j - 1]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if p[j - 1] == '*':
                    # 匹配空序列（跳过 *）或多吃 s 的一个字符
                    dp[i][j] = dp[i][j - 1] or dp[i - 1][j]
                elif p[j - 1] == '?' or s[i - 1] == p[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]

        return dp[m][n]""",
        "code_cpp": """class Solution {
public:
    bool isMatch(string s, string p) {
        int m = s.size(), n = p.size();
        vector<vector<bool>> dp(m + 1, vector<bool>(n + 1, false));
        dp[0][0] = true;

        for (int j = 1; j <= n; j++) {
            if (p[j - 1] == '*')
                dp[0][j] = dp[0][j - 1];
        }

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
                if (p[j - 1] == '*') {
                    dp[i][j] = dp[i][j - 1] || dp[i - 1][j];
                } else if (p[j - 1] == '?' || s[i - 1] == p[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1];
                }
            }
        }
        return dp[m][n];
    }
};
// 时间 O(mn)，空间 O(mn)，可滚动数组优化到 O(n)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 通配符 <code>'*'</code> 与正则 <code>'*'</code> 不同：它不绑定前一个字符，转移是 <code>dp[i][j-1]</code>（跳过 <code>*</code>）和 <code>dp[i-1][j]</code>（<code>*</code> 继续吃字符），不是 <code>dp[i][j-2]</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空串行初始化不能漏：像 <code>"***"</code>、<code>"a*b*"</code> 对空串也应为 true，只有 <code>p[j-1]=='*'</code> 时才能 <code>dp[0][j]=dp[0][j-1]</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>'?'</code> 只能匹配<b>一个</b>字符，不能匹配空；写 <code>dp[i][j]=dp[i][j-1]</code> 会误判。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：模式比串长</div>
    <code>s = "aa", p = "a" → false</code>（模式无法覆盖整个串）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单个 * 通吃</div>
    <code>s = "aa", p = "*" → true</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：? 与字面字符</div>
    <code>s = "cb", p = "?a" → false</code>（? 匹配 c，但 a 无法匹配 b）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：空串 + 纯星号</div>
    <code>s = "", p = "***" → true</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：星号夹字符</div>
    <code>s = "adceb", p = "*a*b" → true</code>（* 匹配空，a 匹配 a，* 匹配 dce，b 匹配 b）
</div>""",
    },

    "jump-game-ii": {
        "type": "贪心",
        "difficulty": "中等",
        "frontend_id": "45",
        "title": "跳跃游戏 II",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给定一个长度为 <code>n</code> 的 <strong>0 索引</strong>整数数组 <code>nums</code>。初始位置在下标 0。</p>
<p>每个元素 <code>nums[i]</code> 表示从索引 <code>i</code> 向后跳转的最大长度。换句话说，如果你在索引 <code>i</code> 处，你可以跳转到任意 <code>(i + j)</code> 处：</p>
<ul>
<li><code>0 &lt;= j &lt;= nums[i]</code> 且</li>
<li><code>i + j &lt; n</code></li>
</ul>
<p>返回到达 <code>n - 1</code> 的最小跳跃次数。测试用例保证可以到达 <code>n - 1</code>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [2,3,1,1,4]</div>
    <div class="example-output">输出：2</div>
    <div class="example-explain">跳到最后一个位置的最小跳跃数是 2。从下标 0 跳到下标 1（跳 1 步），再跳 3 步到达最后一个位置。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [2,3,0,1,4]</div>
    <div class="example-output">输出：2</div>
    <div class="example-explain">与示例 1 类似，最小跳跃次数为 2。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>steps</code></td><td>int</td><td><b>定义</b>：从起点到当前「跳跃层」已使用的最小跳跃次数<br><b>维护</b>：当扫描指针 <code>i</code> 触及当前层右边界 <code>end</code> 时，说明必须再跳一层，<code>steps += 1</code><br><b>更新</b>：循环结束后 <code>steps</code> 即为到达 <code>n-1</code> 的最少跳跃数</td></tr>
    <tr><td><code>end</code></td><td>int</td><td><b>定义</b>：仅用当前 <code>steps</code> 次跳跃所能到达的最远下标（当前层的右边界）<br><b>维护</b>：初始 <code>end=0</code>；每当 <code>i==end</code> 完成一层扫描后，令 <code>end = farthest</code> 扩展到下一层<br><b>更新</b>：<code>end</code> 单调不减，且题目保证可达，最终会 ≥ <code>n-1</code></td></tr>
    <tr><td><code>farthest</code></td><td>int</td><td><b>定义</b>：在<b>当前层</b>内任取起点再跳一步，能到达的最远下标（下一层的候选右边界）<br><b>维护</b>：遍历 <code>i ∈ [0, end]</code> 时持续 <code>farthest = max(farthest, i + nums[i])</code><br><b>更新</b>：一层扫完时把 <code>farthest</code> 赋给 <code>end</code>，作为下一层边界</td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：从左到右扫描的下标，代表「当前层里正在考察的落脚点」<br><b>维护</b>：<code>for i in range(n-1)</code>，最后一格无需再跳<br><b>更新</b>：每轮用 <code>nums[i]</code> 更新 <code>farthest</code>，并在 <code>i==end</code> 时结算一层</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：从每个位置 DFS/BFS 枚举所有合法跳跃路径，记录到达 <code>n-1</code> 的最短路径，状态空间指数级，<code>n=10⁴</code> 会超时。</p>
<p class="thinking-step">2. 重复在哪里？「到位置 <code>i</code> 最少几步」会被反复计算——典型 DP：<code>dp[i] = min(dp[j]+1)</code> 对所有 <code>j&lt;i</code> 且 <code>j+nums[j]≥i</code>，朴素 O(n²)。</p>
<p class="thinking-step">3. 换个视角：不是「到某点最少几步」，而是按<b>跳跃次数分层</b>——第 0 跳能覆盖 <code>[0..end₀]</code>，在第 0 跳可达范围内再跳一次能覆盖 <code>[0..end₁]</code>……层数就是答案。</p>
<p class="thinking-step">4. 贪心关键：扫描当前层 <code>[0..end]</code> 时只需维护「再跳一步最远能到哪」<code>farthest</code>；当 <code>i</code> 扫到本层右边界 <code>end</code>，说明下一跳不可避免，<code>steps++</code> 并把 <code>end</code> 扩展到 <code>farthest</code>。</p>
<p class="thinking-step">5. 正确性直觉：在当前层内无论从哪里再跳，最远不超过 <code>farthest</code>；推迟增加 <code>steps</code> 不会让下一层边界更大，因此在 <code>i==end</code> 时结算一层是最优的。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>steps=0, end=0, farthest=0</code></p>
<p class="code-step">2. 遍历 <code>i</code> 从 0 到 <code>n-2</code>（最后一格不必再跳）</p>
<p class="code-step">3. 更新 <code>farthest = max(farthest, i + nums[i])</code></p>
<p class="code-step">4. 若 <code>i == end</code>：说明当前层扫完，<code>steps += 1</code>，<code>end = farthest</code></p>
<p class="code-step">5. 返回 <code>steps</code></p>""",
        "code_python": """class Solution:
    def jump(self, nums: List[int]) -> int:
        steps = 0
        end = 0          # 当前跳跃次数能到达的最远下标
        farthest = 0     # 下一跳能到达的最远下标
        for i in range(len(nums) - 1):
            farthest = max(farthest, i + nums[i])
            if i == end:
                steps += 1
                end = farthest
        return steps""",
        "code_cpp": """class Solution {
public:
    int jump(vector<int>& nums) {
        int steps = 0, end = 0, farthest = 0;
        for (int i = 0; i < nums.size() - 1; i++) {
            farthest = max(farthest, i + nums[i]);
            if (i == end) {
                steps++;
                end = farthest;
            }
        }
        return steps;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 循环应到 <code>n-2</code> 而非 <code>n-1</code>：已在最后一格时无需再跳，多扫一轮可能多计一次 <code>steps</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 本题求<b>最少跳跃次数</b>，与 #55「跳跃游戏」（判断能否到达）不同；能到达时最少步数贪心有效，不能混用「能跳就跳最远」的写法。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 必须在 <code>i == end</code> 时再 <code>steps++</code>，而不是每更新 <code>farthest</code> 就加；否则把「层内扫描」和「结算一层」混在一起会算错。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单元素</div>
    <code>nums = [0] → 0</code>（已在终点，无需跳跃）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：一步直达</div>
    <code>nums = [2, 1] → 1</code>（从下标 0 直接跳到末尾）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：必须分段跳</div>
    <code>nums = [1, 1, 1, 1] → 3</code>（每次最多跳 1，需 3 次）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：含零步长</div>
    <code>nums = [2, 3, 0, 1, 4] → 2</code>（中间 0 不影响层边界扩展）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：大跨度</div>
    <code>nums = [5, 4, 3, 2, 1] → 1</code>（第一步即可覆盖全程）
</div>""",
    },

    "permutations": {
        "type": "回溯",
        "difficulty": "中等",
        "frontend_id": "46",
        "title": "全排列",
        "time_complexity": "O(n × n!)",
        "space_complexity": "O(n)（递归栈 + used，不计输出）",
        "description": """<p>给定一个不含重复数字的数组 <code>nums</code>，返回其 <strong>所有可能的全排列</strong>。你可以 <strong>按任意顺序</strong> 返回答案。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,2,3]</div>
    <div class="example-output">输出：[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [0,1]</div>
    <div class="example-output">输出：[[0,1],[1,0]]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [1]</div>
    <div class="example-output">输出：[[1]]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>path</code></td><td>list&lt;int&gt;</td><td><b>定义</b>：当前正在构造的排列前缀（已选数字的有序序列）<br><b>维护</b>：每进入一层递归，从 <code>nums</code> 中选一个尚未使用的数追加到末尾<br><b>更新</b>：递归返回后 <code>pop</code> 撤销选择，保证兄弟分支从同一前缀出发</td></tr>
    <tr><td><code>used</code></td><td>list&lt;bool&gt;</td><td><b>定义</b>：长度 <code>n</code> 的标记数组，<code>used[i]</code> 表示 <code>nums[i]</code> 是否已在 <code>path</code> 中<br><b>维护</b>：选 <code>nums[i]</code> 前置 <code>used[i]=True</code>，回溯时恢复 <code>False</code><br><b>更新</b>：保证每个数字在全排列中恰好出现一次，避免重复选取</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&lt;int&gt;&gt;</td><td><b>定义</b>：所有合法全排列的集合<br><b>维护</b>：当 <code>len(path) == n</code> 时，将 <code>path[:]</code> 的副本加入<br><b>更新</b>：每到达一棵 DFS 叶子追加一次；中途不收集半成品</td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：当前层尝试选取的 <code>nums</code> 下标<br><b>维护</b>：<code>for i in range(n)</code>，跳过 <code>used[i]</code> 为真的位置<br><b>更新</b>：同一层按固定顺序枚举候选，自然覆盖所有排列且不重复</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：用 <code>itertools.permutations</code> 或三重循环硬枚举所有排列——思路对，但面试要写 DFS，且要理解为何能剪枝、如何回溯。</p>
<p class="thinking-step">2. 重复在哪里？构造排列时，「已选前缀 + 剩余可选数字」这一状态会被反复访问；若允许同一数字选两次，会产生重复元素或非法排列。</p>
<p class="thinking-step">3. 优化成回溯：用 <code>path</code> 记录当前前缀，用 <code>used[i]</code> 标记 <code>nums[i]</code> 是否已入选；每层从 0 到 n-1 扫描，跳过已用下标。</p>
<p class="thinking-step">4. 终止条件：<code>len(path) == n</code> 时得到一个完整排列，将 <code>path[:]</code> 加入 <code>ans</code>；否则对每个未使用的 <code>nums[i]</code>：标记 → 追加 → 递归 → 撤销。</p>
<p class="thinking-step">5. 题目保证元素互不相同，因此不需要「同层去重」；<code>n ≤ 6</code>，<code>n!</code> 最多 720，回溯完全可行。也可交换法原地生成，但 <code>used</code> 数组更直观。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>ans = []</code>，<code>used = [False] * n</code>，空列表 <code>path</code></p>
<p class="code-step">2. 定义 DFS <code>backtrack()</code>：若 <code>len(path) == n</code>，将 <code>path[:]</code> 加入 <code>ans</code> 并返回</p>
<p class="code-step">3. 遍历 <code>i ∈ [0, n)</code>：若 <code>used[i]</code> 为真则跳过</p>
<p class="code-step">4. 选择 <code>nums[i]</code>：<code>used[i]=True</code>，<code>path.append(nums[i])</code>，递归 <code>backtrack()</code>，再 <code>path.pop()</code> 且 <code>used[i]=False</code></p>
<p class="code-step">5. 从 <code>backtrack()</code> 启动，返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def permute(self, nums: List[int]) -> List[List[int]]:
        ans: List[List[int]] = []
        n = len(nums)
        used = [False] * n
        path: List[int] = []

        def backtrack() -> None:
            if len(path) == n:
                ans.append(path[:])
                return
            for i in range(n):
                if used[i]:
                    continue
                used[i] = True
                path.append(nums[i])
                backtrack()
                path.pop()
                used[i] = False

        backtrack()
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<int>> permute(vector<int>& nums) {
        vector<vector<int>> ans;
        vector<int> path;
        vector<bool> used(nums.size(), false);

        function<void()> dfs = [&]() {
            if (path.size() == nums.size()) {
                ans.push_back(path);
                return;
            }
            for (int i = 0; i < (int)nums.size(); i++) {
                if (used[i]) continue;
                used[i] = true;
                path.push_back(nums[i]);
                dfs();
                path.pop_back();
                used[i] = false;
            }
        };

        dfs();
        return ans;
    }
};
// 时间 O(n × n!)，空间 O(n)（递归栈 + used，不计输出）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 收集答案时必须存 <code>path[:]</code>（或 C++ 里 <code>push_back(path)</code> 副本），不能直接 <code>append(path)</code>——否则 <code>ans</code> 里全是同一可变对象的引用。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 回溯不撤销：递归返回后必须 <code>pop</code> 并恢复 <code>used[i]</code>，否则后续分支会带着脏状态，漏解或重复。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 本题元素互不相同，同层不需要「跳过相同值」；若改成 <code>permutations-ii</code>（含重复数字），才要在同层对相同 <code>nums[i]</code> 去重。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单元素</div>
    <code>nums = [1] → [[1]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：两个元素</div>
    <code>nums = [0,1] → [[0,1],[1,0]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：三个元素</div>
    <code>nums = [1,2,3] → 6 种排列</code>（3! = 6）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：含负数</div>
    <code>nums = [-1,0,1] → 6 种排列</code>（符号不影响回溯逻辑）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：最大规模</div>
    <code>n = 6 → 720 种排列</code>（仍在题目数据范围内）
</div>""",
    },

    "permutations-ii": {
        "type": "回溯",
        "difficulty": "中等",
        "frontend_id": "47",
        "title": "全排列 II",
        "time_complexity": "O(n × n!)",
        "space_complexity": "O(n)（递归栈 + used，不计输出）",
        "description": """<p>给定一个可包含重复数字的序列 <code>nums</code>，<strong>按任意顺序</strong> 返回所有<strong>不重复</strong>的全排列。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [1,1,2]</div>
    <div class="example-output">输出：[[1,1,2],[1,2,1],[2,1,1]]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [1,2,3]</div>
    <div class="example-output">输出：[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>nums</code></td><td>list&lt;int&gt;</td><td><b>定义</b>：输入数组（可能含重复元素）<br><b>维护</b>：回溯前先 <code>sort(nums)</code>，让相同数字相邻<br><b>更新</b>：排序后才能在同一 DFS 层用「相邻相等」规则剪枝，避免重复排列</td></tr>
    <tr><td><code>path</code></td><td>list&lt;int&gt;</td><td><b>定义</b>：当前正在构造的排列前缀<br><b>维护</b>：每层从未使用的 <code>nums[i]</code> 中选一个追加到末尾<br><b>更新</b>：递归返回后 <code>pop</code> 撤销，保证兄弟分支从同一前缀出发</td></tr>
    <tr><td><code>used</code></td><td>list&lt;bool&gt;</td><td><b>定义</b>：长度 <code>n</code> 的标记数组，<code>used[i]</code> 表示 <code>nums[i]</code> 是否已在 <code>path</code> 中<br><b>维护</b>：选 <code>nums[i]</code> 前置 <code>used[i]=True</code>，回溯时恢复 <code>False</code><br><b>更新</b>：保证每个下标最多用一次；配合排序实现同层去重</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&lt;int&gt;&gt;</td><td><b>定义</b>：所有不重复全排列的集合<br><b>维护</b>：当 <code>len(path) == n</code> 时，将 <code>path[:]</code> 副本加入<br><b>更新</b>：每到达一棵 DFS 叶子追加一次</td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：当前层尝试选取的 <code>nums</code> 下标<br><b>维护</b>：<code>for i in range(n)</code>，跳过已用及同层重复值<br><b>更新</b>：若 <code>nums[i]==nums[i-1]</code> 且 <code>used[i-1]</code> 为假，说明同层已枚举过该值，直接 <code>continue</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：沿用 #46 全排列的 DFS + <code>used</code> 回溯——能枚举所有排列，但 <code>nums</code> 有重复时，会产出重复结果，例如 <code>[1,1,2]</code> 会多次得到 <code>[1,1,2]</code>。</p>
<p class="thinking-step">2. 重复在哪里？不是「状态」重复，而是「排列结果」重复：两个相同的 <code>1</code> 互换位置，得到的序列一样。需要在搜索树同层剪掉「选相同值但来自不同下标」的等价分支。</p>
<p class="thinking-step">3. 关键观察：先 <code>sort(nums)</code>，同一层 DFS 中，若 <code>nums[i] == nums[i-1]</code> 且左边的 <code>nums[i-1]</code> 本轮还没用（<code>not used[i-1]</code>），说明同层已经用「第一个 1」试过这条路，再选「第二个 1」只会重复。</p>
<p class="thinking-step">4. 剪枝条件 <code>i &gt; 0 and nums[i] == nums[i-1] and not used[i-1]</code>：保证相同数字按排序后的下标顺序被使用（先选靠前的副本），从而同层只保留一种选法。</p>
<p class="thinking-step">5. 终止与回溯不变：<code>len(path)==n</code> 收集答案；否则对每个合法 <code>i</code>：标记 → 追加 → 递归 → 撤销。<code>n ≤ 8</code>，剪枝后规模仍可控。</p>""",
        "code_steps": """<p class="code-step">1. 将 <code>nums</code> 排序；初始化 <code>ans</code>、<code>used = [False]*n</code>、空 <code>path</code></p>
<p class="code-step">2. 定义 DFS <code>backtrack()</code>：若 <code>len(path) == n</code>，将 <code>path[:]</code> 加入 <code>ans</code> 并返回</p>
<p class="code-step">3. 遍历 <code>i ∈ [0, n)</code>：若 <code>used[i]</code> 为真则跳过</p>
<p class="code-step">4. 同层去重：若 <code>i &gt; 0 and nums[i] == nums[i-1] and not used[i-1]</code>，<code>continue</code></p>
<p class="code-step">5. 选择 <code>nums[i]</code>：<code>used[i]=True</code>，<code>path.append(nums[i])</code>，递归，再 <code>pop</code> 并 <code>used[i]=False</code></p>
<p class="code-step">6. 启动 <code>backtrack()</code>，返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def permuteUnique(self, nums: List[int]) -> List[List[int]]:
        nums.sort()
        ans: List[List[int]] = []
        n = len(nums)
        used = [False] * n
        path: List[int] = []

        def backtrack() -> None:
            if len(path) == n:
                ans.append(path[:])
                return
            for i in range(n):
                if used[i]:
                    continue
                if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:
                    continue
                used[i] = True
                path.append(nums[i])
                backtrack()
                path.pop()
                used[i] = False

        backtrack()
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<int>> permuteUnique(vector<int>& nums) {
        sort(nums.begin(), nums.end());
        vector<vector<int>> ans;
        vector<int> path;
        vector<bool> used(nums.size(), false);

        function<void()> dfs = [&]() {
            if (path.size() == nums.size()) {
                ans.push_back(path);
                return;
            }
            for (int i = 0; i < (int)nums.size(); i++) {
                if (used[i]) continue;
                if (i > 0 && nums[i] == nums[i - 1] && !used[i - 1]) continue;
                used[i] = true;
                path.push_back(nums[i]);
                dfs();
                path.pop_back();
                used[i] = false;
            }
        };

        dfs();
        return ans;
    }
};
// 时间 O(n × n!)，空间 O(n)（递归栈 + used，不计输出）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记先排序：不排序则 <code>nums[i]==nums[i-1]</code> 剪枝无效，仍会输出重复排列。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 同层去重条件写反：应是 <code>not used[i-1]</code>（左边相同值未用才跳过），写成 <code>used[i-1]</code> 会误剪合法分支、漏解。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 收集答案时必须存 <code>path[:]</code> 副本；回溯后忘记 <code>pop</code> 或恢复 <code>used[i]</code> 会导致脏状态。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：全相同</div>
    <code>nums = [1,1,1] → [[1,1,1]]</code>（只有一种排列）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：两两重复</div>
    <code>nums = [1,1,2,2] → 6 种不重复排列</code>（4!/(2!×2!) = 6）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：无重复</div>
    <code>nums = [1,2,3] → 6 种排列</code>（退化为 #46，剪枝条件不触发）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：单元素</div>
    <code>nums = [0] → [[0]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：含负数</div>
    <code>nums = [-1,-1,0] → [[-1,-1,0],[-1,0,-1],[0,-1,-1]]</code>（排序后去重逻辑不变）
</div>""",
    },

    "rotate-image": {
        "type": "矩阵操作",
        "difficulty": "中等",
        "frontend_id": "48",
        "title": "旋转图像",
        "time_complexity": "O(n²)",
        "space_complexity": "O(1)（原地修改，不计输入）",
        "description": """<p>给定一个 <em>n</em> × <em>n</em> 的二维矩阵 <code>matrix</code> 表示一个图像。请你将图像<strong>顺时针旋转 90 度</strong>。</p>
<p>你必须在<strong><a href="https://baike.baidu.com/item/%E5%8E%9F%E5%9C%B0%E7%AE%97%E6%B3%95" target="_blank">原地</a></strong>旋转图像，这意味着你需要直接修改输入的二维矩阵。<strong>请不要</strong>使用另一个矩阵来旋转图像。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：matrix = [[1,2,3],[4,5,6],[7,8,9]]</div>
    <div class="example-output">输出：[[7,4,1],[8,5,2],[9,6,3]]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]</div>
    <div class="example-output">输出：[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>matrix</code></td><td>list&lt;list&lt;int&gt;&gt;</td><td><b>定义</b>：<code>n×n</code> 方阵，既是输入也是最终输出<br><b>维护</b>：分两步原地变换——先沿主对角线转置，再对每一行左右翻转<br><b>更新</b>：转置交换 <code>matrix[i][j]</code> 与 <code>matrix[j][i]</code>；翻转交换行内 <code>matrix[i][left]</code> 与 <code>matrix[i][right]</code></td></tr>
    <tr><td><code>n</code></td><td>int</td><td><b>定义</b>：矩阵边长，<code>n = len(matrix)</code><br><b>维护</b>：转置时 <code>i</code> 取 <code>0..n-1</code>，<code>j</code> 取 <code>i+1..n-1</code>，避免同一对元素交换两次<br><b>更新</b>：全程不变，控制两层循环边界</td></tr>
    <tr><td><code>i, j</code></td><td>int</td><td><b>定义</b>：转置阶段的双重下标，遍历上三角区域<br><b>维护</b>：每对 <code>(i,j)</code> 满足 <code>j &gt; i</code>，交换 <code>matrix[i][j]</code> 与 <code>matrix[j][i]</code><br><b>更新</b>：双重循环递增；转置完成后进入逐行翻转阶段</td></tr>
    <tr><td><code>left, right</code></td><td>int</td><td><b>定义</b>：翻转第 <code>i</code> 行时的双指针，分别指向行首与行尾<br><b>维护</b>：<code>left &lt; right</code> 时交换 <code>matrix[i][left]</code> 与 <code>matrix[i][right]</code>，然后 <code>left++</code>、<code>right--</code><br><b>更新</b>：相遇时当前行翻转完成，换下一行</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：开一个新 <code>n×n</code> 数组，按公式 <code>new[j][n-1-i] = old[i][j]</code> 填值——思路正确，但题目要求原地，额外 <code>O(n²)</code> 空间会被判不符合。</p>
<p class="thinking-step">2. 重复在哪里？若逐元素搬到临时变量再写回，本质上仍需要辅助存储；要把「顺时针 90°」拆成可在原数组上完成的原子操作。</p>
<p class="thinking-step">3. 关键观察：顺时针 90° = 先<strong>转置</strong>（沿主对角线交换）再对<strong>每一行左右翻转</strong>。手画 3×3 例子可验证：转置后 [[1,4,7],[2,5,8],[3,6,9]]，逐行翻转即得目标。</p>
<p class="thinking-step">4. 坐标规律：原位置 <code>(i,j)</code> 顺时针 90° 后到 <code>(j, n-1-i)</code>；转置把 <code>(i,j)→(j,i)</code>，行翻转把 <code>(j,i)→(j, n-1-i)</code>，两步合成即目标映射。</p>
<p class="thinking-step">5. 另一种等价写法是按「同心层」四元组循环交换（每次转 4 个角），但转置+翻转代码更短、不易写错下标；<code>n ≤ 20</code>，<code>O(n²)</code> 完全够用。</p>""",
        "code_steps": """<p class="code-step">1. 取 <code>n = len(matrix)</code></p>
<p class="code-step">2. <strong>转置</strong>：双重循环 <code>for i in range(n): for j in range(i+1, n):</code> 交换 <code>matrix[i][j]</code> 与 <code>matrix[j][i]</code></p>
<p class="code-step">3. <strong>逐行翻转</strong>：对每行 <code>i</code>，令 <code>left=0, right=n-1</code>，当 <code>left &lt; right</code> 时交换两端元素并收缩指针</p>
<p class="code-step">4. 两步完成后 <code>matrix</code> 即为顺时针 90° 结果，无需返回值（原地修改）</p>""",
        "code_python": """class Solution:
    def rotate(self, matrix: List[List[int]]) -> None:
        n = len(matrix)
        # 1. 沿主对角线转置
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        # 2. 每一行左右翻转
        for i in range(n):
            left, right = 0, n - 1
            while left < right:
                matrix[i][left], matrix[i][right] = matrix[i][right], matrix[i][left]
                left += 1
                right -= 1""",
        "code_cpp": """class Solution {
public:
    void rotate(vector<vector<int>>& matrix) {
        int n = matrix.size();
        // 1. 沿主对角线转置
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                swap(matrix[i][j], matrix[j][i]);
            }
        }
        // 2. 每一行左右翻转
        for (int i = 0; i < n; i++) {
            int left = 0, right = n - 1;
            while (left < right) {
                swap(matrix[i][left], matrix[i][right]);
                left++;
                right--;
            }
        }
    }
};
// 时间 O(n²)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 转置时 <code>j</code> 必须从 <code>i+1</code> 开始，不能从 0 开始——否则同一对元素会被交换两次，等于没转置。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 逆时针 90° 是「转置 + 逐列翻转」或「先逐行翻转再转置」，与顺时针步骤不同；混用会得到错误结果。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 题目要求原地修改、无返回值；新建矩阵再赋值虽能 AC 部分测试，但不符合题意且浪费空间。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：1×1 矩阵</div>
    <code>matrix = [[1]] → [[1]]</code>（转置与翻转均为空操作）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：2×2 矩阵</div>
    <code>matrix = [[1,2],[3,4]] → [[3,1],[4,2]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：含负数</div>
    <code>matrix = [[-1,2],[-3,4]] → [[-3,-1],[4,2]]</code>（符号不影响交换逻辑）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：奇数边长 3×3</div>
    <code>matrix = [[1,2,3],[4,5,6],[7,8,9]] → [[7,4,1],[8,5,2],[9,6,3]]</code>（中心元素 5 转置后仍在中心）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：偶数边长 4×4</div>
    <code>见示例 2</code>（无单独中心格，全靠成对交换完成）
</div>""",
    },
    "group-anagrams": {
        "type": "哈希表",
        "difficulty": "中等",
        "frontend_id": "49",
        "title": "字母异位词分组",
        "time_complexity": "O(n · k log k)",
        "space_complexity": "O(n · k)",
        "description": """<p>给你一个字符串数组，请你将 <strong>字母异位词</strong> 组合在一起。可以按任意顺序返回结果列表。</p>
<p><strong>字母异位词</strong> 是由重新排列源单词的所有字母得到的一个新单词。通常，所有源单词中的字母恰好只使用一次。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：strs = ["eat","tea","tan","ate","nat","bat"]</div>
    <div class="example-output">输出：[["bat"],["nat","tan"],["ate","eat","tea"]]</div>
    <div class="example-explain"><code>"nat"</code> 与 <code>"tan"</code> 互为异位词；<code>"ate"</code>、<code>"eat"</code>、<code>"tea"</code> 互为异位词；<code>"bat"</code> 单独成组。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：strs = [""]</div>
    <div class="example-output">输出：[[""]]</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：strs = ["a"]</div>
    <div class="example-output">输出：[["a"]]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>groups</code></td><td>dict[str, list[str]]</td><td><b>定义</b>：从「异位词签名」到「同组字符串列表」的哈希表，最终答案即其所有 value<br><b>维护</b>：遍历过程中，同一签名下的字符串始终被放在同一个列表里<br><b>更新</b>：每处理一个 <code>s</code>，计算签名 <code>key</code>，执行 <code>groups.setdefault(key, []).append(s)</code></td></tr>
    <tr><td><code>s</code></td><td>str</td><td><b>定义</b>：当前正在处理的输入字符串<br><b>维护</b>：外层循环每次取 <code>strs</code> 中的一个元素，内层只读不改原串<br><b>更新</b>：按输入顺序逐个推进，直到全部处理完</td></tr>
    <tr><td><code>key</code></td><td>str</td><td><b>定义</b>：字符串 <code>s</code> 的异位词签名，取排序后的结果（如 <code>"eat" → "aet"</code>）<br><b>维护</b>：互为异位词的字符串必然得到相同的 <code>key</code>，不同组则 <code>key</code> 不同<br><b>更新</b>：对每个 <code>s</code> 重新计算：<code>key = "".join(sorted(s))</code></td></tr>
    <tr><td><code>strs</code></td><td>list[str]</td><td><b>定义</b>：输入字符串数组，长度 <code>n</code>，每个串长度不超过 100<br><b>维护</b>：只读遍历，不修改元素内容<br><b>更新</b>：作为外层循环的数据源，驱动整次分组</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：对每个字符串，和其余所有串两两比较是否为异位词（排序后相等或字符频次相同），相同则划入同一组——思路正确，但最坏要 O(n²) 次比较，每次比较还要 O(k log k) 排序。</p>
<p class="thinking-step">2. 重复在哪里？判断「eat 和 tea 是否同组」时，其实不必关心它们具体怎么排列，只关心<strong>字母 multiset 是否相同</strong>——也就是说，异位词共享同一个「签名」。</p>
<p class="thinking-step">3. 关键转化：为每个字符串算一个签名 <code>key</code>（排序后的串，如 <code>"tan" → "ant"</code>），用哈希表 <code>groups[key]</code> 收集所有同签名字符串；扫一遍输入即可完成分组。</p>
<p class="thinking-step">4. 手推示例 1：<code>"eat","tea","ate"</code> 的 key 都是 <code>"aet"</code>，落入同一列表；<code>"tan","nat"</code> 的 key 都是 <code>"ant"</code>；<code>"bat"</code> 的 key 是 <code>"abt"</code>，单独一组。</p>
<p class="thinking-step">5. 另一种等价签名是长度 26 的字符计数元组（O(k) 不需排序），但排序写法更短；<code>n ≤ 10⁴, k ≤ 100</code>，总复杂度 O(n · k log k) 完全够用。</p>""",
        "code_steps": """<p class="code-step">1. 初始化空哈希表 <code>groups = {}</code></p>
<p class="code-step">2. 遍历每个字符串 <code>s in strs</code></p>
<p class="code-step">3. 计算签名 <code>key = "".join(sorted(s))</code></p>
<p class="code-step">4. 若 <code>key</code> 不在表中则 <code>groups[key] = []</code>，然后将 <code>s</code> 追加到 <code>groups[key]</code></p>
<p class="code-step">5. 返回 <code>list(groups.values())</code>（外层列表顺序任意）</p>""",
        "code_python": """class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        groups: dict[str, list[str]] = {}
        for s in strs:
            key = "".join(sorted(s))
            if key not in groups:
                groups[key] = []
            groups[key].append(s)
        return list(groups.values())""",
        "code_cpp": """class Solution {
public:
    vector<vector<string>> groupAnagrams(vector<string>& strs) {
        unordered_map<string, vector<string>> groups;
        for (const string& s : strs) {
            string key = s;
            sort(key.begin(), key.end());
            groups[key].push_back(s);
        }
        vector<vector<string>> ans;
        for (auto& [k, v] : groups) {
            ans.push_back(move(v));
        }
        return ans;
    }
};
// 时间 O(n·k log k)，空间 O(n·k)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 不能用「字符串长度」当 key——<code>"ab"</code> 和 <code>"cd"</code> 长度相同但不是异位词，必须比较字母组成（排序或计数）。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 返回的是「分组列表的列表」，外层顺序任意，但每组内的字符串必须来自输入、不能遗漏或重复。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 空字符串 <code>""</code> 排序后仍是 <code>""</code>，应正常入组；不要当作特殊值跳过。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单个字符串</div>
    <code>strs = ["a"] → [["a"]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：空字符串</div>
    <code>strs = [""] → [[""]]</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：全部互为异位词</div>
    <code>strs = ["abc","bca","cab"] → [["abc","bca","cab"]]</code>（只有一个分组）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：全部不同组</div>
    <code>strs = ["a","b","c"] → [["a"],["b"],["c"]]</code>（每组仅一个元素）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：相同字符串重复出现</div>
        <code>strs = ["dd","dd"] → [["dd","dd"]]</code>（相同签名，应归入同一组）
</div>""",
    },

    "powx-n": {
        "type": "数学模拟",
        "difficulty": "中等",
        "frontend_id": "50",
        "title": "Pow(x, n)",
        "time_complexity": "O(log|n|)",
        "space_complexity": "O(1)",
        "description": """<p>实现 <a href="https://www.cplusplus.com/reference/valarray/pow/" target="_blank">pow(<em>x</em>, <em>n</em>)</a>，即计算 <code>x</code> 的整数 <code>n</code> 次幂函数（即，<code>x<sup>n</sup></code>）。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：x = 2.00000, n = 10</div>
    <div class="example-output">输出：1024.00000</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：x = 2.10000, n = 3</div>
    <div class="example-output">输出：9.26100</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：x = 2.00000, n = -2</div>
    <div class="example-output">输出：0.25000</div>
    <div class="example-explain"><code>2<sup>-2</sup> = 1/2<sup>2</sup> = 1/4 = 0.25</code></div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>result</code></td><td>double</td><td><b>定义</b>：当前已累积的幂次结果，初始为 1.0<br><b>维护</b>：每当指数 <code>exp</code> 的最低二进制位为 1 时，乘上当前的底数 <code>x</code><br><b>更新</b>：若 <code>exp &amp; 1</code> 则 <code>result *= x</code>；每轮循环结束后 <code>x</code> 会自乘，<code>exp</code> 右移一位</td></tr>
    <tr><td><code>x</code></td><td>double</td><td><b>定义</b>：当前轮的「底数」，代表 <code>原底数<sup>2<sup>k</sup></sup></code>（k 为已右移的位数）<br><b>维护</b>：每轮循环末尾自乘一次，相当于底数平方<br><b>更新</b>：若 <code>n &lt; 0</code> 先变为 <code>1/x</code>；循环中 <code>x *= x</code></td></tr>
    <tr><td><code>exp</code></td><td>long long</td><td><b>定义</b>：剩余待处理的指数（绝对值），用 long long 避免 <code>INT_MIN</code> 取负溢出<br><b>维护</b>：每轮右移一位，等价于将指数二进制表示从低位向高位消费<br><b>更新</b>：若原 <code>n &lt; 0</code> 则 <code>exp = -(long long)n</code>；否则 <code>exp = n</code>；循环中 <code>exp &gt;&gt;= 1</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：循环 <code>n</code> 次做 <code>result *= x</code>——思路对，但 <code>n</code> 可达 2³¹，O(n) 必超时。</p>
<p class="thinking-step">2. 重复在哪里？乘方满足 <code>x<sup>n</sup> = x<sup>n/2</sup> × x<sup>n/2</sup></code>（n 为偶数）或 <code>x<sup>n</sup> = x × x<sup>n-1</sup></code>（n 为奇数）——同一底数被反复平方，可以「折半」处理指数。</p>
<p class="thinking-step">3. 关键转化（快速幂）：把 <code>n</code> 写成二进制，例如 <code>10 = 1010₂</code>，则 <code>x<sup>10</sup> = x<sup>8</sup> × x<sup>2</sup>。从低位到高位扫描：当前位为 1 就把 <code>result</code> 乘上此时的 <code>x</code>，然后 <code>x</code> 自乘、<code>n</code> 右移一位。</p>
<p class="thinking-step">4. 手推示例 1（x=2, n=10）：<code>10 = 1010₂</code>。第 1 轮（末位 0）只平方 x→4；第 2 轮（末位 1）result×4=4，x→16；第 3 轮（末位 0）x→256；第 4 轮（末位 1）result×256=1024。✓</p>
<p class="thinking-step">5. 负指数：若 <code>n &lt; 0</code>，等价于计算 <code>(1/x)<sup>|n|</sup></code>，先把 <code>x</code> 取倒数、<code>exp</code> 取绝对值；<code>n = INT_MIN</code> 时 <code>-n</code> 在 32 位会溢出，必须用 <code>long long</code> 存指数。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>n &lt; 0</code>：令 <code>x = 1.0 / x</code>，<code>exp = -(long long)n</code>；否则 <code>exp = n</code></p>
<p class="code-step">2. 初始化 <code>result = 1.0</code></p>
<p class="code-step">3. 循环 <code>while exp &gt; 0</code>：若 <code>exp &amp; 1</code>（最低位为 1），则 <code>result *= x</code></p>
<p class="code-step">4. 每轮末尾：<code>x *= x</code>（底数平方），<code>exp &gt;&gt;= 1</code>（指数折半）</p>
<p class="code-step">5. 返回 <code>result</code></p>""",
        "code_python": """class Solution:
    def myPow(self, x: float, n: int) -> float:
        exp = n
        if exp < 0:
            x = 1.0 / x
            exp = -exp          # Python int 无溢出，INT_MIN 也安全
        result = 1.0
        while exp:
            if exp & 1:         # 当前二进制位为 1，乘上这一轮的底数
                result *= x
            x *= x              # 底数平方，对应指数左移一位
            exp >>= 1
        return result""",
        "code_cpp": """class Solution {
public:
    double myPow(double x, int n) {
        long long exp = n;          // 用 long long 避免 INT_MIN 取负溢出
        if (exp < 0) {
            x = 1.0 / x;
            exp = -exp;
        }
        double result = 1.0;
        while (exp > 0) {
            if (exp & 1)            // 当前二进制位为 1
                result *= x;
            x *= x;                 // 底数平方
            exp >>= 1;
        }
        return result;
    }
};
// 时间 O(log|n|)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>n = INT_MIN (-2147483648)</code> 时，<code>-n</code> 在 32 位 int 中会溢出；C++ 必须先把 <code>n</code> 转成 <code>long long</code> 再取负。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 负指数要先对 <code>x</code> 取倒数再算正指数幂，不要直接循环负数次乘法。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 判断当前位用 <code>exp &amp; 1</code> 或 <code>exp % 2 == 1</code>，不要用浮点；底数 <code>x</code> 可以为 0（此时 <code>n &gt; 0</code> 才出现，结果为 0）。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：指数为 0</div>
    <code>x = 2.0, n = 0 → 1.0</code>（任何非零数的 0 次幂为 1）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：负指数</div>
    <code>x = 2.0, n = -2 → 0.25</code>（等价于 1/4）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：底数为 1</div>
    <code>x = 1.0, n = 100000 → 1.0</code>
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：INT_MIN 指数</div>
    <code>x = 2.0, n = -2147483648 → 2.0<sup>-2147483648</sup></code>（需 long long 处理，不能对 int 直接取负）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：底数为负、指数为偶数</div>
    <code>x = -2.0, n = 2 → 4.0</code>（负底数偶次幂为正）
</div>""",
    },

    "n-queens": {
        "type": "回溯",
        "difficulty": "困难",
        "frontend_id": "51",
        "title": "N 皇后",
        "time_complexity": "O(n!)（剪枝后远好于 n^n 全枚举）",
        "space_complexity": "O(n)（递归栈 + 冲突集合，不计输出）",
        "description": """<p>按照国际象棋的规则，皇后可以攻击与之处在同一行或同一列或同一斜线上的棋子。</p>
<p><strong>n 皇后问题</strong> 研究的是如何将 <code>n</code> 个皇后放置在 <code>n×n</code> 的棋盘上，并且使皇后彼此之间不能相互攻击。</p>
<p>给你一个整数 <code>n</code>，返回所有不同的 <strong>n 皇后问题</strong> 的解决方案。</p>
<p>每一种解法包含一个不同的 <strong>n 皇后问题</strong> 的棋子放置方案，该方案中 <code>'Q'</code> 和 <code>'.'</code> 分别代表了皇后和空位。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：n = 4</div>
    <div class="example-output">输出：[[".Q..","...Q","Q...","..Q."],["..Q.","Q...","...Q",".Q.."]]</div>
    <div class="example-explain">4 皇后问题存在两个不同的解法，如上图所示（同一行、列、斜线不能有两个皇后）。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：n = 1</div>
    <div class="example-output">输出：[["Q"]]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>queens</code></td><td>int[n]</td><td><b>定义</b>：<code>queens[row]</code> 表示第 <code>row</code> 行皇后所在的列号<br><b>维护</b>：每行恰好放一个皇后，用一维数组即可完整描述当前部分解<br><b>更新</b>：在 <code>row</code> 行尝试列 <code>col</code> 时令 <code>queens[row]=col</code>；回溯返回后该位置会被下一列覆盖</td></tr>
    <tr><td><code>cols</code></td><td>set&lt;int&gt;</td><td><b>定义</b>：已被占用的列号集合<br><b>维护</b>：任意时刻，已放置的皇后两两不同列<br><b>更新</b>：在 <code>(row,col)</code> 放皇后前查 <code>col not in cols</code>；放入时 <code>add(col)</code>，回溯时 <code>remove(col)</code></td></tr>
    <tr><td><code>diag1</code></td><td>set&lt;int&gt;</td><td><b>定义</b>：主对角线标识 <code>row - col</code> 的已占用集合（↘ 方向同线相等）<br><b>维护</b>：同一主对角线上任意两格 <code>row-col</code> 相同<br><b>更新</b>：放皇后前查 <code>(row-col) not in diag1</code>；放入/撤销与 <code>cols</code> 同步</td></tr>
    <tr><td><code>diag2</code></td><td>set&lt;int&gt;</td><td><b>定义</b>：副对角线标识 <code>row + col</code> 的已占用集合（↗ 方向同线相等）<br><b>维护</b>：同一副对角线上任意两格 <code>row+col</code> 相同<br><b>更新</b>：放皇后前查 <code>(row+col) not in diag2</code>；放入/撤销与 <code>cols</code> 同步</td></tr>
    <tr><td><code>row</code></td><td>int</td><td><b>定义</b>：当前待放置皇后的行号（从 0 到 n-1）<br><b>维护</b>：DFS 逐行向下推进，每行只尝试合法列<br><b>更新</b>：初始为 0；每成功放一行后 <code>row+1</code> 递归；<code>row==n</code> 时收集完整解</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&lt;str&gt;&gt;</td><td><b>定义</b>：所有合法棋盘的字符串表示<br><b>维护</b>：仅当 <code>row==n</code> 时，按 <code>queens</code> 构造 n 行字符串并加入<br><b>更新</b>：每到达叶子层追加一次；构造时第 <code>r</code> 行在 <code>queens[r]</code> 处放 <code>'Q'</code>，其余为 <code>'.'</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：在 <code>n×n</code> 的每个格子里决定放或不放皇后，共 <code>2^{n²}</code> 种状态，再过滤出恰好 n 个皇后且互不攻击的——思路对，但状态空间巨大。</p>
<p class="thinking-step">2. 第一个剪枝：每行必须恰好一个皇后（否则某行空着或有两个，都不合法），问题变成「为每一行选一个列」，至多 <code>n^n</code> 种排列。</p>
<p class="thinking-step">3. 重复在哪里？按行放置时，子问题变成「前 <code>row</code> 行已放好，第 <code>row</code> 行该放哪一列？」——很多列选法会与已有皇后同列或同斜线冲突，却还要把后面所有行试完。</p>
<p class="thinking-step">4. 关键转化：用 <code>cols</code>、<code>diag1(row-col)</code>、<code>diag2(row+col)</code> 三个集合 O(1) 判断冲突；DFS 逐行枚举列，能放就递归下一行，子树走不通立刻撤销换列。</p>
<p class="thinking-step">5. 手推 n=4：第 0 行试 col=0 会一路走到死路；col=1 得解 <code>".Q.."/"...Q"/"Q..."/"..Q."</code>；继续搜索还能找到对称解。<code>n≤9</code>，回溯深度 ≤ 9，完全可行。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>ans = []</code>、<code>queens = [0]*n</code>，以及空集合 <code>cols, diag1, diag2</code></p>
<p class="code-step">2. 定义 DFS <code>backtrack(row)</code>：若 <code>row == n</code>，按 <code>queens</code> 构造 n 行字符串加入 <code>ans</code> 并返回</p>
<p class="code-step">3. 对 <code>col</code> 从 0 到 n-1：若 <code>col in cols</code> 或 <code>(row-col) in diag1</code> 或 <code>(row+col) in diag2</code>，跳过</p>
<p class="code-step">4. 否则：登记三个集合、<code>queens[row]=col</code>，递归 <code>backtrack(row+1)</code></p>
<p class="code-step">5. 回溯：从三个集合中移除本次登记，继续尝试下一列</p>
<p class="code-step">6. 从 <code>backtrack(0)</code> 启动，返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        ans: list[list[str]] = []
        queens = [0] * n
        cols: set[int] = set()
        diag1: set[int] = set()   # row - col
        diag2: set[int] = set()   # row + col

        def backtrack(row: int) -> None:
            if row == n:
                board = []
                for r in range(n):
                    line = ['.'] * n
                    line[queens[r]] = 'Q'
                    board.append(''.join(line))
                ans.append(board)
                return
            for col in range(n):
                if col in cols or (row - col) in diag1 or (row + col) in diag2:
                    continue
                cols.add(col)
                diag1.add(row - col)
                diag2.add(row + col)
                queens[row] = col
                backtrack(row + 1)
                cols.remove(col)
                diag1.remove(row - col)
                diag2.remove(row + col)

        backtrack(0)
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<string>> solveNQueens(int n) {
        vector<vector<string>> ans;
        vector<int> queens(n, 0);
        unordered_set<int> cols, diag1, diag2;

        function<void(int)> backtrack = [&](int row) {
            if (row == n) {
                vector<string> board(n, string(n, '.'));
                for (int r = 0; r < n; ++r)
                    board[r][queens[r]] = 'Q';
                ans.push_back(move(board));
                return;
            }
            for (int col = 0; col < n; ++col) {
                if (cols.count(col) || diag1.count(row - col) || diag2.count(row + col))
                    continue;
                cols.insert(col);
                diag1.insert(row - col);
                diag2.insert(row + col);
                queens[row] = col;
                backtrack(row + 1);
                cols.erase(col);
                diag1.erase(row - col);
                diag2.erase(row + col);
            }
        };

        backtrack(0);
        return ans;
    }
};
// 时间 O(n!)，空间 O(n)（递归栈 + 集合，不计输出）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 回溯不撤销：放入皇后后递归返回，必须从 <code>cols/diag1/diag2</code> 中移除本次登记，否则污染兄弟分支。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 斜线判断写错：主对角线是 <code>row - col</code> 相同，副对角线是 <code>row + col</code> 相同；不要混用或漏判其中一种。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 输出格式：每行是长度为 n 的字符串，<code>'Q'</code> 与 <code>'.'</code> 组成；不是坐标列表，也不是二维字符数组的嵌套列表混用 int。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：n = 1</div>
    <code>n = 1 → [["Q"]]</code>（唯一一格放皇后）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：n = 2 或 3 无解</div>
    <code>n = 2 → []，n = 3 → []</code>（小棋盘不存在合法放置，应返回空列表）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：n = 4 两解</div>
    <code>n = 4 → 2 种棋盘</code>（经典样例，注意两种解互为镜像/旋转）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：n = 9 边界</div>
    <code>n = 9</code>（题目上限，回溯深度 9，需依赖剪枝）
</div>""",
    },
    "n-queens-ii": {
        "type": "回溯",
        "difficulty": "困难",
        "frontend_id": "52",
        "title": "N 皇后 II",
        "time_complexity": "O(n!)（剪枝后远好于 n^n 全枚举）",
        "space_complexity": "O(n)（递归栈 + 冲突集合）",
        "description": """<p><strong>n 皇后问题</strong> 研究的是如何将 <code>n</code> 个皇后放置在 <code>n×n</code> 的棋盘上，并且使皇后彼此之间不能相互攻击。</p>
<p>给你一个整数 <code>n</code>，返回 <strong>n 皇后问题</strong> 不同的解决方案的数量。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：n = 4</div>
    <div class="example-output">输出：2</div>
    <div class="example-explain">4 皇后问题存在两个不同的解法，如上图所示（同一行、列、斜线不能有两个皇后）。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：n = 1</div>
    <div class="example-output">输出：1</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>queens</code></td><td>int[n]</td><td><b>定义</b>：<code>queens[row]</code> 表示第 <code>row</code> 行皇后所在的列号<br><b>维护</b>：每行恰好放一个皇后，一维数组即可描述当前部分解<br><b>更新</b>：在 <code>row</code> 行尝试列 <code>col</code> 时令 <code>queens[row]=col</code>；回溯返回后该位置会被下一列覆盖</td></tr>
    <tr><td><code>cols</code></td><td>set&lt;int&gt;</td><td><b>定义</b>：已被占用的列号集合<br><b>维护</b>：任意时刻，已放置的皇后两两不同列<br><b>更新</b>：在 <code>(row,col)</code> 放皇后前查 <code>col not in cols</code>；放入时 <code>add(col)</code>，回溯时 <code>remove(col)</code></td></tr>
    <tr><td><code>diag1</code></td><td>set&lt;int&gt;</td><td><b>定义</b>：主对角线标识 <code>row - col</code> 的已占用集合（↘ 方向同线相等）<br><b>维护</b>：同一主对角线上任意两格 <code>row-col</code> 相同<br><b>更新</b>：放皇后前查 <code>(row-col) not in diag1</code>；放入/撤销与 <code>cols</code> 同步</td></tr>
    <tr><td><code>diag2</code></td><td>set&lt;int&gt;</td><td><b>定义</b>：副对角线标识 <code>row + col</code> 的已占用集合（↗ 方向同线相等）<br><b>维护</b>：同一副对角线上任意两格 <code>row+col</code> 相同<br><b>更新</b>：放皇后前查 <code>(row+col) not in diag2</code>；放入/撤销与 <code>cols</code> 同步</td></tr>
    <tr><td><code>row</code></td><td>int</td><td><b>定义</b>：当前待放置皇后的行号（从 0 到 n-1）<br><b>维护</b>：DFS 逐行向下推进，每行只尝试合法列<br><b>更新</b>：初始为 0；每成功放一行后 <code>row+1</code> 递归；<code>row==n</code> 时说明找到一种完整解</td></tr>
    <tr><td><code>count</code></td><td>int</td><td><b>定义</b>：合法完整解的总数<br><b>维护</b>：仅当 <code>row==n</code> 时加 1，无需构造棋盘字符串<br><b>更新</b>：每到达叶子层 <code>count += 1</code>；DFS 结束后返回 <code>count</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 我先想暴力：在 <code>n×n</code> 的每个格子里决定放或不放皇后，共 <code>2^{n²}</code> 种状态，再过滤出恰好 n 个皇后且互不攻击的——思路对，但状态空间巨大。</p>
<p class="thinking-step">2. 第一个剪枝：每行必须恰好一个皇后，问题变成「为每一行选一个列」，至多 <code>n^n</code> 种排列。</p>
<p class="thinking-step">3. 重复在哪里？按行放置时，很多列选法与已有皇后同列或同斜线冲突，却还要把后面所有行试完——和 #51 N 皇后完全相同的搜索树，只是本题不要求输出棋盘。</p>
<p class="thinking-step">4. 关键转化：用 <code>cols</code>、<code>diag1(row-col)</code>、<code>diag2(row+col)</code> 三个集合 O(1) 判断冲突；DFS 逐行枚举列，能放就递归下一行，<code>row==n</code> 时 <code>count+=1</code> 即可，不必构造字符串棋盘。</p>
<p class="thinking-step">5. 手推 n=4：搜索过程与 #51 一致，最终数到 2 种合法放置；<code>n=2/3</code> 时 <code>count=0</code>。<code>n≤9</code>，回溯深度 ≤ 9，完全可行。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>count = 0</code>、<code>queens = [0]*n</code>，以及空集合 <code>cols, diag1, diag2</code></p>
<p class="code-step">2. 定义 DFS <code>backtrack(row)</code>：若 <code>row == n</code>，<code>count += 1</code> 并返回</p>
<p class="code-step">3. 对 <code>col</code> 从 0 到 n-1：若 <code>col in cols</code> 或 <code>(row-col) in diag1</code> 或 <code>(row+col) in diag2</code>，跳过</p>
<p class="code-step">4. 否则：登记三个集合、<code>queens[row]=col</code>，递归 <code>backtrack(row+1)</code></p>
<p class="code-step">5. 回溯：从三个集合中移除本次登记，继续尝试下一列</p>
<p class="code-step">6. 从 <code>backtrack(0)</code> 启动，返回 <code>count</code></p>""",
        "code_python": """class Solution:
    def totalNQueens(self, n: int) -> int:
        count = 0
        queens = [0] * n
        cols: set[int] = set()
        diag1: set[int] = set()   # row - col
        diag2: set[int] = set()   # row + col

        def backtrack(row: int) -> None:
            nonlocal count
            if row == n:
                count += 1
                return
            for col in range(n):
                if col in cols or (row - col) in diag1 or (row + col) in diag2:
                    continue
                cols.add(col)
                diag1.add(row - col)
                diag2.add(row + col)
                queens[row] = col
                backtrack(row + 1)
                cols.remove(col)
                diag1.remove(row - col)
                diag2.remove(row + col)

        backtrack(0)
        return count""",
        "code_cpp": """class Solution {
public:
    int totalNQueens(int n) {
        int count = 0;
        vector<int> queens(n, 0);
        unordered_set<int> cols, diag1, diag2;

        function<void(int)> backtrack = [&](int row) {
            if (row == n) {
                ++count;
                return;
            }
            for (int col = 0; col < n; ++col) {
                if (cols.count(col) || diag1.count(row - col) || diag2.count(row + col))
                    continue;
                cols.insert(col);
                diag1.insert(row - col);
                diag2.insert(row + col);
                queens[row] = col;
                backtrack(row + 1);
                cols.erase(col);
                diag1.erase(row - col);
                diag2.erase(row + col);
            }
        };

        backtrack(0);
        return count;
    }
};
// 时间 O(n!)，空间 O(n)（递归栈 + 集合）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 回溯不撤销：放入皇后后递归返回，必须从 <code>cols/diag1/diag2</code> 中移除本次登记，否则污染兄弟分支、计数偏大。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 斜线判断写错：主对角线是 <code>row - col</code> 相同，副对角线是 <code>row + col</code> 相同；不要混用或漏判其中一种。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 本题只计数：到达 <code>row==n</code> 时 <code>count+=1</code> 即可，不要像 #51 那样构造棋盘字符串——多此一举且更慢。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：n = 1</div>
    <code>n = 1 → 1</code>（唯一一格放皇后，只有一种解）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：n = 2 或 3 无解</div>
    <code>n = 2 → 0，n = 3 → 0</code>（小棋盘不存在合法放置）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：n = 4 两解</div>
    <code>n = 4 → 2</code>（经典样例，与 #51 的解数一致）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：n = 9 边界</div>
    <code>n = 9</code>（题目上限，回溯深度 9，需依赖剪枝）
</div>""",
    },

    "maximum-subarray": {
        "type": "一维DP",
        "difficulty": "中等",
        "frontend_id": "53",
        "title": "最大子数组和",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个整数数组 <code>nums</code>，请你找出一个具有最大和的连续子数组（子数组最少包含一个元素），返回其最大和。</p>
<p><strong>子数组</strong> 是数组中的一个连续部分。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [-2,1,-3,4,-1,2,1,-5,4]</div>
    <div class="example-output">输出：6</div>
    <div class="example-explain">连续子数组 [4,-1,2,1] 的和最大，为 6。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [1]</div>
    <div class="example-output">输出：1</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：nums = [5,4,-1,7,8]</div>
    <div class="example-output">输出：23</div>
    <div class="example-explain">整个数组即为最大子数组，和为 23。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>cur</code></td><td>int</td><td><b>定义</b>：以当前下标 <code>i</code> <b>结尾</b> 的连续子数组的最大和<br><b>维护</b>：每扫到一个新元素，要么「接上前面的子数组」，要么「从当前元素重新开始」——取两者较大值<br><b>更新</b>：<code>cur = max(nums[i], cur + nums[i])</code>，即 Kadane 核心递推</td></tr>
    <tr><td><code>ans</code></td><td>int</td><td><b>定义</b>：遍历过程中见过的所有「以某位置结尾的子数组」中的全局最大和<br><b>维护</b>：每更新一次 <code>cur</code>，同步 <code>ans = max(ans, cur)</code><br><b>更新</b>：初始 <code>ans = nums[0]</code>（至少含一个元素），扫完返回 <code>ans</code></td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：从左到右扫描的下标，代表「当前考察的结尾位置」<br><b>维护</b>：<code>for i in range(1, n)</code>，第 0 个元素已用于初始化 <code>cur</code> 和 <code>ans</code><br><b>更新</b>：每轮用 <code>nums[i]</code> 更新 <code>cur</code>，再刷新 <code>ans</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：枚举所有连续子数组 <code>[l..r]</code>，对每个区间求和取最大，双重循环 O(n²)，<code>n=10⁵</code> 会超时。</p>
<p class="thinking-step">2. 重复在哪里？固定右端点 <code>r</code> 时，左端点 <code>l</code> 从 0 到 <code>r</code> 的区间和 <code>sum(l,r)</code> 可以从前一个 <code>sum(l,r-1)</code> 加上 <code>nums[r]</code> 得到——但更简单的是只关心「以 <code>r</code> 结尾」的最优子数组。</p>
<p class="thinking-step">3. 子问题定义：设 <code>dp[i]</code> = 以 <code>nums[i]</code> 结尾的连续子数组的最大和。则 <code>dp[i] = max(nums[i], dp[i-1] + nums[i])</code>——要么单独成段，要么接在前一段后面。</p>
<p class="thinking-step">4. 全局答案不在 <code>dp[n-1]</code>，而是 <code>max(dp[0..n-1])</code>：最优子数组可能结束在任意位置（如样例中结束在下标 6 而非末尾）。</p>
<p class="thinking-step">5. 手推 <code>[-2,1,-3,4,-1,2,1,-5,4]</code>：<code>cur</code> 依次为 -2→1→-2→4→3→5→6→1→5，<code>ans</code> 在扫到 6 时取到最大值 6，对应子数组 [4,-1,2,1]。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>cur = ans = nums[0]</code>（子数组至少含一个元素）</p>
<p class="code-step">2. 从下标 1 遍历到 <code>n-1</code></p>
<p class="code-step">3. 对每个 <code>nums[i]</code>：<code>cur = max(nums[i], cur + nums[i])</code>（接上 or 重启）</p>
<p class="code-step">4. 更新全局：<code>ans = max(ans, cur)</code></p>
<p class="code-step">5. 返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        cur = ans = nums[0]
        for i in range(1, len(nums)):
            cur = max(nums[i], cur + nums[i])
            ans = max(ans, cur)
        return ans""",
        "code_cpp": """class Solution {
public:
    int maxSubArray(vector<int>& nums) {
        int cur = nums[0], ans = nums[0];
        for (int i = 1; i < nums.size(); i++) {
            cur = max(nums[i], cur + nums[i]);
            ans = max(ans, cur);
        }
        return ans;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 答案不是 <code>dp[n-1]</code>：最大子数组可以结束在任意位置，必须全程维护 <code>ans = max(ans, cur)</code>，不能只返回最后一次的 <code>cur</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 全负数数组：如 <code>[-3,-2,-1]</code>，<code>cur</code> 会不断被 <code>max(nums[i], ...)</code> 重置为当前元素，<code>ans</code> 应取最大的那个负数（-1），不能返回 0。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 初始化勿用 <code>cur=0</code>：子数组至少包含一个元素，应从 <code>nums[0]</code> 开始；若 <code>cur</code> 初值为 0，全正数组虽能蒙对，全负时会错成 0。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单元素</div>
    <code>nums = [1] → 1</code>（唯一子数组即自身）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全负数</div>
    <code>nums = [-3, -2, -1] → -1</code>（必须选一个元素，取最大负数）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：全正数</div>
    <code>nums = [5, 4, -1, 7, 8] → 23</code>（整个数组即最优，无需截断）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：中间最优段</div>
    <code>nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4] → 6</code>（最优子数组不贴首尾）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：前缀拖累</div>
    <code>nums = [-1, -2, 5, -1, 3] → 7</code>（前面负前缀应被丢弃，从 5 重启）
</div>""",
    },

    "spiral-matrix": {
        "type": "矩阵操作",
        "difficulty": "中等",
        "frontend_id": "54",
        "title": "螺旋矩阵",
        "time_complexity": "O(m × n)",
        "space_complexity": "O(1)（不计输出数组）",
        "description": """<p>给你一个 <code>m</code> 行 <code>n</code> 列的矩阵 <code>matrix</code>，请按照 <strong>顺时针螺旋顺序</strong>，返回矩阵中的所有元素。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：matrix = [[1,2,3],[4,5,6],[7,8,9]]</div>
    <div class="example-output">输出：[1,2,3,6,9,8,7,4,5]</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]</div>
    <div class="example-output">输出：[1,2,3,4,8,12,11,10,9,5,6,7]</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>ans</code></td><td>list&lt;int&gt;</td><td><b>定义</b>：按顺时针螺旋顺序收集到的所有元素<br><b>维护</b>：每走完一条边，就把该边上尚未访问的元素依次追加到 <code>ans</code><br><b>更新</b>：四条边（上→右→下→左）各扫一遍后，<code>ans</code> 长度增加当前「剩余矩形」的周长对应元素数</td></tr>
    <tr><td><code>top, bottom</code></td><td>int</td><td><b>定义</b>：当前待遍历子矩阵的上、下边界行号（含端点）<br><b>维护</b>：每完成一圈螺旋后，<code>top++</code>、<code>bottom--</code>，向内收缩一行<br><b>更新</b>：初始 <code>top=0, bottom=m-1</code>；当 <code>top &gt; bottom</code> 时纵向已无剩余行，停止</td></tr>
    <tr><td><code>left, right</code></td><td>int</td><td><b>定义</b>：当前待遍历子矩阵的左、右边界列号（含端点）<br><b>维护</b>：每完成一圈螺旋后，<code>left++</code>、<code>right--</code>，向内收缩一列<br><b>更新</b>：初始 <code>left=0, right=n-1</code>；当 <code>left &gt; right</code> 时横向已无剩余列，停止</td></tr>
    <tr><td><code>i, j</code></td><td>int</td><td><b>定义</b>：沿当前边扫描时的行、列下标<br><b>维护</b>：上边从左到右、右边从上到下、下边从右到左、左边从下到上，各用一层 <code>for</code> 推进<br><b>更新</b>：每访问 <code>matrix[i][j]</code> 后立即 <code>ans.append(...)</code>，避免重复访问</td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：按螺旋路径手写坐标变化——从 <code>(0,0)</code> 出发，方向依次为右、下、左、上，遇边界或已访问格就转向；需要 <code>visited[m][n]</code> 防重复，时间 O(mn)，额外空间 O(mn)。</p>
<p class="thinking-step">2. 重复在哪里？方向数组解法每走一步都要判「是否出界 / 是否已访问」，逻辑分散在四个分支里，单行或单列时特别容易多走或漏走。</p>
<p class="thinking-step">3. 关键转化：把螺旋看成<strong>一圈圈剥洋葱</strong>——每一圈固定走四条边：顶行从左到右、右列从上到下、底行从右到左（若还有多行）、左列从下到上（若还有多列），然后四条边界各向内缩 1。</p>
<p class="thinking-step">4. 手推 3×3：第一圈收集 1,2,3 → 6,9 → 8,7 → 4；收缩后只剩中心 5，第二圈顶行单独收集 5，得到 [1,2,3,6,9,8,7,4,5]。</p>
<p class="thinking-step">5. 边界条件：底行仅在 <code>top &lt; bottom</code> 时遍历（避免与顶行重复）；左列仅在 <code>left &lt; right</code> 时遍历（避免与右列重复）。单行或单列矩阵靠这两条判断自然处理。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>matrix</code> 为空直接返回 <code>[]</code>；取 <code>m, n</code>，初始化 <code>top=0, bottom=m-1, left=0, right=n-1</code> 与空列表 <code>ans</code></p>
<p class="code-step">2. 当 <code>top &lt;= bottom</code> 且 <code>left &lt;= right</code> 时循环（当前还有未访问的子矩形）</p>
<p class="code-step">3. <strong>上边</strong>：<code>for j in range(left, right+1)</code>，收集 <code>matrix[top][j]</code></p>
<p class="code-step">4. <strong>右边</strong>：<code>for i in range(top+1, bottom+1)</code>，收集 <code>matrix[i][right]</code></p>
<p class="code-step">5. 若 <code>top &lt; bottom</code>，<strong>下边</strong>从 <code>right-1</code> 到 <code>left</code> 逆序收集 <code>matrix[bottom][j]</code></p>
<p class="code-step">6. 若 <code>left &lt; right</code>，<strong>左边</strong>从 <code>bottom-1</code> 到 <code>top+1</code> 逆序收集 <code>matrix[i][left]</code></p>
<p class="code-step">7. 收缩边界 <code>top++, bottom--, left++, right--</code>，进入下一圈</p>
<p class="code-step">8. 返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        if not matrix or not matrix[0]:
            return []
        m, n = len(matrix), len(matrix[0])
        top, bottom = 0, m - 1
        left, right = 0, n - 1
        ans: list[int] = []

        while top <= bottom and left <= right:
            # 上边：从左到右
            for j in range(left, right + 1):
                ans.append(matrix[top][j])
            # 右边：从上到下（跳过顶角，已在上边收集）
            for i in range(top + 1, bottom + 1):
                ans.append(matrix[i][right])
            # 下边：从右到左（仅当还有多行时）
            if top < bottom:
                for j in range(right - 1, left - 1, -1):
                    ans.append(matrix[bottom][j])
            # 左边：从下到上（仅当还有多列时）
            if left < right:
                for i in range(bottom - 1, top, -1):
                    ans.append(matrix[i][left])
            top += 1
            bottom -= 1
            left += 1
            right -= 1

        return ans""",
        "code_cpp": """class Solution {
public:
    vector<int> spiralOrder(vector<vector<int>>& matrix) {
        vector<int> ans;
        if (matrix.empty() || matrix[0].empty()) return ans;
        int m = matrix.size(), n = matrix[0].size();
        int top = 0, bottom = m - 1, left = 0, right = n - 1;

        while (top <= bottom && left <= right) {
            // 上边：从左到右
            for (int j = left; j <= right; j++)
                ans.push_back(matrix[top][j]);
            // 右边：从上到下
            for (int i = top + 1; i <= bottom; i++)
                ans.push_back(matrix[i][right]);
            // 下边：从右到左（仅当还有多行）
            if (top < bottom) {
                for (int j = right - 1; j >= left; j--)
                    ans.push_back(matrix[bottom][j]);
            }
            // 左边：从下到上（仅当还有多列）
            if (left < right) {
                for (int i = bottom - 1; i > top; i--)
                    ans.push_back(matrix[i][left]);
            }
            top++;
            bottom--;
            left++;
            right--;
        }
        return ans;
    }
};
// 时间 O(m×n)，空间 O(1)（不计输出）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记「单行/单列」判断：走完顶行和右列后，若 <code>top == bottom</code> 仍遍历底行，会把同一行元素重复加入；必须用 <code>if (top &lt; bottom)</code> 和 <code>if (left &lt; right)</code> 保护。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 方向数组 + <code>visited</code> 写法里，转向时机写错会导致死循环或漏元素；剥洋葱法用边界收缩，每格恰好访问一次，更不易错。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 右边循环应从 <code>top+1</code> 开始、左边从 <code>bottom-1</code> 到 <code>top+1</code>，否则四个角的元素会被重复收集。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单行</div>
    <code>matrix = [[1,2,3,4]] → [1,2,3,4]</code>（只走顶边，<code>top==bottom</code> 跳过底边）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：单列</div>
    <code>matrix = [[1],[2],[3]] → [1,2,3]</code>（顶边后只走右列，<code>left==right</code> 跳过左边）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：1×1</div>
    <code>matrix = [[7]] → [7]</code>（一圈只收集一个元素）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：3×3 奇数方阵</div>
    <code>matrix = [[1,2,3],[4,5,6],[7,8,9]] → [1,2,3,6,9,8,7,4,5]</code>（中心 5 在第二圈单独收集）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：3×4 长方形</div>
    <code>matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]] → [1,2,3,4,8,12,11,10,9,5,6,7]</code>（非方阵同样适用边界收缩）
</div>""",
    },

    "jump-game": {
        "type": "贪心",
        "difficulty": "中等",
        "frontend_id": "55",
        "title": "跳跃游戏",
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "description": """<p>给你一个非负整数数组 <code>nums</code>，你最初位于数组的 <strong>第一个下标</strong>。数组中的每个元素代表你在该位置可以跳跃的最大长度。</p>
<p>判断你是否能够到达最后一个下标，如果可以，返回 <code>true</code>；否则，返回 <code>false</code>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：nums = [2,3,1,1,4]</div>
    <div class="example-output">输出：true</div>
    <div class="example-explain">可以先跳 1 步，从下标 0 到达下标 1，然后再从下标 1 跳 3 步到达最后一个下标。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：nums = [3,2,1,0,4]</div>
    <div class="example-output">输出：false</div>
    <div class="example-explain">无论怎样，总会到达下标为 3 的位置。但该下标的最大跳跃长度是 0，所以永远不可能到达最后一个下标。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>farthest</code></td><td>int</td><td><b>定义</b>：从起点出发，经过若干次合法跳跃后，<strong>最远能到达的下标</strong>（含该位置）<br><b>维护</b>：从左到右扫描时，每到一个可达位置 <code>i</code>，用 <code>i + nums[i]</code> 尝试扩展 <code>farthest</code><br><b>更新</b>：<code>farthest = max(farthest, i + nums[i])</code>；若最终 <code>farthest ≥ n-1</code> 则可达终点</td></tr>
    <tr><td><code>i</code></td><td>int</td><td><b>定义</b>：从左到右扫描的下标，代表「当前正在考察的落脚点」<br><b>维护</b>：<code>for i in range(n)</code>，只处理 <code>i ≤ farthest</code> 的位置（超出则说明此点不可达）<br><b>更新</b>：每轮用 <code>nums[i]</code> 更新 <code>farthest</code>；若 <code>i &gt; farthest</code> 提前返回 <code>false</code></td></tr>
    <tr><td><code>nums[i]</code></td><td>int</td><td><b>定义</b>：从下标 <code>i</code> 出发单次跳跃的最大步长<br><b>维护</b>：仅当 <code>i</code> 可达（<code>i ≤ farthest</code>）时才参与扩展<br><b>更新</b>：与 <code>i</code> 相加得到从 <code>i</code> 出发能跳到的最远下标，用于刷新 <code>farthest</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：从每个位置 DFS/BFS 枚举所有合法跳跃路径，看能否到达 <code>n-1</code>，状态空间指数级，<code>n=10⁴</code> 会超时。</p>
<p class="thinking-step">2. 重复在哪里？「从位置 <code>i</code> 能否到达终点」会被反复计算——典型 DP：<code>dp[i] = any(dp[j])</code> 对所有 <code>j&lt;i</code> 且 <code>j+nums[j]≥i</code>，朴素 O(n²)。</p>
<p class="thinking-step">3. 换个视角：我们不需要知道「最少几步」，只需知道「最远能到哪」——从左到右扫描，维护一个全局最远可达下标 <code>farthest</code>。</p>
<p class="thinking-step">4. 贪心关键：若当前 <code>i &gt; farthest</code>，说明连位置 <code>i</code> 都到不了，后面更不可能；否则用 <code>i + nums[i]</code> 扩展 <code>farthest</code>，扫完后看 <code>farthest</code> 是否 ≥ <code>n-1</code>。</p>
<p class="thinking-step">5. 正确性直觉：<code>farthest</code> 单调不减，且包含了「从起点经任意合法路径能到达的所有位置」的上界；一旦 <code>farthest ≥ n-1</code> 即存在一条路径到终点。</p>""",
        "code_steps": """<p class="code-step">1. 初始化 <code>farthest = 0</code>，<code>n = len(nums)</code></p>
<p class="code-step">2. 遍历 <code>i</code> 从 0 到 <code>n-1</code></p>
<p class="code-step">3. 若 <code>i &gt; farthest</code>，说明当前位置不可达，返回 <code>false</code></p>
<p class="code-step">4. 更新 <code>farthest = max(farthest, i + nums[i])</code></p>
<p class="code-step">5. 若 <code>farthest ≥ n-1</code>，可提前返回 <code>true</code>（可选优化）</p>
<p class="code-step">6. 循环结束返回 <code>true</code>（能扫完说明终点可达）</p>""",
        "code_python": """class Solution:
    def canJump(self, nums: List[int]) -> bool:
        farthest = 0
        n = len(nums)
        for i in range(n):
            if i > farthest:
                return False
            farthest = max(farthest, i + nums[i])
            if farthest >= n - 1:
                return True
        return True""",
        "code_cpp": """class Solution {
public:
    bool canJump(vector<int>& nums) {
        int farthest = 0;
        int n = nums.size();
        for (int i = 0; i < n; i++) {
            if (i > farthest) return false;
            farthest = max(farthest, i + nums[i]);
            if (farthest >= n - 1) return true;
        }
        return true;
    }
};
// 时间 O(n)，空间 O(1)""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记判断 <code>i &gt; farthest</code>：只更新 <code>farthest</code> 而不检查当前位置是否可达，会在 <code>[3,2,1,0,4]</code> 这类用例上误判为 <code>true</code>。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 本题求<b>能否到达</b>，与 #45「跳跃游戏 II」（求最少跳跃次数）不同；后者需要按层结算 <code>steps</code>，不能混用。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> <code>nums[i]</code> 可以为 0：站在 0 步长处仍算「到达该位置」，只是无法继续向前扩展 <code>farthest</code>。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单元素</div>
    <code>nums = [0] → true</code>（已在终点，无需跳跃）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：一步直达</div>
    <code>nums = [1, 0] → true</code>（从下标 0 跳 1 步到终点）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：卡在中途</div>
    <code>nums = [3, 2, 1, 0, 4] → false</code>（最远只能到下标 3，<code>nums[3]=0</code> 无法继续前进）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：含零步长</div>
    <code>nums = [2, 0, 0, 1] → true</code>（经过若干 0 步长位置仍可到达终点）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：大跨度</div>
    <code>nums = [5, 0, 0, 0, 0] → true</code>（第一步即可覆盖全程）
</div>""",
    },
    "merge-intervals": {
        "type": "区间合并",
        "difficulty": "中等",
        "frontend_id": "56",
        "title": "合并区间",
        "time_complexity": "O(n log n)",
        "space_complexity": "O(log n)（排序栈空间，不计输出）",
        "description": """<p>以数组 <code>intervals</code> 表示若干个区间的集合，其中单个区间为 <code>intervals[i] = [start<sub>i</sub>, end<sub>i</sub>]</code>。请你合并所有重叠的区间，并返回 <em>一个不重叠的区间数组，该数组需恰好覆盖输入中的所有区间</em>。</p>""",
        "examples": """<div class="example-block">
    <h4>示例 1</h4>
    <div class="example-input">输入：intervals = [[1,3],[2,6],[8,10],[15,18]]</div>
    <div class="example-output">输出：[[1,6],[8,10],[15,18]]</div>
    <div class="example-explain">区间 [1,3] 和 [2,6] 重叠，将它们合并为 [1,6]。</div>
</div>
<div class="example-block">
    <h4>示例 2</h4>
    <div class="example-input">输入：intervals = [[1,4],[4,5]]</div>
    <div class="example-output">输出：[[1,5]]</div>
    <div class="example-explain">区间 [1,4] 和 [4,5] 可被视为重叠区间（端点相接也算重叠）。</div>
</div>
<div class="example-block">
    <h4>示例 3</h4>
    <div class="example-input">输入：intervals = [[4,7],[1,4]]</div>
    <div class="example-output">输出：[[1,7]]</div>
    <div class="example-explain">输入顺序不影响结果；排序后 [1,4] 与 [4,7] 端点相接，合并为 [1,7]。</div>
</div>""",
        "var_semantics": """<table class="var-table">
    <thead><tr><th>变量</th><th>类型</th><th>语义（三句法）</th></tr></thead>
    <tbody>
    <tr><td><code>intervals</code></td><td>list&lt;list&lt;int&gt;&gt;</td><td><b>定义</b>：输入的区间集合，每个元素为 <code>[start, end]</code><br><b>维护</b>：处理前先按 <code>start</code> 升序排序，保证从左到右扫描时「当前区间起点 ≥ 已处理区间的起点」<br><b>更新</b>：<code>intervals.sort(key=lambda x: x[0])</code>；排序后线性扫描，不再回退</td></tr>
    <tr><td><code>ans</code></td><td>list&lt;list&lt;int&gt;&gt;</td><td><b>定义</b>：已合并完成的不重叠区间列表（输出结果）<br><b>维护</b>：始终按起点递增排列，且相邻区间互不相交<br><b>更新</b>：首个区间直接入 <code>ans</code>；后续若与 <code>ans[-1]</code> 重叠则扩展 <code>ans[-1][1]</code>，否则 append 新区间</td></tr>
    <tr><td><code>cur</code></td><td>list&lt;int&gt;</td><td><b>定义</b>：当前正在考察的区间 <code>[start, end]</code>（排序后的 <code>intervals[i]</code>）<br><b>维护</b>：每次循环取一个尚未并入 <code>ans</code> 的区间，与 <code>ans</code> 末尾比较<br><b>更新</b>：若 <code>cur[0] &lt;= ans[-1][1]</code> 则重叠，合并；否则 <code>ans.append(cur)</code></td></tr>
    <tr><td><code>ans[-1][1]</code></td><td>int</td><td><b>定义</b>：当前已合并块的最右端点（右边界）<br><b>维护</b>：合并时取 <code>max(原右端, cur[1])</code>，因为 <code>cur</code> 可能完全包含在块内也可能向右延伸<br><b>更新</b>：<code>ans[-1][1] = max(ans[-1][1], cur[1])</code></td></tr>
    </tbody>
</table>""",
        "thinking_steps": """<p class="thinking-step">1. 最直接：枚举所有区间对的交集关系，用并查集或图连通分量把「能互相重叠到达」的区间归为一组，再每组取 min(start) 和 max(end)——思路正确但实现繁琐，且 O(n²) 判重叠。</p>
<p class="thinking-step">2. 重复在哪里？若区间已按起点排序，判断「当前区间是否与已有合并块重叠」只需看 <strong>最后一个合并块</strong>，不必回溯检查 <code>ans</code> 中更早的区间——因为排序后若与更早块重叠，早就被合并进同一块了。</p>
<p class="thinking-step">3. 关键转化：先按 <code>start</code> 排序，再线性扫描。维护 <code>ans</code> 中最后一个区间；若 <code>cur[0] &lt;= ans[-1][1]</code> 说明重叠（含端点相接），扩展右端；否则开新区间。</p>
<p class="thinking-step">4. 重叠判定：排序后 <code>cur[0] &gt; ans[-1][1]</code> 即完全不重叠；否则合并。注意 <code>[1,4]</code> 与 <code>[4,5]</code> 中 <code>4 &lt;= 4</code> 算重叠，输出 <code>[1,5]</code>。</p>
<p class="thinking-step">5. 复杂度：排序 O(n log n) 主导；扫描 O(n)。空间除输出外主要是排序的 O(log n) 栈。</p>""",
        "code_steps": """<p class="code-step">1. 若 <code>intervals</code> 为空，直接返回空列表</p>
<p class="code-step">2. 按每个区间的起点 <code>intervals[i][0]</code> 升序排序</p>
<p class="code-step">3. 初始化 <code>ans = [intervals[0]]</code></p>
<p class="code-step">4. 遍历 <code>intervals[1:]</code> 中的每个 <code>cur</code></p>
<p class="code-step">5. 若 <code>cur[0] &lt;= ans[-1][1]</code>，重叠：更新 <code>ans[-1][1] = max(ans[-1][1], cur[1])</code></p>
<p class="code-step">6. 否则 <code>ans.append(cur)</code>，开始新的合并块</p>
<p class="code-step">7. 返回 <code>ans</code></p>""",
        "code_python": """class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        if not intervals:
            return []
        intervals.sort(key=lambda x: x[0])
        ans = [intervals[0]]
        for cur in intervals[1:]:
            if cur[0] <= ans[-1][1]:
                ans[-1][1] = max(ans[-1][1], cur[1])
            else:
                ans.append(cur)
        return ans""",
        "code_cpp": """class Solution {
public:
    vector<vector<int>> merge(vector<vector<int>>& intervals) {
        if (intervals.empty()) return {};
        sort(intervals.begin(), intervals.end(),
             [](const vector<int>& a, const vector<int>& b) {
                 return a[0] < b[0];
             });
        vector<vector<int>> ans;
        ans.push_back(intervals[0]);
        for (int i = 1; i < intervals.size(); i++) {
            auto& cur = intervals[i];
            if (cur[0] <= ans.back()[1]) {
                ans.back()[1] = max(ans.back()[1], cur[1]);
            } else {
                ans.push_back(cur);
            }
        }
        return ans;
    }
};
// 时间 O(n log n)，空间 O(log n)（排序栈，不计输出）""",
        "pitfalls": """<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 忘记排序：输入顺序任意（如示例 3 <code>[[4,7],[1,4]]</code>），不排序就无法用「只看最后一个合并块」的线性策略。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 重叠条件写错：本题端点相接算重叠，应是 <code>cur[0] &lt;= ans[-1][1]</code>，不能写成 <code>&lt;</code>，否则 <code>[1,4],[4,5]</code> 无法合并。</p>
<p class="pitfall-item"><span class="pitfall-icon">&#x2757;</span> 合并时只取 <code>cur[1]</code> 而不与 <code>ans[-1][1]</code> 取 max：当 <code>cur</code> 完全落在已有块内部时（如 <code>[1,10]</code> 后跟 <code>[2,3]</code>），右端点会被错误缩短。</p>""",
        "edge_cases": """<div class="edge-case">
    <div class="edge-label">Case 1：单个区间</div>
    <code>intervals = [[1,4]] → [[1,4]]</code>（无需合并，直接返回）
</div>
<div class="edge-case">
    <div class="edge-label">Case 2：全部重叠成一块</div>
    <code>intervals = [[1,4],[2,3],[3,6]] → [[1,6]]</code>（排序后依次合并）
</div>
<div class="edge-case">
    <div class="edge-label">Case 3：端点相接</div>
    <code>intervals = [[1,4],[4,5]] → [[1,5]]</code>（<code>4 &lt;= 4</code> 视为重叠）
</div>
<div class="edge-case">
    <div class="edge-label">Case 4：互不重叠</div>
    <code>intervals = [[1,2],[3,4],[5,6]] → [[1,2],[3,4],[5,6]]</code>（每个区间独立成块）
</div>
<div class="edge-case">
    <div class="edge-label">Case 5：乱序输入</div>
    <code>intervals = [[4,7],[1,4]] → [[1,7]]</code>（排序后与前述逻辑一致）
</div>""",
    },
}


def get_problem_semantics(slug: str) -> Optional[dict]:
    """获取预置的变量语义数据（仅精讲题库中的题目有）"""
    return VAR_SEMANTICS_DATA.get(slug)


_POOL_CACHE: Optional[list] = None


def load_pool() -> list:
    """加载候选题库（LeetCode 前 200 题），跳过会员专享题（免费 API 取不到）。

    返回按题号升序的列表，每项含 id / slug / title_en / difficulty。
    """
    global _POOL_CACHE
    if _POOL_CACHE is not None:
        return _POOL_CACHE
    pool: list = []
    if POOL_FILE.exists():
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        pool = [p for p in raw if not p.get("paid_only")]
        pool.sort(key=lambda p: p.get("id", 0))
    _POOL_CACHE = pool
    return pool


def _pool_slug_to_meta() -> dict:
    return {p["slug"]: p for p in load_pool()}


# 英文/中文难度 → 中文难度
_DIFF_ZH = {
    "Easy": "简单", "Medium": "中等", "Hard": "困难",
    "简单": "简单", "中等": "中等", "困难": "困难",
}
_DIFF_CLASS = {"简单": "easy", "中等": "medium", "困难": "hard"}


def resolve_difficulty(slug: str, html_content: str = None, semantics: dict = None) -> str:
    """解析题目难度（中文）。优先级：显式 semantics → 精讲库 → 候选池 → 归档页 HTML → 默认中等。"""
    if semantics and semantics.get("difficulty"):
        return _DIFF_ZH.get(semantics["difficulty"], "中等")
    data = VAR_SEMANTICS_DATA.get(slug)
    if data and data.get("difficulty"):
        return _DIFF_ZH.get(data["difficulty"], "中等")
    meta = _pool_slug_to_meta().get(slug)
    if meta and meta.get("difficulty"):
        return _DIFF_ZH.get(meta["difficulty"], "中等")
    if html_content:
        m = re.search(r'problem-difficulty[^>]*>\s*(简单|中等|困难)', html_content)
        if m:
            return m.group(1)
    return "中等"


def build_semantics_from_leetcode(slug: str) -> Optional[dict]:
    """题库中没有精讲的题目：实时从 LeetCode 拉取官方中文题面 + 代码片段，
    组装成 render_template / 语音生成可用的字典。

    精讲专属字段（变量语义 / 思考 / 落码步骤 / 坑 / 边界 / 复杂度）留空，
    模板会自动省略这些区块。拉取失败返回 None。
    """
    try:
        from scripts.leetcode_api import fetch_problem_detail
        q = fetch_problem_detail(slug)
    except Exception as e:
        print(f"⚠ 拉取 LeetCode 题目 {slug} 失败: {e}")
        return None
    if not q or not q.get("questionFrontendId"):
        return None

    snippets = {s.get("langSlug"): s.get("code", "") for s in (q.get("codeSnippets") or [])}
    code_python = snippets.get("python3") or snippets.get("python") or ""
    code_cpp = snippets.get("cpp") or ""

    tags = q.get("topicTags") or []
    ptype = (tags[0].get("translatedName") or tags[0].get("name")) if tags else "算法题"

    return {
        "title": q.get("translatedTitle") or q.get("title") or slug,
        "frontend_id": str(q.get("questionFrontendId", "")),
        "type": ptype or "算法题",
        "difficulty": _DIFF_ZH.get(q.get("difficulty", ""), "中等"),
        "time_complexity": "",
        "space_complexity": "",
        # translatedContent 已包含题面 + 示例，整体作为描述展示
        "description": q.get("translatedContent") or "",
        "examples": "",
        "var_semantics": "",
        "thinking_steps": "",
        "code_steps": "",
        "code_python": code_python,
        "code_cpp": code_cpp,
        "pitfalls": "",
        "edge_cases": "",
    }


def _html_escape(text: str) -> str:
    """转义代码中的 < > &，避免 vector<int> 之类被当成 HTML 标签吞掉。"""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _frontend_id_to_slug() -> dict[str, str]:
    """题号 → slug 映射（精讲题库 + 候选题池，用于从归档页重建历史）"""
    mapping = {data["frontend_id"]: slug for slug, data in VAR_SEMANTICS_DATA.items()}
    for p in load_pool():
        mapping.setdefault(str(p.get("id", "")), p.get("slug", ""))
    return mapping


def rebuild_history_from_archives() -> list:
    """从 docs/archive/ 已发布页面重建推荐历史（Git 持久化的真实来源）"""
    id_to_slug = _frontend_id_to_slug()
    history = []
    if not ARCHIVE.exists():
        return history

    for path in sorted(ARCHIVE.glob("*.html")):
        date_str = path.stem
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
            continue
        content = path.read_text(encoding="utf-8")
        match = re.search(r'problem-id">#(\d+)<', content)
        if not match:
            continue
        slug = id_to_slug.get(match.group(1))
        if not slug:
            continue
        semantics = VAR_SEMANTICS_DATA.get(slug)
        if semantics:
            title = semantics.get("title", slug)
            ptype = semantics.get("type", "")
        else:
            # 池内非精讲题：标题从归档页里抓，题型无法确定
            title_match = re.search(r'class="problem-title">([^<]+)<', content)
            title = title_match.group(1).strip() if title_match else slug
            ptype = ""
        history.append({
            "date": date_str,
            "slug": slug,
            "title": title,
            "type": ptype,
            "difficulty": resolve_difficulty(slug, html_content=content, semantics=semantics),
        })
    return history


def load_history() -> list:
    """加载推荐历史，合并 history.json 与 archive 页面（archive 优先）"""
    file_history = []
    path = DATA / "history.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            file_history = json.load(f)

    merged: dict[str, dict] = {}
    for item in file_history:
        merged[item.get("date", "")] = item
    for item in rebuild_history_from_archives():
        prev = merged.get(item["date"], {})
        # archive 重建可能缺 type（非精讲题）；保留文件里已有字段
        if not item.get("type") and prev.get("type"):
            item = {**item, "type": prev["type"]}
        if not item.get("difficulty") and prev.get("difficulty"):
            item = {**item, "difficulty": prev["difficulty"]}
        merged[item["date"]] = item

    result = sorted(merged.values(), key=lambda x: x.get("date", ""))
    for item in result:
        if not item.get("difficulty"):
            item["difficulty"] = resolve_difficulty(item.get("slug", ""))
    return result


def save_history(history: list):
    """保存推荐历史"""
    DATA.mkdir(parents=True, exist_ok=True)
    with open(DATA / "history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _last_used_map(history: list) -> dict:
    """slug -> 最近一次被推荐的日期"""
    last_used: dict[str, str] = {}
    for item in history:
        s = item.get("slug", "")
        d = item.get("date", "")
        if s and d > last_used.get(s, ""):
            last_used[s] = d
    return last_used


def select_problem(use_api: bool = False, use_bank: bool = True) -> tuple:
    """选择今日推荐的题目。返回 (slug, source) 或 (None, None)。

    候选题库是 LeetCode 前 200 题（data/problem_pool.json）。优先选题号最小的
    未推荐过的题；全部推荐过后，按「最久未推荐」轮换，保证约 200 天内不重复、
    且绝不会连续两天推荐同一道题。
    """
    history = load_history()
    used_slugs = {item.get("slug", "") for item in history}
    pool = load_pool()

    # 策略 1：按题号顺序，从候选题库里选第一道还没推荐过的题
    if use_bank and pool:
        for entry in pool:
            if entry["slug"] not in used_slugs:
                return (entry["slug"], "pool")

    # 策略 2：可选地尝试 LeetCode API（每日一题 / 热门题）
    if use_api:
        try:
            from scripts.leetcode_api import fetch_hot_problems, fetch_daily_problem
            daily = fetch_daily_problem()
            daily_slug = daily.get("titleSlug", "")
            if daily_slug and daily_slug not in used_slugs:
                return (daily_slug, "api-daily")

            hot = fetch_hot_problems(limit=50)
            for p in hot:
                slug = p.get("titleSlug", "")
                if slug and slug not in used_slugs:
                    return (slug, "api-hot")
        except Exception:
            pass

    # 策略 3：候选题库全部推荐过 → 轮换「最久未推荐」的题目
    # （不能永远返回第一题，否则题库用完后每天都推荐同一道题造成重复）
    if use_bank and pool:
        last_used = _last_used_map(history)
        # 按 (最近推荐日期, 题号) 升序取第一个：最久没推荐的排最前，平局按题号。
        best = min(pool, key=lambda e: (last_used.get(e["slug"], ""), e.get("id", 0)))
        return (best["slug"], "pool-cycle")

    # 兜底：候选题库不可用时，回退到精讲题库轮换
    if use_bank and VAR_SEMANTICS_DATA:
        slugs = list(VAR_SEMANTICS_DATA.keys())
        last_used = _last_used_map(history)
        best_idx, best_slug = min(
            enumerate(slugs),
            key=lambda pair: (last_used.get(pair[1], ""), pair[0]),
        )
        return (best_slug, "bank-cycle")

    return (None, None)


def render_template(slug: str, semantics: dict, date_str: str = None, has_audio: bool = False) -> str:
    """将变量语义数据填充到 HTML 模板中"""
    if date_str is None:
        date_str = date.today().isoformat()

    from scripts.generate_audio import render_audio_section, AUDIO_SCRIPT_JS

    template_path = TEMPLATES / "problem.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    ptype = semantics.get("type", "")
    diff = semantics.get("difficulty", "中等")
    type_class = TYPE_CLASS_MAP.get(ptype, "other")
    diff_class = {
        "简单": "easy", "中等": "medium", "困难": "hard",
        "Easy": "easy", "Medium": "medium", "Hard": "hard",
    }.get(diff, "medium")

    replacements = {
        "{{TITLE}}": semantics.get("title", slug),
        "{{FRONTEND_ID}}": semantics.get("frontend_id", ""),
        "{{SLUG}}": slug,
        "{{DATE}}": date_str,
        "{{PROBLEM_TYPE}}": ptype,
        "{{DIFFICULTY}}": diff,
        "{{TYPE_CLASS}}": type_class,
        "{{DIFFICULTY_CLASS}}": diff_class,
        "{{DESCRIPTION}}": semantics.get("description", ""),
        "{{EXAMPLES}}": semantics.get("examples", ""),
        "{{VAR_SEMANTICS}}": semantics.get("var_semantics", ""),
        "{{THINKING_STEPS}}": semantics.get("thinking_steps", ""),
        "{{CODE_STEPS}}": semantics.get("code_steps", ""),
        "{{CODE_PYTHON}}": _html_escape(semantics.get("code_python", "")),
        "{{CODE_CPP}}": _html_escape(semantics.get("code_cpp", "")),
        "{{TIME_COMPLEXITY}}": semantics.get("time_complexity", ""),
        "{{SPACE_COMPLEXITY}}": semantics.get("space_complexity", ""),
        "{{PITFALLS}}": semantics.get("pitfalls", ""),
        "{{EDGE_CASES}}": semantics.get("edge_cases", ""),
        "{{AUDIO_SECTION}}": render_audio_section(date_str) if has_audio else "",
        "{{AUDIO_SCRIPT}}": AUDIO_SCRIPT_JS if has_audio else "",
    }

    # 省略没有内容的可选区块（自动出页的题目通常只有题面 + 官方代码）
    template = _strip_empty_sections(template, semantics)

    for key, value in replacements.items():
        template = template.replace(key, value)

    return template


# 可选区块标记 → 判断是否为空所依据的 semantics 字段
_OPTIONAL_SECTIONS = {
    "THINKING": ["thinking_steps"],
    "VARSEM": ["var_semantics"],
    "CODESTEPS": ["code_steps"],
    "CODE": ["code_python", "code_cpp"],
    "COMPLEXITY": ["time_complexity", "space_complexity"],
    "PITFALLS": ["pitfalls"],
    "EDGECASES": ["edge_cases"],
}


def _strip_empty_sections(template: str, semantics: dict) -> str:
    """模板中用 <!--S:NAME-->...<!--/S:NAME--> 包裹可选区块；
    若对应字段全为空则整段删除，否则只删掉标记注释。"""
    for name, fields in _OPTIONAL_SECTIONS.items():
        has_content = any((semantics.get(f) or "").strip() for f in fields)
        pattern = re.compile(
            r"[ \t]*<!--S:%s-->.*?<!--/S:%s-->[ \t]*\n?" % (name, name),
            flags=re.S,
        )
        if has_content:
            # 保留内容，去掉标记注释本身
            template = template.replace(f"<!--S:{name}-->", "").replace(f"<!--/S:{name}-->", "")
        else:
            template = pattern.sub("", template)
    return template


def generate_index_html(today_slug: str = None, today_semantics: dict = None,
                        target_date: str = None):
    """生成/更新主页面 index.html"""
    history = load_history()
    featured_date = target_date or date.today().isoformat()

    # 构建归档列表（排除今日推荐，避免重复展示）
    archive_items = []
    for item in history:
        if item.get("date") == featured_date:
            continue
        archive_items.append({
            "date": item.get("date", ""),
            "slug": item.get("slug", ""),
            "title": item.get("title", ""),
            "type": item.get("type", ""),
            "difficulty": resolve_difficulty(
                item.get("slug", ""),
                semantics={"difficulty": item["difficulty"]} if item.get("difficulty") else None,
            ),
        })

    # 构建今日题目卡片
    today_html = ""
    if today_slug and today_semantics:
        ptype = today_semantics.get("type", "")
        type_class = TYPE_CLASS_MAP.get(ptype, "other")
        diff = today_semantics.get("difficulty", "中等")
        diff_class = _DIFF_CLASS.get(diff, "medium")
        from scripts.generate_audio import render_audio_section
        audio_block = render_audio_section(featured_date, base_path="audio")
        today_html = f"""<div class="today-problem">
            <div class="today-label">&#x1F4C5; 今日推荐</div>
            <h2><a href="archive/{featured_date}.html">{today_semantics.get('frontend_id', '')}. {today_semantics.get('title', '')}</a></h2>
            <div class="today-meta">
                <span class="problem-type tag-{type_class}">{ptype}</span>
                <span class="problem-difficulty difficulty-{diff_class}">{diff}</span>
            </div>
            {audio_block}
            <p style="margin-top:12px; color:var(--text-secondary); font-size:0.9rem;">
                {today_semantics.get('description', '')[:200]}...
                <a href="archive/{featured_date}.html">[查看完整讲解]</a>
            </p>
        </div>"""

    # 构建归档网格
    archive_html = ""
    for item in reversed(archive_items):
        ptype = item.get("type", "")
        type_class = TYPE_CLASS_MAP.get(ptype, "other")
        diff = item.get("difficulty", "中等")
        diff_class = _DIFF_CLASS.get(diff, "medium")
        archive_html += f"""<div class="archive-item" data-difficulty="{diff}">
            <a href="archive/{item['date']}.html">
                <div class="archive-date">{item['date']}</div>
                <div class="archive-title">{item['title']}</div>
                <div class="archive-meta">
                    <span class="archive-type problem-type tag-{type_class}">{ptype}</span>
                    <span class="problem-difficulty difficulty-{diff_class}">{diff}</span>
                </div>
            </a>
        </div>"""

    # 构建按题型归类区块：按 history 中的 type 聚合，展示每类题目数量与题目列表
    type_groups: dict = {}
    for item in history:
        tname = item.get("type") or "未分类"
        type_groups.setdefault(tname, []).append(item)

    # 题型按题目数降序、同数量按题型名排序；组内题目按日期倒序（最新在前）
    types_html = ""
    for tname, items in sorted(type_groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        tclass = TYPE_CLASS_MAP.get(tname, "other")
        item_html = ""
        for it in reversed(items):
            diff = resolve_difficulty(
                it.get("slug", ""),
                semantics={"difficulty": it["difficulty"]} if it.get("difficulty") else None,
            )
            item_html += (
                f'<li data-difficulty="{diff}">'
                f'<a href="archive/{it["date"]}.html">{it["title"]}</a>'
                f'<span class="type-item-date">{it["date"]}</span></li>'
            )
        types_html += f"""<div class="type-card">
            <div class="type-card-header">
                <span class="problem-type tag-{tclass}">{tname}</span>
                <span class="type-count">{len(items)} 题</span>
            </div>
            <ul class="type-problem-list">
                {item_html}
            </ul>
        </div>"""

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日算法 · 变量语义法</title>
    <link rel="stylesheet" href="style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <a href="index.html" class="logo">
                <span class="logo-icon">&#x25B3;</span>
            </a>
            <span class="header-date">{featured_date}</span>
        </div>
    </header>

    <main class="container">
        <section class="index-hero">
            <h1>每日一道算法题</h1>
            <p class="subtitle">用变量语义法，把「看懂题」稳定转成「写出代码」</p>
        </section>

        {today_html}

        <section class="archive-section">
            <h2>&#x1F4DA; 往期归档</h2>
            <div class="difficulty-filter" role="group" aria-label="按难度筛选">
                <button type="button" class="filter-btn active" data-filter="全部" onclick="filterByDifficulty('全部')">全部</button>
                <button type="button" class="filter-btn filter-easy" data-filter="简单" onclick="filterByDifficulty('简单')">简单</button>
                <button type="button" class="filter-btn filter-medium" data-filter="中等" onclick="filterByDifficulty('中等')">中等</button>
                <button type="button" class="filter-btn filter-hard" data-filter="困难" onclick="filterByDifficulty('困难')">困难</button>
            </div>
            <div class="archive-grid">
                {archive_html if archive_html else '<p style="color:var(--text-tertiary);">暂无归档，第一道题即将推荐！</p>'}
            </div>
            <p class="filter-empty" id="filter-empty" hidden>该难度暂无题目</p>
        </section>

        <section class="types-section">
            <h2>&#x1F4C2; 按题型归类</h2>
            <div class="types-grid">
                {types_html if types_html else '<p style="color:var(--text-tertiary);">暂无题目。</p>'}
            </div>
        </section>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>每日算法 &mdash; 用变量语义法，把「看懂题」稳定转成「写出代码」</p>
            <p class="footer-meta">基于 daily-algo 项目 · Cursor Automations 自动生成 · 每天 8:00 AM 更新</p>
        </div>
    </footer>
    <script>
    function setSpeed(dateStr, rate) {{
        var audio = document.getElementById('audio-' + dateStr);
        if (!audio) return;
        audio.playbackRate = rate;
        var wrap = audio.closest('.audio-player-wrap');
        if (!wrap) return;
        wrap.querySelectorAll('.speed-btn').forEach(function(btn) {{
            btn.classList.remove('active');
            if (parseFloat(btn.textContent) === rate) btn.classList.add('active');
        }});
    }}
    function filterByDifficulty(diff) {{
        var visible = 0;
        document.querySelectorAll('.archive-item').forEach(function(el) {{
            var match = (diff === '全部' || el.getAttribute('data-difficulty') === diff);
            el.hidden = !match;
            if (match) visible++;
        }});
        document.querySelectorAll('.difficulty-filter .filter-btn').forEach(function(btn) {{
            btn.classList.toggle('active', btn.getAttribute('data-filter') === diff);
        }});
        var empty = document.getElementById('filter-empty');
        if (empty) empty.hidden = visible > 0 || diff === '全部';
    }}
    </script>
</body>
</html>"""

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    with open(DOCS / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)


def add_to_history(slug: str, semantics: dict, date_str: str = None, force: bool = False):
    """添加一条推荐记录到历史"""
    if date_str is None:
        date_str = date.today().isoformat()

    history = load_history()

    if any(item.get("date") == date_str for item in history):
        if not force:
            print(f"今日 ({date_str}) 已有记录，跳过")
            return
        history = [item for item in history if item.get("date") != date_str]

    history.append({
        "date": date_str,
        "slug": slug,
        "title": semantics.get("title", slug),
        "type": semantics.get("type", ""),
        "difficulty": resolve_difficulty(slug, semantics=semantics),
    })
    save_history(history)


def generate_today(dry_run: bool = False, use_api: bool = False, use_bank: bool = True,
                   force_slug: str = None, target_date: str = None, force: bool = False,
                   skip_audio: bool = False, allow_auto: bool = False) -> bool:
    """生成今日题目页面。

    方案 A：候选题库是前 200 题，但每天必须输出完整「变量语义法」精讲。
    若选中的题目在 VAR_SEMANTICS_DATA 中没有精讲，默认**不出页**，而是提示
    Agent 先补充精讲（避免静默发布只有题面+代码的不完整页面）。
    仅当显式传入 allow_auto=True 时，才用 LeetCode 官方题面临时占位出页。
    """
    today_date = target_date or date.today().isoformat()

    if force_slug:
        slug = force_slug
        semantics = get_problem_semantics(slug)
        source = "manual"
    else:
        slug, source = select_problem(use_api=use_api, use_bank=use_bank)

    if not slug:
        print("没有可用的题目！题库已用完且 API 不可用。")
        return False

    semantics = get_problem_semantics(slug)
    if not semantics:
        # 缺精讲：先拉 LeetCode 官方素材（供 Agent 撰写精讲参考 / 占位出页用）
        material = build_semantics_from_leetcode(slug)
        if allow_auto and material:
            # 仅在显式允许时才用官方题面临时占位（不含变量语义法精讲）
            semantics = material
            source = f"{source}+leetcode(自动占位/精讲缺失)"
        else:
            fid = material.get("frontend_id", "?") if material else "?"
            title = material.get("title", slug) if material else slug
            diff = material.get("difficulty", "?") if material else "?"
            print(f"⚠ 题目「{title}」(#{fid}, {slug}) 尚无「变量语义法」精讲，已跳过、未出页。")
            print("  【方案 A】请先按 COACH-VAR-SEMANTICS.md 为该题在 scripts/generate.py 的")
            print("  VAR_SEMANTICS_DATA 中补充一条完整精讲（题型/难度/描述/示例/变量语义三句法/")
            print("  模拟思考/落码步骤/Python+C++ 代码/复杂度/常见坑/边界 Case），然后重新运行：")
            print(f"    python3 scripts/generate.py --slug={slug} --date={today_date} --force")
            if material:
                print(f"  参考：难度 {diff}；可用 scripts.leetcode_api.fetch_problem_detail('{slug}') 拉官方题面与代码。")
            print("  （仅在确需临时占位时可加 --allow-auto 生成「官方题面版」，但那样不含精讲。）")
            return False

    print(f"今日题目：{semantics['title']} (#{semantics['frontend_id']})")
    print(f"题型：{semantics['type']}")
    print(f"难度：{semantics['difficulty']}")
    print(f"来源：{source}")

    if dry_run:
        print("\n[Dry-run] 跳过文件写入")
        return True

    # 生成语音讲解
    has_audio = False
    if not skip_audio:
        try:
            from scripts.generate_audio import generate_audio
            has_audio = generate_audio(semantics, today_date)
        except ImportError as e:
            print(f"⚠ 语音模块加载失败，跳过语音生成: {e}")
        except Exception as e:
            print(f"⚠ 语音生成失败: {e}")

    # 生成题目页面
    html = render_template(slug, semantics, today_date, has_audio=has_audio)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE / f"{today_date}.html", "w", encoding="utf-8") as f:
        f.write(html)

    # 更新主页（含音频播放器）
    generate_index_html(slug, semantics, target_date=today_date)

    # 记录历史
    add_to_history(slug, semantics, today_date, force=force)

    print(f"✓ 已生成 docs/archive/{today_date}.html")
    print(f"✓ 已更新 docs/index.html")
    return True


# ─── CLI ───
def main():
    parser = ArgumentParser(description="每日算法题网站生成器")
    parser.add_argument("--bank", action="store_true", help="只从本地题库选")
    parser.add_argument("--api", action="store_true", help="尝试从 LeetCode API 选")
    parser.add_argument("--dry-run", action="store_true", help="预览但不写入文件")
    parser.add_argument("--slug", type=str, help="指定题目 slug")
    parser.add_argument("--date", type=str, help="指定日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--force", action="store_true", help="覆盖已有日期的记录")
    parser.add_argument("--list", action="store_true", help="列出题库中所有题目")
    parser.add_argument("--skip-audio", action="store_true", help="跳过语音讲解生成")
    parser.add_argument("--allow-auto", action="store_true",
                        help="缺精讲时用 LeetCode 官方题面临时占位出页（默认关闭，避免发布不完整页）")
    args = parser.parse_args()

    if args.list:
        pool = load_pool()
        print("=== 候选题库：LeetCode 前 200 题（可选 {} 道，会员题已排除）===".format(len(pool)))
        print("--- 其中已内置精讲的题目（共 {} 道）---".format(len(VAR_SEMANTICS_DATA)))
        for slug, data in VAR_SEMANTICS_DATA.items():
            print(f"  #{data['frontend_id']:>4s} {data['title']:<20s} [{data['type']}] {data['difficulty']}")
        print("--- 其余题目被选中时需由 Agent 先补「变量语义法」精讲再出页（方案 A）---")
        return

    generate_today(
        dry_run=args.dry_run,
        use_api=args.api,
        use_bank=not args.api or args.bank,
        force_slug=args.slug,
        target_date=args.date,
        force=args.force,
        skip_audio=args.skip_audio,
        allow_auto=args.allow_auto,
    )


if __name__ == "__main__":
    main()
