# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

_TARGET_DOC = '''This defines the amount of products you want to purchase.
The system will compute a purchase order based on the stock you have and the average consumption of each product.
* Target type "€": computed purchase order will cost at least the amount specified.
* Target type "days": computed purchase order will last at least the number of days specified (according to current average consumption).
* Target type "kg": computed purchase order will weight at least the weight specified.'''


class ComputedPurchaseOrder(models.Model):
    _description = 'Computed Purchase Order'
    _name = 'computed.purchase.order'
    _order = 'id desc'

    name = fields.Char(
        string='Computed Purchase Order Reference',
        size=64,
        required=True,
        default='Draft Purchase Order')

    order_date = fields.Datetime(
        string='Purchase Order Date',
        default=fields.Datetime.now,
        help="Depicts the date where the Quotation should be validated and converted into a purchase order.")  # noqa

    date_planned = fields.Datetime(
        string='Scheduled Date',
        compute='_compute_date_planned',
        required=True)

    supplier_id = fields.Many2one(
        'res.partner',
        'Supplier',
        readonly=True,
        help="Supplier of the purchase order.")

    order_line_ids = fields.One2many(
        'computed.purchase.order.line',
        'computed_purchase_order_id',
        string='Order Lines',
    )

    @api.multi
    def make_order(self):
        self.ensure_one()
        return True

    @api.multi
    def _compute_date_planned(self):
        # fixme
        for cpo in self:
            return fields.Datetime.now()
