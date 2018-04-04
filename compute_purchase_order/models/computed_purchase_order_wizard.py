# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ComputedPurchaseOrderWizard(models.TransientModel):
    _description = 'Computed Purchase Order'
    _name = 'computed.purchase.order.wizard'
    _order = 'id desc'

    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        readonly=True,
        help='Supplier of the purchase order.')

    product_ids = fields.Many2many(
        'product.template',
        string='Staged products for cpo',
    )

    @api.model
    def default_get(self, fields):
        record = super(ComputedPurchaseOrderWizard, self).default_get(fields)

        record['supplier_id'] = self._get_selected_supplier()
        record['product_ids'] = self._get_selected_products()

        return record

    def _get_selected_products(self):
        return self.env.context['active_ids']

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

    @api.multi
    def create_computed_purchase_order(self):
        self.ensure_one()
        ComputedPurchaseOrder = self.env['computed.purchase.order']

        cpo_name = 'CPO {} {}'.format(
            self.supplier_id.name,
            fields.Date.today())

        cpo_values = {
            'name': cpo_name,
            'partner_id': self.supplier_id.id,
        }

        cpo = ComputedPurchaseOrder.create(cpo_values)

        OrderLine = self.env['computed.purchase.order.line']
        for product in self.product_ids:
            OrderLine.create(
                {'name': product.name,
                 'computed_purchase_order_id': cpo.id,
                 'product_template_id': product.id,
                 'category_id': product.categ_id.id,
                 'uom_id': product.uom_id.id,
                 'average_consumption': product.average_consumption,
                 'stock_coverage': product.estimated_stock_coverage,
                 'uom_po_id': product.uom_po_id.id
                 }
            )

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'computed.purchase.order',
            'res_id': cpo.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }
        return action
