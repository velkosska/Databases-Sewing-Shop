-- ============================================================
--  SEWING SHOP MANAGEMENT SYSTEM — FULL SCHEMA
--  Matches Django models (shop/models.py) as of migration 0008
--  WARNING: This script drops and recreates database/user objects.
--  Run only in local/dev/test environments.
--
--  HOW TO RUN IN MYSQL WORKBENCH:
--  1. File > Open SQL Script → select this file
--  2. Click the lightning bolt ⚡ to execute
--  3. Refresh Schemas panel to see sewing_shop appear
-- ============================================================


-- ============================================================
--  PART 1: SCHEMA SETUP
-- ============================================================

DROP DATABASE IF EXISTS sewing_shop;
CREATE DATABASE sewing_shop
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sewing_shop;

DROP USER IF EXISTS 'sewing_user'@'localhost';
CREATE USER 'sewing_user'@'localhost' IDENTIFIED BY 'Sewing@1234';
GRANT ALL PRIVILEGES ON sewing_shop.* TO 'sewing_user'@'localhost';
FLUSH PRIVILEGES;


-- ============================================================
--  PART 2: TABLES
-- ============================================================

-- created_at: Django uses auto_now_add=True; mirrored here with CURRENT_DATE default
CREATE TABLE customer (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL DEFAULT '',
    last_name  VARCHAR(100) NOT NULL DEFAULT '',
    phone      VARCHAR(30)  NULL,
    email      VARCHAR(150) NULL,
    address    VARCHAR(255) NULL,
    notes      LONGTEXT     NULL,
    created_at DATE         NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (id)
);

CREATE TABLE employee (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL DEFAULT '',
    last_name  VARCHAR(100) NOT NULL DEFAULT '',
    role       VARCHAR(100) NULL,
    phone      VARCHAR(30)  NULL,
    notes      LONGTEXT     NULL,
    PRIMARY KEY (id)
);

CREATE TABLE material (
    id                  BIGINT        NOT NULL AUTO_INCREMENT,
    name                VARCHAR(150)  NOT NULL,
    color               VARCHAR(80)   NULL,
    unit_price          DECIMAL(10,2) NOT NULL DEFAULT 0,
    stock_quantity      DECIMAL(10,2) NULL,
    low_stock_threshold DECIMAL(10,2) NULL,
    supplier            VARCHAR(200)  NULL,
    PRIMARY KEY (id)
);

