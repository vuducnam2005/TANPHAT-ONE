import { expect, test } from "@odoo/hoot";
import { HrProfileController, HrProfileCompiler } from "@tp_hr_workspace/profile/employee_profile";
import { TpHrMyProfile } from "@tp_hr_workspace/my_profile/my_profile";

test("HR save stays editable on validation failure; success returns to reading", async () => {
    const controller = Object.create(HrProfileController.prototype);
    const modes = [];
    controller.model = {root: {switchMode: async mode => modes.push(mode)}};
    controller.saveButtonClicked = async () => false;
    await controller.saveProfile();
    expect(modes).toEqual([]);
    controller.saveButtonClicked = async () => true;
    await controller.saveProfile();
    expect(modes).toEqual(["readonly"]);
});

test("HR notebook icons follow native page slots and preserve unknown pages", () => {
    const xml = new DOMParser().parseFromString('<form><notebook><page name="page_overview" string="Tổng quan"><div/></page><page name="work_information" string="Công việc"><div/></page><page name="other" string="Khác"><div/></page></notebook></form>', 'text/xml');
    const result = new HrProfileCompiler({form: xml.documentElement}).compile('form');
    const notebook = result.querySelector('Notebook');
    const icons = JSON.parse(notebook.getAttribute('icons'));
    const slots = [...notebook.children];
    expect(icons[slots[0].getAttribute('t-set-slot')]).toBe('grid_view');
    expect(icons[slots[1].getAttribute('t-set-slot')]).toBe('work');
    expect(icons[slots[2].getAttribute('t-set-slot')]).toBe(undefined);
});

test("MyProfile history filters separate profile, role/transfer and account entries", () => {
    const comp = Object.create(TpHrMyProfile.prototype);
    comp.state = {
        historyFilter: "all",
        data: {
            history: [
                { id: 1, filter_group: "profile" },
                { id: 2, filter_group: "role" },
                { id: 3, filter_group: "account" },
            ],
        },
    };
    expect(comp.filteredHistory.map((r) => r.id)).toEqual([1, 2, 3]);
    comp.setHistoryFilter("role");
    expect(comp.filteredHistory.map((r) => r.id)).toEqual([2]);
    comp.setHistoryFilter("account");
    expect(comp.filteredHistory.map((r) => r.id)).toEqual([3]);
});

test("MyProfile delete/security failures stay in the card the user acted on, never a toast", async () => {
    const comp = Object.create(TpHrMyProfile.prototype);
    comp.state = { activeTab: "resume", actionError: null, actionAttempt: 0 };
    comp.confirmDiscard = async () => true;
    comp.notification = { add: (message, { type }) => expect.step(type) };
    comp.orm = { call: async () => { throw { data: { name: "odoo.exceptions.UserError", message: "Kỹ năng đang được dùng." } }; } };
    await comp.deleteSkill({ id: 5, skill_name: "AutoCAD" });
    expect.verifySteps([]);
    expect(comp.actionErrorFor("resume")).toBe(null);
    expect(comp.actionErrorFor("skill")).toEqual({ area: "skill", kind: "business", title: "Máy chủ từ chối xóa",
        message: "Kỹ năng đang được dùng.", note: "Danh sách chưa thay đổi." });
    expect(comp.state.actionAttempt).toBe(1);
    comp.orm = { call: async () => { throw { data: { name: "odoo.exceptions.AccessError", message: "" } }; } };
    await comp.openAccountSecurityPreferences();
    expect(comp.actionErrorFor("skill")).toBe(null);
    expect(comp.actionErrorFor("security").title).toBe("Không có quyền mở cài đặt bảo mật");
    comp.setTab("account");
    expect(comp.state.actionError).toBe(null);
});

test("MyProfile popups list the backend rules that block saving, only after a save attempt", () => {
    const comp = Object.create(TpHrMyProfile.prototype);
    comp.state = { draftAttempted: false, resumeDraft: { name: " ", date_start: "", date_end: "" }, skillDraft: null };
    expect(comp.draftErrors).toEqual([]);
    comp.state.draftAttempted = true;
    expect(comp.draftErrors.map((e) => [e.id, e.message])).toEqual([
        ["tp_resume_name", "Vui lòng nhập tiêu đề mục hồ sơ năng lực."],
        ["tp_resume_start", "Vui lòng chọn ngày bắt đầu."],
    ]);
    Object.assign(comp.state.resumeDraft, { name: "Kỹ sư", date_start: "2026-05-01", date_end: "2026-01-01" });
    expect(comp.draftErrors.map((e) => e.id)).toEqual(["tp_resume_end"]);
    expect(comp.draftFieldError("tp_resume_end")).toInclude("lớn hơn hoặc bằng");
    comp.state.resumeDraft.date_end = "";
    expect(comp.draftErrors).toEqual([]);
    comp.state.resumeDraft = null;
    comp.state.skillDraft = { skill_type_id: 3, skill_id: "", skill_level_id: 0 };
    expect(comp.draftErrors.map((e) => e.label)).toEqual(["Kỹ năng", "Mức độ"]);
    expect(comp.draftErrors.every((e) => e.location === "Hồ sơ và năng lực")).toBe(true);
});
