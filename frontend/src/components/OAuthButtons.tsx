import type { ReactNode } from 'react';
import { getOAuthUrl } from '../api/client';

type ProviderId = 'google' | 'linkedin';

interface ProviderDef {
  id: ProviderId;
  label: string;
  rowClass: string;
  seal: ReactNode;
}

const PROVIDERS: ProviderDef[] = [
  {
    id: 'google',
    label: 'Continue with Google',
    rowClass: 'oauth-row--google',
    seal: (
      <svg viewBox="0 0 18 18" aria-hidden="true">
        <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" />
        <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" />
        <path fill="#FBBC05" d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957C.348 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.332z" />
        <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" />
      </svg>
    ),
  },
  {
    id: 'linkedin',
    label: 'Continue with LinkedIn',
    rowClass: 'oauth-row--linkedin',
    seal: (
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.11 1 2.5 1s2.48 1.12 2.48 2.5zM.22 8.98H4.8V24H.22V8.98zM8.98 8.98h4.38v2.05h.06c.61-1.16 2.1-2.38 4.32-2.38 4.62 0 5.47 3.04 5.47 7v9.35h-4.56v-8.29c0-1.98-.04-4.52-2.75-4.52-2.76 0-3.18 2.15-3.18 4.38v8.43H8.98V8.98z" />
      </svg>
    ),
  },
];

export function OAuthButtons() {
  return (
    <div className="oauth-buttons">
      <div className="auth-divider">
        <span>Or continue with</span>
      </div>
      {PROVIDERS.map((provider) => (
        <a key={provider.id} href={getOAuthUrl(provider.id)} className={`oauth-row ${provider.rowClass}`}>
          <span className="oauth-seal">{provider.seal}</span>
          <span className="oauth-row-label">{provider.label}</span>
          <svg
            className="oauth-row-arrow"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </a>
      ))}
    </div>
  );
}
