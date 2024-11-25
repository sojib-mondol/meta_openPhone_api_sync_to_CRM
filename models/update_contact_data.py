# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _update_openphone_contact(self, partner):
        """Update the contact in OpenPhone."""
        # Fetch API key from system parameters
        api_key = self.env['ir.config_parameter'].sudo().get_param('openphone.api.key', default='')
        if not api_key:
            _logger.warning("OpenPhone API key is missing. Please configure it.")
            raise UserError(_("No OpenPhone API key found. Please configure it in settings."))

        # Get OpenPhone contact ID from the partner
        openphone_contact_id = partner.openphone_contact_id
        if not openphone_contact_id:
            _logger.warning("No OpenPhone contact ID found for partner: %s", partner.name)
            raise UserError(_("No OpenPhone contact ID found for this partner. Contact creation is required first."))

        api_url = f"https://api.openphone.com/v1/contacts/{openphone_contact_id}"

        # Prepare the data payload with updated values
        data = {
            "defaultFields": {
                "firstName": partner.name.split(" ")[0] if partner.name else None,
                "lastName": " ".join(partner.name.split(" ")[1:]) if len(partner.name.split(" ")) > 1 else None,
                "company": partner.company_name or None,
                "role": partner.function or None,
                "emails": [{"name": "Work email", "value": partner.email}] if partner.email else [],
                "phoneNumbers": [{"name": "Work phone", "value": partner.phone}] if partner.phone else []
            },
            
        }

        # Remove keys with empty values
        data["defaultFields"] = {k: v for k, v in data["defaultFields"].items() if v}

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        # Log debug information
        _logger.debug("OpenPhone API Key: %s", api_key)
        _logger.debug("OpenPhone API URL: %s", api_url)
        _logger.debug("Payload being sent to OpenPhone API: %s", data)

        try:
            # Send PATCH request to OpenPhone API to update the contact
            response = requests.patch(api_url, headers=headers, json=data)
            _logger.debug("OpenPhone API Response Status Code: %s", response.status_code)
            _logger.debug("OpenPhone API Response Content: %s", response.text)

            if response.status_code == 200:
                _logger.info("Successfully updated contact in OpenPhone: %s", partner.name)
            else:
                # Log and raise an error for non-successful status codes
                _logger.error("Failed to update contact in OpenPhone: %s", response.text)
                raise UserError(_("Failed to update contact in OpenPhone. Check logs for details."))

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to update contact in OpenPhone: %s", str(e))
            raise UserError(_("Failed to update contact in OpenPhone. Check logs for details."))

    def write(self, vals):
        """Override write method to send updates to OpenPhone."""
        partner_updated = super(ResPartner, self).write(vals)
        for partner in self:
            if partner.openphone_contact_id:
                try:
                    self._update_openphone_contact(partner)
                except UserError as e:
                    _logger.warning("Contact update in OpenPhone failed for partner %s: %s", partner.name, str(e))
        return partner_updated
