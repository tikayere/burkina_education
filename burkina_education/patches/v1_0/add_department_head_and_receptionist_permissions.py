# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""``after_install`` only ever runs once, at install time - sites that
installed ``burkina_education`` before the Department Head/Receptionist
Roles got real permissions and a portal (docs/architecture.md section N)
need this run once as a patch. Reuses the exact same idempotent helpers
``after_install`` itself calls, so there is nothing to duplicate or drift.
"""

from burkina_education.setup.install import (
	create_department_head_permissions,
	create_receptionist_permissions,
)


def execute():
	create_department_head_permissions()
	create_receptionist_permissions()
