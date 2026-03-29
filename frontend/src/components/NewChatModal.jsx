import { useState } from 'react';
import { conversations as convApi } from '../lib/api';
import toast from 'react-hot-toast';
import { X, MessageSquarePlus, FileText, Loader2, Check } from 'lucide-react';

export default function NewChatModal({ docs, onClose, onCreated }) {
  const [selectedDocs, setSelectedDocs] = useState(new Set());
  const [creating, setCreating] = useState(false);

  function toggleDoc(docId) {
    setSelectedDocs((prev) => {
      const next = new Set(prev);
      if (next.has(docId)) next.delete(docId);
      else next.add(docId);
      return next;
    });
  }

  async function handleCreate() {
    if (selectedDocs.size === 0) {
      toast.error('Select at least one document');
      return;
    }
    setCreating(true);
    try {
      const convo = await convApi.create();
      await convApi.addDocuments(convo.conversation_id, [...selectedDocs]);
      onCreated(convo.conversation_id);
    } catch (err) {
      toast.error(err.message || 'Failed to create conversation');
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/30 backdrop-blur-sm animate-fade-in"
      onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl border border-paper-300/60 w-full max-w-lg mx-4 animate-slide-up"
        onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-paper-200">
          <h2 className="font-display text-lg font-semibold text-ink-900">New Conversation</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-paper-200 transition-colors">
            <X size={18} className="text-ink-400" />
          </button>
        </div>

        <div className="px-6 py-5">
          <p className="text-sm text-ink-600 mb-4">
            Select the documents you want to discuss in this conversation. Only processed documents will produce results.
          </p>

          {docs.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="w-8 h-8 text-ink-300 mx-auto mb-2" strokeWidth={1.4} />
              <p className="text-sm text-ink-500">No documents uploaded yet.</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {docs.map((doc) => {
                const selected = selectedDocs.has(doc.document_id);
                return (
                  <button key={doc.document_id} onClick={() => toggleDoc(doc.document_id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border text-left transition-all
                      ${selected
                        ? 'border-accent bg-accent-muted ring-1 ring-accent/30'
                        : 'border-paper-300 hover:border-ink-300 hover:bg-paper-50'
                      }`}>
                    <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all
                      ${selected ? 'bg-accent border-accent' : 'border-ink-300'}`}>
                      {selected && <Check size={12} className="text-white" strokeWidth={3} />}
                    </div>
                    <FileText size={16} className={selected ? 'text-accent' : 'text-ink-400'} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-ink-900 truncate">{doc.file_name}</p>
                      <p className="text-xs text-ink-400">{doc.page_count} pages</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-paper-200 flex justify-between items-center">
          <span className="text-xs text-ink-400">
            {selectedDocs.size} document{selectedDocs.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex gap-3">
            <button onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm text-ink-600 hover:bg-paper-200 transition-colors">
              Cancel
            </button>
            <button onClick={handleCreate}
              disabled={selectedDocs.size === 0 || creating}
              className="px-5 py-2 rounded-lg bg-accent text-white text-sm font-medium
                hover:bg-accent-dark transition-all disabled:opacity-40 disabled:cursor-not-allowed
                flex items-center gap-2">
              {creating ? (
                <><Loader2 size={15} className="animate-spin" /> Creating...</>
              ) : (
                <><MessageSquarePlus size={15} /> Start Chat</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
