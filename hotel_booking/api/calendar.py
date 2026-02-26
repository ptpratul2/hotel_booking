# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Calendar API - returns booking events for FullCalendar.
"""

import json

import frappe
from frappe.desk.calendar import get_event_conditions, get_events as _get_events


@frappe.whitelist()
def get_booking_events(doctype, start, end, field_map, filters=None, fields=None):
	"""
	Get Booking events for calendar view.
	Adds guest name to title for better display.
	"""
	field_map = frappe._dict(json.loads(field_map))
	fields = frappe.parse_json(fields)

	if not fields:
		fields = ["name", "check_in", "check_out", "guest", "status", "total_amount"]

	# Get bookings with guest name (include all statuses for color coding)
	events = frappe.get_all(
		"Booking",
		fields=fields,
		filters=[
			["check_in", "<=", end],
			["check_out", ">=", start],
		],
	)

	result = []
	for e in events:
		d = frappe._dict(e)
		guest_name = frappe.db.get_value("Guest", d.guest, "guest_name") or ""
		d.title = f"{d.name} - {guest_name}" if guest_name else d.name
		d.allDay = 1
		result.append(d)

	return result
