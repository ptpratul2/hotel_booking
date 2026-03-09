# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Razorpay payment integration for hotel bookings.
"""

import hashlib
import hmac

import frappe
from frappe import _


def _get_razorpay_credentials():
	"""Get Razorpay key and secret from Hotel Booking Settings or site config."""
	try:
		key = frappe.db.get_single_value("Hotel Booking Settings", "api_key")
		secret = frappe.db.get_single_value("Hotel Booking Settings", "api_secret")
	except Exception:
		key = secret = None
	key = key or frappe.conf.get("razorpay_api_key")
	secret = secret or frappe.conf.get("razorpay_api_secret")
	return key, secret


@frappe.whitelist(allow_guest=True)
def create_payment_order(booking_id: str) -> dict:
	"""
	Create Razorpay order for booking payment.
	Returns payment link / order details for frontend.

	Args:
		booking_id: Booking document name

	Returns:
		dict with order_id, amount, currency, key (for frontend)
	"""
	if not booking_id:
		frappe.throw(_("Booking ID is required"))

	if not frappe.db.exists("Bookings", booking_id):
		frappe.throw(_("Booking {0} not found").format(booking_id))

	booking = frappe.get_doc("Bookings", booking_id)

	if booking.status == "Cancelled":
		frappe.throw(_("Cannot pay for cancelled booking"))

	if booking.payment_status == "Paid":
		frappe.throw(_("Booking is already paid"))

	key, secret = _get_razorpay_credentials()
	frappe.log_error(str(booking.total_amount), "Booking Data for Payment Order")
	if not key or not secret:
		frappe.throw(
			_("Razorpay is not configured. Set razorpay_api_key and razorpay_api_secret in site config.")
		)

	try:
		import razorpay
	except ImportError:
		frappe.throw(_("Please install razorpay: pip install razorpay"))

	client = razorpay.Client(auth=(key, secret))

	# Amount in paise (Razorpay uses smallest currency unit)
	amount_paise = int(float(booking.total_amount or 0) * 100)
	if amount_paise < 100:  # Razorpay minimum
		amount_paise = 100

	order_data = {
		"amount": amount_paise,
		"currency": "INR",
		"receipt": booking_id,
		"notes": {
			"booking_id": booking_id,
			"guest": booking.guest,
		},
	}

	order = client.order.create(data=order_data)
	order_id = order.get("id")

	# Save order_id on booking for webhook verification
	booking.db_set("razorpay_order_id", order_id, update_modified=False)
	frappe.db.commit()

	return {
		"order_id": order_id,
		"amount": amount_paise,
		"currency": "INR",
		"key": key,
		"booking_id": booking_id,
	}


def _get_webhook_secret():
	"""Get Razorpay webhook secret (different from API secret)."""
	try:
		secret = frappe.db.get_single_value("Hotel Booking Settings", "webhook_secret")
	except Exception:
		secret = None
	return secret or frappe.conf.get("razorpay_webhook_secret")


@frappe.whitelist(allow_guest=True)
def razorpay_webhook():
	"""
	Handle Razorpay webhook for payment confirmation.
	Verifies signature and updates booking to Paid + Confirmed.
	"""
	payload = frappe.request.get_data(as_text=True)
	signature = frappe.request.headers.get("X-Razorpay-Signature", "")

	secret = _get_webhook_secret()
	if not secret:
		frappe.throw(_("Razorpay webhook secret not configured"))

	# Verify webhook signature (HMAC SHA256)
	expected = hmac.new(
		secret.encode("utf-8"),
		payload.encode("utf-8"),
		hashlib.sha256,
	).hexdigest()

	if not hmac.compare_digest(expected, signature):
		frappe.throw(_("Invalid webhook signature"), frappe.AuthenticationError)

	data = frappe.parse_json(payload)
	event = data.get("event", "")

	if event == "payment.captured":
		payload_data = data.get("payload", {}) or {}
		payment = payload_data.get("payment", {}) or {}
		entity = payment.get("entity", payment) if isinstance(payment, dict) else {}
		if not isinstance(entity, dict):
			entity = {}
		order_id = entity.get("order_id")

		if order_id:
			booking = frappe.db.get_value("Bookings", {"razorpay_order_id": order_id}, "name")
			if booking:
				doc = frappe.get_doc("Bookings", booking)
				doc.payment_status = "Paid"
				doc.status = "Confirmed"
				doc.save(ignore_permissions=True)
				frappe.db.commit()

	return {"status": "ok"}
