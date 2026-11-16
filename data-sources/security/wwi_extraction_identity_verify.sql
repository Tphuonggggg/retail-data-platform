/*
DBA REVIEW REQUIRED — DO NOT AUTO-EXECUTE
Read-only verification PREPARED, NOT RUN. Không chạy dưới developer/admin
hoặc EXECUTE AS; dùng fresh actual approved Windows extraction logon.
Không DML/DDL/grants, không privileged diagnostic workaround.
Tất cả inputs và external proof references phải được review trước execution.
*/
DECLARE @VerificationAuthorized bit = 0;
DECLARE @DbaWindowsGroupReviewComplete bit = 0;
DECLARE @ClientTlsProofReviewed bit = 0;
DECLARE @NegativeDatabaseExistsAttested bit = 0;
DECLARE @VerificationConfirmation nvarchar(80) = N'DO_NOT_EXECUTE';
DECLARE @VerificationReference nvarchar(256) = N'<APPROVED_VERIFICATION_REFERENCE>';
DECLARE @WindowsPrincipal nvarchar(256) = N'<APPROVED_WINDOWS_PRINCIPAL>';
DECLARE @DatabaseUser nvarchar(256) = N'<APPROVED_DATABASE_USER>';
DECLARE @NegativeDatabase nvarchar(256) = N'<APPROVED_NEGATIVE_DATABASE>';

IF COALESCE(@VerificationAuthorized, 0) <> 1 OR COALESCE(@DbaWindowsGroupReviewComplete, 0) <> 1
   OR COALESCE(@ClientTlsProofReviewed, 0) <> 1 OR COALESCE(@NegativeDatabaseExistsAttested, 0) <> 1
   OR COALESCE(@VerificationConfirmation, N'') <> N'EXECUTE_APPROVED_READ_ONLY_VERIFICATION'
    THROW 51200, N'Separate verification authority and actual external proof required.', 1;
IF @VerificationReference IS NULL OR LEN(LTRIM(RTRIM(@VerificationReference))) = 0
   OR @VerificationReference LIKE N'%<%' OR @VerificationReference LIKE N'%>%'
    THROW 51201, N'Approved verification/evidence reference required.', 1;
IF @WindowsPrincipal IS NULL OR @DatabaseUser IS NULL OR @NegativeDatabase IS NULL
   OR DATALENGTH(@WindowsPrincipal) NOT BETWEEN 2 AND 256
   OR DATALENGTH(@DatabaseUser) NOT BETWEEN 2 AND 256
   OR DATALENGTH(@NegativeDatabase) NOT BETWEEN 2 AND 256
   OR @WindowsPrincipal LIKE N'%<%' OR @WindowsPrincipal LIKE N'%>%'
   OR @DatabaseUser LIKE N'%<%' OR @DatabaseUser LIKE N'%>%'
   OR @NegativeDatabase LIKE N'%<%' OR @NegativeDatabase LIKE N'%>%'
   OR DATALENGTH(@WindowsPrincipal) <> DATALENGTH(LTRIM(RTRIM(@WindowsPrincipal)))
   OR DATALENGTH(@DatabaseUser) <> DATALENGTH(LTRIM(RTRIM(@DatabaseUser)))
   OR DATALENGTH(@NegativeDatabase) <> DATALENGTH(LTRIM(RTRIM(@NegativeDatabase)))
   OR @DatabaseUser IN (N'dbo', N'guest', N'sys', N'INFORMATION_SCHEMA', N'public')
   OR @NegativeDatabase IN (N'master', N'tempdb', N'model', N'msdb', N'WideWorldImporters')
    THROW 51202, N'Provide reviewed principal/user and non-sensitive negative user-database target.', 1;
IF DB_NAME() <> N'WideWorldImporters'
   OR COALESCE(CONVERT(nvarchar(128), SERVERPROPERTY('MachineName')), N'') <> N'DESKTOP-OBDFK6B'
   OR COALESCE(CONVERT(nvarchar(128), SERVERPROPERTY('InstanceName')), N'') <> N'SQLEXPRESS'
    THROW 51203, N'Source allowlist mismatch.', 1;
IF ORIGINAL_LOGIN() <> @WindowsPrincipal OR SUSER_SNAME() <> @WindowsPrincipal
   OR USER_NAME() <> @DatabaseUser
   OR SUSER_SID() IS NULL OR SUSER_SID(@WindowsPrincipal) IS NULL
   OR SUSER_SID() <> SUSER_SID(@WindowsPrincipal)
    THROW 51204, N'Actual login/user mismatch or impersonation; stop.', 1;
IF @@TRANCOUNT <> 0
    THROW 51205, N'Use a fresh verification session without ambient transaction.', 1;
