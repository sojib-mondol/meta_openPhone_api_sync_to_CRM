{
    'name': 'Opne Phone Api Sync to the CRM',
    'version': '18.1.0',
    'summary': 'Synchronize OpenPhone data with Odoo CRM seamlessly.',
    'description': 'This module integrates OpenPhone API with Odoo CRM to synchronize contacts and communication data.',
    'author': 'Sojib Mondol',
    'website': 'https://metamorphosis.com.bd',
    'license': 'LGPL-3',  
    'category': 'Uncategorized', 
    'depends': ['base', 'web', 'crm', 'contacts'],  
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/openphone_sync_menu.xml',
        'views/add_openphone_contact_id_in_res_partner_from_view.xml',
        'views/actionbutton_for_chatter.xml',
    ],
    'assets': {
        'web.assets_backend': [
           
        ],
        'web.assets_frontend': [
            
            
        ],
    },
    # 'images': ['static/description/icon.png'],  
    'installable': True,
    'application': True,
    'auto_install': False,
}
