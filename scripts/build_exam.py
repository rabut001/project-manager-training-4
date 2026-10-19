#!/usr/bin/env python3
"""回の問題画像と JSON を作る。

問題冊子（ページ全体が画像）を問と問のあいだの余白で1問ずつ切り出し、
解答例 PDF のテキストから正解を取り、public/data/<id>.json を書く。
既にある JSON の stem、choices、visuals、explanation は残す。
最後に public/data/index.json を書き直す。

切り出しの処理は、参照元（rabut001/system-arch-training）の
scripts/cut_am2_questions.py を引き継いでいる。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pymupdf

from exams import CHOICES, DATA_DIR, EXAMS, EXAMS_DIR, QUESTION_COUNT, find_exam

THRESH = 180
MIN_RUN = 9
MIN_BAND = 9
MAX_TEXT_LINE = 48
MIN_TEXT_ROWS = 20  # 200dpi で本文1行の高さはおよそ 30 画素
LEFT_SLACK = 28
PAD_X = 40
PAD_Y = 36
RENDER_SCALE = 200 / 72

# 切り出したあとに上下を削る画素数 {(回の id, 問番号): (上, 下)}。
# 問と問のあいだに、どちらの問でもない書き込みがある画像だけに使う。
IMAGE_TRIMS: dict[tuple[str, int], tuple[int, int]] = {
    # 問1の下に「問2は問題誤りにつき受験者全員正解の措置済み」の枠がある
    ("2016-h28-haru", 1): (0, 90),
    ("2016-h28-haru", 2): (24, 0),
}
HEADER_RE = re.compile(r"[問間]\d+")
# 1行だけを読み直すときは、「問」を形の似た字に読み違えることがある
RESCUE_HEADER_RE = re.compile(r"[問間門閏閑回]\d{1,2}(?!\d)")
def row_left(row: bytes) -> int | None:
    run = 0
    start_x = 0
    for x, pixel in enumerate(row):
        if pixel < THRESH:
            if run == 0:
                start_x = x
            run += 1
            if run >= MIN_RUN:
                return start_x
        else:
            run = 0
    return None


def dark_runs(row: bytes) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start = None
    for x, pixel in enumerate(row):
        if pixel < THRESH:
            if start is None:
                start = x
        elif start is not None:
            if x - start >= MIN_RUN:
                runs.append((start, x))
            start = None
    if start is not None and len(row) - start >= MIN_RUN:
        runs.append((start, len(row)))
    return runs


def text_bands(samples: bytes, width: int, height: int) -> list[tuple[int, int, int]]:
    lefts = [row_left(samples[y * width : (y + 1) * width]) for y in range(height)]
    bands: list[tuple[int, int, int]] = []
    start = None
    min_left = width
    for y in range(height + 1):
        left = lefts[y] if y < height else None
        if left is not None:
            if start is None:
                start = y
                min_left = left
            else:
                min_left = min(min_left, left)
        elif start is not None:
            if y - start >= MIN_BAND:
                bands.append((start, y, min_left))
            start = None
    return [
        band
        for band in bands
        if band[1] - band[0] <= MAX_TEXT_LINE and band[0] < int(height * 0.90)
    ]



def is_page_number(runs: list[tuple[int, int]], width: int) -> bool:
    if not runs:
        return False
    x0 = runs[0][0]
    x1 = runs[-1][1]
    span = x1 - x0
    center = (x0 + x1) / 2
    return 40 < span < 160 and abs(center - width / 2) < 120


def footer_top(samples: bytes, width: int, height: int) -> int:
    """下端から見て、ページ番号「- n -」の上端を返す。"""
    y = height - 1
    limit = int(height * 0.75)
    while y > limit:
        runs = dark_runs(samples[y * width : (y + 1) * width])
        if is_page_number(runs, width):
            while y > limit:
                above = samples[(y - 1) * width : y * width]
                center_band = above[width // 2 - 80 : width // 2 + 80]
                if not any(pixel < THRESH for pixel in center_band):
                    break
                y -= 1
            return y
        y -= 1
    return int(height * 0.90)


def content_bounds(
    samples: bytes, width: int, y0: int, y1: int
) -> tuple[int, int, int, int] | None:
    ink_rows: list[int] = []
    for y in range(y0, y1):
        row = samples[y * width : (y + 1) * width]
        if sum(pixel < THRESH for pixel in row) >= MIN_RUN:
            ink_rows.append(y)
    if not ink_rows:
        return None
    # ページ番号の手前にある孤立した汚れは、問の本文から大きく離れているので捨てる。
    # ただし、大きな空白のあとでも文字の行の高さがあるまとまり（図や表の下の肢など）は残す。
    kept = [ink_rows[0]]
    index = 1
    while index < len(ink_rows):
        y = ink_rows[index]
        if y - kept[-1] > 160:
            block = [y]
            while index + 1 < len(ink_rows) and ink_rows[index + 1] - block[-1] <= 3:
                index += 1
                block.append(ink_rows[index])
            if len(block) < MIN_TEXT_ROWS:
                break
            kept.extend(block)
        else:
            kept.append(y)
        index += 1
    ink_rows = kept
    columns = [0] * width
    for y in ink_rows:
        row = samples[y * width : (y + 1) * width]
        for x, pixel in enumerate(row):
            if pixel < THRESH:
                columns[x] += 1
    clusters: list[list[int]] = []
    start = None
    for x, count in enumerate(columns):
        if count >= 3:
            if start is None:
                start = x
        elif start is not None:
            clusters.append([start, x])
            start = None
    if start is not None:
        clusters.append([start, width])
    merged: list[list[int]] = []
    for cluster in clusters:
        # 選択肢が左右に離れて並ぶ行も、一つの問として残す。
        if not merged or cluster[0] - merged[-1][1] > 180:
            merged.append(cluster)
        else:
            merged[-1][1] = cluster[1]
    main = max(merged, key=lambda item: item[1] - item[0])
    return main[0], ink_rows[0], main[1], ink_rows[-1] + 1



def ocr_tsv(page: pymupdf.Page, clip: pymupdf.Rect, psm: int) -> str:
    """ページの clip の範囲を3倍で描き、tesseract の TSV を返す。"""
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(3, 3),
        colorspace=pymupdf.csGRAY,
        alpha=False,
        clip=clip,
    )
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    pix.save(path)
    try:
        proc = subprocess.run(
            ["tesseract", path, "stdout", "-l", "jpn", "--psm", str(psm), "tsv"],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        os.remove(path)
    return proc.stdout


def header_ys(page: pymupdf.Page) -> list[float]:
    """問番号の行の上端を、ページ上のポイント座標で返す。"""
    tsv = ocr_tsv(page, pymupdf.Rect(20, 30, 150, page.rect.height - 30), psm=6)
    lines: dict[tuple[str, str, str], list[list[str]]] = {}
    for row in tsv.splitlines()[1:]:
        cols = row.split("\t")
        if len(cols) < 12 or cols[0] != "5" or not cols[11].strip():
            continue
        lines.setdefault((cols[2], cols[3], cols[4]), []).append(cols)
    ys: list[float] = []
    for words in lines.values():
        words.sort(key=lambda word: int(word[6]))
        text = "".join(word[11].strip() for word in words).replace(" ", "")
        text = text.lstrip("・･.．-* ")
        if HEADER_RE.match(text):
            top = min(int(word[7]) for word in words)
            ys.append(30 + top / 3)
    ys.sort()
    merged: list[float] = []
    for y in ys:
        if not merged or y - merged[-1] > 8:
            merged.append(y)
    return merged


def rescue_header_ys(page: pymupdf.Page, pix: pymupdf.Pixmap, found: list[float]) -> list[float]:
    """ページ全体の OCR が読み落とした問番号を、1行ずつ読み直して拾う。

    問番号の行は、そのページでいちばん左から書き始まる。画素からそうした行を候補にし、
    まだ見つかっていない候補だけを、その行の左端に絞って OCR する。
    """
    bands = text_bands(pix.samples, pix.width, pix.height)
    if not bands:
        return []
    page_min = min(band[2] for band in bands)
    rescued: list[float] = []
    for top, bottom, left in bands:
        if left > page_min + LEFT_SLACK:
            continue
        y = top / RENDER_SCALE
        if any(abs(y - known) < 8 for known in found + rescued):
            continue
        clip = pymupdf.Rect(20, y - 3, 150, bottom / RENDER_SCALE + 3)
        words = [row.split("\t") for row in ocr_tsv(page, clip, psm=7).splitlines()[1:]]
        text = "".join(cols[11].strip() for cols in words if len(cols) >= 12 and cols[0] == "5")
        if RESCUE_HEADER_RE.match(text.lstrip("・･.．-* ")):
            rescued.append(y)
    return rescued


def crop_questions(pdf_path: Path, out_dir: Path) -> list[Path]:
    doc = pymupdf.open(pdf_path)
    # 表紙・表記ルール・メモ用紙には問番号がない。ページは正立で描く。
    pages: list[tuple[int, pymupdf.Pixmap, list[int], int]] = []
    for page_index in range(doc.page_count):
        page = doc[page_index]
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(RENDER_SCALE, RENDER_SCALE),
            colorspace=pymupdf.csGRAY,
            alpha=False,
        )
        ys = header_ys(page)
        ys = sorted(ys + rescue_header_ys(page, pix, ys))
        if not ys:
            continue
        tops = [max(0, round(y * RENDER_SCALE)) for y in ys]
        pages.append((page_index, pix, tops, footer_top(pix.samples, pix.width, pix.height)))
    total = sum(len(tops) for _, _, tops, _ in pages)
    if total != QUESTION_COUNT:
        doc.close()
        raise SystemExit(f"問の先頭が {total} 個でした。25 個である必要があります。")

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    number = 1
    for _, pix, tops, footer in pages:
        samples = pix.samples
        width, height = pix.width, pix.height
        limits = tops + [footer]
        for index, top in enumerate(tops):
            bottom_limit = limits[index + 1]
            bounds = content_bounds(samples, width, top, bottom_limit)
            if bounds is None:
                doc.close()
                raise SystemExit(f"問{number} の領域が空です。")
            x0, y0, x1, y1 = bounds
            x0 = max(0, x0 - PAD_X)
            y0 = max(0, y0 - PAD_Y)
            x1 = min(width, x1 + PAD_X)
            y1 = min(bottom_limit, y1 + PAD_Y)
            if index + 1 < len(tops):
                y1 = min(y1, tops[index + 1] - 8)
            crop = bytearray()
            for y in range(y0, y1):
                crop += samples[y * width + x0 : y * width + x1]
            out = pymupdf.Pixmap(pymupdf.csGRAY, x1 - x0, y1 - y0, bytes(crop), False)
            path = out_dir / f"q{number:02d}.png"
            out.save(path)
            written.append(path)
            print(f"q{number:02d} {out.width}x{out.height}")
            number += 1
    doc.close()
    return written


ANSWER_RE = re.compile(r"問\s*(\d+)\s*\n\s*(\S+)")
NOTE_RE = re.compile(r"[（(]注[)）][ \t\u3000]*([^\s][^\n]*)")


def trim_images(exam_id: str, out_dir: Path) -> None:
    for (trim_id, no), (top, bottom) in IMAGE_TRIMS.items():
        if trim_id != exam_id:
            continue
        path = out_dir / f"q{no:02d}.png"
        pix = pymupdf.Pixmap(str(path))
        rows = pix.height - top - bottom
        start = top * pix.stride
        samples = pix.samples[start : start + rows * pix.stride]
        pymupdf.Pixmap(pix.colorspace, pix.width, rows, samples, False).save(path)
        print(f"q{no:02d} を {pix.width}x{rows} に削りました")


def read_answers(pdf_path: Path) -> dict[int, tuple[str | None, str | None]]:
    """解答例 PDF のテキストから、問番号ごとの (正解, 注記) を取る。

    正解の欄が「（注）」の問は、正解を None にし、欄外の注記の文を返す。
    """
    with pymupdf.open(pdf_path) as doc:
        text = "".join(page.get_text() for page in doc)
    notes = NOTE_RE.findall(text)
    answers: dict[int, tuple[str | None, str | None]] = {}
    for no, value in ANSWER_RE.findall(text):
        if value in CHOICES:
            answers[int(no)] = (value, None)
        elif value.startswith(("（注）", "(注)")):
            if len(notes) != 1:
                raise SystemExit(f"{pdf_path}: 問{no} の注記を一つに決められません: {notes}")
            answers[int(no)] = (None, notes[0].strip().rstrip("。"))
        else:
            raise SystemExit(f"{pdf_path}: 問{no} の正解を読み取れません: {value}")
    expected = set(range(1, QUESTION_COUNT + 1))
    if set(answers) != expected:
        raise SystemExit(f"{pdf_path}: 正解を読み取れない問があります: {sorted(expected - set(answers))}")
    return answers


def empty_question(exam_id: str, no: int, answer: str | None, note: str | None) -> dict:
    question = {
        "no": no,
        "answer": answer,
        "image": f"{exam_id}/q{no:02d}.png",
        "stem": "",
        "choices": {choice: "" for choice in CHOICES},
        "visuals": [],
        "explanation": "",
    }
    if note is not None:
        question["answerNote"] = note
    return question


def build(exam_id: str, cut: bool) -> None:
    exam = find_exam(exam_id)
    exam_dir = EXAMS_DIR / exam.id
    if cut:
        crop_questions(exam_dir / "am2-mondai.pdf", DATA_DIR / exam.id)
        trim_images(exam.id, DATA_DIR / exam.id)
    answers = read_answers(exam_dir / "am2-kaitou.pdf")

    json_path = DATA_DIR / f"{exam.id}.json"
    previous = {}
    if json_path.exists():
        previous = {q["no"]: q for q in json.loads(json_path.read_text())["questions"]}
    questions = []
    for no in range(1, QUESTION_COUNT + 1):
        answer, note = answers[no]
        question = empty_question(exam.id, no, answer, note)
        old = previous.get(no)
        if old:
            if old["answer"] != answer:
                raise SystemExit(f"{exam.id} 問{no}: 既存の answer {old['answer']} が解答例 {answer} と違います")
            for key in ("stem", "choices", "visuals", "explanation"):
                if key in old:
                    question[key] = old[key]
        questions.append(question)
    body = {"id": exam.id, "title": exam.title, "questions": questions}
    json_path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n")
    print(f"{json_path.relative_to(DATA_DIR.parent.parent)} を書きました")


def write_index() -> None:
    """回の一覧を書く。一覧画面が正解率を出せるよう、各回の正解の並びも持つ。"""
    index = []
    for exam in EXAMS:
        path = DATA_DIR / f"{exam.id}.json"
        questions = json.loads(path.read_text())["questions"] if path.exists() else []
        index.append({"id": exam.id, "title": exam.title, "answers": [q["answer"] for q in questions]})
    (DATA_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ids", nargs="*", help="作る回の id。省略するとすべて")
    parser.add_argument("--no-cut", action="store_true", help="画像を切り出さず、正解と JSON だけを作る")
    args = parser.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for exam_id in args.ids or [exam.id for exam in EXAMS]:
        build(exam_id, cut=not args.no_cut)
    write_index()


if __name__ == "__main__":
    main()
