# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""SMS/WhatsApp provider abstraction (master.md §33/§34/§62) - mirrors
finance/mobile_money/gateway.py's adapter pattern exactly, so the same
review already applies here: business logic (``communication.notify``)
only ever talks to ``BaseMessagingProvider``, never to a specific vendor
SDK. Adding a provider means adding one adapter class and registering it in
``PROVIDER_ADAPTERS``, nothing else changes.

No real Twilio/WhatsApp Cloud API credentials exist in this dev
environment, so ``send`` is stubbed to the shape a real call would return:
while ``sandbox_mode`` is on it always succeeds (exactly like a real
provider's own sandbox/test mode). Flipping ``sandbox_mode`` off in
production requires implementing a real HTTP call - the interface does
not change.
"""

import frappe


class BaseMessagingProvider:
	def __init__(self, provider_doc):
		self.provider = provider_doc

	def send(self, log_doc):
		"""Send ``log_doc.message`` to ``log_doc.phone_number`` (SMS/WhatsApp).
		Must return a dict with at least
		``{"status": "Sent"|"Failed", "provider_message_id": ..., "response": ...}``.
		"""
		if self.provider.sandbox_mode:
			return {
				"status": "Sent",
				"provider_message_id": frappe.generate_hash(length=12),
				"response": {"sandbox": True},
			}
		raise NotImplementedError(
			f"{self.provider.provider_name}: sandbox_mode is off but no live send call has "
			"been implemented for this provider."
		)


class GenericHTTPProvider(BaseMessagingProvider):
	"""Fallback for any HTTP SMS gateway exposing a simple send endpoint.

	Real integration point: POST to ``self.provider.api_base_url`` using
	``self.provider.api_key`` / ``self.provider.get_password("api_secret")``.
	"""

	pass


class TwilioProvider(BaseMessagingProvider):
	# Real integration point: use the Twilio SDK/REST API with
	# self.provider.get_password("api_key") (Account SID) /
	# self.provider.get_password("api_secret") (Auth Token) and
	# self.provider.sender_id (the Twilio "From" number).
	pass


class WhatsAppCloudProvider(BaseMessagingProvider):
	# Real integration point: POST to the WhatsApp Cloud API (Meta) using
	# self.provider.get_password("api_key") (access token) and
	# self.provider.sender_id (the WhatsApp Business phone number ID).
	pass


PROVIDER_ADAPTERS = {
	"Generic HTTP": GenericHTTPProvider,
	"Twilio": TwilioProvider,
	"WhatsApp Cloud API": WhatsAppCloudProvider,
}


def get_adapter(provider_doc):
	adapter_cls = PROVIDER_ADAPTERS.get(provider_doc.provider_code, BaseMessagingProvider)
	return adapter_cls(provider_doc)


def get_default_provider(channel):
	"""Explicit ``is_default`` first; else the only active provider for that
	channel if there's exactly one - avoids forcing a single-provider school
	to configure a default they have no real choice about."""
	name = frappe.db.get_value("Messaging Provider", {"channel": channel, "is_default": 1, "is_active": 1})
	if name:
		return frappe.get_cached_doc("Messaging Provider", name)

	active = frappe.get_all("Messaging Provider", filters={"channel": channel, "is_active": 1}, pluck="name")
	if len(active) == 1:
		return frappe.get_cached_doc("Messaging Provider", active[0])
	return None
