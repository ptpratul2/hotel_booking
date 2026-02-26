# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class Booking(Document):
	"""Booking DocType controller."""

	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		"""Calculate total amount from rooms."""
		total = 0
		if self.rooms:
			for row in self.rooms:
				row.amount = (row.price_per_night or 0) * (row.nights or 0)
				total += row.amount
		self.total_amount = total
