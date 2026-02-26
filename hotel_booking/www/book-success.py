# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	booking_id = frappe.form_dict.get("booking_id")
	context.booking_id = booking_id
	context.paid = frappe.form_dict.get("paid") == "1" and booking_id
	return context
