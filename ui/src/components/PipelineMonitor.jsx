import { useEffect, useState } from 'react';
import { Check, X, Loader2, Circle, SkipForward } from 'lucide-react';

const STATUS_ICON = {
  pending: <Circle size={14} className="text-slate-500" />,
  active: <Loader2 size={14} className="text-blue-400 animate-spin" />,
  complete: <Check size={14} className="text-green-400" />,
  skipped: <SkipForward size={14} className="text-yellow-400" />,
  error: <X size={14} className="text-red-400" />,
};

function elapsed(startMs, endMs) {
  if (!startMs) return '';
  const ms = (endMs || Date.now()) - startMs;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function ProgressBar({ current, total }) {
  const pct = total > 0 ? (current / total) * 100 : 0;
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-400 tabular-nums whitespace-nowrap">
        {current}/{total}
      </span>
    </div>
  );
}

function StageDetail({ stage }) {
  if (!stage.detail) return null;

  if (stage.status === 'active' && stage.detail.path) {
    return (
      <p className="text-xs text-slate-500 mt-1 truncate">
        <span className="text-slate-400">{stage.detail.method}</span>{' '}
        {stage.detail.path}
      </p>
    );
  }

  if (stage.status === 'skipped' && stage.detail.reason) {
    return (
      <p className="text-xs text-yellow-500/70 mt-1">
        Skipped: {stage.detail.reason.replace(/_/g, ' ')}
      </p>
    );
  }

  if (stage.status === 'complete' && stage.detail.distribution) {
    return (
      <div className="flex gap-2 mt-1">
        {Object.entries(stage.detail.distribution).map(([tier, count]) => (
          <span key={tier} className="text-xs text-slate-400">
            {tier}: {count}
          </span>
        ))}
      </div>
    );
  }

  return null;
}

export default function PipelineMonitor({ stages, startedAt, status }) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (status !== 'running') return;
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, [status]);

  if (!stages || stages.length === 0) return null;

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-slate-300">Pipeline Progress</h4>
        {startedAt && (
          <span className="text-xs text-slate-500 tabular-nums">
            {elapsed(startedAt, status === 'running' ? now : undefined)}
          </span>
        )}
      </div>

      <div className="space-y-3">
        {stages.map((stage) => (
          <div key={stage.key} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="mt-0.5">{STATUS_ICON[stage.status]}</div>
              <div className="flex-1 w-px bg-slate-700 mt-1" />
            </div>
            <div className="flex-1 min-w-0 pb-2">
              <div className="flex items-center justify-between">
                <span
                  className={`text-sm font-medium ${
                    stage.status === 'active'
                      ? 'text-blue-400'
                      : stage.status === 'complete'
                        ? 'text-slate-300'
                        : stage.status === 'error'
                          ? 'text-red-400'
                          : 'text-slate-500'
                  }`}
                >
                  {stage.label}
                </span>
                <span className="text-xs text-slate-600 tabular-nums">
                  {elapsed(stage.startedAt, stage.completedAt)}
                </span>
              </div>

              {stage.status === 'active' && stage.progress && (
                <ProgressBar current={stage.progress.current} total={stage.progress.total} />
              )}

              <StageDetail stage={stage} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
