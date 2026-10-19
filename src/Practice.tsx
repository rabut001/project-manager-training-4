import { useEffect, useRef, useState } from "react";
import { SOURCE_URL } from "./ExamList.tsx";
import { CHOICES, imageUrl, type Choice, type Exam, type Question } from "./exam.ts";
import {
  loadProgress,
  percent,
  saveProgress,
  scoreOf,
  type AnswerRecord,
  type Progress,
} from "./progress.ts";
import type { LinkClick } from "./route.ts";

type PracticeProps = {
  exam: Exam;
  listHref: string;
  onLinkClick: LinkClick;
};

type DialogKind = "clear" | "grade";

const CHOICE_KEYS: Record<string, Choice> = {
  "1": "ア",
  "2": "イ",
  "3": "ウ",
  "4": "エ",
  a: "ア",
  b: "イ",
  c: "ウ",
  d: "エ",
};

function statusLabel(answer: AnswerRecord | undefined, question: Question): string {
  if (question.answer === null) {
    return "採点対象外";
  }
  if (!answer) {
    return "未選択";
  }
  if (!answer.confirmed) {
    return "選択済み、未確認";
  }
  return answer.choice === question.answer ? "正解" : "誤答";
}

function numberLabel(question: Question, answer: AnswerRecord | undefined, checked: boolean): string {
  const mark = checked ? "チェック済み、" : "";
  return `問${question.no}、${mark}${statusLabel(answer, question)}`;
}

function preload(src: string) {
  const image = new Image();
  image.src = src;
}

