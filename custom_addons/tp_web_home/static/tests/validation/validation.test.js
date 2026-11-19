import { describe, expect, test } from "@odoo/hoot";
import { animationFrame, queryAllTexts, queryFirst } from "@odoo/hoot-dom";
import {
    clickSave,
    contains,
    defineModels,
    fields,
    makeServerError,
    models,
    mountView,
    mountWithCleanup,
    onRpc,
} from "@web/../tests/web_test_helpers";
import { ConnectionLostError } from "@web/core/network/rpc";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

class TpValidationCert extends models.Model {
    _name = "tp.validation.cert";
    name = fields.Char({ string: "Tên chứng chỉ", required: true });
    level = fields.Char({ string: "Cấp độ" });
    holder_id = fields.Many2one({ relation: "tp.validation.holder" });
    _records = [];
}

class TpValidationHolder extends models.Model {
    _name = "tp.validation.holder";
    name = fields.Char({ string: "Họ tên", required: true });
    code = fields.Char({ string: "Mã tự sinh", readonly: true });
    start = fields.Date({ string: "Ngày bắt đầu", required: true });
    count = fields.Integer({ string: "Số lượng", required: true });
    active_flag = fields.Boolean({ string: "Đang dùng", required: true });
    note = fields.Char({ string: "Ghi chú" });
    cert_ids = fields.One2many({ string: "Chứng chỉ", relation: "tp.validation.cert", relation_field: "holder_id" });
    _records = [];
}

defineModels([TpValidationCert, TpValidationHolder]);

const ARCH = `
    <form>
        <sheet>
            <group><field name="name"/><field name="code"/><field name="note"/></group>
            <notebook>
                <page string="Thời gian" name="time">
                    <group string="Hiệu lực"><field name="count"/><field name="active_flag"/></group>
                </page>
                <page string="Ngày" name="dates">
                    <group string="Hiệu lực"><field name="start"/></group>
                </page>
                <page string="Chứng chỉ" name="certs">
                    <field name="cert_ids"><list editable="bottom"><field name="name"/><field name="level"/></list></field>
                </page>
            </notebook>
        </sheet>
    </form>`;

const links = () => queryAllTexts(".tp_validation_summary .tp_validation_link");

