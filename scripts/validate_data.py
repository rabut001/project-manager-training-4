#!/usr/bin/env python3
"""public/data/ の問題データを検証する。CI でも実行する。

--complete を付けると、stem、choices、explanation が埋まっていることも確かめる。
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from build_exam import read_answers
from exams import CHOICES, DATA_DIR, EXAMS, EXAMS_DIR, QUESTION_COUNT

VISUALS = {"figure", "table", "image"}
KEYS = {"no", "answer", "image", "stem", "choices", "visuals", "explanation"}


def check_exam(exam_id: str, title: str, complete: bool, with_pdf: bool) -> list[str]:
    errors: list[str] = []
    path = DATA_DIR / f"{exam_id}.json"
    if not path.exists():
        return [f"{path.name} がありません"]
    data = json.loads(path.read_text())
    if data.get("id") != exam_id or data.get("title") != title:
        errors.append(f"{exam_id}: id または title が収録表と違います")
    questions = data.get("questions", [])
    if [q.get("no") for q in questions] != list(range(1, QUESTION_COUNT + 1)):
        return errors + [f"{exam_id}: 問番号が 1〜{QUESTION_COUNT} の順に並んでいません"]

    answers = read_answers(EXAMS_DIR / exam_id / "am2-kaitou.pdf") if with_pdf else {}
    for q in questions:
        where = f"{exam_id} 問{q['no']}"
        missing = KEYS - q.keys()
        if missing:
            errors.append(f"{where}: 項目がありません: {sorted(missing)}")
            continue
        if q["answer"] is None:
            if not q.get("answerNote"):
                errors.append(f"{where}: answer が null なのに answerNote がありません")
        elif q["answer"] not in CHOICES:
            errors.append(f"{where}: answer が不正です: {q['answer']}")
        elif "answerNote" in q:
            errors.append(f"{where}: answer があるのに answerNote があります")
        if answers and answers[q["no"]][0] != q["answer"]:
            errors.append(f"{where}: answer {q['answer']} が解答例 {answers[q['no']][0]} と違います")
        if q["image"] != f"{exam_id}/q{q['no']:02d}.png":
            errors.append(f"{where}: image が不正です: {q['image']}")
        elif not (DATA_DIR / q["image"]).is_file():
            errors.append(f"{where}: 画像がありません: {q['image']}")
        if not isinstance(q["choices"], dict) or list(q["choices"]) != list(CHOICES):
            errors.append(f"{where}: choices のキーはア〜エの順である必要があります")
        if not isinstance(q["visuals"], list) or not set(q["visuals"]) <= VISUALS:
            errors.append(f"{where}: visuals が不正です: {q['visuals']}")
        if complete:
            if not q["stem"].strip():
                errors.append(f"{where}: stem が空です")
            if "figure" not in q["visuals"] and any(not str(v).strip() for v in q["choices"].values()):
                errors.append(f"{where}: choices に空の肢があります（肢が図だけなら visuals に figure を入れる）")
            if not q["explanation"].strip():
                errors.append(f"{where}: explanation が空です")
        named = set(re.findall(r"([アイウエ])が(?:正解|正しい)", q["explanation"]))
        if q["explanation"].strip() and q["answer"] and named != {q["answer"]}:
            errors.append(f"{where}: 解説が示す正解 {sorted(named)} が answer {q['answer']} と違います")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complete", action="store_true", help="問題文と解説がそろっていることも確かめる")
    parser.add_argument("--no-pdf", action="store_true", help="解答例 PDF との照合をしない")
    args = parser.parse_args()

    errors: list[str] = []
    index = json.loads((DATA_DIR / "index.json").read_text())
    if [{"id": e["id"], "title": e["title"]} for e in index] != [{"id": e.id, "title": e.title} for e in EXAMS]:
        errors.append("index.json が収録表と違います")
    for entry in index:
        path = DATA_DIR / f"{entry['id']}.json"
        if path.exists():
            answers = [q["answer"] for q in json.loads(path.read_text())["questions"]]
            if entry.get("answers") != answers:
                errors.append(f"index.json の {entry['id']} の answers が回の JSON と違います")
    for exam in EXAMS:
        errors += check_exam(exam.id, exam.title, args.complete, not args.no_pdf)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        sys.exit(f"{len(errors)} 件の問題があります")
    print(f"{len(EXAMS)} 回 × {QUESTION_COUNT} 問のデータは正常です")


if __name__ == "__main__":
    main()
