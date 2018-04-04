# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError

_TARGET_DOC = '''This defines the amount of products you want to purchase.
The system will compute a purchase order based on the stock you have and the average consumption of each product.
* Target type "€": computed purchase order will cost at least the amount specified.
* Target type "days": computed purchase order will last at least the number of days specified (according to current average consumption).
* Target type "kg": computed purchase order will weight at least the weight specified.'''


class ComputedPurchaseOrder(models.TransientModel):
    _description = 'Computed Purchase Order'
    _name = 'computed.purchase.order'
    _order = 'id desc'

    name = fields.Char(
        'Computed Purchase Order Reference',
        size=64,
        required=True,
        readonly=True,
        defaults='Draft Purchase Order')

    order_date = fields.Datetime(
        'Purchase Order Date',
        default=fields.Datetime.now,
        help="Depicts the date where the Quotation should be validated and converted into a purchase order.")  # noqa

    date_planned = fields.Datetime('Scheduled Date',
                                   compute='_compute_date_planned',
                                   required=True)

    supplier_id = fields.Many2one(
        'res.partner',
        'Supplier',
        readonly=True,
        help="Supplier of the purchase order.")

    order_line_ids = fields.Many2many(
        'computed.purchase.order.line',
        string='Ordered Lines',
    )

    @api.model
    def default_get(self, fields):
        record = super(ComputedPurchaseOrder, self).default_get(fields)

        record['supplier_id'] = self._get_selected_supplier()
        record['order_line_ids'] = self._get_selected_products()

        return record

    def _get_selected_supplier(self):
        """
        Calcule le vendeur associé qui a la date de début la plus récente et
        plus petite qu’aujourd’hui pour chaque article sélectionné.
        Will raise an error if more than two sellers are set
        """
        product_ids = self.env.context['active_ids']
        products = self.env['product.template'].browse(product_ids)

        suppliers = set()
        for product in products:
            supplier_ids = product.seller_ids.sorted(
                key=lambda seller: seller.date_start,
                reverse=True)

            if supplier_ids:
                main_supplier_id = supplier_ids[0].name.id
                suppliers.add(main_supplier_id)

        if len(suppliers) == 0:
            raise ValidationError('No supplier is set for selected articles.')
        elif len(suppliers) == 1:
            return suppliers.pop()
        else:
            raise ValidationError(
                'You must select article from a single supplier.')

    def _get_selected_products(self):
        product_ids = self.env.context['active_ids']
        products = self.env['product.template'].browse(product_ids)
        OrderLine = self.env['computed.purchase.order.line']

        order_line_ids = []
        for product in products:
            ol = OrderLine.create(
                {'name': product.name,
                 'category_id': product.categ_id.id,
                 'average_consumption': product.average_consumption,
                 'stock_coverage': product.estimated_stock_coverage,
                 'product_template_id': product.id,
                 'uom_id': product.uom_id.id,
                 'uom_po_id': product.uom_po_id.id
                 }
            )
            order_line_ids.append(ol.id)

        return order_line_ids

    @api.multi
    def make_order(self):
        self.ensure_one()
        po_lines = self._make_po_lines()
        if not po_lines:
            raise ValidationError(
                _('All purchase quantities are set to 0!'))

        PurchaseOrder = self.env['purchase.order']

        po_values = {
            'name': 'name',
            'date_order': self.order_date,
            'partner_id': self.supplier_id.id,
            'date_planned': self.date_planned,
        }

        purchase_order_id = PurchaseOrder.create(po_values)

        # mod_obj = self.env['ir.model.data']
        # res = mod_obj.get_object_reference(
        #     'purchase', 'purchase_order_form')
        # res_id = res and res[1] or False
        # return {
        #     'name': _('Purchase Order'),
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'views': [(res_id, 'form')],
        #     'view_id': [res_id],
        #     'res_model': 'purchase.order',
        #     'type': 'ir.actions.act_window',
        #     'nodestroy': True,
        #     'target': 'current',
        #     'res_id': po_id.id or False,
        # }
        #

    @api.multi
    def _make_po_lines(self):
        pass
