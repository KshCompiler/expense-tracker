from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import BUDGET_WARNING_THRESHOLD
from app.models import Budget, Expense, Income, OAuthAccount, User
from app.schemas import BudgetStatus
from app.security import hash_password


class OAuthUnverifiedEmailError(Exception):
    """Raised by get_or_create_oauth_user when the provider reports
    email_verified=False and there's no existing (provider, sub) link to
    fall back on. Refusing to create/link an account off an unverified
    email is what prevents account takeover via a spoofed email claim."""


# ------------------------------------------------------------------ #
# Users                                                               #
# ------------------------------------------------------------------ #

def create_user(db: Session, full_name: str, email: str, password: str) -> User:
    user = User(full_name=full_name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def update_user_password(db: Session, user: User, new_password_hash: str) -> None:
    user.password_hash = new_password_hash
    db.commit()


# ------------------------------------------------------------------ #
# OAuth accounts                                                      #
# ------------------------------------------------------------------ #

def get_oauth_account(db: Session, provider: str, provider_user_id: str) -> OAuthAccount | None:
    return db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    ).scalar_one_or_none()


def link_oauth_account(db: Session, user_id: int, provider: str, provider_user_id: str) -> OAuthAccount:
    account = OAuthAccount(user_id=user_id, provider=provider, provider_user_id=provider_user_id)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_oauth_user(db: Session, full_name: str, email: str, provider: str, provider_user_id: str) -> User:
    user = User(full_name=full_name, email=email, password_hash=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    link_oauth_account(db, user.id, provider, provider_user_id)
    return user


def get_or_create_oauth_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str,
    full_name: str,
    email_verified: bool,
) -> User:
    # (1) Existing link for this exact (provider, sub) wins outright, regardless
    # of email_verified on this call - the identity was already established.
    existing_link = get_oauth_account(db, provider, provider_user_id)
    if existing_link is not None:
        return get_user_by_id(db, existing_link.user_id)

    # (2) No existing link. Only trust the provider's email to resolve/create
    # an account if the provider itself confirms it's verified.
    if email_verified:
        user = get_user_by_email(db, email)
        if user is not None:
            link_oauth_account(db, user.id, provider, provider_user_id)
            return user
        return create_oauth_user(db, full_name, email, provider, provider_user_id)

    # (3) Unverified email and no existing (provider, sub) link - refuse.
    raise OAuthUnverifiedEmailError(f"{provider} did not confirm email_verified for a new identity")


