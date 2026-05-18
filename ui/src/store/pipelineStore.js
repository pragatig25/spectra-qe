import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const MAX_RETAINED_RUNS = 50;

const STAGE_DEFS = {
  parse: { parse: 'Parse Spec' },
  risk_score: { parse: 'Parse Spec', risk_score: 'Risk Scoring' },
  generate: {
    parse: 'Parse Spec',
    risk_score: 'Risk Scoring',
    generate: 'Test Generation',
    dedup: 'Deduplication',
  },
  report: {
    parse: 'Parse Spec',
    risk_score: 'Risk Scoring',
    generate: 'Test Generation',
    dedup: 'Deduplication',
    report: 'Report Generation',
  },
};

function buildStages(type) {
  const defs = STAGE_DEFS[type] || STAGE_DEFS.parse;
  return Object.entries(defs).map(([key, label]) => ({
    key,
    label,
    status: 'pending',
    startedAt: null,
    completedAt: null,
    progress: null,
    detail: null,
  }));
}

export const usePipelineStore = create(
  persist(
    (set, get) => ({
      runs: {},
      runOrder: [],

      createRun(id, type, specId) {
        set((s) => ({
          runs: {
            ...s.runs,
            [id]: {
              id,
              type,
              specId,
              status: 'running',
              startedAt: Date.now(),
              completedAt: null,
              stages: buildStages(type),
              events: [],
              result: null,
              error: null,
            },
          },
          runOrder: [id, ...s.runOrder.filter((r) => r !== id)],
        }));
      },

      pushEvent(runId, event) {
        set((s) => {
          const run = s.runs[runId];
          if (!run) return s;

          const stages = run.stages.map((st) => {
            if (st.key !== event.stage) return st;

            if (event.status === 'started' || event.status === 'scoring' || event.status === 'generating') {
              return {
                ...st,
                status: 'active',
                startedAt: st.startedAt || event.ts * 1000,
                progress: event.detail?.index
                  ? { current: event.detail.index, total: event.detail.total }
                  : st.progress,
                detail: event.detail || st.detail,
              };
            }

            if (event.status === 'scored' || event.status === 'generated') {
              return {
                ...st,
                status: 'active',
                progress: { current: event.detail.index, total: event.detail.total },
                detail: event.detail,
              };
            }

            if (event.status === 'complete') {
              return { ...st, status: 'complete', completedAt: event.ts * 1000, detail: event.detail };
            }

            if (event.status === 'skipped') {
              return { ...st, status: 'skipped', completedAt: event.ts * 1000, detail: event.detail };
            }

            if (event.status === 'error') {
              return { ...st, status: 'error', completedAt: event.ts * 1000, detail: event.detail };
            }

            return st;
          });

          return {
            runs: {
              ...s.runs,
              [runId]: {
                ...run,
                stages,
                events: [...run.events, event],
              },
            },
          };
        });
      },

      completeRun(runId, result) {
        set((s) => {
          const run = s.runs[runId];
          if (!run) return s;
          return {
            runs: {
              ...s.runs,
              [runId]: { ...run, status: 'complete', completedAt: Date.now(), result },
            },
          };
        });
      },

      failRun(runId, error) {
        set((s) => {
          const run = s.runs[runId];
          if (!run) return s;
          return {
            runs: {
              ...s.runs,
              [runId]: { ...run, status: 'error', completedAt: Date.now(), error },
            },
          };
        });
      },

      clearRun(runId) {
        set((s) => {
          const { [runId]: _, ...rest } = s.runs;
          return { runs: rest, runOrder: s.runOrder.filter((r) => r !== runId) };
        });
      },

      clearAllRuns() {
        set({ runs: {}, runOrder: [] });
      },

      getLatestRun(type) {
        const { runs, runOrder } = get();
        for (const id of runOrder) {
          if (runs[id]?.type === type) return runs[id];
        }
        return null;
      },

      getRunsByType(type) {
        const { runs, runOrder } = get();
        return runOrder.map((id) => runs[id]).filter((r) => r?.type === type);
      },

      getActiveRuns() {
        const { runs, runOrder } = get();
        return runOrder.map((id) => runs[id]).filter((r) => r?.status === 'running');
      },
    }),
    {
      name: 'qe-pipeline-runs',
      version: 1,

      partialize: (state) => {
        const kept = state.runOrder.slice(0, MAX_RETAINED_RUNS);
        const runs = {};
        for (const id of kept) {
          const run = state.runs[id];
          if (run) {
            runs[id] = { ...run, events: [] };
          }
        }
        return { runs, runOrder: kept };
      },

      merge: (persisted, current) => {
        if (!persisted) return current;

        const runs = { ...persisted.runs };
        for (const [id, run] of Object.entries(runs)) {
          if (run.status === 'running') {
            runs[id] = {
              ...run,
              status: 'error',
              error: 'Interrupted — page was reloaded before this run finished',
              completedAt: run.startedAt,
            };
          }
        }

        return {
          ...current,
          runs,
          runOrder: persisted.runOrder || [],
        };
      },
    },
  ),
);
