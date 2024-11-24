

# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _create_openphone_contact(self, partner):
        """Create a contact in OpenPhone."""
        # Fetch API key from system parameters
        api_key = self.env['ir.config_parameter'].sudo().get_param('openphone.api.key', default='')
        if not api_key:
            _logger.warning("OpenPhone API key is missing. Please configure it.")
            raise UserError(_("No OpenPhone API key found. Please configure it in settings."))

        api_url = "https://api.openphone.com/v1/contacts"

        # Prepare the data payload
        data = {
            "defaultFields": {
                "firstName": partner.name.split(" ")[0] if partner.name else "",
                "lastName": " ".join(partner.name.split(" ")[1:]) if len(partner.name.split(" ")) > 1 else "",
                "emails": [{"name": "Work email", "value": partner.email}] if partner.email else [],
                "phoneNumbers": [{"name": "Work phone", "value": partner.phone}] if partner.phone else [],
            },
        }

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        # Log debug information
        _logger.debug("OpenPhone API Key: %s", api_key)
        _logger.debug("OpenPhone API URL: %s", api_url)
        _logger.debug("Payload being sent to OpenPhone API: %s", data)

        try:
            # Send POST request to OpenPhone API
            response = requests.post(api_url, headers=headers, json=data)
            _logger.debug("OpenPhone API Response Status Code: %s", response.status_code)
            _logger.debug("OpenPhone API Response Content: %s", response.text)

            # Raise an exception for HTTP errors
            response.raise_for_status()
            _logger.info("Successfully created contact in OpenPhone: %s", partner.name)
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to create contact in OpenPhone: %s", str(e))
            _logger.error("Response Content: %s", response.text if 'response' in locals() else "No response received")
            raise UserError(_("Failed to create contact in OpenPhone. Check logs for details."))

    @api.model
    def create(self, vals):
        """Override create method to send data to OpenPhone."""
        partner = super(ResPartner, self).create(vals)
        _logger.debug("New partner created in Odoo: %s", partner)
        
        # Call the function to create contact in OpenPhone
        try:
            self._create_openphone_contact(partner)
        except UserError as e:
            _logger.warning("Contact creation in OpenPhone failed: %s", str(e))
        return partner
