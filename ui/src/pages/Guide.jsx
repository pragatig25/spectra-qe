import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen, FileSearch, ShieldAlert, FlaskConical, FileText, Terminal,
  ChevronDown, ChevronRight, ArrowRight, Zap, CheckCircle, Lightbulb,
  Settings, Upload, Play, Eye, Download, AlertTriangle
} from 'lucide-react';
import { Card } from '../components/Card';

const STEPS = [
  {
    id: 1,
    icon: Settings,
    title: 'Configure API Keys',
    color: 'slate',
    navigateTo: null,
    summary: 'Set up your LLM provider credentials to enable AI-powered features.',
    details: [
      { type: 'action', text: 'Copy .env.example to .env in the project root' },
      { type: 'action', text: 'Add your OpenAI or Anthropic API key' },
      { type: 'action', text: 'Optionally configure LangSmith and W&B keys for observability' },
    ],
    code: `cp .env.example .env\n# Edit .env:\nOPENAI_API_KEY=sk-...\nLLM_PROVIDER=openai\nLLM_MODEL=gpt-4o`,
    tip: 'Risk Scoring and Test Generation require LLM API keys. Spec Parsing works without them.',
    highlight: 'Required for AI features',
  },
  {
    id: 2,
    icon: FileSearch,
    title: 'Parse an API Spec',
    color: 'blue',
    navigateTo: '/parse',
    summary: 'Feed an OpenAPI 3.x spec to extract structured endpoint data.',
    details: [
      { type: 'action', text: 'Go to the Spec Parser page' },
      { type: 'action', text: 'Select a demo spec (Petstore) or paste your own OpenAPI YAML/JSON' },
      { type: 'action', text: 'Click Parse to extract all endpoints' },
      { type: 'result', text: 'View: HTTP methods, paths, parameters, auth requirements, request bodies' },
    ],
    code: `# CLI equivalent:\nqe-platform parse demo/petstore_openapi.yaml`,
    tip: 'The parser detects auth requirements automatically from security schemes. Endpoints marked AUTH will get auth_bypass test cases.',
    highlight: 'No API key needed',
  },
  {
    id: 3,
    icon: ShieldAlert,
    title: 'Score Risk per Endpoint',
    color: 'yellow',
    navigateTo: '/risk',
    summary: 'LLM analyzes each endpoint and assigns a risk tier: Low, Med, High, or Critical.',
    details: [
      { type: 'action', text: 'Go to the Risk Scorer page' },
      { type: 'action', text: 'Select a spec and click Score Risk' },
      { type: 'wait', text: 'The LLM evaluates each endpoint individually (may take 30-60 seconds)' },
      { type: 'result', text: 'View: Risk tier, score, factors (data sensitivity, auth, write ops, complexity)' },
      { type: 'result', text: 'Higher risk = more test cases recommended' },
    ],
    code: `# CLI equivalent:\nqe-platform risk-score demo/petstore_openapi.yaml -o risk_report.json`,
    tip: 'Risk scoring considers 5 factors: data sensitivity, authentication, write operations, downstream dependencies, and input complexity.',
    highlight: 'Requires LLM API key',
  },
  {
    id: 4,
    icon: FlaskConical,
    title: 'Generate Test Cases',
    color: 'green',
    navigateTo: '/generate',
    summary: 'Full pipeline: parse → risk score → generate tests → deduplicate near-duplicates.',
    details: [
      { type: 'action', text: 'Go to the Test Generator page' },
      { type: 'action', text: 'Select a spec and click Generate Tests' },
      { type: 'wait', text: 'Runs the complete pipeline (may take 1-3 minutes for all endpoints)' },
      { type: 'result', text: 'View generated test suites grouped by endpoint' },
      { type: 'result', text: 'Each test case shows: type, input data, expected status, assertions' },
      { type: 'result', text: 'Near-duplicate tests are automatically removed (cosine similarity > 0.92)' },
    ],
    code: `# CLI equivalent:\nqe-platform generate demo/petstore_openapi.yaml --skip-execution`,
    tip: 'Test types generated: happy_path, boundary, auth_bypass, malformed_input, and negative. Click the input data expander to see exact payloads.',
    highlight: 'Requires LLM + Embedding API keys',
  },
  {
    id: 5,
    icon: FileText,
    title: 'View Reports',
    color: 'purple',
    navigateTo: '/report',
    summary: 'After execution, view structured reports with coverage, costs, and self-healing stats.',
    details: [
      { type: 'action', text: 'Run generation with execution enabled (provide a base URL)' },
      { type: 'result', text: 'JSON + Markdown reports saved to reports/ directory' },
      { type: 'result', text: 'Metrics: pass rate, coverage %, risk distribution, token costs' },
      { type: 'result', text: 'Self-healing stats show how many broken selectors were repaired by LLM' },
    ],
    code: `# CLI with execution:\nqe-platform generate demo/petstore_openapi.yaml --base-url http://localhost:3000`,
    tip: 'Reports include cost-per-test-case metrics via the W&B token dashboard. Great for optimizing prompts over time.',
    highlight: 'Requires a running target API',
  },
  {
    id: 6,
    icon: Terminal,
    title: 'CLI & Docker',
    color: 'slate',
    navigateTo: null,
    summary: 'Everything in the UI is also available via CLI and Docker for CI/CD integration.',
    details: [
      { type: 'action', text: 'CLI: qe-platform parse | risk-score | generate | demo' },
      { type: 'action', text: 'Docker: docker compose up app (full-stack on port 8000)' },
      { type: 'action', text: 'CI/CD: GitHub Actions runs lint → test → build on every PR' },
      { type: 'result', text: 'All commands output JSON for pipeline integration' },
    ],
    code: `# Docker:\ndocker compose up app\n\n# Run tests:\ndocker compose up test\n\n# CI:\ngit push  # triggers .github/workflows/ci.yml`,
    tip: 'The Docker image bundles the React UI — deploy a single container and access the full platform at port 8000.',
    highlight: 'CI/CD ready',
  },
];

