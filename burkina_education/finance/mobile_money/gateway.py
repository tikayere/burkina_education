# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Mobile money provider abstraction (master.md §28/§62): business logic
(``finance.mobile_money.api``) only ever talks to ``BaseMobileMoneyProvider``,
never to a specific vendor SDK - swapping/adding a provider means adding one
adapter class here, nothing else changes.

    Payment
       |
    Mobile Money Provider (config: credentials, mode_of_payment, sandbox_mode)
       |
    get_adapter() -> BaseMobileMoneyProvider
       |-- OrangeMoneyProvider
       |-- MoovMoneyProvider
       `-- (add more here)

No real Orange Money / Moov Money credentials exist in this dev environment,
so ``initiate`` is stubbed to the shape a real call would return, and
``verify`` (the only thing allowed to confirm a payment - see
docs/architecture.md section H) auto-confirms while ``sandbox_mode`` is on,
exactly like the real providers' own sandbox environments behave. Flipping
``sandbox_mode`` off in production requires implementing a real HTTP call in
``verify`` - the interface does not change.
"""

import frappe


class BaseMobileMoneyProvider:
	def __init__(self, provider_doc):
		self.provider = provider_doc

	def initiate(self, transaction):
		"""Start a payment on the provider's side. Must return a dict with at
		least ``{"gateway_transaction_id": ..., "status": "Pending"|"Failed"}``.
		"""
		raise NotImplementedError

	def verify(self, transaction):
		"""Server-side status check against the provider - the only source of
		truth for whether a payment actually succeeded. Must return a dict
		with at least ``{"status": "Success"|"Failed", ...}``.
		"""
		if self.provider.sandbox_mode:
			return {"status": "Success", "sandbox": True}
		raise NotImplementedError(
			f"{self.provider.provider_name}: sandbox_mode is off but no live "
			"status-check call has been implemented for this provider."
		)


class OrangeMoneyProvider(BaseMobileMoneyProvider):
	def initiate(self, transaction):
		# Real integration point: POST to Orange Money's Web Payment API using
		# self.provider.api_key / self.provider.get_password("api_secret").
		return {"gateway_transaction_id": frappe.generate_hash(length=12), "status": "Pending"}


class MoovMoneyProvider(BaseMobileMoneyProvider):
	def initiate(self, transaction):
		# Real integration point: POST to Moov Money's payment API using
		# self.provider.api_key / self.provider.get_password("api_secret").
		return {"gateway_transaction_id": frappe.generate_hash(length=12), "status": "Pending"}


PROVIDER_ADAPTERS = {
	"Orange Money": OrangeMoneyProvider,
	"Moov Money": MoovMoneyProvider,
}


def get_adapter(provider_doc):
	adapter_cls = PROVIDER_ADAPTERS.get(provider_doc.provider_code, BaseMobileMoneyProvider)
	return adapter_cls(provider_doc)
