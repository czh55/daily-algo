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
    "BST验证": "bst",
}

# ─── Variable Semantics Data for 13 Core Problem Types ───
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
}


def get_problem_semantics(slug: str) -> Optional[dict]:
    """获取预置的变量语义数据"""
    return VAR_SEMANTICS_DATA.get(slug)


def _frontend_id_to_slug() -> dict[str, str]:
    """题号 → slug 映射"""
    return {data["frontend_id"]: slug for slug, data in VAR_SEMANTICS_DATA.items()}


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
        semantics = VAR_SEMANTICS_DATA[slug]
        history.append({
            "date": date_str,
            "slug": slug,
            "title": semantics.get("title", slug),
            "type": semantics.get("type", ""),
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


def select_problem(use_api: bool = False, use_bank: bool = True) -> tuple:
    """选择今日推荐的题目。返回 (slug, source) 或 (None, None)"""
    history = load_history()
    used_slugs = {item.get("slug", "") for item in history}

    # 策略 1：从预置题库中选未用过的
    if use_bank:
        for slug in VAR_SEMANTICS_DATA:
            if slug not in used_slugs:
                return (slug, "bank")

    # 策略 2：如果题库用完，从 API 获取热门题
    if use_api:
        try:
            from scripts.leetcode_api import fetch_hot_problems, fetch_daily_problem
            # 优先尝试每日一题
            daily = fetch_daily_problem()
            daily_slug = daily.get("titleSlug", "")
            if daily_slug and daily_slug not in used_slugs:
                return (daily_slug, "api-daily")

            # 退到热门题列表
            hot = fetch_hot_problems(limit=50)
            for p in hot:
                slug = p.get("titleSlug", "")
                if slug and slug not in used_slugs:
                    return (slug, "api-hot")
        except Exception:
            pass

    # 策略 3：题库用完 → 循环
    if use_bank:
        slugs = list(VAR_SEMANTICS_DATA.keys())
        if slugs:
            return (slugs[0], "bank-cycle")

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
        "{{CODE_PYTHON}}": semantics.get("code_python", ""),
        "{{CODE_CPP}}": semantics.get("code_cpp", ""),
        "{{TIME_COMPLEXITY}}": semantics.get("time_complexity", ""),
        "{{SPACE_COMPLEXITY}}": semantics.get("space_complexity", ""),
        "{{PITFALLS}}": semantics.get("pitfalls", ""),
        "{{EDGE_CASES}}": semantics.get("edge_cases", ""),
        "{{AUDIO_SECTION}}": render_audio_section(date_str) if has_audio else "",
        "{{AUDIO_SCRIPT}}": AUDIO_SCRIPT_JS if has_audio else "",
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

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
                   skip_audio: bool = False) -> bool:
    """生成今日题目页面"""
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
        print(f"题目 {slug} 没有预置的变量语义数据，需要 Agent 手动生成。")
        print(f"来源：{source}，请让 Agent 调用 LeetCode API 获取题目信息并生成讲解。")
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
    args = parser.parse_args()

    if args.list:
        print("=== 题库中的题目（共 {} 道）===".format(len(VAR_SEMANTICS_DATA)))
        for slug, data in VAR_SEMANTICS_DATA.items():
            print(f"  #{data['frontend_id']:>4s} {data['title']:<20s} [{data['type']}] {data['difficulty']}")
        return

    generate_today(
        dry_run=args.dry_run,
        use_api=args.api,
        use_bank=not args.api or args.bank,
        force_slug=args.slug,
        target_date=args.date,
        force=args.force,
        skip_audio=args.skip_audio,
    )


if __name__ == "__main__":
    main()