def _month_date(now: datetime, months_ago: int, day: int) -> str:
    total = (now.year * 12 + (now.month - 1)) - months_ago
    year, month = divmod(total, 12)
    month += 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def seed_db(db: Session) -> None:
    if db.execute(select(func.count()).select_from(User)).scalar_one() > 0:
        return

    user = User(
        full_name="Demo User",
        email="demo@spendly.com",
        password_hash=hash_password("demo123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    now = datetime.now()
    md = lambda months_ago, day: _month_date(now, months_ago, day)  # noqa: E731

    expenses = [
        Expense(user_id=user.id, amount=450.00, category="Food", date=md(2, 1), description="Groceries from D-Mart"),
        Expense(user_id=user.id, amount=120.00, category="Transport", date=md(2, 2), description="Metro card recharge"),
        Expense(user_id=user.id, amount=1200.00, category="Bills", date=md(2, 3), description="Electricity bill"),
        Expense(user_id=user.id, amount=350.00, category="Health", date=md(2, 5), description="Pharmacy — vitamins"),
        Expense(user_id=user.id, amount=500.00, category="Entertainment", date=md(2, 6), description="Movie tickets"),
        Expense(user_id=user.id, amount=800.00, category="Shopping", date=md(2, 7), description="New earphones"),
        Expense(user_id=user.id, amount=200.00, category="Other", date=md(2, 8), description="Miscellaneous"),
        Expense(user_id=user.id, amount=180.00, category="Food", date=md(2, 8), description="Lunch with colleagues"),
        Expense(user_id=user.id, amount=520.00, category="Food", date=md(1, 2), description="Weekly groceries"),
        Expense(user_id=user.id, amount=250.00, category="Transport", date=md(1, 4), description="Cab rides"),
        Expense(user_id=user.id, amount=1400.00, category="Bills", date=md(1, 5), description="Rent contribution"),
        Expense(user_id=user.id, amount=600.00, category="Shopping", date=md(1, 10), description="Clothing"),
        Expense(user_id=user.id, amount=300.00, category="Health", date=md(1, 14), description="Doctor visit"),
        Expense(user_id=user.id, amount=150.00, category="Entertainment", date=md(1, 18), description="Streaming subscriptions"),
        Expense(user_id=user.id, amount=420.00, category="Food", date=md(1, 22), description="Restaurant dinner"),
        Expense(user_id=user.id, amount=680.00, category="Food", date=md(0, 1), description="Groceries — Big Basket"),
        Expense(user_id=user.id, amount=1500.00, category="Bills", date=md(0, 3), description="Electricity + internet"),
        Expense(user_id=user.id, amount=200.00, category="Transport", date=md(0, 5), description="Auto and cab rides"),
        Expense(user_id=user.id, amount=450.00, category="Health", date=md(0, 8), description="Gym membership"),
        Expense(user_id=user.id, amount=900.00, category="Shopping", date=md(0, 10), description="New shoes"),
        Expense(user_id=user.id, amount=350.00, category="Entertainment", date=md(0, 14), description="Concert tickets"),
        Expense(user_id=user.id, amount=280.00, category="Food", date=md(0, 17), description="Team lunch"),
        Expense(user_id=user.id, amount=120.00, category="Transport", date=md(0, 19), description="Metro monthly pass"),
        Expense(user_id=user.id, amount=175.00, category="Other", date=md(0, 21), description="Stationery and misc"),
    ]
    db.add_all(expenses)

    income_entries = [
        Income(user_id=user.id, amount=50000.00, source="Salary", date=md(2, 1), description="Monthly salary"),
        Income(user_id=user.id, amount=5000.00, source="Freelance", date=md(2, 15), description="Web design project"),
        Income(user_id=user.id, amount=50000.00, source="Salary", date=md(1, 1), description="Monthly salary"),
        Income(user_id=user.id, amount=3500.00, source="Freelance", date=md(1, 20), description="Logo design"),
        Income(user_id=user.id, amount=50000.00, source="Salary", date=md(0, 1), description="Monthly salary"),
        Income(user_id=user.id, amount=8000.00, source="Freelance", date=md(0, 10), description="App development project"),
    ]
    db.add_all(income_entries)
    db.commit()


# ------------------------------------------------------------------ #
# Expenses / Income - reads                                           #
# ------------------------------------------------------------------ #

def get_user_expenses_this_month(db: Session, user_id: int) -> list[Expense]:
    current_month = datetime.now().strftime("%Y-%m")
    stmt = (
        select(Expense)
        .where(Expense.user_id == user_id, Expense.date.like(f"{current_month}%"))
        .order_by(Expense.date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_user_income_this_month(db: Session, user_id: int) -> list[Income]:
    current_month = datetime.now().strftime("%Y-%m")
    stmt = (
        select(Income)
        .where(Income.user_id == user_id, Income.date.like(f"{current_month}%"))
        .order_by(Income.date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_expenses_by_category(db: Session, user_id: int) -> list[tuple[str, float]]:
    current_month = datetime.now().strftime("%Y-%m")
    stmt = (
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.user_id == user_id, Expense.date.like(f"{current_month}%"))
        .group_by(Expense.category)
    )
    return [(category, float(total)) for category, total in db.execute(stmt).all()]


def get_recent_transactions(db: Session, user_id: int, limit: int = 5) -> list[Expense]:
    stmt = (
        select(Expense)
        .where(Expense.user_id == user_id)
        .order_by(Expense.date.desc(), Expense.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


# ------------------------------------------------------------------ #
# Expenses / Income - writes                                         #
# ------------------------------------------------------------------ #

def add_income(db: Session, user_id: int, amount: float, source: str, date: str, description: str | None) -> Income:
    income = Income(user_id=user_id, amount=amount, source=source, date=date, description=description)
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def add_expense(db: Session, user_id: int, amount: float, category: str, date: str, description: str | None) -> Expense:
    expense = Expense(user_id=user_id, amount=amount, category=category, date=date, description=description)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expense_by_id(db: Session, expense_id: int) -> Expense | None:
    return db.execute(select(Expense).where(Expense.id == expense_id)).scalar_one_or_none()


def update_expense(db: Session, expense_id: int, amount: float, category: str, date: str, description: str | None) -> Expense:
    expense = get_expense_by_id(db, expense_id)
    expense.amount = amount
    expense.category = category
    expense.date = date
    expense.description = description
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense_helper(db: Session, expense_id: int) -> None:
    expense = get_expense_by_id(db, expense_id)
    if expense is not None:
        db.delete(expense)
        db.commit()


# ------------------------------------------------------------------ #
# Filtered / paginated transactions                                   #
# ------------------------------------------------------------------ #

def _apply_filters(stmt, user_id: int, from_date: str | None, to_date: str | None, q: str | None):
    stmt = stmt.where(Expense.user_id == user_id)
    if from_date:
        stmt = stmt.where(Expense.date >= from_date)
    if to_date:
        stmt = stmt.where(Expense.date <= to_date)
    if q:
        stmt = stmt.where(func.lower(Expense.description).like(f"%{q.lower()}%"))
    return stmt


def get_filtered_transactions(
    db: Session,
    user_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Expense]:
    stmt = _apply_filters(select(Expense), user_id, from_date, to_date, q)
    stmt = stmt.order_by(Expense.date.desc(), Expense.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def count_filtered_transactions(
    db: Session,
    user_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
    q: str | None = None,
) -> int:
    stmt = _apply_filters(select(func.count()).select_from(Expense), user_id, from_date, to_date, q)
    return db.execute(stmt).scalar_one()


# ------------------------------------------------------------------ #
# Monthly aggregates                                                  #
# ------------------------------------------------------------------ #

def get_monthly_expense_summary(db: Session, user_id: int, year_month: str) -> list[tuple[str, float]]:
    stmt = (
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.user_id == user_id, Expense.date.like(f"{year_month}%"))
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    )
    return [(category, float(total)) for category, total in db.execute(stmt).all()]


def get_monthly_income_total(db: Session, user_id: int, year_month: str) -> float:
    stmt = select(func.coalesce(func.sum(Income.amount), 0.0)).where(
        Income.user_id == user_id, Income.date.like(f"{year_month}%")
    )
    return float(db.execute(stmt).scalar_one())


def get_monthly_expense_totals(db: Session, user_id: int, months: int = 6) -> list[dict]:
    now = datetime.now()
    keys = []
    for i in range(months - 1, -1, -1):
        total_months = (now.year * 12 + (now.month - 1)) - i
        year, month = divmod(total_months, 12)
        month += 1
        keys.append(f"{year:04d}-{month:02d}")

    stmt = (
        select(func.strftime("%Y-%m", Expense.date), func.sum(Expense.amount))
        .where(Expense.user_id == user_id, Expense.date >= f"{keys[0]}-01")
        .group_by(func.strftime("%Y-%m", Expense.date))
    )
    totals_by_key = {ym: float(total) for ym, total in db.execute(stmt).all()}

    return [
        {
            "year_month": key,
            "label": datetime.strptime(key, "%Y-%m").strftime("%b"),
            "total": totals_by_key.get(key, 0.0),
        }
        for key in keys
    ]


def get_user_lifetime_totals(db: Session, user_id: int) -> tuple[float, float, int]:
    total_expenses = db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(Expense.user_id == user_id)
    ).scalar_one()
    total_income = db.execute(
        select(func.coalesce(func.sum(Income.amount), 0.0)).where(Income.user_id == user_id)
    ).scalar_one()
    transaction_count = db.execute(
        select(func.count()).select_from(Expense).where(Expense.user_id == user_id)
    ).scalar_one()
    return float(total_expenses), float(total_income), int(transaction_count)


# ------------------------------------------------------------------ #
# Budgets                                                             #
# ------------------------------------------------------------------ #

def get_user_budgets(db: Session, user_id: int) -> list[Budget]:
    stmt = select(Budget).where(Budget.user_id == user_id).order_by(Budget.category)
    return list(db.execute(stmt).scalars().all())


def get_budget_by_id(db: Session, budget_id: int) -> Budget | None:
    return db.execute(select(Budget).where(Budget.id == budget_id)).scalar_one_or_none()


def get_budget_by_category(db: Session, user_id: int, category: str) -> Budget | None:
    return db.execute(
        select(Budget).where(Budget.user_id == user_id, Budget.category == category)
    ).scalar_one_or_none()


def create_budget(db: Session, user_id: int, category: str, monthly_limit: float) -> Budget:
    budget = Budget(user_id=user_id, category=category, monthly_limit=monthly_limit)
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def update_budget(db: Session, budget_id: int, monthly_limit: float) -> Budget:
    budget = get_budget_by_id(db, budget_id)
    budget.monthly_limit = monthly_limit
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, budget_id: int) -> None:
    budget = get_budget_by_id(db, budget_id)
    if budget is not None:
        db.delete(budget)
        db.commit()


def compute_budget_statuses(db: Session, user_id: int) -> list[BudgetStatus]:
    budgets = get_user_budgets(db, user_id)
    if not budgets:
        return []

    category_totals = dict(get_expenses_by_category(db, user_id))
    overall_total: float | None = None
    statuses = []
    for budget in budgets:
        if budget.category == "Overall":
            if overall_total is None:
                overall_total = sum(e.amount for e in get_user_expenses_this_month(db, user_id))
            spent = overall_total
        else:
            spent = category_totals.get(budget.category, 0.0)

        percent_used = (spent / budget.monthly_limit) * 100 if budget.monthly_limit else 0.0
        if percent_used >= 100:
            status = "over"
        elif percent_used >= BUDGET_WARNING_THRESHOLD * 100:
            status = "warning"
        else:
            status = "ok"

        statuses.append(
            BudgetStatus(
                id=budget.id,
                category=budget.category,
                monthly_limit=budget.monthly_limit,
                spent=spent,
                percent_used=round(percent_used, 1),
                remaining=round(budget.monthly_limit - spent, 2),
                status=status,
            )
        )
    return statuses


def get_category_spend_history(db: Session, user_id: int, category: str, months: int = 3) -> list[float]:
    now = datetime.now()
    keys = []
    for i in range(months - 1, -1, -1):
        total_months = (now.year * 12 + (now.month - 1)) - i
        year, month = divmod(total_months, 12)
        month += 1
        keys.append(f"{year:04d}-{month:02d}")

    stmt = select(func.strftime("%Y-%m", Expense.date), func.sum(Expense.amount)).where(
        Expense.user_id == user_id, Expense.date >= f"{keys[0]}-01"
    )
    if category != "Overall":
        stmt = stmt.where(Expense.category == category)
    stmt = stmt.group_by(func.strftime("%Y-%m", Expense.date))
    totals_by_key = {ym: float(total) for ym, total in db.execute(stmt).all()}
    return [totals_by_key.get(key, 0.0) for key in keys]
