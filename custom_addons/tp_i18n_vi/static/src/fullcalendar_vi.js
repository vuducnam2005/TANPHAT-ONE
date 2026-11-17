/** @odoo-module ignore **/
(() => {
    // Upstream vi lacks the long label and inherits the English "Week".
    const vietnamese = FullCalendar.globalLocales.find((locale) => locale.code === "vi");
    if (vietnamese) {
        vietnamese.weekTextLong = "Tuần";
    }
})();
