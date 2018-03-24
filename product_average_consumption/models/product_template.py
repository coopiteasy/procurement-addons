# -*- encoding: utf-8 -*-
from openerp import models, fields, api
import datetime as dt


class ProductTemplate(models.Model):
    _inherit = "product.template"

    consumption_calculation_method = fields.Selection(
        selection=[('sales_history', 'Sales History')],
        string='Consumption Calculation Method',
        default='sales_history',
    )
    calculation_range = fields.Integer(
        'Calculation range (days)',
        default=365,  # todo sensible defaults, 14, 28?
    )

    average_consumption = fields.Float(
        string='Average Consumption',
        compute='_compute_average_daily_consumption',
        readonly=True,
        digits=(100, 2),
    )

    total_consumption = fields.Float(
        string='Total Consumption',
        default=0,
        readonly=True,
        digits=(100, 2),
    )

    estimated_stock_coverage = fields.Float(
        string='Estimated Stock Coverage (days)',
        compute='_compute_estimated_stock_coverage',
        default=0,
        digits=(100, 2),
        readonly=True,
    )

    @api.multi
    @api.depends('calculation_range')
    def _compute_average_daily_consumption(self):
        for template in self:
            if template.calculation_range > 0:
                avg = template.total_consumption / template.calculation_range
            else:
                avg = 0
            template.average_consumption = avg

        return True

    @api.multi
    @api.depends('calculation_range')
    def _compute_total_consumption(self):
        for template in self:
            products = (
                self.env['product.product']
                    .search([('product_tmpl_id', '=', template.id)]))
            products_id = products.mapped('id')

            today = dt.date.today()
            pol_date_limit = (
                 today - dt.timedelta(days=template.calculation_range))

            order_lines = (
                self.env['pos.order.line']
                    .search([
                        ('product_id', 'in', products_id),
                        ('create_date', '>',
                            fields.Datetime.to_string(pol_date_limit))
                ])
            )

            if len(order_lines) > 0:
                res = sum(order_lines.mapped('qty'))
            else:
                res = 0
            template.total_consumption = res
        return True

    @api.multi
    @api.depends('calculation_range')
    def _compute_estimated_stock_coverage(self):
        for product_template in self:
            qty = product_template.qty_available
            avg = product_template.average_consumption
            if avg > 0:
                product_template.estimated_stock_coverage = qty / avg
            else:
                # todo what would be a good default value? (not float(inf))
                product_template.estimated_stock_coverage = 9999

        return True
