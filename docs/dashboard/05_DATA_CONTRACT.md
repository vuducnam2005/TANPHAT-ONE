# Data contract cho Tan Phat Executive Dashboard

Contract này là ranh giới giữa repository và OWL. Các tên bên dưới là tên DTO ổn định, không phải tên cột Excel và không buộc ORM tương lai dùng cùng tên. `schemaVersion` hiện tại đề xuất `1.0`.

## 1. Quy ước chung

```json
{
  "schemaVersion": "1.0",
  "snapshotId": "fixture-2026-10-27-v1",
  "asOf": "2026-10-27T00:00:00+07:00",
  "source": "mock-excel-extract",
  "fixture": true,
  "coverage": "complete"
}
```

- Tiền là số nguyên VNĐ, không dùng chuỗi đã format; không dùng float cho phép tính tiền.
- Tỷ lệ là số thập phân 0–1 khi có mẫu số, ví dụ 0.25 là 25%; có thể lớn hơn 1. Không ép trần.
- Ngày là ISO 8601 có timezone nếu biết; ngày Excel serial phải map một lần ở adapter.
- `null` = thiếu/unavailable; `0` = giá trị bằng 0; `notApplicable` = không áp dụng và được format thành “—”.
- ID là chuỗi ổn định. `projectId`, `itemId`, `contractorId`, `transactionId`, `rootTransactionId` không lấy từ tên hiển thị.
- `provenance` chỉ ra sheet/field gốc hoặc `computed`; không đưa raw formula vào UI.
- DTO read-only. UI không sửa hoặc ghi ngược repository.

## 2. Hình dạng DTO minh họa

Các JSON trong phần này chỉ minh họa field/type, không phải fixture đã trích xuất hoặc số liệu dự án. Timestamp, ID minh họa và các số 0 không được dùng làm dữ liệu thực tế. Schema validation chính thức nằm ở mục 9; quy tắc phạm vi ở mục 11.

### Project

```json
{
  "projectId": "project-fixture-01",
  "code": "FIX-TP-01",
  "name": "Tên dự án đã ẩn danh",
  "investor": { "id": "investor-1", "name": "Chủ đầu tư đã ẩn danh" },
  "status": null,
  "currency": "VND",
  "fixture": true,
  "provenance": { "kind": "source", "references": ["DATA:D6", "DATA:D7", "DATA:D8"] }
}
```

### Overview

```json
{
  "projectId": "project-fixture-01",
  "investor": { "metrics": { "contractOriginal": 0, "contractCurrent": 0,
    "production": null, "accepted": 0, "invoiced": 0,
    "paid": 0, "retention": 0, "receivableByAcceptance": 0,
    "receivableAfterRetention": 0 },
    "ratios": { "productionOverContract": null,
      "paidOverContract": null, "paidOverAcceptance": null },
    "provenance": {} },
  "contractors": { "level1": { "metrics": { "contractOriginal": 0,
      "contractCurrent": 0, "production": null, "accepted": 0,
      "paid": 0, "payableByAcceptance": 0, "payableByContract": 0 },
      "ratios": { "productionOverContract": null,
        "paidOverContract": null, "paidOverAcceptance": null },
      "provenance": {} },
    "level2": { "metrics": { "contractOriginal": 0, "contractCurrent": 0,
      "production": null, "accepted": 0, "paid": 0,
      "payableByAcceptance": 0, "payableByContract": 0 },
      "ratios": { "productionOverContract": null,
        "paidOverContract": null, "paidOverAcceptance": null },
      "provenance": {} } },
  "alerts": [],
  "charts": [],
  "provenance": {}
}
```

`production` là `null` khi không có giá trị. Workbook hiện có raw zero ở cột sản lượng nhưng không đủ bằng chứng người dùng đã khai 0 hay macro điền mặc định. Không tự chuyển raw zero thành null hoặc coi đó là số đã xác nhận: giữ raw value kèm availability=ambiguous_zero cho tới khi PKH xác nhận. Mục 11 quy định cách hiển thị/tính chỉ số phụ thuộc.

### Item và ContractorItem

```json
{
  "itemId": "item-01",
  "projectId": "project-fixture-01",
  "name": "Tên hạng mục chuẩn",
  "side": "investor",
  "metrics": {
    "contractOriginal": 0, "contractCurrent": 0, "production": null,
    "accepted": 0, "unaccepted": null, "invoiced": 0,
    "paid": 0, "retention": 0, "receivableByAcceptance": 0,
    "receivableAfterRetention": 0
  },
  "ratios": { "productionOverContract": null,
    "paidOverContract": null, "paidOverAcceptance": null },
  "alertCodes": [],
  "documentLinks": [],
  "provenance": { "accepted": { "kind": "source", "references": ["ChuDauTu:F"] } }
}
```

ContractorItem thêm `contractorId`, `contractorName`, `transactionType` (`company_subcontractor`, `internal_allocation`, `department_subcontractor`), `parentContractorId`, `level` (1 hoặc 2), `includedInCompanyTotal` và `allocation` (`allocated`, `departmentSubcontracted`, `remaining`).

### Transaction

