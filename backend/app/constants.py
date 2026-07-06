import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

PASSWORD_MIN_LENGTH = 8
PASSWORD_UPPERCASE_REGEX = re.compile(r"[A-Z]")
PASSWORD_DIGIT_REGEX = re.compile(r"\d")
# Keep this character set in sync by hand with PASSWORD_SPECIAL_CHARS in
# frontend/src/utils/generatePassword.ts - there's no shared source across Python/TS.
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
PASSWORD_SPECIAL_REGEX = re.compile("[" + re.escape(PASSWORD_SPECIAL_CHARS) + "]")
VALID_CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}
VALID_INCOME_SOURCES = {"Salary", "Freelance", "Business", "Investment", "Gift", "Other"}

BUDGET_WARNING_THRESHOLD = 0.8
BUDGET_CATEGORIES = VALID_CATEGORIES | {"Overall"}

ALLOWED_BILL_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BILL_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_REQUEST_BODY_BYTES = 6 * 1024 * 1024  # 6 MB, mirrors original Flask MAX_CONTENT_LENGTH
