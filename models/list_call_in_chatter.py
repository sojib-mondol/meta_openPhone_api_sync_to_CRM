from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)

import urllib.parse

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_fetch_call_logs(self):
        """
        Button action to fetch call logs for selected partners.
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('openphone.api.key', default='')
        if not api_key:
            raise UserError(_("OpenPhone API key is not configured."))

        openphone_phone_number_id = "PNultOAaGq"  # Replace with your actual phone number ID.

        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json',
        }

        for partner in self:
            if not partner.phone:
                partner.message_post(
                    body=_("No phone number is defined for this partner."),
                    subject=_("Call Logs Fetching Result"),
                )
                continue

            # Normalize the phone number
            sanitized_phone = partner.phone.strip().replace(" ", "")  # Remove spaces
            encoded_phone = urllib.parse.quote(sanitized_phone)  # URL-encode the phone number

            api_url = (
                f"https://api.openphone.com/v1/calls"
                f"?phoneNumberId={openphone_phone_number_id}"
                f"&participants={encoded_phone}"
                f"&maxResults=10"
            )

            _logger.debug("API URL: %s", api_url)  # Log the constructed URL

            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                call_logs = response.json().get('data', [])
                
                _logger.debug("API Response: %s", response.json())  # Log API response
                _logger.debug("Partner Phone: %s", sanitized_phone)  # Log normalized phone

                if not call_logs:
                    partner.message_post(
                        body=_("No call logs found for the partner."),
                        subject=_("Call Logs Fetching Result"),
                    )
                    continue
            except requests.exceptions.RequestException as e:
                _logger.error("Error fetching call logs for contact %s: %s", partner.name, e)
                partner.message_post(
                    body=_("Error fetching call logs: %s") % str(e),
                    subject=_("Call Logs Fetching Error"),
                )
                continue

            # Process call logs and post to chatter
            messages = []
            for call in call_logs:
                participants = call.get('participants', [])
                if sanitized_phone not in participants:
                    continue

                direction = call.get('direction', 'unknown').capitalize()
                status = call.get('status', 'unknown').capitalize()
                duration = call.get('duration', 0)
                created_at = call.get('createdAt')
                completed_at = call.get('completedAt')

                message = _(
                    "<b>New Call Log:</b><br/>"
                    "- <b>Direction:</b> %s<br/>"
                    "- <b>Status:</b> %s<br/>"
                    "- <b>Duration:</b> %s seconds<br/>"
                    "- <b>Participants:</b> %s<br/>"
                    "- <b>Created At:</b> %s<br/>"
                    "- <b>Completed At:</b> %s"
                ) % (direction, status, duration, ', '.join(participants), created_at, completed_at)
                messages.append(message)

            if messages:
                partner.message_post(
                    body='<br/><hr/>'.join(messages),
                    subject=_("Fetched Call Logs"),
                )
            else:
                partner.message_post(
                    body=_("No call logs match the partner's phone number."),
                    subject=_("Call Logs Fetching Result"),
                )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Call Logs Fetched'),
                'message': _('Call logs have been successfully fetched and posted to the chatter.'),
                'sticky': False,
            },
        }
