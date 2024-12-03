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
        """Fetch phone numbers and sync with Odoo contacts."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('openphone.api.key', default='')

        if not api_key:
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
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json().get("data", [])
            
            if not data:
                _logger.warning("No phone numbers found in OpenPhone API response.")
                return

            for phone_data in data:
                # Process each phone number entry
                self._sync_phone_number(phone_data)

            _logger.info("OpenPhone contact synchronization completed successfully.")

        except requests.exceptions.RequestException as e:
            _logger.error("Failed to fetch data from OpenPhone API: %s", str(e))
            raise UserError(_("Failed to fetch data from OpenPhone API."))

    def _sync_phone_number(self, phone_data):
        """Sync a single phone number and create contact."""
        phone_number = phone_data.get('number')
        formatted_phone_number = phone_data.get('formattedNumber')  # Use formatted number
        phone_name = phone_data.get('name', '')  # Use the name from phone data (e.g., "ALL CITY CLEANER" or "America")

        if not phone_number or not phone_name:
            _logger.warning("Phone number or name missing. Skipping: %s", phone_data)
            return

        # Log the phone data to debug
        _logger.info("Processing phone data: number=%s, name=%s", phone_number, phone_name)

        # Check if a contact already exists with the same number
        existing_contact = self.env['res.partner'].search([('phone', '=', formatted_phone_number)], limit=1)

        if existing_contact:
            _logger.info("Contact already exists with number: %s", formatted_phone_number)
        else:
            # Create new contact in Odoo
            contact_values = {
                'name': phone_name,  # Use the name from the phone data
                'phone': formatted_phone_number,  # Use the formatted phone number
            }
            
            _logger.info("Creating new contact with values: %s", contact_values)
            
            new_contact = self.env['res.partner'].create(contact_values)
            new_contact.message_post(
                body=_("New contact created with phone number '%s'.") % formatted_phone_number
            )
