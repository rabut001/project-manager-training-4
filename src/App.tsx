import { useEffect, useState } from "react";
import { ExamList, MissingExam } from "./ExamList.tsx";
import { ExamNotFound, loadExam, peekExam, type Exam } from "./exam.ts";
import { Practice } from "./Practice.tsx";
import { listPath, useRoute, type LinkClick } from "./route.ts";

type ExamScreenProps = {
  examId: string;
  onLinkClick: LinkClick;
};

function ExamScreen({ examId, onLinkClick }: ExamScreenProps) {
  const [exam, setExam] = useState<Exam | null>(() => peekExam(examId) ?? null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let active = true;
    loadExam(examId)
      .then((loaded) => active && setExam(loaded))
      .catch((reason: unknown) => active && setError(reason));
    return () => {
      active = false;
    };
  }, [examId]);

  if (error instanceof ExamNotFound) {
    return <MissingExam onLinkClick={onLinkClick} />;
  }
  if (error) {
    return <p className="status">{error instanceof Error ? error.message : "読み込みに失敗しました。"}</p>;
  }
  if (!exam) {
    return <p className="status">問題を読み込んでいます。</p>;
  }
  return <Practice exam={exam} listHref={listPath()} onLinkClick={onLinkClick} />;
}

export function App() {
  const { route, onLinkClick } = useRoute();

  if (route.name === "list") {
    return <ExamList onLinkClick={onLinkClick} />;
  }
  if (route.name === "missing") {
    return <MissingExam onLinkClick={onLinkClick} />;
  }
  return <ExamScreen key={route.id} examId={route.id} onLinkClick={onLinkClick} />;
}
