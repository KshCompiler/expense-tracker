import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import type { ChatMessage, DashboardData } from '../types';
import './Suggestions.css';

interface DisplayMessage {
  role: 'user' | 'ai';
  content: string;
  time: string;
}

interface StarterCandidate {
  text: string;
  isEligible: (data: DashboardData) => boolean;
}

const STARTER_COUNT = 4;

// Pool for users with zero expenses
const ONBOARDING_STARTERS = [
  '🤔 What can you help me with?',
  '➕ How do I log my first expense?',
  '📊 What kind of insights will I get once I have more data?',
  '🧾 Can you scan a bill for me instead of typing it in?',
  '🗂️ What expense categories does Spendly support?',
];

// Pool for users with a few expenses (below FEW_EXPENSES_LIMIT)
const FEW_EXPENSES_STARTERS = [
  '📋 What do my expenses look like so far?',
  '💡 What should I be tracking to get useful insights?',
  '🏷️ Am I using the right expense categories?',
  '📅 How should I set a monthly budget?',
  '💰 How can I start saving more each month?',
  '🤔 What financial habits should I build early on?',
  '📊 When will I start seeing spending patterns?',
  '➕ What types of expenses are most important to log?',
];

function shuffle<T>(arr: T[]): T[] {
  const result = [...arr];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

const STARTER_POOL: StarterCandidate[] = [
  { text: '📅 How does this month compare to last month?', isEligible: (d) => d.monthly_trend.filter((p) => p.total > 0).length >= 2 },
  { text: '🔍 Why did my spending change this month?', isEligible: (d) => d.monthly_trend.filter((p) => p.total > 0).length >= 2 },
  { text: '📈 Where did my spending go up the most?', isEligible: (d) => d.monthly_trend.filter((p) => p.total > 0).length >= 2 },
  { text: '⚠️ Am I spending more than I earn?', isEligible: (d) => d.total_income > 0 && d.total_expenses > 0 },
  { text: '🏷️ Where should I cut back?', isEligible: (d) => d.categories.length > 0 },
  { text: '😅 Should I be worried about my spending this month?', isEligible: (d) => d.total_income > 0 && d.total_expenses > 0 },
  { text: '💰 Am I saving anything this month?', isEligible: (d) => d.total_income > 0 && d.total_expenses > 0 },
  { text: '📉 Is my spending trending up or down?', isEligible: (d) => d.monthly_trend.filter((p) => p.total > 0).length >= 2 },
  { text: '📆 Is my spending pretty consistent, or does it swing a lot?', isEligible: (d) => d.monthly_trend.filter((p) => p.total > 0).length >= 2 },
  { text: '🕵️ Is there anything surprising in my spending this month?', isEligible: (d) => d.monthly_trend.filter((p) => p.total > 0).length >= 2 },
];

function pickRandomStarters(data: DashboardData): string[] {
  if (!data.has_transactions) {
    return shuffle(ONBOARDING_STARTERS).slice(0, STARTER_COUNT);
  }
  if (data.recent_transactions.length < FEW_EXPENSES_LIMIT) {
    return shuffle(FEW_EXPENSES_STARTERS).slice(0, STARTER_COUNT);
  }
  const eligible = STARTER_POOL.filter((c) => c.isEligible(data)).map((c) => c.text);
  return shuffle(eligible).slice(0, STARTER_COUNT);
}

function chatStorageKey(userId: number) {
  return `sage-chat-${userId}`;
}

function loadPersistedChat(userId: number | undefined): { messages: DisplayMessage[]; history: ChatMessage[] } {
  if (!userId) return { messages: [], history: [] };
  try {
    const raw = sessionStorage.getItem(chatStorageKey(userId));
    if (!raw) return { messages: [], history: [] };
    const parsed = JSON.parse(raw);
    return { messages: parsed.messages ?? [], history: parsed.history ?? [] };
  } catch {
    return { messages: [], history: [] };
  }
}

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

// recent_transactions is capped at 5 server-side, so a length below that
// unambiguously means the user has fewer than 5 expenses recorded, ever.
const FEW_EXPENSES_LIMIT = 5;

function getWelcome(data: DashboardData | null): { tag: string; body: React.ReactNode } {
  if (data && !data.has_transactions) {
    return {
      tag: 'Getting started',
      body: (
        <>
          Hi! I'm <strong>Sage</strong>, your AI finance assistant. You haven't logged any expenses yet —
          add a few from the <strong>Add Expense</strong> page and I'll help you spot spending patterns,
          compare months, and find ways to save.
        </>
      ),
    };
  }
  if (data && data.recent_transactions.length < FEW_EXPENSES_LIMIT) {
    return {
      tag: 'Just getting started',
      body: (
        <>
          Hi! I'm <strong>Sage</strong>, your AI finance assistant. You've started tracking your spending —
          nice! Keep adding expenses and I'll be able to give you richer insights, like month-over-month
          comparisons and category breakdowns.
        </>
      ),
    };
  }
  return {
    tag: 'Welcome',
    body: (
      <>
        Hi! I'm <strong>Sage</strong>, your AI finance assistant. I have access to your spending data —
        ask me anything about your expenses, where your money is going, or how to save more.
      </>
    ),
  };
}

export function Suggestions() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<DisplayMessage[]>(() => loadPersistedChat(user?.id).messages);
  const [showStarters, setShowStarters] = useState(() => loadPersistedChat(user?.id).messages.length === 0);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const historyRef = useRef<ChatMessage[]>(loadPersistedChat(user?.id).history);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [welcomeTime] = useState(() => formatTime(new Date()));
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [starters, setStarters] = useState<string[]>([]);

  const monthsWithData = dashboardData ? dashboardData.monthly_trend.filter((p) => p.total > 0).length : null;
  const welcome = getWelcome(dashboardData);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (!user) return;
    sessionStorage.setItem(chatStorageKey(user.id), JSON.stringify({ messages, history: historyRef.current }));
  }, [messages, user]);

  useEffect(() => {
    api
      .get<DashboardData>('/dashboard')
      .then((data) => {
        setDashboardData(data);
        setStarters(pickRandomStarters(data));
      })
      .catch(() => setDashboardData(null));
  }, []);

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
        <div className="sage-tb-pill">
          📊{' '}
          {monthsWithData === null
            ? 'Loading data…'
            : monthsWithData === 0
              ? 'No spending data yet'
              : `${monthsWithData} month${monthsWithData === 1 ? '' : 's'} of data loaded`}
        </div>
      </div>

      <div className="sage-messages">
        <div className="sage-messages-inner">
          <div className="msg-group ai">
            <div className="msg-avatar">S</div>
            <div className="msg-body">
              <span className="msg-sender">Sage</span>
              <div className="msg-bubble">
                <span className="bubble-tag">{welcome.tag}</span>
                <br />
                {welcome.body}
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
              {starters.map((chip) => (
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
