"""
storage.py - File-handling layer (no GUI, no business rules).

Everything that touches the disk lives here:
  * creating the data folder and JSON files on first run
  * reading with json.load() and writing with json.dump()
  * safe (atomic) writes: write to a temp file, then replace the original
  * recovery from missing, empty or corrupted JSON files
  * add / update / delete operations for transactions and budgets
"""

import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"

DEFAULT_SETTINGS = {
    "app_name": "Personal Expense Tracker",
    "currency_symbol": "\u20b9",  # Rupee sign. Change to "$" in data/settings.json if you like.
}

REQUIRED_FIELDS = ("id", "date", "type", "category", "amount", "payment_method", "description")


class StorageError(Exception):
    """Raised when a file cannot be read, written or updated."""


class RecordNotFoundError(StorageError):
    """Raised when a transaction ID does not exist."""


class JSONStorage:
    """Centralised reading, writing, updating and deleting of JSON records."""

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.transactions_path = self.data_dir / "transactions.json"
        self.budgets_path = self.data_dir / "budgets.json"
        self.settings_path = self.data_dir / "settings.json"
        self.warnings = []  # human-readable notes about recovered files
        self.initialize()

    # ------------------------------------------------------------------
    # Initialisation and low-level helpers
    # ------------------------------------------------------------------
    def initialize(self):
        """Create the data folder and any missing JSON files."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(f"Could not create data folder '{self.data_dir}': {exc}") from exc
        # Reading each file creates/repairs it when needed.
        for path in (self.transactions_path, self.budgets_path, self.settings_path):
            self._read_json(path)

    def _default_for(self, path):
        if path == self.transactions_path:
            return []
        if path == self.budgets_path:
            return {}
        return dict(DEFAULT_SETTINGS)

    def _expected_type(self, path):
        return list if path == self.transactions_path else dict

    def _read_json(self, path):
        """Read a JSON file; create or repair it if it is missing/empty/corrupted."""
        default = self._default_for(path)
        try:
            if os.path.getsize(path) == 0:  # empty file
                self._write_json(path, default)
                return default
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            self._write_json(path, default)
            return default
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._recover_corrupted(path, default)
        except OSError as exc:
            raise StorageError(f"Could not read {path.name}: {exc}") from exc

        if not isinstance(data, self._expected_type(path)):
            return self._recover_corrupted(path, default)
        return data

    def _write_json(self, path, data):
        """Safe write: dump to a temporary file first, then atomically replace the original."""
        temp_path = path.with_name(path.name + ".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, path)
        except (OSError, TypeError, ValueError) as exc:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass
            raise StorageError(f"Could not save {path.name}: {exc}") from exc

    def _recover_corrupted(self, path, default):
        """Keep a backup copy of a damaged file and start again with a clean one."""
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = path.with_name(f"{path.stem}.corrupted-{stamp}{path.suffix}")
        try:
            os.replace(path, backup)
        except OSError as exc:
            raise StorageError(f"{path.name} is corrupted and could not be backed up: {exc}") from exc
        self._write_json(path, default)
        self.warnings.append(
            f"{path.name} was damaged. A backup was saved as '{backup.name}' and a new file was created."
        )
        return default

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------
    def load_transactions(self):
        """Return a list of valid transaction dictionaries (bad entries are skipped)."""
        raw = self._read_json(self.transactions_path)
        return [item for item in raw if self._is_valid_record(item)]

    def save_transactions(self, transactions):
        self._write_json(self.transactions_path, transactions)

    @staticmethod
    def _is_valid_record(record):
        if not isinstance(record, dict):
            return False
        if any(field not in record for field in REQUIRED_FIELDS):
            return False
        if record["type"] not in ("income", "expense"):
            return False
        amount = record["amount"]
        return isinstance(amount, (int, float)) and not isinstance(amount, bool) and amount > 0

    def generate_transaction_id(self, transactions=None):
        """Create the next unique ID, e.g. TXN0001, TXN0002 ..."""
        if transactions is None:
            transactions = self.load_transactions()
        highest = 0
        for item in transactions:
            tx_id = str(item.get("id", ""))
            if tx_id.startswith("TXN") and tx_id[3:].isdigit():
                highest = max(highest, int(tx_id[3:]))
        return f"TXN{highest + 1:04d}"

    def add_transaction(self, record):
        """Assign an ID, validate the structure and append the record to the file."""
        transactions = self._read_json(self.transactions_path)
        transactions_valid = [item for item in transactions if self._is_valid_record(item)]
        new_record = dict(record)
        new_record["id"] = self.generate_transaction_id(transactions_valid)
        if not self._is_valid_record(new_record):
            raise StorageError("Transaction record is incomplete or invalid and was not saved.")
        transactions.append(new_record)
        self.save_transactions(transactions)
        return new_record

    def get_transaction(self, tx_id):
        for item in self.load_transactions():
            if item["id"] == tx_id:
                return item
        raise RecordNotFoundError(f"Transaction '{tx_id}' was not found.")

    def update_transaction(self, tx_id, updated_record):
        """Replace the stored values of an existing transaction (the ID never changes)."""
        transactions = self._read_json(self.transactions_path)
        for index, item in enumerate(transactions):
            if isinstance(item, dict) and item.get("id") == tx_id:
                new_record = dict(updated_record)
                new_record["id"] = tx_id
                if not self._is_valid_record(new_record):
                    raise StorageError("Updated record is incomplete or invalid and was not saved.")
                transactions[index] = new_record
                self.save_transactions(transactions)
                return new_record
        raise RecordNotFoundError(f"Transaction '{tx_id}' was not found.")

    def delete_transaction(self, tx_id):
        transactions = self._read_json(self.transactions_path)
        remaining = [t for t in transactions if not (isinstance(t, dict) and t.get("id") == tx_id)]
        if len(remaining) == len(transactions):
            raise RecordNotFoundError(f"Transaction '{tx_id}' was not found.")
        self.save_transactions(remaining)

    # ------------------------------------------------------------------
    # Budgets  (format: {"2026-10": 15000.0})
    # ------------------------------------------------------------------
    def load_budgets(self):
        raw = self._read_json(self.budgets_path)
        budgets = {}
        for month, amount in raw.items():
            if isinstance(amount, (int, float)) and not isinstance(amount, bool) and amount > 0:
                budgets[str(month)] = float(amount)
        return budgets

    def set_budget(self, month, amount):
        budgets = self.load_budgets()
        budgets[month] = float(amount)
        self._write_json(self.budgets_path, dict(sorted(budgets.items())))

    def get_budget(self, month):
        return self.load_budgets().get(month)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def load_settings(self):
        settings = dict(DEFAULT_SETTINGS)
        settings.update(self._read_json(self.settings_path))
        return settings

    def save_settings(self, settings):
        self._write_json(self.settings_path, settings)
