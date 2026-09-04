# daily-algo

每日算法题推荐静态网站生成器。核心是纯 Python 脚本，将题库数据渲染为 `docs/` 下的静态 HTML（部署到 GitHub Pages），并可用 edge-tts 生成语音讲解 MP3。

常规用法见 `README.md`（本地生成命令、题库列表等），此处不重复。

## Cursor Cloud specific instructions

### 环境与依赖
- 唯一 Python 依赖是 `edge-tts`（见 `requirements.txt`），由启动 update script 通过 `pip3 install -r requirements.txt` 安装。系统已自带 Python 3.12、`pip3`、`ffmpeg`（合并多段音频用）。
- `edge-tts` 会安装到 `~/.local/bin`（不在 PATH 中），但脚本以库形式 `import edge_tts` 调用，不依赖该可执行文件，无需修改 PATH。

### 运行与验证
- 这不是长驻服务；"运行应用"= 执行生成脚本产出 HTML，再用静态服务器预览。
- 生成今日题目页：`python3 scripts/generate.py --bank`（会写入 `docs/archive/<date>.html`、更新 `docs/index.html`，并尝试生成 `docs/audio/<date>.mp3`）。
- 预览网站：`cd docs && python3 -m http.server 8000`，浏览器打开 `http://localhost:8000/index.html`。

### 非显然的注意点
- 语音生成（`generate_audio.py` / edge-tts）需要访问微软 TTS 服务的网络。若无外网，音频合成会失败但**不影响**页面生成——脚本会打印警告并继续。仅测页面时可加 `--skip-audio` 跳过语音。
- 选题去重的真实来源是 `docs/archive/*.html`（`load_history()` 会从 archive 页面重建历史并与 `data/history.json` 合并）。当题库 11 道题全部出现在 archive 中时，`select_problem` 走 `bank-cycle` 分支回到第一题——这是预期行为，不是 bug。
- `scripts/generate.py --bank` 生成的 `docs/archive/<date>.html`、`docs/audio/<date>.*` 及被修改的 `docs/index.html` 都是每日运行时产物（由每日 automation 提交）。做环境/代码验证时若不想污染提交，记得 `git checkout -- docs/index.html` 并删除新增的 `<date>` 文件。
