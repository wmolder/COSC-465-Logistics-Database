PRAGMA foreign_keys = ON;
.mode box

DROP INDEX IF EXISTS idx_Shelves_Type;
DROP VIEW IF EXISTS AllWarehouses;
DROP VIEW IF EXISTS Production;
DROP TABLE IF EXISTS ProductionMap;
DROP TABLE IF EXISTS Factory;
DROP TABLE IF EXISTS StoredItems;
DROP TABLE IF EXISTS Shelves;
DROP TABLE IF EXISTS Warehouses;
DROP TABLE IF EXISTS Items;

-- Tables
CREATE TABLE Items
(
    ItemID TEXT NOT NULL PRIMARY KEY,
    Type TEXT NOT NULL,
    Subtype TEXT NOT NULL
);

CREATE TABLE Warehouses
(
    WarehouseID INTEGER PRIMARY KEY,
    WarehouseName TEXT NOT NULL,
    NumberOfShelves INTEGER CHECK (NumberOfShelves > 0),
    NumberOfRows INTEGER CHECK (NumberOfRows > 0)
);

CREATE TABLE Shelves
(
    ShelfID INTEGER PRIMARY KEY,
    ShelfRow INTEGER NOT NULL,
    WarehouseID INTEGER,
    Type TEXT NOT NULL,
    Subtype TEXT NOT NULL,

    FOREIGN KEY (WarehouseID) REFERENCES Warehouses(WarehouseID)
);

CREATE TABLE StoredItems
(
    CollectionID INTEGER PRIMARY KEY,
    ItemID INTEGER,
    ShelfID INTEGER,
    Amount INTEGER NOT NULL CHECK (Amount > 0),

    FOREIGN KEY (ItemID) REFERENCES Items(ItemID),
    FOREIGN KEY (ShelfID) REFERENCES Shelves(ShelfID)
);

CREATE TABLE Factory
(
    FactoryID INTEGER PRIMARY KEY,
    WarehouseID INTEGER UNIQUE,

    FactoryName TEXT NOT NULL UNIQUE,

    FOREIGN KEY (WarehouseID) REFERENCES Warehouses(WarehouseID)
);

CREATE TABLE ProductionMap
(
    FactoryID INTEGER,
    ItemID TEXT,
    Speed REAL NOT NULL CHECK(Speed > 0),

    FOREIGN KEY (FactoryID) REFERENCES Factory(FactoryID),
    FOREIGN KEY (ItemID) REFERENCES Items(ItemID),
    PRIMARY KEY (FactoryID, ItemID)
);

-- VIEWS
CREATE VIEW AllWarehouses AS
SELECT WarehouseName AS 'Warehouse', ShelfID, Type, Subtype
FROM Shelves 
LEFT JOIN Warehouses
    ON Warehouses.WarehouseID = Shelves.WarehouseID
ORDER BY Warehouses.WarehouseID ASC;

-- Getting the all the things the factories make.
CREATE VIEW Production AS
SELECT FactoryName AS 'Factory Name', ItemID, Speed AS 'Units Per Hour' FROM Factory
LEFT JOIN ProductionMap 
    ON Factory.FactoryID = ProductionMap.FactoryID
WHERE Speed IS NOT NULL;

-- Indices
CREATE INDEX idx_Shelves_Type
ON Shelves(Type);

