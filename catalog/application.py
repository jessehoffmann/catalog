from flask import (
    Flask,
    render_template,
    request,
    make_response,
    url_for,
    redirect,
    flash,
    jsonify,
    session as login_session
)
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker
from catalog import Base, User, Category, Item
import httplib2
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import json
import requests


engine = create_engine('sqlite:///catalog.db?check_same_thread=False')
Base.metadata.create_all(engine)
DBsession = sessionmaker(bind=engine)
session = DBsession()
app = Flask(__name__)

# for Google user authentication
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login', methods=['GET', 'POST'])
def login():
    # create unique string that will be used as token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    # use session for temporary storage of user info
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Deletes user information stored in database. Refernces to user remain
    in their applicable spots throughout different tables in database/
    """
    session.query(User).delete()
    session.commit()
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # authorization code is exchanged for a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see that the access token is google granted is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if token string is empty
    # or if given access token is the one already stored
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # checks if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '''" style=width: 300px;\
              height: 300px;\
              border-radius: 150px;\
              '-webkit-border-radius': 150px;\
              '-moz-border-radius': 150px>'''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Helper functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.email


def getUserID(email):
    if session.query(User).filter_by(email=email).first() is not None:
        user = session.query(User).filter_by(email=email).first()
        return user.email
    else:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    # Disconnects a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        # depopulates login_session so program works during next login
        del login_session['username']
        del login_session['user_id']
        del login_session['email']
        del login_session['picture']
        del login_session['gplus_id']
        del login_session['provider']
        del login_session['state']
        del login_session['access_token']
        return redirect(url_for('showCatalog'))
    else:
        response = make_response(json.dumps('Failed to revoke token\
                                            for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog.json')
def showCatalogJSON():
    """
    Creates a multi-level JSON endpoint containing all relevant information
    stored in the database.
    """
    categories = session.query(Category).all()
    items = session.query(Item).all()
    Catalog = []
    for category in categories:
        dict = category.serialize
        item_list = []
        for item in items:
            if item.category_name == category.name:
                item_list.append(item.serialize)
        item_dict = {'items': item_list}
        dict.update(item_dict)
        Catalog.append(dict)
    return jsonify(Catalog=Catalog)


@app.route('/')
@app.route('/catalog')
def showCatalog():
    # displays category data from catalog including recently created items
    latest_items = session.query(Item).order_by(desc(Item.id)).limit(8)
    categories = session.query(Category.name).all()
    if 'username' not in login_session:
        return render_template('publicshowCatalog.html',
                               categories=categories,
                               latest_items=latest_items)
    else:
        return render_template('showCatalog.html',
                               categories=categories,
                               latest_items=latest_items)


@app.route('/catalog/addcategory', methods=['GET', 'POST'])
def addCategory():
    # add a cateogry to the database
    if request.method == 'GET':
        # check is their is someone logged in
        if 'username' not in login_session:
            return redirect(url_for('showCatalog'))
        return render_template('addCategory.html')
    else:
        # attain cateogry name from html file and create row in database
        category = request.form['title']
        # if category name is blank refresh page
        if category is None:
            return render_template('addCategory.html')
        else:
            new_category = Category(name=category)
            new_category.user_id = login_session['email']
            session.add(new_category)
            session.commit()
            return redirect(url_for('showCatalog'))


@app.route('/catalog/<category_name>/edit', methods=['GET', 'POST'])
def editCategory(category_name):
    # edit a cateogry in the database
    category = session.query(Category).filter_by(name=category_name).one()
    if request.method == 'GET':
        # checks if user created cateogry (has permission to edit)
        if ('username' not in login_session
                or login_session['email'] != category.user_id):
                return redirect(url_for('showItems',
                                        category_name=category_name))
        return render_template('editCategory.html',
                               category_name=category_name)
    else:
        new_name = request.form['title']
        if new_name is None:
            return redirect(url_for('showItems', category_name=category_name))
        else:
            category.name = new_name
            items = session.query(Item)\
                .filter_by(category_name=category_name).all()
            for item in items:
                if item.category_name == category_name:
                    item.category_name = new_name
                    session.add(item)
            session.add(category)
            session.commit()
            return redirect(url_for('showItems',
                            category_name=new_name))


@app.route('/catalog/<category_name>/delete', methods=['GET', 'POST'])
def deleteCategory(category_name):
    category = session.query(Category)\
        .filter_by(name=category_name).first()
    if request.method == 'GET':
        # checks if user created cateogry (has permission to delete)
        if ('username' not in login_session
                or login_session['email'] != category.user_id):
            return redirect(url_for('showCatalog'))
        else:
            return render_template('deleteCategory.html',
                                   category_name=category_name)
    else:
        items = session.query(Item)\
            .filter_by(category_name=category_name).all()
        # also deletes all items in category base on reference in catalog.py
        session.delete(category)
        session.commit()
        return redirect(url_for('showCatalog'))


@app.route('/catalog/<category_name>')
@app.route('/catalog/<category_name>/showitems')
def showItems(category_name):
    categories = session.query(Category.name)
    items = session.query(Item).filter_by(category_name=category_name).all()
    count = session.query(Item).filter_by(category_name=category_name).count()
    category = session.query(Category)\
        .filter_by(name=category_name).first()
    # checks if a user is logged in (has permission to create/edit/delete)
    if ('username' not in login_session
            or login_session['email'] != category.user_id):
            return render_template('publicshowItems.html',
                                   categories=categories,
                                   items=items, category_name=category_name,
                                   count=count)
    else:
        return render_template('showItems.html', categories=categories,
                               items=items, category_name=category_name,
                               count=count)


@app.route('/catalog/additem', methods=['GET', 'POST'])
def addItem():
    categories = session.query(Category.name)
    if request.method == 'GET':
        # check if a user is logged in
        if 'username' not in login_session:
            return redirect(url_for('showCatalog'))
        return render_template('addItem.html', categories=categories)
    else:
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        # only allows item to be added if all forms have been filled out
        if title is None or description is None or category is None:
            return redirect(url_for('showCatalog'))
        else:
            # create new item from name
            item = Item(name=title)
            # add description and cateogory to item
            item.description = description
            item.category_name = category
            session.add(item)
            session.commit()
            return redirect(url_for('showCatalog'))


@app.route('/catalog/<category_name>/<item_name>')
def itemInfo(category_name, item_name):
    # displays the description of specific item and links to edit/delete
    item = session.query(Item).filter_by(name=item_name).one()
    if ('username' not in login_session
            or login_session['email'] != item.user_id):
            return render_template('publiciteminfo.html',
                                   category=category_name, item=item)
    else:
        return render_template('iteminfo.html',
                               category=category_name, item=item)


@app.route('/catalog/<category_name>/<item_name>/edit',
           methods=['GET', 'POST'])
def editItem(category_name, item_name):
    categories = session.query(Category.name)
    item = session.query(Item).filter_by(name=item_name).one()
    if request.method == 'GET':
        # check if a user is logged in and has permission
        if ('username' not in login_session
                or login_session['email'] != item.user_id):
                return redirect(url_for('showItems',
                                category_name=category_name))
        return render_template('editItem.html',
                               categories=categories, item=item)
    else:
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        # can only edit item when all forms have been filled
        if not title or not description or not category:
            return redirect(url_for('itemInfo', category_name=category_name,
                                    item_name=item_name))
        else:
            # replace item info
            item.name = title
            item.description = description
            item.category_name = category
            session.add(item)
            session.commit()
            return redirect(url_for('itemInfo',
                            category_name=category_name, item_name=title))


@app.route('/catalog/<category_name>/<item_name>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    # delete a specific item
    categories = session.query(Category.name)
    item = session.query(Item).filter_by(name=item_name).first()
    if request.method == 'GET':
        # check if a user is logged in and has permission
        if ('username' not in login_session
                or login_session['email'] != item.user_id):
                return redirect(url_for('showItems',
                                        category_name=category_name))
        return render_template('deleteItem.html',
                               categories=categories, item=item)
    else:
        session.delete(item)
        session.commit()
        return redirect(url_for('showItems', category_name=category_name))


# execute code only when module is run as program
if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host="0.0.0.0", port=8000)
