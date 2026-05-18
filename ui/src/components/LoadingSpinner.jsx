export default function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="flex gap-1.5 mb-4">
        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full loading-dot" />
        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full loading-dot" />
        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full loading-dot" />
      </div>
      <p className="text-sm text-slate-400">{text}</p>
    </div>
  );
}
