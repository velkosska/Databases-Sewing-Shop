# Sewing Shop Management System
## Database Project Report

---

## 0. Project Summary

| Item | Value |
|---|---|
| Project | Sewing Shop Management System |
| Backend framework | Django 6.0.4 (`config/`, `shop/`) |
| Admin UI | Django Unfold (`unfold` in `INSTALLED_APPS`, `UNFOLD` config in `config/settings.py`) |
| Relational database | MySQL 8 (database `sewing_shop`) |
| ORM | Django ORM (`shop/models.py`, migrations `shop/migrations/0001` … `0008_order_payment`) |
| Frontend (optional complement) | Next.js wizard under `frontend/` (does not replace Django) |
| ERD | `docs/erd.png` (also reproduced below) |
| Standalone SQL | `schema.sql` (DDL + sample data + 3 workflows + monitoring queries) |
| Demo data | `schema.sql` Part 3 + `python manage.py seed_demo_data` (+ optional `backfill_order_production_logs` after large seeds) |

---

## 1. Problem Description

### The Problem

Small and medium-sized sewing and tailoring shops typically manage their daily operations manually — through notebooks, spreadsheets, or verbal communication. This approach makes it difficult to track the status of orders, assign work to employees, monitor production progress, and ensure timely delivery. As the volume of work increases, these limitations lead to missed deadlines, lost orders, and poor customer service.

### Context

The system is designed for a sewing shop that accepts custom clothing orders from customers. Each order may involve one or more garments, each requiring specific measurements, materials, design details, and production effort. The shop employs tailors and cutters who work on different garments, and management needs visibility over what is in progress, what is overdue, and what has been delivered.

### Scope

The system covers the full lifecycle of a customer order — from initial registration through production tracking and final delivery. It includes:

- Customer and measurement management
- Order and garment item management
- Service catalogue
- Material inventory tracking
- Work ticket assignment and production stage tracking
- Delivery recording
- **Payment history and balance owed** (`OrderPayment`, admin balances)
- **Production change timeline** (`OrderProductionLog`)
- Operational monitoring and reporting

The system does not cover accounting, payroll, or supplier management beyond material reference prices.

### Intended Users

- **Shop staff / receptionists** — register customers, create orders, assign work tickets
- **Tailors and cutters** — view and update their assigned work tickets and production stages
- **Shop manager / admin** — monitor all orders, production status, deadlines, and deliveries

---

## 2. Requirements Description

### Main Features

1. Register customers with contact details and notes
2. Store a reusable measurement profile per customer
3. Create orders linked to a customer with due dates and status tracking
4. Add one or more garment items to an order, each linked to a service from the catalogue
5. Track materials used per garment item
6. Generate work tickets for each garment item with priority and assigned employee
7. Track production progress through multiple defined stages
8. Record delivery details when an order is completed
9. Record **payments** per order and see **balances owed** vs **paid in full**
10. Review **production / payment-change history** per order from the timeline
11. Monitor operations through a dashboard and admin interface

### Business Rules

| # | Rule | Enforced by |
|---|---|---|
| BR1 | Every order must belong to exactly one customer | `orders.customer_id NOT NULL` + FK |
| BR2 | An order may contain one or more garment items | `order_item.order_id NOT NULL` + FK |
| BR3 | Each garment item may optionally reference a service in the catalogue or a catalogue item | `order_item.catalogue_id NULL`, `order_item.catalogue_item_id NULL` |
| BR4 | Each garment item generates exactly one work ticket | `work_ticket.order_item_id UNIQUE` (OneToOneField) |
| BR5 | A work ticket must always have a status and priority | `work_ticket.status NOT NULL DEFAULT 'pending'`, `priority NOT NULL DEFAULT 'normal'` |
| BR6 | A work ticket may be assigned to one employee or left unassigned | `work_ticket.assigned_to_id NULL`, `ON DELETE SET NULL` |
| BR7 | A work ticket tracks multiple production stages as the garment progresses | `production_stage.work_ticket_id NOT NULL` + FK |
| BR8 | A garment item may use zero or more materials | `order_item_material` junction with `UNIQUE(order_item_id, material_id)` |
| BR9 | Each customer has at most one reusable measurement profile | `measurement.customer_id UNIQUE` (OneToOneField) |
| BR10 | A completed order may have at most one delivery record | `delivery.order_id UNIQUE` (OneToOneField) |
| BR11 | Delivered orders must store the delivery date and method | `delivery.delivered_at`, `delivery.delivery_method` |
| BR12 | Due dates must be stored to enable overdue tracking | `orders.due_date`, `work_ticket.deadline` |
| BR13 | Each order stores zero or more payment lines; when rows exist their sum drives `deposit_paid` / `payment_status` | `order_payment.order_id CASCADE`, `payment_sync.sync_order_payment_totals` |
| BR14 | Production and payment-change events append to an order-scoped timeline for admin review | `order_production_log.order_id CASCADE`, `shop/signals.py` + `production_logging.py` |

