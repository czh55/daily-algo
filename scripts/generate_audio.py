#!/usr/bin/env python3
"""
从题目语义数据生成语音讲解 MP3。
使用 edge-tts（微软 Edge 语音，免费、中文自然）。

用法：
  python3 scripts/generate_audio.py --date=2026-06-27 --slug=trapping-rain-water
  python3 scripts/generate_audio.py --date=2026-06-27  # 从 history.json 查 slug
"""

import asyncio
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DOCS = ROOT / "docs"
AUDIO_DIR = DOCS / "audio"
DATA = ROOT / "data"

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"  # 自然中文女声
MAX_CHUNK_LEN = 2000


def strip_html(html: str) -> str:
    """将 HTML 片段转为适合朗读的纯文本"""
    if not html:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</p>\s*<p[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</(?:p|div|h\d|li|tr)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_table_rows(html: str) -> list[str]:
    """从变量语义表格提取每行朗读文本"""
    rows = []
    for match in re.finditer(r"<tr>(.*?)</tr>", html, flags=re.S | re.I):
        row_html = match.group(1)
        if "<th>" in row_html.lower():
            continue
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, flags=re.S | re.I)
        if len(cells) >= 3:
            var_name = strip_html(cells[0])
            var_type = strip_html(cells[1])
            semantics = strip_html(cells[2])
            rows.append(f"变量 {var_name}，类型 {var_type}。{semantics}")
    return rows


def extract_numbered_items(html: str) -> list[str]:
    """提取带编号的段落（思考步骤、落码步骤等）"""
    items = []
    for match in re.finditer(r"<p[^>]*>(.*?)</p>", html, flags=re.S | re.I):
        text = strip_html(match.group(1))
        if text:
            items.append(text)
    return items


def extract_pitfalls(html: str) -> list[str]:
    items = []
    for match in re.finditer(r'<(?:p|div) class="pitfall-item"[^>]*>(.*?)</(?:p|div)>', html, flags=re.S):
        text = strip_html(match.group(1))
        if text:
            items.append(text)
    return items


def extract_edge_cases(html: str) -> list[str]:
    items = []
    for block in re.split(r'<div class="edge-case">', html)[1:]:
        end = block.find("</div>")
        if end >= 0:
            text = strip_html(block[:end])
            if text:
                items.append(text)
    return items


def extract_examples(html: str) -> list[str]:
    items = []
    for match in re.finditer(r"<div class=\"example-block\"[^>]*>(.*?)</div>", html, flags=re.S):
        text = strip_html(match.group(1))
        if text:
            items.append(text)
    return items


def estimate_duration_label(char_count: int) -> str:
    """根据字数估算朗读时长（中文神经语音约 280 字/分钟）"""
    minutes = char_count / 280
    low = max(1, int(minutes))
    high = max(low, int(minutes + 0.99))
    if low == high:
        return f"约 {low} 分钟"
    return f"约 {low} 到 {high} 分钟"


def _ordinal(n: int) -> str:
    """1-based 序号转中文读法"""
    names = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    if 1 <= n <= len(names):
        return f"第{names[n - 1]}"
    return f"第{n}"


