# Spec: AI Finance Chat Assistant

## Overview
Replace the original card-based "Smart Suggestions" page with a conversational chat interface. Users can ask free-form questions about their spending (e.g. "Where am I spending the most?", "How can I save money?") and get concise, data-grounded responses. The AI receives the user's last two months of real financial data as a system prompt on every message, and the client maintains conversation history so follow-up questions work naturally. This replaces the one-shot suggestion dump with an interactive experience that users actually engage with.

## Depends on
- Step 01 (users table and session management)
- Step 02 (login — user must be authenticated)
- Step 03 (expenses table and `add_expense` — spending data must exist)
- Step 06 (add income — income data required for budget-vs-spend analysis)

## Routes
- `GET /suggestions` — render the Finance Chat page (no AI call on page load) — logged-in only
- `POST /api/chat` — accepts `{message: str, history: [{role, content}]}`, fetches the user's financial data, calls the Groq/LLM API with full conversation context, returns `{reply: str}` — logged-in only

## Database changes
No database changes. Reads from existing `expenses` and `income` tables via `get_monthly_expense_summary` and `get_monthly_income_total` helpers.

## Templates
- **Rewrite:** `templates/suggestions.html`
  - Extends `base.html`
  - Full-height chat layout: scrollable message list + sticky input form at bottom
  - Initial AI greeting message rendered on page load (no API call)
  - Four starter question chips ("Where am I spending the most?", "Compare my last two months", "How can I save money?", "Am I overspending?") — hidden after the first message is sent
  - User messages aligned right (accent background), AI messages aligned left (card background)
  - Animated typing indicator (three bouncing dots) shown while waiting for API response
  - Input disabled during in-flight requests to prevent double-sends
  - Conversation history kept client-side in a JS array and sent with each request
  - HTML-escapes all AI output before rendering (no `innerHTML` with raw API text)

## Files changed
- `app.py`
  - Added `_fmt_expenses(rows)` helper
  - Added `_build_chat_system_prompt(...)` — injects 2-month financial summary as system context; instructs AI to respond in 2–4 sentences, reference real numbers, use ₹
  - Added `POST /api/chat` route — validates session, fetches fresh financial data, builds messages array (system + capped history + new user turn), calls LLM, returns `{reply}`
  - Simplified `GET /suggestions` to just render the template (AI no longer called on page load)
  - Removed `_build_suggestions_prompt`, `_parse_suggestions`, and `GET /api/suggestions`
- `templates/suggestions.html` — full rewrite as chat UI (see Templates above)
- `static/css/style.css` — old `.suggestions-card` / `.suggestions-grid` styles remain but are unused; new chat styles live inline in the template

## AI integration
- Provider: Groq (OpenAI-compatible SDK), key from `GROQ_API_KEY` env var
- Model: `llama-3.1-8b-instant`
- System prompt built fresh on every `/api/chat` request with current financial data
- Up to 10 previous turns sent as history to support follow-up questions
- On exception: return `{"error": "Failed to get a response"}` with HTTP 500 — client shows a friendly fallback message

## Rules for implementation
- No SQLAlchemy or ORMs; parameterised queries only
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for all links — no hardcoded URLs
- No JS frameworks — vanilla JS only
- API key read from `GROQ_API_KEY` environment variable; never hardcoded
- Escape all AI output with `escapeHtml()` before inserting into DOM

## Definition of done
- [x] Navigating to `/suggestions` while logged out redirects to `/login`
- [x] Navigating to `/suggestions` while logged in shows the chat page instantly (no AI call on page load)
- [x] Sending a message calls `/api/chat` and renders the AI reply as a chat bubble
- [x] Starter chips send a pre-filled question and hide themselves after first use
- [x] Typing indicator appears while the API call is in flight
- [x] Conversation history is maintained — follow-up questions have context
- [x] AI responses reference the user's actual spending numbers (not generic filler)
- [x] If `GROQ_API_KEY` is missing or the API errors, a friendly fallback message appears in the chat
- [x] No hardcoded hex colours — all colours use CSS variables
- [x] All links use `url_for()` — no hardcoded URLs
