# Hotel Booking

Production-grade Hotel Booking System for Frappe/ERPNext - scalable, secure, and ready for real hotel usage.

## Features

- **DocTypes**: Hotel, Room Type, Room, Seasonal Price, Guest, Booking, Booking Room
- **Seasonal pricing** with date ranges
- **Guest management** with phone/email
- **Availability API** - SQL-optimized, no Python loops
- **Booking API** - create/fetch guest, check availability, allocate rooms
- **Razorpay payment** - create order, webhook verification
- **Website** `/book` - date picker, room type, check availability, guest form, payment
- **Admin Calendar** - FullCalendar with color coding (Confirmed=Green, Pending=Orange, Cancelled=Red)
- **Email automation** - confirmation email when booking status → Confirmed

## Installation

```bash
cd frappe-bench
pip install -e apps/hotel_booking   # or: bench get-app hotel_booking
bench --site [your-site] install-app hotel_booking
bench build
```

## Configuration

1. **Hotel Booking Settings** (Setup): Add hotel contact for confirmation emails
2. **Razorpay**: Set `api_key`, `api_secret`, `webhook_secret` in Hotel Booking Settings or site_config.json
3. **Webhook URL** for Razorpay: `https://your-domain/api/method/hotel_booking.api.payment.razorpay_webhook`

## Usage

- **Website**: Visit `/book` for public booking
- **Desk**: Hotel Booking module → Booking List → Calendar view
- **API**: `check_room_availability`, `create_booking`, `create_payment_order` (whitelisted, allow_guest)

## License

MIT
