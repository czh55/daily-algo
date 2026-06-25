"""
LeetCode 公开 GraphQL API 封装
用于获取题目信息、热门题目列表、每日一题等数据
"""

import json
import urllib.request
import urllib.error
from pathlib import Path

LEETCODE_GRAPHQL = "https://leetcode.cn/graphql"
LEETCODE_API = "https://leetcode.cn/api"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://leetcode.cn/",
}

# 高频题型核心题库（匹配 COACH-VAR-SEMANTICS.md 的 13 种题型）
TYPE_PROBLEM_MAP = {
    "前缀和+哈希": {"problem": "subarray-sum-equals-k", "title": "和为 K 的子数组"},
    "固定滑窗最值": {"problem": "sliding-window-maximum", "title": "滑动窗口最大值"},
    "可变滑窗": {"problem": "minimum-window-substring", "title": "最小覆盖子串"},
    "单调栈": {"problem": "trapping-rain-water", "title": "接雨水"},
    "链表指针": {"problem": "reverse-linked-list", "title": "反转链表"},
    "设计题": {"problem": "lru-cache", "title": "LRU 缓存"},
    "二维DP": {"problem": "edit-distance", "title": "编辑距离"},
    "树后序递归": {"problem": "lowest-common-ancestor-of-a-binary-tree", "title": "二叉树的最近公共祖先"},
    "并查集": {"problem": "number-of-provinces", "title": "省份数量"},
    "网格搜索": {"problem": "number-of-islands", "title": "岛屿数量"},
    "拓扑排序": {"problem": "course-schedule", "title": "课程表"},
    "排序+双指针": {"problem": "3sum", "title": "三数之和"},
    "BST验证": {"problem": "validate-binary-search-tree", "title": "验证二叉搜索树"},
}

# 扩展高频题（每天推荐的不同题目池）
EXTRA_PROBLEMS = [
    {"slug": "two-sum", "title": "两数之和"},
    {"slug": "longest-substring-without-repeating-characters", "title": "无重复字符的最长子串"},
    {"slug": "longest-palindromic-substring", "title": "最长回文子串"},
    {"slug": "container-with-most-water", "title": "盛最多水的容器"},
    {"slug": "merge-two-sorted-lists", "title": "合并两个有序链表"},
    {"slug": "best-time-to-buy-and-sell-stock", "title": "买卖股票的最佳时机"},
    {"slug": "binary-tree-inorder-traversal", "title": "二叉树的中序遍历"},
    {"slug": "climbing-stairs", "title": "爬楼梯"},
    {"slug": "maximum-subarray", "title": "最大子数组和"},
    {"slug": "merge-intervals", "title": "合并区间"},
    {"slug": "spiral-matrix", "title": "螺旋矩阵"},
    {"slug": "jump-game", "title": "跳跃游戏"},
    {"slug": "word-break", "title": "单词拆分"},
    {"slug": "rotate-image", "title": "旋转图像"},
    {"slug": "valid-parentheses", "title": "有效的括号"},
    {"slug": "longest-consecutive-sequence", "title": "最长连续序列"},
    {"slug": "search-in-rotated-sorted-array", "title": "搜索旋转排序数组"},
    {"slug": "permutations", "title": "全排列"},
    {"slug": "coin-change", "title": "零钱兑换"},
    {"slug": "top-k-frequent-elements", "title": "前 K 个高频元素"},
    {"slug": "evaluate-reverse-polish-notation", "title": "逆波兰表达式求值"},
    {"slug": "kth-largest-element-in-an-array", "title": "数组中的第K个最大元素"},
    {"slug": "binary-tree-level-order-traversal", "title": "二叉树的层序遍历"},
]


def graphql_query(query: str, variables: dict = None) -> dict:
    """发送 GraphQL 请求到 LeetCode CN"""
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(LEETCODE_GRAPHQL, data=payload, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"[LeetCode API] 请求失败: {e}")
        return {}
    except Exception as e:
        print(f"[LeetCode API] 错误: {e}")
        return {}


def fetch_problem_detail(slug: str) -> dict:
    """根据题目 slug 获取完整题目信息（中文）"""
    query = """
    query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        title
        titleSlug
        translatedTitle
        difficulty
        categoryTitle
        topicTags { name translatedName }
        translatedContent
        stats
        hints
        sampleTestCase
        exampleTestcases
        codeSnippets { lang langSlug code }
        similarQuestions
      }
    }
    """
    result = graphql_query(query, {"titleSlug": slug})
    question = result.get("data", {}).get("question", {})
    return question


def fetch_daily_problem() -> dict:
    """获取 LeetCode 每日一题"""
    query = """
    query questionOfToday {
      todayRecord {
        date
        question {
          questionId
          questionFrontendId
          title
          titleSlug
          translatedTitle
          difficulty
          categoryTitle
          topicTags { name translatedName }
          translatedContent
          stats
          codeSnippets { lang langSlug code }
        }
      }
    }
    """
    result = graphql_query(query)
    today = result.get("data", {}).get("todayRecord", [])
    if isinstance(today, list) and today:
        return today[0].get("question", {})
    if isinstance(today, dict):
        return today.get("question", {})
    return {}


def fetch_hot_problems(limit: int = 50) -> list:
    """获取热门题目列表"""
    query = """
    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(
        categorySlug: $categorySlug
        limit: $limit
        skip: $skip
        filters: $filters
      ) {
        total: totalNum
        questions: data {
          questionFrontendId
          title
          titleSlug
          translatedTitle
          difficulty
          acRate
          topicTags { name translatedName }
          stats
        }
      }
    }
    """
    result = graphql_query(query, {
        "categorySlug": "",
        "skip": 0,
        "limit": limit,
        "filters": {}
    })
    questions = result.get("data", {}).get("problemsetQuestionList", {}).get("questions", [])
    return questions


def fetch_contest_problems() -> list:
    """获取最近周赛题目"""
    try:
        req = urllib.request.Request(
            "https://leetcode.cn/contest/api/list/",
            headers=HEADERS
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        contests = data.get("contests", {}).get("upcoming", [])
        return contests
    except Exception:
        return []


def determine_problem_type(slug: str) -> str:
    """根据 slug 判定题目所属的变量语义题型"""
    for ptype, info in TYPE_PROBLEM_MAP.items():
        if info["problem"] == slug:
            return ptype
    return ""


def data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def load_history() -> list:
    """加载已推荐历史"""
    path = data_dir() / "history.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list):
    path = data_dir() / "history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_bank() -> list:
    """加载本地静态题库"""
    path = data_dir() / "bank.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


if __name__ == "__main__":
    # 测试：获取每日一题
    print("=== 每日一题 ===")
    d = fetch_daily_problem()
    print(json.dumps(d, ensure_ascii=False, indent=2)[:2000])
