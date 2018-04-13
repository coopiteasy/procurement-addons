from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


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
        help="Linked Product Template")

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
        related='supplierinfo_id.price',
        read_only=True,
        help='Supplier Product Price by buying unit. Price is  without VAT')

    virtual_coverage = fields.Float(
        string='Expected Stock Coverage',
        compute='_compute_virtual_coverage',
        help='Expected stock coverage (in days) based on current stocks and average daily consumption')  # noqa

    subtotal = fields.Float(
        string='Subtotal (w/o VAT)',
        compute='_compute_sub_total')

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
    def _compute_supplierinfo(self):
        for cpol in self:
            SupplierInfo = self.env['product.supplierinfo']
            si = SupplierInfo.search([
                ('product_tmpl_id', '=', cpol.product_template_id.id),
                ('name', '=', cpol.product_template_id.get_main_supplier().id)
            ])
            cpol.supplierinfo_id = si

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
                '%s:%s template has no variant set'
                % (self.product_template_id.id, self.product_template_id.name)
            )
