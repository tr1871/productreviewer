from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User object"""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)

    # Define relationship to favorites
    favorite_products = db.relationship("FavoriteProduct")
    favorite_reviews = db.relationship("FavoriteReview")

    def __repr__(self):
        """Display when printing a User object"""

        return "<User: {} email: {}>".format(self.user_id, self.email)


class Product(db.Model):
    """Product object"""

    __tablename__ = "products"

    asin = db.Column(db.Text, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer)
    author = db.Column(db.Text)
    image = db.Column(db.Text, nullable=False)   # link to image
    ratings = db.Column(db.Json)    # dictionary with 1-5 star ratings

    categories = db.relationship("Category",
                                 secondary="ProductCategory",
                                 backref=db.backref("products",
                                                    order_by=asin))


    def __repr__(self):
        """Display when printing a Product object"""

        return "<Product: {} name: {}>".format(self.asin, self.title)


    def calculate_review_distribution():
        """Calculates the distribution of 1,2,3,4,5 star reviews"""

        distribution = {1:0, 2:0, 3:0, 4:0, 5:0}



class Review(db.Model):
    """Review object"""

    __tablename__ = "reviews"

    review_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    reviewer_id = db.Column(db.Text, nullable=False)
    reviewer_name = db.Column(db.Text)
    review = db.Column(db.tsquery, nullable=False)
    asin = db.Column(db.Text, db.ForeignKey('products.asin'))
    helpful_total = db.Column(db.Integer)
    helpful_fraction = db.Column(db.Float)
    rating = db.Column(db.Integer, nullable=False)
    summary = db.Column(db.Text)
    time = db.Column(db.DateTime)

    # Define relationship to product
    product = db.relationship("Product",
                              backref=db.backref("reviews",
                                                 order_by=review_id))

    def __repr__(self):
        """Display when printing a Review object"""

        return "<Review: {} asin: {} summary: {}>".format(self.review_id,
                                                          self.asin,
                                                          self.summary)


class Category(db.Model):
    """Product categories"""

    __tablename__ = "categories"

    cat_name = db.Column(db.Text, primary_key=True)

    def __repr__(self):
        """Display when printing a Category object"""

        return "<Category: {}>".format(self.cat_name)


class ProductCategory(db.Model):
    """Link between products and categories"""

    __tablename__ = "product_categories"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    asin = db.Column(db.Text, db.ForeignKey('products.asin'), nullable=False)
    cat_name = db.Column(db.Text, db.ForeignKey('categories.cat_name'), nullable=False)

    def __repr__(self):
        """Display when printing a Product Category object"""

        return "<ProductCategory: {} asin: {} category: {}>".format(self.id,
                                                                    self.asin,
                                                                    self.cat_name)



class FavoriteProduct(db.Model):
    """User favorite product object"""

    __tablename__ = "favorite_products"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    asin = db.Column(db.Text, db.ForeignKey('products.asin'), nullable=False)

    # Define relationship to product
    product = db.relationship("Product")

    def __repr__(self):
        """Display when printing a FavoriteProduct object"""

        return "<FavoriteProduct: {} user: {} product: {}>".format(self.id,
                                                                   self.user_id,
                                                                   self.asin)


class FavoriteReview(db.Model):
    """User favorite review object"""

    __tablename__ = "favorite_reviews"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.review_id'), nullable=False)

    # Define relationship to review
    review = db.relationship("Review")

    def __repr__(self):
        """Display when printing a FavoriteReview object"""

        return "<FavoriteReview: {} >".format(self.review_id)



##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to Flask app."""

    # Configure to use PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///reviewgenius'
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # Work with database directly if run interactively

    from server import app
    connect_to_db(app)
    print "Connected to DB."