"""Interactive console application for the Logistics SQLite database."""

from __future__ import annotations

import argparse
import shlex
import sqlite3
import sys
from pathlib import Path


DEFAULT_DATABASE = Path(__file__).with_name("Logistics.db")
MAX_CELL_WIDTH = 40


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def print_rows_from_rows(
    description: tuple[tuple, ...], rows: list[sqlite3.Row]
) -> None:
    headers = [str(column[0]) for column in description]
    values = [
        ["NULL" if value is None else str(value) for value in row]
        for row in rows
    ]
    widths = [
        min(
            MAX_CELL_WIDTH,
            max(
                len(headers[index]),
                *(min(len(row[index]), MAX_CELL_WIDTH) for row in values),
            ),
        )
        for index in range(len(headers))
    ]

    def format_row(row: list[str]) -> str:
        cells = [
            value if len(value) <= MAX_CELL_WIDTH else value[: MAX_CELL_WIDTH - 3] + "..."
            for value in row
        ]
        return " | ".join(
            cells[index].ljust(widths[index]) for index in range(len(headers))
        )

    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in values:
        print(format_row(row))
    print(f"{len(rows)} row(s)")


def print_rows(cursor: sqlite3.Cursor, limit: int | None = None) -> None:
    rows = cursor.fetchmany(limit + 1) if limit is not None else cursor.fetchall()
    has_more = limit is not None and len(rows) > limit
    if has_more:
        rows = rows[:limit]
    if not cursor.description:
        print(f"Done. {cursor.rowcount if cursor.rowcount >= 0 else 0} row(s) affected.")
        return
    print_rows_from_rows(cursor.description, rows)
    if has_more:
        print("Additional rows were omitted by the limit.")


def confirm(prompt: str) -> bool:
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in {"y", "yes"}
    except EOFError:
        return False


