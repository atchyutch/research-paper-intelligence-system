import { X, FileText, BookMarked } from 'lucide-react';

export default function CitationPanel({ citations, onClose }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-ink-950/20 backdrop-blur-sm animate-fade-in" />

      {/* Panel */}
      <div className="relative w-full max-w-sm bg-white border-l border-paper-300/60 shadow-2xl
        h-full overflow-y-auto animate-slide-right"
        onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className="sticky top-0 bg-white/90 backdrop-blur-lg border-b border-paper-200 px-5 py-4
          flex items-center justify-between z-10">
          <div className="flex items-center gap-2">
            <BookMarked size={16} className="text-accent" />
            <h3 className="font-display text-base font-semibold text-ink-900">
              Sources ({citations.length})
            </h3>
          </div>
          <button onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-paper-200 transition-colors">
            <X size={16} className="text-ink-400" />
          </button>
        </div>

        {/* Citations list */}
        <div className="p-5 space-y-3">
          {citations.map((c, i) => (
            <div key={i}
              className="rounded-xl border border-paper-300/60 bg-paper-50 p-4 hover:shadow-sm transition-shadow">
              {/* Citation number badge */}
              <div className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-accent text-white text-xs font-bold
                  flex items-center justify-center flex-shrink-0">
                  {c['Citation Number']}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-ink-900 truncate">
                    {c.Document}
                  </p>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-ink-500">
                    {c.Section && c.Section !== 'Unknown' && (
                      <span className="flex items-center gap-1">
                        <FileText size={11} />
                        {c.Section}
                      </span>
                    )}
                    {c.Page && c.Page !== 'Unknown' && (
                      <span>Page {c.Page}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
