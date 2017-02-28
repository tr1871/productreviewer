from model import Product, User, FavoriteReview, FavoriteProduct
from model import connect_to_db, db
import json


def find_products(query, index):
    """Queries database to find products within a search index based on user's search.

       This full-text search in postgres stems, removes stop words, applies weights
       to different fields (title is more important than description), and ranks
       the results by relevancy.

       Currently, the default weights in ts_rank() are used, which is 1 for 'A'
       and 0.4 for 'B'. Future goal: experiment with different weightings and/or
       a cutoff for how relevant a product has to be to return.
    """

    # If the search_query is more than one word,
    # need to format the query for sql with a '&' in between words
    words = query.strip().split(' ')
    search_formatted = ' & '.join(words)

    if index == "All":

        sql = """SELECT *, ts_rank(product_search.product_info,
                to_tsquery('english', :search_terms)) AS relevancy
                FROM (SELECT *,
                    setweight(to_tsvector('english', title), 'A') ||
                    setweight(to_tsvector('english', description), 'B') AS product_info
                FROM products) product_search
                WHERE product_search.product_info @@ to_tsquery('english', :search_terms)
                ORDER BY relevancy DESC;
              """
    else:

        # If the search index is not "All", filter results by products within
        # the provided category
        sql = """SELECT *, ts_rank(product_search.product_info,
                to_tsquery('english', :search_terms)) AS relevancy
                FROM (SELECT *,
                    setweight(to_tsvector('english', title), 'A') ||
                    setweight(to_tsvector('english', description), 'B') AS product_info
                FROM products) product_search
                WHERE product_search.product_info @@ to_tsquery('english', :search_terms) AND
                asin IN
                    (SELECT asin
                        FROM categories
                        INNER JOIN product_categories as pc
                        USING (cat_name)
                        INNER JOIN products
                        USING (asin)
                        WHERE pc.cat_name = :category)
                ORDER BY relevancy DESC;
              """

    cursor = db.session.execute(sql,
                                {'search_terms': search_formatted,
                                 'category': index})

    products = cursor.fetchall()

    # Returns a list of product tuples
    return products


def get_scores(asin):
    """Returns the distribution of scores for a product as a list.

       ex:
        if product "P1234" had one 2-star review and four 5-star reviews,
        get_scores() would return [0, 1, 0, 0, 5]

     """

    scores = Product.query.filter_by(asin=asin).one().scores
    scores = json.loads(scores)
    score_list = (scores["1"], scores["2"], scores["3"], scores["4"], scores["5"])

    return score_list


def get_chart_data(score_list):
    """Construct data dictionary to create histogram with chart.js."""

    data_dict = {
        "labels": ["1", "2", "3", "4", "5"],
        "datasets": [{
            "label": "Customer Ratings",
            "data": score_list,
            "backgroundColor": 'rgba(54, 162, 235, 0.6)',
            "hoverBackgroundColor": 'rgba(54, 162, 235, 1)',
            "borderWidth": 5
        }]
    }

    return data_dict


def find_reviews(asin, query):
    """Queries database to find product reviews based on user's search.

       This full-text search in postgres stems, removes stop words, applies weights
       to different fields (review summary is more important than the review text),
       and ranks the results by relevancy.

       Currently, the default weights in ts_rank() are used, which is 1 for 'A'
       and 0.4 for 'B'. Future goal: experiment with different weightings and/or
       a cutoff for how relevant a review has to be to return.
    """

    # If the search_query is more than one word,
    # need to format the query for sql with a '&' in between words
    words = query.strip().split(' ')
    search_formatted = ' & '.join(words)

    sql = """SELECT *, ts_rank(array[0, 0, 0.8, 1], review_search.review_info,
                to_tsquery('english', :search_terms)) AS relevancy
                FROM (SELECT *,
                    setweight(to_tsvector('english', summary), 'A') ||
                    setweight(to_tsvector('english', review), 'B') AS review_info
                FROM reviews
                WHERE asin=:asin) review_search
                WHERE review_search.review_info @@ to_tsquery('english', :search_terms)
                ORDER BY relevancy DESC;
          """

    cursor = db.session.execute(sql,
                                   {'search_terms': search_formatted,
                                    'asin': asin})

    reviews = cursor.fetchall()

    return reviews


def get_favorite_reviews(user_id):
    """Retrives a user's favorited reviews from db.
       Returns an empty set if user has no favorites.
    """

    favorites = set()

    favorite_reviews = FavoriteReview.query.filter_by(user_id=user_id).all()

    for fav in favorite_reviews:
        favorites.add(fav.review_id)

    return favorites


def format_reviews_to_dicts(reviews, user, favorites):
    """Format a list of review tuples into a list of dictionaries.

       This list will be sent to the front-end via json
    """

    rev_dict_list = []

    for rev in reviews:
        rev_dict = {}
        rev_dict["review_id"] = rev[0]
        rev_dict["reviewer_name"] = rev[2]
        rev_dict["review"] = rev[3]
        rev_dict["summary"] = rev[8]
        rev_dict["score"] = rev[7]
        rev_dict["time"] = rev[9]
        rev_dict["user"] = user       # Is user logged in?
        rev_dict["favorite"] = rev[0] in favorites   # Boolean of whether review is favorited
        rev_dict_list.append(rev_dict)

    return rev_dict_list


def update_favorite_product(user_id, asin):
    """Update a product's favorited-status in a user's account"""

    favorite = FavoriteProduct.query.filter(FavoriteProduct.user_id==user_id,
                                            FavoriteProduct.asin==asin)

    if favorite.count() == 0:
        # If the user has not favorited the product, add it to the db
        favorite_product = FavoriteProduct(user_id=user_id,
                                           asin=asin)
        db.session.add(favorite_product)
        db.session.commit()
        return "Favorited"

    else:
        # If the user has favorited the item, remove the favorite from the db
        db.session.delete(favorite.one())
        db.session.commit()
        return "Unfavorited"


def update_favorite_review(user_id, review_id):
    """Update a product's favorited-status in a user's account"""

    favorite = FavoriteReview.query.filter(FavoriteReview.user_id == user_id,
                                           FavoriteReview.review_id == review_id)

    if favorite.count() == 0:
        # If the user has not favorited the product, add it to the db
        favorite_review = FavoriteReview(user_id=user_id,
                                         review_id=review_id)
        db.session.add(favorite_review)
        db.session.commit()
        return "Favorited"

    else:
        # If the user has favorited the item, remove the favorite from the db
        db.session.delete(favorite.one())
        db.session.commit()
        return "Unfavorited"


def register_user(name, email, password):
    """Register a new user and return a message to flash"""

    # If user exists, flash an error message
    if User.query.filter_by(email=email).count() != 0:
        return "That email already exists. Please login or register for a new account"

    else:
        user = User(name=name,
                    email=email,
                    password=password)

        # Add user to the session
        db.session.add(user)

        # Commit transaction to db
        db.session.commit()

        return "Welcome to ProductGenius"