### Modules

#### Payment & balance tracking
- Record individual **payments** per order (`OrderPayment`: amount, method, timestamp, notes).
- When at least one payment row exists, **`deposit_paid`** and **`payment_status`** on the order are **derived** from the sum of amounts vs `total_price` (`shop/payment_sync.py`, signals on `OrderPayment`).
- Wizard / JSON order creation creates a payment row for non-zero intake deposits; legacy `deposit_paid` values were imported into one **“Imported from legacy cumulative deposit.”** row in migration `0008`.
- Admin: global **Payments** changelist (`OrderPaymentAdmin`), **Payment history** inline on orders, **Balance due** column and filters (**Has balance owed**, **Outstanding (not delivered)**, **Paid up**).
- **Mark delivered** action posts any **remaining balance** as a payment line (`admin_mark_delivered`) when totals warrant it.

#### Production audit timeline
- **`OrderProductionLog`** stores append-only events (order/line/ticket/stage/delivery/payment-flag changes).
- Implemented in `shop/signals.py`, summarized for display via `production_logging.format_order_production_log_summary`; read-only inline + **Production logs** menu + `OrderProductionLogAdmin`.
- Optional **`manage.py backfill_order_production_logs`** builds historical-looking rows from `ProductionStage.started_at` / `completed_at` and delivery snapshots (marked `source: backfill` in JSON).

#### Customer Management
- Register customers (first name, last name, phone, email, address, notes)
- Store and update measurement profiles (chest, waist, hip, shoulder, sleeve length, inseam)
- View full order history by customer
- Implemented in: `CustomerAdmin`, `MeasurementAdmin`, view `customer_detail` (`shop/views.py`), API `customer_search`, `customer_snapshot`, `customer_measurements`

#### Catalogue Management
- Maintain a catalogue of services (e.g. Wedding Dress Tailoring, Trouser Tailoring) with `base_price`
- Maintain a richer `catalogue_item` registry that holds `garment_types` (JSON list), price hint, and a `requires_measurements` flag
- Implemented in: `CatalogueAdmin`, `CatalogueItemAdmin`

#### Order Management
- Create orders linked to a customer
- Set order date, due date, and status (`pending`, `in_production`, `completed`, `delivered`)
- Track total price, **cumulative paid** (`deposit_paid`), and payment status (`unpaid`, `deposit`, `paid`) — when **payment rows** exist they are authoritative for the paid total
- Add multiple garment items per order
- **Payment history** inline (`OrderPaymentInline`) and **production log** inline (`OrderProductionLogInline`, read-only)
- Implemented in: `OrderAdmin` (with `OrderItemInline`, `OrderPaymentInline`, `DeliveryInline`, `OrderProductionLogInline`, changelist **Balance due** / filters, actions `mark_in_production`, `mark_completed`, `mark_delivered`) and the `create_order` wizard view + **`create_order` JSON endpoint** (`shop/api_views.py`)

#### Order Item Management
- Each item links to a catalogue service (`catalogue`) and/or catalogue item (`catalogue_item`)
- Records garment type, color, fabric, design notes, quantity, unit price, and final price
- Tracks materials used (via `order_item_material` junction)
- Optional per-item measurement snapshot (`order_item_measurement`)
- Implemented in: `OrderItemAdmin` with `OrderItemMeasurementInline` and `OrderItemMaterialInline`

