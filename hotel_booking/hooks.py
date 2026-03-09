app_name = "hotel_booking"
app_title = "Hotel Booking"
app_publisher = "Frappe"
app_description = "Production-grade Hotel Booking System for Frappe/ERPNext"
app_email = "support@frappe.io"
app_license = "mit"

# Includes in <head>
# ------------------
app_include_css = "public/css/hotel_booking.css"
app_include_js = [
	"public/js/hotel_booking.js",
	"public/js/booking_calendar.js",
]

# include js in doctype views
doctype_js = {
	"Booking": "public/js/booking.js",
}

# Calendars (enables Calendar view in List)
calendars = ["Booking"]

# DocType Class
# ---------------
# override_doctype_class = {
# 	"Booking": "hotel_booking.overrides.booking.CustomBooking"
# }

# Document Events
# ---------------
doc_events = {
	"Bookings": {
		"on_update": "hotel_booking.utils.email_notification.send_booking_confirmation_email",
	}
}

# Scheduled Tasks
# ---------------
# scheduler_events = {
# 	"daily": [
# 		"hotel_booking.tasks.daily"
# 	]
# }

# Jinja response override
# -----------------------
# jinja = {
# 	"methods": "hotel_booking.utils.jinja_methods",
# }

# Website route rules
# -------------------
website_route_rules = [
	{"from_route": "/book", "to_route": "book"},
	{"from_route": "/book-success", "to_route": "book-success"},
]


fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            ["dt", "=", "Contact"],
            ["fieldname", "=", "custom_notes"]
        ]
    }
]