def collect_narration_sections(semantics: dict) -> list[tuple[str, str, list[str]]]:
    """
    收集讲解各章节：(章节名, 大纲描述, 正文段落列表)
    """
    sections: list[tuple[str, str, list[str]]] = []

    desc = strip_html(semantics.get("description", ""))
    examples = extract_examples(semantics.get("examples", ""))
    if desc or examples:
        parts = []
        if desc:
            parts.append(f"题目描述。{desc}")
        if examples:
            parts.append("示例。" + "。".join(examples))
        sections.append(("题面与示例", "题面描述和输入输出示例", parts))

    thinking = extract_numbered_items(semantics.get("thinking_steps", ""))
    if thinking:
        parts = ["先模拟答题者的思考过程，从暴力解法出发，找到重复劳动，再推导优化方向。"] + thinking
        label = f"思考过程，共 {len(thinking)} 步"
        sections.append(("思考过程", label, parts))

    var_rows = extract_table_rows(semantics.get("var_semantics", ""))
    if var_rows:
        parts = ["接下来是变量语义，先理解每个变量的定义、维护和更新，再开始编码。"]
        parts.extend(var_rows)
        label = f"变量语义，共 {len(var_rows)} 个核心变量"
        sections.append(("变量语义", label, parts))

    code_steps = extract_numbered_items(semantics.get("code_steps", ""))
    if code_steps:
        parts = ["落码步骤如下。"] + code_steps
        label = f"落码步骤，共 {len(code_steps)} 步"
        sections.append(("落码步骤", label, parts))

    time_c = semantics.get("time_complexity", "")
    space_c = semantics.get("space_complexity", "")
    if time_c or space_c:
        parts = [f"复杂度分析。时间复杂度 {time_c}，空间复杂度 {space_c}。"]
        sections.append(("复杂度分析", "时间与空间复杂度", parts))

    pitfalls = extract_pitfalls(semantics.get("pitfalls", ""))
    if pitfalls:
        parts = ["常见坑点，请注意。"] + pitfalls
        label = f"常见坑点，共 {len(pitfalls)} 条"
        sections.append(("常见坑点", label, parts))

    edge_cases = extract_edge_cases(semantics.get("edge_cases", ""))
    if edge_cases:
        parts = ["必测的边界情况。"] + edge_cases
        label = f"边界情况，共 {len(edge_cases)} 条"
        sections.append(("边界情况", label, parts))

    return sections


def build_opening_intro(semantics: dict, sections: list[tuple[str, str, list[str]]], body_char_count: int) -> str:
    """构建开场白：题目信息 + 预计时长 + 内容结构"""
    title = semantics.get("title", "")
    pid = semantics.get("frontend_id", "")
    ptype = semantics.get("type", "")
    diff = semantics.get("difficulty", "")

    # 开场白本身约 200 字，计入总时长估算
    duration = estimate_duration_label(body_char_count + 200)

    outline_parts = []
    for i, (_, label, _) in enumerate(sections, 1):
        outline_parts.append(f"{_ordinal(i)}，{label}")

    outline_text = "；".join(outline_parts)
    section_count = len(sections)

    return (
        f"欢迎收听每日算法语音讲解。今天是第 {pid} 题，{title}。"
        f"题型是{ptype}，难度{diff}。"
        f"本次讲解预计时长 {duration}，共 {section_count} 个部分。"
        f"内容结构如下：{outline_text}。"
        f"好，我们开始。"
    )


def build_narration_script(semantics: dict) -> str:
    """将题目语义数据组装为完整语音旁白稿"""
    sections = collect_narration_sections(semantics)

    body_parts = []
    for _, _, parts in sections:
        body_parts.extend(parts)

    body_parts.append(
        "讲解完毕。建议回到网页查看完整代码实现，动手写一遍加深理解。祝学习顺利！"
    )

    body_text = "\n\n".join(p.strip() for p in body_parts if p.strip())
    intro = build_opening_intro(semantics, sections, len(body_text))

    script = f"{intro}\n\n{body_text}"
    script = script.replace("→", "，得到").replace("=>", "等于")
    script = re.sub(r"`([^`]+)`", r"\1", script)
    return script


def split_text(text: str, max_len: int = MAX_CHUNK_LEN) -> list[str]:
    """按段落边界切分长文本，避免超出 TTS 单次限制"""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = ""
    for para in text.split("\n\n"):
        if len(para) > max_len:
            if current:
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(para), max_len):
                chunks.append(para[i:i + max_len])
            continue
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = para
    if current:
        chunks.append(current.strip())
    return chunks


async def _synthesize_chunk(text: str, output: Path, voice: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output))


def _concat_mp3(files: list[Path], output: Path):
    """用 ffmpeg 合并多个 MP3 片段"""
    list_file = output.parent / f".concat_{output.stem}.txt"
    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for p in files:
                f.write(f"file '{p.resolve()}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
             "-c", "copy", str(output)],
            check=True, capture_output=True,
        )
    finally:
        if list_file.exists():
            list_file.unlink()


