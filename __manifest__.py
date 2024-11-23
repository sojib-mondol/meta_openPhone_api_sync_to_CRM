{
    'name': 'Opne Phone Api Sync to the CRM',
    'version': '18.1.0',
    'summary': 'A brief summary of your module',
    'description': 'A detailed description of your module, including features and purpose.',
    'author': 'Sojib Mondol',
    'website': 'https://metamorphosis.com.bd',
    'license': 'LGPL-3',  
    'category': 'Uncategorized', 
    'depends': ['base', 'web', 'crm', 'contacts'],  
    'data': [
        'views/res_config_settings_views.xml',
        'views/openphone_sync_menu.xml',
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
