import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Profile as ProfileData } from '../types';
import './Profile.css';

export function Profile() {
  const [profile, setProfile] = useState<ProfileData | null>(null);

  useEffect(() => {
    api.get<ProfileData>('/profile').then(setProfile);
  }, []);

  if (!profile) return null;

  const memberSince = new Date(profile.created_at.replace(' ', 'T')).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="profile-wrap">
      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-avatar">{profile.full_name.charAt(0).toUpperCase()}</div>
          <div>
            <div className="profile-name">{profile.full_name}</div>
            <div className="profile-email">{profile.email}</div>
            <div className="profile-since">Member since {memberSince}</div>
          </div>
        </div>

        <div className="profile-stats">
          <div className="profile-stat">
            <span className="profile-stat-label">Lifetime Expenses</span>
            <span className="profile-stat-value">₹{profile.total_expenses_all_time.toFixed(0)}</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-label">Lifetime Income</span>
            <span className="profile-stat-value">₹{profile.total_income_all_time.toFixed(0)}</span>
          </div>
          <div className="profile-stat">
            <span className="profile-stat-label">Transactions</span>
            <span className="profile-stat-value">{profile.transaction_count_all_time}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
