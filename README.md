# FashionShop Ecommerce 

A modern Django e-commerce project featuring a product catalogue, cart, orders, a two-step checkout (details → pay), and Stripe payments (with an optional webhook flow). Built against a PostgreSQL schema (fashionshop), using unmanaged Django models that map directly to your existing database tables.

This README explains the project’s goals, features, data model, setup, and how to run it locally.


Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Purpose](#purpose)
4. [Goal](#goal)
5. [Rationale](#rationale)
6. [Data Schema (ERD)](#data-schema)
7. [User Experience (UX Design)](#user-experience-ux-design)
8. [Pages](#pages)
9. [Balsamiq-Wireframe](#balsamiq-wireframe)
10. [Technologies Used](#technologies-used)
11. [Project Setup](#project-setup)
12. [Testing](#testing)
13. [Deployment](#deployment)
14. [Acknowledgements](#acknowledgements)

## Overview
FashionShop showcases:

- Product catalogue and shopping bag/cart

- Order creation from cart with accurate totals

- Two-step checkout: collect buyer + shipping details, then pay

- Stripe Checkout (no webhooks required) and a mock payment for local tests

- Persisted Payment rows and automatic order.status = "paid" on success

- Staff tools to update order statuses and view status history

- Stripe webhooks for robust server-side confirmation

## Key Features

- Cart → Order flow using a service layer (orders/services.py)

- Checkout details form (buyer + shipping) saved to the order row

- Stripe Checkout: creates a session; verifies on return

- Mock payment: quick success/fail testing without Stripe

- Status transitions: pending → paid → shipped → delivered (or cancelled)

- Unmanaged models: clean mapping to existing Postgres tables + ENUMs

## Purpose

Provide a clean, production-leaning example of a Django shop that integrates with an existing Postgres database and Stripe, demonstrating a sensible separation of concerns:

models.py → unmanaged DB mappings

services.py → business logic (create orders, record payments, set status)

views.py → endpoints for checkout + payments

forms.py → checkout and staff forms

templates/ → order pages, checkout, emails

## Goal

Deliver a minimal but complete journey from browse → cart → checkout → pay, with reliable data persistence and a Stripe integration that can be upgraded with webhooks at any time.

## Rationale

Teams often adopt Django after they already have a database. Unmanaged models allow integration without altering the schema.

Stripe Checkout offers a secure, simple payment UX.

A two-step checkout separates address collection (your app) from payment UI (Stripe).

## Data Schema (ERD)

Unmanaged Django models map to an existing Postgres schema named fashionshop.

Tables → Models

- fashionshop.app_user → orders.models.AppUser

- fashionshop.order → orders.models.Order

- fashionshop.order_item → orders.models.OrderItem

- fashionshop.payment → orders.models.Payment (ENUMs: payment_method, payment_status)

- order also includes buyer/shipping columns:
buyer_name, buyer_email, buyer_phone, ship_address1, ship_address2, ship_city, ship_postcode, ship_country, notes.

![ERD Diagram](documentation/diagram/erd_diagram.png)
    
The diagram below shows the main entities and relationships used in this project.

## User Experience (UX Design)

Bag: items with quantities and totals

Order detail: items, totals, buyer & shipping (if present), payment history, pay buttons when unpaid

Checkout details: capture buyer + shipping, Save or Save & continue to payment

Stripe Checkout: hosted payment page, returns to /orders/return/

Staff: update status and view status history

## Pages

- / – Home / Catalogue (via catalog app)

- /catalog/ – Product list + detail

- /bag/ – Shopping bag/cart

- /orders/checkout/ – Create an order from the bag (does not clear bag)

- /orders/<id>/ – Order summary page

- /orders/<id>/checkout/ – Checkout details (buyer + shipping)

- /orders/<id>/pay/ – Mock payment page

- /orders/<id>/pay/stripe/ – Create Stripe Checkout Session

- /orders/return/ – Payment return handler (Stripe + mock)

- /orders/<id>/status/ – Staff: order status update

- /orders/stripe/webhook/ – Stripe webhook endpoint (optional)

## Technologies Used

Backend

- Python 3.11+

- Django 4.2.x

- psycopg2-binary (PostgreSQL)

- dj-database-url, python-dotenv

Payments

- Stripe Python SDK

- (Optional) Stripe CLI for local webhook testing

Frontend

- Django templates

- Bootstrap CSS (plus light custom CSS)

Static

- WhiteNoise (production)

## Project Setup
```bash
git clone https://github.com/your-username/fashionshop.git
cd fashionshop

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

If you don’t have Postgres locally, SQLite is used automatically when DATABASE_URL is not set.
To use Postgres (recommended), put this in .env:
```bash
DATABASE_URL=postgres://USER:PASS@localhost:5432/fashionshop_db?options=-c%20search_path%3Dfashionshop,public
```

search_path ensures the fashionshop schema is searched before public.

Apply migrations for managed apps (unmanaged tables already exist in Postgres):
```bash
python manage.py makemigrations
python manage.py migrate
```
Run the Server:
```bash
python manage.py runserver
```
Open: http://127.0.0.1:8000

### Environment Variables
```bash
# Core
DEBUG=True
SECRET_KEY=dev-not-secure
ALLOWED_HOSTS=127.0.0.1,localhost
TIME_ZONE=Europe/London

# Database (Postgres recommended)
DATABASE_URL=postgres://postgres:admin123@localhost:5432/fashionshop_db?options=-c%20search_path%3Dfashionshop,public

# Stripe (TEST KEYS)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_CURRENCY=gbp

# Optional: Webhooks (only if you use them)
STRIPE_WEBHOOK_SECRET=whsec_xxx
```
## Running Payments
Mock Flow (no Stripe required)

- From an unpaid order page click Pay (mock) and choose success/fail.

- On success:

     - A payment row is created with status=successful

     - The order becomes paid

     - The session bag is cleared

Stripe Checkout (no webhook)

1. Ensure STRIPE_SECRET_KEY is set in .env.

2. From the order page, click Pay with Stripe.

3. Use Stripe test card:
```bash 
Card: 4242 4242 4242 4242
Expiry: any future date
CVC: any 3 digits
ZIP: any

```
4. After payment, the app verifies the Checkout Session on /orders/return/ and:

- Records a payment row

- Marks the order paid

- Clears the bag

- Sends a confirmation email (console backend prints to terminal)

Stripe Webhook (optional)

For extra robustness (user closes browser, etc.):
```bash
# Install Stripe CLI and login
stripe login
stripe listen --forward-to http://127.0.0.1:8000/orders/stripe/webhook/
```
- Copy the printed whsec_... into .env as STRIPE_WEBHOOK_SECRET.

- The endpoint /orders/stripe/webhook/ will receive events like checkout.session.completed.

- Enhance your handler to record payments and mark orders paid server-side.

## Testing 

Manual checklist:

- Cart → order: add items to bag, create order

- Checkout details: save buyer/shipping and confirm they persist on the order

- Mock payment: verify success/fail paths and payment row creation

- Stripe Checkout: pay with test card, confirm payment row & order paid

- Emails: check the console output after payment success

- Staff status: update status, confirm transitions & history

## Deployment

- Use environment variables for all secrets (never commit keys).

- Set DEBUG=False and configure:

    - ALLOWED_HOSTS

    - CSRF_TRUSTED_ORIGINS

Collect static files with WhiteNoise:
```bash
python manage.py collectstatic --noinput
```
- Ensure the production DB has the fashionshop schema and tables.

- Set Stripe keys and, optionally, the webhook secret.

## Acknowledgements

This project was built with the help of many awesome tools, docs, and communities:

- Django – web framework that powers the app.

- Stripe – developer-friendly payments & excellent docs.

- Bootstrap – fast, responsive UI building.

- PostgreSQL & psycopg2 – reliable data layer.

- WhiteNoise – simple static files in production.

- dj-database-url, python-dotenv – clean environment & DB config.

- VS Code + Pylance – great Python IDE experience.

- Git, GitHub – version control & collaboration.

- Stripe CLI – invaluable for local webhook testing.

- pytest / pytest-django (future tests) – testing stack.

Assistive tooling & learning resources

- ChatGPT – iterative code reviews, refactoring ideas, and debugging tips throughout development.

- Stack Overflow – targeted answers to tricky edge cases.

- Official docs – Django, Stripe, Bootstrap, PostgreSQL, and Python docs referenced frequently.

- Linters/formatters – flake8, isort, and black helped keep code tidy (where used).

Huge thanks to the maintainers and communities behind these projects for sharing knowledge and tooling.

