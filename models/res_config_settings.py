# # -*- coding: utf-8 -*-

# from odoo import models, fields, api

# class ResConfigSettings(models.TransientModel):
#     _inherit = 'res.config.settings'

#     openphone_api_key = fields.Char(string="OpenPhone API Key")

#     def set_values(self):
#         super(ResConfigSettings, self).set_values()
#         self.env['ir.config_parameter'].sudo().set_param(
#             'openphone.api_key', self.openphone_api_key
#         )

#     @api.model
#     def get_values(self):
#         res = super(ResConfigSettings, self).get_values()
#         res['openphone_api_key'] = self.env['ir.config_parameter'].sudo().get_param(
#             'openphone.api_key', default=''
#         )
#         return res
