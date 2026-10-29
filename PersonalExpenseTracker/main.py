"""
main.py - Tkinter user interface for the Personal Expense Tracker.

This file contains ONLY GUI code. All rules and calculations live in
expense_manager.py / reports.py, and all file operations live in storage.py.

Run with:   python main.py
"""

import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

import charts
from expense_manager import (EXPENSE_CATEGORIES, INCOME_SOURCES, PAYMENT_METHODS,
                             ExpenseManager, ValidationError)
from storage import StorageError

# ----------------------------------------------------------------------
# Colour scheme and fonts
# ----------------------------------------------------------------------
FONT = "Segoe UI"
BG = "#f3f5f9"
CARD = "#ffffff"
SIDEBAR = "#1e293b"
SIDEBAR_HOVER = "#334155"
SIDEBAR_ACTIVE = "#3b82f6"
TEXT = "#1f2937"
MUTED = "#6b7280"
ACCENT = "#3b82f6"
ACCENT_DARK = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
AMBER = "#d97706"
BLUE = "#2563eb"

TRANSACTION_COLUMNS = [
    ("id", "ID", 80, "center"),
    ("date", "Date", 95, "center"),
    ("type", "Type", 75, "center"),
    ("category", "Category / Source", 130, "w"),
    ("amount", "Amount", 100, "e"),
    ("payment", "Payment", 110, "center"),
    ("description", "Description", 260, "w"),
]


def money(symbol, value):
    """Format a number as currency, e.g. ₹1,250.50"""
    return f"{symbol}{value:,.2f}"


def today_text():
    return date.today().strftime("%Y-%m-%d")


# ----------------------------------------------------------------------
# Styling and reusable widgets
# ----------------------------------------------------------------------
def configure_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", font=(FONT, 10), background=BG, foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT)
    style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED)
    style.configure("CardHeading.TLabel", background=CARD, foreground=TEXT, font=(FONT, 12, "bold"))
    style.configure("Title.TLabel", font=(FONT, 20, "bold"), foreground=TEXT)
    style.configure("Subtitle.TLabel", foreground=MUTED)

    style.configure("Primary.TButton", background=ACCENT, foreground="white",
                    font=(FONT, 10, "bold"), padding=(16, 8), borderwidth=0)
    style.map("Primary.TButton", background=[("active", ACCENT_DARK), ("pressed", ACCENT_DARK)])
    style.configure("Danger.TButton", background=RED, foreground="white",
                    font=(FONT, 10, "bold"), padding=(16, 8), borderwidth=0)
    style.map("Danger.TButton", background=[("active", "#b91c1c")])
    style.configure("Secondary.TButton", background="#e5e7eb", foreground=TEXT,
                    font=(FONT, 10), padding=(14, 8), borderwidth=0)
    style.map("Secondary.TButton", background=[("active", "#d1d5db")])

    style.configure("Treeview", rowheight=28, font=(FONT, 10), background="white",
                    fieldbackground="white", borderwidth=0)
    style.configure("Treeview.Heading", font=(FONT, 10, "bold"), background="#e5e7eb",
                    foreground=TEXT, padding=6)
    style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", TEXT)])
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(16, 8), font=(FONT, 10))
    style.configure("TCombobox", padding=4)
    style.configure("TEntry", padding=4)

    for name, color in (("Green", GREEN), ("Amber", AMBER), ("Red", RED), ("Blue", BLUE)):
        style.configure(f"{name}.Horizontal.TProgressbar", background=color,
                        troughcolor="#e5e7eb", thickness=18, borderwidth=0)


def create_table(parent, columns, height=10):
    """Build a Treeview with a vertical scrollbar. Returns (container_frame, tree)."""
    container = ttk.Frame(parent, style="Card.TFrame")
    names = [col[0] for col in columns]
    tree = ttk.Treeview(container, columns=names, show="headings", height=height, selectmode="browse")
    for name, heading, width, anchor in columns:
        tree.heading(name, text=heading)
        tree.column(name, width=width, anchor=anchor)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    tree.tag_configure("income", foreground=GREEN)
    tree.tag_configure("expense", foreground=RED)
    return container, tree


