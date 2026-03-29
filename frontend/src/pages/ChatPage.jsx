import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { conversations as convApi } from '../lib/api';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import {
  BookOpen, ArrowLeft, Send, Loader2, FileText, User, Bot, BookMarked, ChevronDown
} from 'lucide-react';
import CitationPanel from '../components/CitationPanel';

export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [convoDocs, setConvoDocs] = useState([]);
  const [showDocs, setShowDocs] = useState(false);
  const [activeCitations, setActiveCitations] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    async function load() {
      try {
        const [msgs, docsResp] = await Promise.all([
          convApi.getMessages(conversationId),
          convApi.getDocuments(conversationId).catch(() => ({ documents_to_update: [] })),
        ]);
        setMessages(msgs || []);
        setConvoDocs(docsResp?.documents_to_update || []);
      } catch (err) {
        toast.error('Failed to load conversation');
      }
    }
    load();
  }, [conversationId]);

  useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

  async function handleSend(e) {
    e.preventDefault();
    const content = input.trim();
    if (!content || sending) return;

    setInput('');
    setSending(true);

    // Optimistic user message
    const tempUserMsg = {
      message_id: `temp-${Date.now()}`,
      conversation_id: parseInt(conversationId),
      content,
      role: 'user',
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await convApi.sendMessage(conversationId, content);

      // Replace optimistic message and add assistant response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.message_id !== tempUserMsg.message_id);
        return [
          ...filtered,
          {
            message_id: response.message_id - 1, // user message id (approx)
            conversation_id: parseInt(conversationId),
            content,
            role: 'user',
            created_at: tempUserMsg.created_at,
          },
          {
            message_id: response.message_id,
            conversation_id: parseInt(conversationId),
            content: response.response_content,
            role: 'assistant',
            created_at: response.created_at,
            citations: response.sources_list,
          },
        ];
      });
    } catch (err) {
      toast.error(err.message || 'Failed to send message');
      setMessages((prev) => prev.filter((m) => m.message_id !== tempUserMsg.message_id));
      setInput(content);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="h-screen flex flex-col bg-paper-100">
      {/* Header */}
      <header className="flex-shrink-0 bg-white/80 backdrop-blur-lg border-b border-paper-300/60 z-20">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')}
              className="p-1.5 rounded-lg hover:bg-paper-200 transition-colors text-ink-500 hover:text-ink-800">
              <ArrowLeft size={18} />
            </button>
            <div className="w-8 h-8 rounded-lg bg-ink-950 flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-paper-50" strokeWidth={1.8} />
            </div>
            <span className="font-display text-base font-semibold text-ink-900">
              Chat #{conversationId}
            </span>
          </div>

          {/* Docs badge */}
          <button onClick={() => setShowDocs(!showDocs)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-ink-600
              hover:bg-paper-200 transition-colors border border-paper-300">
            <FileText size={13} />
            {convoDocs.length} doc{convoDocs.length !== 1 ? 's' : ''}
            <ChevronDown size={12} className={`transition-transform ${showDocs ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Docs dropdown */}
        {showDocs && convoDocs.length > 0 && (
          <div className="max-w-4xl mx-auto px-4 pb-3 animate-slide-up">
            <div className="flex flex-wrap gap-2">
              {convoDocs.map((docId) => (
                <span key={docId}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-accent-muted text-accent text-xs font-medium">
                  <FileText size={11} /> Doc #{docId}
                </span>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-1">
          {messages.length === 0 && !sending && (
            <div className="flex flex-col items-center justify-center py-24 animate-fade-in">
              <div className="w-16 h-16 rounded-2xl bg-ink-100 flex items-center justify-center mb-4">
                <BookMarked className="w-8 h-8 text-ink-300" strokeWidth={1.4} />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-700 mb-1">Ready to explore</h3>
              <p className="text-sm text-ink-400 text-center max-w-sm">
                Ask questions about your research papers. The AI will respond with citations from the documents.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble
              key={msg.message_id}
              message={msg}
              onShowCitations={msg.citations ? () => setActiveCitations(msg.citations) : undefined}
            />
          ))}

          {sending && (
            <div className="flex items-start gap-3 py-4 animate-fade-in">
              <div className="w-8 h-8 rounded-lg bg-accent-muted flex items-center justify-center flex-shrink-0">
                <Bot size={16} className="text-accent" />
              </div>
              <div className="flex items-center gap-1.5 pt-2">
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse-dot" />
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse-dot" style={{ animationDelay: '0.2s' }} />
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse-dot" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-paper-300/60 bg-white/80 backdrop-blur-lg">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-end gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e);
                  }
                }}
                placeholder="Ask about your research papers..."
                rows={1}
                className="w-full px-4 py-3 rounded-xl border border-paper-300 bg-paper-50 text-sm text-ink-900
                  placeholder:text-ink-400 resize-none focus:outline-none focus:ring-2 focus:ring-accent/20
                  focus:border-accent transition-all"
                style={{ minHeight: '44px', maxHeight: '120px' }}
              />
            </div>
            <button type="submit" disabled={!input.trim() || sending}
              className="w-11 h-11 rounded-xl bg-ink-950 text-paper-50 flex items-center justify-center
                hover:bg-ink-800 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed
                flex-shrink-0">
              {sending ? (
                <Loader2 size={17} className="animate-spin" />
              ) : (
                <Send size={17} />
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Citation Panel */}
      {activeCitations && (
        <CitationPanel citations={activeCitations} onClose={() => setActiveCitations(null)} />
      )}
    </div>
  );
}


function MessageBubble({ message, onShowCitations }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start gap-3 py-3 animate-slide-up ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
        ${isUser ? 'bg-ink-900' : 'bg-accent-muted'}`}>
        {isUser
          ? <User size={15} className="text-paper-50" />
          : <Bot size={16} className="text-accent" />
        }
      </div>

      <div className={`max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block px-4 py-3 rounded-2xl text-sm leading-relaxed
          ${isUser
            ? 'bg-ink-900 text-paper-50 rounded-tr-md'
            : 'bg-white border border-paper-300/60 text-ink-800 rounded-tl-md shadow-sm'
          }`}>
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="markdown-body">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Citation button */}
        {onShowCitations && message.citations && message.citations.length > 0 && (
          <button onClick={onShowCitations}
            className="mt-1.5 inline-flex items-center gap-1 text-xs text-accent hover:text-accent-dark
              transition-colors font-medium">
            <BookMarked size={12} />
            {message.citations.length} source{message.citations.length !== 1 ? 's' : ''}
          </button>
        )}
      </div>
    </div>
  );
}
