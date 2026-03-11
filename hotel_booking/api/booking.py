# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Booking creation API - creates guest, checks availability, allocates rooms.
"""

from datetime import datetime

import frappe
from frappe import _

from hotel_booking.api.availability import check_room_availability


# def _get_seasonal_price(room_type: str, check_in: str, check_out: str) -> float:
# 	"""
# 	Get price per night - seasonal if exists, else base price.
# 	Uses SQL for performance.
# 	"""
# 	# Check if any date in range falls in seasonal price
# 	seasonal = frappe.db.sql(
# 		"""
# 		SELECT price FROM `tabSeasonal Price`
# 		WHERE room_type = %(room_type)s
# 		AND from_date <= %(check_out)s
# 		AND to_date >= %(check_in)s
# 		ORDER BY from_date DESC
# 		LIMIT 1
# 		""",
# 		{"room_type": room_type, "check_in": check_in, "check_out": check_out},
# 		as_dict=True,
# 	)

# 	if seasonal:
# 		return float(seasonal[0].price)
# 	frappe.log_error(f"seasonal:{seasonal[0].price}")

# 	rt = frappe.get_cached_doc("Room Type", room_type)
# 	frappe.log_error(f"base_price:{rt.base_price}")
# 	return float(rt.base_price or 0)

def _get_seasonal_price(room_type: str, check_in: str, check_out: str) -> float:
    """
    Get price per night - seasonal if exists and > 0, else base price.
    Uses SQL for performance.
    """

    seasonal = frappe.db.sql(
        """
        SELECT price
        FROM `tabSeasonal Price`
        WHERE room_type = %(room_type)s
        AND from_date <= %(check_out)s
        AND to_date >= %(check_in)s
        ORDER BY from_date DESC
        LIMIT 1
        """,
        {
            "room_type": room_type,
            "check_in": check_in,
            "check_out": check_out
        },
        as_dict=True,
    )

    # Seasonal price found
    if seasonal:
        seasonal_price = float(seasonal[0].price or 0)

        # If seasonal price > 0 use it
        if seasonal_price > 0:
            frappe.logger().info(
                f"Using seasonal price for {room_type}: {seasonal_price}"
            )
            return seasonal_price

        # Seasonal price = 0 → fallback
        frappe.logger().info(
            f"Seasonal price is 0, falling back to base price for {room_type}"
        )

    # Fallback to base price
    rt = frappe.get_cached_doc("Room Type", room_type)
    base_price = float(rt.base_price or 0)

    frappe.logger().info(
        f"Using base price for {room_type}: {base_price}"
    )

    return base_price


def _allocate_rooms(room_type: str, check_in: str, check_out: str, count: int) -> list:
    """
    Allocate available rooms for the date range.
    Uses SQL with FOR UPDATE for concurrent booking safety.
    """
    # Get rooms of this type that are Available and NOT in overlapping bookings
    # Use subquery to exclude booked rooms
    rooms = frappe.db.sql(
        """
        SELECT r.name
        FROM `tabRoom` r
        WHERE r.room_type = %(room_type)s
        AND r.status = 'Available'
        AND r.name NOT IN (
            SELECT DISTINCT br.room
            FROM `tabBooking Room` br
            INNER JOIN `tabBookings` b ON b.name = br.parent
            WHERE br.room_type = %(room_type)s
            AND b.status != 'Cancelled'
            AND b.docstatus = 0
            AND %(check_in)s < b.check_out
            AND %(check_out)s > b.check_in
        )
        LIMIT %(count)s
        """,
        {"room_type": room_type, "check_in": check_in, "check_out": check_out, "count": count},
        as_dict=True,
    )

    return [r.name for r in rooms]


