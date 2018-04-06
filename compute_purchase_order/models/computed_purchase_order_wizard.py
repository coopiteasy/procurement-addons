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
        help='Supplier of the purchase order')

    product_ids = fields.Many2many(
        'product.template',
        string='Staged products for cpo',
    )

    computed_purchase_order_id = fields.Many2one(
        'computed.purchase.order',
        string='Target CPO'
    )

    is_cpo_set = fields.Boolean(
        string='Is CPO set',
        compute='_is_cpo_set'
    )

    @api.model
    def default_get(self, fields):
        record = super(ComputedPurchaseOrderWizard, self).default_get(fields)

        record['supplier_id'] = self._get_selected_supplier()
        record['product_ids'] = self._get_selected_products()

        return record

    @api.multi
    def _is_cpo_set(self):
        for cpow in self:
            if cpow.computed_purchase_order_id:
                cpow.is_cpo_set = True
            else:
                cpow.is_cpo_set = False

    def _get_selected_products(self):
        return self.env.context['active_ids']

    def _get_main_supplier(self, product_template):
        supplier_ids = product_template.seller_ids.sorted(
            key=lambda seller: seller.date_start,
            reverse=True)

        if supplier_ids:
            return supplier_ids[0].name
        else:
            raise ValidationError(
                'No supplier set for product %s' % product_template)

    def _get_selected_supplier(self):
        """
        Calcule le vendeur associé qui a la date de début la plus récente et
        plus petite qu’aujourd’hui pour chaque article sélectionné.
        Will raise an error if more than two sellers are set
        """
        product_ids = self.env.context['active_ids']  # may be cpo if coming form cpo
        products = self.env['product.template'].browse(product_ids)

        suppliers = set()
        for product in products:
            main_supplier_id = self._get_main_supplier(product).id
            suppliers.add(main_supplier_id)

        if len(suppliers) == 0:
            raise ValidationError('No supplier is set for selected articles.')
        elif len(suppliers) == 1:
            return suppliers.pop()
        else:
            raise ValidationError(
                'You must select article from a single supplier.')

    def _get_supplierinfo(self, product_tmpl_id):
        SupplierInfo = self.env['product.supplierinfo']
        si = SupplierInfo.search([
            ('product_tmpl_id', '=', product_tmpl_id),
            ('name', '=', self.supplier_id.id)
        ])
        return si

    @api.multi
    def create_computed_purchase_order(self):
        self.ensure_one()
        ComputedPurchaseOrder = self.env['computed.purchase.order']

        cpo_name = 'CPO {} {}'.format(
            self.supplier_id.name,
            fields.Date.today())

        cpo_values = {
            'name': cpo_name,
            'supplier_id': self.supplier_id.id,
            # pass product template and not product product
        }

        cpo = ComputedPurchaseOrder.create(cpo_values)

        OrderLine = self.env['computed.purchase.order.line']
        for product in self.product_ids:
            OrderLine.create(
                {'name': product.name,
                 'computed_purchase_order_id': cpo.id,
                 'supplierinfo_id': self._get_supplierinfo(product.id).id,
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

    @api.multi
    def add_products_to_cpo(self):
        self.ensure_one()
        cpo = self.computed_purchase_order_id

        OrderLine = self.env['computed.purchase.order.line']
        for product in self.product_ids:

            if self.supplier_id != self._get_main_supplier(product):
                raise ValidationError('You can only add products from '
                                      'selected supplier')

            if not cpo.contains_product(product):

                OrderLine.create(
                    {'name': product.name,
                     'computed_purchase_order_id': cpo.id,
                     'supplierinfo_id': self._get_supplierinfo(product.id).id,
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
