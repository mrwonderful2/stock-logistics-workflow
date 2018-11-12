# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    qty_loc_lot = fields.Float(
        string="Qty available (lot)",
        compute='_compute_qty_loc_lot',
    )

    @api.depends('location_id', 'lot_id', 'product_uom_id')
    def _compute_qty_loc_lot(self):
        quant_obj = self.env['stock.quant']
        for rec in self:
            if rec.lot_id and rec.location_id:
                quants = quant_obj.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', 'child_of', rec.location_id.id),
                    ('lot_id',  '=', rec.lot_id.id),
                ])
                qty = sum(quants.mapped('quantity'))
                uom = quants.mapped('product_uom_id')
                rec.qty_loc_lot = uom._compute_quantity(
                    qty, rec.product_uom_id)
            else:
                rec.qty_loc_lot = 0.0
