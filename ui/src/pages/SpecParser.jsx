import { useState, useEffect } from 'react';
import { FileSearch, Upload, Play } from 'lucide-react';
import { Card } from '../components/Card';
import { MethodBadge } from '../components/Badge';
import LoadingSpinner from '../components/LoadingSpinner';
import { api } from '../lib/api';
import { useParsePipeline } from '../hooks/usePipeline';

export default function SpecParser() {
  const [specs, setSpecs] = useState([]);
  const [selectedSpec, setSelectedSpec] = useState('petstore');
  const [customSpec, setCustomSpec] = useState('');
  const [useCustom, setUseCustom] = useState(false);
  const { run, start, isRunning, result, error } = useParsePipeline();

  useEffect(() => {
    api.specs().then(setSpecs).catch(() => {});
  }, []);

  function handleParse() {
    const body = useCustom
      ? { spec_content: customSpec }
      : { spec_id: selectedSpec };
    start(body);
  }

  return (
    <div className="animate-in max-w-5xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 rounded-lg bg-blue-400/10">
          <FileSearch size={22} className="text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Spec Parser</h1>
          <p className="text-sm text-slate-400">Parse OpenAPI 3.x specs into structured endpoint data</p>
        </div>
      </div>

      <Card className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => setUseCustom(false)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              !useCustom ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Demo Specs
          </button>
          <button
            onClick={() => setUseCustom(true)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              useCustom ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Upload size={14} className="inline mr-1" />
            Custom Spec
          </button>
        </div>

        {!useCustom ? (
          <div className="flex gap-3">
            <select
              value={selectedSpec}
              onChange={(e) => setSelectedSpec(e.target.value)}
              className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            >
              {specs.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} — {s.endpoint_count} endpoints
                </option>
              ))}
            </select>
            <button
              onClick={handleParse}
              disabled={isRunning}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Play size={14} />
              Parse
            </button>
          </div>
        ) : (
          <div>
            <textarea
              value={customSpec}
              onChange={(e) => setCustomSpec(e.target.value)}
              placeholder="Paste your OpenAPI YAML/JSON spec here..."
              rows={10}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-blue-500 resize-y"
            />
            <button
              onClick={handleParse}
              disabled={isRunning || !customSpec.trim()}
              className="mt-3 flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Play size={14} />
              Parse Custom Spec
            </button>
          </div>
        )}
      </Card>

      {error && (
        <div className="bg-red-400/10 border border-red-400/20 rounded-lg p-4 mb-6 text-red-400 text-sm">
          {error}
        </div>
      )}

      {isRunning && <LoadingSpinner text="Parsing spec..." />}

      {result && (
        <div className="animate-in">
          <Card className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold text-white">{result.title}</h2>
              <span className="text-xs text-slate-400">v{result.version}</span>
            </div>
            <p className="text-sm text-slate-400">{result.description}</p>
            <div className="flex gap-4 mt-3 text-xs text-slate-500">
              <span>Base URL: <code className="text-slate-300">{result.base_url}</code></span>
              <span>Endpoints: <strong className="text-white">{result.endpoint_count}</strong></span>
            </div>
          </Card>

          <Card>
            <h3 className="text-base font-semibold text-white mb-4">Endpoints</h3>
            <div className="space-y-2">
              {result.endpoints.map((ep, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition-colors"
                >
                  <MethodBadge method={ep.method} />
                  <code className="text-sm text-white font-mono flex-1">{ep.path}</code>
                  <span className="text-xs text-slate-400 max-w-xs truncate">{ep.summary}</span>
                  {ep.requires_auth && (
                    <span className="text-xs text-yellow-400 bg-yellow-400/10 px-2 py-0.5 rounded">AUTH</span>
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
