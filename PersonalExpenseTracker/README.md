# Personal Expense Tracker (Python + Tkinter + JSON)

A desktop application to record income and expenses, track a monthly budget, view reports and
charts, and export data to CSV. All data is stored permanently in local **JSON files** using
Python file handling. No database and no internet connection are needed.

## Features
- **Dashboard**: total income, total expenses, balance (`Income - Expenses`), this month's expenses, recent transactions, category summary, budget status
- **Add Income / Add Expense** with validation (positive amount, valid date, required fields)
- **Transactions** table (`ttk.Treeview`) with search and filters (keyword, type, category, date range)
- **Edit / Delete** with confirmation, saved to disk immediately
- **Reports**: monthly income, expenses, savings, highest spending category, category totals, daily summary
- **Charts (Matplotlib)**: pie (categories), bar (income vs expenses per month), line (daily spending trend)
- **Budget**: set monthly budget, see spent / remaining / % used, warning at 80% and when exceeded
- **Export** to CSV using the built-in `csv` module
- **Safe file handling**: atomic writes (temp file then replace), auto-created data files, recovery from empty/corrupted JSON

## Folder structure
```
PersonalExpenseTracker/
├── main.py               # Tkinter GUI only
├── expense_manager.py    # Business logic and validation
├── reports.py            # Calculations and CSV export
├── charts.py             # Matplotlib charts
├── storage.py            # All JSON file handling
├── requirements.txt
├── README.md
├── REPORT.md             # Mini-project report
├── data/                 # Created automatically on first run
│   ├── transactions.json
│   ├── budgets.json
│   └── settings.json
├── sample_data/          # Ready-made test data (copy into data/ to try it)
│   ├── transactions.json
│   ├── budgets.json
│   └── settings.json
└── tests/
    └── test_backend.py   # 25 automated tests (no GUI needed)
```

## Install and run on Windows (VS Code)

1. **Install Python 3.9+** from https://www.python.org/downloads/. On the first installer screen tick
   **"Add python.exe to PATH"**. Keep **"tcl/tk and IDLE"** ticked (this provides Tkinter).
2. **Install VS Code** and its **Python** extension (publisher: Microsoft).
3. **Create the folder** `PersonalExpenseTracker` anywhere (for example `C:\Projects\PersonalExpenseTracker`)
   and put all the files from this project in it, keeping the structure above.
4. In VS Code: **File > Open Folder...** and choose `PersonalExpenseTracker`.
5. Open the terminal: **Terminal > New Terminal** and run:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and try again
   (or use Command Prompt and run `venv\Scripts\activate.bat`).
6. Press `Ctrl+Shift+P` > **Python: Select Interpreter** > choose the one inside `.\venv`.
7. Start the app:

```powershell
python main.py
```

The `data` folder and JSON files are created automatically the first time you run it.

### Try it with sample data
Close the app, then copy the three files from `sample_data\` into `data\` (overwrite), and start again:

```powershell
copy sample_data\*.json data\
python main.py
```

### Run the automated tests
```powershell
python -m unittest discover -s tests -v
```

## Data format

`data/transactions.json`
```json
[
    {"id": "TXN0001", "date": "2026-10-01", "type": "income", "category": "Salary",
     "amount": 8000.0, "payment_method": "-", "description": "Monthly salary"},
    {"id": "TXN0002", "date": "2026-10-04", "type": "expense", "category": "Food",
     "amount": 350.0, "payment_method": "Cash", "description": "Lunch"}
]
```
`data/budgets.json` : `{"2026-10": 6000.0}` &nbsp;&nbsp; `data/settings.json` : `{"currency_symbol": "₹"}`
(change the symbol to `$` or any other if you prefer).

## Sample output (using `sample_data`, month 2026-10)

| Screen | What you should see |
|---|---|
| Dashboard | Income ₹21,000.00, Expenses ₹7,519.00, Balance ₹13,481.00, This month ₹5,269.00; budget line says 87.8% used (warning) |
| Reports (2026-10) | Income ₹13,000.00, Expenses ₹5,269.00, Savings ₹7,731.00, Highest spending: Shopping (₹2,500.00) |
| Budget (2026-10) | Budget ₹6,000.00, Spent ₹5,269.00, Remaining ₹731.00, Used 87.8%, amber bar and "Warning" message |
| Pie chart | Slices for Shopping, Food, Travel, Bills, Health with percentages |
| Bar chart | Two months (2026-09, 2026-10), green income bars and red expense bars |

## Manual test cases (GUI)

| # | Scenario | Steps | Expected result |
|---|---|---|---|
| 1 | Add income | Add Income > Amount `5000`, Source `Salary`, today's date > Save | "Income saved" message; appears in Transactions and Dashboard |
| 2 | Add expense | Add Expense > `250`, `Food`, `UPI` > Save | Saved; Dashboard expenses increase by 250 |
| 3 | Persistence | Close the window, run `python main.py` again | All records still present |
| 4 | Edit / delete | Transactions > select row > Edit Selected, change amount > Save; then Delete Selected > Yes | Table updates; JSON file updated immediately |
| 5 | Balance | Check Dashboard | Balance = Total Income - Total Expenses |
| 6 | Reports | Reports & Charts > choose month | Totals, category table, daily table and charts match the data |
| 7 | Budget | Budget > Month `2026-10`, amount `1000` > Save (with higher spending) | "Budget Exceeded" popup; at 80-100% a "Budget Warning" popup |
| 8 | Export | Export Report > choose month > Export to CSV | CSV file opens in Excel with summary and transactions |
| 9 | Missing/empty JSON | Delete or empty `data\transactions.json`, start app | App starts with no records; file recreated |
| 10 | Invalid input | Amount `abc`, `-5`, `0`; date `31-12-2026` or `2026-02-30` | Error popup, nothing saved |

The non-GUI scenarios (1-6, 7-10 logic) are also covered by `tests/test_backend.py`.

## Common errors and solutions

| Error / Problem | Cause | Solution |
|---|---|---|
| `'python' is not recognized...` | Python not on PATH | Reinstall Python and tick "Add python.exe to PATH", or use `py` instead of `python` |
| `ModuleNotFoundError: No module named 'tkinter'` | Tkinter not installed | Re-run the Python installer > Modify > tick "tcl/tk and IDLE" |
| `ModuleNotFoundError: No module named 'matplotlib'` | Dependencies not installed or wrong interpreter | Activate the venv, run `pip install -r requirements.txt`, select the venv interpreter in VS Code |
| `ModuleNotFoundError: No module named 'storage'` | Running from the wrong folder | Open the project folder in VS Code and run `python main.py` from its terminal |
| `...activate.ps1 cannot be loaded because running scripts is disabled` | PowerShell policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| "Data File Recovered" popup at startup | A JSON file was damaged or hand-edited wrongly | A backup named `*.corrupted-<time>.json` was saved in `data`. Fix it manually if you need the old data |
| `Permission denied` when exporting | CSV already open in Excel | Close the file in Excel or choose a new file name |
| Charts are empty | No data for the selected month | Pick a month that has transactions, or load the sample data |
| `₹` shows as `?` | Font/console issue | Change `currency_symbol` in `data/settings.json` to `Rs.` or `$` |
| `Invalid date` error | Wrong format | Type dates as `YYYY-MM-DD`, for example `2026-10-27` |
| `Could not save ...json` | Folder is read-only or locked | Move the project out of protected folders; make sure no other program locks the file |
| Pressing **Run** in VS Code does nothing visible | Wrong file or interpreter | Open `main.py`, make sure the venv interpreter is selected, then Run Python File |
