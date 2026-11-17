PRAGMA foreign_keys = ON;
.mode box

--1. Filtering and Sorting
-- This tells show all the factories that produce raw iron and ranks them by speed.
SELECT * 
FROM ProductionMap
WHERE ItemID = 'minecraft:raw_iron'
ORDER BY Speed ASC;

--2. INNER JOIN
-- This shows all the shelves and what warehouse they belong to.
SELECT Warehouses.WarehouseName, ShelfID
FROM Warehouses
INNER JOIN Shelves
    On Shelves.WarehouseID = Warehouses.WarehouseID;

--3. LEFT JOIN
-- This shows what shelves are in what warehouses and includes warehouses with no shelves.
SELECT Warehouses.WarehouseName, ShelfID
FROM Warehouses
LEFT JOIN Shelves
    On Shelves.WarehouseID = Warehouses.WarehouseID;

--4. Three-Table Join
-- This shows what items are stored in what warehouses and where.
SELECT Warehouses.WarehouseName, Shelves.ShelfID, StoredItems.ItemID
FROM Warehouses
LEFT JOIN Shelves
    ON Shelves.ShelfID = Warehouses.WarehouseID
INNER JOIN StoredItems
    ON Shelves.ShelfID = StoredItems.ShelfID;

--5. Aggregate Query
-- This shows how many shelves have been added to each warehouse
-- and what the maximum number of shelves for each warehouse is.
SELECT WarehouseName AS 'Warehouse Name', 
    COUNT(Shelves.ShelfID) AS 'Current Shelf Count', 
    Warehouses.NumberOfShelves AS 'MAX Shelf Count'
FROM Warehouses
LEFT JOIN Shelves
    ON Warehouses.WarehouseID = Shelves.WarehouseID
GROUP BY Warehouses.WarehouseID;

--6. GROUP BY and HAVING
-- Shows the total amount of each item across the entire network.
SELECT StoredItems.ItemID, SUM(StoredItems.Amount) AS 'Amount'
FROM StoredItems
GROUP BY StoredItems.ItemID
HAVING SUM(StoredItems.Amount) > 0;

--7. Subquery
-- Gets all the items produced by Metal Mine.
SELECT ItemID, Speed AS 'Current Speed'
FROM ProductionMap
WHERE FactoryID =
(
    SELECT FactoryID 
    FROM Factory
    Where FactoryName = 'Metal Mine'
);

--8. Set Operation
-- This shows what factories are currently making items.
SELECT FactoryName
FROM Factory
WHERE FactoryID in
(
    SELECT FactoryID FROM Factory
    INTERSECT
    SELECT FactoryID FROM ProductionMap
);

--9. View
-- This tells me how fast o
SELECT ItemID, [Units Per Hour]
FROM Production
WHERE ItemID = 'minecraft:oak_plank';