# Sales & Invoicing Profiling — Phase 1.2

**Trạng thái: Verified từ `COUNT_BIG(*)` và truy vấn `SELECT` trực tiếp trên WWI ngày 2026-11-07.** Các số tiền dưới đây là tổng cột nguồn, **không phải** định nghĩa revenue/COGS đã duyệt. SQL tái kiểm chứng: [WWI Profiling Queries](wwi-profiling-queries.md).

## Số dòng chính xác, PK và NULL

| Bảng | COUNT_BIG(*) | DISTINCT PK | Duplicate PK | NULL quan trọng |
| --- | ---: | ---: | ---: | --- |
| `Sales.Orders` | 73,595 | 73,595 | 0 | `PickedByPersonID` 10,623; `BackorderOrderID` 66,057; `PickingCompletedWhen` 3,085; `CustomerPurchaseOrderNumber` 0 |
| `Sales.OrderLines` | 231,412 | 231,412 | 0 | `UnitPrice` 0; `PickingCompletedWhen` 3,147 |
| `Sales.Invoices` | 70,510 | 70,510 | 0 | `OrderID` 0; `ConfirmedDeliveryTime` 84; `ConfirmedReceivedBy` 84 |
| `Sales.InvoiceLines` | 228,265 | 228,265 | 0 | `UnitPrice` 0 |
| `Sales.CustomerTransactions` | 97,147 | 97,147 | 0 | `InvoiceID` 26,637; `PaymentMethodID` 70,510; `FinalizationDate` 84; `IsFinalized` 0 |

`NULL` của FK tùy chọn được phân biệt với orphan trong [Inventory & Integrity Profiling](wwi-inventory-integrity-profiling.md). Các dòng `Sales.Orders` không có `PickingCompletedWhen` là quan sát, chưa gán business status.

## Quan hệ order, invoice, line và customer role

| Kiểm tra | Kết quả Verified |
| --- | ---: |
| Orders chưa có invoice | 3,085 |
| Orders có đúng một invoice | 70,510 |
| Orders có nhiều invoice | 0 (max = 1) |
| Invoices có `OrderID` NULL | 0 |
| Invoices không có invoice line | 0 |
| Invoices có một invoice line | 5,572 |
| Invoices có hơn một invoice line | 64,938 (max = 5) |
| Invoices có linked order với hơn một order line | 64,938 (max = 5) |
| Invoices có `CustomerID <> BillToCustomerID` | 44,245 |
| Invoice `CustomerID` khác linked Order `CustomerID` | 0 |
| Invoices có `IsCreditNote = 1` | 0 |

Order line và invoice line **không** có FK trực tiếp giữa từng dòng. Các số đếm không phê duyệt quan hệ một-một giữa line hoặc grain của fact.

## CustomerTransactions và trạng thái

| `TransactionTypeID` / tên nguồn | Dòng | `InvoiceID` NULL | `PaymentMethodID` NULL | Tổng `TransactionAmount` nguồn |
| --- | ---: | ---: | ---: | ---: |
| 1 / `Customer Invoice` | 70,510 | 0 | 70,510 | 198,043,439.45 |
| 3 / `Customer Payment Received` | 26,637 | 26,637 | 0 | -197,776,428.01 |

`IsFinalized=1`: 97,063 dòng; `IsFinalized=0`: 84 dòng. Toàn bộ 70,510 invoice transactions có `TransactionAmount > 0`, toàn bộ 26,637 payment transactions có `TransactionAmount < 0`. `FinalizationDate` NULL ở 84 dòng. `InvoiceID` NULL của payment là trạng thái nguồn hợp lệ theo nullable FK, chưa phải orphan.

## Số lượng và giá trị nguồn

| Cột/nhóm | Tổng | Min | Max | Ghi chú |
| --- | ---: | ---: | ---: | --- |
| OrderLines.`Quantity` | 9,310,904 | 1 | 360 | 0 dòng ≤ 0 |
| OrderLines.`UnitPrice` | 10,461,457.50 | 0.66 | 1,899.00 | Tổng đơn giá, không phải order amount; 0 dòng âm |
| InvoiceLines.`Quantity` | 8,950,628 | 1 | 360 | 0 dòng ≤ 0 |
| InvoiceLines.`UnitPrice` | 10,406,986.80 | 0.66 | 1,899.00 | Tổng đơn giá, không phải revenue; 0 dòng âm |
| InvoiceLines.`TaxAmount` | 25,782,098.25 | 0.38 | 2,848.50 | 0 dòng âm |
| InvoiceLines.`ExtendedPrice` | 198,043,439.45 | 2.88 | 21,838.50 | 0 dòng âm |
| InvoiceLines.`LineProfit` | 85,729,180.90 | -645.00 | 9,200.00 | 4,626 dòng âm; 0 dòng bằng 0 |

**Quan sát đối soát:** ở cả 70,510 invoice, tổng `InvoiceLines.ExtendedPrice` theo `InvoiceID` bằng `CustomerTransactions.TransactionAmount` của đúng một transaction type `Customer Invoice`. Đây là equality quan sát trên snapshot, không phải định nghĩa doanh thu, tax treatment hay COGS.

## Date range và phân phối

| Cột thời gian | Min | Max |
| --- | --- | --- |
| Orders.`OrderDate` | 2013-01-01 | 2016-05-31 |
| OrderLines.`PickingCompletedWhen` (non-NULL) | 2013-01-01 11:00 | 2016-05-31 11:00 |
| Invoices.`InvoiceDate` | 2013-01-01 | 2016-05-31 |
| Invoices.`ConfirmedDeliveryTime` (non-NULL) | 2013-01-02 07:05 | 2016-05-31 13:30 |
| CustomerTransactions.`TransactionDate` | 2013-01-01 | 2016-05-31 |
| CustomerTransactions.`FinalizationDate` (non-NULL) | 2013-01-02 | 2016-05-31 |

