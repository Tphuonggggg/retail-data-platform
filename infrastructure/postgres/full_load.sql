-- WWI-06A owner-reviewed initialization proposal. NOT EXECUTED by the loader.

-- Only retail_raw; normal runtime stays retail_ingest. No role creation or source DDL.

\set ON_ERROR_STOP on

BEGIN;

DO $$ BEGIN IF current_database() <> 'retail_raw' OR current_user <> 'postgres' THEN RAISE EXCEPTION 'Wrong initialization context'; END IF; END $$;

CREATE TABLE ingestion_meta.load_contracts (run_id uuid PRIMARY KEY REFERENCES ingestion_meta.runs(run_id), scope text[] NOT NULL, contract_hash text NOT NULL CHECK (contract_hash ~ '^[0-9a-f]{64}$'), source_context jsonb NOT NULL);

CREATE TABLE ingestion_meta.load_audits (run_id uuid NOT NULL REFERENCES ingestion_meta.load_contracts(run_id), object_name text NOT NULL, row_count bigint NOT NULL CHECK(row_count>=0), row_digest text NOT NULL CHECK(row_digest ~ '^[0-9a-f]{64}$'), PRIMARY KEY(run_id,object_name));

CREATE TABLE ingestion_meta.raw_publications (publication_id uuid PRIMARY KEY, run_id uuid NOT NULL UNIQUE REFERENCES ingestion_meta.load_contracts(run_id), previous_id uuid REFERENCES ingestion_meta.raw_publications(publication_id), published_at timestamptz NOT NULL DEFAULT clock_timestamp());

CREATE TABLE ingestion_meta.raw_current (singleton boolean PRIMARY KEY CHECK(singleton), publication_id uuid REFERENCES ingestion_meta.raw_publications(publication_id));

INSERT INTO ingestion_meta.raw_current(singleton,publication_id) VALUES (true,NULL);

GRANT SELECT,INSERT ON ingestion_meta.load_contracts,ingestion_meta.load_audits,ingestion_meta.raw_publications TO retail_ingest;

GRANT SELECT,UPDATE ON ingestion_meta.raw_current TO retail_ingest;

CREATE TABLE raw."sales_customertransactions" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "CustomerTransactionID" integer NOT NULL,
  "CustomerID" integer NOT NULL,
  "TransactionTypeID" integer NOT NULL,
  "InvoiceID" integer,
  "PaymentMethodID" integer,
  "TransactionDate" date NOT NULL,
  "AmountExcludingTax" numeric(18,2) NOT NULL,
  "TaxAmount" numeric(18,2) NOT NULL,
  "TransactionAmount" numeric(18,2) NOT NULL,
  "OutstandingBalance" numeric(18,2) NOT NULL,
  "FinalizationDate" date,
  "IsFinalized" boolean,
  "LastEditedBy" integer NOT NULL,
  "LastEditedWhen" text COLLATE "C" NOT NULL CHECK("LastEditedWhen" IS NULL OR "LastEditedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"CustomerTransactionID")
);

GRANT SELECT,INSERT ON raw."sales_customertransactions" TO retail_ingest;

CREATE VIEW raw."current_sales_customertransactions" AS SELECT p._run_id,p._row_ordinal,p."CustomerTransactionID",p."CustomerID",p."TransactionTypeID",p."InvoiceID",p."PaymentMethodID",p."TransactionDate",p."AmountExcludingTax",p."TaxAmount",p."TransactionAmount",p."OutstandingBalance",p."FinalizationDate",p."IsFinalized",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_customertransactions" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_sales_customertransactions" TO retail_ingest;

