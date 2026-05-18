import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileSearch, ShieldAlert, FlaskConical, Server, Cpu, Zap, Clock, Check, X, Loader2 } from 'lucide-react';
import { Card, StatCard } from '../components/Card';
import { api } from '../lib/api';
import { useRunHistory, useActiveRuns } from '../hooks/usePipeline';
import { useAppStore } from '../store/appStore';

const TYPE_META = {
  parse: { label: 'Spec Parse', color: 'blue', path: '/parse' },
  risk_score: { label: 'Risk Score', color: 'yellow', path: '/risk' },
  generate: { label: 'Test Generate', color: 'green', path: '/generate' },
  report: { label: 'Report', color: 'purple', path: '/report' },
};

function formatDuration(startMs, endMs) {
  if (!startMs) return '-';
  const ms = (endMs || Date.now()) - startMs;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [specs, setSpecs] = useState([]);
  const navigate = useNavigate();
  const history = useRunHistory();
  const activeRuns = useActiveRuns();
  const setAppHealth = useAppStore((s) => s.setHealth);

  useEffect(() => {
    api.health().then((h) => { setHealth(h); setAppHealth(h); }).catch(() => {});
    api.specs().then(setSpecs).catch(() => {});
  }, []);

  const features = [
    {
      icon: FileSearch,
      title: 'Spec Parser',
      desc: 'Parse OpenAPI 3.x specs into structured endpoint data',
      to: '/parse',
      color: 'blue',
    },
    {
      icon: ShieldAlert,
      title: 'Risk Scorer',
      desc: 'LLM-powered risk assessment per endpoint',
      to: '/risk',
      color: 'yellow',
    },
    {
      icon: FlaskConical,
      title: 'Test Generator',
      desc: 'AI-generated pytest cases with deduplication',
      to: '/generate',
      color: 'green',
    },
  ];

  return (
    <div className="animate-in max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Spectra — AI Test Generation</h1>
        <p className="text-slate-400 mt-2 text-base">
          AI-powered test orchestration — parse specs, score risk, generate tests, execute & report.
        </p>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <StatCard
          label="API Status"
          value={health ? 'Online' : 'Checking...'}
          sublabel={health ? `${health.llm_provider} / ${health.llm_model}` : ''}
          icon={Server}
          color={health ? 'green' : 'yellow'}
        />
        <StatCard
          label="Demo Specs"
          value={specs.length}
          sublabel="Available for testing"
          icon={Cpu}
          color="blue"
        />
        <StatCard
          label="Pipeline"
          value="5 Stages"
          sublabel="Parse → Risk → Gen → Dedup → Report"
          icon={Zap}
          color="purple"
        />
      </div>

      {/* Active runs */}
      {activeRuns.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-500" />
            </span>
            Active Pipelines
          </h2>
          <div className="space-y-2">
            {activeRuns.map((run) => {
              const meta = TYPE_META[run.type] || TYPE_META.parse;
              const activeStage = run.stages?.find((s) => s.status === 'active');
              return (
                <Card
                  key={run.id}
                  className="cursor-pointer hover:border-blue-500/50"
                  onClick={() => navigate(meta.path)}
                >
                  <div className="flex items-center gap-3">
                    <Loader2 size={16} className="text-blue-400 animate-spin" />
                    <span className="text-sm font-medium text-white">{meta.label}</span>
                    {activeStage && (
                      <span className="text-xs text-slate-400">
                        {activeStage.label}
                        {activeStage.progress &&
                          ` (${activeStage.progress.current}/${activeStage.progress.total})`}
                      </span>
                    )}
                    <span className="text-xs text-slate-500 ml-auto tabular-nums">
                      {formatDuration(run.startedAt)}
                    </span>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Feature cards */}
      <h2 className="text-lg font-semibold text-white mb-4">Pipeline Stages</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {features.map((f) => (
          <Card
            key={f.to}
            className="cursor-pointer hover:border-blue-500/50 transition-colors group"
          >
            <div onClick={() => navigate(f.to)}>
              <div className={`p-2.5 rounded-lg w-fit mb-3 bg-${f.color}-400/10`}>
                <f.icon size={22} className={`text-${f.color}-400`} />
              </div>
              <h3 className="text-base font-semibold text-white group-hover:text-blue-400 transition-colors">
                {f.title}
              </h3>
              <p className="text-sm text-slate-400 mt-1">{f.desc}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Session history */}
      {history.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Clock size={18} className="text-slate-400" />
            Session History
          </h2>
          <Card>
            <div className="divide-y divide-slate-700/50">
              {history.slice(0, 10).map((run) => {
                const meta = TYPE_META[run.type] || TYPE_META.parse;
                return (
                  <div
                    key={run.id}
                    className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0 cursor-pointer hover:opacity-80"
                    onClick={() => navigate(meta.path)}
                  >
                    {run.status === 'running' ? (
                      <Loader2 size={14} className="text-blue-400 animate-spin" />
                    ) : run.status === 'complete' ? (
                      <Check size={14} className="text-green-400" />
                    ) : (
                      <X size={14} className="text-red-400" />
                    )}
                    <span className="text-sm text-slate-300">{meta.label}</span>
                    <span className="text-xs text-slate-500">{run.specId}</span>
                    <span className="text-xs text-slate-500 ml-auto tabular-nums">
                      {formatDuration(run.startedAt, run.completedAt)}
                    </span>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}

      {/* Architecture */}
      <Card>
        <h2 className="text-lg font-semibold text-white mb-3">Architecture</h2>
        <pre className="text-sm text-slate-300 font-mono leading-relaxed overflow-x-auto">
{`OpenAPI Spec ──→ Parse ──→ Risk Score ──→ Generate Tests ──→ Deduplicate ──→ Report
                  │          │               │                  │              │
              YAML/JSON    LLM           LangChain          Embeddings     JSON/MD
                         scoring       + Pydantic          cosine sim`}
        </pre>
      </Card>
    </div>
  );
}
