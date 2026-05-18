const TIER_COLORS = {
  Low: 'bg-green-400/10 text-green-400 border-green-400/20',
  Med: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
  High: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
  Critical: 'bg-red-400/10 text-red-400 border-red-400/20',
};

const METHOD_COLORS = {
  GET: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
  POST: 'bg-green-400/10 text-green-400 border-green-400/20',
  PUT: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
  PATCH: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
  DELETE: 'bg-red-400/10 text-red-400 border-red-400/20',
};

export function RiskBadge({ tier }) {
  return (
    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full border ${TIER_COLORS[tier] || TIER_COLORS.Low}`}>
      {tier}
    </span>
  );
}

export function MethodBadge({ method }) {
  return (
    <span className={`inline-flex px-2 py-0.5 text-xs font-bold font-mono rounded border ${METHOD_COLORS[method] || METHOD_COLORS.GET}`}>
      {method}
    </span>
  );
}

export function TypeBadge({ type }) {
  const colors = {
    happy_path: 'bg-green-400/10 text-green-400',
    boundary: 'bg-yellow-400/10 text-yellow-400',
    auth_bypass: 'bg-red-400/10 text-red-400',
    malformed_input: 'bg-orange-400/10 text-orange-400',
    negative: 'bg-purple-400/10 text-purple-400',
  };

  return (
    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded ${colors[type] || 'bg-slate-600 text-slate-300'}`}>
      {type.replace('_', ' ')}
    </span>
  );
}
