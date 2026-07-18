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
        merged[item["date"]] = item

    return sorted(merged.values(), key=lambda x: x.get("date", ""))


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
        })

    # 构建今日题目卡片
    today_html = ""
    if today_slug and today_semantics:
        ptype = today_semantics.get("type", "")
        type_class = TYPE_CLASS_MAP.get(ptype, "other")
        diff = today_semantics.get("difficulty", "中等")
        diff_class = {"简单": "easy", "中等": "medium", "困难": "hard"}.get(diff, "medium")
        from scripts.generate_audio import render_audio_section
        audio_block = render_audio_section(featured_date, base_path="audio")
        today_html = f"""<div class="today-problem">
            <div class="today-label">&#x1F4C5; 今日推荐</div>
            <h2><a href="archive/{featured_date}.html">{today_semantics.get('frontend_id', '')}. {today_semantics.get('title', '')}</a></h2>
            <div class="today-meta">
                <span class="problem-type {type_class}">{ptype}</span>
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
        archive_html += f"""<div class="archive-item">
            <a href="archive/{item['date']}.html">
                <div class="archive-date">{item['date']}</div>
                <div class="archive-title">{item['title']}</div>
                <span class="archive-type problem-type {type_class}">{ptype}</span>
            </a>
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
                <span class="logo-text">每日算法</span>
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
            <div class="archive-grid">
                {archive_html if archive_html else '<p style="color:var(--text-tertiary);">暂无归档，第一道题即将推荐！</p>'}
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
