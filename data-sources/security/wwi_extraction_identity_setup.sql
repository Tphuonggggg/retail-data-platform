/*
DBA REVIEW REQUIRED — DO NOT AUTO-EXECUTE
M1B-OD01/03: prepared administrative SQL; NOT approved for execution.
Chạy TOÀN BỘ một batch, không chọn riêng đoạn; không thêm batch separators.
Windows account provisioning, actual names, reviewed artifact hash và
Owner change authorization phải được xác nhận ngoài SQL trước khi mở guard.
Không có OS-account creation, source data/schema/configuration changes.
*/
DECLARE @DbaReviewed bit = 0;
DECLARE @OwnerExecutionAuthorized bit = 0;
DECLARE @WindowsAccountProvisioned bit = 0;
DECLARE @WindowsNonAdminAttested bit = 0;
DECLARE @ExecutionConfirmation nvarchar(80) = N'DO_NOT_EXECUTE';
DECLARE @ChangeReference nvarchar(256) = N'<APPROVED_CHANGE_REFERENCE>';
DECLARE @WindowsPrincipal nvarchar(256) = N'<APPROVED_WINDOWS_PRINCIPAL>';
DECLARE @DatabaseUser nvarchar(256) = N'<APPROVED_DATABASE_USER>';

IF COALESCE(@DbaReviewed, 0) <> 1 OR COALESCE(@OwnerExecutionAuthorized, 0) <> 1
   OR COALESCE(@WindowsAccountProvisioned, 0) <> 1 OR COALESCE(@WindowsNonAdminAttested, 0) <> 1
   OR COALESCE(@ExecutionConfirmation, N'') <> N'EXECUTE_APPROVED_WWI_IDENTITY_SETUP'
    THROW 51100, N'DBA review and separate Owner execution authorization required.', 1;

IF @ChangeReference IS NULL OR LEN(LTRIM(RTRIM(@ChangeReference))) = 0
   OR @ChangeReference LIKE N'%<%' OR @ChangeReference LIKE N'%>%'
    THROW 51101, N'Approved external change reference is required.', 1;

IF @WindowsPrincipal IS NULL OR @DatabaseUser IS NULL
   OR DATALENGTH(@WindowsPrincipal) NOT BETWEEN 2 AND 256
   OR DATALENGTH(@DatabaseUser) NOT BETWEEN 2 AND 256
   OR DATALENGTH(@WindowsPrincipal) <> DATALENGTH(LTRIM(RTRIM(@WindowsPrincipal)))
   OR DATALENGTH(@DatabaseUser) <> DATALENGTH(LTRIM(RTRIM(@DatabaseUser)))
   OR @WindowsPrincipal LIKE N'%<%' OR @WindowsPrincipal LIKE N'%>%'
   OR @DatabaseUser LIKE N'%<%' OR @DatabaseUser LIKE N'%>%'
   OR CHARINDEX(NCHAR(10), @WindowsPrincipal + @DatabaseUser) > 0
   OR CHARINDEX(NCHAR(13), @WindowsPrincipal + @DatabaseUser) > 0
   OR CHARINDEX(NCHAR(9), @WindowsPrincipal + @DatabaseUser) > 0
   OR CHARINDEX(N'\', @WindowsPrincipal) NOT BETWEEN 2 AND LEN(@WindowsPrincipal) - 1
   OR @DatabaseUser IN (N'dbo', N'guest', N'sys', N'INFORMATION_SCHEMA', N'public')
    THROW 51102, N'Replace placeholders with reviewed bounded Windows/user identifiers.', 1;

DECLARE @LoginQuoted nvarchar(258) = QUOTENAME(@WindowsPrincipal);
DECLARE @UserQuoted nvarchar(258) = QUOTENAME(@DatabaseUser);
IF @LoginQuoted IS NULL OR @UserQuoted IS NULL
    THROW 51103, N'Identifier quoting failed.', 1;

IF DB_NAME() <> N'WideWorldImporters'
   OR COALESCE(CONVERT(nvarchar(128), SERVERPROPERTY('MachineName')), N'') <> N'DESKTOP-OBDFK6B'
   OR COALESCE(CONVERT(nvarchar(128), SERVERPROPERTY('InstanceName')), N'') <> N'SQLEXPRESS'
    THROW 51104, N'Source instance/database allowlist mismatch.', 1;
IF @@TRANCOUNT <> 0
    THROW 51105, N'Use a clean dedicated DBA session, no ambient transaction.', 1;

-- New-identity-only package. Reuse requires another reviewed package, not edits here.
IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name = @WindowsPrincipal)
   OR EXISTS (SELECT 1 FROM sys.database_principals WHERE name = @DatabaseUser)
    THROW 51106, N'Principal already exists; stop, do not alter or reuse automatically.', 1;

