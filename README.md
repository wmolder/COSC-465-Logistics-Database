# DBMS
SQLite was used for this database.

# Software
1. The scripts were written in Powershell so Powershell is needed. However, both scripts are short and
   easily translatable to bash or another shell.
   
# Scripts
1. SQLcreation.ps1: Creates the tables, views, and index.
2. SQLinitialization.ps1: Initializes the database with data. Also calls
                       SQLcreation.ps1
# Setup
The default data was created using minecraft items and their ids, but the system should be
generalized enough to allow for any set of items with unique ids.
1. Run SQLinitialization.ps1 with the command: & SQLinitialization.ps1
    If there are no problems, it should end with "Done:".
2. Use the database, it is now setup.

## Console application

The application is written in Python 3 and uses only the Python standard
library (`sqlite3`, `argparse`, `shlex`, and `pathlib`); no package installation
is needed. The SQLite database must first be set up using the scripts above.

Start the application from this folder in PowerShell:

```powershell
python .\application.py
```

By default, it opens `Logistics.db` next to `application.py`. To use a
different database file, pass its path:

```powershell
python .\application.py --db .\Logistics.db
```

At the `logistics>` prompt, type `help` for all commands. The six required
operations are available without writing SQL:

1. **Search/browse inventory:** `search` or `search stone`
2. **Display related data:** `warehouse 1` shows warehouse, shelf, and inventory
   information joined from related tables.
3. **Add data:** for example, `add item minecraft:copper_ingot Material Refined`
4. **Update data:** `move inventory minecraft:diamond 4 7 2` transfers two
   units between shelves as one transaction.
5. **Summary/report:** `report` displays inventory totals and warehouse shelf
   capacity.
6. **Additional operation:** `production` (or `production 1`) displays factory
   output rates and the items produced.

Other useful commands include `tables`, `schema`, `list`, `add warehouse`,
`add shelf`, `add inventory`, `add factory`, `add production`, `move shelf`,
and `delete`. Input values are validated, foreign-key constraints are enabled,
and database errors are reported in the console. Optional `query` and `sql`
commands are available for direct database work; `sql` requires confirmation.

# Views
2 views were created: one holds all of the shelves of a warehouse and groups them by warehouse,
the second shows what factories produce what items, and at what speed.

# Indices
There is currently 1 index, which is used to search shelves by the type of items they hold.
                     
    