# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from itertools import chain

_TARGET_DOC = '''This defines the amount of products you want to purchase.
The system will compute a purchase order based on the stock you have and the average consumption of each product.
* Target type "€": computed purchase order will cost at least the amount specified.
* Target type "days": computed purchase order will last at least the number of days specified (according to current average consumption).
* Target type "kg": computed purchase order will weight at least the weight specified.'''
             

class ComputedPurchaseOrder(models.Model):
    _description = 'Computed Purchase Order'
    _name = 'computed.purchase.order'  # todo is this a relevant name?
    _order = 'id desc'

    def _get_selected_products(self):
        return self.env.context['active_ids']

    def _get_selected_suppliers(self):
        Products = self.env['product.template']
        products = Products.browse(self.env.context['active_ids'])
        supplier_infos = products.mapped('seller_ids')
        partners = supplier_infos.mapped('name')
        return partners

    name = fields.Char(
        'Computed Purchase Order Reference',
        size=64,
        required=True,
        defaults='New Purchase Order')

    order_date = fields.Datetime(
        'Purchase Order Date',
        default=fields.Datetime.now())

    # partner_id = fields.Many2many(
    #     'res.partner',
    #     'Supplier',
    #     default=_get_selected_suppliers,
    #     required=True,
    #     domain=[('supplier', '=', True)],
    #     help="Supplier of the purchase order.")

    order_line_ids = fields.Many2many(
        'product.template',  # todo replace by order lines
        string='Ordered Lines',
        default=_get_selected_products
    )

    # _DEFAULT_NAME = _('New')
    #
    # _STATE = [
    #     ('draft', 'Draft'),
    #     ('done', 'Done'),
    #     ('canceled', 'Canceled'),
    # ]
    #
    # _TARGET_TYPE = [
    #     ('product_price_inv_eq', '€'),
    #     ('time', 'days'),
    #     ('weight', 'kg'),
    # ]
    #
    # _VALID_PSI = [
    #     ('first', 'Consider only the first supplier on the product'),
    #     ('all', 'Consider all the suppliers registered on the product'),
    # ]
    #
    # # Columns section
    # name = fields.Char(
    #     'Computed Purchase Order Reference',
    #     size=64,
    #     required=True,
    #     defaults=_DEFAULT_NAME
    # )
    # company_id = fields.Many2one(
    #     'res.company',
    #     'Company',
    #     readonly=True,
    #     required=True,
    #     help="""When you will validate this item, this will create a"""
    #          """ purchase order for this company.""",
    #     default=lambda self: self.env.user.company_id, )
    #
    # partner_id = fields.Many2one(
    #     'res.partner',
    #     'Supplier',
    #     required=True,
    #     domain=[('supplier', '=', True)],
    #     help="Supplier of the purchase order.")
    #
    # active = fields.Boolean(
    #     'Active',
    #     default=True,
    #     help="""By unchecking the active field, you may hide this item"""
    #          """ without deleting it.""")
    #
    # state = fields.Selection(
    #     _STATE,
    #     'State',
    #     required=True,
    #     default='draft')
    #
    # # order_line_ids = fields.One2many(
    # #     comodel_name='computed.purchase.order.line',
    # #     inverse_name='computed_purchase_order_id',
    # #     string='Order Lines',
    # #     help="Products to order.")
    #
    # purchase_order_id = fields.Many2one(
    #     'purchase.order',
    #     'Purchase Order',
    #     readonly=True)
    #
    # purchase_target = fields.Integer(
    #     'Purchase Target',
    #     default=0)
    #
    # target_type = fields.Selection(
    #     _TARGET_TYPE,
    #     'Target Type',
    #     required=True,
    #     default='product_price_inv_eq',
    #     help=_TARGET_DOC)
    #
    # valid_psi = fields.Selection(
    #     _VALID_PSI,
    #     'Supplier choice',
    #     required=True,
    #     default='first',
    #     help="""Method of selection of suppliers""")
    #
    # computed_amount = fields.Float(
    #     compute='_get_computed_amount',
    #     digits=(100, 2),
    #     string='Amount of the computed order',
    #     multi='computed_amount_duration')
    #
    # computed_duration = fields.Integer(
    #     compute='_get_computed_amount_duration',
    #     string='Minimum duration after order',
    #     multi='computed_amount_duration')
    #
    # products_updated = fields.Boolean(
    #     compute='_get_products_updated',
    #     string='Indicate if there were any products updated in the list')
    #
    # # View Section
    # @api.onchange('partner_id')
    # def onchange_partner_id(self):
    #     pass
    #
    # @api.model
    # def _make_po_lines(self):
    #     pass
    #
    # @api.multi
    # def _get_computed_amount(self):
    #     return 0.
    #
    # @api.multi
    # def _get_computed_amount_duration(self):
    #     return 0.
    #
    # @api.multi
    # def _get_products_updated(self):
    #     return True
    #
    # @api.multi
    # def make_purchase_order(self):
    #     for cpo in self:
    #         po_lines = cpo._make_po_lines()
    #         if not po_lines:
    #             raise ValidationError(
    #                 _('All purchase quantities are set to 0!'))
    #
    #         po_obj = self.env['purchase.order']
    #         po_values = {
    #             'origin': cpo.name,
    #             'partner_id': cpo.partner_id.id,
    #             'location_id': self.env['res.users'].browse(self.env.uid).company_id.partner_id.property_stock_customer.id,
    #             'order_line': po_lines,
    #             'date_planned': (cpo.incoming_date or fields.Date.context_today(self)),
    #         }
    #
    #         po_id = po_obj.create(po_values)
    #         cpo.state = 'done'
    #         cpo.purchase_order_id = po_id
    #
    #         mod_obj = self.env['ir.model.data']
    #         res = mod_obj.get_object_reference('purchase', 'purchase_order_form')
    #         res_id = res and res[1] or False
    #         return {
    #             'name': _('Purchase Order'),
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'views': [(res_id, 'form')],
    #             'view_id': [res_id],
    #             'res_model': 'purchase.order',
    #             'type': 'ir.actions.act_window',
    #             'nodestroy': True,
    #             'target': 'current',
    #             'res_id': po_id.id or False,
    #         }
    #
    #
    #
    #
