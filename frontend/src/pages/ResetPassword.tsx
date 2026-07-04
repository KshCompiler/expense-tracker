import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useToast } from '../context/ToastContext';
import { ApiError, api } from '../api/client';
import type { MessageResponse } from '../types';
import { PasswordStrengthMeter } from '../components/PasswordStrengthMeter';
import { PasswordVisibilityToggle } from '../components/PasswordVisibilityToggle';
import { generateStrongPassword } from '../utils/generatePassword';

// Must stay byte-for-byte identical to RESET_TOKEN_INVALID_MESSAGE in
// backend/app/routers/auth.py - that's what this compares against below to
// decide whether to show the "VOID" stamp state instead of a generic error.
const RESET_TOKEN_INVALID_MESSAGE = 'This reset link is invalid or has expired.';

function VoidState() {
  return (
    <div className="void-state">
      <div className="void-watermark">
        <span>Void</span>
      </div>
      <p className="void-message">{RESET_TOKEN_INVALID_MESSAGE}</p>
      <Link to="/forgot-password" className="btn-submit">
        Request a new link
      </Link>
    </div>
  );
}

export function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [tokenRejected, setTokenRejected] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.post<MessageResponse>('/auth/reset-password', {
        token,
        password,
        confirm_password: confirmPassword,
      });
      showToast(res.message, 'success');
      navigate('/login');
    } catch (err) {
      if (err instanceof ApiError && err.message === RESET_TOKEN_INVALID_MESSAGE) {
        setTokenRejected(true);
      } else {
        setError(err instanceof ApiError ? err.message : 'An error occurred. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-section">
      <div className="auth-container">
        <div className="auth-header">
          <h1 className="auth-title">Set a new password</h1>
          <p className="auth-subtitle">Choose a strong password for your account</p>
        </div>

        <div className="auth-card">
          {!token || tokenRejected ? (
            <VoidState />
          ) : (
            <>
              {error && <div className="auth-error">{error}</div>}

              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="password">New password</label>
                  <div className="pw-input-wrap">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="password"
                      className="form-input"
                      placeholder="Min. 8 characters"
                      required
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        setError(null);
                      }}
                      onFocus={() => setPasswordTouched(true)}
                    />
                    <PasswordVisibilityToggle visible={showPassword} onToggle={() => setShowPassword((v) => !v)} />
                  </div>
                  {passwordTouched && (
                    <>
                      <PasswordStrengthMeter password={password} />
                      <button
                        type="button"
                        className="pw-suggest-btn"
                        onClick={() => {
                          const generated = generateStrongPassword();
                          setPassword(generated);
                          setConfirmPassword(generated);
                          setError(null);
                          setShowPassword(true);
                          setShowConfirmPassword(true);
                        }}
                      >
                        <svg className="pw-suggest-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8" />
                        </svg>
                        Suggest a strong password
                      </button>
                    </>
                  )}
                </div>
                <div className="form-group">
                  <label htmlFor="confirm_password">Confirm new password</label>
                  <div className="pw-input-wrap">
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      id="confirm_password"
                      className="form-input"
                      placeholder="Confirm your new password"
                      required
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                        setError(null);
                      }}
                    />
                    <PasswordVisibilityToggle
                      visible={showConfirmPassword}
                      onToggle={() => setShowConfirmPassword((v) => !v)}
                    />
                  </div>
                </div>
                <button type="submit" className="btn-submit" disabled={submitting}>
                  Reset password
                </button>
              </form>
            </>
          )}
        </div>

        <p className="auth-switch">
          <Link to="/login">← Back to sign in</Link>
        </p>
      </div>
    </section>
  );
}
