import { PASSWORD_SPECIAL_CHARS } from '../utils/generatePassword';

// Escape every character (not just regex metacharacters) before building the
// character class. Escaping only ".*+?^${}()|[]\\" left the hyphen in
// PASSWORD_SPECIAL_CHARS bare, and inside a char class an unescaped "-"
// between two other chars is a range, not a literal - "...+-=..." was being
// read as the range "+" through "=" (0x2B-0x3D), which happens to include
// every digit (0x30-0x39). That silently made any digit count as a "special
// character" here, even though the backend's Python re.escape()-based regex
// never had this bug.
const specialCharRegex = new RegExp(`[${PASSWORD_SPECIAL_CHARS.replace(/./g, '\\$&')}]`);

export const passwordRules: { key: string; label: string; test: (pw: string) => boolean }[] = [
  { key: 'length', label: 'At least 8 characters', test: (pw) => pw.length >= 8 },
  { key: 'uppercase', label: 'One uppercase letter', test: (pw) => /[A-Z]/.test(pw) },
  { key: 'digit', label: 'One number', test: (pw) => /\d/.test(pw) },
  { key: 'special', label: 'One special character (!@#$...)', test: (pw) => specialCharRegex.test(pw) },
];

export function getPasswordStrength(password: string): 'weak' | 'medium' | 'strong' {
  const [lengthRule, ...classRules] = passwordRules;
  if (!lengthRule.test(password)) return 'weak';
  const classesPassed = classRules.filter((rule) => rule.test(password)).length;
  if (classesPassed <= 1) return 'weak';
  if (classesPassed === 2) return 'medium';
  return 'strong';
}

const STRENGTH_LABEL: Record<string, string> = {
  weak: 'Weak',
  medium: 'Medium',
  strong: 'Strong',
};

interface PasswordStrengthMeterProps {
  password: string;
}

export function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps) {
  const strength = getPasswordStrength(password);
  const passedCount = passwordRules.filter((rule) => rule.test(password)).length;
  const fillPercent = password.length === 0 ? 0 : Math.max((passedCount / passwordRules.length) * 100, 15);

  return (
    <div className="pw-meter">
      <div className={`pw-meter-bar pw-meter-bar--${strength}`}>
        <div className="pw-meter-bar-fill" style={{ '--pw-fill': `${fillPercent}%` } as React.CSSProperties} />
      </div>
      <span className={`pw-meter-label pw-meter-label--${strength}`}>{STRENGTH_LABEL[strength]}</span>
      <ul className="pw-checklist">
        {passwordRules.map((rule) => {
          const ok = rule.test(password);
          return (
            <li key={rule.key} className={`pw-checklist-item ${ok ? 'pw-checklist-item--pass' : ''}`}>
              <span className="pw-checklist-glyph">{ok ? '✓' : '○'}</span>
              {rule.label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