Không thấy invoice date trước linked order date hoặc confirmed delivery time trước invoice date trong các dòng có đủ cột liên quan. OrderLines và InvoiceLines không có business date riêng trong metadata; phân phối dưới đây dùng ngày của header qua FK.

### Theo năm

| Năm | Orders | OrderLines theo OrderDate | Invoices | InvoiceLines theo InvoiceDate | CustomerTransactions |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2013 | 19,450 | 61,655 | 18,767 | 60,968 | 25,536 |
| 2014 | 21,199 | 66,852 | 20,303 | 65,941 | 27,917 |
| 2015 | 23,329 | 73,003 | 22,250 | 71,898 | 30,885 |
| 2016 (đến tháng 5) | 9,617 | 29,902 | 9,190 | 29,458 | 12,809 |

### Theo tháng

| Tháng | Orders | OrderLines theo OrderDate | Invoices | InvoiceLines theo InvoiceDate | CustomerTransactions |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2013-01 | 1,674 | 5,281 | 1,639 | 5,246 | 2,181 |
| 2013-02 | 1,139 | 3,726 | 1,120 | 3,707 | 1,547 |
| 2013-03 | 1,683 | 5,389 | 1,624 | 5,330 | 2,236 |
| 2013-04 | 1,696 | 5,314 | 1,636 | 5,254 | 2,180 |
| 2013-05 | 1,808 | 5,699 | 1,727 | 5,617 | 2,330 |
| 2013-06 | 1,675 | 5,338 | 1,624 | 5,287 | 2,262 |
| 2013-07 | 1,886 | 5,896 | 1,824 | 5,834 | 2,452 |
| 2013-08 | 1,537 | 4,819 | 1,486 | 4,767 | 2,026 |
| 2013-09 | 1,617 | 5,099 | 1,539 | 5,021 | 2,089 |
| 2013-10 | 1,618 | 5,171 | 1,546 | 5,097 | 2,128 |
| 2013-11 | 1,552 | 4,957 | 1,494 | 4,899 | 2,049 |
| 2013-12 | 1,565 | 4,966 | 1,508 | 4,909 | 2,056 |
| 2014-01 | 1,791 | 5,682 | 1,719 | 5,610 | 2,354 |
| 2014-02 | 1,538 | 4,830 | 1,476 | 4,768 | 2,035 |
| 2014-03 | 1,586 | 5,118 | 1,538 | 5,070 | 2,107 |
| 2014-04 | 1,739 | 5,513 | 1,670 | 5,443 | 2,257 |
| 2014-05 | 1,908 | 6,027 | 1,811 | 5,930 | 2,509 |
| 2014-06 | 1,887 | 5,888 | 1,800 | 5,798 | 2,451 |
| 2014-07 | 2,008 | 6,310 | 1,925 | 6,227 | 2,669 |
| 2014-08 | 1,642 | 5,130 | 1,572 | 5,059 | 2,200 |
| 2014-09 | 1,637 | 5,117 | 1,580 | 5,059 | 2,173 |
| 2014-10 | 1,921 | 6,077 | 1,831 | 5,983 | 2,508 |
| 2014-11 | 1,628 | 5,151 | 1,549 | 5,070 | 2,177 |
| 2014-12 | 1,914 | 6,009 | 1,832 | 5,924 | 2,477 |
| 2015-01 | 1,830 | 5,735 | 1,749 | 5,651 | 2,442 |
| 2015-02 | 1,732 | 5,478 | 1,661 | 5,406 | 2,308 |
| 2015-03 | 1,891 | 5,947 | 1,821 | 5,877 | 2,529 |
| 2015-04 | 2,111 | 6,641 | 2,020 | 6,549 | 2,782 |
| 2015-05 | 1,959 | 6,103 | 1,857 | 6,000 | 2,618 |
| 2015-06 | 1,989 | 6,198 | 1,878 | 6,084 | 2,596 |
| 2015-07 | 2,273 | 7,066 | 2,166 | 6,955 | 2,994 |
| 2015-08 | 1,729 | 5,411 | 1,642 | 5,321 | 2,273 |
| 2015-09 | 2,065 | 6,392 | 1,970 | 6,297 | 2,701 |
| 2015-10 | 1,965 | 6,240 | 1,880 | 6,152 | 2,639 |
| 2015-11 | 1,834 | 5,719 | 1,743 | 5,625 | 2,421 |
| 2015-12 | 1,951 | 6,073 | 1,863 | 5,981 | 2,582 |
| 2016-01 | 1,944 | 6,017 | 1,844 | 5,914 | 2,606 |
| 2016-02 | 1,706 | 5,247 | 1,655 | 5,196 | 2,258 |
| 2016-03 | 1,969 | 6,159 | 1,887 | 6,074 | 2,640 |
| 2016-04 | 1,951 | 6,022 | 1,856 | 5,923 | 2,614 |
| 2016-05 | 2,047 | 6,457 | 1,948 | 6,351 | 2,691 |

## Điểm cần quyết định sau Phase 1.2

- **Verified:** 44,245 invoice có customer khác bill-to; owner cần chọn customer role theo từng KPI ở WWI-03.
- **Verified:** 3,085 order chưa invoiced; không suy tự động là canceled.
- **Unverified:** Ý nghĩa kế toán của `LineProfit`, `ExtendedPrice`, `IsCreditNote`, thuế và thời điểm ghi nhận doanh thu.
- **Proposed:** Phase 1.3/WWI-03 dùng profile này để đề xuất công thức và phép đối soát theo grain; chưa tạo fact/dimension.