#### Work Ticket Management
- One ticket generated per order item (OneToOne)
- Ticket tracks: assigned employee, priority (`low`, `normal`, `high`, `urgent`), status (`pending`, `in_progress`, `done`), and deadline
- Status can be updated as work progresses (admin actions, drag-and-drop API in `update_ticket_status`)
- Implemented in: `WorkTicketAdmin`, view `production_board`

#### Production Stage Tracking
- Each ticket may have multiple production stages
- Stage names: `order_received`, `design_confirmed`, `cutting`, `sewing`, `finishing`, `quality_check`, `ready_for_delivery`, `delivered`
- Each stage records start time, completion time, and comments
- Implemented in: `ProductionStageAdmin`, `ProductionStageInline`

#### Delivery Management
- One delivery record per completed order (OneToOne)
- Records delivery method (`pickup`, `courier`, `in_store`), recipient name, delivery date, and comments
- Implemented in: `DeliveryAdmin` and `DeliveryInline`

#### Monitoring and Reporting
- Pending orders list
- Orders currently in production
- Overdue orders (past due date, not completed)
- Completed and delivered orders
- Work ticket status summary
- Customer order history
- Implemented in: `dashboard` view (`templates/shop/dashboard.html`), `production_board` view, admin list filters, plus `schema.sql` Part 8 monitoring queries

### Workflows

#### Workflow 1: Customer Order Creation
1. Staff registers a new customer (or selects an existing one)
2. Staff records or updates the customer's measurement profile
3. Staff creates a new order with a due date
4. Staff adds one or more garment items to the order, each linked to a catalogue service
5. Order is saved with status `pending`

UI: `/orders/new/` wizard (Next.js front-end + Django backend) → `create_order` view in `shop/views.py`.
SQL equivalent: `schema.sql` Part 5.

#### Workflow 2: Ticket Creation and Production Follow-up
1. A work ticket is created for each garment item in the order (auto-created by the wizard)
2. Ticket is assigned to an employee with a priority and deadline
3. Employee updates ticket status to `in_progress` when work begins
4. Production stages are recorded as the garment moves through the process
5. Ticket is marked `done` when the garment is finished

UI: `/production/` board (`production_board` view) and admin `WorkTicketAdmin` actions.
SQL equivalent: `schema.sql` Part 6.

#### Workflow 3: Order Completion and Delivery
1. Once all items are finished, the order status is updated to `completed`
2. A delivery record is created with the delivery method and recipient
3. The `delivered` flag is set and `delivered_at` is recorded
4. The order status is updated to `delivered`
5. **`mark_delivered`** also sets **`payment_status` to paid** and, when there is **remaining balance**, creates an **`OrderPayment`** line for the remainder so the ledger matches “cleared out”

UI: `OrderAdmin` actions `mark_completed` and `mark_delivered` (the latter also creates/updates the `Delivery` row and may post a balance payment).
SQL equivalent: `schema.sql` Part 7.

---

## 3. Normalized Database Design

### Entities and Attributes

Main entities (**15**):

