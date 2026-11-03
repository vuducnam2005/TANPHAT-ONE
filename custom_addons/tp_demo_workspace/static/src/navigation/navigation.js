import { Component, computed, onWillUnmount, proxy, signal, t, useListener, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { activeDestination, buildCatalog, filterCatalog } from "./navigation_catalog";

function useDemoCatalog(component) {
    component.menu = useService("menu");
    component.action = useService("action");
    component.catalog = computed(() => {
        const app = component.menu.getCurrentApp();
        return buildCatalog(app && component.menu.getMenuAsTree(app.id));
    });
    component.selection = proxy({ action: component.action.currentController?.action });
    useListener(component.env.bus, "ACTION_MANAGER:UPDATE", (event) => {
        const action = event.detail?.componentProps?.action;
        if (action) {
            component.selection.action = action;
        }
    });
    useListener(component.env.bus, "ACTION_MANAGER:UI-UPDATED", () => {
        component.selection.action = component.action.currentController?.action;
    });
    component.active = computed(() => activeDestination(component.catalog(), component.selection.action));
}

export class DemoModuleDialog extends Component {
    static template = "tp_demo_workspace.ModuleDialog";
    static components = { Dialog };
    props = useProps({ close: t.function() });
    search = signal.ref();

    setup() {
        useDemoCatalog(this);
        this.state = proxy({ query: "" });
        this.results = computed(() => filterCatalog(this.catalog(), this.state.query));
        useAutofocus({ ref: this.search });
    }

    async select(menu) {
        await this.props.close();
        return this.menu.selectMenu(menu);
    }

    updateQuery(query) {
        this.state.query = query;
        // A filtered group may be shorter than the previous scrolled catalog.
        // Start at its heading instead of leaving it underneath the sticky search.
        this.search()?.closest(".o_tp_demo_module_body")?.scrollTo({ top: 0 });
    }

    clearSearch() {
        this.updateQuery("");
        this.search()?.focus();
    }
}

export class DemoCatalogButton extends Component {
    static template = "tp_demo_workspace.CatalogButton";

    setup() {
        this.dialog = useService("dialog");
        this.closeDialog = null;
        onWillUnmount(() => this.closeDialog?.());
    }

    open(event) {
        const trigger = event.currentTarget;
        this.closeDialog = this.dialog.add(DemoModuleDialog, {}, {
            onClose: () => {
                this.closeDialog = null;
                if (trigger.isConnected) {
                    trigger.focus();
                }
            },
        });
    }
}

export class DemoNavigation extends Component {
    static template = "tp_demo_workspace.Navigation";
    static components = { Dropdown, DropdownItem };

    setup() {
        useDemoCatalog(this);
    }

    href(menu) {
        // Same native path contract as NavBar.getMenuItemHref, using server menu data.
        return `/odoo/${menu.actionPath || "action-" + menu.actionID}`;
    }

    select(menu) {
        return this.menu.selectMenu(menu);
    }
}

// NavBar has no component registry extension point. Register only the two
// template components; do not patch its setup/adapt/router/menu behavior.
patch(NavBar, { components: { ...NavBar.components, DemoCatalogButton, DemoNavigation } });
