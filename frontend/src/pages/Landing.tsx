import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Landing() {
  const { user } = useAuth();

  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-badge">Personal Finance Tracker</div>
          <h1 className="hero-title">
            Stop guessing
            <br />
            where your <em>money goes</em>
          </h1>
          <p className="hero-subtitle">
            Log every expense in seconds, understand your spending patterns, and take control of your
            financial life — one transaction at a time.
          </p>
          {!user ? (
            <>
              <div className="hero-actions">
                <Link to="/register" className="btn-primary btn-lg">
                  Start tracking free
                </Link>
                <Link to="/login" className="btn-ghost btn-lg">
                  Sign in
                </Link>
              </div>
              <p className="hero-trust">Free forever &middot; No credit card required &middot; Set up in 30 seconds</p>
            </>
          ) : (
            <div className="hero-actions">
              <Link to="/dashboard" className="btn-primary btn-lg">
                Go to dashboard
              </Link>
              <Link to="/suggestions" className="btn-ghost btn-lg">
                Chat with Sage
              </Link>
            </div>
          )}
        </div>
        <div className="hero-visual">
          <div className="mock-card">
            <div className="mock-cover">
              <div className="mock-cover-left">
                <span className="mock-cover-seal" aria-hidden="true">
                  ◈
                </span>
                <span className="mock-label">June 2026</span>
              </div>
              <span className="mock-total">₹12,450</span>
            </div>
            <div className="mock-ledger">
              <div className="mock-mini-stats">
                <div className="mock-mini-stat">
                  <span className="mock-mini-label">Income</span>
                  <span className="mock-mini-val mock-positive">₹40,000</span>
                </div>
                <div className="mock-mini-stat">
                  <span className="mock-mini-label">Saved</span>
                  <span className="mock-mini-val mock-accent2">₹27,550</span>
                </div>
                <div className="mock-mini-stat">
                  <span className="mock-mini-label">Txns</span>
                  <span className="mock-mini-val">24</span>
                </div>
              </div>
              <div className="mock-tally-bar">
                <div className="mock-tally-seg" style={{ flex: '0 0 39%', background: '#e65100' }} />
                <div className="mock-tally-seg" style={{ flex: '0 0 28%', background: '#c17f24' }} />
                <div className="mock-tally-seg" style={{ flex: '0 0 18%', background: '#1a472a' }} />
                <div className="mock-tally-seg" style={{ flex: '0 0 15%', background: '#1565c0' }} />
              </div>
              <div className="mock-legend">
                <div className="mock-legend-row">
                  <span className="mock-legend-dot" style={{ background: '#e65100' }} />
                  <span className="mock-legend-name">Bills</span>
                  <span className="mock-legend-leader" />
                  <span className="mock-legend-amt">₹4,500</span>
                </div>
                <div className="mock-legend-row">
                  <span className="mock-legend-dot" style={{ background: '#c17f24' }} />
                  <span className="mock-legend-name">Food</span>
                  <span className="mock-legend-leader" />
                  <span className="mock-legend-amt">₹3,200</span>
                </div>
                <div className="mock-legend-row">
                  <span className="mock-legend-dot" style={{ background: '#1a472a' }} />
                  <span className="mock-legend-name">Health</span>
                  <span className="mock-legend-leader" />
                  <span className="mock-legend-amt">₹2,050</span>
                </div>
                <div className="mock-legend-row">
                  <span className="mock-legend-dot" style={{ background: '#1565c0' }} />
                  <span className="mock-legend-name">Transport</span>
                  <span className="mock-legend-leader" />
                  <span className="mock-legend-amt">₹1,800</span>
                </div>
              </div>
              <div className="mock-ai-hint">
                <span className="mock-ai-dot" />
                <span className="mock-ai-text">Sage: Food spend up 18% vs last month</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="stats-strip">
        <div className="stats-strip-inner">
          <div className="stat-pill">
            <span className="stat-pill-num">₹</span>
            <span className="stat-pill-label">Track every rupee</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-pill">
            <span className="stat-pill-num">7</span>
            <span className="stat-pill-label">expense categories</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-pill">
            <span className="stat-pill-num">✦</span>
            <span className="stat-pill-label">Sage AI assistant</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-pill">
            <span className="stat-pill-num">100%</span>
            <span className="stat-pill-label">free to use</span>
          </div>
        </div>
      </div>

      <section className="features">
        <div className="features-inner">
          <div className="features-header">
            <span className="features-eyebrow">Why Spendly</span>
            <h2 className="features-heading">Everything you need to own your finances</h2>
            <p className="features-subheading">
              No bloat, no subscriptions, no excuses — just a clean tool that helps you spend smarter.
            </p>
          </div>
          <div className="features-grid">
            <div className="feature-card feat-log">
              <div className="feature-card-top">
                <div className="feature-icon-wrap">
                  <span className="feature-icon">₹</span>
                </div>
              </div>
              <h3 className="feature-title">Log expenses instantly</h3>
              <p className="feature-body">
                Add any expense in seconds — category, amount, date. No bloat, no friction, no forgetting.
              </p>
            </div>
            <div className="feature-card feat-patterns">
              <div className="feature-card-top">
                <div className="feature-icon-wrap">
                  <span className="feature-icon">◎</span>
                </div>
              </div>
              <h3 className="feature-title">See spending patterns</h3>
              <p className="feature-body">
                Category breakdowns reveal exactly where your money goes each month — so you can fix it.
              </p>
            </div>
            <div className="feature-card feat-sage">
              <div className="feature-card-top">
                <div className="feature-icon-wrap">
                  <span className="feature-icon">✦</span>
                </div>
              </div>
              <h3 className="feature-title">Meet Sage, your AI advisor</h3>
              <p className="feature-body">
                Chat with Sage to get personalised insights based on your actual numbers — not generic tips
                from the internet.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="how-it-works">
        <div className="how-inner">
          <div className="features-header">
            <span className="features-eyebrow">How it works</span>
            <h2 className="features-heading">Up and running in three steps</h2>
          </div>
          <div className="steps-grid">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3 className="step-title">Create your account</h3>
                <p className="step-body">Sign up in under 30 seconds. No credit card, no trial — free from day one.</p>
              </div>
            </div>
            <div className="step-connector" />
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3 className="step-title">Log income &amp; expenses</h3>
                <p className="step-body">Add transactions as you go. Pick a category, enter the amount, and you're done.</p>
              </div>
            </div>
            <div className="step-connector" />
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3 className="step-title">Chat with Sage</h3>
                <p className="step-body">
                  Ask Sage anything — it analyses two months of your data and gives you concrete, actionable
                  answers.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="ai-showcase">
        <div className="ai-showcase-inner">
          <div className="ai-showcase-header">
            <span className="ai-showcase-eyebrow">Meet Sage</span>
            <h2 className="ai-showcase-heading">Your AI finance assistant, always ready</h2>
            <p className="ai-showcase-subtitle">
              Sage analyses your spending patterns across two months and answers your questions in plain
              language — not generic advice, but insights tied to your actual numbers.
            </p>
          </div>
          <div className="ai-sample-grid">
            <div className="ai-sample-card">
              <div className="ai-sample-icon">✦</div>
              <h3 className="ai-sample-heading">"Where am I overspending?"</h3>
              <p className="ai-sample-body">
                Food is 26% of your total this month — up from 19% last month. Try meal prepping twice a
                week; most users cut dining costs by 20–30% within the first month.
              </p>
            </div>
            <div className="ai-sample-card">
              <div className="ai-sample-icon">✦</div>
              <h3 className="ai-sample-heading">"Compare my last two months"</h3>
              <p className="ai-sample-body">
                You spent ₹3,200 less in May than June. The biggest jump was Bills — up ₹900. Your savings
                rate dropped from 32% to 24% as a result.
              </p>
            </div>
            <div className="ai-sample-card">
              <div className="ai-sample-icon">✦</div>
              <h3 className="ai-sample-heading">"How can I save more?"</h3>
              <p className="ai-sample-body">
                Switching to a monthly metro pass and cutting one dining-out meal a week could free up
                ₹1,200/month — that's ₹14,400 extra saved by year end.
              </p>
            </div>
          </div>
          <div className="ai-showcase-cta">
            {user ? (
              <Link to="/suggestions" className="btn-primary btn-lg">
                Chat with Sage
              </Link>
            ) : (
              <Link to="/register" className="btn-primary btn-lg">
                Try it free
              </Link>
            )}
            <p className="ai-showcase-cta-note">Answers based on your actual spending — not generic filler</p>
          </div>
        </div>
      </section>

      {!user && (
        <section className="cta-section">
          <div className="cta-inner">
            <h2 className="cta-title">Your finances deserve clarity</h2>
            <p className="cta-body">Start logging today — it takes less than 30 seconds to set up.</p>
            <Link to="/register" className="btn-primary btn-lg">
              Create free account
            </Link>
            <p className="cta-note">No credit card &middot; Always free &middot; Cancel anytime</p>
          </div>
        </section>
      )}
    </>
  );
}
