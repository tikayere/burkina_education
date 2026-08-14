# Copyright (c) 2026, Burkina Education Project and contributors
# For license information, please see license.txt

"""Per-student aggregation used by both the Student Portal (own record) and
the Guardian Portal (each linked child) — one implementation instead of two
near-identical copies. Every function here takes an already-authorized
``student`` name; the *authorization* (own record / own child) happens one
call up, in ``student_api.py``/``guardian_api.py``, via
``portal/permissions.py``. See that module's docstring for why these read
with ``ignore_permissions=True`` rather than a doctype-level grant.
"""

import frappe
from frappe.utils import add_days, flt, nowdate

from burkina_education.academic import grading
from burkina_education.messaging.doctype.announcement.announcement import get_visible_announcements_for_student

OPEN_LIBRARY_STATUSES = ("Emprunté", "En retard")


def student_summary(student):
	info = frappe.db.get_value(
		"Student",
		student,
		[
			"student_name",
			"matricule",
			"grade",
			"school",
			"campus",
			"image",
			"status",
			"gender",
			"date_of_birth",
			"student_email_id",
			"student_mobile_number",
		],
		as_dict=True,
	)
	if not info:
		frappe.throw(frappe._("Élève introuvable."))
	if info.grade:
		info["grade_name"] = frappe.db.get_value("Grade", info.grade, "grade_name")
	if info.school:
		info["school_name"] = frappe.db.get_value("School", info.school, "school_name")
	return info


def guardians_of(student):
	rows = frappe.get_all(
		"Student Guardian", filters={"parent": student}, fields=["guardian", "relation"]
	)
	out = []
	for row in rows:
		g = frappe.db.get_value(
			"Guardian", row.guardian, ["guardian_name", "mobile_number", "email_address"], as_dict=True
		)
		if g:
			g["name"] = row.guardian
			g["relation"] = row.relation
			out.append(g)
	return out


def attendance_overview(student):
	today = nowdate()
	return {
		"last_30_days": grading.get_attendance_summary(student, add_days(today, -30), today),
		"this_year": grading.get_attendance_summary(student, add_days(today, -365), today),
		"monthly_trend": attendance_monthly_trend(student),
	}


#: French month abbreviations - Frappe's own ``frappe.utils.formatdate`` takes
#: "dd"/"mm"/"yyyy"-style tokens, not a "MMM" name token, so there's no
#: built-in way to get a short French month label from it. Exported (not
#: underscore-prefixed) since finance_api.py's own monthly trend needs the
#: same labels and there's no reason to duplicate the table.
MONTH_ABBR_FR = {
	1: "Janv", 2: "Févr", 3: "Mars", 4: "Avr", 5: "Mai", 6: "Juin",
	7: "Juil", 8: "Août", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Déc",
}


def attendance_monthly_trend(student, months=6):
	"""Month-by-month attendance percentage for the last ``months`` months -
	powers the "Évolution des présences" chart on the Student/Guardian
	Overview page (see frontend Overview.vue), the same shape as the
	marketing mockup's own dashboard chart. Same Student Attendance scope as
	``attendance_overview`` above, just grouped by calendar month instead of
	collapsed into one summary.
	"""
	from frappe.utils import add_months, getdate

	start = getdate(add_months(nowdate(), -(months - 1))).replace(day=1)
	rows = frappe.db.sql(
		"""
		select date_format(date, '%%Y-%%m') as ym,
			sum(case when status in ('Present', 'Late') then 1 else 0 end) as attended,
			count(*) as total
		from `tabStudent Attendance`
		where student = %(student)s and docstatus = 1 and date >= %(start)s
		group by ym
		""",
		{"student": student, "start": start},
		as_dict=True,
	)
	by_month = {r.ym: r for r in rows}

	out = []
	cursor = start
	for _ in range(months):
		key = cursor.strftime("%Y-%m")
		row = by_month.get(key)
		percentage = round(row.attended / row.total * 100, 1) if row and row.total else None
		out.append({"month": key, "label": MONTH_ABBR_FR[cursor.month], "percentage": percentage})
		cursor = getdate(add_months(cursor, 1))
	return out


def attendance_records(student, from_date, to_date):
	return frappe.get_all(
		"Student Attendance",
		filters={"student": student, "docstatus": 1, "date": ["between", (from_date, to_date)]},
		fields=["name", "date", "status", "remarks", "student_group"],
		order_by="date desc",
	)


