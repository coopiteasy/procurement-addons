# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_main_supplier(self):
        supplier_ids = self.seller_ids.sorted(
            key=lambda seller: seller.date_start,
            reverse=True)

        if supplier_ids:
            return supplier_ids[0].name
        else:
            raise ValidationError(
                'No supplier set for product %s' % self.name)