CREATE TABLE raw."sales_customers" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "CustomerID" integer NOT NULL,
  "CustomerName" text NOT NULL,
  "BillToCustomerID" integer NOT NULL,
  "CustomerCategoryID" integer NOT NULL,
  "BuyingGroupID" integer,
  "PrimaryContactPersonID" integer NOT NULL,
  "AlternateContactPersonID" integer,
  "DeliveryMethodID" integer NOT NULL,
  "DeliveryCityID" integer NOT NULL,
  "PostalCityID" integer NOT NULL,
  "CreditLimit" numeric(18,2),
  "AccountOpenedDate" date NOT NULL,
  "StandardDiscountPercentage" numeric(18,3) NOT NULL,
  "IsStatementSent" boolean NOT NULL,
  "IsOnCreditHold" boolean NOT NULL,
  "PaymentDays" integer NOT NULL,
  "PhoneNumber" text NOT NULL,
  "FaxNumber" text NOT NULL,
  "DeliveryRun" text,
  "RunPosition" text,
  "WebsiteURL" text NOT NULL,
  "DeliveryAddressLine1" text NOT NULL,
  "DeliveryAddressLine2" text,
  "DeliveryPostalCode" text NOT NULL,
  "DeliveryLocation" bytea,
  "PostalAddressLine1" text NOT NULL,
  "PostalAddressLine2" text,
  "PostalPostalCode" text NOT NULL,
  "LastEditedBy" integer NOT NULL,
  "ValidFrom" text COLLATE "C" NOT NULL CHECK("ValidFrom" IS NULL OR "ValidFrom" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "ValidTo" text COLLATE "C" NOT NULL CHECK("ValidTo" IS NULL OR "ValidTo" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"CustomerID")
);

GRANT SELECT,INSERT ON raw."sales_customers" TO retail_ingest;

CREATE VIEW raw."current_sales_customers" AS SELECT p._run_id,p._row_ordinal,p."CustomerID",p."CustomerName",p."BillToCustomerID",p."CustomerCategoryID",p."BuyingGroupID",p."PrimaryContactPersonID",p."AlternateContactPersonID",p."DeliveryMethodID",p."DeliveryCityID",p."PostalCityID",p."CreditLimit",p."AccountOpenedDate",p."StandardDiscountPercentage",p."IsStatementSent",p."IsOnCreditHold",p."PaymentDays",p."PhoneNumber",p."FaxNumber",p."DeliveryRun",p."RunPosition",p."WebsiteURL",p."DeliveryAddressLine1",p."DeliveryAddressLine2",p."DeliveryPostalCode",p."DeliveryLocation",p."PostalAddressLine1",p."PostalAddressLine2",p."PostalPostalCode",p."LastEditedBy",p."ValidFrom",p."ValidTo" FROM raw."sales_customers" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_sales_customers" TO retail_ingest;

CREATE TABLE raw."sales_customers_archive" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "CustomerID" integer NOT NULL,
  "CustomerName" text NOT NULL,
  "BillToCustomerID" integer NOT NULL,
  "CustomerCategoryID" integer NOT NULL,
  "BuyingGroupID" integer,
  "PrimaryContactPersonID" integer NOT NULL,
  "AlternateContactPersonID" integer,
  "DeliveryMethodID" integer NOT NULL,
  "DeliveryCityID" integer NOT NULL,
  "PostalCityID" integer NOT NULL,
  "CreditLimit" numeric(18,2),
  "AccountOpenedDate" date NOT NULL,
  "StandardDiscountPercentage" numeric(18,3) NOT NULL,
  "IsStatementSent" boolean NOT NULL,
  "IsOnCreditHold" boolean NOT NULL,
  "PaymentDays" integer NOT NULL,
  "PhoneNumber" text NOT NULL,
  "FaxNumber" text NOT NULL,
  "DeliveryRun" text,
  "RunPosition" text,
  "WebsiteURL" text NOT NULL,
  "DeliveryAddressLine1" text NOT NULL,
  "DeliveryAddressLine2" text,
  "DeliveryPostalCode" text NOT NULL,
  "DeliveryLocation" bytea,
  "PostalAddressLine1" text NOT NULL,
  "PostalAddressLine2" text,
  "PostalPostalCode" text NOT NULL,
  "LastEditedBy" integer NOT NULL,
  "ValidFrom" text COLLATE "C" NOT NULL CHECK("ValidFrom" IS NULL OR "ValidFrom" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "ValidTo" text COLLATE "C" NOT NULL CHECK("ValidTo" IS NULL OR "ValidTo" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal)
);

