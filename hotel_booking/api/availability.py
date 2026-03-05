# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Room availability API - optimized SQL queries for production.
Uses overlapping date condition: check_in < existing_check_out AND check_out > existing_check_in
"""

from datetime import datetime

import frappe
from frappe import _


# @frappe.whitelist(allow_guest=True)
# def get_room_types():
# 	"""Return list of room types for booking form. Uses ignore_permissions for public booking page."""
# 	return frappe.get_all(
# 		"Room Type",
# 		fields=["name", "room_type_name", "base_price", "max_guests", "image", "description"],
# 		order_by="room_type_name",
# 		ignore_permissions=True,
# 	)

@frappe.whitelist(allow_guest=True)
def get_room_types():

    rooms = frappe.get_all(
        "Room Type",
        fields=[
            "name",
            "room_type_name",
            "base_price",
            "max_guests",
            "image",
			"description"
        ]
    )

    for room in rooms:

        room["features"] = frappe.get_all(
            "Room Feature",
            filters={"parent": room["name"]},
            fields=["feature_name", "icon", "description"]
        )

        room["amenities"] = frappe.get_all(
            "Room Amenity",
            filters={"parent": room["name"]},
            fields=["amenity_name", "icon", "description"]
        )
        
        room["tariffs"] = frappe.get_all(
            "Room Tariff",
            filters={"parent": room["name"]},
            fields=["category", "price"]
        )
        
        room["pricing"] = frappe.get_all(
            "Room Pricing",
            filters={"parent": room["name"]},
            fields=["plan_name", "category", "price"]
        )

    return rooms


@frappe.whitelist(allow_guest=True)
def check_room_availability(room_type: str, check_in: str, check_out: str) -> int:
	"""
	Check available room count for given room type and date range.
	Uses optimized SQL - no Python loops.

	Overlapping condition: check_in < existing_check_out AND check_out > existing_check_in
	Excludes Cancelled bookings.

	Args:
		room_type: Room Type name
		check_in: Check-in date (YYYY-MM-DD)
		check_out: Check-out date (YYYY-MM-DD)

	Returns:
		Available rooms count (int)
	"""
	# Validate inputs
	if not room_type:
		frappe.throw(_("Room Type is required"))

	# Parse and validate dates
	try:
		check_in_dt = datetime.strptime(str(check_in).strip(), "%Y-%m-%d").date()
		check_out_dt = datetime.strptime(str(check_out).strip(), "%Y-%m-%d").date()
	except (ValueError, TypeError):
		frappe.throw(_("Invalid date format. Use YYYY-MM-DD"))

	if check_in_dt >= check_out_dt:
		frappe.throw(_("Check-out date must be after check-in date"))

	if not frappe.db.exists("Room Type", room_type):
		frappe.throw(_("Room Type {0} does not exist").format(room_type))

	# Total available rooms of this type (status = Available, not Maintenance/Blocked)
	total_rooms = frappe.db.sql(
		"""
		SELECT COUNT(name) FROM `tabRoom`
		WHERE room_type = %(room_type)s
		AND status = 'Available'
		""",
		{"room_type": room_type},
		as_dict=False,
	)[0][0]

	if total_rooms == 0:
		return 0

	# Count rooms already booked for overlapping period
	# Overlap: new_check_in < existing_check_out AND new_check_out > existing_check_in
	# Exclude Cancelled status
	booked_rooms = frappe.db.sql(
		"""
		SELECT COUNT(DISTINCT br.room) as cnt
		FROM `tabBooking Room` br
		INNER JOIN `tabBooking` b ON b.name = br.parent
		WHERE br.room_type = %(room_type)s
		AND b.status != 'Cancelled'
		AND b.docstatus = 0
		AND %(check_in)s < b.check_out
		AND %(check_out)s > b.check_in
		""",
		{"room_type": room_type, "check_in": check_in, "check_out": check_out},
		as_dict=False,
	)[0][0]

	available = max(0, int(total_rooms) - int(booked_rooms))
	return available
