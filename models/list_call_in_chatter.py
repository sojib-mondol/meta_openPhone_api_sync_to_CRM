from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import requests
import logging
from datetime import datetime
import urllib.parse
from markupsafe import Markup

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _normalize_phone_number(self, phone):
        """
        Normalize the phone number to remove spaces, dashes, and parentheses,
        and ensure it has a leading '+' for international format.
        """
        cleaned_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        if not cleaned_phone.startswith('+'):
            cleaned_phone = '+1' + cleaned_phone
        return cleaned_phone

    def _fetch_call_recording(self, call_id, headers):
        """
        Fetch the call recording URL for a specific call ID.
        """
        api_url = f"https://api.openphone.com/v1/call-recordings/{call_id}"
        
        try:
            _logger.debug("Fetching call recording for call ID %s", call_id)
            
            # Send GET request to OpenPhone API
            response = requests.get(api_url, headers=headers)
            
            # Log the response status code and body
            _logger.debug("API response status code for call recording request: %s", response.status_code)
            _logger.debug("API response body for call recording request: %s", response.text)
            
            # Raise an error for bad responses (non-200 status codes)
            response.raise_for_status()

            # Parse the response JSON
            recording_data = response.json()
            
            _logger.debug("Call recording data for call ID %s: %s", call_id, recording_data)

            # Ensure 'data' key exists and contains a list with recordings
            if 'data' in recording_data and isinstance(recording_data['data'], list) and len(recording_data['data']) > 0:
                # Access the first recording in the 'data' array
                recording_info = recording_data['data'][0]
                
                _logger.debug("Recording info for call ID %s: %s", call_id, recording_info)
                
                # Check if 'url' key is present in the recording info
                if 'url' in recording_info:
                    _logger.debug("Recording URL found for call ID %s: %s", call_id, recording_info['url'])
                    return recording_info['url']
                else:
                    _logger.warning("Recording URL not found for call ID %s. Full API response: %s", call_id, recording_data)
                    return None
            else:
                _logger.warning("No recording data found for call ID %s. Full API response: %s", call_id, recording_data)
                return None
        except requests.exceptions.RequestException as e:
            # Log any request exception (like network issues or non-200 responses)
            _logger.error("Error fetching call recording for call ID %s: %s", call_id, e)
            return None

    def _format_call_log_message(self, call, sanitized_phone, index, headers):
        """
        Format a single call log into an HTML message for the chatter.
        """
        
        # Log the full JSON data of the call for debugging
        _logger.debug("Processing call log %d: %s", index, call)
    
        direction = tools.html_escape(call.get('direction', 'unknown').capitalize())
        status = tools.html_escape(call.get('status', 'unknown').capitalize())
        duration = tools.html_escape(str(call.get('duration', 0)))

        created_at_str = call.get('createdAt')
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')

        completed_at_str = call.get('completedAt')
        completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')

        participants = ', '.join(tools.html_escape(p) for p in call.get('participants', []))

        # Get the call ID from the JSON data
        call_id = call.get('id')
        call_id_html = f"<li><b>Call ID:</b> {tools.html_escape(call_id)}</li>" if call_id else "<li><b>Call ID:</b> Not Available</li>"

        # Call recording URL (if available)
        call_recording_url = None
        if call_id:
            call_recording_url = self._fetch_call_recording(call_id, headers)

        # Prepare HTML for the call log message
        call_recording_html = (
            f"<li><b>Call Recording:</b> <a href='{tools.html_escape(call_recording_url)}' target='_blank'>Download</a></li>"
            if call_recording_url else "<li><b>Call Recording:</b> Not Available</li>"
        )

        # Return the formatted message for the chatter
        return _(
            """
            <b>Call Log %d:</b><br/>
            <ul>
                <li><b>Direction:</b> %s</li>
                <li><b>Status:</b> %s</li>
                <li><b>Duration:</b> %s seconds</li>
                <li><b>Participants:</b> %s</li>
                <li><b>Created At:</b> %s</li>
                <li><b>Completed At:</b> %s</li>
                %s
                %s
            </ul>
            """
        ) % (index, direction, status, duration, participants, created_at, completed_at, call_id_html, call_recording_html)

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

            sanitized_phone = self._normalize_phone_number(partner.phone)
            encoded_phone = urllib.parse.quote(sanitized_phone)
            api_url = (
                f"https://api.openphone.com/v1/calls"
                f"?phoneNumberId={openphone_phone_number_id}"
                f"&participants={encoded_phone}"
                f"&maxResults=10"
            )

            _logger.debug("Fetching call logs for partner %s. API URL: %s", partner.name, api_url)

            try:
                response = requests.get(api_url, headers=headers)
                _logger.debug("API response status code for call logs: %s", response.status_code)
                _logger.debug("API response body for call logs: %s", response.text)
                response.raise_for_status()
                call_logs = response.json().get('data', [])

                if not call_logs:
                    partner.message_post(
                        body=_("No call logs found for this partner."),
                        subject=_("Call Logs Fetching Result"),
                    )
                    continue

                messages = [
                    self._format_call_log_message(call, sanitized_phone, index + 1, headers)
                    for index, call in enumerate(call_logs)
                    if sanitized_phone in call.get('participants', [])
                ]

                if messages:
                    partner.message_post(
                        body=Markup('<br/>'.join(messages)),
                        subject=_("Fetched Call Logs"),
                        subtype_id=self.env.ref('mail.mt_note').id,
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
