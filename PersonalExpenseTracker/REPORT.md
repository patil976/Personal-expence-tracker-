# Mini-Project Report

## Personal Expense Tracker Using Python and File Handling

**Student Name:** ____________________  **Roll No.:** ____________  
**Course / Department:** ____________________  **Guide:** ____________________  
**Academic Year:** 2026-27

---

## 1. Abstract
This project is a desktop application, the *Personal Expense Tracker*, built with Python 3, Tkinter and
Matplotlib. It helps students and individuals record daily income and expenses, monitor spending habits,
set a monthly budget and view financial reports. All data is stored permanently in JSON files using
Python's file handling (`open()`, `json.load()`, `json.dump()`), so no database or internet connection is
required. Safe-writing techniques (temporary file followed by atomic replacement) and recovery from
missing or corrupted files protect the user's data. The code is separated into GUI, business-logic and
file-handling layers, which keeps it easy to understand, test and extend.

## 2. Introduction
Many people do not know where their money goes each month. Paper notes are easily lost and
spreadsheets need manual formulas. A simple, offline tool that records transactions, calculates the balance,
warns about overspending and draws charts can build better financial habits.

The application demonstrates key Python concepts: file handling, JSON serialisation, exception handling,
classes and functions, modular programming, GUI programming with event handling, date handling and data
visualisation.

## 3. Objectives
1. Record income and expenses with validated inputs.
2. Store all data permanently in JSON files without using any database.
3. Calculate balance as `Balance = Total Income - Total Expenses`.
4. Allow viewing, searching, filtering, editing and deleting of transactions.
5. Generate monthly and category-wise reports.
6. Visualise spending with pie, bar and line charts.
7. Let the user set a monthly budget and warn at 80% usage and when it is exceeded.
8. Export reports to CSV.
9. Handle missing, empty and corrupted files without crashing.
10. Provide a clean, user-friendly interface suitable for demonstration.

## 4. Hardware and Software Requirements
**Hardware (minimum)**

| Item | Requirement |
|---|---|
| Processor | Dual-core, 1.5 GHz or faster |
| RAM | 2 GB (4 GB recommended) |
| Disk space | 200 MB free (Python + Matplotlib) |
| Display | 1280 x 720 or higher |

**Software**

| Item | Requirement |
|---|---|
| Operating system | Windows 10/11 (also works on Linux/macOS) |
| Language | Python 3.9 or later |
| GUI | Tkinter / ttk (bundled with Python) |
| Charts | Matplotlib (`pip install matplotlib`) |
| Storage | JSON files via `json` and `open()` |
| Editor | Visual Studio Code with the Python extension |

## 5. System Design

### 5.1 Architecture (three layers)
```
+--------------------------------------------------------------+
|  Presentation layer   main.py (Tkinter) + charts.py (Matplotlib) |
+-------------------------------+------------------------------+
                                |
+-------------------------------v------------------------------+
|  Logic layer    expense_manager.py  (validation, rules, budgets) |
|                 reports.py          (totals, summaries, CSV)     |
+-------------------------------+------------------------------+
                                |
+-------------------------------v------------------------------+
|  Data layer     storage.py  ->  data/*.json                      |
+--------------------------------------------------------------+
```
The GUI never touches files directly; it calls `ExpenseManager`, which validates input and calls
`JSONStorage`.

### 5.2 Modules

| File | Responsibility |
|---|---|
| `main.py` | Windows, sidebar, pages, dialogs, message boxes |
| `expense_manager.py` | Input validation, add/edit/delete/search, budget status, export |
| `reports.py` | Pure functions: totals, monthly summary, category totals, daily summary, CSV writer |
| `charts.py` | Pie, bar and line chart drawing and Tkinter embedding |
| `storage.py` | Create files, read/write JSON, atomic save, recovery, unique IDs |

### 5.3 Data design

**transactions.json** (list of records)

| Field | Type | Description |
|---|---|---|
| id | string | Unique ID such as `TXN0007` |
| date | string | `YYYY-MM-DD` |
| type | string | `income` or `expense` |
| category | string | Income source or expense category |
| amount | number | Positive, 2 decimals |
| payment_method | string | Cash / UPI / Card / Bank Transfer (`-` for income) |
| description | string | Notes (max 200 characters) |

**budgets.json**: `{"YYYY-MM": budget_amount}` &nbsp;&nbsp; **settings.json**: `{"currency_symbol": "₹"}`

### 5.4 Data flow (adding an expense)
```
User form -> main.py (AddExpensePage.save)
          -> ExpenseManager.add_expense()  [validate amount, date, category, payment]
          -> JSONStorage.add_transaction() [generate ID, check structure]
          -> _write_json()                 [write temp file -> os.replace()]
          -> data/transactions.json
          -> GUI shows confirmation + budget alert if needed
```

### 5.5 Screens
Sidebar navigation with seven screens: Dashboard, Add Income, Add Expense, Transactions,
Reports & Charts, Budget, Export Report. A consistent colour scheme is used (dark blue sidebar,
light grey background, white cards, green for income, red for expenses, amber for warnings).

## 6. Algorithms

**6.1 Balance calculation**
```
total_income  = sum(amount) of all records where type == "income"
total_expense = sum(amount) of all records where type == "expense"
balance       = total_income - total_expense
```

**6.2 Unique transaction ID**
```
highest = 0
for each record: if id matches "TXN" + digits: highest = max(highest, number)
new_id = "TXN" + (highest + 1) padded to 4 digits
```

