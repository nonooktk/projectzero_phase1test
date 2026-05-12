"use client";
// POST + SSE を fetch ReadableStream でパース。EventSource は POST 非対応のため自前実装。
import { useCallback, useRef, useState } from "react";

import { analysesStreamUrl } from "@/lib/api";
import type { AnalysisResult, StageEventPayload, StageName } from "@/lib/types";

const STAGES: StageName[] = [
  "VECTORIZE",
  "CHROMA",
  "GRAPH",
  "CONTEXT",
  "LLM_STAGE1",
  "LLM_STAGE2",
];

export type StageState = Record<StageName, StageEventPayload>;

const initialStages = (): StageState =>
  STAGES.reduce((acc, s) => {
    acc[s] = { stage: s, status: "pending", elapsed_ms: 0 };
    return acc;
  }, {} as StageState);

type ParsedEvent = { event: string; data: string };

function* parseSSE(buffer: string): Generator<ParsedEvent> {
  // 改行は LF に正規化（sse-starlette が CRLF を送るケースがあるため）
  const normalized = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const messages = normalized.split("\n\n");
  for (const msg of messages) {
    if (!msg.trim()) continue;
    let event = "message";
    const dataLines: string[] = [];
    for (const line of msg.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
    }
    if (dataLines.length === 0) continue;
    yield { event, data: dataLines.join("\n") };
  }
}

export function useAnalysisSSE() {
  const [stages, setStages] = useState<StageState>(initialStages);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setStages(initialStages());
    setResult(null);
    setError(null);
  }, []);

  const handleEvents = useCallback((events: ParsedEvent[]) => {
    for (const evt of events) {
      console.debug("[SSE]", evt.event, evt.data.slice(0, 200));
      if (evt.event === "stage") {
        try {
          const payload = JSON.parse(evt.data) as StageEventPayload;
          setStages((prev) => ({ ...prev, [payload.stage]: payload }));
        } catch (e) {
          console.error("stage parse failed", e, evt.data);
        }
      } else if (evt.event === "result") {
        try {
          const r = JSON.parse(evt.data) as AnalysisResult;
          console.log("[SSE result]", r);
          setResult(r);
        } catch (e) {
          console.error("result parse failed", e, evt.data);
          setError("結果 JSON のパースに失敗しました。Console を確認してください。");
        }
      } else if (evt.event === "error") {
        try {
          const err = JSON.parse(evt.data) as {
            error?: string;
            message?: string;
            traceback?: string;
          };
          if (err.traceback) console.error("backend traceback:\n" + err.traceback);
          setError(
            `${err.error ?? "Error"}: ${err.message ?? "unknown"}\n${err.traceback ?? ""}`,
          );
        } catch {
          setError("backend error (parse failed)");
        }
      } else if (evt.event === "done") {
        console.debug("[SSE done]");
      }
    }
  }, []);

  const submit = useCallback(
    async (theme: string) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      reset();
      setRunning(true);
      try {
        const res = await fetch(analysesStreamUrl(), {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
          body: JSON.stringify({ theme }),
          signal: ctrl.signal,
        });
        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}`);
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // メッセージ区切り探索を正規化文字列で行う
        const drainBuffer = (force: boolean) => {
          const normalized = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
          const split = normalized.lastIndexOf("\n\n");
          if (split < 0) {
            if (!force) return;
            // ストリーム終了時：残バッファ全てを解析
            const events = [...parseSSE(normalized)];
            buffer = "";
            handleEvents(events);
            return;
          }
          const ready = normalized.slice(0, split + 2);
          buffer = normalized.slice(split + 2);
          const events = [...parseSSE(ready)];
          handleEvents(events);
        };

        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            // 終端：残りを必ず処理
            buffer += decoder.decode();
            drainBuffer(true);
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          drainBuffer(false);
        }
      } catch (e) {
        if ((e as Error).name !== "AbortError") {
          console.error("[SSE fetch error]", e);
          setError((e as Error).message);
        }
      } finally {
        setRunning(false);
      }
    },
    [reset, handleEvents],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setRunning(false);
  }, []);

  return { stages, result, error, running, submit, cancel };
}

export { STAGES };
