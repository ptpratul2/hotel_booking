# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	context.room_types = frappe.get_all(
		"Room Type",
		fields=["name", "room_type_name", "base_price", "max_guests"],
		order_by="room_type_name",
	)
	return context
