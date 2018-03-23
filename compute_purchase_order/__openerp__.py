# -*- encoding: utf-8 -*-
{
    'name': 'Computed Purchase Order',
    'version': '9.0.1',
    'category': 'Purchase Order',
    'description': """ todo """,
    'author': 'Coop IT Easy',
    'website': 'https://github.com/coopiteasy/procurement-addons',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'beesdoo_product',  # for main seller ids
        'stock',
        'product_average_consumption',
    ],
    'data': [
        'views/purchase_order_preparation.xml',
    ],
}