const colorMap = {
  blue: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30', ring: 'ring-blue-500/20', solid: 'bg-blue-500' },
  yellow: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30', ring: 'ring-yellow-500/20', solid: 'bg-yellow-500' },
  green: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30', ring: 'ring-green-500/20', solid: 'bg-green-500' },
  purple: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/30', ring: 'ring-purple-500/20', solid: 'bg-purple-500' },
  slate: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/30', ring: 'ring-slate-500/20', solid: 'bg-slate-500' },
};

export default function Guide() {
  const [expandedSteps, setExpandedSteps] = useState({ 1: true });
  const [completedSteps, setCompletedSteps] = useState({});
  const navigate = useNavigate();

  function toggleStep(id) {
    setExpandedSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function markComplete(id) {
    setCompletedSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  const completedCount = Object.values(completedSteps).filter(Boolean).length;
  const progressPct = Math.round((completedCount / STEPS.length) * 100);

  return (
    <div className="animate-in max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 rounded-lg bg-indigo-400/10">
          <BookOpen size={22} className="text-indigo-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Getting Started Guide</h1>
          <p className="text-sm text-slate-400">Step-by-step walkthrough of the Spectra pipeline</p>
        </div>
      </div>

      {/* Progress bar */}
      <Card className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-white">Your Progress</span>
          <span className="text-sm text-slate-400">{completedCount}/{STEPS.length} steps</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2.5 overflow-hidden">
          <div
            className="h-2.5 rounded-full bg-gradient-to-r from-blue-500 via-green-500 to-purple-500 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        {completedCount === STEPS.length && (
          <div className="mt-3 flex items-center gap-2 text-green-400 text-sm">
            <CheckCircle size={16} />
            <span className="font-medium">All steps complete — you're ready to demo!</span>
          </div>
        )}
      </Card>

      {/* Pipeline overview */}
      <Card className="mb-6">
        <h2 className="text-base font-semibold text-white mb-3">Pipeline at a Glance</h2>
        <div className="flex items-center gap-1 overflow-x-auto pb-2">
          {STEPS.slice(0, 5).map((step, i) => {
            const c = colorMap[step.color];
            return (
              <div key={step.id} className="flex items-center shrink-0">
                <button
                  onClick={() => { toggleStep(step.id); setExpandedSteps(prev => ({ ...prev, [step.id]: true })); }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                    ${completedSteps[step.id] ? 'bg-green-500/10 border-green-500/30 text-green-400' : `${c.bg} ${c.border} ${c.text}`}
                    hover:ring-2 ${c.ring}`}
                >
                  {completedSteps[step.id] ? <CheckCircle size={12} /> : <step.icon size={12} />}
                  {step.title.split(' ').slice(0, 2).join(' ')}
                </button>
                {i < 4 && <ArrowRight size={14} className="text-slate-600 mx-1 shrink-0" />}
              </div>
            );
          })}
        </div>
      </Card>

      {/* Steps */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-5 top-0 bottom-0 w-px bg-slate-700" />

        <div className="space-y-4">
          {STEPS.map((step) => {
            const c = colorMap[step.color];
            const isExpanded = expandedSteps[step.id];
            const isDone = completedSteps[step.id];

            return (
              <div key={step.id} className="relative pl-12">
                {/* Step number circle */}
                <div className={`absolute left-2.5 top-4 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold
                  ${isDone ? 'bg-green-500 text-white' : `${c.solid} text-white`} ring-4 ring-slate-950 z-10 transition-colors`}>
                  {isDone ? '✓' : step.id}
                </div>

                <Card className={`transition-all ${isExpanded ? `ring-1 ${c.ring}` : ''} ${isDone ? 'opacity-75' : ''}`}>
                  {/* Header */}
                  <div className="flex items-start gap-3 cursor-pointer" onClick={() => toggleStep(step.id)}>
                    <div className={`p-2 rounded-lg ${c.bg} shrink-0`}>
                      <step.icon size={18} className={c.text} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-base font-semibold text-white">{step.title}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${c.bg} ${c.text} font-medium`}>
                          {step.highlight}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-0.5">{step.summary}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {isDone && <CheckCircle size={16} className="text-green-400" />}
                      {isExpanded ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
                    </div>
                  </div>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div className="mt-4 space-y-4 animate-in">
                      {/* Action list */}
                      <div className="space-y-2">
                        {step.details.map((d, i) => (
                          <div key={i} className="flex items-start gap-2.5">
                            {d.type === 'action' && (
                              <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0 mt-0.5">
                                <Play size={10} className="text-blue-400" />
                              </div>
                            )}
                            {d.type === 'wait' && (
                              <div className="w-5 h-5 rounded-full bg-yellow-500/20 flex items-center justify-center shrink-0 mt-0.5">
                                <Zap size={10} className="text-yellow-400" />
                              </div>
                            )}
                            {d.type === 'result' && (
                              <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center shrink-0 mt-0.5">
                                <Eye size={10} className="text-green-400" />
                              </div>
                            )}
                            <span className="text-sm text-slate-300">{d.text}</span>
                          </div>
                        ))}
                      </div>

                      {/* Tip */}
                      <div className="flex items-start gap-2 bg-indigo-500/5 border border-indigo-500/20 rounded-lg p-3">
                        <Lightbulb size={16} className="text-indigo-400 shrink-0 mt-0.5" />
                        <p className="text-xs text-indigo-300">{step.tip}</p>
                      </div>

                      {/* Code block */}
                      <div className="bg-slate-900 rounded-lg p-3 border border-slate-700">
                        <div className="flex items-center gap-2 mb-2">
                          <Terminal size={12} className="text-slate-500" />
                          <span className="text-xs text-slate-500 font-medium">CLI equivalent</span>
                        </div>
                        <pre className="text-xs text-green-400 font-mono leading-relaxed whitespace-pre-wrap">{step.code}</pre>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-3 pt-1">
                        <button
                          onClick={() => markComplete(step.id)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                            isDone
                              ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                          }`}
                        >
                          <CheckCircle size={12} />
                          {isDone ? 'Completed' : 'Mark as done'}
                        </button>

                        {step.navigateTo && (
                          <button
                            onClick={() => navigate(step.navigateTo)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium ${c.bg} ${c.text} hover:ring-2 ${c.ring} transition-all`}
                          >
                            <ArrowRight size={12} />
                            Open {step.title.split(' ').slice(0, 2).join(' ')}
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </Card>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer quick ref */}
      <Card className="mt-8">
        <h3 className="text-base font-semibold text-white mb-3">Quick Reference</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="bg-slate-700/30 rounded-lg p-3">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Test Types Generated</h4>
            <div className="flex flex-wrap gap-1.5">
              {['happy_path', 'boundary', 'auth_bypass', 'malformed_input', 'negative'].map((t) => (
                <span key={t} className="text-xs bg-slate-600/50 text-slate-300 px-2 py-0.5 rounded">{t}</span>
              ))}
            </div>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-3">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Risk Tiers</h4>
            <div className="flex flex-wrap gap-1.5">
              {[
                { tier: 'Low', color: 'text-green-400 bg-green-400/10' },
                { tier: 'Med', color: 'text-yellow-400 bg-yellow-400/10' },
                { tier: 'High', color: 'text-orange-400 bg-orange-400/10' },
                { tier: 'Critical', color: 'text-red-400 bg-red-400/10' },
              ].map((r) => (
                <span key={r.tier} className={`text-xs px-2 py-0.5 rounded font-medium ${r.color}`}>{r.tier}</span>
              ))}
            </div>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-3">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Stack</h4>
            <p className="text-xs text-slate-300">LangChain + Pydantic + FastAPI + React + TailwindCSS</p>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-3">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Dedup Threshold</h4>
            <p className="text-xs text-slate-300">Cosine similarity &gt; 0.92 → removed as near-duplicate</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
