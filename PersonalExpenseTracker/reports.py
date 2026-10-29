"""
reports.py - Pure calculation functions for summaries, reports and CSV export.

These functions receive a list of transaction dictionaries and return plain
Python data. They do not touch the GUI or read JSON files themselves.
"""

import calendar
import csv
from collections import defaultdict
from datetime import datetime


def calculate_totals(transactions):
    """Return (total_income, total_expense, balance). Balance = Income - Expenses."""
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expense = sum(t["amount"] for t in transactions if t["type"] == "expense")
    return round(income, 2), round(expense, 2), round(income - expense, 2)


def filter_by_month(transactions, month):
    """Keep only transactions whose date starts with 'YYYY-MM'."""
    return [t for t in transactions if t["date"].startswith(month)]


def category_totals(transactions, tx_type="expense"):
    """Return {category: total} for the given type, largest first."""
    totals = defaultdict(float)
    for t in transactions:
        if t["type"] == tx_type:
            totals[t["category"]] += t["amount"]
    ordered = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
    return {name: round(amount, 2) for name, amount in ordered}


def monthly_summary(transactions, month):
    """Income, expenses, savings and highest spending category for one month."""
    month_tx = filter_by_month(transactions, month)
    income, expense, savings = calculate_totals(month_tx)
    categories = category_totals(month_tx, "expense")
    if categories:
        top_category = next(iter(categories))
        top_amount = categories[top_category]
    else:
        top_category, top_amount = None, 0.0
    return {
        "month": month,
        "income": income,
        "expense": expense,
        "savings": savings,
        "highest_category": top_category,
        "highest_amount": top_amount,
        "category_totals": categories,
        "transaction_count": len(month_tx),
    }


def daily_summary(transactions, month):
    """Return rows (date, income, expense, net) for each day that has activity."""
    per_day = defaultdict(lambda: [0.0, 0.0])
    for t in filter_by_month(transactions, month):
        slot = 0 if t["type"] == "income" else 1
        per_day[t["date"]][slot] += t["amount"]
    rows = []
    for day in sorted(per_day):
        income, expense = per_day[day]
        rows.append((day, round(income, 2), round(expense, 2), round(income - expense, 2)))
    return rows


def monthly_income_vs_expense(transactions):
    """Return rows (month, income, expense) in chronological order."""
    per_month = defaultdict(lambda: [0.0, 0.0])
    for t in transactions:
        slot = 0 if t["type"] == "income" else 1
        per_month[t["date"][:7]][slot] += t["amount"]
    return [(m, round(v[0], 2), round(v[1], 2)) for m, v in sorted(per_month.items())]


def daily_spending_series(transactions, month):
    """Return (day_numbers, expense_per_day) for every day of the month (zeros included)."""
    year, month_number = (int(part) for part in month.split("-"))
    days_in_month = calendar.monthrange(year, month_number)[1]
    spending = {day: 0.0 for day in range(1, days_in_month + 1)}
    for t in filter_by_month(transactions, month):
        if t["type"] == "expense":
            spending[int(t["date"][8:10])] += t["amount"]
    return list(spending.keys()), [round(v, 2) for v in spending.values()]


def available_months(transactions):
    """All months that have data, plus the current month (newest first)."""
    months = {t["date"][:7] for t in transactions}
    months.add(datetime.now().strftime("%Y-%m"))
    return sorted(months, reverse=True)


def export_report_csv(filepath, transactions, scope_label, budget_status=None):
    """
    Write a CSV report using the built-in csv module.
    Sections: summary, category-wise expenses, optional budget, then all transactions.
    """
    income, expense, balance = calculate_totals(transactions)
    categories = category_totals(transactions, "expense")
    ordered = sorted(transactions, key=lambda t: (t["date"], t["id"]))

    # utf-8-sig lets Excel display the currency symbol correctly.
    with open(filepath, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["PERSONAL EXPENSE TRACKER REPORT"])
        writer.writerow(["Scope", scope_label])
        writer.writerow(["Generated on", datetime.now().strftime("%Y-%m-%d %H:%M")])
        writer.writerow([])

        writer.writerow(["FINANCIAL SUMMARY"])
        writer.writerow(["Total Income", f"{income:.2f}"])
        writer.writerow(["Total Expenses", f"{expense:.2f}"])
        writer.writerow(["Balance (Savings)", f"{balance:.2f}"])
        writer.writerow([])

        writer.writerow(["CATEGORY-WISE EXPENSES"])
        writer.writerow(["Category", "Amount", "Percentage"])
        for name, amount in categories.items():
            share = (amount / expense * 100) if expense else 0
            writer.writerow([name, f"{amount:.2f}", f"{share:.1f}%"])
        writer.writerow([])

        if budget_status and budget_status.get("budget"):
            writer.writerow(["MONTHLY BUDGET"])
            writer.writerow(["Month", budget_status["month"]])
            writer.writerow(["Budget", f"{budget_status['budget']:.2f}"])
            writer.writerow(["Spent", f"{budget_status['spent']:.2f}"])
            writer.writerow(["Remaining", f"{budget_status['remaining']:.2f}"])
            writer.writerow(["Used", f"{budget_status['percent_used']:.1f}%"])
            writer.writerow([])

        writer.writerow(["TRANSACTIONS"])
        writer.writerow(["ID", "Date", "Type", "Category/Source", "Amount", "Payment Method", "Description"])
        for t in ordered:
            writer.writerow([t["id"], t["date"], t["type"].title(), t["category"],
                             f"{t['amount']:.2f}", t["payment_method"], t["description"]])
    return filepath
