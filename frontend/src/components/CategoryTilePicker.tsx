import type { TileOption } from './categoryTiles';

interface CategoryTilePickerProps {
  options: TileOption[];
  value: string;
  onChange: (value: string) => void;
  income?: boolean;
}

export function CategoryTilePicker({ options, value, onChange, income }: CategoryTilePickerProps) {
  return (
    <div className={`cat-grid ${income ? 'income-cat-grid' : ''}`}>
      {options.map((option) => (
        <div
          key={option.value}
          className={`cat-item ${income ? 'income-cat-item' : ''} ${value === option.value ? 'selected' : ''}`}
          data-value={option.value}
          style={{ '--tile-color': option.color, '--tile-tint': option.tint } as React.CSSProperties}
          onClick={() => onChange(option.value)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onChange(option.value);
            }
          }}
        >
          <span className="cat-icon">{option.icon}</span>
          <span className="cat-label">{option.label}</span>
        </div>
      ))}
    </div>
  );
}
