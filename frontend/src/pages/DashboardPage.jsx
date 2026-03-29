import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { documents as docsApi, conversations as convApi } from '../lib/api';
import toast from 'react-hot-toast';
import {
  BookOpen, Upload, FileText, MessageSquarePlus, Trash2, LogOut,
  ChevronRight, Loader2, Cpu, CheckCircle2, Clock, X
} from 'lucide-react';
import UploadModal from '../components/UploadModal';
import NewChatModal from '../components/NewChatModal';

export default function DashboardPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [docs, setDocs] = useState([]);
  const [convos, setConvos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [showNewChat, setShowNewChat] = useState(false);
  const [processingIds, setProcessingIds] = useState(new Set());

  const fetchData = useCallback(async () => {
    try {
      const [d, c] = await Promise.all([docsApi.list(), convApi.list()]);
      setDocs(d || []);
      setConvos(c || []);
    } catch (err) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  async function handleProcess(docId) {
    setProcessingIds((s) => new Set(s).add(docId));
    try {
      await docsApi.process(docId);
      toast.success('Document processed — ready for chat');
    } catch (err) {
      toast.error(err.message || 'Processing failed');
    } finally {
      setProcessingIds((s) => {
        const next = new Set(s);
        next.delete(docId);
        return next;
      });
    }
  }

  async function handleDeleteDoc(docId) {
    try {
      await docsApi.delete(docId);
      setDocs((d) => d.filter((x) => x.document_id !== docId));
      toast.success('Document deleted');
    } catch (err) {
      toast.error(err.message || 'Delete failed');
    }
  }

  async function handleDeleteConvo(convoId) {
    try {
      await convApi.delete(convoId);
      setConvos((c) => c.filter((x) => x.conversation_id !== convoId));
      toast.success('Conversation deleted');
    } catch (err) {
      toast.error(err.message || 'Delete failed');
    }
  }

  function handleUploadDone() {
    setShowUpload(false);
    fetchData();
  }

  function handleChatCreated(conversationId) {
    setShowNewChat(false);
    navigate(`/chat/${conversationId}`);
  }

  return (
    <div className="min-h-screen bg-paper-100">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-paper-100/80 backdrop-blur-lg border-b border-paper-300/60">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-ink-950 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-paper-50" strokeWidth={1.8} />
            </div>
            <span className="font-display text-xl font-semibold tracking-tight text-ink-950">Research Paper Intelligence System</span>
          </div>
          <button onClick={() => { logout(); navigate('/login'); }}
            className="flex items-center gap-2 text-sm text-ink-500 hover:text-ink-800 transition-colors">
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {loading ? (
          <div className="flex items-center justify-center py-32">
            <Loader2 className="w-6 h-6 text-ink-400 animate-spin" />
          </div>
        ) : (
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Documents Section */}
            <section className="animate-slide-up">
              <div className="flex items-center justify-between mb-5">
                <h2 className="font-display text-xl font-semibold text-ink-900">Documents</h2>
                <button onClick={() => setShowUpload(true)}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-ink-950 text-paper-50 text-sm font-medium
                    hover:bg-ink-800 active:scale-[0.97] transition-all">
                  <Upload size={14} /> Upload
                </button>
              </div>

              {docs.length === 0 ? (
                <div className="bg-white rounded-xl border border-paper-300/60 p-10 text-center">
                  <FileText className="w-10 h-10 text-ink-300 mx-auto mb-3" strokeWidth={1.4} />
                  <p className="text-ink-500 text-sm">No documents yet. Upload research papers to get started.</p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {docs.map((doc) => (
                    <div key={doc.document_id}
                      className="bg-white rounded-xl border border-paper-300/60 px-5 py-4 flex items-center gap-4
                        hover:shadow-sm transition-shadow group">
                      <div className="w-10 h-10 rounded-lg bg-accent-muted flex items-center justify-center flex-shrink-0">
                        <FileText className="w-5 h-5 text-accent" strokeWidth={1.6} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-ink-900 truncate">{doc.file_name}</p>
                        <p className="text-xs text-ink-400 mt-0.5">
                          {doc.page_count} pages • Uploaded {new Date(doc.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button onClick={() => handleProcess(doc.document_id)}
                          disabled={processingIds.has(doc.document_id)}
                          className="p-2 rounded-lg text-ink-400 hover:text-accent hover:bg-accent-muted transition-all
                            disabled:opacity-40" title="Process for RAG">
                          {processingIds.has(doc.document_id) ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Cpu size={16} />
                          )}
                        </button>
                        <button onClick={() => handleDeleteDoc(doc.document_id)}
                          className="p-2 rounded-lg text-ink-400 hover:text-red-500 hover:bg-red-50 transition-all"
                          title="Delete">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Conversations Section */}
            <section className="animate-slide-up" style={{ animationDelay: '80ms' }}>
              <div className="flex items-center justify-between mb-5">
                <h2 className="font-display text-xl font-semibold text-ink-900">Conversations</h2>
                <button onClick={() => setShowNewChat(true)}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-accent text-white text-sm font-medium
                    hover:bg-accent-dark active:scale-[0.97] transition-all">
                  <MessageSquarePlus size={14} /> New Chat
                </button>
              </div>

              {convos.length === 0 ? (
                <div className="bg-white rounded-xl border border-paper-300/60 p-10 text-center">
                  <MessageSquarePlus className="w-10 h-10 text-ink-300 mx-auto mb-3" strokeWidth={1.4} />
                  <p className="text-ink-500 text-sm">No conversations yet. Start one to query your papers.</p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {convos.map((c) => (
                    <div key={c.conversation_id}
                      className="bg-white rounded-xl border border-paper-300/60 px-5 py-4 flex items-center gap-4
                        hover:shadow-sm transition-shadow cursor-pointer group"
                      onClick={() => navigate(`/chat/${c.conversation_id}`)}>
                      <div className="w-10 h-10 rounded-lg bg-ink-100 flex items-center justify-center flex-shrink-0">
                        <MessageSquarePlus className="w-5 h-5 text-ink-500" strokeWidth={1.6} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-ink-900">
                          Conversation #{c.conversation_id}
                        </p>
                        <p className="text-xs text-ink-400 mt-0.5 flex items-center gap-1">
                          <Clock size={11} />
                          {new Date(c.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteConvo(c.conversation_id); }}
                          className="p-2 rounded-lg text-ink-400 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100">
                          <Trash2 size={16} />
                        </button>
                        <ChevronRight size={16} className="text-ink-300 group-hover:text-ink-500 transition-colors" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>

      {/* Modals */}
      {showUpload && <UploadModal onClose={() => setShowUpload(false)} onDone={handleUploadDone} />}
      {showNewChat && <NewChatModal docs={docs} onClose={() => setShowNewChat(false)} onCreated={handleChatCreated} />}
    </div>
  );
}