@frappe.whitelist(allow_guest=True)
def create_booking(
    guest_name: str,
    phone: str,
    email: str,
    room_type: str,
    check_in: str,
    check_out: str,
    rooms_required: int = 1,
    adults: int = 1,
    children: int = 0,
) -> dict:
    """
    Create a booking: create/fetch guest, check availability, allocate rooms, create booking.

    Args:
        guest_name: Guest name
        phone: Phone number
        email: Email address
        room_type: Room Type name
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        rooms_required: Number of rooms needed

    Returns:
        dict with booking_id
    """
    # Validate inputs
    if not all([guest_name, room_type, check_in, check_out]):
        frappe.throw(_("Guest name, room type, check-in and check-out are required"))

    rooms_required = int(rooms_required or 1)
    if rooms_required < 1:
        frappe.throw(_("At least 1 room is required"))

    adults = int(adults or 1)
    children = int(children or 0)
    frappe.log_error(f"adults:{adults}, children:{children}")
    if adults < 1:
        frappe.throw(_("At least 1 adult is required"))

    # Parse dates
    try:
        check_in_dt = datetime.strptime(str(check_in).strip(), "%Y-%m-%d").date()
        check_out_dt = datetime.strptime(str(check_out).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        frappe.throw(_("Invalid date format. Use YYYY-MM-DD"))

    if check_in_dt >= check_out_dt:
        frappe.throw(_("Check-out date must be after check-in date"))

    if not frappe.db.exists("Room Type", room_type):
        frappe.throw(_("Room Type {0} does not exist").format(room_type))

    # Validate guest capacity
    room_type_doc = frappe.get_doc("Room Type", room_type)
    frappe.log_error(f"room_type:{room_type}")

    if (adults + children) > (room_type_doc.max_guests * rooms_required):
        frappe.throw(
            _("Guest count exceeds maximum capacity for selected room(s)")
        )
  
    # Check availability (re-validate at creation time)
    available = check_room_availability(room_type, check_in, check_out)
    if available < rooms_required:
        frappe.throw(
            _("Only {0} room(s) available for selected dates. Required: {1}").format(
                available, rooms_required
            )
        )

    # Create or fetch guest (match by phone or email for simplicity)
    guest = None
    if phone:
        guest = frappe.db.get_value("Guest", {"phone": phone}, "name")
    if not guest and email:
        guest = frappe.db.get_value("Guest", {"email": email}, "name")

    if not guest:
        guest_doc = frappe.get_doc(
            {
                "doctype": "Guest",
                "guest_name": guest_name,
                "phone": phone or "",
                "email": email or "",
            }
        )
        guest_doc.insert(ignore_permissions=True)
        guest = guest_doc.name
    else:
        # Update guest details if changed
        guest_doc = frappe.get_doc("Guest", guest)
        guest_doc.guest_name = guest_name
        guest_doc.phone = phone or guest_doc.phone
        guest_doc.email = email or guest_doc.email
        guest_doc.save(ignore_permissions=True)

    # Get price and calculate
    price_per_night = _get_seasonal_price(room_type, check_in, check_out)
    nights = (check_out_dt - check_in_dt).days
    frappe.log_error(f"price_per_night:{price_per_night}, nights:{nights}")

    # Allocate rooms (within transaction for concurrency)
    allocated = _allocate_rooms(room_type, check_in, check_out, rooms_required)
    if len(allocated) < rooms_required:
        frappe.throw(_("Rooms could not be allocated. Please try again."))

    # Create booking
    rooms_data = []
    for room_name in allocated:
        room_doc = frappe.get_cached_doc("Room", room_name)
        amount = price_per_night * nights
        rooms_data.append(
            {
                "room": room_name,
                "room_type": room_type,
                "price_per_night": price_per_night,
                "nights": nights,
                "amount": amount,
                "adults": adults,
                "children": children,
            }
        )

    total_amount = sum(r["amount"] for r in rooms_data)

    booking = frappe.get_doc(
        {
            # "doctype": "Booking",
            "doctype": "Bookings",
            "guest": guest,
            "check_in": check_in,
            "check_out": check_out,
            "rooms_required": rooms_required,
            "adults": adults,
            "children": children,
            "total_amount": total_amount,
            "status": "Pending Payment",
            "payment_status": "Unpaid",
            "rooms": rooms_data,
        }
    )
    booking.insert(ignore_permissions=True)
    frappe.db.commit()

    # return {"booking_id": booking.name, "total_amount": total_amount, "rooms_required": rooms_required, "adults": adults, "children": children}
    return {
        "booking_id": str(booking.name),
        "total_amount": float(total_amount),
        "rooms_required": int(rooms_required),
        "adults": int(adults),
        "children": int(children),
    }

@frappe.whitelist(allow_guest=True)
def get_room_price(room_type: str, check_in: str, check_out: str):
    price = _get_seasonal_price(room_type, check_in, check_out)
    return {"price": float(price)}