class LogisticsConsole:
    def __init__(self, database: Path) -> None:
        self.database = database.resolve()
        self.connection = sqlite3.connect(self.database)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.connection.close()

    def run(self) -> None:
        print(f"Connected to {self.database}")
        print("Type 'help' for commands, or 'quit' to exit.")
        while True:
            try:
                line = input("logistics> ").strip()
            except EOFError:
                print()
                return
            except KeyboardInterrupt:
                print()
                return
            if not line:
                continue
            if line.lower() in {"quit", "exit"}:
                return
            try:
                self.execute_command(line)
            except sqlite3.IntegrityError as error:
                print(f"Database constraint rejected the change: {error}")
            except sqlite3.Error as error:
                print(f"Database operation failed: {error}")
            except (ValueError, IndexError) as error:
                print(f"Invalid input: {error}")

    def execute_command(self, line: str) -> None:
        command, _, arguments = line.partition(" ")
        command = command.lower()
        if command in {"help", "?"}:
            self.show_help()
        elif command == "tables":
            self.show_tables()
        elif command == "schema":
            self.show_schema(arguments.strip() or None)
        elif command == "list":
            self.list_table(arguments)
        elif command == "search":
            self.search_inventory(arguments)
        elif command == "warehouse":
            self.show_warehouse(arguments)
        elif command == "report":
            self.show_report()
        elif command == "production":
            self.show_production(arguments)
        elif command == "query":
            self.run_query(arguments)
        elif command == "sql":
            self.run_sql(arguments)
        elif command == "add":
            self.add_record(arguments)
        elif command == "move":
            self.move_record(arguments)
        elif command == "delete":
            self.delete_record(arguments)
        else:
            print(f"Unknown command: {command}. Type 'help' to see available commands.")

    @staticmethod
    def show_help() -> None:
        print(
            """Commands:
  tables
  schema [TABLE]
  list TABLE [LIMIT]
  search [ITEM_OR_CATEGORY]       browse inventory; optional text filter
  warehouse WAREHOUSE_ID          show shelves and their stored items
  report                          inventory totals and warehouse capacity
  production [FACTORY_ID]         show factory output rates
  query SELECT_SQL
  sql SQL_STATEMENT              (asks for confirmation before running)
  add warehouse NAME SHELVES ROWS
  add item ITEM_ID TYPE SUBTYPE
  add shelf WAREHOUSE_ID ROW TYPE SUBTYPE
  add inventory ITEM_ID SHELF_ID AMOUNT
  add factory NAME [WAREHOUSE_ID]
  add production FACTORY_ID ITEM_ID UNITS_PER_HOUR
  move inventory ITEM_ID FROM_SHELF TO_SHELF AMOUNT
  move shelf SHELF_ID TO_WAREHOUSE_ID ROW
  delete TABLE PRIMARY_KEY_VALUE (asks for confirmation)
  help
  quit

Use quotes around values containing spaces. For arbitrary inserts, updates,
and other database operations, use 'sql' followed by one SQL statement."""
        )

    def search_inventory(self, arguments: str) -> None:
        term = arguments.strip()
        search = f"%{term}%"
        cursor = self.connection.execute(
            """SELECT i.ItemID, i.Type, i.Subtype, s.ShelfID, w.WarehouseName,
                      si.Amount
               FROM Items AS i
               LEFT JOIN StoredItems AS si ON si.ItemID = i.ItemID
               LEFT JOIN Shelves AS s ON s.ShelfID = si.ShelfID
               LEFT JOIN Warehouses AS w ON w.WarehouseID = s.WarehouseID
               WHERE ? = ''
                  OR i.ItemID LIKE ? COLLATE NOCASE
                  OR i.Type LIKE ? COLLATE NOCASE
                  OR i.Subtype LIKE ? COLLATE NOCASE
               ORDER BY i.ItemID, w.WarehouseName, s.ShelfID""",
            (term, search, search, search),
        )
        print_rows(cursor)

    def show_warehouse(self, arguments: str) -> None:
        parts = shlex.split(arguments)
        if len(parts) != 1:
            raise ValueError("Usage: warehouse WAREHOUSE_ID")
        warehouse_id = self._parse_integer(parts[0], "Warehouse ID", minimum=1)
        cursor = self.connection.execute(
            """SELECT w.WarehouseID, w.WarehouseName, w.NumberOfShelves,
                      w.NumberOfRows, s.ShelfID, s.ShelfRow, s.Type, s.Subtype,
                      si.ItemID, si.Amount
               FROM Warehouses AS w
               LEFT JOIN Shelves AS s ON s.WarehouseID = w.WarehouseID
               LEFT JOIN StoredItems AS si ON si.ShelfID = s.ShelfID
               WHERE w.WarehouseID = ?
               ORDER BY s.ShelfID, si.ItemID""",
            (warehouse_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            print(f"Warehouse {warehouse_id} does not exist.")
            return
        print_rows_from_rows(cursor.description, rows)

    def show_report(self) -> None:
        print("Inventory totals by item and warehouse:")
        cursor = self.connection.execute(
            """SELECT i.ItemID, w.WarehouseName,
                      COALESCE(SUM(si.Amount), 0) AS TotalUnits
               FROM Items AS i
               LEFT JOIN StoredItems AS si ON si.ItemID = i.ItemID
               LEFT JOIN Shelves AS s ON s.ShelfID = si.ShelfID
               LEFT JOIN Warehouses AS w ON w.WarehouseID = s.WarehouseID
               GROUP BY i.ItemID, w.WarehouseID
               ORDER BY i.ItemID, w.WarehouseName"""
        )
        print_rows(cursor)
        print("\nWarehouse shelf capacity:")
        cursor = self.connection.execute(
            """SELECT w.WarehouseName,
                      COUNT(s.ShelfID) AS ShelvesInUse,
                      w.NumberOfShelves AS ShelfCapacity,
                      w.NumberOfRows AS Rows
               FROM Warehouses AS w
               LEFT JOIN Shelves AS s ON s.WarehouseID = w.WarehouseID
               GROUP BY w.WarehouseID
               ORDER BY w.WarehouseName"""
        )
        print_rows(cursor)

    def show_production(self, arguments: str) -> None:
        parts = shlex.split(arguments)
        if len(parts) > 1:
            raise ValueError("Usage: production [FACTORY_ID]")
        factory_id = (
            self._parse_integer(parts[0], "Factory ID", minimum=1) if parts else None
        )
        cursor = self.connection.execute(
            """SELECT f.FactoryName, w.WarehouseName, i.ItemID, i.Type, i.Subtype,
                      pm.Speed AS UnitsPerHour
               FROM Factory AS f
               LEFT JOIN Warehouses AS w ON w.WarehouseID = f.WarehouseID
               INNER JOIN ProductionMap AS pm ON pm.FactoryID = f.FactoryID
               INNER JOIN Items AS i ON i.ItemID = pm.ItemID
               WHERE ? IS NULL OR f.FactoryID = ?
               ORDER BY f.FactoryName, i.ItemID""",
            (factory_id, factory_id),
        )
        print_rows(cursor)

    def show_tables(self) -> None:
        cursor = self.connection.execute(
            """SELECT type, name FROM sqlite_master
               WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
               ORDER BY type, name"""
        )
        print_rows(cursor)

    def show_schema(self, table: str | None) -> None:
        if table is None:
            cursor = self.connection.execute(
                """SELECT sql FROM sqlite_master
                   WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
                   AND sql IS NOT NULL ORDER BY type, name"""
            )
            for row in cursor:
                print(row["sql"] + ";\n")
            return
        row = self.connection.execute(
            """SELECT sql FROM sqlite_master
               WHERE type IN ('table', 'view') AND name = ?""",
            (table,),
        ).fetchone()
        if row is None:
            raise ValueError(f"No table or view named {table!r}.")
        print((row["sql"] or "(schema is not available)") + ";")

    def list_table(self, arguments: str) -> None:
        parts = shlex.split(arguments)
        if not parts or len(parts) > 2:
            raise ValueError("Usage: list TABLE [LIMIT]")
        table = parts[0]
        limit = self._parse_integer(parts[1], "LIMIT", minimum=1) if len(parts) == 2 else 50
        if not self._object_exists(table):
            raise ValueError(f"No table or view named {table!r}.")
        cursor = self.connection.execute(
            f"SELECT * FROM {quote_identifier(table)} LIMIT ?", (limit + 1,)
        )
        print_rows(cursor, limit)

    def run_query(self, sql: str) -> None:
        if not sql.strip():
            raise ValueError("Usage: query SELECT_SQL")
        uri = self.database.as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as read_connection:
            cursor = read_connection.execute(sql)
            print_rows(cursor)

    def run_sql(self, sql: str) -> None:
        if not sql.strip():
            raise ValueError("Usage: sql SQL_STATEMENT")
        if not confirm("Run this SQL statement?"):
            print("Cancelled.")
            return
        try:
            cursor = self.connection.execute(sql)
            self.connection.commit()
        except sqlite3.Error:
            self.connection.rollback()
            raise
        print_rows(cursor)

    def add_record(self, arguments: str) -> None:
        parts = shlex.split(arguments)
        if not parts:
            raise ValueError("Usage: add warehouse|item|shelf|inventory|factory|production ...")
        kind, *values = parts
        if kind == "warehouse" and len(values) == 3:
            name, shelves, rows = values
            if not name.strip():
                raise ValueError("Warehouse name cannot be empty.")
            shelf_count = self._parse_integer(shelves, "Shelf capacity", minimum=1)
            row_count = self._parse_integer(rows, "Row count", minimum=1)
            self.connection.execute(
                "INSERT INTO Warehouses (WarehouseName, NumberOfShelves, NumberOfRows) "
                "VALUES (?, ?, ?)",
                (name, shelf_count, row_count),
            )
        elif kind == "item" and len(values) == 3:
            if any(not value.strip() for value in values):
                raise ValueError("Item ID, type, and subtype cannot be empty.")
            self.connection.execute(
                "INSERT INTO Items (ItemID, Type, Subtype) VALUES (?, ?, ?)", values
            )
        elif kind == "shelf" and len(values) == 4:
            warehouse_id, row, shelf_type, subtype = values
            warehouse_id = self._parse_integer(warehouse_id, "Warehouse ID", minimum=1)
            row = self._parse_integer(row, "Shelf row", minimum=1)
            if not shelf_type.strip() or not subtype.strip():
                raise ValueError("Shelf type and subtype cannot be empty.")
            self._validate_shelf_location(warehouse_id, row)
            self.connection.execute(
                "INSERT INTO Shelves (WarehouseID, ShelfRow, Type, Subtype) "
                "VALUES (?, ?, ?, ?)",
                (warehouse_id, row, shelf_type, subtype),
            )
        elif kind == "inventory" and len(values) == 3:
            item_id, shelf_id, amount = values
            if not item_id.strip():
                raise ValueError("Item ID cannot be empty.")
            shelf_id = self._parse_integer(shelf_id, "Shelf ID", minimum=1)
            amount = self._parse_integer(amount, "Amount", minimum=1)
            self.connection.execute(
                "INSERT INTO StoredItems (ItemID, ShelfID, Amount) VALUES (?, ?, ?)",
                (item_id, shelf_id, amount),
            )
        elif kind == "factory" and len(values) in {1, 2}:
            name = values[0]
            if not name.strip():
                raise ValueError("Factory name cannot be empty.")
            warehouse_id = (
                self._parse_integer(values[1], "Warehouse ID", minimum=1)
                if len(values) == 2
                else None
            )
            self.connection.execute(
                "INSERT INTO Factory (FactoryName, WarehouseID) VALUES (?, ?)",
                (name, warehouse_id),
            )
        elif kind == "production" and len(values) == 3:
            factory_id, item_id, speed = values
            factory_id = self._parse_integer(factory_id, "Factory ID", minimum=1)
            if not item_id.strip():
                raise ValueError("Item ID cannot be empty.")
            try:
                speed = float(speed)
            except ValueError as error:
                raise ValueError("Units per hour must be a positive number.") from error
            if speed <= 0:
                raise ValueError("Units per hour must be a positive number.")
            self.connection.execute(
                "INSERT INTO ProductionMap (FactoryID, ItemID, Speed) VALUES (?, ?, ?)",
                (factory_id, item_id, speed),
            )
        else:
            raise ValueError("Invalid arguments. Type 'help' to see add command formats.")
        self.connection.commit()
        print(f"Added {kind} record.")

    def move_record(self, arguments: str) -> None:
        parts = shlex.split(arguments)
        if not parts:
            raise ValueError("Usage: move inventory|shelf ...")
        kind, *values = parts
        if kind == "shelf" and len(values) == 3:
            shelf_id = self._parse_integer(values[0], "Shelf ID", minimum=1)
            warehouse_id = self._parse_integer(values[1], "Warehouse ID", minimum=1)
            row = self._parse_integer(values[2], "Shelf row", minimum=1)
            self._validate_shelf_location(warehouse_id, row, exclude_shelf_id=shelf_id)
            cursor = self.connection.execute(
                "UPDATE Shelves SET WarehouseID = ?, ShelfRow = ? WHERE ShelfID = ?",
                (warehouse_id, row, shelf_id),
            )
            self.connection.commit()
            if cursor.rowcount == 0:
                print(f"Shelf {shelf_id} does not exist.")
            else:
                print(f"Moved shelf {shelf_id} to warehouse {warehouse_id}, row {row}.")
            return
        if kind != "inventory" or len(values) != 4:
            raise ValueError("Usage: move inventory ITEM_ID FROM_SHELF TO_SHELF AMOUNT")

        item_id, from_shelf, to_shelf, amount = values
        source_id = self._parse_integer(from_shelf, "Source shelf ID", minimum=1)
        target_id = self._parse_integer(to_shelf, "Destination shelf ID", minimum=1)
        amount_to_move = self._parse_integer(amount, "Amount", minimum=1)
        if source_id == target_id:
            raise ValueError("Source and destination shelves must be different.")
        if self.connection.execute(
            "SELECT 1 FROM Shelves WHERE ShelfID = ?", (target_id,)
        ).fetchone() is None:
            raise ValueError(f"Destination shelf {target_id} does not exist.")

        sources = self.connection.execute(
            """SELECT CollectionID, Amount FROM StoredItems
               WHERE ItemID = ? AND ShelfID = ? ORDER BY CollectionID""",
            (item_id, source_id),
        ).fetchall()
        available = sum(row["Amount"] for row in sources)
        if amount_to_move > available:
            raise ValueError(
                f"Only {available} unit(s) of {item_id!r} are available on shelf {source_id}."
            )

        remaining = amount_to_move
        with self.connection:
            for source in sources:
                if remaining == 0:
                    break
                moved = min(source["Amount"], remaining)
                leftover = source["Amount"] - moved
                if leftover:
                    self.connection.execute(
                        "UPDATE StoredItems SET Amount = ? WHERE CollectionID = ?",
                        (leftover, source["CollectionID"]),
                    )
                else:
                    self.connection.execute(
                        "DELETE FROM StoredItems WHERE CollectionID = ?",
                        (source["CollectionID"],),
                    )
                remaining -= moved

            destination = self.connection.execute(
                """SELECT CollectionID, Amount FROM StoredItems
                   WHERE ItemID = ? AND ShelfID = ? ORDER BY CollectionID LIMIT 1""",
                (item_id, target_id),
            ).fetchone()
            if destination is None:
                self.connection.execute(
                    "INSERT INTO StoredItems (ItemID, ShelfID, Amount) VALUES (?, ?, ?)",
                    (item_id, target_id, amount_to_move),
                )
            else:
                self.connection.execute(
                    "UPDATE StoredItems SET Amount = ? WHERE CollectionID = ?",
                    (destination["Amount"] + amount_to_move, destination["CollectionID"]),
                )
        print(
            f"Moved {amount_to_move} unit(s) of {item_id} "
            f"from shelf {source_id} to shelf {target_id}."
        )

    def delete_record(self, arguments: str) -> None:
        parts = shlex.split(arguments)
        if len(parts) != 2:
            raise ValueError("Usage: delete TABLE PRIMARY_KEY_VALUE")
        table, value = parts
        if not self._object_exists(table, object_type="table"):
            raise ValueError(f"No table named {table!r}.")
        columns = self.connection.execute(
            f"PRAGMA table_info({quote_identifier(table)})"
        ).fetchall()
        primary_keys = [column for column in columns if column["pk"]]
        if len(primary_keys) != 1:
            raise ValueError("This table does not have a single-column primary key; use sql.")
        primary_key = primary_keys[0]
        if "INT" in primary_key["type"].upper():
            value = int(value)
        if not confirm(f"Delete the row in {table} where {primary_key['name']} = {value!r}?"):
            print("Cancelled.")
            return
        cursor = self.connection.execute(
            f"DELETE FROM {quote_identifier(table)} "
            f"WHERE {quote_identifier(primary_key['name'])} = ?",
            (value,),
        )
        self.connection.commit()
        print("Deleted 1 row." if cursor.rowcount else "No matching row found.")

    def _object_exists(self, name: str, object_type: str | None = None) -> bool:
        if object_type is None:
            row = self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name = ? "
                "AND type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'",
                (name,),
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name = ? AND type = ?",
                (name, object_type),
            ).fetchone()
        return row is not None

    def _validate_shelf_location(
        self, warehouse_id: int, row: int, exclude_shelf_id: int | None = None
    ) -> None:
        warehouse = self.connection.execute(
            """SELECT NumberOfShelves, NumberOfRows FROM Warehouses
               WHERE WarehouseID = ?""",
            (warehouse_id,),
        ).fetchone()
        if warehouse is None:
            raise ValueError(f"Warehouse {warehouse_id} does not exist.")
        if warehouse["NumberOfRows"] is not None and row > warehouse["NumberOfRows"]:
            raise ValueError(
                f"Row {row} is outside this warehouse's 1-{warehouse['NumberOfRows']} range."
            )
        if warehouse["NumberOfShelves"] is not None:
            query = "SELECT COUNT(*) FROM Shelves WHERE WarehouseID = ?"
            parameters: tuple[int, ...] = (warehouse_id,)
            if exclude_shelf_id is not None:
                query += " AND ShelfID != ?"
                parameters += (exclude_shelf_id,)
            count = self.connection.execute(query, parameters).fetchone()[0]
            if count >= warehouse["NumberOfShelves"]:
                raise ValueError(f"Warehouse {warehouse_id} has no shelf capacity left.")

    @staticmethod
    def _parse_integer(value: str, label: str, minimum: int | None = None) -> int:
        try:
            number = int(value)
        except ValueError as error:
            raise ValueError(f"{label} must be a whole number.") from error
        if minimum is not None and number < minimum:
            raise ValueError(f"{label} must be at least {minimum}.")
        return number


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path (default: {DEFAULT_DATABASE})",
    )
    args = parser.parse_args()
    if not args.db.is_file():
        print(f"Database file not found: {args.db}", file=sys.stderr)
        return 1
    try:
        console = LogisticsConsole(args.db)
    except sqlite3.Error as error:
        print(f"Could not open database: {error}", file=sys.stderr)
        return 1
    try:
        console.run()
    finally:
        console.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())