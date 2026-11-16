import { onWillStart, onWillUnmount, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { render } from "@web/owl2/utils";
import { HierarchyController } from "@web_hierarchy/hierarchy_controller";
import { hrEmployeeHierarchyView } from "@hr/views/hr_employee_hierarchy/hr_employee_hierarchy_view";
import { HrEmployeeHierarchyModel } from "@hr/views/hr_employee_hierarchy/hr_employee_hierarchy_model";

const EXEC_DEPT_NAMES = new Set(["ban giám đốc", "ban giam doc", "ban lãnh đạo", "ban lanh dao"]);

export function isExecutiveDepartmentName(name) {
    return EXEC_DEPT_NAMES.has(String(name || "").trim().toLocaleLowerCase("vi"));
}

export class TpHrHierarchyModel extends HrEmployeeHierarchyModel {
    get context() {
        return { ...super.context, tp_hr_hierarchy: true };
    }

    _formatData(data) {
        const orderIndex = new Map(data.map((record, index) => [record.id, index]));
        const formatted = super._formatData(data);
        return formatted.sort((a, b) => (orderIndex.get(a.id) ?? 0) - (orderIndex.get(b.id) ?? 0));
    }
}

export class HrHierarchyController extends HierarchyController {
    static template = "tp_hr_workspace.HierarchyView";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = proxy({ departments: [], departmentId: "" });
        this.tpDeptGroupId = null;

        const searchModel = this.env.searchModel;
        const onSearchUpdate = () => this._syncDepartmentFromSearchModel();
        if (searchModel) {
            searchModel.addEventListener("update", onSearchUpdate);
            onWillUnmount(() => searchModel.removeEventListener("update", onSearchUpdate));
        }

        onWillStart(async () => {
            await this._loadDepartments();
            this._syncDepartmentFromSearchModel();
        });
    }

    async _loadDepartments() {
        try {
            const rows = await this.orm.searchRead(
                "hr.department",
                [["active", "=", true]],
                ["id", "name"],
                { context: this.props.context }
            );
            this.state.departments = rows.sort((a, b) => {
                const rankA = isExecutiveDepartmentName(a.name) ? 0 : 1;
                const rankB = isExecutiveDepartmentName(b.name) ? 0 : 1;
                return rankA - rankB || String(a.name || "").localeCompare(String(b.name || ""), "vi") || a.id - b.id;
            });
        } catch {
            this.state.departments = [];
        }
    }

    _syncDepartmentFromSearchModel() {
        const searchModel = this.env.searchModel;
        if (!searchModel || !this.tpDeptGroupId) {
            if (this.state.departmentId) {
                this.state.departmentId = "";
                render(this);
            }
            return;
        }
        const active = searchModel.facets.some((facet) => facet.groupId === this.tpDeptGroupId);
        if (!active) {
            this.tpDeptGroupId = null;
            this.state.departmentId = "";
            render(this);
        }
    }

    _clearDepartmentFacet() {
        const searchModel = this.env.searchModel;
        if (searchModel && this.tpDeptGroupId) {
            const groupId = this.tpDeptGroupId;
            this.tpDeptGroupId = null;
            searchModel.deactivateGroup(groupId);
        }
    }

    changeDepartment(ev) {
        const value = ev.target.value;
        const searchModel = this.env.searchModel;
        if (!searchModel) return;
        this._clearDepartmentFacet();
        if (!value) {
            this.state.departmentId = "";
            return;
        }
        const deptId = Number(value);
        const dept = this.state.departments.find((row) => row.id === deptId);
        if (!dept) return;
        this.state.departmentId = String(dept.id);
        const label = `Phòng ban: ${dept.name}`;
        searchModel.createNewFilters([
            {
                description: label,
                domain: [["department_id", "=", dept.id]],
            },
        ]);
        const created = Object.values(searchModel.searchItems).findLast(
            (item) => item.type === "filter" && item.description === label
        );
        this.tpDeptGroupId = created?.groupId ?? null;
    }

    clearDepartment() {
        this._clearDepartmentFacet();
        this.state.departmentId = "";
    }
}

registry.category("views").add("tp_hr_hierarchy", {
    ...hrEmployeeHierarchyView,
    Model: TpHrHierarchyModel,
    Controller: HrHierarchyController,
});
