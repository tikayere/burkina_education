# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Whitelisted API for the Vue Boarding Manager Portal. Building/Room/Bed
CRUD and the actual check-out (``Student Boarding Assignment.check_out()``,
already a whitelisted doc method) are done directly from the frontend
(full permissions — docs/architecture.md section M); this module supplies
the dashboard and an "assign a bed" helper, since finding a free bed by hand
across every room would be tedious — exactly the "tedious to navigate"
complaint this whole batch of portals exists to fix.
"""

import frappe

from burkina_education.portal.permissions import require_any_role
from burkina_education.portal.roles import current_academic_year


@frappe.whitelist()
def get_dashboard():
	require_any_role("Boarding Manager")

	buildings = frappe.db.count("Boarding Building")
	rooms = frappe.db.count("Boarding Room")
	beds = frappe.db.count("Boarding Bed")
	occupied = frappe.db.count("Boarding Bed", {"status": "Occupé"})
	available = frappe.db.count("Boarding Bed", {"status": "Disponible"})
	out_of_service = frappe.db.count("Boarding Bed", {"status": "Hors service"})
	active_assignments = frappe.db.count("Student Boarding Assignment", {"status": "Actif"})

	buildings_rows = frappe.get_all("Boarding Building", fields=["name", "building_name", "supervisor"])
	for b in buildings_rows:
		room_names = frappe.get_all("Boarding Room", filters={"building": b.name}, pluck="name")
		b["room_count"] = len(room_names)
		b["bed_count"] = frappe.db.count("Boarding Bed", {"room": ["in", room_names or [""]]})
		b["occupied_count"] = frappe.db.count(
			"Boarding Bed", {"room": ["in", room_names or [""]], "status": "Occupé"}
		)
		if b.supervisor:
			b["supervisor_name"] = frappe.db.get_value("Employee", b.supervisor, "employee_name")

	return {
		"buildings": buildings,
		"rooms": rooms,
		"beds": beds,
		"occupied": occupied,
		"available": available,
		"out_of_service": out_of_service,
		"active_assignments": active_assignments,
		"buildings_detail": buildings_rows,
	}


@frappe.whitelist()
def get_available_beds():
	require_any_role("Boarding Manager")

	beds = frappe.get_all(
		"Boarding Bed", filters={"status": "Disponible"}, fields=["name", "bed_number", "room"], order_by="room"
	)
	for bed in beds:
		room = frappe.db.get_value("Boarding Room", bed.room, ["room_number", "building"], as_dict=True)
		if room:
			bed["room_number"] = room.room_number
			bed["building_name"] = frappe.db.get_value("Boarding Building", room.building, "building_name")
	return beds


@frappe.whitelist()
def assign_bed(student, bed, academic_year=None):
	require_any_role("Boarding Manager")

	doc = frappe.get_doc(
		{
			"doctype": "Student Boarding Assignment",
			"student": student,
			"bed": bed,
			"academic_year": academic_year or current_academic_year(),
			"check_in_date": frappe.utils.nowdate(),
			"status": "Actif",
		}
	).insert()
	return doc.name
