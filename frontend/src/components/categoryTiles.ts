export interface TileOption {
  value: string;
  label: string;
  icon: string;
  color: string;
  tint: string;
}

export const EXPENSE_CATEGORY_TILES: TileOption[] = [
  { value: 'Food', label: 'Food', icon: '🍔', color: '#c17f24', tint: '#fdf3e3' },
  { value: 'Transport', label: 'Transport', icon: '🚌', color: '#1565c0', tint: '#e3f2fd' },
  { value: 'Bills', label: 'Bills', icon: '💡', color: '#e65100', tint: '#fff8e1' },
  { value: 'Health', label: 'Health', icon: '💊', color: '#1a472a', tint: '#e8f0eb' },
  { value: 'Entertainment', label: 'Entertainment', icon: '🎬', color: '#c2185b', tint: '#fce4ec' },
  { value: 'Shopping', label: 'Shopping', icon: '🛍️', color: '#7b1fa2', tint: '#f3e5f5' },
  { value: 'Other', label: 'Other', icon: '📦', color: '#6b6b6b', tint: '#f0ede6' },
];

export const INCOME_SOURCE_TILES: TileOption[] = [
  { value: 'Salary', label: 'Salary', icon: '💼', color: '#1a472a', tint: '#e8f0eb' },
  { value: 'Freelance', label: 'Freelance', icon: '💻', color: '#5b7fa6', tint: '#e8eef5' },
  { value: 'Business', label: 'Business', icon: '🏪', color: '#c17f24', tint: '#fdf3e3' },
  { value: 'Investment', label: 'Investment', icon: '📈', color: '#2a7a6f', tint: '#e3f2ef' },
  { value: 'Gift', label: 'Gift', icon: '🎁', color: '#c2185b', tint: '#fce4ec' },
  { value: 'Other', label: 'Other', icon: '✦', color: '#6b6b6b', tint: '#f0ede6' },
];