| Entity | Table | Key Attributes |
|---|---|---|
| Customer | `customer` | id (PK), first_name, last_name, phone, email, address, notes, created_at |
| Measurement | `measurement` | id (PK), customer_id (FK, UNIQUE), chest, waist, hip, shoulder, sleeve_length, inseam, notes, updated_at |
| Catalogue | `catalogue` | id (PK), service, base_price |
| Catalogue Item | `catalogue_item` | id (PK), name, garment_types (JSON), base_price, price_hint, requires_measurements |
| Order | `orders` | id (PK), customer_id (FK), order_date, due_date, status, total_price, deposit_paid, payment_status, notes |
| **Order Payment** | `order_payment` | id (PK), order_id (FK), amount, method, recorded_at, notes |
| Order Item | `order_item` | id (PK), order_id (FK), catalogue_id (FK), catalogue_item_id (FK), garment_type, color, color_fabric, unit_price, item_notes, assigned_employee_id (soft FK), price_overridden, design_notes, quantity, status, final_price |
| Material | `material` | id (PK), name, color, unit_price, stock_quantity, low_stock_threshold, supplier |
| Order Item Material | `order_item_material` | id (PK), order_item_id (FK), material_id (FK), quantity_used, notes — UNIQUE(order_item_id, material_id) |
| Order Item Measurement | `order_item_measurement` | id (PK), customer_id (soft FK), order_item_id (soft FK), bust, waist, hips, shoulder, sleeve, length, inseam, neck, notes, created_at |
| Employee | `employee` | id (PK), first_name, last_name, role, phone, notes |
| Work Ticket | `work_ticket` | id (PK), order_item_id (FK, UNIQUE), assigned_to_id (FK), status, priority, deadline, notes, created_at |
| Production Stage | `production_stage` | id (PK), work_ticket_id (FK), stage_name, started_at, completed_at, comments |
| **Order Production Log** | `order_production_log` | id (PK), order_id (FK), created_at, kind, payload (JSON) |
| Delivery | `delivery` | id (PK), order_id (FK, UNIQUE), delivered_at, delivery_method, recipient_name, delivered, comments |

> "Soft FK" means the column exists and is logically a foreign key, but Django creates it with `db_constraint=False`. The relationship is enforced in application code rather than the database. This is documented inline in `schema.sql`.

### Relationships

| Relationship | Type | Description |
|---|---|---|
| Customer → Orders | 1 to many | One customer can place many orders |
| Customer → Measurement | 1 to 0..1 | Each customer has at most one reusable measurement profile |
| Customer → Order Item Measurement | 1 to 0..many | Per-order snapshot of a customer's measurements (soft FK) |
| Orders → Order Item | 1 to many | One order contains one or more garment items |
| Orders → Delivery | 1 to 0..1 | One order has at most one delivery record |
| Orders → Order Payment | 1 to 0..many | Zero or more payment lines; when present they define paid total |
| Orders → Order Production Log | 1 to 0..many | Append-only timeline rows for admin |
| Catalogue → Order Item | 1 to 0..many | A catalogue service can be optionally referenced by order items |
| Catalogue Item → Order Item | 1 to 0..many | A catalogue item can be optionally referenced by order items |
| Order Item → Order Item Measurement | 1 to 0..many | Per-item measurement snapshots (soft FK) |
| Order Item → Work Ticket | 1 to 0..1 | Each garment item has at most one work ticket (in practice exactly one, created with the item) |
| Order Item ↔ Material | many to many | Via `order_item_material` junction table |
| Work Ticket → Production Stage | 1 to many | One ticket can have multiple production stages |
| Employee → Work Ticket | 1 to 0..many | One employee can be assigned to many tickets (or none) |
| Employee → Order Item | 1 to 0..many | Optional pre-assignment at intake (soft FK `assigned_employee_id`) |

### Normalization

The database is normalized to **Third Normal Form (3NF)**:

- **1NF**: All tables have a single-valued primary key and no repeating groups. The `garment_types` field on `catalogue_item` uses a JSON list of garment-type tags; this is a controlled tag set that is read-only at runtime, not a relational join target, so storing it in JSON keeps the model simple without violating 1NF semantics for the rest of the schema. **`order_production_log.payload`** similarly stores structured audit details (not a join target).
- **2NF**: All non-key attributes depend on the full primary key. The `order_item_material` junction table correctly separates material usage from order items, and `order_item_measurement` separates per-item measurement snapshots from the customer's reusable profile.
- **3NF**: No transitive dependencies. Customer name is not stored on orders (joined via FK). Employee name is not stored on tickets (joined via FK). Reusable measurement data is stored in `measurement`, separate from the per-order snapshot in `order_item_measurement`. Catalogue prices are joined via FK rather than copied — when a price is overridden on an item, the override is captured explicitly via `unit_price` + `price_overridden` instead of mutating the catalogue.

### Referential Actions

