# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""``after_install`` only ever runs once, at install time - sites that
installed ``burkina_education`` before ``create_property_setters()`` grew
the ``TITLE_LINK_DOCTYPES`` block (Guardian/Instructor/Room/Fees/Fee
Structure/Employee/Driver showing an opaque autoname instead of their name
in every Link dropdown/awesomebar result - see docs/architecture.md) need
this run once as a patch. Reuses the exact same idempotent helper
``after_install`` itself calls, so there is nothing to duplicate or drift.
"""

from burkina_education.setup.install import create_property_setters


def execute():
	create_property_setters()
