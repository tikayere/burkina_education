# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Communications Portal (Secretary). Announcement
CRUD (draft/edit) and Notification Template CRUD are done directly from the
frontend (Secretary already has full permissions — docs/architecture.md
section M); publishing/archiving an Announcement calls its own existing
whitelisted doc methods (``Announcement.publish``/``archive``, see
``messaging/doctype/announcement/announcement.py``) via Frappe's generic
``run_doc_method`` rather than a new wrapper here. This module supplies only
the dashboard.
"""

import frappe

from burkina_education.portal.permissions import require_any_role


@frappe.whitelist()
def get_dashboard():
	require_any_role("Secretary", "Academic Director", "School Director")

	drafts = frappe.get_all(
		"Announcement",
		filters={"publication_status": "Draft"},
		fields=["name", "title", "audience_type", "priority", "start_date"],
		order_by="modified desc",
		limit=10,
	)
	published = frappe.get_all(
		"Announcement",
		filters={"publication_status": "Published"},
		fields=["name", "title", "audience_type", "priority", "published_on"],
		order_by="published_on desc",
		limit=10,
	)

	today = frappe.utils.nowdate()
	sent_today = frappe.db.count("Message Log", {"creation": [">=", f"{today} 00:00:00"], "status": "Sent"})
	failed_today = frappe.db.count("Message Log", {"creation": [">=", f"{today} 00:00:00"], "status": "Failed"})
	templates = frappe.db.count("Notification Template")

	return {
		"drafts": drafts,
		"published": published,
		"sent_today": sent_today,
		"failed_today": failed_today,
		"templates": templates,
	}