describe("TP form validation presenter", () => {
    describe.current.tags("desktop");

    test("lists every Odoo-invalid field in the form instead of a vanishing toast", async () => {
        await mountView({ resModel: "tp.validation.holder", type: "form", arch: ARCH });
        expect(".tp_required_hint").toHaveCount(1);
        // Only truly required, editable, non-numeric fields get a star; readonly codes never do.
        expect(".o_form_label:contains('Họ tên') .tp_required_mark").toHaveCount(1);
        expect(".o_form_label:contains('Mã tự sinh') .tp_required_mark").toHaveCount(0);
        expect(".o_form_label:contains('Số lượng') .tp_required_mark").toHaveCount(0);

        await clickSave();
        expect(".o_notification").toHaveCount(0);
        expect(".tp_validation_summary").toHaveCount(1);
        expect(".tp_validation_summary").toHaveAttribute("role", "alert");
        // 0 and False are values, not missing information.
        expect(links()).toEqual(["Họ tên — Thông tin chung", "Ngày bắt đầu — Ngày / Hiệu lực"]);
        expect(".tp_validation_summary").toHaveText(/Vui lòng chọn Ngày bắt đầu\./);
        expect(".o_field_widget[name='name'] .tp_validation_inline").toHaveText("Vui lòng nhập Họ tên.");
        expect(".o_field_widget[name='name']").toHaveAttribute("aria-invalid", "true");
        expect(".o_notebook [role=tab]:contains('Ngày') .tp_validation_count").toHaveText(/^1/);
        expect(".o_notebook [role=tab]:contains('Thời gian') .tp_validation_count").toHaveCount(0);
        expect(".tp_required_hint").toHaveCount(0);

        // Fixing a field updates the list at once, without another save.
        await contains(".o_field_widget[name='name'] input").edit("Nguyễn Văn Thử");
        expect(links()).toEqual(["Ngày bắt đầu — Ngày / Hiệu lực"]);
        expect(".o_field_widget[name='name'] .tp_validation_inline").toHaveCount(0);
        expect(".o_field_widget[name='note'] input").toHaveValue("");
    });

    test("errors and the star use the label the form shows, once per label", async () => {
        await mountView({ resModel: "tp.validation.holder", type: "form", arch: `
            <form><sheet>
                <label for="name" string="Danh xưng"/><h1><field name="name"/></h1>
                <group>
                    <label for="start" string="Thời hạn" invisible="count"/>
                    <label for="start" string="Ngày học" invisible="not count"/>
                    <div><field name="start" nolabel="1"/></div>
                    <field name="count"/>
                </group>
            </sheet></form>` });
        expect(".o_form_label:contains('Danh xưng') .tp_required_mark").toHaveCount(1);
        expect(".o_form_label:contains('Thời hạn') .tp_required_mark").toHaveCount(1);
        await clickSave();
        expect(links()).toEqual(["Danh xưng — Thông tin chung", "Thời hạn — Thông tin chung"]);
        expect(".o_field_widget[name='name'] .tp_validation_inline").toHaveText("Vui lòng nhập Danh xưng.");
        await contains(".o_field_widget[name='count'] input").edit("1");
        expect(links()).toEqual(["Danh xưng — Thông tin chung", "Ngày học — Thông tin chung"]);
    });

    test("clicking an error opens its tab and focuses the field once", async () => {
        await mountView({ resModel: "tp.validation.holder", type: "form", arch: ARCH });
        await contains(".o_field_widget[name='name'] input").edit("Nguyễn Văn Thử");
        await clickSave();
        expect(".o_notebook [role=tab]:contains('Thời gian')").toHaveClass("active");
        await contains(".tp_validation_summary button.tp_validation_link").click();
        await animationFrame();
        expect(".o_notebook [role=tab]:contains('Ngày')").toHaveClass("active");
        expect(".o_field_widget[name='start'] input").toBeFocused();
        expect(".o_field_widget[name='name'] input").toHaveValue("Nguyễn Văn Thử");
    });

    test("sub-table rows are named by table, row number and column, and lead back to the row", async () => {
        await mountView({ resModel: "tp.validation.holder", type: "form", arch: ARCH });
        await contains(".o_field_widget[name='name'] input").edit("Nguyễn Văn Thử");
        await contains(".o_notebook [role=tab]:contains('Ngày')").click();
        await contains(".o_field_widget[name='start'] input").edit("01/02/2026");
        await contains(".o_notebook [role=tab]:contains('Chứng chỉ')").click();
        await contains(".o_field_x2many_list_row_add button").click();
        await contains(".o_selected_row [name='level'] input").edit("B2");
        await clickSave();
        expect(".o_notification").toHaveCount(0);
        expect(links()).toEqual(["Chứng chỉ — dòng 1: Tên chứng chỉ"]);
        expect(".tp_validation_summary").toHaveText(/Vui lòng nhập Tên chứng chỉ\./);
        expect(".o_notebook [role=tab]:contains('Chứng chỉ') .tp_validation_count").toHaveText(/^1/);

        await contains(".o_notebook [role=tab]:contains('Ngày')").click();
        await contains(".tp_validation_summary button.tp_validation_link").click();
        await animationFrame();
        expect(".o_notebook [role=tab]:contains('Chứng chỉ')").toHaveClass("active");
        expect(".o_selected_row [name='name'] input").toBeFocused();
        expect(".o_selected_row [name='level'] input").toHaveValue("B2");
    });

    test("backend rejection stays in the form with its own message and kind", async () => {
        expect.errors(1);
        onRpc("web_save", () => {
            throw makeServerError({ type: "ValidationError", description: "Mã nhân viên đã tồn tại trong công ty." });
        });
        await mountView({ resModel: "tp.validation.holder", type: "form", arch: ARCH });
        await contains(".o_field_widget[name='name'] input").edit("Nguyễn Văn Thử");
        await contains(".o_notebook [role=tab]:contains('Ngày')").click();
        await contains(".o_field_widget[name='start'] input").edit("01/02/2026");
        await clickSave();
        await animationFrame();
        expect.verifyErrors([/RPC_ERROR/]);
        expect(".tp_validation_server").toHaveAttribute("data-kind", "duplicate");
        expect(".tp_validation_server").toHaveText(/Giá trị bị trùng\s+Mã nhân viên đã tồn tại trong công ty\./);
        expect(".o_field_widget[name='name'] input").toHaveValue("Nguyễn Văn Thử");
    });
});