```json
{
  "transactionId": "tx-0004",
  "rootTransactionId": "tx-0001",
  "sequence": 4,
  "sourceRow": 8,
  "projectId": "project-fixture-01",
  "side": "investor",
  "itemId": "item-01",
  "contractorId": null,
  "bookedAt": "2026-10-07T00:00:00+07:00",
  "eventType": null,
  "description": "Bản sửa giao dịch minh họa",
  "amounts": { "contractOriginal": 0, "contractAdjustment": 0,
    "production": null, "accepted": 0, "invoiced": 0,
    "paid": 0, "retention": 0 },
  "operation": "edit",
  "effective": true,
  "documentLinks": [],
  "provenance": { "kind": "source", "references": ["NHAT_KY_TC:L", "NHAT_KY_TC:O"] }
}
```

Không trả bản cũ đã mất hiệu lực trong `getTransactions` mặc định. Tab lịch sử có thể trả thêm `effective=false` khi query yêu cầu, có nhãn rõ và không đưa lịch sử vào tổng snapshot.

### Alert

```json
{
  "alertId": "alert-item-01-payment-over-acceptance",
  "code": "PAYMENT_OVER_ACCEPTANCE",
  "severity": "attention",
  "scope": { "projectId": "project-fixture-01", "itemId": "item-01" },
  "message": "Đã thanh toán vượt giá trị nghiệm thu theo dữ liệu hiện có.",
  "explanation": "Có thể gồm tạm ứng hoặc biên bản nghiệm thu chưa nhập.",
  "metric": { "paid": 120, "accepted": 100, "difference": 20 },
  "provenance": { "kind": "computed", "references": ["paid - accepted"] }
}
```

Alert codes bắt buộc: `PAYMENT_OVER_ACCEPTANCE`, `NOT_ACCEPTED`, `RECEIVABLE_BY_ACCEPTANCE`, `RETENTION_ONLY`, `PAID_IN_FULL`, `CHILD_ALLOCATION_OVER_PARENT`, `MISSING_DATA`. Không dùng `PROFIT_MARGIN` vì chưa có dữ liệu/lệnh tính được duyệt.

## 3. Query và kết quả

```json
{
  "projectId": "project-fixture-01",
  "side": "all",
  "itemId": null,
  "contractorId": null,
  "transactionType": null,
  "level": "all",
  "search": "",
  "dateFrom": null,
  "dateTo": null,
  "page": 1,
  "pageSize": 25,
  "sort": { "field": "accepted", "direction": "desc" }
}
```

Kết quả danh sách phải chứa `{ rows, totalRows, totals, totalsScope, filtersApplied, meta }`. `totals` tính trên toàn scope sau bộ lọc tài chính, trước search và phân trang. V1 chốt `search` chỉ thu hẹp danh sách hiển thị, không đổi KPI/totals; `totalRows` là số dòng sau search, UI ghi rõ. `dateFrom/dateTo` chỉ là ngày ghi sổ ở tab giao dịch, không áp vào KPI snapshot.

## 4. Ánh xạ Excel → DTO → component

| Sheet | Trường gốc | Ý nghĩa | Kiểu DTO | Property | Component |
| --- | --- | --- | --- | --- | --- |
| DATA | D6, D7, D8 | Mã, tên, CĐT | string | Project.code/name/investor | ProjectHeader |
| ChuDauTu | B11:B110 | Một hạng mục CĐT | string | Item.name/itemId | InvestorTable, charts |
| ChuDauTu | C/D | HĐ gốc/cập nhật | integer VND | metrics.contractOriginal/current | KpiCard, table |
| ChuDauTu | E/F/G | Sản lượng/NT/chưa NT | integer or null | production/accepted/unaccepted | KpiCard, table |
| ChuDauTu | H/I/J/K/L | Hóa đơn/đã thu/giữ lại/công nợ | integer VND | invoiced/paid/retention/receivables | Overview, table |
| ChuDauTu | M/N/O/Q | Tỷ lệ/cảnh báo | decimal/string code | ratios/alertCodes | KpiCard, AlertList |
| NHAT_KY_TC | C,D,E:R,L:O | CĐT transaction + effective chain | Transaction | side=investor, amounts, operation/effective | Detail, transaction table |
| Thauphu | B/C/D/E | Đơn vị/hạng mục/loại/khoán mẹ | string/enum | contractor fields | ContractorTable |
| Thauphu | F/P | Tính tổng và cấp | boolean/integer | includedInCompanyTotal/level | HierarchyTable |
| Thauphu | H:O | Hợp đồng/sản lượng/NT/TT/công nợ | integer/null | contractor metrics | Overview, table |
| Thauphu | Q:R:S:T | Khoán mẹ, cấp 2, còn lại/cảnh báo | integer/string | allocation/alertCodes | Allocation block |
| NHAT_KY | C:E,F:Q,R:S,K:N | Thầu phụ transaction + chain | Transaction | side=contractor, amounts, type/effective | Detail/history |
| DM_HangMuc | A:D | Danh mục và search không dấu | string | Item catalogue/crosswalk candidate | Filters |
| DanhBa_ThauPhu | A:F | Danh bạ/loại/liên hệ | string | Contractor reference | Project filters/detail |
| TP_* | B:M | Chi tiết đơn vị dựng từ nhật ký | Transaction view | detail rows only | Contractor detail |
| Dashboard | B:H | Tổng tham chiếu | computed | Overview only, never source of truth | Overview |

