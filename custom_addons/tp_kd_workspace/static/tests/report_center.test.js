import { describe, expect, test } from "@odoo/hoot";
import { contains, defineModels, fields, models, mountView, onRpc, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";
import { user } from "@web/core/user";
import {
    computePeriodDates,
    readReportState,
    readVisibleColumns,
    reportColumnKey,
    reportStateKey,
    writeReportState,
    writeVisibleColumns,
} from "@tp_kd_workspace/report_center/report_center";

class KdReportCenterMock extends models.Model {
    _name = "tp.kd.report.center";
    name = fields.Char();
    _records = [{ id: 1, name: "Báo cáo KH-KD" }];
}

defineModels([KdReportCenterMock]);
defineMailModels();

function samplePayload(reportKey = "R01", titleSuffix = "Initial") {
    return {
        report_key: reportKey,
        report_meta: {
            key: reportKey,
            code: reportKey,
            title: `Dự án và hợp đồng (${titleSuffix})`,
            short_title: "Dự án & Hợp đồng",
            question: "Câu hỏi quản trị kiểm thử HOOT",
            date_field_label: "effective_date",
            basis_note: "Không cộng trùng phiên bản",
            unverified_note: "Chưa có chứng từ quyết toán",
        },
        catalog: [
            { key: "R01", code: "R01", title: "Dự án và hợp đồng", short_title: "Dự án & Hợp đồng" },
            { key: "R02", code: "R02", title: "Cơ hội và hồ sơ thầu", short_title: "Cơ hội & Hồ sơ thầu" },
        ],
        updated_at: "12:00:00 09/11/2026",
        today: "2026-11-09",
        user_name: "Người kiểm thử",
        financial_project_count: 1,
        accessible_project_count: 1,
        options: {
            projects: [{ id: 10, label: "[DA-01] Dự án cầu A" }],
            allow_unassigned_project: false,
            owners: [{ id: 5, label: "Chủ nhiệm A" }],
            statuses: [{ value: "life:effective", label: "Đang hiệu lực" }],
            sub_filter_title: "Loại HĐ",
            sub_filters: [{ value: "revenue", label: "Doanh thu" }],
            group_by_options: [{ value: "project", label: "Theo Dự án" }],
            sort_options: [{ value: "code", label: "Mã HĐ" }],
            page_sizes: [10, 20, 50, 100],
        },
        applied_filters: {
            period_preset: "",
            period_label: "Tất cả kỳ",
            date_from: "",
            date_to: "",
            project_id: "",
            project_label: "Tất cả dự án trong quyền",
            owner_id: "",
            owner_label: "Tất cả người phụ trách",
            status: "",
            status_label: "Tất cả trạng thái",
            sub_filter: "",
            sub_filter_label: "Tất cả phân loại",
            group_by: "project",
            group_by_label: "Theo Dự án",
            sort_by: "code",
            sort_dir: "asc",
            search: "",
        },
        applied_chips: [{ key: "period", label: "Kỳ: Tất cả kỳ" }],
        summary_cards: [
            { key: "contracts", label: "Tổng số hợp đồng", value: "1", unit: "hợp đồng", note: titleSuffix, tone: "info" },
        ],
        exclusion_info: { note: "Tất cả khoản đủ điều kiện." },
        chart: {
            kind: "donut",
            title: "Biểu đồ kiểm thử",
            subtitle: "Mô tả",
            unit: "hợp đồng",
            total: 1,
            items: [{ key: "effective", label: "Đang hiệu lực", value: 1, display: "1 HĐ", tone: "done", percent: 100 }],
        },
        columns: [
            { key: "code", label: "Mã HĐ", align: "center", kind: "code", optional: false, default_visible: true, sortable: true },
            { key: "name", label: "Tên hợp đồng", align: "left", kind: "link", optional: false, default_visible: true, sortable: true },
            { key: "partner_label", label: "Đối tác", align: "left", kind: "text", optional: true, default_visible: false, sortable: true },
            { key: "effective_money", label: "Giá trị hiệu lực", align: "right", kind: "money", optional: false, default_visible: true, sortable: false },
        ],
        money_keys: ["effective_money"],
        groups: [
            { key: "10", label: "[DA-01] Dự án cầu A", count: 1, metrics: [{ label: "Hiệu lực", value: "1 HĐ" }] },
        ],
        rows: [
            {
                id: "contract:1",
                res_model: "tp.contract",
                res_id: 1,
                code: `HD-${titleSuffix}`,
                name: `Hợp đồng ${titleSuffix}`,
                partner_label: "Đối tác A",
                effective_money: { state: "confirmed", display: "1.000.000.000 VND (trước thuế)" },
                drill: { kind: "record", payload: { model: "tp.contract", res_id: 1 } },
            },
        ],
        totals_row: {
            label: "Tổng cộng (1 hợp đồng)",
            cells: { effective_money: { state: "confirmed", display: "1.000.000.000 VND (trước thuế)" } },
        },
        pagination: { page: 1, page_size: 20, total_rows: 1, total_pages: 1, start_row: 1, end_row: 1 },
    };
}

describe("KD-REPORT-001 Report Center", () => {
    test("period preset helper computes exact month/quarter/year boundaries", () => {
        expect(computePeriodDates("this_month", "2026-11-09")).toEqual({
            date_from: "2026-11-01",
            date_to: "2026-11-30",
        });
        expect(computePeriodDates("this_quarter", "2026-11-09")).toEqual({
            date_from: "2026-10-01",
            date_to: "2026-12-31",
        });
        expect(computePeriodDates("this_year", "2026-11-09")).toEqual({
            date_from: "2026-01-01",
            date_to: "2026-12-31",
        });
    });

    test("session state and column visibility isolate db/user and keep mandatory columns", () => {
        const k1 = reportStateKey();
        writeReportState({ reportKey: "R04", page: 2 });
        expect(readReportState().reportKey).toBe("R04");

        patchWithCleanup(session, { db: "other_db_hoot" });
        expect(reportStateKey()).not.toBe(k1);
        expect(readReportState()).toBe(null);

        patchWithCleanup(user, { userId: 77777 });
        const cols = [
            { key: "code", optional: false, default_visible: true },
            { key: "partner_label", optional: true, default_visible: false },
        ];
        expect(readVisibleColumns("R01", cols)).toEqual({ code: true, partner_label: false });
        writeVisibleColumns("R01", { code: false, partner_label: true });
        // Mandatory column `code` cannot be hidden even if localStorage has `code: false`
        expect(readVisibleColumns("R01", cols)).toEqual({ code: true, partner_label: true });
        expect(reportColumnKey("R01")).toInclude("77777");
    });

    test("pending vs applied filters, race condition guard, and access error state wipe", async () => {
        browser.sessionStorage.clear();
        let resolveSlow;
        const slowDef = new Promise((resolve) => {
            resolveSlow = resolve;
        });
        let callIndex = 0;

        onRpc("get_kd_report", async ({ args }) => {
            callIndex += 1;
            if (callIndex === 1) {
                return samplePayload(args[0], "First");
            }
            if (callIndex === 2) {
                await slowDef;
                return samplePayload(args[0], "StaleSlow");
            }
            if (callIndex === 3) {
                return samplePayload(args[0], "FreshFast");
            }
            const err = new Error("AccessError: Bạn không có quyền truy cập");
            err.name = "AccessError";
            throw err;
        });

        await mountView({
            type: "form",
            resModel: "tp.kd.report.center",
            resId: 1,
            arch: '<form js_class="tp_kd_report_center"><sheet/></form>',
        });

        expect(".o_tp_kd_rc").toHaveCount(1);
        expect(".o_tp_kd_rc_row_link").toHaveText("Hợp đồng First");

        // Changing a filter marks pending without calling RPC until Apply is clicked
        await contains(".o_tp_kd_rc_preset_btn:nth-of-type(2)").click();
        expect(".o_tp_kd_rc_pending_notice").toHaveCount(1);
        expect(callIndex).toBe(1);

        // Trigger call #2 (slow) via Apply, then immediately trigger call #3 (fast) via Refresh
        contains(".o_tp_kd_rc_btn_apply").click();
        await contains(".o_tp_kd_rc_btn_refresh").click();
        expect(".o_tp_kd_rc_row_link").toHaveText("Hợp đồng FreshFast");

        // Now resolve slow call #2 -> must be ignored by seq guard!
        resolveSlow();
        await Promise.resolve();
        expect(".o_tp_kd_rc_row_link").toHaveText("Hợp đồng FreshFast");

        // Call #4 throws AccessError -> must wipe data and show denied banner
        await contains(".o_tp_kd_rc_btn_refresh").click();
        expect(".o_tp_kd_rc_denied").toHaveCount(1);
        expect(".o_tp_kd_rc_body").toHaveCount(0);
    });
});
