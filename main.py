from flask import Flask, render_template, request, session, redirect, url_for, flash
from database import db, init_db, Product, Order, OrderProduct
import random

# Initialize the Flask application
app = Flask(__name__)

# Configure the database URI and session secret keys
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopping_cart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize the database with the Flask app
init_db(app)


@app.route('/')
def home():
    # Initialize the shopping cart in the session if it doesn't exist
    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}  # Ensure cart is a dictionary

    # Fetch all products from the database
    products = Product.query.all()
    # Render the homepage template with the products
    return render_template('index.html', products=products)


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    # Ensure the cart is initialized
    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}

    # Retrieve the product from the database
    product = Product.query.get(product_id)

    # Check if the product exists and is in stock
    if product and int(product.qty) > 0:
        product_id_str = str(product_id)  # Convert product_id to a string
        if product_id_str in session['cart']:
            session['cart'][product_id_str] += 1  # Increase quantity in the cart
        else:
            session['cart'][product_id_str] = 1  # Set quantity to 1 if not already in the cart

        # Decrease the inventory quantity of the product
        product.qty -= 1
        db.session.commit()  # Commit the changes to the database

        session.modified = True  # Mark the session as modified
        flash(f"{product.name} has been added to your cart.", "success")
    else:
        flash("Item is out of stock.", "danger")

    # Redirect back to the home page
    return redirect(url_for('home'))


@app.route('/remove_from_cart/<int:product_id>/', methods=['POST'])
def remove_from_cart(product_id):
    # Check if the cart exists in the session
    if 'cart' in session and isinstance(session['cart'], dict):
        if str(product_id) in session['cart']:  # Ensure product_id is treated as a string
            quantity = session['cart'][str(product_id)]  # Get quantity of the product being removed

            # Retrieve the product from the database
            product = Product.query.get(product_id)

            if product:
                # Restore the product quantity back to inventory
                product.qty += quantity
                db.session.commit()

                # Remove the product from the cart
                del session['cart'][str(product_id)]
                session.modified = True
                flash("Product removed from cart.", "success")
    else:
        flash("Your cart is empty.", "info")

    # Redirect to the cart page
    return redirect(url_for('cart'))


@app.route('/clear_cart')
def clear_cart():
    session['cart'] = {}  # Clear the cart
    session.modified = True
    flash("Cart cleared.", "success")
    return redirect(url_for('cart'))


@app.route('/increase_quantity/<int:product_id>', methods=['POST'])
def increase_quantity(product_id):
    if 'cart' in session and isinstance(session['cart'], dict):
        product_id_str = str(product_id)  # Ensure product_id is treated as a string

        product = Product.query.get(product_id)  # Retrieve the product from the database

        if product and product.qty > 0:  # Check if product exists and is in stock
            if product_id_str in session['cart']:
                session['cart'][product_id_str] += 1  # Increase quantity in the cart
            else:
                session['cart'][product_id_str] = 1  # Set quantity to 1 if not in cart

            session.modified = True

            # Decrease inventory quantity
            product.qty -= 1
            db.session.commit()  # Commit the changes to the database

    # Redirect to the cart page
    return redirect(url_for('cart'))


@app.route('/decrease_quantity/<int:product_id>', methods=['POST'])
def decrease_quantity(product_id):
    if 'cart' in session and isinstance(session['cart'], dict):
        product_id_str = str(product_id)  # Ensure product_id is treated as a string

        if product_id_str in session['cart']:
            current_quantity = session['cart'][product_id_str]  # Get current quantity

            product = Product.query.get(product_id)  # Retrieve the product from the database

            if product:
                if current_quantity > 1:
                    session['cart'][product_id_str] -= 1  # Decrease quantity in the cart
                    product.qty += 1  # Restore inventory quantity
                else:
                    del session['cart'][product_id_str]  # Remove product if quantity is 1
                    product.qty += 1  # Restore inventory quantity

                session.modified = True
                db.session.commit()  # Commit the changes to the database

    # Redirect to the cart page
    return redirect(url_for('cart'))


