import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
VALID_CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}
VALID_INCOME_SOURCES = {"Salary", "Freelance", "Business", "Investment", "Gift", "Other"}

ALLOWED_BILL_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BILL_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_REQUEST_BODY_BYTES = 6 * 1024 * 1024  # 6 MB, mirrors original Flask MAX_CONTENT_LENGTH
