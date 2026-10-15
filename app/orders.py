from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.db import connection
from app.logging import event


class OrderInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    customer_name: str = Field(min_length=1, max_length=120)
    product_id: int = Field(gt=0, strict=True)
    quantity: int = Field(ge=1, le=1000, strict=True)

    @field_validator('customer_name')
    @classmethod
    def normalize_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Customer name is required')
        return value


SELECT_ORDERS = '''SELECT o.*, p.name AS product_name, p.sku FROM orders o
                   JOIN products p ON p.id=o.product_id'''


def list_orders():
    with connection() as db:
        return db.execute(SELECT_ORDERS + ' ORDER BY o.id DESC LIMIT 200').fetchall()


def create_order(data):
    with connection() as db:
        product = db.execute('SELECT * FROM products WHERE id=%s', (data.product_id,)).fetchone()
        if not product:
            raise HTTPException(404, 'Product not found')
        order = db.execute('''INSERT INTO orders(customer_name,product_id,quantity,total_cents)
                              VALUES (%s,%s,%s,%s) RETURNING *''',
                           (data.customer_name, data.product_id, data.quantity,
                            product['price_cents'] * data.quantity)).fetchone()
        db.execute('INSERT INTO outbox(order_id) VALUES (%s)', (order['id'],))
        order.update(product_name=product['name'], sku=product['sku'])
    event('order.created', order_id=order['id'])
    return order