| FK | ON DELETE | Reason |
|---|---|---|
| `orders.customer_id` | RESTRICT | Don't lose orders if a customer record is removed |
| `order_item.order_id` | CASCADE | Items belong to their parent order |
| `order_item.catalogue_id` | RESTRICT | Don't break historical line items |
| `order_item.catalogue_item_id` | SET NULL | Catalogue items can be retired without nuking line items |
| `order_item_material.order_item_id` | CASCADE | Material usage rows live with their parent item |
| `order_item_material.material_id` | RESTRICT | Don't allow deleting a material that has historic usage |
| `work_ticket.order_item_id` | CASCADE | Ticket lives with its item |
| `work_ticket.assigned_to_id` | SET NULL | Tickets survive employee deletion (left unassigned) |
| `production_stage.work_ticket_id` | CASCADE | Stages live with their ticket |
| `delivery.order_id` | CASCADE | Delivery row lives with its order |
| `order_payment.order_id` | CASCADE | Payment lines live with their order |
| `order_production_log.order_id` | CASCADE | Timeline rows live with their order |

---

## 4. Entity-Relationship Diagram (ERD)

The full ERD is committed at [`docs/erd.png`](docs/erd.png) and reproduced below.

![ERD](docs/erd.png)

The ERD illustrates the **core transactional schema** used since the original design. **`order_payment`** (payment ledger) and **`order_production_log`** (append-only timeline) are additional child tables on **`orders`** and may not appear on every diagram revision; they are documented in §3 and in `schema.sql` Part 2.

The narrative below applies to **`docs/erd.png`** as drawn: Soft-FK columns (`order_item.assigned_employee_id`, `order_item_measurement.customer_id`, `order_item_measurement.order_item_id`, `measurement.customer_id`) appear as plain attributes because they are not enforced as database-level FKs — they are relational only at the application level.

---

## 5. Working Django Application

The Django application lives under:

- `config/` — project settings, URLs, WSGI/ASGI entry points.
- `shop/` — the `Shop` app:
  - `models.py` — every entity from section 3, with explicit `db_table` overrides so the ORM table names match `schema.sql` exactly.
  - `migrations/0001_initial.py` … `0008_order_payment.py` — database migrations (**`0007`** = production log; **`0008`** = payments + legacy deposit import).
  - `admin.py` — Unfold admin (including **`OrderPaymentAdmin`**, **`OrderProductionLogAdmin`**, order balance column/filters, payment + timeline inlines).
  - `signals.py` — timeline + payment sync; `workflow_sync.py` — ticket-driven order aggregates.
  - `production_logging.py`, `payment_sync.py` — log formatting and paid total rollups.
  - `api_views.py` — primary JSON `/api/*` endpoints for the dashboard and Next.js.
  - `views.py` — `dashboard`, `create_order`, `production_board`, `customer_detail`, and lighter JSON helpers.
  - `forms.py` — admin forms (`OrderAdminForm`, `OrderItemInlineForm`).
  - `management/commands/seed_demo_data.py` — demo-data generator (wraps **`pause_order_production_logs`** for bulk inserts).
  - `management/commands/backfill_order_production_logs.py` — optional backfill command.
- `templates/shop/` — `dashboard.html`, `order_wizard.html`, `production_board.html`, `customer_detail.html`.
- `frontend/` — optional Next.js wizard that calls the Django API; the Django backend is fully functional without it.

### Django Unfold Integration

`unfold`, `unfold.contrib.filters`, and `unfold.contrib.forms` are first in `INSTALLED_APPS` (`config/settings.py`), every admin class extends `unfold.admin.ModelAdmin`/`TabularInline`/`StackedInline`, and the `UNFOLD` dict configures branding, sidebar groups (**Customers & Orders** including **Payments**; **Production** including **Production logs**), search, and history.

---

## 6. Source Code, Dependencies and Setup

### Dependencies

`requirements.txt`:

```
asgiref==3.11.1
Django==6.0.4
django-unfold==0.89.0
mysqlclient==2.2.8
pillow==12.2.0
python-dotenv==1.2.2
sqlparse==0.5.5
django-cors-headers==4.9.0
```

### Quickstart

