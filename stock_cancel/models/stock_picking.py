# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Andrea Cometa All Rights Reserved.
#                       www.andreacometa.it
#                       openerp@andreacometa.it
#    Copyright (C) 2013 Agile Business Group sagl (<http://www.agilebg.com>)
#    Ported to new API by Alexis de Lattre <alexis.delattre@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models, exceptions, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def cancel_valuation_moves(self):
        self.ensure_one()
        account_moves = self.env['account.move'].search(
            [('ref', '=', self.name)])
        account_moves.button_cancel()
        return account_moves

    def _check_restrictions(self):
        # returned_move_ids in stock.move
        # split_from in stock.move
        if self.backorder_id:
            raise exceptions.UserError(
                _('Not Allowed, picking has backorder.'))  # noqa

    @api.multi
    def action_revert_done(self):
        for picking in self:
            picking._check_restrictions()
            picking.cancel_valuation_moves()
            if picking.invoice_id.filtered(
                    lambda order: order.state != 'cancel'):
                raise exceptions.UserError(
                    _('Picking %s has invoices') % (picking.name))
            picking.move_lines.write({'state': 'draft'})
            # reassign quants done
            for move in picking.move_lines:
                move._check_restrictions()
                move.quant_ids._revert()
                move.group_id.procurement_ids.reset_to_confirmed()
            picking.state = 'draft'
            picking.action_confirm()
            picking.do_prepare_partial()
            picking.message_post(
                _("The picking has been re-opened and set to draft state"))
        return