CREATE TABLE catalogue (
    id         BIGINT        NOT NULL AUTO_INCREMENT,
    service    VARCHAR(100)  NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE catalogue_item (
    id                    BIGINT       NOT NULL AUTO_INCREMENT,
    name                  VARCHAR(200) NOT NULL,
    garment_types         JSON         NOT NULL,
    base_price            DECIMAL(8,2) NOT NULL,
    price_hint            VARCHAR(200) NOT NULL DEFAULT '',
    requires_measurements BOOL         NOT NULL DEFAULT TRUE,
    PRIMARY KEY (id)
);

-- status choices: 'pending' | 'in_production' | 'completed' | 'delivered'
-- payment_status choices: 'unpaid' | 'deposit' | 'paid'
CREATE TABLE orders (
    id             BIGINT        NOT NULL AUTO_INCREMENT,
    customer_id    BIGINT        NOT NULL,
    order_date     DATE          NOT NULL DEFAULT (CURRENT_DATE),
    due_date       DATE          NULL,
    status         VARCHAR(50)   NOT NULL DEFAULT 'pending',
    total_price    DECIMAL(10,2) NULL,
    deposit_paid   DECIMAL(10,2) NOT NULL DEFAULT 0,
    payment_status VARCHAR(20)   NOT NULL DEFAULT 'unpaid',
    notes          LONGTEXT      NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customer(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- assigned_employee_id: db_constraint=False in Django → column exists but no FK enforced
-- status choices for order_item are free-form (no Django choices defined)
CREATE TABLE order_item (
    id                   BIGINT        NOT NULL AUTO_INCREMENT,
    order_id             BIGINT        NOT NULL,
    catalogue_id         BIGINT        NULL,
    catalogue_item_id    BIGINT        NULL,
    garment_type         VARCHAR(100)  NULL,
    color_fabric         VARCHAR(200)  NOT NULL DEFAULT '',
    unit_price           DECIMAL(8,2)  NOT NULL DEFAULT 0,
    item_notes           LONGTEXT      NOT NULL DEFAULT '',
    assigned_employee_id BIGINT        NULL,
    price_overridden     BOOL          NOT NULL DEFAULT FALSE,
    color                VARCHAR(80)   NULL,
    design_notes         LONGTEXT      NULL,
    quantity             INT UNSIGNED  NOT NULL DEFAULT 1,
    status               VARCHAR(50)   NOT NULL DEFAULT 'pending',
    final_price          DECIMAL(10,2) NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_order_item_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_order_item_catalogue
        FOREIGN KEY (catalogue_id) REFERENCES catalogue(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_order_item_catalogue_item
        FOREIGN KEY (catalogue_item_id) REFERENCES catalogue_item(id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- customer_id: db_constraint=False in Django → column exists but no FK enforced
CREATE TABLE measurement (
    id            BIGINT        NOT NULL AUTO_INCREMENT,
    customer_id   BIGINT        NULL UNIQUE,
    chest         DECIMAL(6,2)  NULL,
    waist         DECIMAL(6,2)  NULL,
    hip           DECIMAL(6,2)  NULL,
    shoulder      DECIMAL(6,2)  NULL,
    sleeve_length DECIMAL(6,2)  NULL,
    inseam        DECIMAL(6,2)  NULL,
    notes         LONGTEXT      NULL,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                         ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Both FKs use db_constraint=False in Django → columns exist but no FKs enforced
CREATE TABLE order_item_measurement (
    id            BIGINT        NOT NULL AUTO_INCREMENT,
    customer_id   BIGINT        NOT NULL,
    order_item_id BIGINT        NOT NULL,
    bust          DECIMAL(6,2)  NULL,
    waist         DECIMAL(6,2)  NULL,
    hips          DECIMAL(6,2)  NULL,
    shoulder      DECIMAL(6,2)  NULL,
    sleeve        DECIMAL(6,2)  NULL,
    length        DECIMAL(6,2)  NULL,
    inseam        DECIMAL(6,2)  NULL,
    neck          DECIMAL(6,2)  NULL,
    notes         LONGTEXT      NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- order_item_id is UNIQUE (OneToOneField in Django)
-- status choices: 'pending' | 'in_progress' | 'done'
-- priority choices: 'low' | 'normal' | 'high' | 'urgent'
CREATE TABLE work_ticket (
    id             BIGINT      NOT NULL AUTO_INCREMENT,
    order_item_id  BIGINT      NOT NULL UNIQUE,
    assigned_to_id BIGINT      NULL,
    status         VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority       VARCHAR(20) NOT NULL DEFAULT 'normal',
    deadline       DATE        NULL,
    notes          LONGTEXT    NULL,
    created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_work_ticket_order_item
        FOREIGN KEY (order_item_id) REFERENCES order_item(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_work_ticket_employee
        FOREIGN KEY (assigned_to_id) REFERENCES employee(id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- stage_name choices: 'order_received' | 'design_confirmed' | 'cutting' |
--                     'sewing' | 'finishing' | 'quality_check' |
--                     'ready_for_delivery' | 'delivered'
CREATE TABLE production_stage (
    id             BIGINT       NOT NULL AUTO_INCREMENT,
    work_ticket_id BIGINT       NOT NULL,
    stage_name     VARCHAR(100) NOT NULL,
    started_at     DATETIME(6)  NULL,
    completed_at   DATETIME(6)  NULL,
    comments       LONGTEXT     NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_production_stage_ticket
        FOREIGN KEY (work_ticket_id) REFERENCES work_ticket(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- delivery_method choices: 'pickup' | 'courier' | 'in_store'
CREATE TABLE delivery (
    id              BIGINT       NOT NULL AUTO_INCREMENT,
    order_id        BIGINT       NOT NULL UNIQUE,
    delivered_at    DATETIME     NULL,
    delivery_method VARCHAR(50)  NULL,
    recipient_name  VARCHAR(100) NULL,
    delivered       BOOL         NOT NULL DEFAULT FALSE,
    comments        LONGTEXT     NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_delivery_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE order_item_material (
    id            BIGINT        NOT NULL AUTO_INCREMENT,
    order_item_id BIGINT        NOT NULL,
    material_id   BIGINT        NOT NULL,
    quantity_used DECIMAL(10,2) NULL,
    notes         LONGTEXT      NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_oim UNIQUE (order_item_id, material_id),
    CONSTRAINT fk_oim_order_item
        FOREIGN KEY (order_item_id) REFERENCES order_item(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oim_material
        FOREIGN KEY (material_id) REFERENCES material(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- kinds: order_status | payment_status | order_item_status | order_item_assigned |
--       ticket_status | ticket_assigned | stage_started | stage_completed | delivery
CREATE TABLE order_production_log (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    order_id   BIGINT       NOT NULL,
    created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    kind       VARCHAR(32)  NOT NULL,
    payload    JSON         NOT NULL,
    PRIMARY KEY (id),
    KEY idx_opl_order_created (order_id, created_at),
    CONSTRAINT fk_order_production_log_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- methods: cash | card | transfer | other | admin_mark_delivered
CREATE TABLE order_payment (
    id           BIGINT        NOT NULL AUTO_INCREMENT,
    order_id     BIGINT        NOT NULL,
    amount       DECIMAL(10,2) NOT NULL,
    method       VARCHAR(32)   NOT NULL DEFAULT 'cash',
    recorded_at  DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    notes        VARCHAR(255)  NOT NULL DEFAULT '',
    PRIMARY KEY (id),
    KEY idx_order_payment_ord_rec (order_id, recorded_at),
    CONSTRAINT fk_order_payment_order
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


-- ============================================================
--  PART 3: SAMPLE DATA
-- ============================================================

INSERT INTO customer (first_name, last_name, phone, email, address, notes) VALUES
('Maria',  'Garcia',    '612345678', 'maria@email.com',  'Calle Mayor 12, Madrid',    'Prefers silk fabrics'),
('Carlos', 'Lopez',     '623456789', 'carlos@email.com', 'Av. Libertad 5, Barcelona', 'Urgent orders weekdays only'),
('Ana',    'Martinez',  '634567890', 'ana@email.com',    'Gran Via 88, Madrid',       NULL),
('Pedro',  'Fernandez', '645678901', 'pedro@email.com',  'Calle Sol 3, Valencia',     'Allergic to wool');

INSERT INTO measurement (customer_id, chest, waist, hip, shoulder, sleeve_length, inseam, notes) VALUES
(1, 88.0, 68.0, 94.0, 38.0, 60.0, NULL,  'Tall frame'),
(2, 98.0, 82.0, 100.0, 44.0, 64.0, 82.0, NULL),
(3, 84.0, 64.0, 90.0, 36.5, 58.0, NULL,  NULL),
(4, 92.0, 78.0, 96.0, 42.0, 63.0, 80.0, 'No elastic waistband; no wool');

INSERT INTO catalogue (service, base_price) VALUES
('Wedding Dress Tailoring', 350.00),
('Formal Suit Tailoring',   280.00),
('Summer Dress Sewing',      90.00),
('Trousers Tailoring',      110.00),
('Bridesmaid Dress Sewing', 180.00);

INSERT INTO employee (first_name, last_name, phone, role, notes) VALUES
('Lucia',  'Ramos',  '611000001', 'Tailor',   NULL),
('Jorge',  'Diaz',   '611000002', 'Cutter',   NULL),
('Sofia',  'Torres', '611000003', 'Finisher', NULL),
('Miguel', 'Ruiz',   '611000004', 'Tailor',   'Currently inactive');

INSERT INTO material (name, color, unit_price, stock_quantity) VALUES
('Premium Denim', 'Blue',  12.50, 45.50),
('White Cotton',  'White',  6.00, 80.00),
('Red Silk',      'Red',   22.00, 20.00),
('Black Thread',  'Black',  0.80, 100.00),
('White Zipper',  'White',  1.20, 60.00),
('Floral Lining', 'Mixed',  8.00, 30.00);

INSERT INTO orders (customer_id, order_date, due_date, status, total_price, deposit_paid, payment_status, notes) VALUES
(1, '2025-04-01', '2025-04-15', 'in_production', 380.00, 100.00, 'deposit', 'Wedding dress, high priority'),
(2, '2025-04-03', '2025-04-20', 'pending',        560.00,   0.00, 'unpaid',  'Two formal suits'),
(3, '2025-04-05', '2025-04-25', 'pending',          95.00,  0.00, 'unpaid',  NULL),
(4, '2025-04-06', '2025-04-18', 'delivered',       115.00, 115.00, 'paid',   'Casual trousers, no wool');

INSERT INTO order_item (order_id, catalogue_id, garment_type, quantity, color, design_notes, status, final_price) VALUES
(1, 1, 'Wedding Dress',   1, 'White',  'Long train, lace sleeves',    'in_progress',        380.00),
(2, 2, 'Formal Suit',     2, 'Navy',   'Classic cut, two buttons',    'pending',            560.00),
(3, 3, 'Summer Dress',    1, 'Floral', 'Short, A-line, pockets',      'pending',             95.00),
(4, 4, 'Casual Trousers', 2, 'Khaki',  'Straight leg, no wool blend', 'ready_for_delivery', 115.00);

INSERT INTO order_item_material (order_item_id, material_id, quantity_used) VALUES
(1, 3, 5.0),
(1, 6, 3.0),
(1, 4, 2.0),
(2, 1, 4.0),
(2, 4, 1.5),
(3, 2, 2.5),
(3, 5, 1.0),
(4, 1, 3.0),
(4, 4, 1.0);

INSERT INTO work_ticket (order_item_id, assigned_to_id, priority, status, deadline, notes) VALUES
(1, 1, 'urgent', 'in_progress', '2025-04-14', 'Prioritize over other tickets'),
(2, 1, 'high',   'pending',     '2025-04-19', NULL),
(3, 2, 'normal', 'pending',     '2025-04-24', NULL),
(4, 1, 'normal', 'done',        '2025-04-17', 'Completed ahead of schedule');

INSERT INTO delivery (order_id, delivered_at, delivery_method, recipient_name, delivered, comments) VALUES
(4, '2025-04-11 11:00:00', 'pickup', 'Pedro Fernandez', TRUE, 'Customer collected in store. Satisfied.');

-- Ledger rows aligning sample deposit_paid on orders (1: partial deposit; 4: paid in full)
INSERT INTO order_payment (order_id, amount, method, notes) VALUES
(1, 100.00, 'cash', 'Sample seed deposit'),
(4, 115.00, 'card', 'Sample paid in full');


-- ============================================================
--  PART 4: VERIFY ROW COUNTS
-- ============================================================

SELECT 'customer'             AS tbl, COUNT(*) AS total FROM sewing_shop.customer
UNION ALL SELECT 'measurement',        COUNT(*) FROM sewing_shop.measurement
UNION ALL SELECT 'catalogue',          COUNT(*) FROM sewing_shop.catalogue
UNION ALL SELECT 'catalogue_item',     COUNT(*) FROM sewing_shop.catalogue_item
UNION ALL SELECT 'orders',             COUNT(*) FROM sewing_shop.orders
UNION ALL SELECT 'order_item',         COUNT(*) FROM sewing_shop.order_item
UNION ALL SELECT 'material',           COUNT(*) FROM sewing_shop.material
UNION ALL SELECT 'order_item_material',COUNT(*) FROM sewing_shop.order_item_material
UNION ALL SELECT 'employee',           COUNT(*) FROM sewing_shop.employee
UNION ALL SELECT 'work_ticket',        COUNT(*) FROM sewing_shop.work_ticket
UNION ALL SELECT 'production_stage',   COUNT(*) FROM sewing_shop.production_stage
UNION ALL SELECT 'delivery',           COUNT(*) FROM sewing_shop.delivery
UNION ALL SELECT 'order_production_log', COUNT(*) FROM sewing_shop.order_production_log
UNION ALL SELECT 'order_payment',       COUNT(*) FROM sewing_shop.order_payment;


-- ============================================================
--  PART 5: WORKFLOW 1 — Customer Order Creation
--  Register a new customer, save measurements, create an
--  order, add a garment item, and confirm the result.
-- ============================================================

INSERT INTO sewing_shop.customer (first_name, last_name, phone, email, address, notes)
VALUES ('Laura', 'Sanchez', '699000001', 'laura@email.com', 'Calle Luna 7, Seville', 'Prefers pastel colors');

SET @customer_id = LAST_INSERT_ID();

INSERT INTO sewing_shop.measurement (customer_id, chest, waist, hip, shoulder, sleeve_length, inseam, notes)
VALUES (@customer_id, 86.0, 66.0, 92.0, 37.0, 59.0, NULL, 'Petite frame');

INSERT INTO sewing_shop.orders (customer_id, order_date, due_date, status, notes)
VALUES (@customer_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'pending', 'Bridesmaid dress for May wedding');

SET @order_id = LAST_INSERT_ID();

INSERT INTO sewing_shop.order_item
    (order_id, catalogue_id, garment_type, quantity, color, design_notes, status, final_price)
VALUES (@order_id, 5, 'Bridesmaid Dress', 1, 'Dusty Rose', 'A-line, knee length, satin finish', 'pending', 185.00);

SET @item_id = LAST_INSERT_ID();

SELECT
    c.first_name,
    c.last_name,
    o.id            AS order_id,
    o.due_date,
    o.status,
    oi.garment_type,
    oi.color,
    oi.final_price,
    m.chest,
    m.waist,
    m.hip,
    m.shoulder
FROM sewing_shop.orders o
JOIN sewing_shop.customer   c  ON c.id  = o.customer_id
JOIN sewing_shop.order_item oi ON oi.order_id = o.id
JOIN sewing_shop.measurement m ON m.customer_id = c.id
WHERE o.id = @order_id;


-- ============================================================
--  PART 6: WORKFLOW 2 — Work Ticket and Production Follow-up
--  Create a work ticket and track status updates.
-- ============================================================

INSERT INTO sewing_shop.work_ticket
    (order_item_id, assigned_to_id, priority, status, deadline, notes)
VALUES (@item_id, 1, 'high', 'pending', DATE_ADD(CURDATE(), INTERVAL 12 DAY), 'Satin requires careful ironing');

SET @ticket_id = LAST_INSERT_ID();

UPDATE sewing_shop.work_ticket
SET status = 'in_progress'
WHERE id = @ticket_id;

UPDATE sewing_shop.work_ticket
SET status = 'done'
WHERE id = @ticket_id;

SELECT
    wt.id            AS ticket_id,
    wt.status        AS ticket_status,
    wt.priority,
    CONCAT(e.first_name, ' ', e.last_name) AS assigned_to,
    wt.deadline,
    wt.notes
FROM sewing_shop.work_ticket wt
JOIN sewing_shop.employee e ON e.id = wt.assigned_to_id
WHERE wt.id = @ticket_id;


-- ============================================================
--  PART 7: WORKFLOW 3 — Order Completion and Delivery
--  Mark order completed, record delivery, confirm summary.
-- ============================================================

UPDATE sewing_shop.order_item
SET status = 'ready_for_delivery'
WHERE id = @item_id;

UPDATE sewing_shop.orders
SET status = 'completed'
WHERE id = @order_id;

INSERT INTO sewing_shop.delivery
    (order_id, delivered_at, delivery_method, recipient_name, delivered, comments)
VALUES (@order_id, NOW(), 'pickup', 'Laura Sanchez', TRUE, 'Customer picked up dress. Very satisfied.');

SELECT
    CONCAT(c.first_name, ' ', c.last_name) AS customer,
    o.id              AS order_id,
    o.status          AS order_status,
    oi.garment_type,
    wt.status         AS ticket_status,
    wt.priority,
    d.delivered_at,
    d.delivery_method,
    d.recipient_name,
    d.comments
FROM sewing_shop.orders o
JOIN sewing_shop.customer    c  ON c.id  = o.customer_id
JOIN sewing_shop.order_item  oi ON oi.order_id = o.id
JOIN sewing_shop.work_ticket wt ON wt.order_item_id = oi.id
JOIN sewing_shop.delivery    d  ON d.order_id = o.id
WHERE o.id = @order_id;


-- ============================================================
--  PART 8: MONITORING QUERIES
-- ============================================================

-- Pending orders
SELECT o.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       o.due_date, o.notes
FROM sewing_shop.orders o
JOIN sewing_shop.customer c ON c.id = o.customer_id
WHERE o.status = 'pending'
ORDER BY o.due_date;

-- Orders in production
SELECT o.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       o.due_date, oi.garment_type, wt.priority
FROM sewing_shop.orders o
JOIN sewing_shop.customer    c  ON c.id  = o.customer_id
JOIN sewing_shop.order_item  oi ON oi.order_id = o.id
JOIN sewing_shop.work_ticket wt ON wt.order_item_id = oi.id
WHERE o.status = 'in_production'
ORDER BY FIELD(wt.priority, 'urgent', 'high', 'normal', 'low'), o.due_date;

-- Overdue orders
SELECT o.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       o.due_date, DATEDIFF(CURDATE(), o.due_date) AS days_overdue
FROM sewing_shop.orders o
JOIN sewing_shop.customer c ON c.id = o.customer_id
WHERE o.status NOT IN ('completed', 'delivered', 'cancelled')
  AND o.due_date < CURDATE()
ORDER BY days_overdue DESC;

-- Completed orders with delivery info
SELECT o.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       o.due_date, d.delivered_at, d.delivery_method, d.recipient_name
FROM sewing_shop.orders o
JOIN sewing_shop.customer c ON c.id = o.customer_id
LEFT JOIN sewing_shop.delivery d ON d.order_id = o.id
WHERE o.status IN ('completed', 'delivered')
ORDER BY d.delivered_at DESC;

-- Work ticket status summary
SELECT status, COUNT(*) AS total
FROM sewing_shop.work_ticket
GROUP BY status;

-- Customer order history with catalogue service info
SELECT o.id AS order_id, o.order_date, o.due_date, o.status,
       oi.garment_type, oi.color, cat.service, oi.final_price,
       wt.status AS ticket_status
FROM sewing_shop.orders o
JOIN sewing_shop.customer    c   ON c.id   = o.customer_id
JOIN sewing_shop.order_item  oi  ON oi.order_id = o.id
JOIN sewing_shop.catalogue   cat ON cat.id = oi.catalogue_id
JOIN sewing_shop.work_ticket wt  ON wt.order_item_id = oi.id
WHERE c.first_name = 'Maria' AND c.last_name = 'Garcia'
ORDER BY o.order_date DESC;

-- Open balances (mirror Django Order.balance_due: total_price - deposit_paid, floored at 0)
SELECT o.id AS order_id,
       o.status,
       o.total_price,
       o.deposit_paid,
       GREATEST(COALESCE(o.total_price, 0) - COALESCE(o.deposit_paid, 0), 0) AS balance_due
FROM sewing_shop.orders o
WHERE o.total_price IS NOT NULL
  AND o.status <> 'delivered'
  AND GREATEST(COALESCE(o.total_price, 0) - COALESCE(o.deposit_paid, 0), 0) > 0;
