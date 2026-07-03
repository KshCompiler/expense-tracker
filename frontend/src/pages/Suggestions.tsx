import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import type { ChatMessage } from '../types';
import './Suggestions.css';

interface DisplayMessage {
  role: 'user' | 'ai';
  content: string;
  time: string;
}

const STARTERS = [
  '📊 Where am I spending the most?',
  '📅 Compare my last two months',
  '💡 How can I save money?',
  '⚠️ Am I overspending?',
];

function formatTime(d: Date) {
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(t: string) {
  return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderMarkdown(text: string): string {
  let h = escapeHtml(text);
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
  if (h.includes('<li>')) h = h.replace(/(<li>[\s\S]*?<\/li>)/m, '<ul>$1</ul>');
  h = h.replace(/\n/g, '<br>');
  h = h.replace(/<br>(<\/?[uo]l>)/g, '$1');
  h = h.replace(/(<\/?li>)<br>/g, '$1');
  return h;
}

export function Suggestions() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [showStarters, setShowStarters] = useState(true);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const historyRef = useRef<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [welcomeTime] = useState(() => formatTime(new Date()));

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (message: string) => {
    const trimmed = message.trim();
    if (!trimmed) return;

    setShowStarters(false);
    setMessages((prev) => [...prev, { role: 'user', content: trimmed, time: formatTime(new Date()) }]);
    const priorHistory = [...historyRef.current];
    historyRef.current.push({ role: 'user', content: trimmed });
    setLoading(true);

    try {
      const data = await api.post<{ reply?: string }>('/chat', { message: trimmed, history: priorHistory });
      const reply = data.reply || 'Sorry, I could not get a response. Please try again.';
      setMessages((prev) => [...prev, { role: 'ai', content: reply, time: formatTime(new Date()) }]);
      historyRef.current.push({ role: 'assistant', content: reply });
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: 'Something went wrong. Please check your connection and try again.', time: formatTime(new Date()) },
      ]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  };

  const handleSend = () => {
    const msg = input;
    setInput('');
    send(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const charCount = input.length;

  return (
    <div className="sage-shell">
      <div className="sage-topbar">
        <div className="sage-tb-avatar">
          S
          <span className="sage-tb-online" />
        </div>
        <div className="sage-tb-info">
          <div className="sage-tb-name">
            Sage <span className="sage-tb-badge">AI Assistant</span>
          </div>
          <div className="sage-tb-sub">Your personal finance advisor · powered by Spendly</div>
        </div>
        <div className="sage-tb-pill">📊 2 months of data loaded</div>
      </div>

      <div className="sage-messages">
        <div className="sage-messages-inner">
          <div className="msg-group ai">
            <div className="msg-avatar">S</div>
            <div className="msg-body">
              <span className="msg-sender">Sage</span>
              <div className="msg-bubble">
                <span className="bubble-tag">Welcome</span>
                <br />
                Hi! I'm <strong>Sage</strong>, your AI finance assistant. I have access to your spending data for
                the last 2 months — ask me anything about your expenses, where your money is going, or how to
                save more.
              </div>
              <span className="msg-time">{welcomeTime}</span>
            </div>
          </div>

          {messages.map((msg, i) => (
            <div className={`msg-group ${msg.role}`} key={i}>
              <div className="msg-avatar">
                {msg.role === 'ai' ? 'S' : (user?.full_name.charAt(0).toUpperCase() ?? 'Y')}
              </div>
              <div className="msg-body">
                <span className="msg-sender">{msg.role === 'ai' ? 'Sage' : 'You'}</span>
                {msg.role === 'ai' ? (
                  <div className="msg-bubble" dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />
                ) : (
                  <div className="msg-bubble">{msg.content}</div>
                )}
                <span className="msg-time">{msg.time}</span>
              </div>
            </div>
          ))}

          {loading && (
            <div className="msg-group ai">
              <div className="msg-avatar">S</div>
              <div className="msg-body">
                <span className="msg-sender">Sage</span>
                <div className="typing-row">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="sage-bottom">
        <div className="sage-bottom-inner">
          {showStarters && (
            <div className="sage-starters">
              <span className="starters-label">Try asking</span>
              {STARTERS.map((chip) => (
                <button key={chip} className="sage-chip" onClick={() => send(chip.replace(/^\S+\s*/u, '').trim())}>
                  {chip}
                </button>
              ))}
            </div>
          )}

          <div className="sage-input-row">
            <div className="sage-input-box">
              <textarea
                ref={textareaRef}
                className="sage-textarea"
                placeholder="Message Sage…"
                rows={1}
                maxLength={500}
                disabled={loading}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button className="sage-send-btn" title="Send" disabled={loading} onClick={handleSend}>
                <svg viewBox="0 0 24 24">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </div>
          </div>
          <div className="sage-input-footer">
            <span className="sage-hint">Enter to send · Shift+Enter for new line</span>
            <span className={`sage-char ${charCount > 440 ? 'warn' : ''}`}>{charCount} / 500</span>
          </div>
        </div>
      </div>
    </div>
  );
}
