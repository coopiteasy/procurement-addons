# -*- coding: utf-8 -*-
from openerp.tests.common import TransactionCase
from openerp.addons.stock.product import product_template as ProductTemplate
from openerp.addons.stock.product import product_product as ProductProduct
import datetime as dt

_datetimes = map(
    lambda d: d.strftime('%Y-%m-%d %H:%M:%S'),
    (dt.datetime.now() - dt.timedelta(days=d) for d in range(0, 24, 2)))

_quantities = [0.64, 6.45, 9.65, 1.76, 9.14, 3.99,
               6.92, 2.25, 6.91, 1.44, 6.52, 1.44]


class TestProductTemplate(TransactionCase):

    def setUp(self, *args, **kwargs):
        result = super(TestProductTemplate, self).setUp(*args, **kwargs)

        test_product_template = (
            self.env['product.template']
                .create({'name': 'test product template',
                         'calculation_range': 14,
                         'consumption_calculation_method': 'sales_history',
                         'product_template_id': 0,
                         })
        )

        pid = (
            self.env['product.product']
                .search([('product_tmpl_id', '=', test_product_template.id)])
                .ids
        ).pop()

        for date, qty in zip(_datetimes, _quantities):
            (self.env['pos.order.line']
                 .create({'create_date': date,
                          'qty': qty,
                          'product_id': pid
                          })
             )

        def _product_available(*args, **kwargs):
            products = (
                self.env['product.product']
                    .search([
                        ('product_tmpl_id', '=', test_product_template.id)])
            )
            mock_data = {
                    'qty_available': 53.2,
                    'incoming_qty': 14,
                    'outgoing_qty': 4.1,
                    'virtual_available': 53.2 + 14 - 4.1,
                }
            return {pid: mock_data for pid in products.ids}

        ProductTemplate._product_available = _product_available
        ProductProduct._product_available = _product_available

        test_product_template._compute_total_consumption()
        self.product_template_id = test_product_template.id

        return result

    def test_create(self):
        """Create a simple product template"""
        Template = self.env['product.template']
        product = Template.create({'name': 'Test create product'})
        self.assertEqual(product.name, 'Test create product')

    def test_compute_average_daily_consumption(self):
        ProductTemplate = self.env['product.template']
        product_template = ProductTemplate.browse(self.product_template_id)

        computed_value = product_template.average_consumption
        expected_value = 4.08
        self.assertEqual(computed_value, expected_value, 7)

    def test_compute_total_consumption(self):
        ProductTemplate = self.env['product.template']
        product_template = ProductTemplate.browse(self.product_template_id)
        computed_value = product_template.total_consumption
        expected_value = 57.11
        self.assertEqual(computed_value, expected_value)

    def test_compute_estimated_stock_coverage(self):
        ProductTemplate = self.env['product.template']
        product_template = ProductTemplate.browse(self.product_template_id)
        computed_value = product_template.estimated_stock_coverage
        expected_value = 13.04
        self.assertEqual(computed_value, expected_value)
