# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _delete_openphone_contact(self, partner):
        """Delete the contact in OpenPhone."""
        # Fetch API key from system parameters
        api_key = self.env['ir.config_parameter'].sudo().get_param('openphone.api.key', default='')
        if not api_key:
            _logger.warning("OpenPhone API key is missing. Please configure it.")
            raise UserError(_("No OpenPhone API key found. Please configure it in settings."))

        # Get OpenPhone contact ID from the partner
        openphone_contact_id = partner.openphone_contact_id
        if not openphone_contact_id:
            _logger.warning("No OpenPhone contact ID found for partner: %s", partner.name)
            raise UserError(_("No OpenPhone contact ID found for this partner. Contact deletion is not possible."))

        api_url = f"https://api.openphone.com/v1/contacts/{openphone_contact_id}"

        headers = {
            "Authorization": api_key
        }

        _logger.debug("OpenPhone API URL for deletion: %s", api_url)

        try:
            # Send DELETE request to OpenPhone API
            response = requests.delete(api_url, headers=headers)
            _logger.debug("OpenPhone API Response Status Code: %s", response.status_code)
            _logger.debug("OpenPhone API Response Content: %s", response.text)

            if response.status_code == 204:  # No Content indicates successful deletion
                _logger.info("Successfully deleted contact in OpenPhone: %s", partner.name)
            else:
                # Log and raise an error for non-successful status codes
                _logger.error("Failed to delete contact in OpenPhone: %s", response.text)
                raise UserError(_("Failed to delete contact in OpenPhone. Check logs for details."))

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to delete contact in OpenPhone: %s", str(e))
            raise UserError(_("Failed to delete contact in OpenPhone. Check logs for details."))

    def unlink(self):
        """Override unlink method to send delete requests to OpenPhone."""
        for partner in self:
            if partner.openphone_contact_id:
                try:
                    self._delete_openphone_contact(partner)
                except UserError as e:
                    _logger.warning("Contact deletion in OpenPhone failed for partner %s: %s", partner.name, str(e))
        return super(ResPartner, self).unlink()