def reports(student):
	term_reports = frappe.get_all(
		"Student Term Report",
		filters={"student": student, "docstatus": 1},
		fields=["name", "academic_year", "academic_term", "term_average", "max_average", "class_rank", "class_size"],
		order_by="creation desc",
	)
	annual_reports = frappe.get_all(
		"Student Annual Report",
		filters={"student": student, "docstatus": 1},
		fields=["name", "academic_year", "annual_average", "annual_rank", "class_size", "decision"],
		order_by="creation desc",
	)
	return {"term_reports": term_reports, "annual_reports": annual_reports}


def term_report_detail(student, name):
	doc = frappe.get_doc("Student Term Report", name)
	if doc.student != student or doc.docstatus != 1:
		frappe.throw(frappe._("Bulletin introuvable."), frappe.PermissionError)
	return doc.as_dict()


def annual_report_detail(student, name):
	doc = frappe.get_doc("Student Annual Report", name)
	if doc.student != student or doc.docstatus != 1:
		frappe.throw(frappe._("Bulletin annuel introuvable."), frappe.PermissionError)
	return doc.as_dict()


def invoices(student):
	rows = frappe.get_all(
		"Sales Invoice",
		filters={"student": student, "docstatus": 1},
		fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount", "currency", "status"],
		order_by="posting_date desc",
	)
	return {"invoices": rows, "outstanding_balance": sum(flt(r.outstanding_amount) for r in rows)}


def invoice_detail(student, name):
	doc = frappe.get_doc("Sales Invoice", name)
	if doc.student != student or doc.docstatus != 1:
		frappe.throw(frappe._("Facture introuvable."), frappe.PermissionError)

	payments = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Invoice", "reference_name": name, "docstatus": 1},
		fields=["parent as payment_entry", "allocated_amount"],
	)
	for p in payments:
		pe = frappe.db.get_value(
			"Payment Entry", p.payment_entry, ["posting_date", "mode_of_payment", "reference_no"], as_dict=True
		)
		p.update(pe or {})

	return {
		"name": doc.name,
		"posting_date": doc.posting_date,
		"due_date": doc.due_date,
		"grand_total": doc.grand_total,
		"outstanding_amount": doc.outstanding_amount,
		"currency": doc.currency,
		"status": doc.status,
		"items": [
			{"item_name": i.item_name, "amount": i.amount, "description": i.description} for i in doc.items
		],
		"payment_schedule": [
			{"due_date": s.due_date, "payment_amount": s.payment_amount, "outstanding": s.outstanding}
			for s in doc.payment_schedule
		],
		"payments": payments,
	}


def active_mobile_money_providers():
	"""Safe, secret-free provider list for the "Pay now" dialog — mirrors
	what ``finance/client_scripts/sales_invoice_mobile_money.js`` shows on
	the Desk side."""
	return frappe.get_all(
		"Mobile Money Provider",
		filters={"is_active": 1},
		fields=["name", "provider_name", "provider_code", "currency"],
		ignore_permissions=True,
	)


def library(student):
	membership = frappe.db.get_value(
		"Library Membership",
		{"student": student},
		["name", "status", "issue_date", "expiry_date", "max_books"],
		as_dict=True,
	)
	if not membership:
		return {"membership": None, "open_loans": [], "history": []}

	loans = frappe.get_all(
		"Library Transaction",
		filters={"membership": membership.name},
		fields=["name", "book_copy", "book_title", "status", "issue_date", "due_date", "return_date", "fine_amount", "fine_paid"],
		order_by="issue_date desc",
	)
	open_loans = [l for l in loans if l.status in OPEN_LIBRARY_STATUSES]
	history = [l for l in loans if l.status not in OPEN_LIBRARY_STATUSES]
	return {"membership": membership, "open_loans": open_loans, "history": history}


def transport(student):
	assignment = frappe.db.get_value(
		"Student Transport Assignment",
		{"student": student, "status": "Actif"},
		["name", "route", "stop_name", "start_date", "end_date"],
		as_dict=True,
	)
	if not assignment:
		return {"assignment": None}

	route = frappe.db.get_value(
		"Transport Route", assignment.route, ["route_name", "vehicle", "driver", "distance_km"], as_dict=True
	)
	if route:
		route["stops"] = frappe.get_all(
			"Transport Route Stop",
			filters={"parent": assignment.route},
			fields=["stop_name", "sequence", "pickup_time", "drop_time"],
			order_by="sequence",
		)
		if route.driver:
			route["driver_name"] = frappe.db.get_value("Driver", route.driver, "full_name")
	assignment["route_detail"] = route
	return {"assignment": assignment}


