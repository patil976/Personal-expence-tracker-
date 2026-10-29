"""
expense_manager.py - Business logic: validation, transactions, budgets.

The GUI talks only to ExpenseManager. ExpenseManager validates data, applies
the rules, and uses JSONStorage (storage.py) to save records and the helper
functions in reports.py to calculate summaries.
"""

import math
from datetime import datetime

import reports
from storage import JSONStorage

EXPENSE_CATEGORIES = ["Food", "Travel", "Education", "Shopping",
                      "Entertainment", "Bills", "Health", "Other"]
INCOME_SOURCES = ["Salary", "Pocket Money", "Scholarship", "Other"]
PAYMENT_METHODS = ["Cash", "UPI", "Card", "Bank Transfer"]

DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"
MAX_AMOUNT = 100_000_000
MAX_DESCRIPTION_LENGTH = 200
WARNING_PERCENT = 80  # show a warning when 80% of the budget is used


class ValidationError(ValueError):
    """Raised when user input is invalid. The message is safe to show to the user."""


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------
def parse_amount(value):
    """Convert text to a positive float rounded to 2 decimals."""
    text = str(value).strip().replace(",", "")
    if not text:
        raise ValidationError("Amount is required.")
    try:
        amount = float(text)
    except ValueError:
        raise ValidationError("Amount must be a valid number (for example 250 or 99.50).") from None
    if not math.isfinite(amount):
        raise ValidationError("Amount must be a valid number.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if amount > MAX_AMOUNT:
        raise ValidationError(f"Amount is too large (maximum {MAX_AMOUNT:,}).")
    return round(amount, 2)


def parse_date(value):
    """Validate a date typed as YYYY-MM-DD and return it in that format."""
    text = str(value).strip()
    if not text:
        raise ValidationError("Date is required.")
    try:
        return datetime.strptime(text, DATE_FORMAT).strftime(DATE_FORMAT)
    except ValueError:
        raise ValidationError("Invalid date. Use the format YYYY-MM-DD (for example 2026-10-27).") from None


def parse_month(value):
    """Validate a month typed as YYYY-MM and return it in that format."""
    text = str(value).strip()
    if not text:
        raise ValidationError("Month is required.")
    try:
        return datetime.strptime(text, MONTH_FORMAT).strftime(MONTH_FORMAT)
    except ValueError:
        raise ValidationError("Invalid month. Use the format YYYY-MM (for example 2026-10).") from None


def _choose(value, allowed, field_name):
    """Make sure a required value is one of the allowed options (case-insensitive)."""
    text = str(value).strip()
    if not text:
        raise ValidationError(f"{field_name} is required.")
    for option in allowed:
        if option.lower() == text.lower():
            return option
    raise ValidationError(f"{field_name} must be one of: {', '.join(allowed)}.")


def _clean_description(value):
    text = " ".join(str(value or "").split())
    if len(text) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters.")
    return text


def build_record(tx_type, amount, category, date, payment_method="", description=""):
    """Validate every field and return a clean record (without ID)."""
    if tx_type == "income":
        category = _choose(category, INCOME_SOURCES, "Income source")
        payment_method = "-"
    elif tx_type == "expense":
        category = _choose(category, EXPENSE_CATEGORIES, "Expense category")
        payment_method = _choose(payment_method, PAYMENT_METHODS, "Payment method")
    else:
        raise ValidationError("Transaction type must be 'income' or 'expense'.")
    return {
        "date": parse_date(date),
        "type": tx_type,
        "category": category,
        "amount": parse_amount(amount),
        "payment_method": payment_method,
        "description": _clean_description(description),
    }


# ----------------------------------------------------------------------
# Manager class
# ----------------------------------------------------------------------
class ExpenseManager:
    def __init__(self, storage=None):
        self.storage = storage or JSONStorage()

    @property
    def currency_symbol(self):
        return self.storage.load_settings().get("currency_symbol", "\u20b9")

    # ---------------- add / edit / delete ----------------
    def add_income(self, amount, source, date, description=""):
        record = build_record("income", amount, source, date, "", description)
        return self.storage.add_transaction(record)

    def add_expense(self, amount, category, date, payment_method, description=""):
        record = build_record("expense", amount, category, date, payment_method, description)
        return self.storage.add_transaction(record)

    def update_transaction(self, tx_id, amount, category, date, payment_method="", description=""):
        existing = self.storage.get_transaction(tx_id)
        record = build_record(existing["type"], amount, category, date, payment_method, description)
        return self.storage.update_transaction(tx_id, record)

    def delete_transaction(self, tx_id):
        self.storage.delete_transaction(tx_id)

    def get_transaction(self, tx_id):
        return self.storage.get_transaction(tx_id)

    # ---------------- queries ----------------
    @staticmethod
    def _sort_newest_first(transactions):
        return sorted(transactions, key=lambda t: (t["date"], t["id"]), reverse=True)

    def get_all_transactions(self):
        return self._sort_newest_first(self.storage.load_transactions())

    def get_recent_transactions(self, limit=8):
        return self.get_all_transactions()[:limit]

    def search_transactions(self, keyword="", tx_type="All", category="All", date_from="", date_to=""):
        """Filter by keyword, type, category and an optional date range."""
        start = parse_date(date_from) if str(date_from).strip() else None
        end = parse_date(date_to) if str(date_to).strip() else None
        if start and end and start > end:
            raise ValidationError("'From' date must not be later than 'To' date.")

        keyword = str(keyword).strip().lower()
        wanted_type = str(tx_type).strip().lower()
        results = []
        for t in self.storage.load_transactions():
            if wanted_type in ("income", "expense") and t["type"] != wanted_type:
                continue
            if category not in ("", "All") and t["category"].lower() != category.lower():
                continue
            if start and t["date"] < start:
                continue
            if end and t["date"] > end:
                continue
            if keyword:
                haystack = " ".join([t["id"], t["description"], t["category"],
                                     t["payment_method"], t["date"], f"{t['amount']:.2f}"]).lower()
                if keyword not in haystack:
                    continue
            results.append(t)
        return self._sort_newest_first(results)

    # ---------------- summaries ----------------
    @staticmethod
    def current_month():
        return datetime.now().strftime(MONTH_FORMAT)

    def get_totals(self):
        return reports.calculate_totals(self.storage.load_transactions())

    def get_monthly_expense(self, month=None):
        month = month or self.current_month()
        return reports.monthly_summary(self.storage.load_transactions(), month)["expense"]

    def get_category_totals(self, month=None):
        transactions = self.storage.load_transactions()
        if month:
            transactions = reports.filter_by_month(transactions, month)
        return reports.category_totals(transactions, "expense")

    def get_monthly_summary(self, month):
        return reports.monthly_summary(self.storage.load_transactions(), parse_month(month))

    def get_daily_summary(self, month):
        return reports.daily_summary(self.storage.load_transactions(), parse_month(month))

    def get_monthly_comparison(self):
        return reports.monthly_income_vs_expense(self.storage.load_transactions())

    def get_daily_spending(self, month):
        return reports.daily_spending_series(self.storage.load_transactions(), parse_month(month))

    def get_available_months(self):
        return reports.available_months(self.storage.load_transactions())

    # ---------------- budgets ----------------
    def set_budget(self, month, amount):
        month = parse_month(month)
        amount = parse_amount(amount)
        self.storage.set_budget(month, amount)
        return month, amount

    def get_budget_status(self, month=None):
        """Return budget, spent, remaining, percent used and a warning level."""
        month = parse_month(month) if month else self.current_month()
        budget = self.storage.get_budget(month)
        spent = self.get_monthly_expense(month)
        symbol = self.currency_symbol

        status = {"month": month, "budget": budget, "spent": spent, "remaining": None,
                  "percent_used": 0.0, "level": "none", "message": "No budget has been set for this month."}
        if not budget:
            return status

        status["remaining"] = round(budget - spent, 2)
        status["percent_used"] = round(spent / budget * 100, 1)
        if spent > budget:
            status["level"] = "exceeded"
            status["message"] = (f"Budget exceeded! You are over by {symbol}{spent - budget:,.2f}.")
        elif status["percent_used"] >= WARNING_PERCENT:
            status["level"] = "warning"
            status["message"] = (f"Warning: you have used {status['percent_used']:.1f}% of your budget. "
                                 f"Only {symbol}{budget - spent:,.2f} is left.")
        else:
            status["level"] = "ok"
            status["message"] = f"You are within budget ({status['percent_used']:.1f}% used)."
        return status

    def get_all_budget_status(self):
        return [self.get_budget_status(month) for month in sorted(self.storage.load_budgets(), reverse=True)]

    # ---------------- export ----------------
    def export_report(self, filepath, month=None):
        """Export all data, or one month, to a CSV file."""
        transactions = self.storage.load_transactions()
        budget_status = None
        if month:
            month = parse_month(month)
            transactions = reports.filter_by_month(transactions, month)
            budget_status = self.get_budget_status(month)
            scope = f"Month {month}"
        else:
            scope = "All time"
        return reports.export_report_csv(filepath, self._sort_newest_first(transactions), scope, budget_status)
