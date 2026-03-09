import frappe

@frappe.whitelist(allow_guest=True)
def create_contact(first_name, last_name, email, phone, subject, message):

    contact = frappe.new_doc("Contact")
    contact.first_name = first_name
    contact.last_name = last_name

    contact.append("email_ids", {
        "email_id": email,
        "is_primary": 1
    })

    if phone:
        contact.append("phone_nos", {
            "phone": phone,
            "is_primary_phone": 1
        })

    contact.custom_notes = f"{subject}\n\n{message}"

    contact.insert(ignore_permissions=True)

    return {"message": "Contact created"}