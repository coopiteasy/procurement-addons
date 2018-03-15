# -*- encoding: utf-8 -*-
from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    consumption_calculation_method = fields.Selection(
        selection=[('sales_history', 'Sales History')],
        string="Consumption Calculation Method",
        default='sales_history',
    )
    calculation_range = fields.Integer(
        'Calculation range (days)',
        default=14,
    )

    average_consumption = fields.Float(
        string='Average consumption',
        compute='_compute_average_daily_consumption',
        digits=(100, 2),
    )
    total_consumption = fields.Integer(
        string='Total consumption',
        compute='_compute_total_consumption',
    )
    stock_coverage = fields.Float(
        string='Stock coverage (days)',
        compute='_compute_stock_coverage',
        digits=(100, 2),
    )

    def _compute_average_daily_consumption(self):
        return 6.8

    def _compute_total_consumption(self):
        return 67

    def _compute_stock_coverage(self):
        return 7.1
