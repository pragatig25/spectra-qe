import { useNavigate } from 'react-router-dom';
import { Check, X, Loader2 } from 'lucide-react';
import { useRunHistory } from '../hooks/usePipeline';

const TYPE_META = {
  parse: { label: 'Parse', path: '/parse', color: 'blue' },
  risk_score: { label: 'Risk Score', path: '/risk', color: 'yellow' },
  generate: { label: 'Generate', path: '/generate', color: 'green' },
  report: { label: 'Report', path: '/report', color: 'purple' },
};

function timeAgo(ts) {
  if (!ts) return '';
  const sec = Math.floor((Date.now() - ts) / 1000);
  if (sec < 60) return `${sec}s ago`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  return `${Math.floor(sec / 3600)}h ago`;
}

export default function RunHistory() {
  const runs = useRunHistory();
  const navigate = useNavigate();

  if (runs.length === 0) return null;

  return (
    <div className="px-3 py-2">
      <p className="text-xs text-slate-500 font-medium uppercase tracking-wider px-1 mb-2">
        Recent Runs
      </p>
      <div className="space-y-0.5">
        {runs.slice(0, 5).map((run) => {
          const meta = TYPE_META[run.type] || TYPE_META.parse;
          return (
            <button
              key={run.id}
              onClick={() => navigate(meta.path)}
              className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-left hover:bg-slate-800 transition-colors group"
            >
              {run.status === 'running' ? (
                <Loader2 size={12} className="text-blue-400 animate-spin shrink-0" />
              ) : run.status === 'complete' ? (
                <Check size={12} className="text-green-400 shrink-0" />
              ) : (
                <X size={12} className="text-red-400 shrink-0" />
              )}
              <span className="text-xs text-slate-400 group-hover:text-slate-200 truncate flex-1">
                {meta.label}
              </span>
              <span className="text-xs text-slate-600 tabular-nums shrink-0">
                {timeAgo(run.startedAt)}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
