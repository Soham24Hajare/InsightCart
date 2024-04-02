# models.py
from database import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255))  # Add the image column

    def __repr__(self):
        return f"Product(name={self.name}, price={self.price}, image={self.image})"

# class CartItem(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
#     name = db.Column(db.String(100), nullable=False)
#     price = db.Column(db.Float, nullable=False)
#     image = db.Column(db.String(255))  # Add the image column

#     product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))

#     def __repr__(self):
#         return f"CartItem(name={self.name}, price={self.price}, image={self.image})"
class CartItem(db.Model):
    __tablename__ = 'cart_item'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=1)  # Adding the quantity field

    def __repr__(self):
        return f"CartItem(id={self.id}, product_id={self.product_id}, name={self.name}, price={self.price}, image={self.image}, quantity={self.quantity})"