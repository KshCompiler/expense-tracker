// Keep this character set in sync by hand with PASSWORD_SPECIAL_CHARS in
// backend/app/constants.py - there's no shared source across Python/TS.
export const PASSWORD_SPECIAL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?/~`';

const UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const LOWERCASE = 'abcdefghijklmnopqrstuvwxyz';
const DIGITS = '0123456789';
const ALL_CHARS = UPPERCASE + LOWERCASE + DIGITS + PASSWORD_SPECIAL_CHARS;

const GENERATED_PASSWORD_LENGTH = 14;

function randomInt(max: number): number {
  const arr = new Uint32Array(1);
  window.crypto.getRandomValues(arr);
  return arr[0] % max;
}

function randomChar(pool: string): string {
  return pool[randomInt(pool.length)];
}

export function generateStrongPassword(length: number = GENERATED_PASSWORD_LENGTH): string {
  const required = [randomChar(UPPERCASE), randomChar(LOWERCASE), randomChar(DIGITS), randomChar(PASSWORD_SPECIAL_CHARS)];
  const rest = Array.from({ length: Math.max(length - required.length, 0) }, () => randomChar(ALL_CHARS));
  const chars = [...required, ...rest];

  for (let i = chars.length - 1; i > 0; i--) {
    const j = randomInt(i + 1);
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }

  return chars.join('');
}
