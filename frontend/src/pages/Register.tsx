import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { ApiError } from '../api/client';
import { PasswordStrengthMeter } from '../components/PasswordStrengthMeter';
import { PasswordVisibilityToggle } from '../components/PasswordVisibilityToggle';
import { generateStrongPassword } from '../utils/generatePassword';
import { OAuthButtons } from '../components/OAuthButtons';

export function Register() {
  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(fullName, email, password, confirmPassword);
      navigate('/');
      showToast('Account created successfully', 'success');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'An error occurred. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="auth-section">
      <div className="auth-container">
        <div className="auth-header">
          <h1 className="auth-title">Create your account</h1>
          <p className="auth-subtitle">Start tracking your expenses today</p>
        </div>

        <div className="auth-card">
          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="full_name">Full name</label>
              <input
                type="text"
                id="full_name"
                className="form-input"
                placeholder="kshitize singh"
                required
                autoFocus
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                  setError(null);
                }}
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input
                type="email"
                id="email"
                className="form-input"
                placeholder="kshitizesingh@example.com"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError(null);
                }}
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
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
              <label htmlFor="confirm_password">Confirm Password</label>
              <div className="pw-input-wrap">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirm_password"
                  className="form-input"
                  placeholder="Confirm your password"
                  required
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    setError(null);
                  }}
                />
                <PasswordVisibilityToggle visible={showConfirmPassword} onToggle={() => setShowConfirmPassword((v) => !v)} />
              </div>
            </div>
            <button type="submit" className="btn-submit" disabled={submitting}>
              Create account
            </button>
          </form>
          <OAuthButtons />
        </div>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </section>
  );
}
