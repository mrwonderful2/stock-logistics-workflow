# -*- coding: utf-8 -*-
# Copyright 2012 Andrea Cometa
# Copyright 2013 Agile Business Group sagl
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import SavepointCase
from odoo.exceptions import UserError


class TestStockCancel(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockCancel, cls).setUpClass()

        cls.sup_location = cls.env.ref('stock.stock_location_suppliers')
        cls.src_location = cls.env.ref('stock.stock_location_stock')
        cls.cust_location = cls.env.ref('stock.stock_location_customers')
        cls.product = cls.env['product.product'].create({
            'name': 'Test product',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test partner'})

    def create_picking(self, partner, p_type, src=None, dest=None):
        picking = self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': p_type.id,
            'location_id': src or self.src_location.id,
            'location_dest_id': dest or self.cust_location.id,
        })
        return picking

    def create_move(self, pick, product, qty, src=None, dest=None):
        move = self.env['stock.move'].create({
            'name': '/',
            'picking_id': pick.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'location_id': src or self.src_location.id,
            'location_dest_id': dest or self.cust_location.id,
        })
        return move

    def create_invoice(self):
        receivable = self.env.ref('account.data_account_type_receivable').id
        return self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'name': "Test",
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'account_id': self.env['account.account'].search(
                        [('user_type_id', '=', receivable)], limit=1).id,
                    'quantity': 8.0,
                    'price_unit': 100.0,
                })
            ]
        })

    def test_backorder(self):
        picking = self.create_picking(
            self.partner, self.env.ref('stock.picking_type_out'))
        self.create_move(
            picking, self.product, 10.0)
        # Picking state is draft
        self.assertEqual(picking.state, 'draft')
        # Confirm picking
        picking.action_confirm()
        # We assign quantities
        picking.action_assign()
        pack_opt = self.env['stock.pack.operation'].search(
            [('picking_id', '=', picking.id)], limit=1)
        pack_opt.qty_done = 4.0
        # Split picking: 4 and 6
        picking.pack_operation_product_ids.write({'qty_done': 4})
        backorder_wiz_id = picking.do_new_transfer()['res_id']
        backorder_wiz = self.env['stock.backorder.confirmation'].browse(
            [backorder_wiz_id])
        backorder_wiz.process()
        with self.assertRaises(UserError):
            picking.action_revert_done()

    def test_invoice(self):
        picking = self.create_picking(
            self.partner, self.env.ref('stock.picking_type_out'))
        self.create_move(
            picking, self.product, 8.0)
        # Picking state is draft
        self.assertEqual(picking.state, 'draft')
        # Confirm picking
        picking.action_confirm()
        # We assign quantities
        picking.action_assign()
        picking.do_transfer()
        self.assertEqual(picking.state, 'done')
        invoice = self.create_invoice()
        picking.invoice_id = invoice.id
        with self.assertRaises(UserError):
            picking.action_revert_done()

    def test_reopen(self):
        picking_in = self.create_picking(
            self.partner, self.env.ref('stock.picking_type_in'))
        move_in = self.create_move(
            picking_in, self.product, 8.0)
        # Confirm picking
        picking_in.action_confirm()
        # We assign quantities
        picking_in.action_assign()
        picking_in.do_transfer()
        picking = self.create_picking(
            self.partner, self.env.ref('stock.picking_type_out'))
        self.create_move(
            picking, self.product, 8.0)
        # Picking state is draft
        self.assertEqual(picking.state, 'draft')
        # Confirm picking
        picking.action_confirm()
        # We assign quantities
        picking.action_assign()
        picking.do_transfer()
        picking.action_revert_done()
        self.assertEqual(picking.state, 'confirmed')
        quant = move_in.quant_ids[-1]
        previous_move = quant.history_ids[-1]
        previous_location = previous_move.location_id
        self.assertEqual(previous_location, self.src_location,
                         "Quant in wrong location")
        self.assertEqual(quant.qty, 8.0,
                         "Quant wrong qty")
