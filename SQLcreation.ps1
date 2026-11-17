Clear-Host;

Write-Output "DB Creation:";
Get-Content .\schema.sql | sqlite3 .\Logistics.db;
Write-Output "Done:";