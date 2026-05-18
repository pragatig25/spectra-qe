import { useState, useEffect } from 'react';
import {
  FileText, Play, Download, ChevronDown, ChevronRight, Clock,
  Check, X, BarChart3, Shield, FlaskConical, Code, Layers,
} from 'lucide-react';
import { Card, StatCard } from '../components/Card';
import { RiskBadge, MethodBadge, TypeBadge } from '../components/Badge';
import PipelineMonitor from '../components/PipelineMonitor';
import { api } from '../lib/api';
import { useReportPipeline, useReportHistory } from '../hooks/usePipeline';

function DistributionBar({ data, colorMap }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  return (
    <div className="space-y-2">
      {Object.entries(data).map(([key, count]) => (
        <div key={key} className="flex items-center gap-3">
          <span className="text-xs text-slate-400 w-28 truncate">{key.replace('_', ' ')}</span>
          <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${colorMap[key] || 'bg-blue-500'}`}
              style={{ width: `${(count / total) * 100}%` }}
            />
          </div>
          <span className="text-xs text-slate-400 tabular-nums w-8 text-right">{count}</span>
        </div>
      ))}
    </div>
  );
}

function ReportView({ result, onExport }) {
  const [expandedSuites, setExpandedSuites] = useState({});
  const [activeTab, setActiveTab] = useState('overview');

  const report = result.report || {};
  const coverage = report.coverage || {};
  const tokenCost = report.token_cost || {};
  const selfHealing = report.self_healing || {};

  const totalTests = result.total_tests_after_dedup || result.total_tests_generated || 0;

  const tierColors = {
    Low: 'bg-green-500', Med: 'bg-yellow-500', High: 'bg-orange-500', Critical: 'bg-red-500',
  };
  const typeColors = {
    happy_path: 'bg-green-500', boundary: 'bg-yellow-500', auth_bypass: 'bg-red-500',
    malformed_input: 'bg-orange-500', negative: 'bg-purple-500',
  };

  function toggleSuite(i) {
    setExpandedSuites((prev) => ({ ...prev, [i]: !prev[i] }));
  }

  const tabs = [
    { key: 'overview', label: 'Overview', icon: BarChart3 },
    { key: 'coverage', label: 'Coverage', icon: Shield },
    { key: 'tests', label: 'Test Suites', icon: FlaskConical },
    { key: 'cost', label: 'Token Cost', icon: Layers },
  ];

  return (
    <div className="animate-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white">
            Report: {result.spec_title}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Run {result.run_id} — {result.total_endpoints} endpoints — {totalTests} tests
            {result.duration_seconds && ` — ${result.duration_seconds.toFixed(1)}s`}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onExport('json')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs font-medium transition-colors"
          >
            <Download size={12} /> JSON
          </button>
          <button
            onClick={() => onExport('markdown')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs font-medium transition-colors"
          >
            <Download size={12} /> Markdown
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-800/50 p-1 rounded-lg w-fit">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === key
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Tests Generated" value={result.total_tests_generated} color="green" />
            <StatCard label="After Dedup" value={result.total_tests_after_dedup} sublabel={`${result.duplicates_removed} removed`} color="yellow" />
            <StatCard label="Endpoints" value={result.total_endpoints} color="blue" />
            <StatCard label="Coverage" value={`${(coverage.coverage_pct || 100).toFixed(0)}%`} color="purple" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <h3 className="text-sm font-semibold text-white mb-3">Risk Distribution</h3>
              {result.tier_distribution ? (
                <>
                  <DistributionBar data={result.tier_distribution} colorMap={tierColors} />
                  <div className="mt-3 flex gap-1 h-4 rounded-lg overflow-hidden">
                    {Object.entries(result.tier_distribution).map(([tier, count]) => (
                      <div
                        key={tier}
                        className={`${tierColors[tier]} transition-all`}
                        style={{ flex: count }}
                        title={`${tier}: ${count}`}
                      />
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-xs text-slate-500">No risk data available</p>
              )}
            </Card>
            <Card>
              <h3 className="text-sm font-semibold text-white mb-3">Test Type Distribution</h3>
              {coverage.test_type_distribution && Object.keys(coverage.test_type_distribution).length > 0 ? (
                <DistributionBar data={coverage.test_type_distribution} colorMap={typeColors} />
              ) : (
                <p className="text-xs text-slate-500">No type distribution data</p>
              )}
            </Card>
          </div>

          {report.total_tests > 0 && (
            <Card>
              <h3 className="text-sm font-semibold text-white mb-3">Execution Summary</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[
                  { label: 'Total', value: report.total_tests, color: 'text-white' },
                  { label: 'Passed', value: report.passed, color: 'text-green-400' },
                  { label: 'Failed', value: report.failed, color: 'text-red-400' },
                  { label: 'Errors', value: report.error, color: 'text-orange-400' },
                  { label: 'Healed', value: report.healed, color: 'text-blue-400' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="text-center">
                    <p className={`text-2xl font-bold ${color}`}>{value}</p>
                    <p className="text-xs text-slate-500">{label}</p>
                  </div>
                ))}
              </div>
              {report.pass_rate > 0 && (
                <div className="mt-3">
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                    <span>Pass Rate</span>
                    <span>{report.pass_rate.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 rounded-full" style={{ width: `${report.pass_rate}%` }} />
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>
      )}

      {/* Coverage Tab */}
      {activeTab === 'coverage' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard
              label="Endpoints Covered"
              value={`${coverage.covered_endpoints || result.total_endpoints}/${coverage.total_endpoints || result.total_endpoints}`}
              color="green"
            />
            <StatCard
              label="Coverage %"
              value={`${(coverage.coverage_pct || 100).toFixed(1)}%`}
              color="blue"
            />
            <StatCard
              label="Unique Test Types"
              value={Object.keys(coverage.test_type_distribution || {}).length}
              color="purple"
            />
          </div>

          <Card>
            <h3 className="text-sm font-semibold text-white mb-4">Test Types Breakdown</h3>
            {coverage.test_type_distribution && Object.keys(coverage.test_type_distribution).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(coverage.test_type_distribution).map(([type, count]) => {
                  const totalTyped = Object.values(coverage.test_type_distribution).reduce((a, b) => a + b, 0);
                  const pct = totalTyped > 0 ? ((count / totalTyped) * 100).toFixed(1) : 0;
                  return (
                    <div key={type} className="flex items-center gap-3">
                      <TypeBadge type={type} />
                      <div className="flex-1 h-2.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${typeColors[type] || 'bg-blue-500'}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-sm text-white tabular-nums w-8 text-right">{count}</span>
                      <span className="text-xs text-slate-500 w-12 text-right">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500">Run a report to see coverage data</p>
            )}
          </Card>

          <Card>
            <h3 className="text-sm font-semibold text-white mb-4">Risk Tier Breakdown</h3>
            {coverage.risk_tier_distribution && Object.keys(coverage.risk_tier_distribution).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(coverage.risk_tier_distribution).map(([tier, count]) => {
                  const totalRisk = Object.values(coverage.risk_tier_distribution).reduce((a, b) => a + b, 0);
                  const pct = totalRisk > 0 ? ((count / totalRisk) * 100).toFixed(1) : 0;
                  return (
                    <div key={tier} className="flex items-center gap-3">
                      <RiskBadge tier={tier} />
                      <div className="flex-1 h-2.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${tierColors[tier] || 'bg-slate-500'}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-sm text-white tabular-nums w-8 text-right">{count}</span>
                      <span className="text-xs text-slate-500 w-12 text-right">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-slate-500">Run a report to see risk data</p>
            )}
          </Card>
        </div>
      )}

      {/* Tests Tab */}
      {activeTab === 'tests' && (
        <div className="space-y-4">
          {(result.suites || []).map((suite, i) => (
            <Card key={i}>
              <div
                className="flex items-center gap-3 cursor-pointer"
                onClick={() => toggleSuite(i)}
              >
                {expandedSuites[i] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                <MethodBadge method={suite.method} />
                <code className="text-sm text-white font-mono">{suite.endpoint_path}</code>
                <RiskBadge tier={suite.risk_tier} />
                <span className="text-xs text-slate-400 ml-auto">
                  {suite.test_cases.length} tests
                </span>
              </div>

              {expandedSuites[i] && (
                <div className="mt-4 space-y-3">
                  {suite.test_cases.map((tc, j) => (
                    <div key={j} className="p-3 bg-slate-700/30 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <TypeBadge type={tc.test_type} />
                        <span className="text-sm font-medium text-white">{tc.name}</span>
                        <span className="text-xs text-slate-500 ml-auto">
                          expect {tc.expected_status}
                        </span>
                      </div>
                      {tc.description && (
                        <p className="text-xs text-slate-400 mb-2">{tc.description}</p>
                      )}
                      {tc.input_data && Object.keys(tc.input_data).length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300 flex items-center gap-1">
                            <Code size={12} /> Input Data
                          </summary>
                          <pre className="mt-1 text-xs text-slate-400 bg-slate-800 rounded p-2 overflow-x-auto">
                            {JSON.stringify(tc.input_data, null, 2)}
                          </pre>
                        </details>
                      )}
                      {tc.assertions && tc.assertions.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {tc.assertions.map((a, k) => (
                            <span key={k} className="text-xs text-slate-500 bg-slate-600/30 px-1.5 py-0.5 rounded">
                              {a}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          ))}
          {(!result.suites || result.suites.length === 0) && (
            <Card>
              <p className="text-sm text-slate-500 text-center py-4">No test suites in this report</p>
            </Card>
          )}
        </div>
      )}

      {/* Token Cost Tab */}
      {activeTab === 'cost' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Tokens" value={tokenCost.total_tokens?.toLocaleString() || '—'} color="blue" />
            <StatCard label="Prompt Tokens" value={tokenCost.total_prompt_tokens?.toLocaleString() || '—'} color="green" />
            <StatCard label="Completion Tokens" value={tokenCost.total_completion_tokens?.toLocaleString() || '—'} color="yellow" />
            <StatCard label="Total Cost" value={tokenCost.total_cost_usd ? `$${tokenCost.total_cost_usd.toFixed(4)}` : '—'} color="purple" />
          </div>

          <Card>
            <h3 className="text-sm font-semibold text-white mb-3">Cost Breakdown</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-700/30 rounded-lg">
                  <p className="text-xs text-slate-400">Cost per Test</p>
                  <p className="text-lg font-bold text-white mt-1">
                    {tokenCost.avg_cost_per_test ? `$${tokenCost.avg_cost_per_test.toFixed(6)}` : '—'}
                  </p>
                </div>
                <div className="p-3 bg-slate-700/30 rounded-lg">
                  <p className="text-xs text-slate-400">Duration</p>
                  <p className="text-lg font-bold text-white mt-1">
                    {result.duration_seconds ? `${result.duration_seconds.toFixed(1)}s` : '—'}
                  </p>
                </div>
              </div>

              {selfHealing.total_failures > 0 && (
                <>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mt-4">Self-Healing</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { label: 'Failures', value: selfHealing.total_failures },
                      { label: 'Attempts', value: selfHealing.heal_attempts },
                      { label: 'Successes', value: selfHealing.heal_successes },
                      { label: 'Rate', value: `${selfHealing.heal_rate?.toFixed(1) || 0}%` },
                    ].map(({ label, value }) => (
                      <div key={label} className="p-2 bg-slate-700/30 rounded text-center">
                        <p className="text-sm font-bold text-white">{value}</p>
                        <p className="text-xs text-slate-500">{label}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}

              <p className="text-xs text-slate-600 mt-2">
                Token tracking requires W&B integration. Configure WANDB_API_KEY for detailed per-call metrics.
              </p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

function ReportHistoryItem({ run, isSelected, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
        isSelected
          ? 'bg-blue-600/20 border border-blue-500/30'
          : 'bg-slate-700/30 hover:bg-slate-700/50 border border-transparent'
      }`}
    >
      {run.status === 'complete' ? (
        <Check size={14} className="text-green-400 shrink-0" />
      ) : (
        <X size={14} className="text-red-400 shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white truncate">
          {run.result?.spec_title || run.specId}
        </p>
        <p className="text-xs text-slate-500">
          {run.result?.total_tests_after_dedup || run.result?.total_tests_generated || '?'} tests
          {run.result?.duration_seconds && ` — ${run.result.duration_seconds.toFixed(1)}s`}
        </p>
      </div>
      <span className="text-xs text-slate-600 tabular-nums shrink-0">
        {run.result?.run_id?.slice(4, 12)}
      </span>
    </button>
  );
}

export default function Reports() {
  const [specs, setSpecs] = useState([]);
  const [selectedSpec, setSelectedSpec] = useState('petstore');
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);
  const { run, start, isRunning, result, error, stages } = useReportPipeline();
  const reportHistory = useReportHistory();

  useEffect(() => {
    api.specs().then(setSpecs).catch(() => {});
  }, []);

  const viewResult = selectedHistoryId
    ? reportHistory.find((r) => r.id === selectedHistoryId)?.result
    : result;

  const hasAnyResult = viewResult || reportHistory.length > 0;

  async function handleExport(format) {
    if (!viewResult?.report) return;

    try {
      const res = await fetch('/api/report/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report: viewResult.report, format }),
      });
      const data = await res.json();

      const blob = new Blob([data.content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      try {
        const content = format === 'json'
          ? JSON.stringify(viewResult, null, 2)
          : `# Report ${viewResult.run_id}\n\nExport failed — raw JSON attached.\n\n\`\`\`json\n${JSON.stringify(viewResult, null, 2)}\n\`\`\``;

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report_${viewResult.run_id}.${format === 'json' ? 'json' : 'md'}`;
        a.click();
        URL.revokeObjectURL(url);
      } catch { /* ignore */ }
    }
  }

  return (
    <div className="animate-in max-w-6xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 rounded-lg bg-purple-400/10">
          <FileText size={22} className="text-purple-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Reports</h1>
          <p className="text-sm text-slate-400">
            Full pipeline reports with coverage, risk, and cost metrics
          </p>
        </div>
      </div>

      {/* Generate controls */}
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
            onClick={() => { setSelectedHistoryId(null); start(selectedSpec); }}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Play size={14} />
            {isRunning ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Full pipeline: Parse → Risk Score → Generate → Deduplicate → Report. Requires LLM API key.
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

      {/* Report History */}
      {reportHistory.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Clock size={14} /> Report History ({reportHistory.length})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {reportHistory.map((r) => (
              <ReportHistoryItem
                key={r.id}
                run={r}
                isSelected={selectedHistoryId ? selectedHistoryId === r.id : run?.id === r.id}
                onClick={() => setSelectedHistoryId(selectedHistoryId === r.id ? null : r.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Report content */}
      {viewResult ? (
        <ReportView result={viewResult} onExport={handleExport} />
      ) : !isRunning && (
        <Card>
          <div className="text-center py-12">
            <FileText size={48} className="text-slate-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No Reports Yet</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto mb-4">
              Click Generate Report to run the full pipeline and produce a comprehensive report
              with coverage metrics, risk distribution, test suites, and cost analysis.
            </p>
            <div className="flex flex-wrap gap-3 justify-center text-xs text-slate-500">
              <span className="bg-slate-700/50 px-3 py-1.5 rounded-lg">JSON export</span>
              <span className="bg-slate-700/50 px-3 py-1.5 rounded-lg">Markdown export</span>
              <span className="bg-slate-700/50 px-3 py-1.5 rounded-lg">Coverage metrics</span>
              <span className="bg-slate-700/50 px-3 py-1.5 rounded-lg">Risk distribution</span>
              <span className="bg-slate-700/50 px-3 py-1.5 rounded-lg">Token costs</span>
              <span className="bg-slate-700/50 px-3 py-1.5 rounded-lg">Self-healing stats</span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
