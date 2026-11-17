PRAGMA foreign_keys = ON;
.mode box

-- This transaction will move all the diamonds from shelf 4 to shelf 7.
BEGIN TRANSACTION;

    -- Copying diamond data from shelf 4 to shelf 7
    INSERT INTO StoredItems(ItemID, ShelfID, Amount)
    SELECT ItemID, 7, Amount
    FROM StoredItems
    WHERE ShelfID = 4 AND ItemID = 'minecraft:diamond';

    -- Removing the diamonds from shelf 4
    DELETE FROM StoredItems
    WHERE ShelfID = 4 AND ItemID = 'minecraft:diamond';


COMMIT TRANSACTION;