@app.route('/buy_now', methods=['POST'])
def buy_now():
    cart_items = session.get('cart', {})

    if not cart_items:  # Check if the cart is empty
        flash("Your cart is empty.", "danger")
        return redirect(url_for('cart'))  # Redirect to the cart page

    order_number = random.randint(1000, 9999)  # Generate a random order number
    order = Order(order_number=order_number, status='not shipped')  # Create a new order instance

    total_price = 0  # Initialize total price

    # Add the order to the database and commit to get the order ID
    db.session.add(order)
    db.session.commit()

    # Associate products with the order and store quantities
    for product_id, quantity in cart_items.items():
        product = Product.query.get(product_id)
        if product:
            # Create an OrderProduct instance to store the relationship
            order_product = OrderProduct(order_id=order.id, product_id=product.id, quantity=quantity)
            db.session.add(order_product)  # Add to the session
            total_price += product.price * quantity  # Calculate total price for the order

    db.session.commit()  # Commit changes to the database

    session['cart'] = {}  # Clear the cart after order is placed
    flash(f"Order #{order_number} has been placed successfully.", "success")

    # Pass order details to the confirmation template
    return render_template(
        'order_confirmation.html',
        order_number=order_number,
        cart_items=cart_items,
        total_price=total_price,
        Product=Product
    )


@app.route('/cart')
def cart():
    # Initialize cart if it doesn't exist
    if 'cart' not in session or not isinstance(session['cart'], dict):
        session['cart'] = {}  # Ensure cart is a dictionary

    cart_items = session.get('cart', {})  # Retrieve cart items from session
    products_in_cart = []
    total_price = 0.0

    # Iterate over items in the cart
    for product_id, quantity in cart_items.items():
        product = Product.query.get(product_id)
        if product:
            products_in_cart.append((product, quantity))  # Append product and quantity as a tuple
            total_price += product.price * quantity  # Calculate total price
        else:
            flash(f"Product with ID {product_id} is no longer available.", "warning")

    if not products_in_cart:
        flash("Your cart is empty.", "info")

    # Render the cart template with the products and total price
    return render_template('cart.html', products=products_in_cart, total_price=total_price)


@app.route('/portal', methods=['GET', 'POST'])
def portal():
    order_status = None
    cancel_message = None

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            if action == 'cancel':
                # Cancel the order if requested
                order_number = request.form.get('order_number')
                order = Order.query.filter_by(order_number=order_number).first()

                if order:
                    return cancel_order(order.id)  # Call the cancel_order function

        except Exception as e:
            app.logger.error(f"Error in portal route: {str(e)}")
            flash("An unexpected error occurred. Please try again later.", "danger")

    # Fetch all orders to display in the portal
    orders = Order.query.all()

    # Render the portal template with order details
    return render_template('portal.html', order_status=order_status, cancel_message=cancel_message, orders=orders)


@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    order = Order.query.get(order_id)

    if order:
        # Restore product quantities to inventory
        for order_product in order.order_products:
            product = Product.query.get(order_product.product_id)
            if product:
                product.qty = min(50, product.qty + order_product.quantity)  # For testing purposes

        order.status = 'cancelled'  # Update the order status
        db.session.commit()

        flash(f"Order #{order.order_number} has been cancelled.", "success")

        return redirect(url_for('portal'))


@app.route('/view_order/<int:order_id>', methods=['GET'])
def view_order(order_id):
    order = Order.query.get(order_id)
    if order:
        products_with_quantity = []
        # Retrieve products and their quantities from the association table
        order_details = OrderProduct.query.filter_by(order_id=order.id).all()  # Use the OrderProduct model
        for detail in order_details:
            product = Product.query.get(detail.product_id)
            if product:
                products_with_quantity.append((product, detail.quantity))  # Append product and quantity as a tuple

        total_price = sum(product.price * quantity for product, quantity in products_with_quantity)
        return render_template(
            'view_order.html',
            order=order,
            products_with_quantity=products_with_quantity,
            total_price=total_price)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they don't exist
        session.clear()  # Clear session data on application start

    app.run(debug=True)
