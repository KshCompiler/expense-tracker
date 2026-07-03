from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


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
    amount: str
    category: str
    date: str
    description: str | None = None


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
    amount: str
    source: str
    date: str
    description: str | None = None


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