def clear_tree(tree):
    tree.delete(*tree.get_children())


def fill_transactions(tree, transactions, symbol, short=False):
    """Insert transaction rows. short=True is the compact layout used on the dashboard."""
    clear_tree(tree)
    for t in transactions:
        if short:
            values = (t["date"], t["type"].title(), t["category"], money(symbol, t["amount"]))
        else:
            values = (t["id"], t["date"], t["type"].title(), t["category"],
                      money(symbol, t["amount"]), t["payment_method"], t["description"])
        tree.insert("", "end", iid=t["id"], values=values, tags=(t["type"],))


class Page(ttk.Frame):
    """Base class for every screen. Subclasses override build() and refresh()."""
    title = ""
    subtitle = ""

    def __init__(self, parent, app):
        super().__init__(parent, padding=24)
        self.app = app
        self.manager = app.manager
        ttk.Label(self, text=self.title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text=self.subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(0, 16))
        self.build()

    @property
    def symbol(self):
        return self.app.symbol

    def build(self):
        pass

    def refresh(self):
        pass


# ----------------------------------------------------------------------
# Transaction form (used by Add Income, Add Expense and the Edit dialog)
# ----------------------------------------------------------------------
class TransactionForm(ttk.Frame):
    def __init__(self, parent, tx_type):
        super().__init__(parent, style="Card.TFrame", padding=24)
        self.tx_type = tx_type
        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.date_var = tk.StringVar(value=today_text())
        self.payment_var = tk.StringVar(value=PAYMENT_METHODS[0])
        self.description_var = tk.StringVar()

        is_income = tx_type == "income"
        row = 0
        self._row(row, "Amount", ttk.Entry(self, textvariable=self.amount_var, width=34)); row += 1
        self.category_box = ttk.Combobox(self, textvariable=self.category_var, state="readonly", width=32,
                                         values=INCOME_SOURCES if is_income else EXPENSE_CATEGORIES)
        self._row(row, "Source" if is_income else "Category", self.category_box); row += 1
        self._row(row, "Date (YYYY-MM-DD)", ttk.Entry(self, textvariable=self.date_var, width=34)); row += 1
        if not is_income:
            payment_box = ttk.Combobox(self, textvariable=self.payment_var, state="readonly",
                                       width=32, values=PAYMENT_METHODS)
            self._row(row, "Payment Method", payment_box); row += 1
        self._row(row, "Description / Notes", ttk.Entry(self, textvariable=self.description_var, width=34))

    def _row(self, row, label, widget):
        ttk.Label(self, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=8, padx=(0, 20))
        widget.grid(row=row, column=1, sticky="w", pady=8)

    def get_data(self):
        return {
            "amount": self.amount_var.get(),
            "category": self.category_var.get(),
            "date": self.date_var.get(),
            "payment_method": self.payment_var.get() if self.tx_type == "expense" else "",
            "description": self.description_var.get(),
        }

    def set_data(self, record):
        self.amount_var.set(f"{record['amount']:.2f}")
        self.category_var.set(record["category"])
        self.date_var.set(record["date"])
        if record["type"] == "expense":
            self.payment_var.set(record["payment_method"])
        self.description_var.set(record["description"])

    def clear(self):
        self.amount_var.set("")
        self.category_var.set("")
        self.date_var.set(today_text())
        self.payment_var.set(PAYMENT_METHODS[0])
        self.description_var.set("")


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
class DashboardPage(Page):
    title = "Dashboard"
    subtitle = "A quick overview of your money"

    def build(self):
        cards = ttk.Frame(self)
        cards.pack(fill="x")
        self.card_values = {}
        definitions = [("income", "Total Income", GREEN), ("expense", "Total Expenses", RED),
                       ("balance", "Current Balance", BLUE), ("month", "This Month's Expenses", AMBER)]
        for index, (key, label, color) in enumerate(definitions):
            cards.columnconfigure(index, weight=1, uniform="cards")
            card = ttk.Frame(cards, style="Card.TFrame", padding=16)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))
            ttk.Label(card, text=label, style="CardMuted.TLabel").pack(anchor="w")
            value = tk.Label(card, text="", font=(FONT, 18, "bold"), bg=CARD, fg=color)
            value.pack(anchor="w", pady=(6, 0))
            self.card_values[key] = value

        lower = ttk.Frame(self)
        lower.pack(fill="both", expand=True, pady=(16, 0))
        lower.columnconfigure(0, weight=3, uniform="lower")
        lower.columnconfigure(1, weight=2, uniform="lower")
        lower.rowconfigure(0, weight=1)

        left = ttk.Frame(lower, style="Card.TFrame", padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(left, text="Recent Transactions", style="CardHeading.TLabel").pack(anchor="w", pady=(0, 8))
        columns = [("date", "Date", 90, "center"), ("type", "Type", 70, "center"),
                   ("category", "Category", 110, "w"), ("amount", "Amount", 100, "e")]
        frame, self.recent_tree = create_table(left, columns, height=8)
        frame.pack(fill="both", expand=True)

        right = ttk.Frame(lower, style="Card.TFrame", padding=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(right, text="Expense Category Summary", style="CardHeading.TLabel").pack(anchor="w", pady=(0, 8))
        columns = [("category", "Category", 110, "w"), ("amount", "Total", 100, "e"), ("share", "Share", 60, "e")]
        frame, self.category_tree = create_table(right, columns, height=8)
        frame.pack(fill="both", expand=True)
        self.budget_label = ttk.Label(right, text="", style="CardMuted.TLabel", wraplength=300)
        self.budget_label.pack(anchor="w", pady=(10, 0))

    def refresh(self):
        income, expense, balance = self.manager.get_totals()
        self.card_values["income"].config(text=money(self.symbol, income))
        self.card_values["expense"].config(text=money(self.symbol, expense))
        self.card_values["balance"].config(text=money(self.symbol, balance), fg=BLUE if balance >= 0 else RED)
        self.card_values["month"].config(text=money(self.symbol, self.manager.get_monthly_expense()))

        fill_transactions(self.recent_tree, self.manager.get_recent_transactions(8), self.symbol, short=True)

        clear_tree(self.category_tree)
        totals = self.manager.get_category_totals()
        grand_total = sum(totals.values())
        for name, amount in totals.items():
            share = f"{amount / grand_total * 100:.1f}%" if grand_total else "0%"
            self.category_tree.insert("", "end", values=(name, money(self.symbol, amount), share))

        status = self.manager.get_budget_status()
        self.budget_label.config(text=f"Budget ({status['month']}): {status['message']}")


class AddIncomePage(Page):
    title = "Add Income"
    subtitle = "Record money you have received"

    def build(self):
        self.form = TransactionForm(self, "income")
        self.form.pack(anchor="nw")
        buttons = ttk.Frame(self)
        buttons.pack(anchor="w", pady=16)
        ttk.Button(buttons, text="Save Income", style="Primary.TButton", command=self.save).pack(side="left")
        ttk.Button(buttons, text="Clear", style="Secondary.TButton", command=self.form.clear).pack(side="left", padx=10)

    def save(self):
        data = self.form.get_data()
        try:
            record = self.manager.add_income(data["amount"], data["category"], data["date"], data["description"])
        except ValidationError as error:
            messagebox.showerror("Invalid Input", str(error))
            return
        except StorageError as error:
            messagebox.showerror("File Error", str(error))
            return
        messagebox.showinfo("Saved", f"Income {record['id']} of {money(self.symbol, record['amount'])} was saved.")
        self.form.clear()


class AddExpensePage(Page):
    title = "Add Expense"
    subtitle = "Record money you have spent"

    def build(self):
        self.form = TransactionForm(self, "expense")
        self.form.pack(anchor="nw")
        buttons = ttk.Frame(self)
        buttons.pack(anchor="w", pady=16)
        ttk.Button(buttons, text="Save Expense", style="Primary.TButton", command=self.save).pack(side="left")
        ttk.Button(buttons, text="Clear", style="Secondary.TButton", command=self.form.clear).pack(side="left", padx=10)

    def save(self):
        data = self.form.get_data()
        try:
            record = self.manager.add_expense(data["amount"], data["category"], data["date"],
                                              data["payment_method"], data["description"])
        except ValidationError as error:
            messagebox.showerror("Invalid Input", str(error))
            return
        except StorageError as error:
            messagebox.showerror("File Error", str(error))
            return
        messagebox.showinfo("Saved", f"Expense {record['id']} of {money(self.symbol, record['amount'])} was saved.")
        self.form.clear()
        self.app.show_budget_alert(record["date"][:7])


class EditDialog(tk.Toplevel):
    """Pop-up window for editing one transaction."""

    def __init__(self, parent, manager, record, on_saved):
        super().__init__(parent)
        self.manager = manager
        self.record = record
        self.on_saved = on_saved
        self.title(f"Edit {record['type'].title()} - {record['id']}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())

        self.form = TransactionForm(self, record["type"])
        self.form.pack(padx=16, pady=16)
        self.form.set_data(record)

        buttons = ttk.Frame(self)
        buttons.pack(pady=(0, 16))
        ttk.Button(buttons, text="Save Changes", style="Primary.TButton", command=self.save).pack(side="left")
        ttk.Button(buttons, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="left", padx=10)

        self.wait_visibility()
        self.grab_set()

    def save(self):
        try:
            self.manager.update_transaction(self.record["id"], **self.form.get_data())
        except ValidationError as error:
            messagebox.showerror("Invalid Input", str(error), parent=self)
            return
        except StorageError as error:
            messagebox.showerror("File Error", str(error), parent=self)
            return
        self.on_saved()
        self.destroy()


class TransactionsPage(Page):
    title = "Transactions"
    subtitle = "Search, filter, edit or delete your records"

    def build(self):
        self.keyword_var = tk.StringVar()
        self.type_var = tk.StringVar(value="All")
        self.category_var = tk.StringVar(value="All")
        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()

        bar = ttk.Frame(self, style="Card.TFrame", padding=12)
        bar.pack(fill="x")
        categories = ["All"] + list(dict.fromkeys(EXPENSE_CATEGORIES + INCOME_SOURCES))
        fields = [("Search", ttk.Entry(bar, textvariable=self.keyword_var, width=18)),
                  ("Type", ttk.Combobox(bar, textvariable=self.type_var, state="readonly", width=9,
                                        values=["All", "Income", "Expense"])),
                  ("Category", ttk.Combobox(bar, textvariable=self.category_var, state="readonly",
                                            width=14, values=categories)),
                  ("From", ttk.Entry(bar, textvariable=self.from_var, width=12)),
                  ("To", ttk.Entry(bar, textvariable=self.to_var, width=12))]
        for column, (label, widget) in enumerate(fields):
            ttk.Label(bar, text=label, style="CardMuted.TLabel").grid(row=0, column=column, sticky="w", padx=(0, 10))
            widget.grid(row=1, column=column, sticky="w", padx=(0, 10))
        ttk.Button(bar, text="Apply", style="Primary.TButton", command=self.apply_filters).grid(
            row=1, column=5, padx=(6, 6))
        ttk.Button(bar, text="Reset", style="Secondary.TButton", command=self.reset_filters).grid(row=1, column=6)
        ttk.Label(bar, text="Dates use YYYY-MM-DD. Leave blank for no limit.",
                  style="CardMuted.TLabel").grid(row=2, column=0, columnspan=7, sticky="w", pady=(6, 0))
        fields[0][1].bind("<Return>", lambda event: self.apply_filters())

        table_card = ttk.Frame(self, style="Card.TFrame", padding=12)
        table_card.pack(fill="both", expand=True, pady=(12, 0))
        frame, self.tree = create_table(table_card, TRANSACTION_COLUMNS, height=12)
        frame.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda event: self.edit_selected())

        footer = ttk.Frame(self)
        footer.pack(fill="x", pady=(12, 0))
        self.summary_label = ttk.Label(footer, text="", style="Subtitle.TLabel")
        self.summary_label.pack(side="left")
        ttk.Button(footer, text="Delete Selected", style="Danger.TButton", command=self.delete_selected).pack(side="right")
        ttk.Button(footer, text="Edit Selected", style="Primary.TButton", command=self.edit_selected).pack(
            side="right", padx=(0, 10))

    def refresh(self):
        self.apply_filters()

    def apply_filters(self):
        try:
            rows = self.manager.search_transactions(
                keyword=self.keyword_var.get(), tx_type=self.type_var.get(),
                category=self.category_var.get(), date_from=self.from_var.get(), date_to=self.to_var.get())
        except ValidationError as error:
            messagebox.showerror("Invalid Filter", str(error))
            return
        fill_transactions(self.tree, rows, self.symbol)
        income = sum(t["amount"] for t in rows if t["type"] == "income")
        expense = sum(t["amount"] for t in rows if t["type"] == "expense")
        self.summary_label.config(text=f"{len(rows)} transaction(s)   |   Income: {money(self.symbol, income)}"
                                       f"   |   Expenses: {money(self.symbol, expense)}")

    def reset_filters(self):
        self.keyword_var.set("")
        self.type_var.set("All")
        self.category_var.set("All")
        self.from_var.set("")
        self.to_var.set("")
        self.apply_filters()

    def _selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a transaction in the table first.")
            return None
        return selection[0]

    def edit_selected(self):
        tx_id = self._selected_id()
        if not tx_id:
            return
        try:
            record = self.manager.get_transaction(tx_id)
        except StorageError as error:
            messagebox.showerror("File Error", str(error))
            return
        EditDialog(self, self.manager, record, on_saved=self.apply_filters)

    def delete_selected(self):
        tx_id = self._selected_id()
        if not tx_id:
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete transaction {tx_id}?\nThis cannot be undone."):
            return
        try:
            self.manager.delete_transaction(tx_id)
        except StorageError as error:
            messagebox.showerror("File Error", str(error))
            return
        self.apply_filters()


class ReportsPage(Page):
    title = "Reports & Charts"
    subtitle = "Monthly and category-wise analysis"

    def build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Month:").pack(side="left")
        self.month_var = tk.StringVar(value=self.manager.current_month())
        self.month_box = ttk.Combobox(top, textvariable=self.month_var, state="readonly", width=12)
        self.month_box.pack(side="left", padx=8)
        self.month_box.bind("<<ComboboxSelected>>", lambda event: self.update_reports())
        ttk.Button(top, text="Refresh", style="Secondary.TButton", command=self.update_reports).pack(side="left")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        # --- Tab 1: text report ---
        report_tab = ttk.Frame(notebook, style="Card.TFrame", padding=14)
        notebook.add(report_tab, text="Monthly Report")
        cards = ttk.Frame(report_tab, style="Card.TFrame")
        cards.pack(fill="x")
        self.summary_labels = {}
        for index, (key, label) in enumerate([("income", "Total Income"), ("expense", "Total Expenses"),
                                              ("savings", "Monthly Savings"), ("top", "Highest Spending")]):
            cards.columnconfigure(index, weight=1, uniform="summary")
            box = ttk.Frame(cards, style="Card.TFrame")
            box.grid(row=0, column=index, sticky="w", padx=(0, 16))
            ttk.Label(box, text=label, style="CardMuted.TLabel").pack(anchor="w")
            value = tk.Label(box, text="-", font=(FONT, 14, "bold"), bg=CARD, fg=TEXT)
            value.pack(anchor="w")
            self.summary_labels[key] = value

        tables = ttk.Frame(report_tab, style="Card.TFrame")
        tables.pack(fill="both", expand=True, pady=(14, 0))
        tables.columnconfigure(0, weight=1, uniform="tables")
        tables.columnconfigure(1, weight=2, uniform="tables")
        tables.rowconfigure(1, weight=1)
        ttk.Label(tables, text="Category-wise Expenses", style="CardHeading.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tables, text="Daily Summary", style="CardHeading.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0))
        frame, self.category_tree = create_table(
            tables, [("category", "Category", 110, "w"), ("amount", "Total", 90, "e"), ("share", "Share", 60, "e")], 9)
        frame.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        frame, self.daily_tree = create_table(
            tables, [("date", "Date", 100, "center"), ("income", "Income", 100, "e"),
                     ("expense", "Expenses", 100, "e"), ("net", "Net", 100, "e")], 9)
        frame.grid(row=1, column=1, sticky="nsew", padx=(12, 0), pady=(6, 0))

        # --- Tabs 2-4: Matplotlib charts ---
        pie_tab = ttk.Frame(notebook, style="Card.TFrame")
        bar_tab = ttk.Frame(notebook, style="Card.TFrame")
        line_tab = ttk.Frame(notebook, style="Card.TFrame")
        notebook.add(pie_tab, text="Category Pie Chart")
        notebook.add(bar_tab, text="Income vs Expenses")
        notebook.add(line_tab, text="Spending Trend")
        self.pie_figure, self.pie_canvas = charts.embed_figure(pie_tab)
        self.bar_figure, self.bar_canvas = charts.embed_figure(bar_tab)
        self.line_figure, self.line_canvas = charts.embed_figure(line_tab)

    def refresh(self):
        months = self.manager.get_available_months()
        self.month_box.config(values=months)
        if self.month_var.get() not in months:
            self.month_var.set(self.manager.current_month())
        self.update_reports()

    def update_reports(self):
        month = self.month_var.get()
        summary = self.manager.get_monthly_summary(month)
        symbol = self.symbol

        self.summary_labels["income"].config(text=money(symbol, summary["income"]), fg=GREEN)
        self.summary_labels["expense"].config(text=money(symbol, summary["expense"]), fg=RED)
        self.summary_labels["savings"].config(text=money(symbol, summary["savings"]),
                                              fg=BLUE if summary["savings"] >= 0 else RED)
        if summary["highest_category"]:
            top_text = f"{summary['highest_category']} ({money(symbol, summary['highest_amount'])})"
        else:
            top_text = "No expenses"
        self.summary_labels["top"].config(text=top_text)

        clear_tree(self.category_tree)
        for name, amount in summary["category_totals"].items():
            share = amount / summary["expense"] * 100 if summary["expense"] else 0
            self.category_tree.insert("", "end", values=(name, money(symbol, amount), f"{share:.1f}%"))

        clear_tree(self.daily_tree)
        for day, income, expense, net in self.manager.get_daily_summary(month):
            self.daily_tree.insert("", "end", values=(day, money(symbol, income),
                                                      money(symbol, expense), money(symbol, net)))

        charts.draw_category_pie(self.pie_figure, summary["category_totals"], f"Expenses by Category - {month}")
        charts.draw_income_vs_expense_bar(self.bar_figure, self.manager.get_monthly_comparison(), symbol)
        days, amounts = self.manager.get_daily_spending(month)
        charts.draw_spending_trend(self.line_figure, days, amounts, f"Daily Spending Trend - {month}", symbol)
        for canvas in (self.pie_canvas, self.bar_canvas, self.line_canvas):
            canvas.draw_idle()


class BudgetPage(Page):
    title = "Budget Management"
    subtitle = "Set a monthly spending limit and track it"

    def build(self):
        self.month_var = tk.StringVar(value=self.manager.current_month())
        self.amount_var = tk.StringVar()

        form = ttk.Frame(self, style="Card.TFrame", padding=18)
        form.pack(fill="x")
        ttk.Label(form, text="Month (YYYY-MM)", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(form, textvariable=self.month_var, width=14).grid(row=0, column=1, padx=(0, 24))
        ttk.Label(form, text="Budget Amount", style="Card.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 10))
        ttk.Entry(form, textvariable=self.amount_var, width=16).grid(row=0, column=3, padx=(0, 24))
        ttk.Button(form, text="Save Budget", style="Primary.TButton", command=self.save_budget).grid(row=0, column=4)
        ttk.Button(form, text="View Status", style="Secondary.TButton", command=self.show_status).grid(
            row=0, column=5, padx=(10, 0))

        status = ttk.Frame(self, style="Card.TFrame", padding=18)
        status.pack(fill="x", pady=(14, 0))
        self.stat_labels = {}
        for index, (key, label) in enumerate([("budget", "Monthly Budget"), ("spent", "Amount Spent"),
                                              ("remaining", "Remaining Budget"), ("percent", "Budget Used")]):
            status.columnconfigure(index, weight=1, uniform="stat")
            box = ttk.Frame(status, style="Card.TFrame")
            box.grid(row=0, column=index, sticky="w")
            ttk.Label(box, text=label, style="CardMuted.TLabel").pack(anchor="w")
            value = tk.Label(box, text="-", font=(FONT, 15, "bold"), bg=CARD, fg=TEXT)
            value.pack(anchor="w")
            self.stat_labels[key] = value
        self.progress = ttk.Progressbar(status, maximum=100, style="Green.Horizontal.TProgressbar")
        self.progress.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(14, 6))
        self.message_label = tk.Label(status, text="", font=(FONT, 11, "bold"), bg=CARD, fg=MUTED)
        self.message_label.grid(row=2, column=0, columnspan=4, sticky="w")

        history = ttk.Frame(self, style="Card.TFrame", padding=14)
        history.pack(fill="both", expand=True, pady=(14, 0))
        ttk.Label(history, text="All Saved Budgets", style="CardHeading.TLabel").pack(anchor="w", pady=(0, 8))
        columns = [("month", "Month", 90, "center"), ("budget", "Budget", 110, "e"), ("spent", "Spent", 110, "e"),
                   ("remaining", "Remaining", 110, "e"), ("percent", "Used", 70, "e"), ("state", "Status", 110, "center")]
        frame, self.history_tree = create_table(history, columns, height=6)
        frame.pack(fill="both", expand=True)

    def refresh(self):
        self.show_status()

    def save_budget(self):
        try:
            month, amount = self.manager.set_budget(self.month_var.get(), self.amount_var.get())
        except ValidationError as error:
            messagebox.showerror("Invalid Input", str(error))
            return
        except StorageError as error:
            messagebox.showerror("File Error", str(error))
            return
        self.month_var.set(month)
        self.amount_var.set("")
        messagebox.showinfo("Budget Saved", f"Budget for {month} set to {money(self.symbol, amount)}.")
        self.show_status()
        self.app.show_budget_alert(month)

    def show_status(self):
        try:
            status = self.manager.get_budget_status(self.month_var.get())
        except ValidationError as error:
            messagebox.showerror("Invalid Month", str(error))
            return
        symbol = self.symbol
        colors = {"none": ("Blue", MUTED), "ok": ("Green", GREEN), "warning": ("Amber", AMBER), "exceeded": ("Red", RED)}
        bar_style, text_color = colors[status["level"]]

        if status["budget"]:
            self.stat_labels["budget"].config(text=money(symbol, status["budget"]))
            self.stat_labels["remaining"].config(text=money(symbol, status["remaining"]),
                                                 fg=RED if status["remaining"] < 0 else TEXT)
            self.stat_labels["percent"].config(text=f"{status['percent_used']:.1f}%")
        else:
            for key in ("budget", "remaining", "percent"):
                self.stat_labels[key].config(text="-", fg=TEXT)
        self.stat_labels["spent"].config(text=money(symbol, status["spent"]))
        self.progress.config(style=f"{bar_style}.Horizontal.TProgressbar", value=min(status["percent_used"], 100))
        self.message_label.config(text=status["message"], fg=text_color)

        clear_tree(self.history_tree)
        labels = {"ok": "Within budget", "warning": "Near limit", "exceeded": "Exceeded"}
        for item in self.manager.get_all_budget_status():
            self.history_tree.insert("", "end", values=(
                item["month"], money(symbol, item["budget"]), money(symbol, item["spent"]),
                money(symbol, item["remaining"]), f"{item['percent_used']:.1f}%", labels.get(item["level"], "-")))


class ExportPage(Page):
    title = "Export Report"
    subtitle = "Save your transactions and summary as a CSV file (opens in Excel)"

    def build(self):
        card = ttk.Frame(self, style="Card.TFrame", padding=24)
        card.pack(anchor="nw")
        ttk.Label(card, text="What do you want to export?", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        self.scope_var = tk.StringVar(value="All Time")
        self.scope_box = ttk.Combobox(card, textvariable=self.scope_var, state="readonly", width=24)
        self.scope_box.grid(row=1, column=0, sticky="w")
        ttk.Button(card, text="Export to CSV...", style="Primary.TButton", command=self.export).grid(
            row=2, column=0, sticky="w", pady=(18, 0))
        self.result_label = ttk.Label(card, text="", style="CardMuted.TLabel", wraplength=520)
        self.result_label.grid(row=3, column=0, sticky="w", pady=(14, 0))

    def refresh(self):
        scopes = ["All Time"] + self.manager.get_available_months()
        self.scope_box.config(values=scopes)
        if self.scope_var.get() not in scopes:
            self.scope_var.set("All Time")

    def export(self):
        scope = self.scope_var.get()
        month = None if scope == "All Time" else scope
        suggested = f"expense_report_{'all' if month is None else month}.csv"
        path = filedialog.asksaveasfilename(title="Save report", defaultextension=".csv", initialfile=suggested,
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return  # user cancelled
        try:
            self.manager.export_report(path, month)
        except (OSError, ValidationError, StorageError) as error:
            messagebox.showerror("Export Failed", f"The report could not be saved.\n\n{error}")
            return
        self.result_label.config(text=f"Report saved to: {path}")
        messagebox.showinfo("Export Complete", f"Report saved successfully:\n{path}")


# ----------------------------------------------------------------------
# Main application window
# ----------------------------------------------------------------------
class ExpenseTrackerApp(tk.Tk):
    PAGES = [("Dashboard", DashboardPage), ("Add Income", AddIncomePage), ("Add Expense", AddExpensePage),
             ("Transactions", TransactionsPage), ("Reports & Charts", ReportsPage),
             ("Budget", BudgetPage), ("Export Report", ExportPage)]

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.symbol = manager.currency_symbol
        self.title("Personal Expense Tracker")
        self.geometry("1200x740")
        self.minsize(1050, 680)
        self.configure(bg=BG)
        configure_styles(self)

        # Sidebar
        sidebar = tk.Frame(self, bg=SIDEBAR, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="Expense Tracker", font=(FONT, 17, "bold"), bg=SIDEBAR, fg="white").pack(
            anchor="w", padx=22, pady=(28, 2))
        tk.Label(sidebar, text="Personal finance manager", font=(FONT, 9), bg=SIDEBAR, fg="#94a3b8").pack(
            anchor="w", padx=22, pady=(0, 24))
        self.nav_buttons = {}
        for name, _ in self.PAGES:
            button = tk.Button(sidebar, text=name, anchor="w", font=(FONT, 11), bg=SIDEBAR, fg="white",
                               activebackground=SIDEBAR_HOVER, activeforeground="white", relief="flat", bd=0,
                               padx=22, pady=12, cursor="hand2", command=lambda n=name: self.show_page(n))
            button.pack(fill="x")
            self.nav_buttons[name] = button
        tk.Label(sidebar, text="Data saved in /data (JSON)", font=(FONT, 8), bg=SIDEBAR, fg="#64748b").pack(
            side="bottom", pady=14)

        # Content area where pages are stacked on top of each other
        container = ttk.Frame(self)
        container.pack(side="right", fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.pages = {}
        for name, page_class in self.PAGES:
            page = page_class(container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

        self.show_page("Dashboard")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        if manager.storage.warnings:
            self.after(400, lambda: messagebox.showwarning("Data File Recovered", "\n\n".join(manager.storage.warnings)))

    def show_page(self, name):
        for button_name, button in self.nav_buttons.items():
            button.config(bg=SIDEBAR_ACTIVE if button_name == name else SIDEBAR)
        page = self.pages[name]
        page.refresh()
        page.tkraise()

    def show_budget_alert(self, month):
        """Pop up a warning when spending reaches 80% of the budget or goes over it."""
        status = self.manager.get_budget_status(month)
        if status["level"] == "exceeded":
            messagebox.showwarning("Budget Exceeded", status["message"])
        elif status["level"] == "warning":
            messagebox.showwarning("Budget Warning", status["message"])

    def on_close(self):
        self.quit()
        self.destroy()


def main():
    try:
        manager = ExpenseManager()
    except StorageError as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Startup Error", f"The application could not start.\n\n{error}")
        root.destroy()
        return
    ExpenseTrackerApp(manager).mainloop()


if __name__ == "__main__":
    main()
