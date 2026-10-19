"""収録する回の定義。scripts の各スクリプトが共有する。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMS_DIR = ROOT / "exams"
DATA_DIR = ROOT / "public" / "data"
QUESTION_COUNT = 25
CHOICES = ("ア", "イ", "ウ", "エ")


@dataclass(frozen=True)
class Exam:
    id: str
    title: str
    page: str  # IPA の年度ページ（https://www.ipa.go.jp/shiken/mondai-kaiotu/<page>.html）
    prefix: str  # IPA のファイル名の先頭（<prefix>_pm_am2_qs.pdf）


# 一覧の表示順（新しい順）
EXAMS: tuple[Exam, ...] = (
    Exam("2025-r07-aki", "令和7年度秋期", "2025r07", "2025r07a"),
    Exam("2024-r06-aki", "令和6年度秋期", "2024r06", "2024r06a"),
    Exam("2023-r05-aki", "令和5年度秋期", "2023r05", "2023r05a"),
    Exam("2022-r04-aki", "令和4年度秋期", "2022r04", "2022r04a"),
    Exam("2021-r03-aki", "令和3年度秋期", "2021r03", "2021r03a"),
    Exam("2020-r02-oct", "令和2年度10月", "2020r02", "2020r02o"),
    Exam("2019-h31-haru", "平成31年度春期", "2019h31", "2019h31h"),
    Exam("2018-h30-haru", "平成30年度春期", "2018h30", "2018h30h"),
    Exam("2017-h29-haru", "平成29年度春期", "2017h29", "2017h29h"),
    Exam("2016-h28-haru", "平成28年度春期", "2016h28", "2016h28h"),
    Exam("2015-h27-haru", "平成27年度春期", "2015h27", "2015h27h"),
    Exam("2014-h26-haru", "平成26年度春期", "2014h26", "2014h26h"),
    Exam("2013-h25-haru", "平成25年度春期", "2013h25", "2013h25h"),
    Exam("2012-h24-haru", "平成24年度春期", "2012h24", "2012h24h"),
    Exam("2011-h23-tokubetsu", "平成23年度特別", "2011h23", "2011h23tokubetsu"),
    Exam("2010-h22-haru", "平成22年度春期", "2010h22", "2010h22h"),
    Exam("2009-h21-haru", "平成21年度春期", "2009h21", "2009h21h"),
)


def find_exam(exam_id: str) -> Exam:
    for exam in EXAMS:
        if exam.id == exam_id:
            return exam
    raise SystemExit(f"収録していない回です: {exam_id}")