def canteen(student):
	subscription = frappe.db.get_value(
		"Canteen Subscription",
		{"student": student, "status": "Active"},
		["name", "meal_plan", "start_date", "end_date"],
		as_dict=True,
	)
	if not subscription:
		return {"subscription": None, "recent_consumption": []}

	subscription["meal_plan_detail"] = frappe.db.get_value(
		"Meal Plan", subscription.meal_plan, ["plan_name", "price_per_month"], as_dict=True
	)
	consumption = frappe.get_all(
		"Meal Consumption",
		filters={"subscription": subscription.name},
		fields=["date", "meal_type", "consumed"],
		order_by="date desc",
		limit=30,
	)
	return {"subscription": subscription, "recent_consumption": consumption}


def boarding(student):
	assignment = frappe.db.get_value(
		"Student Boarding Assignment",
		{"student": student, "status": "Actif"},
		["name", "bed", "supervisor", "check_in_date", "check_out_date"],
		as_dict=True,
	)
	if not assignment:
		return {"assignment": None}

	room_name = frappe.db.get_value("Boarding Bed", assignment.bed, "room")
	room = frappe.db.get_value("Boarding Room", room_name, ["room_number", "floor", "building"], as_dict=True) if room_name else None
	building = frappe.db.get_value("Boarding Building", room.building, "building_name") if room else None
	if assignment.supervisor:
		assignment["supervisor_name"] = frappe.db.get_value("Employee", assignment.supervisor, "employee_name")
	assignment["bed_number"] = frappe.db.get_value("Boarding Bed", assignment.bed, "bed_number")
	assignment["room"] = room
	assignment["building_name"] = building
	return {"assignment": assignment}


def discipline(student):
	"""Read-only history of the student's own Disciplinary Case records.
	Exposed to both Student and Guardian (a school-discipline record is
	normally something a family is entitled to see, unlike Clinic Visit -
	see docs/architecture.md section L)."""
	return frappe.get_all(
		"Disciplinary Case",
		filters={"student": student},
		fields=["name", "date", "incident_type", "severity", "status", "description", "action_taken", "resolution"],
		order_by="date desc",
		ignore_permissions=True,
	)


def clinic(student):
	"""Guardian-only (see ``guardian_api.py`` — this function is never
	called from ``student_api.py``). Health data is the tightest access
	boundary in the whole app; even here it's read-only and never exposed
	to a Student's own login."""
	return frappe.get_all(
		"Clinic Visit",
		filters={"student": student},
		fields=["name", "date", "complaint", "treatment", "referral", "status", "follow_up"],
		order_by="date desc",
		ignore_permissions=True,
	)


def announcements(student, limit=20):
	return get_visible_announcements_for_student(student, limit=limit)


def upcoming_schedule(student, limit=15):
	groups = frappe.get_all(
		"Student Group Student", filters={"student": student, "active": 1}, pluck="parent"
	)
	if not groups:
		return []
	return frappe.get_all(
		"Course Schedule",
		filters={"student_group": ["in", groups], "schedule_date": [">=", nowdate()]},
		fields=["name", "student_group", "course", "instructor_name", "room", "schedule_date", "from_time", "to_time"],
		order_by="schedule_date asc, from_time asc",
		limit=limit,
		ignore_permissions=True,
	)


def inbox(user, limit=50):
	"""In-app message center: every ``Message Log`` this app's notification
	engine (``messaging/notify.py``) has ever delivered to this portal user
	(payment confirmations, fee reminders, result-available, announcements,
	a teacher's direct note) — one unified inbox instead of per-event
	one-off UI."""
	return frappe.get_all(
		"Message Log",
		filters={"recipient_doctype": "User", "recipient": user, "channel": "In-App"},
		fields=["name", "event_key", "subject", "message", "status", "queued_on", "reference_doctype", "reference_name"],
		order_by="queued_on desc",
		limit=limit,
		ignore_permissions=True,
	)
