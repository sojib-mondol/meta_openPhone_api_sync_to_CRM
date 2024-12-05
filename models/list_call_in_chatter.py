from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import requests
import logging
from datetime import datetime
import urllib.parse

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _normalize_phone_number(self, phone):
        """
        Normalize the phone number to remove spaces, dashes, and parentheses,
        and ensure it has a leading '+' for international format.
        """
        # Remove non-digit characters except '+'
        cleaned_phone = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Ensure it starts with '+1' if it does not already have a country code
        if not cleaned_phone.startswith('+'):
            cleaned_phone = '+1' + cleaned_phone

        return cleaned_phone

    def _format_call_log_message(self, call, sanitized_phone):
        """
        Format a single call log into an HTML message for the chatter.
        """
        direction = tools.html_escape(call.get('direction', 'unknown').capitalize())
        status = tools.html_escape(call.get('status', 'unknown').capitalize())
        duration = tools.html_escape(str(call.get('duration', 0)))

        created_at_str = call.get('createdAt')
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')

        completed_at_str = call.get('completedAt')
        completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')

        participants = ', '.join(tools.html_escape(p) for p in call.get('participants', []))

        return _(
            """
            <b>New Call Log:</b><br/>
            <ul>
                <li><b>Direction:</b> %s</li>
                <li><b>Status:</b> %s</li>
                <li><b>Duration:</b> %s seconds</li>
                <li><b>Participants:</b> %s</li>
                <li><b>Created At:</b> %s</li>
                <li><b>Completed At:</b> %s</li>
            </ul>
            """
        ) % (direction, status, duration, participants, created_at, completed_at)

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
            sanitized_phone = self._normalize_phone_number(partner.phone)
            encoded_phone = urllib.parse.quote(sanitized_phone)  # URL-encode the phone number
            api_url = (
                f"https://api.openphone.com/v1/calls"
                f"?phoneNumberId={openphone_phone_number_id}"
                f"&participants={encoded_phone}"
                f"&maxResults=10"
            )

            _logger.debug("Fetching call logs for partner %s. API URL: %s", partner.name, api_url)

            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                call_logs = response.json().get('data', [])

                if not call_logs:
                    partner.message_post(
                        body=_("No call logs found for this partner."),
                        subject=_("Call Logs Fetching Result"),
                    )
                    continue

                messages = [
                    self._format_call_log_message(call, sanitized_phone)
                    for call in call_logs
                    if sanitized_phone in call.get('participants', [])
                ]

                if messages:
                    partner.message_post(
                        body='<br/>'.join(messages),
                        subject=_("Fetched Call Logs"),
                        subtype_id=self.env.ref('mail.mt_note').id,  # Ensure proper message subtype
                    )
                else:
                    partner.message_post(
                        body=_("No call logs match the partner's phone number."),
                        subject=_("Call Logs Fetching Result"),
                    )
            except requests.exceptions.RequestException as e:
                _logger.error("Error fetching call logs for partner %s: %s", partner.name, e)
                partner.message_post(
                    body=_("Error fetching call logs: %s") % tools.html_escape(str(e)),
                    subject=_("Call Logs Fetching Error"),
                )
            except ValueError as e:
                _logger.error("Error parsing API response for partner %s: %s", partner.name, e)
                partner.message_post(
                    body=_("Error parsing API response: %s") % tools.html_escape(str(e)),
                    subject=_("Call Logs Fetching Error"),
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
