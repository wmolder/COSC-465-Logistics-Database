PRAGMA foreign_keys = ON;
.mode box

INSERT INTO Items VALUES 
('minecraft:stone_bricks', 'Building Material', 'Stone'),
('minecraft:iron_ingot', 'Material', 'Refined'),
('minecraft:gold_ingot', 'Material', 'Refined'),
('minecraft:diamond', 'Material', 'Gem'),
('minecraft:oak_plank', 'Building Material', 'Wood'),
('minecraft:emerald', 'Material', 'Gem'),
('minecraft:raw_gold', 'Material', 'Raw'),
('minecraft:raw_copper', 'Material', 'Raw'),
('minecraft:raw_iron','Material', 'Raw'),
('minecraft:cobblestone', 'Building Material', 'Stone'),
('minecraft:stone','Building Material', 'Stone'),
('minecraft:deepslate','Building Material', 'Stone'),
('minecraft:deepslate_bricks','Building Material', 'Stone'),
('minecraft:dirt', 'Building Material', 'Filler');

INSERT INTO Warehouses (WarehouseName, NumberOfShelves, NumberOfRows) VALUES
('Northern Complex', 6, 5),
('Southern Buffer', 3, 2),
('Eastern Factory', 9, 3),
('Western Port', 1000, 10),
('Metal Mine', 12, 4),
('Oak Logging Corp', 243, 18),
('Spruce Logging Corp', 243, 18),
('Quartz Quarry', 666, 13),
('Farland Keep', 60, 20);

INSERT INTO Shelves (ShelfRow, WarehouseID, Type, Subtype) VALUES
(3, 1, 'Building Material', 'Stone'),
(3, 1, 'Building Material', 'Wood'),
(3, 3, 'Material', 'Raw'),
(4, 2, 'Material', 'Gem'),
(1, 5, 'Material', 'Refined'),
(1, 5, 'Material', 'Refined');

INSERT INTO Shelves (ShelfRow, WarehouseID, Type, Subtype) VALUES
(1, 9, 'Material', 'Gem'),
(1, 9, 'Material', 'Refined'),
(1, 9, 'Material', 'Raw'),
(2, 9, 'Building Material', 'Wood'),
(2, 9, 'Building Material', 'Stone'),
(2, 9, 'Building Material', 'Filler');

INSERT INTO StoredItems (ItemID, ShelfID, Amount) VALUES
('minecraft:stone_bricks', 1, 360),
('minecraft:diamond', 4, 64),
('minecraft:oak_plank', 2, 542),
('minecraft:emerald', 4, 10);

INSERT INTO StoredItems (ItemID, ShelfID, Amount)
SELECT ItemID, 6, 100
FROM Items
WHERE Type IS 'Material' AND Subtype IS 'Refined';

INSERT INTO StoredItems (ItemID, ShelfID, Amount)
SELECT ItemID, 3, 100
FROM Items
WHERE Type IS 'Material' AND Subtype IS 'Raw';

INSERT INTO StoredItems (ItemID, ShelfID, Amount)
SELECT ItemID, 4, 100
FROM Items
WHERE Type IS 'Building Material' AND Subtype IS 'Wood';

INSERT INTO StoredItems (ItemID, ShelfID, Amount)
SELECT ItemID, 11, 128
FROM Items
WHERE Type IS 'Building Material' AND Subtype IS 'Stone';

-- Factories
INSERT INTO Factory (WarehouseID, FactoryName)
SELECT WarehouseID, WarehouseName
FROM Warehouses
WHERE WarehouseName IN ('Oak Logging Corp', 'Metal Mine', 'Spruce Logging Corp', 'Quartz Quarry');


-- Production Map
INSERT INTO ProductionMap (FactoryID, ItemID, Speed)
SELECT FactoryID, 'minecraft:oak_plank', 100
FROM Factory
WHERE FactoryName IS 'Oak Logging Corp';

INSERT INTO ProductionMap (FactoryID, ItemID, Speed)
SELECT FactoryID, ItemID, 70 
FROM Items 
LEFT JOIN Factory
	ON FactoryName IS 'Metal Mine'
WHERE Type = 'Material' AND Subtype = 'Raw';

-- Stone is a byproduct of mining
INSERT INTO ProductionMap (FactoryID, ItemID, Speed)
SELECT FactoryID, ItemID, 20
FROM Factory
LEFT JOIN Items
	ON Items.ItemID IN (	'minecraft:cobblestone', 
					'minecraft:stone', 
					'minecraft:deepslate',
					'minecraft:deepslate_bricks')
WHERE FactoryName IS 'Metal Mine';


--SELECT * FROM Items ORDER BY Type ASC;
--SELECT * FROM Warehouses;
--SELECT * FROM Shelves;
SELECT * FROM StoredItems;
--SELECT * FROM Factory;
--SELECT * FROM ProductionMap;

SELECT * FROM AllWarehouses;
--SELECT * FROM Production;
