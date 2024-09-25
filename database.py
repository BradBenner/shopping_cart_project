from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object
db = SQLAlchemy()


# Define the Product model, representing products in the database
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Integer, default=50)
    image = db.Column(db.String(100), nullable=False)


# Define the Order model, representing customer orders
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.Integer)
    status = db.Column(db.String(50))
    # Relationship to OrderProduct model (one order can have multiple products)
    order_products = db.relationship('OrderProduct', backref='order', cascade="all, delete-orphan")


# Define the OrderProduct model, representing products within an order
class OrderProduct(db.Model):
    __tablename__ = 'order_products'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Relationship to Product model (each OrderProduct is linked to a Product)
    product = db.relationship('Product', backref='order_products')


# Function to initialize the database
def init_db(app):
    # Bind the SQLAlchemy object to the  Flask app
    db.init_app(app)
    # Create all database tables within the application context
    with app.app_context():
        db.create_all()  # Create tables if they don't exist

        # Check if there are any products in the database
        if not Product.query.first():
            # Create a list of sample products
            sample_products = [
                Product(name='Shovel', price=10.00, qty=50, image='shovel.png'),
                Product(name='Rake', price=15.00, qty=50, image='rake.png'),
                Product(name='Hose', price=20.00, qty=50, image='hose.png'),
            ]
            # Save the sample products to the database in bulk
            db.session.bulk_save_objects(sample_products)
            # Commit the session to persist the products
            db.session.commit()