```bash
# 1) Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2) Database (option A — apply the standalone schema)
mysql -u root -p < schema.sql

# 2) Database (option B — let Django create the schema)
python manage.py migrate

# 3) Admin user
python manage.py createsuperuser

# 4) Demo data (optional)
python manage.py seed_demo_data --reset --orders 120

# Optional: production-log snapshots from seeded stages/deliveries
python manage.py backfill_order_production_logs

# 5) Run the server
python manage.py runserver
```

### Known first-run commands

Use this exact sequence on a fresh clone:

```bash
# 1) backend deps
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2) frontend deps (required once before ./start.sh)
cd frontend
npm install
cd ..

# 3) database + migrations
python manage.py migrate

# 4) admin account
python manage.py createsuperuser

# 5) optional demo data
python manage.py seed_demo_data --reset --orders 120 --extra-customers 45

# Optional
python manage.py backfill_order_production_logs

# 6) run both backend + frontend
./start.sh
```

Open:

- Dashboard: `http://127.0.0.1:8000/`
- Admin (Django Unfold): `http://127.0.0.1:8000/admin/`
- Production board: `http://127.0.0.1:8000/production/`

### Environment

`config/settings.py` reads MySQL connection settings from `.env` via `python-dotenv`:

```
DB_NAME=sewing_shop
DB_USER=sewing_user
DB_PASSWORD=Sewing@1234
DB_HOST=localhost
DB_PORT=3306
```

`schema.sql` Part 1 also creates the `sewing_user` MySQL account that matches these defaults, so the standalone SQL script and the Django app target the same database.

---

## 7. Workflow Documentation

Every workflow listed in section 2 is implemented twice for traceability — once in Python (Django views/admin) and once in `schema.sql` so the workflow can also be exercised from the MySQL Workbench.

| Workflow | Django entry point | SQL equivalent |
|---|---|---|
| 1 — Customer Order Creation | `create_order` view (`/orders/new/`) and `OrderAdmin` `add_view` | `schema.sql` Part 5 |
| 2 — Ticket Creation & Production Follow-up | `production_board` view (`/production/`), `WorkTicketAdmin` actions, `update_ticket_status` API | `schema.sql` Part 6 |
| 3 — Order Completion & Delivery | `OrderAdmin` `mark_completed`, `mark_delivered` (**`Delivery`** + optional **`OrderPayment`** for remaining balance); payment flags via ledger sync | `schema.sql` Part 7 |

`schema.sql` Part 8 contains six monitoring queries (pending orders, in-production orders, overdue orders, completed orders with delivery info, ticket-status summary, customer order history) that mirror the dashboard view.

---

## 8. Demo Data

Two interchangeable demo-data sources are provided:

- **`schema.sql` Part 3** — minimal, deterministic seed (4 customers, 5 catalogue services, 4 employees, 6 materials, 4 orders, 4 work tickets, 1 delivery, **2 `order_payment` rows** tying sample deposits to the ledger). **`order_production_log`** starts empty in SQL (use Django + `backfill_order_production_logs` if desired).
- **`shop/management/commands/seed_demo_data.py`** — randomized, larger seed for the dashboard. Run with `python manage.py seed_demo_data --reset --orders 120 --extra-customers 45`. Spreads priorities, due dates, and statuses to exercise dashboard filters and backfills measurements for all existing customers.

`schema.sql` Part 4 prints row counts immediately after seeding so the script doubles as a self-check.

---

## 9. Consistency Check (Documentation ↔ ERD ↔ Schema ↔ Code)

