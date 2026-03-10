"""
Email automation - send confirmation email when booking status changes to Confirmed.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


def send_booking_confirmation_email(doc, method=None):
  """
  Called from doc_events on Booking on_update.
  Send email when status changes to Confirmed.
  """

  # Only proceed if status is Confirmed
  if doc.status != "Confirmed":
    return

  # Prevent duplicate email if already confirmed before
  previous = doc.get_doc_before_save()
  if previous and previous.status == "Confirmed":
    return

  # Get guest
  guest = frappe.get_doc("Guest", doc.guest)
  if not guest.email:
    return

  hotel_contact = _get_hotel_contact()
  
  subject = _("Booking Confirmed - {0}").format(doc.name)
 
  # ----------------------------
  # Build Email Template
  # ----------------------------

  message = f"""
<div style="font-family: Arial, Helvetica, sans-serif; background-color:#f4f6f9; padding:30px 0;">
  <div style="max-width:650px; margin:0 auto; background:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:#2c3e50; padding:20px; text-align:center;">
      <h2 style="color:#ffffff; margin:0;">Booking Confirmation</h2>
    </div>

    <!-- Body -->
    <div style="padding:30px; color:#333; font-size:14px; line-height:1.6;">

      <p style="font-size:16px;">Dear <strong>{guest.guest_name}</strong>,</p>

      <p>
        We are pleased to inform you that your booking has been 
        <span style="color:#27ae60; font-weight:bold;">successfully confirmed</span>.
      </p>

      <!-- Booking Details -->
      <div style="background:#f8f9fa; padding:15px 20px; border-radius:6px; margin:20px 0;">
        <p style="margin:5px 0;"><strong>Booking ID:</strong> {doc.name}</p>
        <p style="margin:5px 0;"><strong>Check-in:</strong> {doc.check_in}</p>
        <p style="margin:5px 0;"><strong>Check-out:</strong> {doc.check_out}</p>
      
        
        <p style="margin:5px 0; font-size:16px;">
          <strong>Total Amount:</strong> 
          <span style="color:#2c3e50; font-weight:bold;">
            {frappe.format_value(doc.total_amount, {'fieldtype': 'Currency'})}
          </span>
        </p>
      </div>

      <!-- Room Details -->
      <h4 style="margin-bottom:10px;">Room Details</h4>

      <table width="100%" cellpadding="8" cellspacing="0" style="border-collapse:collapse; border:1px solid #e0e0e0;">
        <thead>
          <tr style="background:#f1f3f5;">
            <th align="left">Room Type</th>
            <th align="left">Room</th>
            <th align="right">Adults</th>
            <th align="right">Children</th>

            <th align="center">Nights</th>
            <th align="right">Price/Night</th>
            <th align="right">Amount</th>
          </tr>
        </thead>
        <tbody>
"""

  for row in doc.rooms or []:
    message += f"""
          <tr style="border-top:1px solid #e0e0e0;">
            <td>{row.room_type}</td>
            <td>{row.room}</td>
            <td align="right">{row.adults}</td>
            <td align="right">{row.children}</td>
            <td align="center">{row.nights}</td>
            <td align="right">{frappe.format_value(row.price_per_night, {'fieldtype': 'Currency'})}</td>
            <td align="right">{frappe.format_value(row.amount, {'fieldtype': 'Currency'})}</td>
           
          </tr>
"""

  message += f"""
        </tbody>
      </table>

      {"<p style='margin-top:20px;'><strong>Hotel Contact:</strong> " + hotel_contact + "</p>" if hotel_contact else ""}

      <p style="margin-top:30px;">
        Thank you for your booking!
      </p>

    </div>

    <!-- Footer -->
   

  </div>
</div>
"""

  # Send Email
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

  # Fallback to first hotel record
  hotel = frappe.db.get_value(
    "Hotel", {}, ["hotel_name", "address", "city"], as_dict=True
  )

  if hotel:
    parts = [str(hotel.hotel_name or "")]
    if hotel.get("address"):
      parts.append(str(hotel.address))
    if hotel.get("city"):
      parts.append(str(hotel.city))
    return ", ".join(p for p in parts if p)

  return ""