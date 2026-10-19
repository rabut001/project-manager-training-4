import { describe, expect, it } from "vitest";
import { parseProgress, scoreOf } from "./progress.ts";

const nos = new Set(Array.from({ length: 25 }, (_, index) => index + 1));

describe("parseProgress", () => {
  it("保存が無いときは問1の未選択", () => {
    expect(parseProgress(null, nos)).toEqual({ currentNo: 1, answers: {}, checked: [] });
  });

  it("壊れた JSON は捨てる", () => {
    expect(parseProgress("{", nos)).toEqual({ currentNo: 1, answers: {}, checked: [] });
  });

  it("形の合う値だけを残す", () => {
    const raw = JSON.stringify({
      currentNo: 3,
      answers: {
        "1": { choice: "イ", confirmed: true },
        "2": { choice: "オ", confirmed: false },
        "3": { choice: "ア" },
        "30": { choice: "ア", confirmed: true },
      },
      checked: [14, 3, 3, 1.5, 99, "2"],
    });
    expect(parseProgress(raw, nos)).toEqual({
      currentNo: 3,
      answers: { 1: { choice: "イ", confirmed: true } },
      checked: [3, 14],
    });
  });

  it("その回に無い問番号を開いていたら問1に戻す", () => {
    expect(parseProgress(JSON.stringify({ currentNo: 26 }), nos).currentNo).toBe(1);
  });

  it("checked が無い保存も読める", () => {
    const raw = JSON.stringify({ currentNo: 2, answers: { "2": { choice: "ウ", confirmed: false } } });
    expect(parseProgress(raw, nos)).toEqual({
      currentNo: 2,
      answers: { 2: { choice: "ウ", confirmed: false } },
      checked: [],
    });
  });
});

describe("scoreOf", () => {
  const correct = new Map([
    [1, "ア" as const],
    [2, null],
    [3, "ウ" as const],
    [4, "エ" as const],
  ]);

  it("確認済みだけを数え、正解の無い問は分母に入れない", () => {
    const answers = {
      1: { choice: "ア" as const, confirmed: true },
      2: { choice: "イ" as const, confirmed: true },
      3: { choice: "ア" as const, confirmed: true },
      4: { choice: "エ" as const, confirmed: false },
    };
    expect(scoreOf(answers, correct)).toEqual({ confirmed: 2, correct: 1 });
  });
});
