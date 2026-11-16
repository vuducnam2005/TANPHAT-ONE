/** @odoo-module **/

const SEARCHABLE_TYPES = new Set([
    "char",
    "text",
    "many2one",
    "selection",
    "boolean",
    "date",
    "datetime",
]);

/**
 * Build a native `<search>` XML string for x2many relation filter dialogs from list columns and field metadata.
 */
export function buildRelationSearchArch(listArchEl, relatedFields = {}) {
    const search = document.createElement("search");
    const seen = new Set();
    for (const node of listArchEl.querySelectorAll("field")) {
        const name = node.getAttribute("name");
        if (!name || seen.has(name)) continue;
        seen.add(name);
        const field = relatedFields[name];
        if (field && field.searchable !== false && SEARCHABLE_TYPES.has(field.type)) {
            const fieldNode = document.createElement("field");
            fieldNode.setAttribute("name", name);
            search.appendChild(fieldNode);
        }
    }
    return new XMLSerializer().serializeToString(search);
}
