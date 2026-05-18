import { useState, useEffect } from 'react';
import { FlaskConical, Play, ChevronDown, ChevronRight, Code } from 'lucide-react';
import { Card, StatCard } from '../components/Card';
import { RiskBadge, MethodBadge, TypeBadge } from '../components/Badge';
import PipelineMonitor from '../components/PipelineMonitor';
import { api } from '../lib/api';
import { useGeneratePipeline } from '../hooks/usePipeline';

export default function TestGenerator() {
  const [specs, setSpecs] = useState([]);
  const [selectedSpec, setSelectedSpec] = useState('petstore');
  const [expandedSuites, setExpandedSuites] = useState({});
  const { run, start, isRunning, result, error, stages } = useGeneratePipeline();

  useEffect(() => {
    api.specs().then(setSpecs).catch(() => {});
  }, []);

  useEffect(() => {
    if (result?.suites) {
      const expanded = {};
      result.suites.forEach((_, i) => { expanded[i] = true; });
      setExpandedSuites(expanded);
    }
  }, [result]);

  function toggleSuite(i) {
    setExpandedSuites((prev) => ({ ...prev, [i]: !prev[i] }));
  }

  return (
    <div className="animate-in max-w-5xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 rounded-lg bg-green-400/10">
          <FlaskConical size={22} className="text-green-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Test Generator</h1>
          <p className="text-sm text-slate-400">Generate risk-scored test cases with LangChain + Pydantic</p>
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
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Play size={14} />
            {isRunning ? 'Generating...' : 'Generate Tests'}
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Full pipeline: Parse → Risk Score → Generate → Deduplicate. Requires LLM API keys.
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
          {/* Summary stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Run ID" value={result.run_id.slice(4, 16)} color="blue" />
            <StatCard label="Endpoints" value={result.total_endpoints} color="purple" />
            <StatCard label="Tests Generated" value={result.total_tests_generated} color="green" />
            <StatCard label="After Dedup" value={result.total_tests_after_dedup} sublabel={`${result.duplicates_removed} removed`} color="yellow" />
          </div>

          {/* Suites */}
          {result.suites.map((suite, i) => (
            <Card key={i} className="mb-4">
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
        </div>
      )}
    </div>
  );
}
