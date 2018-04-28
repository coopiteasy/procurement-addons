# -*- coding: utf-8 -*-
import logging

from openerp import models, fields, api
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ComputedPurchaseOrderLine(models.Model):
    _description = 'Computed Purchase Order Line'
    _name = 'computed.purchase.order.line'

    computed_purchase_order_id = fields.Many2one(
        'computed.purchase.order',
        string='Computed Purchase Order',
    )

    product_template_id = fields.Many2one(
        'product.template',
        string='Linked Product Template',
        required=True,
        help='Product')

    name = fields.Char(
        string='Product Name',
        related='product_template_id.name',
        read_only=True)

    supplierinfo_id = fields.Many2one(
        'product.supplierinfo',
        string='Supplier information',
        compute='_compute_supplierinfo',
        readonly=True,
    )

    category_id = fields.Many2one(
        'product.category',
        string='Internal Category',
        related='product_template_id.categ_id',
        read_only=True)

    uom_id = fields.Many2one(
        'product.uom',
        string='Unit of Measure',
        read_only=True,
        related='product_template_id.uom_id',
        help="Default Unit of Measure used for all stock operation.")

    stock_qty = fields.Float(
        string='Stock Quantity',
        related='product_template_id.qty_available',
        read_only=True,
        help='Quantity currently in stock. Does not take '
             'into account incoming orders.')

    average_consumption = fields.Float(
        string='Average Consumption',
        related='product_template_id.average_consumption',
        read_only=True)

    stock_coverage = fields.Float(
        string='Stock Coverage',
        related='product_template_id.estimated_stock_coverage',
        read_only=True,
    )

    minimum_purchase_qty = fields.Float(
        string='Minimum Purchase Quantity',
        compute='_compute_on_product_template_update',
    )

    purchase_quantity = fields.Float(
        string='Purchase Quantity',
        required=True,
        default=0.)

    uom_po_id = fields.Many2one(
        'product.uom',
        string='Purchase Unit of Measure',
        read_only=True,
        related='product_template_id.uom_po_id',
        help="Default Unit of Measure used for all stock operation.")

    product_price = fields.Float(
        string='Product Price (w/o VAT)',
        compute='_compute_on_product_template_update',
        read_only=True,
        help='Supplier Product Price by buying unit. Price is  without VAT')

    virtual_coverage = fields.Float(
        string='Expected Stock Coverage',
        compute='_compute_virtual_coverage',
        help='Expected stock coverage (in days) based on current stocks and average daily consumption')  # noqa

    subtotal = fields.Float(
        string='Subtotal (w/o VAT)',
        compute='_compute_sub_total')

    @api.multi
    @api.onchange('product_template_id')
    def _compute_on_product_template_update(self):
        for cpol in self:
            # get supplier info
            cpol.minimum_purchase_qty = cpol.supplierinfo_id.min_qty
            cpol.product_price = cpol.supplierinfo_id.price
            cpol.purchase_quantity = cpol.supplierinfo_id.min_qty

    @api.depends('purchase_quantity')
    @api.multi
    def _compute_virtual_coverage(self):
        for pol in self:
            avg = pol.average_consumption
            if avg > 0:
                qty = pol.stock_qty + pol.purchase_quantity
                pol.virtual_coverage = qty / avg
            else:
                # todo what would be a good default value? (not float(inf))
                pol.virtual_coverage = 9999

        return True

    @api.depends('purchase_quantity')
    @api.multi
    def _compute_sub_total(self):
        for pol in self:
            pol.subtotal = pol.product_price * pol.purchase_quantity
        return True

    @api.multi
    @api.depends('product_template_id')  # fixme
    @api.onchange('product_template_id')
    def _compute_supplierinfo(self):
        for cpol in self:
            if not cpol.product_template_id:
                cpol.supplierinfo_id = False
            else:
                SupplierInfo = self.env['product.supplierinfo']
                si = SupplierInfo.search([
                    ('product_tmpl_id', '=', cpol.product_template_id.id),
                    ('name', '=', cpol.product_template_id.main_supplier_id.id)  # noqa
                ])

                if len(si) == 0:
                    raise ValidationError(
                        u'No supplier information set for {name}'
                        .format(name=cpol.product_template_id.name))
                elif len(si) == 1:
                    cpol.supplierinfo_id = si
                else:
                    _logger.warning(
                        u'product {name} has several suppliers, chose last'
                        .format(name=cpol.product_template_id.name)
                    )
                    si = si.sorted(key=lambda r: r.create_date, reverse=True)
                    cpol.supplierinfo_id = si[0]

    @api.constrains('purchase_quantity')
    def _check_minimum_purchase_quantity(self):
        for cpol in self:
            if cpol.purchase_quantity < 0:
                raise ValidationError(u'Purchase quantity for {product_name} must be greater than 0'  # noqa
                                        .format(product_name=cpol.product_template_id.name))
            elif 0 < cpol.purchase_quantity < cpol.minimum_purchase_qty:
                raise ValidationError(u'Purchase quantity for {product_name} must be greater than {min_qty}'  # noqa
                                       .format(product_name=cpol.product_template_id.name,
                                               min_qty=cpol.minimum_purchase_qty))

    @api.multi
    def get_default_product_product(self):
        self.ensure_one()
        ProductProduct = self.env['product.product']
        products = ProductProduct.search([
            ('product_tmpl_id', '=', self.product_template_id.id)
        ])

        products = products.sorted(
            key=lambda product: product.create_date,
            reverse=True
        )

        if products:
            return products[0]
        else:
            raise ValidationError(
                u'%s:%s template has no variant set'
                % (self.product_template_id.id, self.product_template_id.name)
            )