IF COALESCE(IS_SRVROLEMEMBER(N'sysadmin'), 1) <> 0
   OR COALESCE(IS_SRVROLEMEMBER(N'securityadmin'), 1) <> 0
   OR COALESCE(IS_ROLEMEMBER(N'db_owner'), 1) <> 0
   OR COALESCE(IS_ROLEMEMBER(N'db_datawriter'), 1) <> 0
   OR COALESCE(IS_ROLEMEMBER(N'db_ddladmin'), 1) <> 0
   OR COALESCE(IS_ROLEMEMBER(N'db_securityadmin'), 1) <> 0
    THROW 51206, N'Privileged/unknown role context is not extraction verification evidence.', 1;

SELECT N'LP01_IDENTITY' AS CheckId, DB_NAME() AS DatabaseName,
       CONVERT(varchar(64), HASHBYTES('SHA2_256', SUSER_SID()), 2) AS SidSha256,
       CONNECTIONPROPERTY('net_transport') AS NetTransport,
       CONNECTIONPROPERTY('physical_net_transport') AS PhysicalNetTransport,
       CONNECTIONPROPERTY('auth_scheme') AS AuthScheme,
       @VerificationReference AS EvidenceReference;
-- SID fingerprint is not the UTF-8 login-name fingerprint used in M1A/M1B.
-- Non-public fixed/custom role tokens require DBA review; token counts alone
-- cannot audit Windows local-admin/group inheritance outside SQL Server.
SELECT N'LP02_ROLE_TOKENS' AS CheckId,
       (SELECT COUNT(*) FROM sys.login_token
        WHERE type = N'SERVER ROLE' AND name <> N'public') AS UnexpectedServerRoleTokens,
       (SELECT COUNT(*) FROM sys.user_token
        WHERE type = N'DATABASE ROLE' AND name <> N'public') AS UnexpectedDatabaseRoleTokens;

-- Strict review lists, not an automatic gate PASS. Public metadata rights may
-- need individually approved exceptions; do not revoke public rights globally.
SELECT N'LP03_SERVER_EFFECTIVE' AS CheckId, permission_name,
       CASE WHEN permission_name = N'CONNECT SQL' THEN N'EXPECTED'
            ELSE N'DBA_REVIEW_REQUIRED' END AS ReviewStatus
FROM sys.fn_my_permissions(NULL, N'SERVER');
SELECT N'LP03_DATABASE_EFFECTIVE' AS CheckId, permission_name,
       CASE WHEN permission_name = N'CONNECT' THEN N'EXPECTED'
            ELSE N'DBA_REVIEW_REQUIRED' END AS ReviewStatus
FROM sys.fn_my_permissions(NULL, N'DATABASE');

;WITH Allowlist(SchemaName, ObjectName) AS
(
    SELECT v.SchemaName, v.ObjectName FROM (VALUES
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
(N'Warehouse', N'StockItems_Archive')
    ) AS v(SchemaName, ObjectName)
),
ObjectRights AS
(
    SELECT SchemaName, ObjectName,
      OBJECT_ID(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'U') AS ObjectId,
      HAS_PERMS_BY_NAME(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'OBJECT', N'SELECT') AS CanSelect,
      HAS_PERMS_BY_NAME(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'OBJECT', N'INSERT') AS CanInsert,
      HAS_PERMS_BY_NAME(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'OBJECT', N'UPDATE') AS CanUpdate,
      HAS_PERMS_BY_NAME(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'OBJECT', N'DELETE') AS CanDelete,
      HAS_PERMS_BY_NAME(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'OBJECT', N'ALTER') AS CanAlter,
      HAS_PERMS_BY_NAME(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'OBJECT', N'CONTROL') AS CanControl,
      HAS_PERMS_BY_NAME(QUOTENAME(SchemaName)+N'.'+QUOTENAME(ObjectName), N'OBJECT', N'TAKE OWNERSHIP') AS CanOwn
    FROM Allowlist
)
SELECT N'LP04_05_OBJECTS' AS CheckId, *,
       CASE WHEN ObjectId IS NULL OR CanSelect IS NULL OR CanInsert IS NULL
                 OR CanUpdate IS NULL OR CanDelete IS NULL OR CanAlter IS NULL
                 OR CanControl IS NULL OR CanOwn IS NULL THEN N'NOT_VERIFIED'
            WHEN CanSelect = 1 AND CanInsert = 0 AND CanUpdate = 0 AND CanDelete = 0
                 AND CanAlter = 0 AND CanControl = 0 AND CanOwn = 0 THEN N'EXPECTED'
            ELSE N'FAIL' END AS ReviewStatus,
       (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = ObjectId) AS VisibleColumns,
       (SELECT COUNT(*) FROM sys.computed_columns c
        WHERE c.object_id = ObjectId AND c.definition IS NULL) AS HiddenComputedDefinitions,
       (SELECT COUNT(*) FROM sys.default_constraints c
        WHERE c.parent_object_id = ObjectId AND c.definition IS NULL) AS HiddenDefaultDefinitions