Dashboard sheet là view công thức, không dùng làm raw source khi nhật ký/summary có thể đọc. `TP_*` chỉ là view chi tiết; không cộng nó với NHAT_KY lần nữa.

## 5. Chuẩn hóa hiệu lực và tính tổng

Adapter thực hiện theo thứ tự:

1. Đọc record có `rootTransactionId = ID GỐC` (giao dịch mới có root bằng ID của nó).
2. Chọn record có `transactionId` lớn nhất trong stream.
3. Nếu operation là `delete`/`XÓA`, đánh dấu stream không hiệu lực; nếu là `edit`, dùng amounts/metadata của record mới nhất.
4. Chỉ record effective=true đi vào aggregate. Giữ lịch sử bên cạnh cho drill-down, không đưa vào totals.
5. Với CĐT, group theo projectId + normalized itemId. Với thầu phụ, group theo projectId + contractorId + normalized itemId. Nếu cùng cặp có nhiều loại giao dịch/khoán mẹ xung đột, báo validation issue để BA giải quyết; không tự gộp hoặc tự chuyển thành cấp 1.
6. Với tổng cấp công ty, filter `level=1` và `includedInCompanyTotal=true`. Cấp 2 group riêng theo `parentContractorId`; không cộng parent row một lần cho mỗi child.
7. Mọi aggregate trả provenance: record IDs/sheet fields đã góp vào metric, cùng `availability`.

Pseudo-code kiểm chứng:

```text
effective = latestByRoot(transactions).filter(not_deleted)
investor = aggregate(effective where side=investor, project + item)
level1 = aggregate(effective where side=contractor and level=1)
level2 = aggregate(effective where side=contractor and level=2)
payableByAcceptance = accepted - paid
payableByContract = contractCurrent - paid
unaccepted = production - accepted only when production is present
ratio = numerator / denominator only when denominator is non-zero and numerator present
```

Không dùng công thức chênh HĐ CĐT − HĐ thầu phụ làm lợi nhuận. Không cộng `Thauphu!I` cấp 2 vào `Thauphu!I4`. Cảnh báo cấp 2 vượt mẹ so tổng HĐ cập nhật child với giá trị khoán mẹ phù hợp scope; nếu mẹ không phân bổ được theo hạng mục, trả `allocationScope="contractor"` và cảnh báo cần BA.

## 6. Null, zero, negative và format

| Trường hợp | Lưu DTO | Hiển thị |
| --- | --- | --- |
| Chưa khai sản lượng | null + availability=missing | “Chưa có sản lượng” |
| Sản lượng thật bằng 0 | 0 + availability=reported | `0 ₫` |
| Mẫu số tỷ lệ bằng 0 | null + unavailableReason=zero_denominator | `—` + tooltip |
| Hóa đơn phía thầu phụ không áp dụng | null + notApplicable=true | `—` |
| Công nợ âm | số âm | `−20 ₫` theo locale VN, kèm explanation |
| Số tiền lớn | integer VND | format locale VN, tooltip giá trị đầy đủ |
| Tên thiếu | null | “Chưa đặt tên”; không tạo ID từ chuỗi rỗng |

Formatter nhận locale từ Odoo và unit từ DTO. Phần trăm dùng 1 chữ số thập phân ở bảng, 0 hoặc 1 ở KPI theo độ dài; metric gốc không bị làm tròn trước aggregate.

## 7. API/ORM tương lai

Khi có backend, endpoint hoặc ORM method phải trả cùng DTO/Result contract. Server chịu trách nhiệm company/user/project scope, effective ledger, aggregate và pagination lớn. JSON API phải có `schemaVersion`, `snapshotId`, `asOf`, `source` và error code. Không trả path NAS thô; dùng attachment/document URL được cấp quyền.

Đề xuất mapping dài hạn thống nhất với roadmap: `project.project`/`tp.project` → Project; `tp.client.transaction` → investor transactions; `tp.contractor.transaction` → contractor transactions; `res.partner` + loại đối tác → contractor/investor reference; `tp.work.item` là danh mục hạng mục nếu được duyệt. Đây là mapping để thẩm định, chưa tạo model trong phase frontend.

## 8. Kiểm soát phiên bản và dữ liệu thật

- Fixture chính thức đi kèm tests phải nhỏ, ẩn danh, có edge cases và được tạo từ mapping đã review.
- Snapshot thật/Excel thật không commit vào static, không đưa vào bundle công khai, không gửi lên client nếu chỉ cần aggregate.
- `schemaVersion` minor khi thêm nullable field; major khi đổi nghĩa/kiểu; adapter có migration test.
- Mọi KPI phải truy ngược provenance tới sheet/field hoặc model/field và có owner nghiệp vụ. Chưa có nguồn thì DTO để null, không “ước lượng”.

## 9. JSON Schema v1

