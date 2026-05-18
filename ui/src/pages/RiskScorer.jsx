import { useState, useEffect } from 'react';
import { ShieldAlert, Play } from 'lucide-react';
import { Card } from '../components/Card';
import { RiskBadge, MethodBadge } from '../components/Badge';
import PipelineMonitor from '../components/PipelineMonitor';
import { api } from '../lib/api';
import { useRiskScorePipeline } from '../hooks/usePipeline';

export default function RiskScorer() {
  const [specs, setSpecs] = useState([]);
  const [selectedSpec, setSelectedSpec] = useState('petstore');
  const { run, start, isRunning, result, error, stages } = useRiskScorePipeline();

  useEffect(() => {
    api.specs().then(setSpecs).catch(() => {});
  }, []);

  const tierColors = {
    Low: 'bg-green-500',
    Med: 'bg-yellow-500',
    High: 'bg-orange-500',
    Critical: 'bg-red-500',
  };

  return (
    <div className="animate-in max-w-5xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 rounded-lg bg-yellow-400/10">
          <ShieldAlert size={22} className="text-yellow-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Risk Scorer</h1>
          <p className="text-sm text-slate-400">LLM-powered risk tier assessment per endpoint</p>
        </div>
      </div>

      <Card className="mb-6">
        <div className="flex gap-3">
          <select
            value={selectedSpec}
            onChange={(e) => setSelectedSpec(e.target.value)}
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            {specs.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button
            onClick={() => start(selectedSpec)}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-500 disabled:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Play size={14} />
            {isRunning ? 'Scoring...' : 'Score Risk'}
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Requires LLM API key configured on backend. Each endpoint is scored individually.
        </p>
      </Card>

      {error && (
        <div className="bg-red-400/10 border border-red-400/20 rounded-lg p-4 mb-6 text-red-400 text-sm">
          {error}
        </div>
      )}

      {isRunning && (
        <div className="mb-6">
          <PipelineMonitor stages={stages} startedAt={run?.startedAt} status="running" />
        </div>
      )}

      {result && (
        <div className="animate-in">
          {/* Distribution */}
          <Card className="mb-4">
            <h3 className="text-base font-semibold text-white mb-3">Risk Distribution</h3>
            <div className="flex gap-4">
              {Object.entries(result.tier_distribution).map(([tier, count]) => (
                <div key={tier} className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${tierColors[tier] || 'bg-slate-500'}`} />
                  <span className="text-sm text-slate-300">{tier}: <strong className="text-white">{count}</strong></span>
                </div>
              ))}
            </div>
            {/* Bar chart */}
            <div className="mt-4 flex gap-1 h-6 rounded-lg overflow-hidden">
              {Object.entries(result.tier_distribution).map(([tier, count]) => (
                <div
                  key={tier}
                  className={`${tierColors[tier]} transition-all`}
                  style={{ flex: count }}
                  title={`${tier}: ${count}`}
                />
              ))}
            </div>
          </Card>

          {/* Assessments */}
          <Card>
            <h3 className="text-base font-semibold text-white mb-4">
              Endpoint Assessments ({result.total_endpoints})
            </h3>
            <div className="space-y-3">
              {result.assessments.map((a, i) => (
                <div
                  key={i}
                  className="p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <MethodBadge method={a.method} />
                    <code className="text-sm text-white font-mono">{a.path}</code>
                    <RiskBadge tier={a.risk_tier} />
                    <span className="text-xs text-slate-400 ml-auto">
                      Score: {(a.risk_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-xs text-slate-500">
                      → {a.recommended_test_count} tests
                    </span>
                  </div>

                  {/* Risk score bar */}
                  <div className="w-full bg-slate-600/50 rounded-full h-1.5 mb-2">
                    <div
                      className={`h-1.5 rounded-full ${tierColors[a.risk_tier]}`}
                      style={{ width: `${a.risk_score * 100}%` }}
                    />
                  </div>

                  {/* Factors */}
                  {a.factors.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {a.factors.map((f, j) => (
                        <span
                          key={j}
                          className="text-xs text-slate-400 bg-slate-600/50 px-2 py-0.5 rounded"
                          title={f.reasoning}
                        >
                          {f.name}: {(f.score * 100).toFixed(0)}%
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
