import json

from odoo.http import request, route
from odoo.tools.translate import code_translations

from odoo.addons.spreadsheet_dashboard.controllers.dashboards_controllers import (
    DashboardDataRoute,
)


class VietnameseDashboardData(DashboardDataRoute):
    @route()
    def get_dashboard_data(self, dashboard):
        response = super().get_dashboard_data(dashboard)
        if request.env.lang in ('vi', 'vi_VN'):
            data = response.get_json()
            # Native sample responses omit the namespace used by spreadsheet _t.
            if data.get('is_sample') and not data.get('translation_namespace'):
                namespace = dashboard._get_dashboard_translation_namespace()
                data['translation_namespace'] = namespace
                if namespace:
                    terms = {term['id']: term['string'] for term in code_translations.get_web_translations(namespace, request.env.lang)['messages']}
                    # Static sample headings are literals rather than _t formulas.
                    for sheet in data['snapshot'].get('sheets', []):
                        cells = sheet.get('cells', {})
                        for address, value in cells.items():
                            if isinstance(value, str) and value in terms:
                                cells[address] = terms[value]
                response.set_data(json.dumps(data))
        return response
