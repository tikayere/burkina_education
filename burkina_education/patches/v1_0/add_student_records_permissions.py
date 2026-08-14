# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""``after_install`` only ever runs once, at install time - sites that
installed ``burkina_education`` before Registrar/Academic Director/School
Director got real permissions on Student/Guardian (setup/install.py::
create_student_records_permissions) need this run once as a patch. Reuses
the exact same idempotent helper ``after_install`` itself calls, so there is
nothing to duplicate or drift.
"""

from burkina_education.setup.install import create_student_records_permissions


def execute():
	create_student_records_permissions()