async def synthesize_speech(text: str, output_path: Path, voice: str = DEFAULT_VOICE) -> bool:
    """将文本合成为 MP3 文件"""
    chunks = split_text(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if len(chunks) == 1:
        await _synthesize_chunk(chunks[0], output_path, voice)
        return output_path.exists()

    temp_files = []
    try:
        for i, chunk in enumerate(chunks):
            tmp = output_path.parent / f".tmp_{output_path.stem}_{i}.mp3"
            await _synthesize_chunk(chunk, tmp, voice)
            temp_files.append(tmp)
        _concat_mp3(temp_files, output_path)
        return output_path.exists()
    finally:
        for f in temp_files:
            if f.exists():
                f.unlink()


def generate_audio(semantics: dict, date_str: str, voice: str = DEFAULT_VOICE) -> bool:
    """
    生成指定日期的语音讲解。
    返回是否成功生成 MP3。
    """
    script = build_narration_script(semantics)
    output_mp3 = AUDIO_DIR / f"{date_str}.mp3"
    output_txt = AUDIO_DIR / f"{date_str}.txt"

    try:
        ok = asyncio.run(synthesize_speech(script, output_mp3, voice))
        if ok:
            output_txt.write_text(script, encoding="utf-8")
            print(f"✓ 已生成语音讲解 docs/audio/{date_str}.mp3")
        return ok
    except Exception as e:
        print(f"⚠ 语音生成失败: {e}")
        return False


def audio_exists(date_str: str) -> bool:
    return (AUDIO_DIR / f"{date_str}.mp3").exists()


def render_audio_section(date_str: str, base_path: str = "../audio") -> str:
    """生成 HTML 音频播放器片段（archive 页用 ../audio，index 用 audio）"""
    if not audio_exists(date_str):
        return ""
    src = f"{base_path}/{date_str}.mp3"
    return f"""<section class="section audio-section">
                <h2 class="section-title">
                    <span class="section-icon">&#x1F3A7;</span>
                    语音讲解
                </h2>
                <p class="audio-hint">开车或通勤时可听，跟着思路走一遍</p>
                <div class="audio-player-wrap">
                    <audio controls preload="metadata" class="audio-player" id="audio-{date_str}">
                        <source src="{src}" type="audio/mpeg">
                        您的浏览器不支持音频播放
                    </audio>
                    <div class="playback-speed" aria-label="播放速度">
                        <span class="speed-label">速度</span>
                        <button type="button" class="speed-btn" onclick="setSpeed('{date_str}', 0.75)">0.75x</button>
                        <button type="button" class="speed-btn active" onclick="setSpeed('{date_str}', 1)">1x</button>
                        <button type="button" class="speed-btn" onclick="setSpeed('{date_str}', 1.25)">1.25x</button>
                        <button type="button" class="speed-btn" onclick="setSpeed('{date_str}', 1.5)">1.5x</button>
                    </div>
                </div>
            </section>"""


AUDIO_SCRIPT_JS = """
function setSpeed(dateStr, rate) {
    var audio = document.getElementById('audio-' + dateStr);
    if (!audio) return;
    audio.playbackRate = rate;
    var wrap = audio.closest('.audio-player-wrap');
    if (!wrap) return;
    wrap.querySelectorAll('.speed-btn').forEach(function(btn) {
        btn.classList.remove('active');
        if (parseFloat(btn.textContent) === rate) btn.classList.add('active');
    });
}
"""


def main():
    from argparse import ArgumentParser
    import json

    sys.path.insert(0, str(ROOT))
    from scripts.generate import get_problem_semantics, load_history

    parser = ArgumentParser(description="生成算法题语音讲解")
    parser.add_argument("--date", type=str, required=True, help="日期 YYYY-MM-DD")
    parser.add_argument("--slug", type=str, help="题目 slug（默认从 history.json 查）")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE, help="TTS 语音")
    parser.add_argument("--print-script", action="store_true", help="只打印旁白稿，不生成音频")
    args = parser.parse_args()

    slug = args.slug
    if not slug:
        history = load_history()
        for item in history:
            if item.get("date") == args.date:
                slug = item.get("slug")
                break
    if not slug:
        print(f"找不到 {args.date} 对应的题目 slug，请用 --slug 指定")
        sys.exit(1)

    semantics = get_problem_semantics(slug)
    if not semantics:
        print(f"题目 {slug} 没有预置语义数据")
        sys.exit(1)

    if args.print_script:
        print(build_narration_script(semantics))
        return

    ok = generate_audio(semantics, args.date, voice=args.voice)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
