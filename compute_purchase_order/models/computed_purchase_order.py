# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ComputedPurchaseOrder(models.Model):
    _description = 'Computed Purchase Order'
    _name = 'computed.purchase.order'
    _order = 'id desc'

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
        string='Supplier',
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

    generated_purchase_order_ids = fields.Many2many(
        'purchase.order',
        string='Generated Purchase Orders'
    )

    generated_po_count = fields.Integer(
        string='Generated Purchase Order count',
        compute='_compute_generated_po_count',
    )

    @api.model
    def default_get(self, fields_list):
        record = super(ComputedPurchaseOrder, self).default_get(fields_list)

        record['date_planned'] = self._get_default_date_planned()

        supplier_id = self._get_selected_supplier()
        record['supplier_id'] = supplier_id

        product_tmpl_ids = self._get_selected_products()
        cpol_ids = []
        OrderLine = self.env['computed.purchase.order.line']
        for product_id in product_tmpl_ids:
            cpol = OrderLine.create(
                {'computed_purchase_order_id': self.id,
                 'product_template_id': product_id,
                 # pass product product and not product template?
                 }
            )
            cpol_ids.append(cpol.id)

        record['order_line_ids'] = cpol_ids

        supplier_name = (
            self.env['res.partner']
                .browse(supplier_id)
                .name)

        record['name'] = u'CPO {} {}'.format(
            supplier_name,
            fields.Date.today())

        return record

    def _get_default_date_planned(self):
        return fields.Datetime.now()

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
            main_supplier_id = product.get_main_supplier().id
            suppliers.add(main_supplier_id)

        if len(suppliers) == 0:
            raise ValidationError('No supplier is set for selected articles.')
        elif len(suppliers) == 1:
            return suppliers.pop()
        else:
            raise ValidationError(
                'You must select article from a single supplier.')

    @api.multi
    def _compute_generated_po_count(self):
        for cpo in self:
            cpo.generated_po_count = len(cpo.generated_purchase_order_ids)

    @api.multi
    def get_generated_po_action(self):
        self.ensure_one()
        print self.generated_purchase_order_ids.ids
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form,kanban',
            'target': 'current',
            'domain': [('id', 'in', self.generated_purchase_order_ids.ids)],
        }
        return action

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

        self.generated_purchase_order_ids += purchase_order

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
    def add_products(self):
        self.ensure_one()

        CPOW = self.env['computed.purchase.order.wizard']

        product_tmpl_ids = self.order_line_ids.mapped(
            'product_template_id').ids

        cpow = CPOW.create({
            'computed_purchase_order_id': self.id,
            'supplier_id': self.supplier_id.id,
            'product_ids': [(6, 0, product_tmpl_ids)]
        })

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Change product selection',
            'res_model': 'computed.purchase.order.wizard',
            'res_id': cpow.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'compute_purchase_order.view_form_purchase_order_wizard').id,
            'target': 'new',
        }
        return action

    def contains_product(self, product_template):
        linked_products = self.order_line_ids.mapped('product_template_id')
        return product_template in linked_products
