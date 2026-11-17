Clear-Host;

.\SQLcreation.ps1;
Write-Output "DB Initialization:";
Get-Content .\insert_data.sql | sqlite3 .\Logistics.db;
Write-Output "Done:";