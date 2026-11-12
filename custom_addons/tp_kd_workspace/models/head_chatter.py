"""Native CRM chatter remains readable; HEAD writes use audited commands."""

from odoo import models


class Opportunity(models.Model):
    _inherit = 'crm.lead'

    def _store_thread_fields(self, res, *, request_list, **kwargs):
        super()._store_thread_fields(res, request_list=request_list, **kwargs)
        if res.is_for_current_user():
            def is_head(thread):
                return thread.sudo(False)._kd_head()

            res.attr('tpKdHeadContentCommand', is_head)
            res.attr('hasWriteAccess', False, predicate=is_head)
            res.attr('canPostOnReadonly', False, predicate=is_head)