Đặc tả dưới đây dùng JSON Schema draft 2020-12. Khi triển khai, lưu trong `features/dashboard_data/schema.json`; không cài validator dependency lớn chỉ để chạy schema nếu validator nhẹ theo field và HOOT contract test đủ dùng. Schema mô tả cấu trúc, mục 11 bổ sung invariants liên trường. Dùng `$ref` tương ứng cho từng method trả về.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:tanphat:dashboard:v1",
  "$defs": {
    "Id": { "type": "string", "minLength": 1 },
    "Money": {
      "type": ["integer", "null"],
      "minimum": -9007199254740991,
      "maximum": 9007199254740991
    },
    "Ratio": { "type": ["number", "null"] },
    "Link": {
      "type": "object",
      "required": ["id", "label", "url", "allowed"],
      "properties": {
        "id": { "$ref": "#/$defs/Id" },
        "label": { "type": "string" },
        "url": { "type": "string", "format": "uri" },
        "allowed": { "type": "boolean" }
      }
    },
    "Meta": {
      "type": "object",
      "required": ["schemaVersion", "snapshotId", "asOf", "source", "fixture", "coverage"],
      "properties": {
        "schemaVersion": { "const": "1.0" },
        "snapshotId": { "$ref": "#/$defs/Id" },
        "asOf": { "type": "string", "format": "date-time" },
        "source": { "enum": ["mock-excel-extract", "odoo-api"] },
        "fixture": { "type": "boolean" },
        "coverage": { "enum": ["complete", "partial", "missing", "ambiguous"] },
        "warnings": { "type": "array", "items": { "type": "string" } }
      }
    },
    "Provenance": {
      "type": "object",
      "required": ["kind", "references"],
      "properties": {
        "kind": { "enum": ["source", "computed"] },
        "references": { "type": "array", "items": { "type": "string" } },
        "availability": {
          "enum": ["reported", "missing", "ambiguous_zero", "not_applicable", "partial", "zero_denominator"]
        }
      }
    },
    "Scope": {
      "type": "object",
      "required": ["projectId"],
      "properties": {
        "projectId": { "$ref": "#/$defs/Id" },
        "side": { "enum": ["all", "investor", "contractor"] },
        "itemId": { "type": ["string", "null"] },
        "contractorId": { "type": ["string", "null"] },
        "transactionType": { "enum": [null, "company_subcontractor", "internal_allocation", "department_subcontractor"] },
        "level": { "enum": ["all", 1, 2] }
      }
    },
    "Query": {
      "allOf": [
        { "$ref": "#/$defs/Scope" },
        {
          "type": "object",
          "properties": {
            "search": { "type": "string" },
            "dateFrom": { "type": ["string", "null"], "format": "date" },
            "dateTo": { "type": ["string", "null"], "format": "date" },
            "includeHistory": { "type": "boolean" },
            "page": { "type": "integer", "minimum": 1 },
            "pageSize": { "type": "integer", "minimum": 1, "maximum": 100 },
            "sort": { "type": "object", "required": ["field", "direction"], "properties": { "field": { "type": "string" }, "direction": { "enum": ["asc", "desc"] } } }
          }
        }
      ]
    },
    "Project": {
      "type": "object",
      "required": ["projectId", "code", "name", "investor", "currency", "fixture"],
      "properties": {
        "projectId": { "$ref": "#/$defs/Id" },
        "code": { "type": "string", "minLength": 1 },
        "name": { "type": "string", "minLength": 1 },
        "investor": {
          "type": "object",
          "required": ["id", "name"],
          "properties": {
            "id": { "type": ["string", "null"] },
            "name": { "type": ["string", "null"] }
          }
        },
        "status": { "type": ["string", "null"] },
        "currency": { "const": "VND" },
        "fixture": { "type": "boolean" },
        "provenance": { "$ref": "#/$defs/Provenance" }
      }
    },
    "Metrics": {
      "type": "object",
      "required": ["contractOriginal", "contractCurrent", "production", "accepted", "paid"],
      "properties": {
        "contractOriginal": { "$ref": "#/$defs/Money" },
        "contractCurrent": { "$ref": "#/$defs/Money" },
        "production": { "$ref": "#/$defs/Money" },
        "accepted": { "$ref": "#/$defs/Money" },
        "unaccepted": { "$ref": "#/$defs/Money" },
        "invoiced": { "$ref": "#/$defs/Money" },
        "paid": { "$ref": "#/$defs/Money" },
        "retention": { "$ref": "#/$defs/Money" },
        "receivableByAcceptance": { "$ref": "#/$defs/Money" },
        "receivableAfterRetention": { "$ref": "#/$defs/Money" },
        "payableByAcceptance": { "$ref": "#/$defs/Money" },
        "payableByContract": { "$ref": "#/$defs/Money" }
      },
      "additionalProperties": false
    },
    "Ratios": {
      "type": "object",
      "required": ["productionOverContract", "paidOverContract", "paidOverAcceptance"],
      "properties": {
        "productionOverContract": { "$ref": "#/$defs/Ratio" },
        "paidOverContract": { "$ref": "#/$defs/Ratio" },
        "paidOverAcceptance": { "$ref": "#/$defs/Ratio" }
      },
      "additionalProperties": false
    },
    "Item": {
      "type": "object",
      "required": ["itemId", "projectId", "name", "side", "metrics", "ratios", "provenance"],
      "properties": {
        "itemId": { "$ref": "#/$defs/Id" },
        "projectId": { "$ref": "#/$defs/Id" },
        "name": { "type": "string" },
        "side": { "const": "investor" },
        "metrics": { "$ref": "#/$defs/Metrics" },
        "ratios": { "$ref": "#/$defs/Ratios" },
        "provenance": { "type": "object", "additionalProperties": { "$ref": "#/$defs/Provenance" } },
        "alertCodes": { "type": "array", "items": { "type": "string" } },
        "documentLinks": { "type": "array", "items": { "$ref": "#/$defs/Link" } }
      }
    },
    "Contractor": {
      "type": "object",
      "required": ["contractorId", "name", "catalogCode"],
      "properties": {
        "contractorId": { "$ref": "#/$defs/Id" },
        "name": { "type": "string" },
        "catalogCode": { "type": ["string", "null"] },
        "group": { "type": ["string", "null"] },
        "contact": { "type": ["string", "null"] },
        "pastProjectsText": { "type": ["string", "null"] },
        "notes": { "type": ["string", "null"] }
      }
    },
    "ContractorItem": {
      "type": "object",
      "required": ["rowId", "projectId", "contractorId", "itemId", "transactionType", "parentContractorId", "level", "includedInCompanyTotal", "metrics", "ratios"],
      "properties": {
        "rowId": { "$ref": "#/$defs/Id" },
        "projectId": { "$ref": "#/$defs/Id" },
        "contractorId": { "$ref": "#/$defs/Id" },
        "itemId": { "$ref": "#/$defs/Id" },
        "transactionType": { "enum": ["company_subcontractor", "internal_allocation", "department_subcontractor"] },
        "parentContractorId": { "type": ["string", "null"] },
        "level": { "enum": [1, 2] },
        "includedInCompanyTotal": { "type": "boolean" },
        "metrics": { "$ref": "#/$defs/Metrics" },
        "ratios": { "$ref": "#/$defs/Ratios" },
        "allocation": {
          "type": ["object", "null"],
          "properties": {
            "scope": { "enum": ["contractor", "item"] },
            "allocated": { "$ref": "#/$defs/Money" },
            "departmentSubcontracted": { "$ref": "#/$defs/Money" },
            "remaining": { "$ref": "#/$defs/Money" }
          }
        }
      }
    },
    "Transaction": {
      "type": "object",
      "required": ["transactionId", "rootTransactionId", "sequence", "sourceRow", "projectId", "side", "itemId", "operation", "effective", "amounts"],
      "properties": {
        "transactionId": { "$ref": "#/$defs/Id" },
        "rootTransactionId": { "$ref": "#/$defs/Id" },
        "sequence": { "type": "integer", "minimum": 1 },
        "sourceRow": { "type": "integer", "minimum": 1 },
        "projectId": { "$ref": "#/$defs/Id" },
        "side": { "enum": ["investor", "contractor"] },
        "itemId": { "$ref": "#/$defs/Id" },
        "contractorId": { "type": ["string", "null"] },
        "bookedAt": { "type": ["string", "null"], "format": "date-time" },
        "eventType": { "type": ["string", "null"] },
        "description": { "type": ["string", "null"] },
        "operation": { "enum": ["new", "edit", "delete"] },
        "effective": { "type": "boolean" },
        "provenance": { "$ref": "#/$defs/Provenance" },
        "amounts": {
          "type": "object",
          "required": ["contractOriginal", "contractAdjustment", "production", "accepted", "invoiced", "paid", "retention"],
          "properties": {
            "contractOriginal": { "$ref": "#/$defs/Money" },
            "contractAdjustment": { "$ref": "#/$defs/Money" },
            "production": { "$ref": "#/$defs/Money" },
            "accepted": { "$ref": "#/$defs/Money" },
            "invoiced": { "$ref": "#/$defs/Money" },
            "paid": { "$ref": "#/$defs/Money" },
            "retention": { "$ref": "#/$defs/Money" }
          }
        },
        "documentLinks": { "type": "array", "items": { "$ref": "#/$defs/Link" } }
      }
    },
    "Alert": {
      "type": "object",
      "required": ["alertId", "code", "severity", "scope", "message", "explanation"],
      "properties": {
        "alertId": { "$ref": "#/$defs/Id" },
        "code": { "enum": ["PAYMENT_OVER_ACCEPTANCE", "NOT_ACCEPTED", "RECEIVABLE_BY_ACCEPTANCE", "RETENTION_ONLY", "PAID_IN_FULL", "CHILD_ALLOCATION_OVER_PARENT", "MISSING_DATA"] },
        "severity": { "enum": ["info", "attention", "success", "data_issue"] },
        "scope": { "type": "object", "required": ["projectId"], "properties": { "projectId": { "$ref": "#/$defs/Id" }, "itemId": { "type": ["string", "null"] }, "contractorId": { "type": ["string", "null"] } } },
        "message": { "type": "string" },
        "explanation": { "type": "string" },
        "metric": { "type": "object" },
        "provenance": { "$ref": "#/$defs/Provenance" }
      }
    },
    "SideSummary": {
      "type": "object",
      "required": ["metrics", "ratios", "provenance"],
      "properties": {
        "metrics": { "$ref": "#/$defs/Metrics" },
        "ratios": { "$ref": "#/$defs/Ratios" },
        "provenance": { "type": "object", "additionalProperties": { "$ref": "#/$defs/Provenance" } }
      }
    },
    "ChartSpec": {
      "type": "object",
      "required": ["id", "type", "unit", "labels", "datasets", "fallbackTable"],
      "properties": {
        "id": { "$ref": "#/$defs/Id" },
        "type": { "enum": ["bar", "line"] },
        "unit": { "const": "VND" },
        "labels": { "type": "array", "items": { "type": "string" } },
        "datasets": { "type": "array", "items": { "type": "object", "required": ["label", "data"], "properties": { "label": { "type": "string" }, "data": { "type": "array", "items": { "$ref": "#/$defs/Money" } } } } },
        "fallbackTable": { "type": "array", "items": { "type": "object" } }
      }
    },
    "Overview": {
      "type": "object",
      "required": ["projectId", "investor", "contractors", "alerts", "charts"],
      "properties": {
        "projectId": { "$ref": "#/$defs/Id" },
        "investor": { "$ref": "#/$defs/SideSummary" },
        "contractors": { "type": "object", "required": ["level1", "level2"], "properties": { "level1": { "$ref": "#/$defs/SideSummary" }, "level2": { "$ref": "#/$defs/SideSummary" } } },
        "alerts": { "type": "array", "items": { "$ref": "#/$defs/Alert" } },
        "charts": { "type": "array", "items": { "$ref": "#/$defs/ChartSpec" } }
      }
    },
    "Detail": {
      "type": "object",
      "required": ["project", "contractor", "summary", "investorItems", "contractorItems", "transactions", "documentLinks"],
      "properties": {
        "project": { "$ref": "#/$defs/Project" },
        "contractor": { "anyOf": [{ "$ref": "#/$defs/Contractor" }, { "type": "null" }] },
        "summary": { "$ref": "#/$defs/Overview" },
        "investorItems": { "type": "array", "items": { "$ref": "#/$defs/Item" } },
        "contractorItems": { "type": "array", "items": { "$ref": "#/$defs/ContractorItem" } },
        "transactions": { "type": "array", "items": { "$ref": "#/$defs/Transaction" } },
        "documentLinks": { "type": "array", "items": { "$ref": "#/$defs/Link" } }
      }
    }
  }
}
```

Result envelope bắt buộc `{status: "ok"|"empty", data, meta: Meta}`; `empty` dùng array rỗng cho list và DTO hợp lệ có coverage=missing cho dự án chưa giao dịch, không dùng null cho Project có metadata. Mỗi list dùng row schema tương ứng, `totalRows` integer >=0, `totals` SideSummary, `filtersApplied` Scope, `page` >=1, `pageSize` 1–100. Method `getContractors` trả thêm `contractors: Contractor[]` và hai summary `level1Totals/level2Totals`; tổng không được lấy bằng sum mọi row.

## 10. Mapping field chi tiết và nguồn gốc

Ký hiệu: r = dòng có ID ở nhật ký, i = dòng summary có tên, n = dòng danh bạ. Các range không tự là ID; adapter cấp surrogate ID ổn định theo registry mapping. Các cột helper ngoài danh sách không đi vào số liệu.

| Sheet Excel | Trường gốc | Ý nghĩa | Kiểu | JSON property | Component |
| --- | --- | --- | --- | --- | --- |
| NHAT_KY_TC | B[r] | Ngày ghi sổ, Excel serial | date-time/null | Transaction.bookedAt | TransactionTable/Timeline |
| NHAT_KY_TC | C[r] | Hạng mục | ID lookup | Transaction.itemId | InvestorDetail/Filters |
| NHAT_KY_TC | D[r] | Nội dung, có thể nhiều nghiệp vụ | string/null | Transaction.description | TransactionTable |
| NHAT_KY_TC | E[r] | HĐ gốc phát sinh | integer VND | amounts.contractOriginal | KPI hợp đồng |
| NHAT_KY_TC | F[r] | Giá trị mới sau phụ lục | integer/null | amounts.contractAdjustment | Detail/current contract |
| NHAT_KY_TC | G[r] | Nghiệm thu phát sinh | integer VND | amounts.accepted | KPI nghiệm thu |
| NHAT_KY_TC | H[r] | Hóa đơn đã ghi nhận | integer VND | amounts.invoiced | InvestorTable |
| NHAT_KY_TC | I[r] | Tiền về phát sinh | integer VND | amounts.paid | KPI đã thu |
| NHAT_KY_TC | J[r] | Giữ lại phát sinh | integer VND | amounts.retention | InvestorTable |
| NHAT_KY_TC | K[r] | Ghi chú | string/null | notes | Detail |
| NHAT_KY_TC | L[r] | ID dòng duy nhất tăng dần | integer | sequence + transactionId namespace | History |
| NHAT_KY_TC | M[r] | NHẬP MỚI/SỬA LẦN n/XÓA | enum + raw | operation/operationRaw | History |
| NHAT_KY_TC | N[r] | ID GỐC | namespaced ID | rootTransactionId | History/aggregate |
| NHAT_KY_TC | O[r] | Hiệu lực cache, kiểm lại độc lập | boolean | effective | Ledger/reconciliation |
| NHAT_KY_TC | P[r] | HĐ hiện tại đóng góp tại dòng | integer | computedContractContribution | Reconciliation only |
| NHAT_KY_TC | Q[r] | Hyperlink target/location | allowed link/null | documentLinks | DocumentLinks |
| NHAT_KY_TC | R[r] | Sản lượng phát sinh | integer/null | amounts.production | KPI/table |
| NHAT_KY | B[r] | Ngày ghi sổ | date-time/null | bookedAt | Timeline/TransactionTable |
| NHAT_KY | C[r] | Tên đơn vị, join danh bạ B | ID lookup | contractorId | ContractorDetail |
| NHAT_KY | D[r] | Hạng mục | ID lookup | itemId | ContractorTable |
| NHAT_KY | E[r] | Nội dung hỗn hợp | string/null | description | TransactionTable |
| NHAT_KY | F[r] | HĐ gốc phát sinh | integer VND | amounts.contractOriginal | KPI/table |
| NHAT_KY | G[r] | Giá trị mới sau phụ lục | integer/null | amounts.contractAdjustment | Detail |
| NHAT_KY | H[r] | Nghiệm thu phát sinh | integer VND | amounts.accepted | KPI/table |
| NHAT_KY | I[r] | Tiền trả phát sinh | integer VND | amounts.paid | KPI/table |
| NHAT_KY | J[r] | Ghi chú | string/null | notes | Detail |
| NHAT_KY | K[r]/L[r]/M[r]/N[r] | ID/thao tác/root/hiệu lực | ID/enum/boolean | sequence/operation/rootTransactionId/effective | History |
| NHAT_KY | O[r] | HĐ hiện tại đóng góp | integer | computedContractContribution | Reconciliation only |
| NHAT_KY | P[r] | Link tài liệu | allowed link/null | documentLinks | DocumentLinks |
| NHAT_KY | Q[r] | Sản lượng phát sinh | integer/null | amounts.production | KPI/table |
| NHAT_KY | R[r] | Thầu phụ công ty/khoán nội bộ/của phòng | enum | transactionType | LevelBadge/Filter |
| NHAT_KY | S[r] | Đơn vị mẹ theo tên | ID lookup/null | parentContractorId | HierarchyTable |
| ChuDauTu | B[i]/P[i]/Q[i] | Hạng mục/link/cảnh báo Excel | string/link/code | name/documentLinks/alertCodes | InvestorPage |
| ChuDauTu | C/D/E/F/G/H/I/J/K/L[i] | HĐgốc/HĐmới/SL/NT/chưaNT/HĐơn/TT/giữlại/nợ/nợsaugiữ | integer/null | Metrics tương ứng mục4 | InvestorPage/Overview |
| ChuDauTu | M/N/O[i] | SL/HĐ, TT/HĐ, TT/NT | number/null | Ratios | InvestorTable/KpiCard |
| Thauphu | B/C/D/E/F/P[i] | Tên/item/loại/mẹ/tính tổng/cấp | ID/enum/bool/int | ContractorItem fields | HierarchyTable |
| Thauphu | H/I/J/K/L/M/N/O[i] | HĐgốc/HĐmới/SL/NT/chưaNT/TT/nợHĐ/nợNT | integer/null | Metrics tương ứng | ContractorsPage |
| Thauphu | Q/R/S/T[i] | Khoán mẹ/cấp2/còn lại/cảnh báo | integer/null/code | allocation + alert | AllocationSummary |
| DanhBa_ThauPhu | A[n] | Mã NB-/TQ- ổn định | string/null | Contractor.catalogCode | Detail |
| DanhBa_ThauPhu | B[n]/C[n]/D[n] | Tên/nhóm/liên hệ | string/null | name/group/contact | Filter/Detail |
| DanhBa_ThauPhu | E[n]/F[n] | Dự án đã làm/ghi chú | text/null | pastProjectsText/notes | Detail |
| DM_HangMuc | A[n] | Tên chuẩn danh mục | string | Item.name | ItemSelector |
| DM_HangMuc | D[n] | Từ khóa không dấu, có sai lệch với A | string/helper | searchAlias sau kiểm tra | Search only |
| TP_* | B/C/D/E/F/G/H/I/J/K/L/M | Ngày/item/mô tả/HĐgốc/điềuchỉnh/SL/NT/TT/sốdư/link/note/ID | nhiều kiểu | View từ Transaction, không nguồn cộng mới | ContractorDetail |
| Dashboard | D8:D20/H8:H20/H22 | KPI tham chiếu summary | computed | Golden reconciliation | Overview validation |

Không map DanhBa E thành quan hệ project tự động vì đây là text “Dự án đã làm”. Không lấy Thauphu G “Mở sheet” thành URL chứng từ; đó là hyperlink nội bộ workbook. Mẫu chưa có link chứng từ tài chính ngoài các link điều hướng nội bộ.

## 11. Invariants tính toán và phạm vi

### Hiệu lực, phụ lục và thứ tự

- Stream key = projectId + side + rootTransactionId; ID của hai sổ không chung namespace. So `sequence` số, không so chuỗi “10” < “2”.
- Quy tắc hiệu lực đúng công thức workbook: bản sequence lớn nhất cùng root; nếu XÓA thì không record hiệu lực. So cờ tính lại với O/N cache để phát hiện stale data.
- HĐ gốc = tổng amount gốc của các bản hiệu lực trong một item/cặp đơn vị×item.
- HĐ cập nhật = amount điều chỉnh **>0 của bản hiệu lực ở dòng cuối cùng** trong item/cặp; không có thì tổng HĐ gốc. Công thức Excel xét dòng bên dưới, không sort theo ngày. Kiểm tra sequence tăng theo sourceRow; nếu bị reorder phải ghi mismatch/chốt BA, không tự sửa thứ tự.
- Phụ lục là replacement, không delta. Điều chỉnh 0/âm chưa được Excel hỗ trợ qua điều kiện >0; trả issue và cần BA chốt trước đưa lên dữ liệu thật.
- Không phân loại transaction duy nhất từ description tự do: một dòng có thể vừa NT vừa thanh toán, hoặc ký HĐ có tạm ứng. `eventType` null nếu chưa có mã loại; aggregate dùng amounts, không parse chuỗi mô tả.

### KPI và availability

- paid/accepted, paid/contract, production/contract tính bằng **tổng tử / tổng mẫu cùng scope**, không trung bình tỷ lệ dòng. Mẫu 0 → null/zero_denominator; không NaN/Infinity.
- receivableByAcceptance = accepted − paid; receivableAfterRetention = accepted − paid − retention. Không trừ giữ lại lần nữa trong số dư NT.
- payableByAcceptance = accepted − paid; payableByContract = contractCurrent − paid. Số âm giữ nguyên.
- unaccepted ở dòng Excel để blank khi production=0, ngược lại production−accepted. Tổng G9/L4 bằng SUM các giá trị đã hiện, không nhất thiết bằng tổng production−accepted. Đây là khác biệt quan trọng với công thức giản lược.
- Vì raw production=0 chưa phân biệt đã khai hay mặc định, giữ số0 + provenance.availability=ambiguous_zero; UI thêm ghi chú. unaccepted=null; tổng unaccepted khi toàn dòng blank chuẩn hóa null và ghi raw Excel summary0 trong reconciliation, không tuyên bố không còn khối lượng chờ NT. Nếu BA cần giữ cách tổng Excel, thêm metric riêng `excelDisplayedUnacceptedTotal`, không đổi nghĩa `unaccepted`.
- KPI tổng thiếu một thành phần bắt buộc trả null/coverage=partial, có thể cung cấp knownSubtotal riêng với nhãn; không dùng knownSubtotal làm tổng đầy đủ.
- Mọi phép cộng và kết quả trung gian cần Number.isSafeInteger. Vượt 2^53−1 phải reject out_of_range; contract V2 có thể chuyển tiền thành decimal string/BigInt ở adapter, UI formatter thay theo contract. Không làm tròn để vừa giới hạn.

### Filter, snapshot và danh mục

- Scope tài chính = projectId, itemId, contractorId, transactionType, level; tất cả data region dùng cùng scope + snapshotId. Filter đơn vị chỉ có trên trang thầu phụ/chi tiết, không âm thầm lọc CĐT.
- Search và sort/page là thao tác trình bày; không đổi KPI/totals. `totalRows` tính sau scope và sau search; `totals` tính sau scope, trước search, và có `totalsScope` mô tả rõ. Đã chốt lựa chọn này cho v1; không để adapter tùy ý đổi nghĩa.
- Date filter chỉ tab giao dịch/timeline, không thay KPI lũy kế. Timeline là phân bổ các bản **hiệu lực hiện tại** theo ngày ghi sổ, không phải diễn biến số dư đã biết ở từng thời điểm lịch sử. Thiếu ngày → không dựng trend giả.
- Hạng mục xuyên CĐT/thầu phụ cần crosswalk BA; “Khảo sát” không tự coi là “Khảo sát địa hình”. Cho phép mỗi phía lọc riêng trước khi chốt crosswalk.
- Khoán cấp1/2 có summary riêng. Parent context row để hiển thị hierarchy không tham gia tổng lần nữa. Với parent nhiều item, tổng R của Excel theo tên parent có thể lặp; allocation scope cấp phòng chỉ tính một lần, chờ BA phân bổ theo item.
- Snapshot thật phục vụ đối chiếu riêng; fixture frontend ẩn danh và biến đổi tiền bằng cùng một phép biến đổi xác định trên **raw transaction**, sau đó recompute mọi total/ratio. Không biến đổi KPI từng ô độc lập. So raw extraction với Excel trong kho riêng trước, rồi kiểm bảo toàn công thức của fixture; không gọi tiền fixture là tiền thật.

### Cảnh báo

Phía CĐT giữ thứ tự điều kiện Q của Excel: mọi HĐ/NT/paid đều0 → không có trạng thái tài chính; paid>accepted → PAYMENT_OVER_ACCEPTANCE; accepted=0 và contract>0 → NOT_ACCEPTED; số dư sau giữ lại>0 → RECEIVABLE_BY_ACCEPTANCE; số dư NT>0 → RETENTION_ONLY; còn lại → PAID_IN_FULL (chỉ nói phần đã NT). Dữ liệu thiếu thì MISSING_DATA ưu tiên hơn kết luận “đủ”.

Phía thầu phụ có cảnh báo khoán con vượt mẹ khi allocated−departmentSubcontracted<0. Cảnh báo paid>accepted cho thầu phụ có thể hiển thị attention cùng giải thích tạm ứng, là bổ sung rõ ràng từ amounts chứ không mạo nhận cột cảnh báo sẵn của workbook. Không tạo aging/overdue/deadline/profit alert khi chưa có ngày đến hạn/chi phí thật.