describe("saveError classification", () => {
    const rpc = (name, message) => ({ data: { name: `odoo.exceptions.${name}`, message } });

    test("keeps backend wording and separates every kind", () => {
        expect(saveError(rpc("ValidationError", "Số CCCD đã được sử dụng."))).toEqual({
            kind: "duplicate", title: "Giá trị bị trùng", message: "Số CCCD đã được sử dụng." });
        expect(saveError(rpc("ValidationError", "Vui lòng nhập Ngày vào làm.")).kind).toBe("required");
        expect(saveError(rpc("ValidationError", "Ngày kết thúc phải sau ngày bắt đầu.")).kind).toBe("date");
        expect(saveError(rpc("ValidationError", "Số điện thoại chỉ gồm chữ số.")).kind).toBe("validation");
        expect(saveError(rpc("AccessError", "Bạn không có quyền sửa hồ sơ này."))).toEqual({
            kind: "access", title: "Không có quyền lưu", message: "Bạn không có quyền sửa hồ sơ này." });
        expect(saveError(rpc("MissingError", "")).kind).toBe("missing");
        expect(saveError(rpc("UserError", "Kỳ đã khóa.")).kind).toBe("business");
        expect(saveError(new ConnectionLostError("/web/dataset/call_kw")).kind).toBe("connection");
    });

    test("names the action the user tried; typed-data wording stays only for saves", () => {
        expect(saveError(rpc("AccessError", ""), { verb: "xóa", note: "Danh sách chưa thay đổi." })).toEqual({
            kind: "access", title: "Không có quyền xóa",
            message: "Tài khoản của bạn không có quyền thực hiện thao tác này. Vui lòng liên hệ người quản trị.",
            note: "Danh sách chưa thay đổi." });
        expect(saveError(rpc("UserError", "Chọn Dự án trước."), { verb: "thêm mới" }).title).toBe("Máy chủ từ chối thêm mới");
        expect(saveError(new ConnectionLostError("/web/dataset/call_kw"), { verb: "mở hồ sơ", write: false }).message)
            .toBe("Chưa kết nối được máy chủ nên chưa mở hồ sơ được. Kiểm tra kết nối rồi thử lại.");
        expect(saveError(new ConnectionLostError("/web/dataset/call_kw"), { verb: "sắp xếp" }).message)
            .toInclude("Chưa xác nhận được kết quả sắp xếp.");
        const system = saveError({ data: { name: "builtins.KeyError", message: "'x_secret_field'" } }, { verb: "sắp xếp" });
        expect([system.title, system.message]).toEqual(["Lỗi hệ thống khi sắp xếp",
            "Hệ thống chưa sắp xếp được. Thử lại sau ít phút hoặc liên hệ người quản trị kèm thời điểm xảy ra lỗi."]);
        expect(JSON.stringify(system)).not.toInclude("x_secret_field");
        expect("note" in saveError(rpc("UserError", "Kỳ đã khóa."))).toBe(false);
    });

    test("never shows technical details of unexpected failures", () => {
        const error = saveError({ data: { name: "builtins.KeyError", message: "'x_secret_field'", debug: "Traceback..." } });
        expect(error.kind).toBe("system");
        expect(JSON.stringify(error)).not.toInclude("x_secret_field");
        expect(JSON.stringify(error)).not.toInclude("Traceback");
    });
});

describe("InlineErrors for custom forms", () => {
    test("renders caller errors, focuses the field and keeps the server message", async () => {
        await mountWithCleanup(`
            <div class="o_tp_hr_my_profile">
                <label for="tp_demo_name">Tên</label><input id="tp_demo_name"/>
            </div>`);
        await mountWithCleanup(InlineErrors, {
            target: queryFirst(".o_tp_hr_my_profile"),
            props: {
                errors: [{ id: "tp_demo_name", label: "Tên", location: "Thông tin chung", message: "Vui lòng nhập Tên." }],
                server: { kind: "access", title: "Không có quyền lưu", message: "Liên hệ người quản trị." },
                attempt: 1,
            },
        });
        expect(".tp_validation_summary").toHaveCount(1);
        expect(links()).toEqual(["Tên — Thông tin chung"]);
        expect(".tp_validation_server").toHaveAttribute("data-kind", "access");
        await contains(".tp_validation_summary button.tp_validation_link").click();
        expect("#tp_demo_name").toBeFocused();
    });

    test("screens that save nothing typed replace the save wording", async () => {
        await mountWithCleanup(InlineErrors, {
            props: {
                errors: [{ id: "tp_demo_project", label: "Dự án", location: "Bộ lọc", message: "Chọn Dự án." }],
                intro: "Chưa mở được màn thêm mới. Vui lòng kiểm tra", note: "Bộ lọc được giữ nguyên.", attempt: 1,
            },
        });
        expect(".tp_validation_summary strong").toHaveText("Chưa mở được màn thêm mới. Vui lòng kiểm tra 1 thông tin:");
        expect(".tp_validation_summary small").toHaveText("Bộ lọc được giữ nguyên.");
    });

    test("a classified action error carries its own closing line", async () => {
        await mountWithCleanup(InlineErrors, {
            props: { errors: [], server: { kind: "business", title: "Máy chủ từ chối xóa", message: "Mục đã khóa.", note: "Danh sách chưa thay đổi." } },
        });
        expect(".tp_validation_server").toHaveText(/Máy chủ từ chối xóa\s+Mục đã khóa\./);
        expect(".tp_validation_summary small").toHaveText("Danh sách chưa thay đổi.");
    });

    test("renders nothing while there is nothing to fix", async () => {
        await mountWithCleanup(InlineErrors, { props: { errors: [] } });
        expect(".tp_validation_summary").toHaveCount(0);
    });
});