export function Practice({ exam, listHref, onLinkClick }: PracticeProps) {
  const questionNos = new Set(exam.questions.map((question) => question.no));
  const [progress, setProgress] = useState<Progress>(() => loadProgress(exam.id, questionNos));
  const [dialogKind, setDialogKind] = useState<DialogKind | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const imageScroll = useRef<HTMLDivElement>(null);
  const lower = useRef<HTMLDivElement>(null);
  // 閉じるアニメーションのあいだも文言を保つため、最後に開いた種類を覚えておく
  const shownKind = useRef<DialogKind>("clear");
  if (dialogKind) {
    shownKind.current = dialogKind;
  }

  const index = Math.max(
    0,
    exam.questions.findIndex((item) => item.no === progress.currentNo),
  );
  const question = exam.questions[index];
  const previous = exam.questions[index - 1];
  const next = exam.questions[index + 1];
  const answer = progress.answers[question.no];
  const gradable = question.answer !== null;
  const confirmed = answer?.confirmed ?? false;
  const isChecked = progress.checked.includes(question.no);

  useEffect(() => {
    saveProgress(exam.id, progress);
  }, [exam.id, progress]);

  useEffect(() => {
    imageScroll.current?.scrollTo(0, 0);
    lower.current?.scrollTo(0, 0);
  }, [question.no]);

  useEffect(() => {
    for (const neighbor of [previous, next]) {
      if (neighbor) {
        preload(imageUrl(neighbor.image));
      }
    }
  }, [previous, next]);

  useEffect(() => {
    const element = dialog.current;
    if (!element) {
      return;
    }
    if (dialogKind && !element.open) {
      element.showModal();
    }
    if (!dialogKind && element.open) {
      element.close();
    }
  }, [dialogKind]);

  const correctAnswers = new Map(exam.questions.map((item) => [item.no, item.answer]));
  const score = scoreOf(progress.answers, correctAnswers);
  const scoreText =
    score.confirmed === 0 ? "—" : `${score.correct}/${score.confirmed}（${percent(score)}%）`;
  const draftCount = exam.questions.filter((item) => {
    const record = progress.answers[item.no];
    return item.answer !== null && record !== undefined && !record.confirmed;
  }).length;

  function select(choice: Choice) {
    if (!gradable || confirmed) {
      return;
    }
    setProgress((current) => ({
      ...current,
      answers: { ...current.answers, [question.no]: { choice, confirmed: false } },
    }));
  }

  function confirmAnswer() {
    if (!gradable || !answer || answer.confirmed) {
      return;
    }
    setProgress((current) => ({
      ...current,
      answers: { ...current.answers, [question.no]: { choice: answer.choice, confirmed: true } },
    }));
  }

  function moveTo(target: Question | undefined) {
    if (target) {
      setProgress((current) => ({ ...current, currentNo: target.no }));
    }
  }

  function closeDialog() {
    dialog.current?.close();
    setDialogKind(null);
  }

  function gradeDrafts() {
    setProgress((current) => {
      const answers = { ...current.answers };
      for (const item of exam.questions) {
        const record = answers[item.no];
        if (item.answer !== null && record && !record.confirmed) {
          answers[item.no] = { choice: record.choice, confirmed: true };
        }
      }
      return { ...current, answers };
    });
    closeDialog();
  }

  function clearAnswers() {
    setProgress((current) => ({ currentNo: exam.questions[0].no, answers: {}, checked: current.checked }));
    closeDialog();
  }

  function toggleCheck() {
    setProgress((current) => ({
      ...current,
      checked: current.checked.includes(question.no)
        ? current.checked.filter((no) => no !== question.no)
        : [...current.checked, question.no],
    }));
  }

  // キー操作は最新の状態で動かすため、毎回の描画で処理を差し替える
  const onKey = useRef<(event: KeyboardEvent) => void>(() => {});
  onKey.current = (event) => {
    if (dialogKind || event.ctrlKey || event.altKey || event.metaKey || event.isComposing) {
      return;
    }
    const target = event.target as HTMLElement | null;
    const tag = target?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
      return;
    }
    const choice = CHOICE_KEYS[event.key.toLowerCase()];
    if (choice) {
      event.preventDefault();
      select(choice);
    } else if (event.key === "Enter") {
      if (tag === "BUTTON" || tag === "A") {
        return;
      }
      event.preventDefault();
      confirmAnswer();
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      moveTo(previous);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      moveTo(next);
    }
  };

  useEffect(() => {
    const listener = (event: KeyboardEvent) => onKey.current(event);
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

  return (
    <div className="practice">
      <header className="top">
        <a className="back" href={listHref} onClick={(event) => onLinkClick(event, listHref)}>
          一覧へ戻る
        </a>
        <div className="heading">
          <h1>{exam.title}</h1>
          <p className="score">
            正解 <span>{scoreText}</span>
          </p>
        </div>
        <nav className="numbers" aria-label="問題番号">
          {exam.questions.map((item) => {
            const record = progress.answers[item.no];
            const itemChecked = progress.checked.includes(item.no);
            const result =
              item.answer !== null && record?.confirmed
                ? record.choice === item.answer
                  ? "correct"
                  : "incorrect"
                : null;
            const classes = ["number"];
            if (item.no === question.no) {
              classes.push("current");
            }
            if (result) {
              classes.push(result);
            } else if (item.answer !== null && record) {
              classes.push("draft");
            }
            return (
              <button
                key={item.no}
                type="button"
                className={classes.join(" ")}
                aria-current={item.no === question.no ? "true" : undefined}
                aria-label={numberLabel(item, record, itemChecked)}
                onClick={() => moveTo(item)}
              >
                <span>{item.no}</span>
                <span className="badges" aria-hidden="true">
                  {result && <span className="mark">{result === "correct" ? "○" : "×"}</span>}
                  {itemChecked && (
                    <span className="flag">
                      <svg viewBox="0 0 16 16">
                        <path d="M2.6 8.2 6.4 12.2 13.4 3.8" />
                      </svg>
                    </span>
                  )}
                </span>
              </button>
            );
          })}
        </nav>
      </header>

      <div className="image-pane">
        <div className="check-row">
          <label className="check">
            <input
              type="checkbox"
              checked={isChecked}
              aria-label={`問${question.no}をチェック`}
              onChange={toggleCheck}
            />
          </label>
        </div>
        <div className="image-scroll" ref={imageScroll}>
          <img src={imageUrl(question.image)} alt={`問${question.no}`} />
        </div>
      </div>

      <div className="lower" ref={lower}>
        {gradable ? (
          <>
            <div className="choices" role="group" aria-label="選択肢">
              {CHOICES.map((choice) => (
                <button
                  key={choice}
                  type="button"
                  className={answer?.choice === choice ? "selected" : undefined}
                  aria-pressed={answer?.choice === choice}
                  disabled={confirmed}
                  onClick={() => select(choice)}
                >
                  {choice}
                </button>
              ))}
            </div>

            {confirmed && answer ? (
              <section className="result" aria-live="polite">
                <p className={answer.choice === question.answer ? "ok" : "ng"}>
                  {answer.choice === question.answer ? "正解" : "不正解"}
                </p>
                <p>
                  正答 <strong>{question.answer}</strong>
                </p>
                <p>{question.explanation || "解説は準備中です。"}</p>
                <p className="note">IPA の公式解説ではない</p>
              </section>
            ) : (
              <button type="button" className="confirm" disabled={!answer} onClick={confirmAnswer}>
                結果を確認
              </button>
            )}
          </>
        ) : (
          <section className="result">
            <p className="void">
              この問は、IPA の解答例で「{question.answerNote}」とされています。採点の対象外です。
            </p>
            {question.explanation && (
              <>
                <p>{question.explanation}</p>
                <p className="note">IPA の公式解説ではない</p>
              </>
            )}
          </section>
        )}

        <div className="pager">
          <button type="button" disabled={!previous} onClick={() => moveTo(previous)}>
            前へ
          </button>
          <button type="button" disabled={!next} onClick={() => moveTo(next)}>
            次へ
          </button>
        </div>

        <button
          type="button"
          className="grade"
          disabled={draftCount === 0}
          onClick={() => setDialogKind("grade")}
        >
          一括採点
        </button>

        <button type="button" className="clear" onClick={() => setDialogKind("clear")}>
          回答をすべてクリア
        </button>

        <footer>
          出典: <a href={SOURCE_URL}>IPA の過去問題</a>
        </footer>
        <p className="keys">キー操作: 1〜4 または A〜D で選択、Enter で結果を確認、← → で前後の問</p>
      </div>

      <dialog ref={dialog} onClose={() => setDialogKind(null)} aria-labelledby="dialog-title">
        {shownKind.current === "grade" ? (
          <>
            <h2 id="dialog-title">選択済みの問をまとめて採点します</h2>
            <p>
              選択済みで未確認の{draftCount}
              問を確認済みにします。採点後は、その問の選択を変えられません。未選択の問は採点しません。
            </p>
            <div className="dialog-actions">
              <button type="button" onClick={closeDialog}>
                中止
              </button>
              <button type="button" onClick={gradeDrafts}>
                採点する
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 id="dialog-title">この回の解答を消します</h2>
            <p>
              {exam.title}
              の確認済みの解答と、まだ確認していない選択を消して、問1に戻ります。チェックはそのまま残します。
            </p>
            <div className="dialog-actions">
              <button type="button" onClick={closeDialog}>
                中止
              </button>
              <button type="button" className="danger" onClick={clearAnswers}>
                消してやり直す
              </button>
            </div>
          </>
        )}
      </dialog>
    </div>
  );
}
