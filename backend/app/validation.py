from datetime import datetime

from fastapi import HTTPException, status


def validate_transaction_input(
    amount_raw: str | None,
    field_value: str | None,
    valid_values: set[str],
    date_raw: str | None,
    short_label: str,
    descriptive_label: str | None = None,
) -> tuple[float, str]:
    """Shared validation for expense/income create+edit forms. Mirrors the
    original Flask route's field-by-field checks and error copy exactly.
    `short_label` is used in "Amount, X, and date are required!" (e.g. "category"
    or "source"); `descriptive_label` (defaults to short_label) is used in
    "Please select a valid Y!" (e.g. "category" or "income source")."""
    descriptive_label = descriptive_label or short_label

    if not amount_raw or not field_value or not date_raw:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Amount, {short_label}, and date are required!",
        )

    if field_value not in valid_values:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Please select a valid {descriptive_label}!")

    try:
        datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Please enter a valid date!")

    try:
        amount = float(amount_raw)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Please enter a valid amount!")

    if amount <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Amount must be greater than zero!")

    return amount, date_raw
