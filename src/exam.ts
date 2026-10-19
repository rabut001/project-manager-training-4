export const CHOICES = ["ア", "イ", "ウ", "エ"] as const;

export type Choice = (typeof CHOICES)[number];

export type Question = {
  no: number;
  /** 解答例で正解が示されていない問は null */
  answer: Choice | null;
  answerNote?: string;
  image: string;
  explanation: string;
};

export type Exam = {
  id: string;
  title: string;
  questions: Question[];
};

export type ExamSummary = {
  id: string;
  title: string;
  answers: (Choice | null)[];
};

export class ExamNotFound extends Error {}

export function isChoice(value: unknown): value is Choice {
  return typeof value === "string" && (CHOICES as readonly string[]).includes(value);
}

function isAnswer(value: unknown): value is Choice | null {
  return value === null || isChoice(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isQuestion(value: unknown): value is Question {
  return (
    isRecord(value) &&
    typeof value.no === "number" &&
    isAnswer(value.answer) &&
    (value.answerNote === undefined || typeof value.answerNote === "string") &&
    typeof value.image === "string" &&
    typeof value.explanation === "string"
  );
}

export function parseExam(value: unknown): Exam {
  if (
    !isRecord(value) ||
    typeof value.id !== "string" ||
    typeof value.title !== "string" ||
    !Array.isArray(value.questions) ||
    value.questions.length === 0 ||
    !value.questions.every(isQuestion)
  ) {
    throw new Error("問題データの形式が不正です。");
  }
  return { id: value.id, title: value.title, questions: value.questions };
}

export function parseIndex(value: unknown): ExamSummary[] {
  if (
    !Array.isArray(value) ||
    !value.every(
      (item) =>
        isRecord(item) &&
        typeof item.id === "string" &&
        typeof item.title === "string" &&
        Array.isArray(item.answers) &&
        item.answers.every(isAnswer),
    )
  ) {
    throw new Error("回の一覧の形式が不正です。");
  }
  return value as ExamSummary[];
}

function dataUrl(path: string): string {
  return `${import.meta.env.BASE_URL}data/${path}`;
}

export function imageUrl(image: string): string {
  return dataUrl(image);
}

const cache = new Map<string, Promise<unknown>>();
const resolved = new Map<string, unknown>();

function fetchJson(path: string): Promise<unknown> {
  const cached = cache.get(path);
  if (cached) {
    return cached;
  }
  const pending = fetch(dataUrl(path))
    .then(async (response) => {
      // 開発サーバは、無いパスにもアプリの HTML を返すので、JSON でない応答も「無い」とみなす
      const json = response.headers.get("content-type")?.includes("json") ?? false;
      if (response.status === 404 || (response.ok && !json)) {
        throw new ExamNotFound();
      }
      if (!response.ok) {
        throw new Error("データを読み込めませんでした。");
      }
      const body: unknown = await response.json();
      resolved.set(path, body);
      return body;
    })
    .catch((error: unknown) => {
      cache.delete(path);
      throw error;
    });
  cache.set(path, pending);
  return pending;
}

export function peekIndex(): ExamSummary[] | undefined {
  const body = resolved.get("index.json");
  return body === undefined ? undefined : parseIndex(body);
}

export async function loadIndex(): Promise<ExamSummary[]> {
  return parseIndex(await fetchJson("index.json"));
}

export function peekExam(examId: string): Exam | undefined {
  const body = resolved.get(`${examId}.json`);
  return body === undefined ? undefined : parseExam(body);
}

export async function loadExam(examId: string): Promise<Exam> {
  const exam = parseExam(await fetchJson(`${examId}.json`));
  if (exam.id !== examId) {
    throw new Error("問題データの id が一致しません。");
  }
  return exam;
}
