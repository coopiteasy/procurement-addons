# -*- coding: utf-8 -*-
from openerp import models, fields
from openerp.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    original_cpo_ids = fields.Many2many(
        'computed.purchase.order',
        string='Generated Purchase Orders'
    )
