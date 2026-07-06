import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

export function Navbar() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [panelOpen, setPanelOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!panelOpen) return;

    function onClickOutside(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setPanelOpen(false);
      }
    }
    function onEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setPanelOpen(false);
    }

    document.addEventListener('mousedown', onClickOutside);
    document.addEventListener('keydown', onEscape);
    return () => {
      document.removeEventListener('mousedown', onClickOutside);
      document.removeEventListener('keydown', onEscape);
    };
  }, [panelOpen]);

  const handleLogout = async () => {
    setPanelOpen(false);
    await logout();
    showToast('You have been logged out successfully.', 'info');
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="nav-inner">
        <Link to="/" className="nav-brand">
          <span className="brand-icon">◆</span>
          <span className="brand-name">Spendly</span>
        </Link>

        {user ? (
          <div className="nav-links">
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/budgets">Budgets</Link>
            <div className="nav-avatar-wrap" ref={wrapRef}>
              <button
                type="button"
                className="nav-avatar"
                onClick={() => setPanelOpen((open) => !open)}
                aria-haspopup="true"
                aria-expanded={panelOpen}
              >
                {user.full_name.charAt(0).toUpperCase()}
              </button>
              <div className="nav-profile-panel" hidden={!panelOpen}>
                <Link to="/profile" onClick={() => setPanelOpen(false)} style={{ textDecoration: 'none' }}>
                  <div className="npp-avatar">{user.full_name.charAt(0).toUpperCase()}</div>
                  <div className="npp-name">{user.full_name}</div>
                  <div className="npp-email">{user.email}</div>
                </Link>
                <Link to="/suggestions" className="npp-suggestions" onClick={() => setPanelOpen(false)}>
                  Chat with Sage
                </Link>
                <button type="button" className="npp-signout" onClick={handleLogout}>
                  Sign out
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="nav-links">
            <Link to="/login">Sign in</Link>
            <Link to="/register" className="nav-cta">
              Get started
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