FROM ObjectRights;

-- Separate physical-H linkage evidence, not inherited SELECT assurance.
SELECT N'LP07_08_TEMPORAL_BINDING' AS CheckId, t.name AS CurrentTable,
       OBJECT_SCHEMA_NAME(t.history_table_id) AS HistorySchema,
       OBJECT_NAME(t.history_table_id) AS HistoryTable
FROM sys.tables t
WHERE t.object_id IN (OBJECT_ID(N'Sales.Customers'), OBJECT_ID(N'Warehouse.StockItems'));

-- Column-level grants and application-module execution/ownership/Windows-group
-- paths must ALSO be reviewed; zero object predicates are not complete evidence.
-- These SELECTs return own effective subentity rights, not other principals.
SELECT N'Sales.Customers' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Sales.Customers', N'OBJECT');
SELECT N'Sales.Orders' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Sales.Orders', N'OBJECT');
SELECT N'Sales.OrderLines' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Sales.OrderLines', N'OBJECT');
SELECT N'Sales.Invoices' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Sales.Invoices', N'OBJECT');
SELECT N'Sales.InvoiceLines' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Sales.InvoiceLines', N'OBJECT');
SELECT N'Sales.CustomerTransactions' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Sales.CustomerTransactions', N'OBJECT');
SELECT N'Warehouse.StockItems' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Warehouse.StockItems', N'OBJECT');
SELECT N'Warehouse.StockItemHoldings' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Warehouse.StockItemHoldings', N'OBJECT');
SELECT N'Warehouse.StockItemTransactions' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Warehouse.StockItemTransactions', N'OBJECT');
SELECT N'Sales.Customers_Archive' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Sales.Customers_Archive', N'OBJECT');
SELECT N'Warehouse.StockItems_Archive' AS Population, subentity_name, permission_name
FROM sys.fn_my_permissions(N'Warehouse.StockItems_Archive', N'OBJECT');

-- Bounded constant-only read probes, INCLUDING each physical H separately.
-- Empty source -> zero result rows, not permission failure or an invented row.
SELECT TOP (1) N'Sales.Customers' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Sales].[Customers];
SELECT TOP (1) N'Sales.Orders' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Sales].[Orders];
SELECT TOP (1) N'Sales.OrderLines' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Sales].[OrderLines];
SELECT TOP (1) N'Sales.Invoices' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Sales].[Invoices];
SELECT TOP (1) N'Sales.InvoiceLines' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Sales].[InvoiceLines];
SELECT TOP (1) N'Sales.CustomerTransactions' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Sales].[CustomerTransactions];
SELECT TOP (1) N'Warehouse.StockItems' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Warehouse].[StockItems];
SELECT TOP (1) N'Warehouse.StockItemHoldings' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Warehouse].[StockItemHoldings];
SELECT TOP (1) N'Warehouse.StockItemTransactions' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Warehouse].[StockItemTransactions];
SELECT TOP (1) N'Sales.Customers_Archive' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Sales].[Customers_Archive];
SELECT TOP (1) N'Warehouse.StockItems_Archive' AS Population, CAST(1 AS bit) AS RowPresent
FROM [Warehouse].[StockItems_Archive];

SELECT N'LP09_CROSS_DATABASE' AS CheckId,
       HAS_PERMS_BY_NAME(NULL, NULL, N'CONNECT ANY DATABASE') AS ConnectAnyDatabase,
       HAS_PERMS_BY_NAME(NULL, NULL, N'SELECT ALL USER SECURABLES') AS SelectAllUserSecurables,
       HAS_DBACCESS(@NegativeDatabase) AS NegativeDatabaseAccess;
-- Expected forbidden powers=0 and negative access=0. NULL -> NOT VERIFIED.
-- One negative target does not audit every database/module/group path.

-- Read-only TLS support: strict client handshake/certificate validation evidence
-- is external to SQL. Do not grant server-state rights just for this DMV.
IF HAS_PERMS_BY_NAME(NULL, NULL, N'VIEW SERVER PERFORMANCE STATE') = 1
   OR HAS_PERMS_BY_NAME(NULL, NULL, N'VIEW SERVER STATE') = 1
    SELECT N'LP06_OPTIONAL_DMV' AS CheckId, encrypt_option, net_transport, auth_scheme
    FROM sys.dm_exec_connections WHERE session_id = @@SPID;
ELSE
    SELECT N'LP06_OPTIONAL_DMV' AS CheckId,
           N'NOT_RUN_NO_DMV_PRIVILEGE_USE_REVIEWED_CLIENT_OR_DBA_PROOF' AS ReviewStatus;

SELECT N'EVIDENCE_ONLY_NOT_G01_G02_PASS' AS Outcome;
-- Human confirmations are prerequisites, not self-authenticating proof. Record
-- actual artifacts, all row counts/NULLs/errors and DBA review before gate closure.
