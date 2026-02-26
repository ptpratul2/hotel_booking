// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
// Hotel Booking Calendar - Color coded by status

frappe.views.calendar["Booking"] = {
	field_map: {
		start: "check_in",
		end: "check_out",
		id: "name",
		title: "name",
		allDay: 1,
	},
	get_events_method: "hotel_booking.api.calendar.get_booking_events",
	get_css_class: function(d) {
		// Confirmed = Green, Pending = Orange, Cancelled = Red
		if (d.status === "Confirmed") return "success";
		if (d.status === "Pending Payment" || d.status === "Checked In" || d.status === "Draft") return "warning";
		if (d.status === "Cancelled") return "danger";
		if (d.status === "Completed") return "info";
		return "default";
	},
};
