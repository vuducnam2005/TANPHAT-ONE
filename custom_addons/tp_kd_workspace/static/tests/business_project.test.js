import { describe, expect, queryOne, test } from "@odoo/hoot";
import { contains, defineModels, fields, models, mountView, onRpc } from "@web/../tests/web_test_helpers";
import "@tp_kd_workspace/business_project/business_project";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";

class BpRelated extends models.Model {
    name = fields.Char();
    _records = [{ id: 1, name: "Cầu Tân Phát " + "khảo sát thiết kế tuyến kết nối ".repeat(10) }, { id: 2, name: "Cầu khác" }];
}
class BpDossier extends models.Model {
    name = fields.Char();
    related_id = fields.Many2one({ relation: "bp.related" });
    _records = [{ id: 1, name: "Hồ sơ", related_id: 1 }];
}
defineModels([BpRelated, BpDossier]);
defineMailModels();
const arch = '<form><field name="name"/><field name="related_id" widget="tp_kd_bp_many2one" options="{\'no_create\': True}"/></form>';
describe("business project related-name disclosure", () => {
    test("disclosure preserves native autocomplete and makes no RPC or write", async () => {
        await mountView({ type: "form", resModel: "bp.dossier", resId: 1, arch });
        const input = queryOne('[name="related_id"] input');
        onRpc(() => expect.step("rpc"));
        await contains('.tp_kd_bp_preview summary').click();
        expect('.tp_kd_bp_full_name').toHaveText(("Cầu Tân Phát " + "khảo sát thiết kế tuyến kết nối ".repeat(10)).trim());
        expect(queryOne('[name="related_id"] input')).toBe(input);
        expect('.tp_kd_bp_preview[open]').toHaveCount(1);
        expect.verifySteps([]);
    });
    test("native autocomplete selection updates the full name", async () => {
        await mountView({ type: "form", resModel: "bp.dossier", resId: 1, arch });
        await contains('[name="related_id"] input').click();
        await contains('.o-autocomplete--dropdown-item', { text: "Cầu khác" }).click();
        await contains('.tp_kd_bp_preview summary').click();
        expect('.tp_kd_bp_full_name').toHaveText("Cầu khác");
        expect('.o_form_button_save').toHaveCount(1);
    });
    test("empty value has no misleading disclosure; readonly stays native", async () => {
        await mountView({ type: "form", resModel: "bp.dossier", arch });
        expect('.tp_kd_bp_preview').toHaveCount(0);
        expect('[name="related_id"] input').toHaveCount(1);
    });
    test("display name is escaped text", async () => {
        BpRelated._records[0].name = '<img src=x onerror="alert(1)">';
        await mountView({ type: "form", resModel: "bp.dossier", resId: 1, arch });
        await contains('.tp_kd_bp_preview summary').click();
        expect('.tp_kd_bp_full_name img').toHaveCount(0);
        expect('.tp_kd_bp_full_name').toHaveText('<img src=x onerror="alert(1)">');
    });
    test("project secondary links use one native dropdown and object callbacks", async () => {
        onRpc("action_one", () => { expect.step("one"); return false; });
        await mountView({ type: "form", resModel: "bp.dossier", resId: 1, arch: `
            <form js_class="tp_kd_bp_project_form"><sheet><field name="name"/>
                <div name="button_box"><button name="action_one" type="object" string="Một"/>
                    <button name="action_two" type="object" string="Hai"/></div>
            </sheet></form>` });
        expect('.o_button_more').toHaveCount(1);
        expect('.o_button_more').toHaveText("Hồ sơ liên quan");
        expect('button[name="action_one"]').toHaveCount(0);
        await contains('.o_button_more').click();
        expect('.tp_kd_bp_related_menu button').toHaveCount(2);
        await contains('button[name="action_one"]').click();
        expect.verifySteps(["one"]);
    });
});
