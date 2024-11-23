# -*- coding: utf-8 -*-
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class OpenPhoneContactSync(models.Model):
    _name = 'openphone.contact.sync'
    _description = 'Sync Contacts with OpenPhone'

    @api.model
    def fetch_and_sync_contacts(self):
        """Fetch users from OpenPhone and sync them with Odoo contacts."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('openphone.api.key', default='')
        _logger.debug("Using OpenPhone API key: %s", api_key)
        print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>{api_key}")
        
        if not api_key:
            _logger.warning("OpenPhone API key is missing. Please configure it.")
            raise UserError(_("No OpenPhone API key found. Please configure it in settings."))

        # API URL
        api_url = "https://api.openphone.com/v1/phone-numbers"

        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        try:
            # Fetch data from OpenPhone API
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            data = response.json().get("data", [])
            _logger.info("Fetched %d phone numbers from OpenPhone API", len(data))
            
            if not data:
                _logger.warning("No data found in the OpenPhone API response.")
                
            for item in data:
                # Sync users from OpenPhone to Odoo contacts
                for user in item.get('users', []):
                    self._sync_openphone_user_to_odoo(user)

            _logger.info("OpenPhone contact synchronization completed successfully.")
            return None  # Return None instead of True to avoid action processing issues

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to fetch data from OpenPhone API: %s", str(e))
            raise ValueError(_("Failed to fetch data from OpenPhone API."))


    def _sync_openphone_user_to_odoo(self, user_data):
        """Create or update an Odoo contact based on OpenPhone user data."""
        email = user_data.get('email')
        if not email:
            _logger.warning("Skipping user with missing email: %s", user_data)
            return

        partner = self.env['res.partner'].search([('email', '=', email)], limit=1)
        values = {
            'name': f"{user_data.get('firstName')} {user_data.get('lastName')}".strip(),
            'email': email,
        }

        if partner:
            _logger.info("Updating existing contact: %s", email)
            partner.write(values)
        else:
            _logger.info("Creating new contact: %s", email)
            self.env['res.partner'].create(values)