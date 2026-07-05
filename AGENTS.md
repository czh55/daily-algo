# AGENTS.md

## Cursor Cloud specific instructions

`daily-algo` is a Python static-site generator (no server, no database). `python3 scripts/generate.py` selects an algorithm problem, renders an HTML page into `docs/`, optionally synthesizes a Chinese narration MP3, and updates `docs/index.html`. The site in `docs/` is served by GitHub Pages. Standard CLI usage is documented in `README.md`.

Runtime: Python 3 (`python3`), no virtualenv — deps install to the user site via `pip install -r requirements.txt`. `ffmpeg` is available at `/usr/bin/ffmpeg`.

Non-obvious notes:
- **No automated tests and no configured linter.** For a quick sanity check use `python3 -m py_compile scripts/*.py`.
- **Running `generate.py` mutates tracked files** (`data/history.json`, `docs/index.html`, and new files under `docs/archive/` and `docs/audio/`). Use `--dry-run` to preview selection without writing. If you only ran it to test, revert with `git checkout -- data/history.json docs/index.html` and delete the new `docs/archive/<date>.html` / `docs/audio/<date>.*` files.
- **The problem bank is exhausted.** `VAR_SEMANTICS_DATA` in `scripts/generate.py` has 11 problems (README's table lists 13, but `#15` three-sum and `#98` validate-BST have no semantics data), and `data/history.json` already covers all 11. So `--bank` selection reports source `bank-cycle` and re-picks the first problem (`#560`). To force a specific problem use `--slug=<slug>` (e.g. `--slug=lru-cache`), and use `--date=YYYY-MM-DD --force` to write a specific/duplicate date.
- **Audio generation needs network.** `generate_audio.py` calls Microsoft Edge TTS (`edge-tts`) over the network and uses `ffmpeg` to concatenate multi-chunk MP3s. Pass `--skip-audio` to skip it; failures are caught and generation continues without audio.
- **Preview the site locally** by serving the `docs/` directory, e.g. `python3 -m http.server 8000` run from `docs/`, then open `http://localhost:8000/index.html`.
