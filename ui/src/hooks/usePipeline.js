import { useCallback } from 'react';
import { usePipelineStore } from '../store/pipelineStore';
import { consumeSSE } from '../lib/stream';
import { useShallow } from 'zustand/react/shallow';

function processEvent(runId, event, store) {
  store.pushEvent(runId, event);

  if (event.status === 'error') {
    store.failRun(runId, event.error || 'Pipeline stage failed');
  }

  const isTerminal =
    (event.stage === 'risk_score' && event.status === 'complete' && event.result) ||
    (event.stage === 'pipeline' && event.status === 'complete' && event.result);

  if (isTerminal) {
    store.completeRun(runId, event.result);
  }
}

export function useRiskScorePipeline() {
  const store = usePipelineStore();
  const run = usePipelineStore((s) => s.getLatestRun('risk_score'));

  const start = useCallback(
    async (specId) => {
      const runId = `risk_${Date.now()}`;
      store.createRun(runId, 'risk_score', specId);
      try {
        await consumeSSE(
          '/api/risk-score/stream',
          { spec_id: specId },
          (event) => processEvent(runId, event, store),
        );
        const latest = usePipelineStore.getState().runs[runId];
        if (latest?.status === 'running') {
          store.completeRun(runId, latest.result);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          store.failRun(runId, err.message);
        }
      }
    },
    [store],
  );

  return {
    run,
    start,
    isRunning: run?.status === 'running',
    result: run?.result,
    error: run?.error,
    stages: run?.stages || [],
    events: run?.events || [],
  };
}

export function useGeneratePipeline() {
  const store = usePipelineStore();
  const run = usePipelineStore((s) => s.getLatestRun('generate'));

  const start = useCallback(
    async (specId, skipExecution = true) => {
      const runId = `gen_${Date.now()}`;
      store.createRun(runId, 'generate', specId);
      try {
        await consumeSSE(
          '/api/generate/stream',
          { spec_id: specId, skip_execution: skipExecution },
          (event) => processEvent(runId, event, store),
        );
        const latest = usePipelineStore.getState().runs[runId];
        if (latest?.status === 'running') {
          store.completeRun(runId, latest.result);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          store.failRun(runId, err.message);
        }
      }
    },
    [store],
  );

  return {
    run,
    start,
    isRunning: run?.status === 'running',
    result: run?.result,
    error: run?.error,
    stages: run?.stages || [],
    events: run?.events || [],
  };
}

export function useParsePipeline() {
  const store = usePipelineStore();
  const run = usePipelineStore((s) => s.getLatestRun('parse'));

  const start = useCallback(
    async (body) => {
      const runId = `parse_${Date.now()}`;
      store.createRun(runId, 'parse', body.spec_id || 'custom');
      try {
        const res = await fetch('/api/parse', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new Error(err.detail || `HTTP ${res.status}`);
        }
        const data = await res.json();
        store.pushEvent(runId, { stage: 'parse', status: 'complete', ts: Date.now() / 1000 });
        store.completeRun(runId, data);
      } catch (err) {
        store.failRun(runId, err.message);
      }
    },
    [store],
  );

  return {
    run,
    start,
    isRunning: run?.status === 'running',
    result: run?.result,
    error: run?.error,
  };
}

export function useReportPipeline() {
  const store = usePipelineStore();
  const run = usePipelineStore((s) => s.getLatestRun('report'));

  const start = useCallback(
    async (specId) => {
      const runId = `rpt_${Date.now()}`;
      store.createRun(runId, 'report', specId);
      try {
        await consumeSSE(
          '/api/report/stream',
          { spec_id: specId },
          (event) => processEvent(runId, event, store),
        );
        const latest = usePipelineStore.getState().runs[runId];
        if (latest?.status === 'running') {
          store.completeRun(runId, latest.result);
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          store.failRun(runId, err.message);
        }
      }
    },
    [store],
  );

  return {
    run,
    start,
    isRunning: run?.status === 'running',
    result: run?.result,
    error: run?.error,
    stages: run?.stages || [],
    events: run?.events || [],
  };
}

export function useReportHistory() {
  return usePipelineStore(
    useShallow((s) =>
      s.runOrder
        .map((id) => s.runs[id])
        .filter((r) => r?.type === 'report' && r?.status === 'complete'),
    ),
  );
}

export function useActiveRuns() {
  return usePipelineStore(
    useShallow((s) => s.runOrder.map((id) => s.runs[id]).filter((r) => r?.status === 'running')),
  );
}

export function useRunHistory() {
  return usePipelineStore(
    useShallow((s) => s.runOrder.map((id) => s.runs[id]).filter(Boolean).slice(0, 20)),
  );
}
