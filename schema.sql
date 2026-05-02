-- ============================================================
--  SEWING SHOP MANAGEMENT SYSTEM — REVISED SCHEMA
--  Adapted from sewing_shop_erd_revised.xlsx
--
--  Key changes from original:
--    • customer.full_name  → first_name + last_name
--    • measurement now belongs to Customer (reusable profile),
--      not to order_item — removed per-item measurement
--    • New: catalogue table (services + base prices)
--    • order_item now references catalogue_id + has status
--      and final_price
--    • CustomerOrder (was orders) gains total_price
--    • employee.full_name  → first_name + last_name
--    • work_ticket can have MULTIPLE tickets per order_item
--      (removed UNIQUE on order_item_id)
--    • delivery: delivery_date+method → delivered_at +
--      delivery_method + recipient_name
--    • order_item_material now has a surrogate PK (id)
--    • production_stage table REMOVED (not in revised ERD)
--    • material gains unit_price; drops type/unit columns
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

-- BR2: every order belongs to exactly one customer
CREATE TABLE customer (
    id          INT           NOT NULL AUTO_INCREMENT,
    first_name  VARCHAR(100)  NOT NULL,
    last_name   VARCHAR(100)  NOT NULL,
    phone       VARCHAR(20),
    email       VARCHAR(150),
    address     VARCHAR(255),
    notes       TEXT,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- BR1: one reusable measurement profile per customer (0..1)
CREATE TABLE measurement (
    id              INT           NOT NULL AUTO_INCREMENT,
    customer_id     INT           NOT NULL UNIQUE,   -- one profile per customer
    chest           DECIMAL(5,2),
    waist           DECIMAL(5,2),
    hip             DECIMAL(5,2),
    shoulder        DECIMAL(5,2),
    sleeve_length   DECIMAL(5,2),
    inseam          DECIMAL(5,2),
    notes           TEXT,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                           ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_meas_customer
        FOREIGN KEY (customer_id) REFERENCES customer(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- BR3/BR4: catalogue of services; each order item references one service
-- BR8: base_price is the default; final_price on order_item is the actual charge
CREATE TABLE catalogue (
    id          INT           NOT NULL AUTO_INCREMENT,
    service     VARCHAR(100)  NOT NULL,
    base_price  DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id)
);

-- BR2/BR10: order belongs to one customer; total_price = sum of item final prices
CREATE TABLE customer_order (
    id          INT           NOT NULL AUTO_INCREMENT,
    customer_id INT           NOT NULL,
    order_date  DATE          NOT NULL DEFAULT (CURRENT_DATE),
    due_date    DATE,
    status      VARCHAR(50)   NOT NULL DEFAULT 'Pending',
    total_price DECIMAL(10,2),          -- BR10: total charged for the order
    notes       TEXT,
    PRIMARY KEY (id),
    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id) REFERENCES customer(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- BR3/BR4/BR9: one order → many items; each item ties to a catalogue service
CREATE TABLE order_item (
    id              INT           NOT NULL AUTO_INCREMENT,
    order_id        INT           NOT NULL,
    catalogue_id    INT           NOT NULL,           -- BR4
    garment_type    VARCHAR(100)  NOT NULL,
    quantity        INT           NOT NULL DEFAULT 1,
    color           VARCHAR(50),
    design_notes    TEXT,
    status          VARCHAR(50)   NOT NULL DEFAULT 'Pending',
    final_price     DECIMAL(10,2) NOT NULL,           -- BR9: actual charged price
    PRIMARY KEY (id),
    CONSTRAINT fk_item_order
        FOREIGN KEY (order_id) REFERENCES customer_order(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_item_catalogue
        FOREIGN KEY (catalogue_id) REFERENCES catalogue(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- BR11: unit_price stores cost/reference price per material
CREATE TABLE material (
    id              INT           NOT NULL AUTO_INCREMENT,
    name            VARCHAR(100)  NOT NULL,
    color           VARCHAR(50),
    unit_price      DECIMAL(10,2) NOT NULL,           -- BR11
    stock_quantity  DECIMAL(10,2),
    PRIMARY KEY (id)
);

-- BR5: one item can use multiple materials (junction)
CREATE TABLE order_item_material (
    id              INT           NOT NULL AUTO_INCREMENT,
    order_item_id   INT           NOT NULL,
    material_id     INT           NOT NULL,
    quantity_used   DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_oim UNIQUE (order_item_id, material_id),
    CONSTRAINT fk_oim_item
        FOREIGN KEY (order_item_id) REFERENCES order_item(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oim_material
        FOREIGN KEY (material_id) REFERENCES material(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE employee (
    id          INT           NOT NULL AUTO_INCREMENT,
    first_name  VARCHAR(100)  NOT NULL,
    last_name   VARCHAR(100)  NOT NULL,
    phone       VARCHAR(20),
    role        VARCHAR(100),
    notes       TEXT,
    PRIMARY KEY (id)
);

-- BR6: one order_item can generate MULTIPLE work tickets (no UNIQUE on order_item_id)
-- BR7: ticket must have status; employee is optional (may be unassigned)
CREATE TABLE work_ticket (
    id              INT           NOT NULL AUTO_INCREMENT,
    order_item_id   INT           NOT NULL,
    employee_id     INT,
    priority        VARCHAR(20)   NOT NULL DEFAULT 'Medium',
    status          VARCHAR(50)   NOT NULL DEFAULT 'Open',
    deadline        DATE,
    notes           TEXT,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_ticket_item
        FOREIGN KEY (order_item_id) REFERENCES order_item(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ticket_employee
        FOREIGN KEY (employee_id) REFERENCES employee(id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- BR12: at most one delivery record per order (UNIQUE on order_id)
CREATE TABLE delivery (
    id              INT           NOT NULL AUTO_INCREMENT,
    order_id        INT           NOT NULL UNIQUE,
    delivered_at    DATETIME,
    delivery_method VARCHAR(50),
    recipient_name  VARCHAR(100),
    comments        TEXT,
    PRIMARY KEY (id),
    CONSTRAINT fk_delivery_order
        FOREIGN KEY (order_id) REFERENCES customer_order(id)
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

INSERT INTO customer_order (customer_id, order_date, due_date, status, total_price, notes) VALUES
(1, '2025-04-01', '2025-04-15', 'In Production', 380.00, 'Wedding dress, high priority'),
(2, '2025-04-03', '2025-04-20', 'Pending',        560.00, 'Two formal suits'),
(3, '2025-04-05', '2025-04-25', 'Pending',         95.00, NULL),
(4, '2025-04-06', '2025-04-18', 'Delivered',      115.00, 'Casual trousers, no wool');

INSERT INTO order_item (order_id, catalogue_id, garment_type, quantity, color, design_notes, status, final_price) VALUES
(1, 1, 'Wedding Dress',   1, 'White',  'Long train, lace sleeves',    'In Progress',       380.00),
(2, 2, 'Formal Suit',     2, 'Navy',   'Classic cut, two buttons',    'Pending',           560.00),
(3, 3, 'Summer Dress',    1, 'Floral', 'Short, A-line, pockets',      'Pending',            95.00),
(4, 4, 'Casual Trousers', 2, 'Khaki',  'Straight leg, no wool blend', 'Ready for Delivery',115.00);

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

INSERT INTO work_ticket (order_item_id, employee_id, priority, status, deadline, notes) VALUES
(1, 1, 'Urgent', 'In Progress', '2025-04-14', 'Prioritize over other tickets'),
(2, 1, 'High',   'Open',        '2025-04-19', NULL),
(3, 2, 'Medium', 'Open',        '2025-04-24', NULL),
(4, 1, 'Medium', 'Completed',   '2025-04-17', 'Completed ahead of schedule');

INSERT INTO delivery (order_id, delivered_at, delivery_method, recipient_name, comments) VALUES
(4, '2025-04-11 11:00:00', 'Pickup', 'Pedro Fernandez', 'Customer collected in store. Satisfied.');


-- ============================================================
--  PART 4: VERIFY ROW COUNTS
-- ============================================================

SELECT 'customer'            AS tbl, COUNT(*) AS total FROM sewing_shop.customer
UNION ALL SELECT 'measurement',       COUNT(*) FROM sewing_shop.measurement
UNION ALL SELECT 'catalogue',         COUNT(*) FROM sewing_shop.catalogue
UNION ALL SELECT 'customer_order',    COUNT(*) FROM sewing_shop.customer_order
UNION ALL SELECT 'order_item',        COUNT(*) FROM sewing_shop.order_item
UNION ALL SELECT 'material',          COUNT(*) FROM sewing_shop.material
UNION ALL SELECT 'order_item_material',COUNT(*) FROM sewing_shop.order_item_material
UNION ALL SELECT 'employee',          COUNT(*) FROM sewing_shop.employee
UNION ALL SELECT 'work_ticket',       COUNT(*) FROM sewing_shop.work_ticket
UNION ALL SELECT 'delivery',          COUNT(*) FROM sewing_shop.delivery;


-- ============================================================
--  PART 5: WORKFLOW 1 — Customer Order Creation
--  Register a new customer, save measurements, create an
--  order, add garment items, and confirm the result.
-- ============================================================

INSERT INTO sewing_shop.customer (first_name, last_name, phone, email, address, notes)
VALUES ('Laura', 'Sanchez', '699000001', 'laura@email.com', 'Calle Luna 7, Seville', 'Prefers pastel colors');

SET @customer_id = LAST_INSERT_ID();

-- Reusable measurement profile stored on the customer
INSERT INTO sewing_shop.measurement (customer_id, chest, waist, hip, shoulder, sleeve_length, inseam, notes)
VALUES (@customer_id, 86.0, 66.0, 92.0, 37.0, 59.0, NULL, 'Petite frame');

INSERT INTO sewing_shop.customer_order (customer_id, order_date, due_date, status, notes)
VALUES (@customer_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY), 'Pending', 'Bridesmaid dress for May wedding');

SET @order_id = LAST_INSERT_ID();

INSERT INTO sewing_shop.order_item
    (order_id, catalogue_id, garment_type, quantity, color, design_notes, status, final_price)
VALUES (@order_id, 5, 'Bridesmaid Dress', 1, 'Dusty Rose', 'A-line, knee length, satin finish', 'Pending', 185.00);

SET @item_id = LAST_INSERT_ID();

-- Confirm order + customer measurements
SELECT
    c.first_name,
    c.last_name,
    co.id            AS order_id,
    co.due_date,
    co.status,
    oi.garment_type,
    oi.color,
    oi.final_price,
    m.chest,
    m.waist,
    m.hip,
    m.shoulder
FROM sewing_shop.customer_order co
JOIN sewing_shop.customer   c  ON c.id  = co.customer_id
JOIN sewing_shop.order_item oi ON oi.order_id = co.id
JOIN sewing_shop.measurement m ON m.customer_id = c.id
WHERE co.id = @order_id;


-- ============================================================
--  PART 6: WORKFLOW 2 — Work Ticket and Production Follow-up
--  Create a work ticket and track status updates.
-- ============================================================

INSERT INTO sewing_shop.work_ticket
    (order_item_id, employee_id, priority, status, deadline, notes)
VALUES (@item_id, 1, 'High', 'Assigned', DATE_ADD(CURDATE(), INTERVAL 12 DAY), 'Satin requires careful ironing');

SET @ticket_id = LAST_INSERT_ID();

-- Employee starts working
UPDATE sewing_shop.work_ticket
SET status = 'In Progress'
WHERE id = @ticket_id;

-- Work is finished
UPDATE sewing_shop.work_ticket
SET status = 'Completed'
WHERE id = @ticket_id;

SELECT
    wt.id            AS ticket_id,
    wt.status        AS ticket_status,
    wt.priority,
    CONCAT(e.first_name, ' ', e.last_name) AS assigned_to,
    wt.deadline,
    wt.notes
FROM sewing_shop.work_ticket wt
JOIN sewing_shop.employee e ON e.id = wt.employee_id
WHERE wt.id = @ticket_id;


-- ============================================================
--  PART 7: WORKFLOW 3 — Order Completion and Delivery
--  Mark order completed, record delivery, confirm summary.
-- ============================================================

UPDATE sewing_shop.order_item
SET status = 'Ready for Delivery'
WHERE id = @item_id;

UPDATE sewing_shop.customer_order
SET status = 'Completed'
WHERE id = @order_id;

INSERT INTO sewing_shop.delivery
    (order_id, delivered_at, delivery_method, recipient_name, comments)
VALUES (@order_id, NOW(), 'Pickup', 'Laura Sanchez', 'Customer picked up dress. Very satisfied.');

SELECT
    CONCAT(c.first_name, ' ', c.last_name) AS customer,
    co.id             AS order_id,
    co.status         AS order_status,
    oi.garment_type,
    wt.status         AS ticket_status,
    wt.priority,
    d.delivered_at,
    d.delivery_method,
    d.recipient_name,
    d.comments
FROM sewing_shop.customer_order co
JOIN sewing_shop.customer   c  ON c.id  = co.customer_id
JOIN sewing_shop.order_item oi ON oi.order_id = co.id
JOIN sewing_shop.work_ticket wt ON wt.order_item_id = oi.id
JOIN sewing_shop.delivery   d  ON d.order_id = co.id
WHERE co.id = @order_id;


-- ============================================================
--  PART 8: MONITORING QUERIES
-- ============================================================

-- Pending orders
SELECT co.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       co.due_date, co.notes
FROM sewing_shop.customer_order co
JOIN sewing_shop.customer c ON c.id = co.customer_id
WHERE co.status = 'Pending'
ORDER BY co.due_date;

-- Orders in production
SELECT co.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       co.due_date, oi.garment_type, wt.priority
FROM sewing_shop.customer_order co
JOIN sewing_shop.customer   c  ON c.id  = co.customer_id
JOIN sewing_shop.order_item oi ON oi.order_id = co.id
JOIN sewing_shop.work_ticket wt ON wt.order_item_id = oi.id
WHERE co.status = 'In Production'
ORDER BY FIELD(wt.priority, 'Urgent','High','Medium','Low'), co.due_date;

-- Overdue orders
SELECT co.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       co.due_date, DATEDIFF(CURDATE(), co.due_date) AS days_overdue
FROM sewing_shop.customer_order co
JOIN sewing_shop.customer c ON c.id = co.customer_id
WHERE co.status NOT IN ('Completed', 'Delivered', 'Cancelled')
  AND co.due_date < CURDATE()
ORDER BY days_overdue DESC;

-- Completed orders with delivery info
SELECT co.id, CONCAT(c.first_name, ' ', c.last_name) AS customer,
       co.due_date, d.delivered_at, d.delivery_method, d.recipient_name
FROM sewing_shop.customer_order co
JOIN sewing_shop.customer c ON c.id = co.customer_id
LEFT JOIN sewing_shop.delivery d ON d.order_id = co.id
WHERE co.status IN ('Completed', 'Delivered')
ORDER BY d.delivered_at DESC;

-- Work ticket status summary
SELECT status, COUNT(*) AS total
FROM sewing_shop.work_ticket
GROUP BY status;

-- Customer order history with catalogue service info
SELECT co.id AS order_id, co.order_date, co.due_date, co.status,
       oi.garment_type, oi.color, cat.service, oi.final_price,
       wt.status AS ticket_status
FROM sewing_shop.customer_order co
JOIN sewing_shop.customer   c   ON c.id  = co.customer_id
JOIN sewing_shop.order_item oi  ON oi.order_id = co.id
JOIN sewing_shop.catalogue  cat ON cat.id = oi.catalogue_id
JOIN sewing_shop.work_ticket wt ON wt.order_item_id = oi.id
WHERE c.first_name = 'Maria' AND c.last_name = 'Garcia'
ORDER BY co.order_date DESC;