GRANT SELECT,INSERT ON raw."sales_customers_archive" TO retail_ingest;

CREATE VIEW raw."current_sales_customers_archive" AS SELECT p._run_id,p._row_ordinal,p."CustomerID",p."CustomerName",p."BillToCustomerID",p."CustomerCategoryID",p."BuyingGroupID",p."PrimaryContactPersonID",p."AlternateContactPersonID",p."DeliveryMethodID",p."DeliveryCityID",p."PostalCityID",p."CreditLimit",p."AccountOpenedDate",p."StandardDiscountPercentage",p."IsStatementSent",p."IsOnCreditHold",p."PaymentDays",p."PhoneNumber",p."FaxNumber",p."DeliveryRun",p."RunPosition",p."WebsiteURL",p."DeliveryAddressLine1",p."DeliveryAddressLine2",p."DeliveryPostalCode",p."DeliveryLocation",p."PostalAddressLine1",p."PostalAddressLine2",p."PostalPostalCode",p."LastEditedBy",p."ValidFrom",p."ValidTo" FROM raw."sales_customers_archive" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_sales_customers_archive" TO retail_ingest;

CREATE TABLE raw."sales_invoicelines" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "InvoiceLineID" integer NOT NULL,
  "InvoiceID" integer NOT NULL,
  "StockItemID" integer NOT NULL,
  "Description" text NOT NULL,
  "PackageTypeID" integer NOT NULL,
  "Quantity" integer NOT NULL,
  "UnitPrice" numeric(18,2),
  "TaxRate" numeric(18,3) NOT NULL,
  "TaxAmount" numeric(18,2) NOT NULL,
  "LineProfit" numeric(18,2) NOT NULL,
  "ExtendedPrice" numeric(18,2) NOT NULL,
  "LastEditedBy" integer NOT NULL,
  "LastEditedWhen" text COLLATE "C" NOT NULL CHECK("LastEditedWhen" IS NULL OR "LastEditedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"InvoiceLineID")
);

GRANT SELECT,INSERT ON raw."sales_invoicelines" TO retail_ingest;

CREATE VIEW raw."current_sales_invoicelines" AS SELECT p._run_id,p._row_ordinal,p."InvoiceLineID",p."InvoiceID",p."StockItemID",p."Description",p."PackageTypeID",p."Quantity",p."UnitPrice",p."TaxRate",p."TaxAmount",p."LineProfit",p."ExtendedPrice",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_invoicelines" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_sales_invoicelines" TO retail_ingest;

