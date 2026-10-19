import { isChoice, type Choice } from "./exam.ts";

export type AnswerRecord = {
  choice: Choice;
  confirmed: boolean;
};

export type Progress = {
  currentNo: number;
  answers: Record<number, AnswerRecord>;
  checked: number[];
};

export function storageKey(examId: string): string {
  return `pm-am2:${examId}`;
}

export function emptyProgress(): Progress {
  return { currentNo: 1, answers: {}, checked: [] };
}

function sorted(values: Iterable<number>): number[] {
  return [...new Set(values)].sort((left, right) => left - right);
}

function isAnswerRecord(value: unknown): value is AnswerRecord {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return isChoice(record.choice) && typeof record.confirmed === "boolean";
}

/** 保存値を読む。形の合わない値と、その回に無い問番号は捨てる。 */
export function parseProgress(raw: string | null, questionNos: ReadonlySet<number>): Progress {
  if (raw === null) {
    return emptyProgress();
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return emptyProgress();
  }
  if (typeof parsed !== "object" || parsed === null) {
    return emptyProgress();
  }
  const value = parsed as Record<string, unknown>;

  const currentNo =
    typeof value.currentNo === "number" && questionNos.has(value.currentNo) ? value.currentNo : 1;

  const answers: Record<number, AnswerRecord> = {};
  if (typeof value.answers === "object" && value.answers !== null) {
    for (const [key, record] of Object.entries(value.answers)) {
      const no = Number(key);
      if (questionNos.has(no) && isAnswerRecord(record)) {
        answers[no] = { choice: record.choice, confirmed: record.confirmed };
      }
    }
  }

  const checked = Array.isArray(value.checked)
    ? sorted(value.checked.filter((no): no is number => Number.isInteger(no) && questionNos.has(no)))
    : [];

  return { currentNo, answers, checked };
}

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function loadProgress(examId: string, questionNos: ReadonlySet<number>): Progress {
  return parseProgress(readStorage(storageKey(examId)), questionNos);
}

export function saveProgress(examId: string, progress: Progress): void {
  const stored: Progress = { ...progress, checked: sorted(progress.checked) };
  try {
    localStorage.setItem(storageKey(examId), JSON.stringify(stored));
  } catch {
    // 保存できない環境（プライベートブラウズなど）では、その場の操作だけで続ける
  }
}

export type Score = { confirmed: number; correct: number };

/** 確認済みの問の数と正解数。正解の無い問は数えない。 */
export function scoreOf(
  answers: Record<number, AnswerRecord>,
  correctAnswers: ReadonlyMap<number, Choice | null>,
): Score {
  let confirmed = 0;
  let correct = 0;
  for (const [no, answer] of correctAnswers) {
    const record = answers[no];
    if (answer === null || !record?.confirmed) {
      continue;
    }
    confirmed += 1;
    if (record.choice === answer) {
      correct += 1;
    }
  }
  return { confirmed, correct };
}

export function percent(score: Score): number {
  return Math.round((score.correct / score.confirmed) * 100);
}
