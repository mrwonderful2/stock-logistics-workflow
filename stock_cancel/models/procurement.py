# -*- coding: utf-8 -*-
# Copyright 2012 Andrea Cometa
# Copyright 2013 Agile Business Group sagl
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.multi
    def cancel(self):
        propagated_procurements = self.propagate_cancels()
        for rec in self:
            rec.write({'state': 'cancel'})
        for rec in propagated_procurements:
            rec.write({'state': 'cancel'})
        return super(ProcurementOrder, self).cancel()