CREATE TABLE raw."sales_invoices" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "InvoiceID" integer NOT NULL,
  "CustomerID" integer NOT NULL,
  "BillToCustomerID" integer NOT NULL,
  "OrderID" integer,
  "DeliveryMethodID" integer NOT NULL,
  "ContactPersonID" integer NOT NULL,
  "AccountsPersonID" integer NOT NULL,
  "SalespersonPersonID" integer NOT NULL,
  "PackedByPersonID" integer NOT NULL,
  "InvoiceDate" date NOT NULL,
  "CustomerPurchaseOrderNumber" text,
  "IsCreditNote" boolean NOT NULL,
  "CreditNoteReason" text,
  "Comments" text,
  "DeliveryInstructions" text,
  "InternalComments" text,
  "TotalDryItems" integer NOT NULL,
  "TotalChillerItems" integer NOT NULL,
  "DeliveryRun" text,
  "RunPosition" text,
  "ReturnedDeliveryData" text,
  "ConfirmedDeliveryTime" text COLLATE "C" CHECK("ConfirmedDeliveryTime" IS NULL OR "ConfirmedDeliveryTime" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "ConfirmedReceivedBy" text,
  "LastEditedBy" integer NOT NULL,
  "LastEditedWhen" text COLLATE "C" NOT NULL CHECK("LastEditedWhen" IS NULL OR "LastEditedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"InvoiceID")
);

GRANT SELECT,INSERT ON raw."sales_invoices" TO retail_ingest;

CREATE VIEW raw."current_sales_invoices" AS SELECT p._run_id,p._row_ordinal,p."InvoiceID",p."CustomerID",p."BillToCustomerID",p."OrderID",p."DeliveryMethodID",p."ContactPersonID",p."AccountsPersonID",p."SalespersonPersonID",p."PackedByPersonID",p."InvoiceDate",p."CustomerPurchaseOrderNumber",p."IsCreditNote",p."CreditNoteReason",p."Comments",p."DeliveryInstructions",p."InternalComments",p."TotalDryItems",p."TotalChillerItems",p."DeliveryRun",p."RunPosition",p."ReturnedDeliveryData",p."ConfirmedDeliveryTime",p."ConfirmedReceivedBy",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_invoices" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_sales_invoices" TO retail_ingest;

CREATE TABLE raw."sales_orderlines" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "OrderLineID" integer NOT NULL,
  "OrderID" integer NOT NULL,
  "StockItemID" integer NOT NULL,
  "Description" text NOT NULL,
  "PackageTypeID" integer NOT NULL,
  "Quantity" integer NOT NULL,
  "UnitPrice" numeric(18,2),
  "TaxRate" numeric(18,3) NOT NULL,
  "PickedQuantity" integer NOT NULL,
  "PickingCompletedWhen" text COLLATE "C" CHECK("PickingCompletedWhen" IS NULL OR "PickingCompletedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "LastEditedBy" integer NOT NULL,
  "LastEditedWhen" text COLLATE "C" NOT NULL CHECK("LastEditedWhen" IS NULL OR "LastEditedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"OrderLineID")
);

GRANT SELECT,INSERT ON raw."sales_orderlines" TO retail_ingest;

CREATE VIEW raw."current_sales_orderlines" AS SELECT p._run_id,p._row_ordinal,p."OrderLineID",p."OrderID",p."StockItemID",p."Description",p."PackageTypeID",p."Quantity",p."UnitPrice",p."TaxRate",p."PickedQuantity",p."PickingCompletedWhen",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_orderlines" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_sales_orderlines" TO retail_ingest;

CREATE TABLE raw."sales_orders" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "OrderID" integer NOT NULL,
  "CustomerID" integer NOT NULL,
  "SalespersonPersonID" integer NOT NULL,
  "PickedByPersonID" integer,
  "ContactPersonID" integer NOT NULL,
  "BackorderOrderID" integer,
  "OrderDate" date NOT NULL,
  "ExpectedDeliveryDate" date NOT NULL,
  "CustomerPurchaseOrderNumber" text,
  "IsUndersupplyBackordered" boolean NOT NULL,
  "Comments" text,
  "DeliveryInstructions" text,
  "InternalComments" text,
  "PickingCompletedWhen" text COLLATE "C" CHECK("PickingCompletedWhen" IS NULL OR "PickingCompletedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "LastEditedBy" integer NOT NULL,
  "LastEditedWhen" text COLLATE "C" NOT NULL CHECK("LastEditedWhen" IS NULL OR "LastEditedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"OrderID")
);

GRANT SELECT,INSERT ON raw."sales_orders" TO retail_ingest;

CREATE VIEW raw."current_sales_orders" AS SELECT p._run_id,p._row_ordinal,p."OrderID",p."CustomerID",p."SalespersonPersonID",p."PickedByPersonID",p."ContactPersonID",p."BackorderOrderID",p."OrderDate",p."ExpectedDeliveryDate",p."CustomerPurchaseOrderNumber",p."IsUndersupplyBackordered",p."Comments",p."DeliveryInstructions",p."InternalComments",p."PickingCompletedWhen",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_orders" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_sales_orders" TO retail_ingest;

CREATE TABLE raw."warehouse_stockitemholdings" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "StockItemID" integer NOT NULL,
  "QuantityOnHand" integer NOT NULL,
  "BinLocation" text NOT NULL,
  "LastStocktakeQuantity" integer NOT NULL,
  "LastCostPrice" numeric(18,2) NOT NULL,
  "ReorderLevel" integer NOT NULL,
  "TargetStockLevel" integer NOT NULL,
  "LastEditedBy" integer NOT NULL,
  "LastEditedWhen" text COLLATE "C" NOT NULL CHECK("LastEditedWhen" IS NULL OR "LastEditedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"StockItemID")
);

GRANT SELECT,INSERT ON raw."warehouse_stockitemholdings" TO retail_ingest;

CREATE VIEW raw."current_warehouse_stockitemholdings" AS SELECT p._run_id,p._row_ordinal,p."StockItemID",p."QuantityOnHand",p."BinLocation",p."LastStocktakeQuantity",p."LastCostPrice",p."ReorderLevel",p."TargetStockLevel",p."LastEditedBy",p."LastEditedWhen" FROM raw."warehouse_stockitemholdings" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_warehouse_stockitemholdings" TO retail_ingest;

CREATE TABLE raw."warehouse_stockitemtransactions" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "StockItemTransactionID" integer NOT NULL,
  "StockItemID" integer NOT NULL,
  "TransactionTypeID" integer NOT NULL,
  "CustomerID" integer,
  "InvoiceID" integer,
  "SupplierID" integer,
  "PurchaseOrderID" integer,
  "TransactionOccurredWhen" text COLLATE "C" NOT NULL CHECK("TransactionOccurredWhen" IS NULL OR "TransactionOccurredWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "Quantity" numeric(18,3) NOT NULL,
  "LastEditedBy" integer NOT NULL,
  "LastEditedWhen" text COLLATE "C" NOT NULL CHECK("LastEditedWhen" IS NULL OR "LastEditedWhen" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"StockItemTransactionID")
);

GRANT SELECT,INSERT ON raw."warehouse_stockitemtransactions" TO retail_ingest;

CREATE VIEW raw."current_warehouse_stockitemtransactions" AS SELECT p._run_id,p._row_ordinal,p."StockItemTransactionID",p."StockItemID",p."TransactionTypeID",p."CustomerID",p."InvoiceID",p."SupplierID",p."PurchaseOrderID",p."TransactionOccurredWhen",p."Quantity",p."LastEditedBy",p."LastEditedWhen" FROM raw."warehouse_stockitemtransactions" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_warehouse_stockitemtransactions" TO retail_ingest;

CREATE TABLE raw."warehouse_stockitems" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "StockItemID" integer NOT NULL,
  "StockItemName" text NOT NULL,
  "SupplierID" integer NOT NULL,
  "ColorID" integer,
  "UnitPackageID" integer NOT NULL,
  "OuterPackageID" integer NOT NULL,
  "Brand" text,
  "Size" text,
  "LeadTimeDays" integer NOT NULL,
  "QuantityPerOuter" integer NOT NULL,
  "IsChillerStock" boolean NOT NULL,
  "Barcode" text,
  "TaxRate" numeric(18,3) NOT NULL,
  "UnitPrice" numeric(18,2) NOT NULL,
  "RecommendedRetailPrice" numeric(18,2),
  "TypicalWeightPerUnit" numeric(18,3) NOT NULL,
  "MarketingComments" text,
  "InternalComments" text,
  "Photo" bytea,
  "CustomFields" text,
  "Tags" text,
  "SearchDetails" text NOT NULL,
  "LastEditedBy" integer NOT NULL,
  "ValidFrom" text COLLATE "C" NOT NULL CHECK("ValidFrom" IS NULL OR "ValidFrom" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "ValidTo" text COLLATE "C" NOT NULL CHECK("ValidTo" IS NULL OR "ValidTo" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal),
  UNIQUE(_run_id,"StockItemID")
);

GRANT SELECT,INSERT ON raw."warehouse_stockitems" TO retail_ingest;

CREATE VIEW raw."current_warehouse_stockitems" AS SELECT p._run_id,p._row_ordinal,p."StockItemID",p."StockItemName",p."SupplierID",p."ColorID",p."UnitPackageID",p."OuterPackageID",p."Brand",p."Size",p."LeadTimeDays",p."QuantityPerOuter",p."IsChillerStock",p."Barcode",p."TaxRate",p."UnitPrice",p."RecommendedRetailPrice",p."TypicalWeightPerUnit",p."MarketingComments",p."InternalComments",p."Photo",p."CustomFields",p."Tags",p."SearchDetails",p."LastEditedBy",p."ValidFrom",p."ValidTo" FROM raw."warehouse_stockitems" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_warehouse_stockitems" TO retail_ingest;

CREATE TABLE raw."warehouse_stockitems_archive" (
  _run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
  _row_ordinal bigint NOT NULL CHECK(_row_ordinal>0),
  "StockItemID" integer NOT NULL,
  "StockItemName" text NOT NULL,
  "SupplierID" integer NOT NULL,
  "ColorID" integer,
  "UnitPackageID" integer NOT NULL,
  "OuterPackageID" integer NOT NULL,
  "Brand" text,
  "Size" text,
  "LeadTimeDays" integer NOT NULL,
  "QuantityPerOuter" integer NOT NULL,
  "IsChillerStock" boolean NOT NULL,
  "Barcode" text,
  "TaxRate" numeric(18,3) NOT NULL,
  "UnitPrice" numeric(18,2) NOT NULL,
  "RecommendedRetailPrice" numeric(18,2),
  "TypicalWeightPerUnit" numeric(18,3) NOT NULL,
  "MarketingComments" text,
  "InternalComments" text,
  "Photo" bytea,
  "CustomFields" text,
  "Tags" text,
  "SearchDetails" text NOT NULL,
  "LastEditedBy" integer NOT NULL,
  "ValidFrom" text COLLATE "C" NOT NULL CHECK("ValidFrom" IS NULL OR "ValidFrom" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  "ValidTo" text COLLATE "C" NOT NULL CHECK("ValidTo" IS NULL OR "ValidTo" ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{7}$'),
  PRIMARY KEY(_run_id,_row_ordinal)
);

GRANT SELECT,INSERT ON raw."warehouse_stockitems_archive" TO retail_ingest;

CREATE VIEW raw."current_warehouse_stockitems_archive" AS SELECT p._run_id,p._row_ordinal,p."StockItemID",p."StockItemName",p."SupplierID",p."ColorID",p."UnitPackageID",p."OuterPackageID",p."Brand",p."Size",p."LeadTimeDays",p."QuantityPerOuter",p."IsChillerStock",p."Barcode",p."TaxRate",p."UnitPrice",p."RecommendedRetailPrice",p."TypicalWeightPerUnit",p."MarketingComments",p."InternalComments",p."Photo",p."CustomFields",p."Tags",p."SearchDetails",p."LastEditedBy",p."ValidFrom",p."ValidTo" FROM raw."warehouse_stockitems_archive" p JOIN ingestion_meta.raw_publications u ON u.run_id=p._run_id JOIN ingestion_meta.raw_current c ON c.publication_id=u.publication_id WHERE c.singleton;

GRANT SELECT ON raw."current_warehouse_stockitems_archive" TO retail_ingest;

COMMIT;
