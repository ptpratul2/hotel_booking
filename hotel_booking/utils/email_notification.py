# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Email automation - send confirmation email when booking status changes to Confirmed.
"""

import frappe
from frappe import _


def send_booking_confirmation_email(doc, method=None):
	"""
	Called from doc_events on Booking on_update.
	Send email when status changes to Confirmed.
	"""
	if doc.status != "Confirmed":
		return

	# Only send if status was just changed to Confirmed (avoid duplicate emails)
	if doc.get_doc_before_save() and doc.get_doc_before_save().status == "Confirmed":
		return

	guest = frappe.get_doc("Guest", doc.guest)
	if not guest.email:
		return

	# Get hotel contact from first Hotel or settings
	hotel_contact = _get_hotel_contact()

	subject = _("Booking Confirmed - {0}").format(doc.name)

	# Build room details
	room_details = []
	for row in doc.rooms or []:
		room_details.append(
			"- {0} ({1}): {2} nights @ {3} = {4}".format(
				row.room_type,
				row.room,
				row.nights,
				frappe.format_value(row.price_per_night, {"fieldtype": "Currency"}),
				frappe.format_value(row.amount, {"fieldtype": "Currency"}),
			)
		)
	rooms_text = "\n".join(room_details) if room_details else "-"

	message = f"""
<p>Dear {guest.guest_name},</p>

<p>Your booking has been confirmed. Here are the details:</p>

<p><strong>Booking ID:</strong> {doc.name}</p>
<p><strong>Check-in:</strong> {doc.check_in}</p>
<p><strong>Check-out:</strong> {doc.check_out}</p>
<p><strong>Total Amount:</strong> {frappe.format_value(doc.total_amount, {'fieldtype': 'Currency'})}</p>

<p><strong>Room(s):</strong></p>
<pre>{rooms_text}</pre>

{f'<p><strong>Hotel Contact:</strong> {hotel_contact}</p>' if hotel_contact else ''}

<p>Thank you for your booking!</p>
"""

	frappe.sendmail(
		recipients=[guest.email],
		subject=subject,
		message=message,
		delayed=False,
	)


def _get_hotel_contact() -> str:
	"""Get hotel contact info for email."""
	try:
		settings = frappe.get_single("Hotel Booking Settings")
		if settings and getattr(settings, "hotel_contact", None):
			return str(settings.hotel_contact).strip()
	except Exception:
		pass

	# Fallback: first hotel's address
	hotel = frappe.db.get_value("Hotel", {}, ["hotel_name", "address", "city"], as_dict=True)
	if hotel:
		parts = [str(hotel.hotel_name or "")]
		if hotel.get("address"):
			parts.append(str(hotel.address))
		if hotel.get("city"):
			parts.append(str(hotel.city))
		return ", ".join(p for p in parts if p)

	return ""
