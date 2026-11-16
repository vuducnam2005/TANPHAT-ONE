import { registry } from "@web/core/registry";
import { FormCompiler } from "@web/views/form/form_compiler";
import { formView } from "@web/views/form/form_view";

/** Tab icons + chatter moved into the "Lịch sử" tab, same pattern as the HR profile. */
const ICONS = {
    overview: "grid_view",
    info: "grid_view",
    config: "memory",
    handover: "swap_horiz",
    repair: "build",
    warranty: "verified",
    software: "apps",
    documents: "folder",
    history: "history",
    proposal_lines: "list_alt",
    proposal_approval: "fact_check",
    proposal_history: "history",
    proposal_notes: "notes",
};

export class TpEquipmentFormCompiler extends FormCompiler {
    compile(node, params) {
        const result = super.compile(node, params);
        for (const notebook of result.querySelectorAll("Notebook")) {
            const pages = {};
            for (const slot of notebook.children) {
                const name = slot.getAttribute("name")?.replaceAll("`", "");
                if (ICONS[name]) {
                    pages[slot.getAttribute("t-set-slot")] = ICONS[name];
                }
            }
            notebook.setAttribute("icons", JSON.stringify(pages));
        }
        const history = result.querySelector(".o_tp_eq_history");
        const chatterBelow = result.querySelector(".o_tp_eq_chatter_below");
        const chatter = result.querySelector(".o-mail-Form-chatter");
        const target = history || chatterBelow;
        if (target && chatter) {
            target.append(chatter);
            chatter.setAttribute("t-if", "!__comp__.env.inDialog");
            chatter.removeAttribute("t-attf-class");
            const component = chatter.querySelector("t[t-component]");
            component?.setAttribute("isChatterAside", "false");
            component?.setAttribute("isInFormSheetBg", history ? "true" : "false");
        }
        return result;
    }
}

registry.category("views").add("tp_equipment_form", { ...formView, Compiler: TpEquipmentFormCompiler });