**6.3 Safe file writing**
```
1. Write the data to "<file>.tmp" using json.dump()
2. Flush and fsync the temporary file
3. os.replace(temp, original)   # atomic: original is never half-written
4. If anything fails, delete the temp file and report an error
```

**6.4 Reading with recovery**
```
if file missing or empty      -> create it with default content
try json.load()
   on JSONDecodeError or wrong data type -> rename the file to *.corrupted-<time>.json,
                                            create a fresh file, warn the user
```

**6.5 Budget status**
```
percent = spent / budget * 100
if spent > budget      -> level "exceeded"
elif percent >= 80     -> level "warning"
else                   -> level "ok"
(no budget set -> level "none")
```

**6.6 Category-wise totals**
```
totals = {}
for each expense record in the selected period: totals[category] += amount
sort totals by amount (descending); the first entry is the highest spending category
```

**6.7 Validation**
Amount: not empty, numeric, finite, `> 0`, `<= 100,000,000`. Date: parsed with
`datetime.strptime(text, "%Y-%m-%d")`, so impossible dates such as `2026-02-30` are rejected.
Category and payment method must be chosen from the allowed lists.

## 7. Implementation

### 7.1 Technologies
Python 3, `tkinter`/`ttk` for the GUI, `json` and `open()` for storage, `datetime` and `calendar` for
dates, `csv` for export, and `matplotlib` for charts (the only external library).

### 7.2 Key implementation points
- **Context managers:** every file operation uses `with open(...)`.
- **Exception handling:** `FileNotFoundError`, `json.JSONDecodeError`, `UnicodeDecodeError`, `OSError`
  are handled in `storage.py`; user mistakes raise `ValidationError`, which the GUI shows in a message box.
- **Separation of concerns:** only `storage.py` opens JSON files; only `main.py` imports Tkinter.
- **Reusable GUI:** one `TransactionForm` class is used by Add Income, Add Expense and the Edit dialog;
  `create_table()` builds every `ttk.Treeview`.
- **Charts from stored data:** `charts.py` receives data computed from the JSON records; it never uses
  hard-coded values. It works with a Matplotlib `Figure` embedded in Tkinter using `FigureCanvasTkAgg`.
- **Persistence:** nothing is kept only in memory; each screen re-reads the files when it is opened.

### 7.3 Execution steps
```
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 8. Testing

Automated tests (`python -m unittest discover -s tests -v`) cover the logic layer; GUI scenarios are
verified manually.

| # | Test case | Input | Expected result | Result |
|---|---|---|---|---|
| 1 | Add income | 5000, Salary, 2026-10-01 | Record `TXN0001` saved | Pass |
| 2 | Add expense | 250.50, Food, UPI | Saved, category/payment normalised | Pass |
| 3 | Persistence | Close and reopen | Records still present | Pass |
| 4 | Edit / delete | Change amount; delete record | File updated; deleting again raises not-found | Pass |
| 5 | Balance | Income 12,500.50; expense 1,200.25 | Balance 11,300.25 | Pass |
| 6 | Reports | Month 2026-10 test data | Correct totals, highest category, daily rows | Pass |
| 7 | Budget warnings | Budget 5000 / 4000 / 3000 vs spent 3200 | ok / warning (80%) / exceeded | Pass |
| 8 | CSV export | Month and all-time export | Summary, budget and transaction rows present | Pass |
| 9 | Missing / empty / corrupted JSON | Delete, empty or damage file | Recreated; corrupted file backed up | Pass |
| 10 | Invalid input | `abc`, `-50`, `0`, `nan`, `2026-02-30`, `27-10-2026` | `ValidationError`, nothing saved | Pass |
| 11 | Filters | Type, category, keyword, date range | Correct subset; bad range rejected | Pass |
| 12 | Unique IDs | 20 inserts | 20 distinct IDs | Pass |

## 9. Results
With the sample data supplied in `sample_data/`:

| Item | Value |
|---|---|
| Total income | ₹21,000.00 |
| Total expenses | ₹7,519.00 |
| Balance | ₹13,481.00 |
| October expenses | ₹5,269.00 (income ₹13,000.00, savings ₹7,731.00) |
| Highest spending category (Oct) | Shopping, ₹2,500.00 |
| October budget ₹6,000 | 87.8% used, "Warning" displayed |

The application starts correctly on a fresh machine (creating `data/` automatically), retains all
records after restart, displays all three charts from stored data, and exports a CSV file that opens
correctly in Excel.

## 10. Conclusion
The project meets all stated objectives. It shows how a useful, complete desktop application can be built
with only Python's standard library plus Matplotlib. JSON file handling with atomic writes provides
reliable permanent storage without a database. The layered structure keeps the code readable and testable.

## 11. Future Scope
- Recurring transactions (rent, subscriptions) and reminders
- Per-category budgets and savings goals
- Import from bank CSV statements
- Password protection or encryption of the data files
- Multiple user profiles and cloud backup
- Date-picker widget, dark theme and PDF reports
- Packaging as a Windows `.exe` with PyInstaller
- Mobile or web version using the same logic layer

## 12. References
1. Python documentation: `json`, `csv`, `datetime`, `tkinter` - https://docs.python.org/3/
2. Matplotlib documentation - https://matplotlib.org/stable/
3. Tkinter `ttk.Treeview` reference - https://docs.python.org/3/library/tkinter.ttk.html
