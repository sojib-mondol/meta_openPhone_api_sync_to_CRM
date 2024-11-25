from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    openphone_contact_id = fields.Char(string="OpenPhone Contact ID")

