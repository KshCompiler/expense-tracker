from datetime import date as date_type, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, model_validator

from app.constants import (
    EMAIL_REGEX,
    PASSWORD_DIGIT_REGEX,
    PASSWORD_MIN_LENGTH,
    PASSWORD_SPECIAL_REGEX,
    PASSWORD_UPPERCASE_REGEX,
    VALID_CATEGORIES,
    VALID_INCOME_SOURCES,
)


def _check_email(v: str) -> str:
    if not EMAIL_REGEX.match(v):
        raise ValueError("Please enter a valid email address!")
    return v


def _check_password_strength(v: str) -> str:
    unmet = []
    if len(v) < PASSWORD_MIN_LENGTH:
        unmet.append("be at least 8 characters long")
    if not PASSWORD_UPPERCASE_REGEX.search(v):
        unmet.append("contain an uppercase letter")
    if not PASSWORD_DIGIT_REGEX.search(v):
        unmet.append("contain a number")
    if not PASSWORD_SPECIAL_REGEX.search(v):
        unmet.append("contain a special character")
    if unmet:
        raise ValueError("Password must " + ", ".join(unmet) + "!")
    return v


def _parse_amount(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        raise ValueError("Please enter a valid amount!")


def _check_positive_amount(v: float) -> float:
    if v <= 0:
        raise ValueError("Amount must be greater than zero!")
    return v


def _parse_form_date(v):
    if isinstance(v, str):
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Please enter a valid date!")
    return v


def _check_category(v: str) -> str:
    if v not in VALID_CATEGORIES:
        raise ValueError("Please select a valid category!")
    return v


def _check_income_source(v: str) -> str:
    if v not in VALID_INCOME_SOURCES:
        raise ValueError("Please select a valid income source!")
    return v


Email = Annotated[str, AfterValidator(_check_email)]
Password = Annotated[str, AfterValidator(_check_password_strength)]
PositiveAmount = Annotated[float, BeforeValidator(_parse_amount), AfterValidator(_check_positive_amount)]
FormDate = Annotated[date_type, BeforeValidator(_parse_form_date)]
Category = Annotated[str, AfterValidator(_check_category)]
IncomeSource = Annotated[str, AfterValidator(_check_income_source)]


class RegisterRequest(BaseModel):
    full_name: str
    email: Email
    password: Password
    confirm_password: str

    @model_validator(mode="before")
    @classmethod
    def check_required_and_match(cls, data):
        if not isinstance(data, dict):
            return data

        if not data.get("full_name") or not data.get("email") or not data.get("password") or not data.get("confirm_password"):
            raise ValueError("All fields are required!")
        if data.get("password") != data.get("confirm_password"):
            raise ValueError("Passwords do not match!")
        return data


class LoginRequest(BaseModel):
    email: str
    password: str

    @model_validator(mode="before")
    @classmethod
    def check_required(cls, data):
        if not isinstance(data, dict):
            return data
        if not data.get("email") or not data.get("password"):
            raise ValueError("Email and password are required!")
        return data


class ForgotPasswordRequest(BaseModel):
    email: Email

    @model_validator(mode="before")
    @classmethod
    def check_required(cls, data):
        if not isinstance(data, dict):
            return data
        if not data.get("email"):
            raise ValueError("Email is required!")
        return data


class ResetPasswordRequest(BaseModel):
    token: str
    password: Password
    confirm_password: str

    @model_validator(mode="before")
    @classmethod
    def check_required_and_match(cls, data):
        if not isinstance(data, dict):
            return data
        if not data.get("token") or not data.get("password") or not data.get("confirm_password"):
            raise ValueError("All fields are required!")
        if data.get("password") != data.get("confirm_password"):
            raise ValueError("Passwords do not match!")
        return data


class MessageOut(BaseModel):
    message: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str


class ProfileOut(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: str
    total_expenses_all_time: float
    total_income_all_time: float
    transaction_count_all_time: int


class ExpenseIn(BaseModel):
    amount: PositiveAmount
    category: Category
    date: FormDate
    description: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_required(cls, data):
        if not isinstance(data, dict):
            return data
        if not data.get("amount") or not data.get("category") or not data.get("date"):
            raise ValueError("Amount, category, and date are required!")
        return data


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount: float
    category: str
    date: str
    description: str | None
    created_at: str


class IncomeIn(BaseModel):
    amount: PositiveAmount
    source: IncomeSource
    date: FormDate
    description: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_required(cls, data):
        if not isinstance(data, dict):
            return data
        if not data.get("amount") or not data.get("source") or not data.get("date"):
            raise ValueError("Amount, source, and date are required!")
        return data


class IncomeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    amount: float
    source: str
    date: str
    description: str | None
    created_at: str


class CategoryTotal(BaseModel):
    category: str
    total: float


class MonthlyTrendPoint(BaseModel):
    year_month: str
    label: str
    total: float


class DashboardOut(BaseModel):
    user: UserOut
    today_date: str
    current_time: str
    total_expenses: float
    total_income: float
    remaining_balance: float
    transaction_count: int
    categories: list[CategoryTotal]
    recent_transactions: list[ExpenseOut]
    has_transactions: bool
    monthly_trend: list[MonthlyTrendPoint]


class TransactionsPage(BaseModel):
    items: list[ExpenseOut]
    page: int
    per_page: int
    total: int
    total_pages: int
    invalid_range: bool


class BillExtractionOut(BaseModel):
    amount: float | None
    date: str | None
    description: str | None
    category: str | None = None
    source: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
