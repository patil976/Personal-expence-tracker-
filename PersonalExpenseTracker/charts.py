"""
charts.py - Matplotlib charts built from the stored transaction data.

The draw_* functions only need a matplotlib Figure, so they are independent of
Tkinter. embed_figure() places a Figure inside a Tkinter widget.
"""

from matplotlib.figure import Figure

PALETTE = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
           "#ec4899", "#14b8a6", "#6b7280"]


def embed_figure(parent, figsize=(7, 4)):
    """Create a Figure and show it inside a Tkinter container. Returns (figure, canvas)."""
    # Imported here so the drawing functions work even without Tkinter (e.g. in tests).
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    figure = Figure(figsize=figsize, dpi=100, constrained_layout=True)
    canvas = FigureCanvasTkAgg(figure, master=parent)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    return figure, canvas


def _show_message(figure, message):
    figure.clear()
    axis = figure.add_subplot(111)
    axis.axis("off")
    axis.text(0.5, 0.5, message, ha="center", va="center", fontsize=13, color="#6b7280")


def draw_category_pie(figure, category_totals, title):
    """Pie chart of category-wise expenses."""
    figure.clear()
    if not category_totals:
        _show_message(figure, "No expense data for this period")
        return
    axis = figure.add_subplot(111)
    labels = list(category_totals.keys())
    values = list(category_totals.values())
    axis.pie(values, labels=labels, autopct="%1.1f%%", startangle=90,
             colors=PALETTE[:len(values)] if len(values) <= len(PALETTE) else None,
             wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    axis.set_title(title, fontsize=13, fontweight="bold")
    axis.axis("equal")


def draw_income_vs_expense_bar(figure, monthly_rows, symbol=""):
    """Grouped bar chart: income versus expenses for each month."""
    figure.clear()
    if not monthly_rows:
        _show_message(figure, "No transactions to display yet")
        return
    axis = figure.add_subplot(111)
    months = [row[0] for row in monthly_rows]
    income = [row[1] for row in monthly_rows]
    expense = [row[2] for row in monthly_rows]
    positions = list(range(len(months)))
    width = 0.38
    axis.bar([p - width / 2 for p in positions], income, width, label="Income", color="#16a34a")
    axis.bar([p + width / 2 for p in positions], expense, width, label="Expenses", color="#dc2626")
    axis.set_xticks(positions)
    axis.set_xticklabels(months, rotation=30 if len(months) > 6 else 0)
    axis.set_ylabel(f"Amount ({symbol})" if symbol else "Amount")
    axis.set_title("Monthly Income vs Expenses", fontsize=13, fontweight="bold")
    axis.legend()
    axis.grid(axis="y", alpha=0.3)


def draw_spending_trend(figure, days, amounts, title, symbol=""):
    """Line chart of daily spending."""
    figure.clear()
    if not days or not any(amounts):
        _show_message(figure, "No spending recorded for this month")
        return
    axis = figure.add_subplot(111)
    axis.plot(days, amounts, marker="o", color="#3b82f6", linewidth=2)
    axis.fill_between(days, amounts, alpha=0.15, color="#3b82f6")
    axis.set_xlabel("Day of month")
    axis.set_ylabel(f"Spent ({symbol})" if symbol else "Spent")
    axis.set_title(title, fontsize=13, fontweight="bold")
    axis.grid(alpha=0.3)
