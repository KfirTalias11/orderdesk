CREATE TABLE products (
 id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 name text NOT NULL, sku text UNIQUE NOT NULL, category text NOT NULL,
 price_cents integer NOT NULL CHECK (price_cents > 0)
);
CREATE TABLE orders (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 customer_name text NOT NULL CHECK (length(trim(customer_name)) BETWEEN 1 AND 120),
 product_id integer NOT NULL REFERENCES products(id),
 quantity integer NOT NULL CHECK (quantity BETWEEN 1 AND 1000),
 total_cents bigint NOT NULL CHECK (total_cents > 0),
 status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','fulfilled')),
 created_at timestamptz NOT NULL DEFAULT now(), fulfilled_at timestamptz
);
CREATE TABLE outbox (
 order_id bigint PRIMARY KEY REFERENCES orders(id),
 dispatched_at timestamptz, completed_at timestamptz
);
CREATE INDEX outbox_pending ON outbox (dispatched_at) WHERE completed_at IS NULL;
CREATE TABLE worker_status (name text PRIMARY KEY, heartbeat_at timestamptz NOT NULL, last_success_at timestamptz);
INSERT INTO products (name,sku,category,price_cents) VALUES
 ('Everyday notebook','NB-001','Stationery',2400),
 ('Stoneware cup','CW-002','Homeware',3200),
 ('Canvas carryall','BG-003','Accessories',4800),
 ('Brass desk tray','DT-004','Workspace',5600),
 ('Weekly planner','PL-005','Stationery',1800),
 ('Linen pencil case','PC-006','Accessories',2200);
INSERT INTO orders (customer_name,product_id,quantity,total_cents,status,created_at,fulfilled_at) VALUES
 ('Juniper Studio',1,4,9600,'fulfilled',now()-interval '2 days',now()-interval '2 days'+interval '1 minute'),
 ('North & Co.',3,2,9600,'fulfilled',now()-interval '1 day',now()-interval '1 day'+interval '1 minute'),
 ('Marlow Workshop',4,1,5600,'fulfilled',now()-interval '4 hours',now()-interval '4 hours'+interval '1 minute');
