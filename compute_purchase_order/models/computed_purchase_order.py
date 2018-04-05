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

    _STATE = [
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ]

    name = fields.Char(
        string='CPO Reference',
        size=64,
        default='New')

    order_date = fields.Datetime(
        string='Purchase Order Date',
        default=fields.Datetime.now,
        help="Depicts the date where the Quotation should be validated and converted into a purchase order.")  # noqa

    date_planned = fields.Datetime(
        string='Date Planned'
    )

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

    total_amount = fields.Float(
        string='Total Amount (w/o VAT)',
        compute='_compute_cpo_total'
    )

    generated_purchase_order_id = fields.Many2one(
        'purchase.order',
        'Generated PO'
    )

    state = fields.Selection(
        _STATE,
        'State',
        required=True,
        default='draft')


    @api.model
    def default_get(self, fields_list):
        record = super(ComputedPurchaseOrder, self).default_get(fields_list)
        record['date_planned'] = self._get_default_date_planned()
        return record

    def _get_default_date_planned(self):
        return fields.Datetime.now()

    # @api.onchange(order_line_ids)  # fixme
    @api.multi
    def _compute_cpo_total(self):
        for cpo in self:
            total_amount = sum(cpol.subtotal for cpol in cpo.order_line_ids)
            cpo.total_amount = total_amount

    @api.multi
    def create_purchase_order(self):
        self.ensure_one()
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        po_values = {
            'name': 'New',
            'date_order': self.order_date,
            'partner_id': self.supplier_id.id,
            'date_planned': self.date_planned,
        }
        purchase_order = PurchaseOrder.create(po_values)

        for cpo_line in self.order_line_ids:
            pol_values = {
                'name': cpo_line.name,
                'product_id': cpo_line.get_default_product_product().id,
                'product_qty': cpo_line.purchase_quantity,
                'price_unit': cpo_line.product_price,
                'product_uom': cpo_line.uom_po_id.id,
                'order_id': purchase_order.id,
                'date_planned': self.date_planned,
            }
            PurchaseOrderLine.create(pol_values)

        self.generated_purchase_order_id = purchase_order.id
        self.state = 'done'

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }
        return action

    @api.multi
    def cancel_cpo(self):
        for cpo in self:
            cpo.state = 'cancelled'