| Concern | Documentation (`report.md`, `README.md`) | ERD (`docs/erd.png`) | Schema (`schema.sql`) | Code (`shop/models.py` + migrations) |
|---|---|---|---|---|
| Entities | **15** entities in §3 (see also **Payment** / **Production log**) | Diagram may omit the two ledger/timeline tables; see note in §4 | **15** `CREATE TABLE` in Part 2 (incl. `order_payment`, `order_production_log`) | **15** `models.Model` classes (`0001`…`0008`) |
| Primary keys | All `id` BIGINT | All `id (PK)` | `BIGINT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id)` | `BigAutoField` (default) |
| `customer.full_name` | Documented as derived | Not drawn (correct — it's a property) | Not stored | `@property full_name` derived from `first_name + last_name` |
| Measurement uniqueness | "1 to 0..1" | UNIQUE drawn on `customer_id` | `customer_id BIGINT NULL UNIQUE` | `OneToOneField(Customer, db_constraint=False)` |
| Work ticket uniqueness | "1 to 0..1" | UNIQUE on `order_item_id` | `order_item_id BIGINT NOT NULL UNIQUE` | `OneToOneField(OrderItem)` |
| Delivery uniqueness | "1 to 0..1" | UNIQUE on `order_id` | `order_id BIGINT NOT NULL UNIQUE` | `OneToOneField(Order)` |
| Order status choices | `pending`, `in_production`, `completed`, `delivered` | n/a | Comment header on `orders` | `Order.Status` TextChoices |
| Payment status choices | `unpaid`, `deposit`, `paid` | n/a | Comment header on `orders` | `Order.PaymentStatus` TextChoices |
| Ticket status choices | `pending`, `in_progress`, `done` | n/a | Comment header on `work_ticket` | `WorkTicket.Status` TextChoices |
| Priority choices | `low`, `normal`, `high`, `urgent` | n/a | Comment header on `work_ticket` | `WorkTicket.Priority` TextChoices |
| Stage choices | 8 stages listed in §2 | n/a | Comment header on `production_stage` | `ProductionStage.StageName` TextChoices |
| Payment method choices (`order_payment.method`) | `cash`, `card`, `transfer`, `other`, `admin_mark_delivered` | n/a | Comment on `order_payment` | `OrderPayment.Method` TextChoices |
| Production log kinds (`order_production_log.kind`) | order/payment/item/ticket/stage/delivery buckets (see migrations) | n/a | `VARCHAR` + JSON `payload` | `OrderProductionLog.Kind` TextChoices |
| Many-to-many | `OrderItem ↔ Material` via `order_item_material` | Junction box drawn | `UNIQUE(order_item_id, material_id)` | `ManyToManyField(through="OrderItemMaterial")` |
| Soft FKs (no DB constraint) | Annotated as "soft FK" in §3 | Drawn as plain attributes | Comments above each table | `db_constraint=False` in models |
| Workflows | 3 workflows in §7 | n/a | Parts 5/6/7 | Views + admin actions |
| Required tech | Django, MySQL, Django Unfold | n/a | MySQL DDL | `INSTALLED_APPS` includes `unfold`, every admin class extends Unfold base classes |

### How the PDF deliverables map

| PDF requirement | Where it lives |
|---|---|
| 1. Problem Description | `report.md` §1 |
| 2. Requirements Description | `report.md` §2 (features, business rules, modules, workflows) |
| 3. Normalized Database Design | `report.md` §3 |
| 4. ERD | `docs/erd.png` (embedded in §4) |
| 5. Working Django Application | `shop/`, `config/`, `templates/` (described in §5) |
| 6. Source Code and Dependencies | `requirements.txt`, `README.md`, `report.md` §6 |
| 7. Workflow Documentation | `report.md` §7 + `schema.sql` Parts 5–7 |
| 8. Optional Demo Data | `schema.sql` Part 3 + `seed_demo_data` command (§8) |

### How the PDF "Required Technologies" map

| PDF requirement | Implementation |
|---|---|
| Django as the main backend framework | `Django==6.0.4` (`requirements.txt`), `config/` project, `shop/` app |
| A relational database such as PostgreSQL, MySQL | MySQL 8 (`config/settings.py` `ENGINE = django.db.backends.mysql`) |
| Django ORM for model design and database interaction | `shop/models.py` + **eight** migration files under `shop/migrations/` (through **`0008`**) |
| Django Unfold integrated into the project | `unfold` first in `INSTALLED_APPS`, `UNFOLD` config block, every admin class extends `unfold.admin.*` |
| Additional tools or frameworks only as complements | Optional Next.js wizard in `frontend/` (uses Django API; backend works without it) |
