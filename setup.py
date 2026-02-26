from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="hotel_booking",
    version="1.0.0",
    description="Production-grade Hotel Booking System for Frappe/ERPNext",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Frappe",
    author_email="support@frappe.io",
    license="MIT",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "razorpay>=1.4.0",
    ],
)
