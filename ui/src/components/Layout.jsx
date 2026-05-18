import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, FileSearch, ShieldAlert, FlaskConical, FileText, BookOpen } from 'lucide-react';
import RunHistory from './RunHistory';
import { useActiveRuns } from '../hooks/usePipeline';

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', pipelineType: null },
  { to: '/guide', icon: BookOpen, label: 'Guide', pipelineType: null },
  { to: '/parse', icon: FileSearch, label: 'Spec Parser', pipelineType: 'parse' },
  { to: '/risk', icon: ShieldAlert, label: 'Risk Scorer', pipelineType: 'risk_score' },
  { to: '/generate', icon: FlaskConical, label: 'Test Generator', pipelineType: 'generate' },
  { to: '/report', icon: FileText, label: 'Reports', pipelineType: 'report' },
];

export default function Layout() {
  const activeRuns = useActiveRuns();
  const activeTypes = new Set(activeRuns.map((r) => r.type));

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <nav className="w-64 bg-slate-900 border-r border-slate-700 flex flex-col shrink-0">
        <div className="p-5 border-b border-slate-700">
          <h1 className="text-lg font-bold text-white tracking-tight">QE Platform</h1>
          <p className="text-xs text-slate-400 mt-1">AI Test Generation</p>
        </div>

        <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label, pipelineType }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              <span className="flex-1">{label}</span>
              {pipelineType && activeTypes.has(pipelineType) && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                </span>
              )}
            </NavLink>
          ))}

          <div className="pt-3 mt-3 border-t border-slate-700/50">
            <RunHistory />
          </div>
        </div>

        <div className="p-4 border-t border-slate-700">
          <div className="text-xs text-slate-500">
            <p>v0.1.0 — LangChain + Pydantic</p>
            <p className="mt-1">Python + React</p>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-slate-950 p-6">
        <Outlet />
      </main>
    </div>
  );
}
