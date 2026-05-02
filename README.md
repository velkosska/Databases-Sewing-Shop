# Sewing Shop Management System

A Django-based management system for tailoring/sewing shops that covers customer profiles, order intake, production tracking, delivery handling, and a live operational dashboard.

## Features

- Customer management with reusable measurement profiles.
- Orders and order items linked to a service catalogue.
- Work tickets with assignment, priority, and status.
- Production stages per ticket.
- Materials and usage tracking per order item.
- Delivery records and completion tracking.
- Admin UI powered by Django Unfold.
- Interactive dashboard with:
  - live status cards,
  - table filtering/search/sorting,
  - overdue and due-soon indicators,
  - priority/status color coding,
  - row count and load-more behavior.

## Tech Stack

- Python 3.13 (local `venv`)
- Django 6
- MySQL
- django-unfold

## Project Structure

- `shop/models.py` - domain models and relationships.
- `shop/admin.py` - admin configuration and list/filter/search setup.
- `shop/views.py` - dashboard backend data preparation.
- `templates/shop/dashboard.html` - interactive dashboard UI.
- `shop/management/commands/seed_demo_data.py` - demo data generator.

## Data Model (Current)

Main entities:

- `Customer(first_name, last_name, phone, email, address, notes, created_at)`
- `Measurement(customer OneToOne, chest, waist, hip, shoulder, sleeve_length, inseam, notes, updated_at)`
- `Catalogue(service, base_price)`
- `Order(customer FK, order_date, due_date, status, total_price, notes)`
- `OrderItem(order FK, catalogue FK, garment_type, color, design_notes, quantity, status, final_price)`
- `Employee(first_name, last_name, role, phone, notes)`
- `WorkTicket(order_item OneToOne, assigned_to FK, priority, status, deadline, notes, created_at)`
- `ProductionStage(work_ticket FK, stage_name, started_at, completed_at, comments)`
- `Material(name, color, unit_price, stock_quantity)`
- `OrderItemMaterial(order_item FK, material FK, quantity_used, notes)`
- `Delivery(order OneToOne, delivered_at, delivery_method, recipient_name, delivered, comments)`

## Setup

### 1) Create and activate environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure `.env`

Set:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

### 4) Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5) Create admin user

```bash
python manage.py createsuperuser
```

### 6) Start server

```bash
python manage.py runserver
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Seed Demo Data

The project includes a built-in seeder command:

```bash
python manage.py seed_demo_data --reset --orders 120
```

Arguments:

- `--reset` - deletes existing shop data first, then reseeds.
- `--orders N` - total number of generated orders (minimum 20, default 80).

Seeder characteristics:

- Generates many customers, orders, order items, tickets, stages, and deliveries.
- Mixes all ticket priorities (`urgent`, `high`, `normal`, `low`).
- Spreads due dates across overdue, due-soon, and future windows.
- Produces a balanced status mix for dashboard testing.

## Workflow Overview

1. Create or import customer + measurement profile.
2. Create order with due date and one or more order items.
3. Assign work ticket(s) and priority.
4. Track production stages.
5. Mark completion and register delivery.
6. Monitor operations from dashboard and admin lists/filters.
