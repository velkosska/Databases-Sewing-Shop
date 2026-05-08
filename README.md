# Sewing Shop Management System

A Django-based management system for tailoring/sewing shops that covers customer profiles, order intake, production tracking, delivery handling, and a live operational dashboard.

## Features

- Customer management with reusable measurement profiles.
- Orders and order items linked to a service catalogue.
- Work tickets with assignment, priority, and status.
- Production stages per ticket.
- Materials and usage tracking per order item.
- Delivery records and completion tracking.
- **Payment ledger** (`OrderPayment`): per-order payment history; when rows exist, totals drive `deposit_paid` and `payment_status`. Admin lists balance due and filters (owed / open / paid up).
- **Production audit trail** (`OrderProductionLog`): append-only timeline on each order (status, tickets, stages, delivery, payment flag changes). Optional backfill from existing stage/delivery data.
- Admin UI powered by Django Unfold (sidebar: Customers & Orders, Production, Resources, **Payments**, **Production logs**).
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
- `shop/signals.py` — order/ticket/stage/delivery logging and payment total sync hooks.
- `shop/workflow_sync.py` — aggregate order/line status from work tickets.
- `shop/production_logging.py` / `shop/payment_sync.py` — helpers for production logs and payment rollups.
- `shop/api_views.py` — JSON API for Next.js (dashboard, orders, tickets, deliveries, etc.).
- `shop/management/commands/seed_demo_data.py` — demo data generator.
- `shop/management/commands/backfill_order_production_logs.py` — one-time production-log rows from `ProductionStage` / `Delivery` timestamps.

## Data Model (Current)

Matches `shop/models.py`, migrations through **`0008`**, and `schema.sql` Part 2 (keep `schema.sql` in sync when changing models).

Main entities (**15**):

- `Customer` → `customer`
- `Measurement` → `measurement` (optional profile per customer; `customer_id` soft FK, unique when set)
- `Catalogue` / `CatalogueItem` → `catalogue`, `catalogue_item`
- `Order` → `orders` (includes `deposit_paid`, `payment_status`; amounts align with payment rows when a ledger exists)
- `OrderPayment` → `order_payment` (many payments per order; intake/wizard and admin record rows here)
- `OrderItem` → `order_item` (optional `catalogue` / `catalogue_item`, pricing fields, `assigned_employee` soft FK)
- `OrderItemMaterial` → `order_item_material` (M:N junction with unique `(order_item, material)`)
- `OrderItemMeasurement` → `order_item_measurement` (per-line snapshot; `customer_id` / `order_item_id` soft FK)
- `Employee` → `employee`
- `WorkTicket` → `work_ticket` (OneToOne with `OrderItem`)
- `ProductionStage` → `production_stage`
- `OrderProductionLog` → `order_production_log` (append-only timeline per order)
- `Material` → `material` (includes `low_stock_threshold`, `supplier`)
- `Delivery` → `delivery` (OneToOne with `Order`)

Full field lists and keys: see `report.md` §3 and `schema.sql`.

Design notes:

- `ORDER_ITEM.unit_price` is a snapshot of the price at time of order, intentionally decoupled from the catalogue to preserve order history.
- `DELIVERY.recipient_name` is a delivery snapshot, not always the customer (third-party pickup is supported).
- `ORDER_ITEM_MEASUREMENT` stores per-item measurements that may differ from the customer's default measurements in `MEASUREMENT`.
- `CATALOGUE_ITEM.garment_types` uses JSON for flexibility, acknowledged as a pragmatic 1NF exception.

## Setup

### 1) Create and activate environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2) Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3) Install frontend dependencies (first run)

```bash
cd frontend
npm install
cd ..
```

### 4) MySQL database

The app expects database `sewing_shop` (or your `DB_NAME`) to exist and a user with access (see `schema.sql` for `sewing_user` and grants).

- **Full setup (schema + sample data):** `mysql -u root -p < schema.sql`
- **Or** create an empty DB:
  `mysql -u root -p -e "CREATE DATABASE sewing_shop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"`

### 5) Configure `.env`

Set:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

### 6) Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

After pulling changes that add tables (e.g. `order_production_log`, `order_payment`), run **`migrate`** before opening the matching admin screens.

### Optional: backfill production logs on an existing database

If the **Production logs** list is empty for old data, run once (idempotent):

```bash
python manage.py backfill_order_production_logs
python manage.py backfill_order_production_logs --dry-run   # preview counts only
```

### 7) Create admin user

```bash
python manage.py createsuperuser
```

### 8) Start server

```bash
python manage.py runserver
```

### 9) Start both backend + frontend with one command

Use this after dependencies are installed:

```bash
./start.sh
```

If needed, make it executable once:

```bash
chmod +x start.sh
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
- `--extra-customers N` - synthetic customer pool size used during generation (minimum 20, default 30).

Seeder characteristics:

- Generates many customers, orders, order items, tickets, stages, and deliveries.
- **Suppresses production-log writes during the run** (`pause_order_production_logs`) so seeded data does not flood the audit table; run `backfill_order_production_logs` afterward if you want sample timeline rows.
- Mixes all ticket priorities (`urgent`, `high`, `normal`, `low`).
- Spreads due dates across overdue, due-soon, and future windows.
- Produces a balanced status mix for dashboard testing.

To **fill production logs from seeded stage timestamps** afterward, run `backfill_order_production_logs` (see Setup).

## Workflow Overview

1. Create or import customer + measurement profile.
2. Create order with due date and one or more order items.
3. Assign work ticket(s) and priority.
4. Track production stages; review **Production log** on the order or under **Production logs** in admin.
5. Record **Payments** per order (or rely on migrated legacy deposit rows); monitor **Balance due** on the order changelist.
6. Mark completion and register delivery (**Mark delivered** can post the remaining balance as a payment line when needed).
7. Monitor operations from dashboard and admin lists/filters.
