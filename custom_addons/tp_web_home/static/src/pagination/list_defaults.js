import { patch } from "@web/core/utils/patch";
import { ListArchParser } from "@web/views/list/list_arch_parser";

// Product-wide initial page size, including native lists, grouped lists and embedded relation tables.
// A controller can still restore the user's current page or apply a later page-size selection.
patch(ListArchParser.prototype, {
    parse(...args) {
        return { ...super.parse(...args), limit: 100, groupsLimit: 100 };
    },
});
