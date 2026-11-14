# WWI Logical Star Schemas — DW-01

**DW-01 logical diagrams accepted.** Logical relationships đích, không phải FK đã triển khai. Đối chiếu [Fact & Dimension Dictionary](wwi-fact-dimension-dictionary.md) và [Bus Matrix](wwi-logical-dw-design.md). Mỗi FK fact phải resolve đúng một version sau policy unknown/history được duyệt; ERD không khẳng định nguồn có đủ lịch sử. Source IDs khác tên là logical aliases, không phải cột nguồn mới.

## 1. Invoice Line Star

```mermaid
erDiagram
    dim_date ||--o{ fact_invoice_line : invoice_date_key
    dim_customer ||--o{ fact_invoice_line : buyer_customer_key
    dim_customer ||--o{ fact_invoice_line : bill_to_customer_key
    dim_product ||--o{ fact_invoice_line : product_key
    fact_invoice_line {
        int source_invoice_line_id PK
        int source_invoice_id
        int source_order_id "nullable reference"
        key invoice_date_key FK
        key buyer_customer_key FK
        key bill_to_customer_key FK
        key product_key FK
        numeric quantity
        decimal unit_price "nullable non-additive"
        decimal invoiced_sales_before_tax
        decimal tax_amount
        decimal invoice_amount_including_tax
        decimal source_reported_line_profit "optional"
    }
```

Hai cạnh dim_customer là hai alias role của cùng dimension. InvoiceID không là FK nối fact_order_line hoặc fact_stock_movement. Count toàn invoice lấy intermediate header, không SUM trên line.

## 2. Order Line Star

```mermaid
erDiagram
    dim_date ||--o{ fact_order_line : order_date_key
    dim_customer ||--o{ fact_order_line : buyer_customer_key
    dim_product ||--o{ fact_order_line : product_key
    fact_order_line {
        int source_order_line_id PK
        int source_order_id
        key order_date_key FK
        key buyer_customer_key FK
        key product_key FK
        numeric ordered_quantity
        decimal source_unit_price "nullable non-additive"
        numeric source_picked_quantity
    }
```

int_order_header bao phủ mọi order, không phải fact thứ năm. Order không line không có record trong fact_order_line; vẫn được S01/C01/C02 tính tại header.

## 3. Stock Movement Star

```mermaid
erDiagram
    dim_date ||--o{ fact_stock_movement : movement_date_key
    dim_product ||--o{ fact_stock_movement : product_key
    dim_movement_type ||--o{ fact_stock_movement : movement_type_key
    fact_stock_movement {
        int source_movement_id PK
        key movement_date_key FK
        key product_key FK
        key movement_type_key FK
        datetime source_occurred_at
        decimal signed_quantity
        int source_invoice_id "nullable reference"
        int source_purchase_order_id "nullable reference"
    }
```

Optional document references không tạo đường join fact-to-fact. Đối soát riêng các tập aggregate document-product.

## 4. Current Inventory Star

```mermaid
erDiagram
    dim_product ||--o{ fact_inventory_current : product_key_current_version
    fact_inventory_current {
        int source_stock_item_id PK
        key product_key FK
        numeric quantity_on_hand
        datetime observed_at
        datetime published_at
        string published_state_id
        string batch_id
    }
```

Grain một StockItemID trong **một current published state**, không `(StockItemID, date)`. Mỗi current fact có đúng một dimension key theo lookup policy. Một real resolved product version chỉ gắn tối đa một current item; cardinality 0..N ở diagram cho phép candidate unknown chung khi nhiều source NK chưa resolve. Dimension có nhiều versions nhưng holdings chọn current version duy nhất; các version cũ không có current holding. Không thêm dim_date vào current fact.

## 5. Consolidated Kimball Bus

Các cạnh dimension→fact thể hiện resolved/published SK, không phải JOIN natural key với toàn bộ version history. Lookup 0 match và fallback chờ DW-02; >1 match là ambiguity. Current inventory product_key gắn với published_state_id đã kiểm, observed_at và published_at là hai thời điểm riêng.

```mermaid
flowchart LR
    D[dim_date] --> I[fact_invoice_line]
    D --> O[fact_order_line]
    D --> M[fact_stock_movement]
    C[dim_customer] -->|buyer and bill-to roles| I
    C -->|buyer| O
    P[dim_product] --> I
    P --> O
    P --> M
    P -->|current version| H[fact_inventory_current]
    T[dim_movement_type] --> M
    OH[int_order_header - all orders] -. header population .-> OM[Order counts and repeat marts]
    IH[int_invoice_header - all invoices] -. invoice population .-> SM[Sales marts and AIV]
    I --> SM
    M --> MM[Inventory movement mart]
    H --> HM[Inventory current mart]
```

Bus arrows là dependency dùng chung, không chỉ định physical JOIN. Product/customer SK version keys không được dùng để distinct entity qua thời gian. Không có cạnh nối trực tiếp hai facts; drill-across chỉ sau aggregate về common grain và semantics đã xác định.