DECLARE @Allowlist TABLE
(
    SchemaName sysname NOT NULL,
    ObjectName sysname NOT NULL,
    PRIMARY KEY (SchemaName, ObjectName)
);
-- INSERT below populates a local table variable only, not WWI user data.
INSERT INTO @Allowlist (SchemaName, ObjectName) VALUES
(N'Sales', N'Customers'),
(N'Sales', N'Orders'),
(N'Sales', N'OrderLines'),
(N'Sales', N'Invoices'),
(N'Sales', N'InvoiceLines'),
(N'Sales', N'CustomerTransactions'),
(N'Warehouse', N'StockItems'),
(N'Warehouse', N'StockItemHoldings'),
(N'Warehouse', N'StockItemTransactions'),
(N'Sales', N'Customers_Archive'),
(N'Warehouse', N'StockItems_Archive');

IF (SELECT COUNT(*) FROM @Allowlist) <> 11
    THROW 51107, N'Expected exactly eleven approved objects.', 1;
IF EXISTS
(
    SELECT 1 FROM @Allowlist
    WHERE OBJECT_ID(QUOTENAME(SchemaName) + N'.' + QUOTENAME(ObjectName), N'U') IS NULL
)
    THROW 51108, N'Required source object missing or metadata visibility incomplete.', 1;
IF COALESCE((SELECT history_table_id FROM sys.tables WHERE object_id = OBJECT_ID(N'Sales.Customers')), -1)
       <> COALESCE(OBJECT_ID(N'Sales.Customers_Archive', N'U'), -2)
   OR COALESCE((SELECT history_table_id FROM sys.tables WHERE object_id = OBJECT_ID(N'Warehouse.StockItems')), -1)
       <> COALESCE(OBJECT_ID(N'Warehouse.StockItems_Archive', N'U'), -2)
    THROW 51109, N'Current/history binding differs from approved source contract.', 1;

-- No optional metadata grant is included. VIEW DEFINITION needs a separately
-- justified per-object change proposal; do not enable it across the database.
DECLARE @GrantSql nvarchar(max);
SELECT @GrantSql = STRING_AGG(
    CONVERT(nvarchar(max), N'GRANT SELECT ON OBJECT::'
      + QUOTENAME(SchemaName) + N'.' + QUOTENAME(ObjectName)
      + N' TO ' + @UserQuoted + N';'), NCHAR(10))
FROM @Allowlist;

DECLARE @LoginSql nvarchar(max) = N'CREATE LOGIN ' + @LoginQuoted
    + N' FROM WINDOWS WITH DEFAULT_DATABASE = [WideWorldImporters];';
DECLARE @UserSql nvarchar(max) = N'CREATE USER ' + @UserQuoted
    + N' FOR LOGIN ' + @LoginQuoted + N';';
-- Server-scope GRANT requires master; restore the approved database for CONNECT.
-- Context switches stay inside this dynamic batch and the existing transaction.
DECLARE @ConnectSql nvarchar(max) = N'USE [master]; GRANT CONNECT SQL TO ' + @LoginQuoted
    + N'; USE [WideWorldImporters]; GRANT CONNECT TO ' + @UserQuoted + N';';

SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;
    EXEC sys.sp_executesql @LoginSql;
    IF NOT EXISTS
    (
        SELECT 1 FROM sys.server_principals
        WHERE name = @WindowsPrincipal AND type = 'U' AND is_disabled = 0
    )
        THROW 51110, N'Expected a Windows user login, not a group/SQL login.', 1;
    EXEC sys.sp_executesql @UserSql;
    IF NOT EXISTS
    (
        SELECT 1 FROM sys.database_principals
        WHERE name = @DatabaseUser AND type = 'U'
          AND sid = SUSER_SID(@WindowsPrincipal)
    )
        THROW 51111, N'Windows login/database-user SID mapping mismatch.', 1;
    EXEC sys.sp_executesql @ConnectSql;
    EXEC sys.sp_executesql @GrantSql;
    COMMIT TRANSACTION;
    SELECT N'PREPARED_SETUP_APPLIED_NOT_GATE_PASS' AS Outcome,
           @ChangeReference AS ChangeReference;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
-- No role assignment, broad reader/writer/admin grant, source DML, schema change,
-- security fallback, copy/backup/restore or automatic post-commit revocation.
-- A fresh real Windows extraction session and independent verification follow.
