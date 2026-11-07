# Customer & Temporal Profiling — Phase 1.2

**Trạng thái: Verified từ `SELECT` trên `Sales.Customers`, `Sales.Customers_Archive` và các bảng giao dịch WWI ngày 2026-11-07.** Không quyết định thuộc tính SCD Type 2. SQL tái kiểm chứng ở [WWI Profiling Queries](wwi-profiling-queries.md).

## Quy mô và khoảng thời gian system-time

| Nguồn | COUNT_BIG(*) | DISTINCT `CustomerID` | Min `ValidFrom` | Max `ValidFrom` | Min `ValidTo` | Max `ValidTo` |
| --- | ---: | ---: | --- | --- | --- | --- |
| `Sales.Customers` hiện hành | 663 | 663 | 2013-01-01 00:00 | 2016-05-07 00:00 | 9999-12-31 23:59:59.9999999 | 9999-12-31 23:59:59.9999999 |
| `Sales.Customers_Archive` | 51 | 46 | 2013-01-01 00:00 | 2015-06-12 00:00 | 2013-07-01 16:00 | 2015-07-01 16:00 |

`AccountOpenedDate` của bảng hiện hành trải từ 2013-01-01 đến 2016-05-07. Hợp **trực tiếp** bảng hiện hành và archive bằng `UNION ALL` có 714 version rows trên 663 `CustomerID`. Đếm version theo customer: 617 ID có 1 version, 42 có 2, 3 có 3 và 1 có 4. Có 46 customer ID xuất hiện trong archive.

## Thay đổi thuộc tính giữa các version liền kề

So sánh null-safe từng cột qua `LAG` theo `CustomerID, ValidFrom, ValidTo` trên hợp trực tiếp 714 dòng; riêng `DeliveryLocation` so bằng `STAsBinary()`. Loại `CustomerID` và period columns khỏi tập thuộc tính so sánh.

| Thuộc tính | Số transition có thay đổi | Số customer ID liên quan | Nhận xét |
| --- | ---: | ---: | --- |
| `CreditLimit` | 51 | 46 | Thuộc tính nghiệp vụ duy nhất quan sát có thay đổi trong 28 cột được so sánh. |
| `LastEditedBy` | 50 | 46 | Metadata người sửa, không tự coi là thuộc tính SCD2. |
| 26 cột còn lại | 0 | 0 | Bao gồm `CustomerName`, `BillToCustomerID`, category/group, contact, địa chỉ, discount, hold flag và `DeliveryLocation`; kết quả chỉ áp dụng cho snapshot này. |

Số transition là số cặp version liền kề có giá trị khác, không phải số sự kiện nghiệp vụ độc lập. Không suy diễn nguyên nhân cập nhật từ temporal history.

## Validity, overlap, gap và phiên bản zero-duration

| Kiểm tra trên hợp trực tiếp current + archive | Kết quả |
| --- | ---: |
| Tổng version rows | 714 |
| `ValidFrom = ValidTo` | 1 |
| `ValidFrom > ValidTo` | 0 |
| Cặp version kế tiếp bị overlap | 0 |
| Cặp version kế tiếp có gap | 0 |
| Cặp version kế tiếp liền kề (`ValidTo = next ValidFrom`) | 51 |
| DISTINCT `ValidFrom` / `ValidTo` trên 714 dòng | 65 / 4 |

**Lưu ý truy vấn:** `FOR SYSTEM_TIME ALL` trả 713 dòng, trong khi current + archive trực tiếp là 714; một archive row có `ValidFrom = ValidTo` không xuất hiện trong kết quả `FOR SYSTEM_TIME ALL`. Vì vậy đếm version/transition ở đây dùng `UNION ALL` trực tiếp. Version zero-duration không cung cấp khoảng hiệu lực dương cho as-of lookup.

## Quan sát as-of với giao dịch

Kiểm tra bằng `CustomerID` và thời điểm **00:00 của business date**; một version hợp lệ nếu `ValidFrom <= timestamp < ValidTo`. Đây là phép thử khả năng lookup theo system-time, không phải xác nhận business effective time.

| Giao dịch / date proxy | Tổng dòng | Có version customer tại 00:00 | Không có version |
| --- | ---: | ---: | ---: |
| `Sales.Orders.OrderDate` | 73,595 | 73,595 | 0 |
| `Sales.Invoices.InvoiceDate` | 70,510 | 70,510 | 0 |
| `Sales.CustomerTransactions.TransactionDate` | 97,147 | 97,147 | 0 |

**Unverified:** `ValidFrom/ValidTo` là SQL Server system-time. `OrderDate`, `InvoiceDate` và `TransactionDate` là ngày nghiệp vụ, không có giờ. Lookup tại 00:00 phủ các dòng hiện có nhưng **không** chứng minh dữ liệu customer tại lúc giao dịch thật, lịch sử trước lần theo dõi đầu tiên, hoặc SCD2 chính xác toàn bộ lịch sử. Cần owner quyết định thuộc tính và quy tắc validity ở WWI-04 sau khi có thêm bằng chứng.

**Proposed cho Phase 1.3:** phân tích vai trò `CustomerID`/`BillToCustomerID` theo câu hỏi phân tích; không chuyển profile này thành warehouse schema hoặc SCD2 policy trong Phase 1.2.
