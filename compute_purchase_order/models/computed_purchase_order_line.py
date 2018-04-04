from openerp import models, fields, api, _


class ComputedPurchaseOrderLine(models.Model):
    _description = 'Computed Purchase Order Line'
    _name = 'computed.purchase.order.line'

    name = fields.Char(
        string='Product Name',
        required=True,
        read_only=True)

    computed_purchase_order_id = fields.Many2one(
        'computed.purchase.order',
        string='Computed Purchase Order',
    )

    category_id = fields.Many2one(
        'product.category',
        string='Internal Category',
        required=True,
        read_only=True)

    product_template_id = fields.Many2one(
        'product.template',
        string='Linked Product Template',
        required=True,
        help="Linked Product Template")

    uom_id = fields.Many2one(
        'product.uom',
        string='Unit of Measure',
        read_only=True,
        required=True,
        help="Default Unit of Measure used for all stock operation.")

    stock_qty = fields.Float(
        string='Stock Quantity',
        related='product_template_id.qty_available',
        help='Quantity currently in stock. Does not take '
             'into account incoming orders.')

    average_consumption = fields.Float(
        string='Average Consumption',
        related='product_template_id.average_consumption',
        read_only=True)

    stock_coverage = fields.Float(
        string='Stock Coverage',
        related='product_template_id.estimated_stock_coverage',
    )

    purchase_quantity = fields.Float(
        string='Purchase Quantity',
        required=True,
        default=0.)

    uom_po_id = fields.Many2one(
        'product.uom',
        string='Purchase Unit of Measure',
        read_only=True,
        required=True,
        help="Default Unit of Measure used for all stock operation.")  # noqa

    # supplier_product_price = fields.Float('Supplier Product Price (w/o VAT)',
    #                                       help='Supplier Product Price by buying unit. Price is  without VAT')  # noqa
    #
    # supplier_product_vat = fields.Float('Supplier Product VAT')
    #
    # virtual_coverage = fields.Integer('Expected Stock Coverage',
    #                                   compute='_compute_virtual_coverage',
    #                                   help='Expected stock coverage (in days) based on current stocks and average daily consumption')  # noqa
    #
    # sub_total = fields.Float('Total Amount (w/o VAT)',
    #                          compute='_compute_sub_total')
    #
    # def _compute_virtual_coverage(self):
    #     return 231
    #
    # def _compute_sub_total(self):
    #     return 1234.5

    # @api.multi
    # def _get_product_statistics(self):
    #     for pol in self:
    #         pol.stock_qty = pol.product_template_id.qty_available
    #         pol.average_consumption = pol.product_template_id.average_consumption  # noqa
    #         pol.stock_coverage = pol.product_template_id.estimated_stock_coverage  # noqa
