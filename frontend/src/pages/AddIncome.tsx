import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import { CategoryTilePicker } from '../components/CategoryTilePicker';
import { BillUploadDropzone } from '../components/BillUploadDropzone';
import { INCOME_SOURCE_TILES } from '../components/categoryTiles';
import type { BillExtraction } from '../types';

export function AddIncome() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [amount, setAmount] = useState('');
  const [source, setSource] = useState('');
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleExtracted = (data: BillExtraction) => {
    if (data.amount != null) setAmount(String(data.amount));
    if (data.source) setSource(data.source);
    if (data.date) setDate(data.date);
    if (data.description) setDescription(data.description);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!source) {
      showToast('Please select an income source.', 'error');
      return;
    }
    if (!date) {
      showToast('Please select a date.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/income', { amount, source, date, description: description || null });
      showToast('Income added successfully!', 'success');
      navigate('/dashboard');
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'An error occurred while adding income. Please try again.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="exp-section">
      <div className="exp-container">
        <div className="entry-page-header">
          <div className="income-badge">
            <svg className="income-badge-arrow" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M6 10V2M6 2L2.5 5.5M6 2L9.5 5.5"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Income Entry
          </div>
          <h1 className="auth-title">Record Income</h1>
          <p className="auth-subtitle">Add an income entry to keep your finances accurate.</p>
        </div>

        <div className="auth-card income-card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <BillUploadDropzone
                endpoint="/income/extract-bill"
                fieldKey="source"
                idleText="Drop a payslip or income proof here, or click to choose one"
                scanningText="Reading your document…"
                emptyMessage="Nothing could be read from that image — make sure it's a clear payslip or income proof, or enter the details manually."
                successMessage="Filled in from your upload — check it over before saving."
                onExtracted={handleExtracted}
              />
            </div>

            <div className="form-group">
              <label htmlFor="amount">Amount</label>
              <div className="amount-slip">
                <span className="amount-slip-currency">₹</span>
                <input
                  type="number"
                  id="amount"
                  className="amount-slip-input"
                  placeholder="0.00"
                  step="0.01"
                  min="0.01"
                  required
                  autoFocus
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Source</label>
              <CategoryTilePicker options={INCOME_SOURCE_TILES} value={source} onChange={setSource} income />
            </div>

            <div className="form-group">
              <label htmlFor="date">Date</label>
              <input
                type="date"
                id="date"
                className="form-input"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">
                Note <span style={{ color: 'var(--ink-faint)', fontWeight: 400 }}>(optional)</span>
              </label>
              <textarea
                id="description"
                className="form-input"
                placeholder="e.g. Monthly salary, project payment…"
                rows={2}
                style={{ resize: 'vertical' }}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-submit income-submit" disabled={submitting}>
                <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z" />
                </svg>
                Save Income
              </button>
              <Link to="/dashboard" className="btn-cancel">
                Cancel
              </Link>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
