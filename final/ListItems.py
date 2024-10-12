from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import  SQLAlchemy
from flask_wtf import FlaskForm
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
from wtforms import StringField, SubmitField, IntegerField, PasswordField, BooleanField, EmailField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import *
import string, random

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config["SECRET_KEY"] = "secrets.token_hex(16)"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.sqlite3"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "sqlalchemy"
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

def validateCardNumber(FlaskForm, field):
    card_number = str(field.data)
    cleaned_number = card_number.replace(" ", "").replace("-", "")    #custom validator for cardNumber field. Removes whitelisted characters and if remaining string is only digits, its validated.
    if not cleaned_number.isdigit():
        raise ValidationError("Invalid card number. Hyphens, spaces,  and digits are allowed only")
    
def validateExpiryEnd(FlaskForm, field):
    expiry = str(field.data)
    cleaned_expiry = expiry.replace(" ", "").replace("-", "")
    if not cleaned_expiry.isdigit():
        raise ValidationError("Invalid expiry date. Hyphens, spaces,  and digits are allowed only")
    
def validateCVC(FlaskForm, field):
    try:
        cvc = int(field.data)
        if len(str(field.data)) > 3:
            raise ValidationError("Invalid CVC. (it is the 3 digits on the back of your card :3")
    except ValueError:
        raise ValidationError("Invalid CVC. (3 digits on the back of your card)")
    except:
        raise ValidationError("How you mess up typing 3 digits that badly")

def set_password(self, password):
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password_hash, password)

class creditCardForm(FlaskForm):
    
    cardNumber = StringField("Card Number: ", validators = [DataRequired(), Length(min=16, max=19), validateCardNumber], render_kw={'placeholder':"1234 5678 9876 5432"})
    expiryDate = StringField("Expiry End: ", validators= [DataRequired(), Length(min=4, max=5), validateExpiryEnd], render_kw={'placeholder': "mm/yy"})
    cvc = StringField("CVC: ", validators= [DataRequired(), validateCVC])
    Submit = SubmitField("PAY NOW")
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')
    
class signUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up!')


class bike(db.Model):
    __tablename__ = 'bikes'
    product_id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(16), index = True, unique=True)
    price = db.Column(db.Float(32)) 
    description = db.Column(db.Text)
    imagefilename = db.Column(db.String(32), unique=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    

@app.route('/clear_session_data')
def clear_session_data():
    session.clear()
    
    if len(session) == 0:
        print("Session data has been cleared.")
    else:
        print("Failed to clear session data.")

@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    form = signUpForm()
    users = User.query.all()
    if form.validate_on_submit():
        
        username = str(form.username.data)
        password = form.password.data                       #only really ask for email to look legit
        
        if User.query.filter_by(username=username).first() in users:
            flash('That username is already taken.')
            return redirect(url_for('signUp'))
        
        new_User = User(username=username) #, email=email
        set_password(new_User, password)
        
        db.session.add(new_User)
        db.session.commit()
        login_user(new_User)
        return redirect(url_for('index'))
    return render_template('signUp.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    #need to figure out how to clear flashed messages because they're retained after every request atm
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not check_password(user, form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'basket' not in session:
        print("New Session", flush=True)
        session['basket'] = []
        
    bikes = bike.query.all()
    sortingMethod = request.form.get('filter_select')
    if sortingMethod != None:
        if sortingMethod == '1':
            sortedBikes = sorted(bikes, key=lambda bike: bike.name)
        elif sortingMethod == '2':
            sortedBikes = sorted(bikes, key=lambda bike: bike.name, reverse=True)
        elif sortingMethod == '3':
            sortedBikes = sorted(bikes, key=lambda bike: bike.price)
        elif sortingMethod == '4':
            sortedBikes = sorted(bikes, key=lambda bike: bike.price, reverse=True)
        bikes = sortedBikes        
        
        
    return render_template('index.html', bikes = bikes, basket = session['basket']) #form=form

def generateOrderID(length):
    source = string.ascii_lowercase + string.ascii_uppercase + string.digits
    id = ''.join((random.choice(source) for i in range(length)))
    return id


@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    form = creditCardForm()
    quantities = getQuantities(session['basket'])
    totalPrice = gettotalPrice(bike, quantities)
    ordered = False
    if form.validate_on_submit():
        ordered = True
        orderID = generateOrderID(16)
        session['basket'] = [] #if order goes through successfully, clear cart
        return render_template('checkoutPage.html', totalPrice=totalPrice, form=form, ordered = ordered, orderID = orderID)

    return render_template('checkoutPage.html', totalPrice=totalPrice, form=form, ordered = ordered)


def getQuantities(basket):
    session['quantities'] = dict.fromkeys(basket)
    for item in session['quantities']:
        session['quantities'][item] = basket.count(item)
            
    return session['quantities']
    
@app.route('/empty_basket', methods=['POST', 'GET'])
def empty_basket():
    if 'basket' not in session:
        pass
    else:
        session['basket'] = []
    return redirect(url_for('view_basket'))


@app.route('/remove_from_basket/<int:bike_id>', methods=['POST', 'GET'])
def remove_from_basket(bike_id):
    if 'basket' not in session:
        pass
    else:
        if bike_id in session['basket']:    #.remove() doesn't work on these Lists idk why so gotta create whole new list without the itemtoRemove
            temp = []
            for i in session['basket']:
                if i == bike_id:
                    continue
                temp.append(i)
            session['basket'] = temp
        
    return redirect(url_for('view_basket', basket=session['basket']))

@app.route('/increase_basket_quantity/<int:bike_id>', methods=['POST'])
def increase_basket_quantity(bike_id):
    if bike_id in session['basket']:
        session['basket'] += [bike_id]
        
    return redirect(url_for('view_basket'))

    
@app.route('/decrease_basket_quantity/<int:bike_id>', methods=['POST'])
def decrease_basket_quantity(bike_id):
    if bike_id in session['basket']: 
            removed_first_instance = False
            temp = []
            for i in session['basket']:  #again, .remove() doesnt work so create new list that has only the first instance of itemtoRemove removed
                if i == bike_id and not removed_first_instance:
                    removed_first_instance = True
                else:
                    temp.append(i)
            session['basket'] = temp
    return redirect(url_for('view_basket'))

@app.route('/add_to_basket/<int:bike_id>', methods=['POST', 'GET'])
def add_to_basket(bike_id):
    if 'basket' not in session:
        session['basket'] = []
        
    session['basket'] += [bike_id] #add ids to basket, then in template, GET names and other details via id
    return redirect(url_for('index'))

@app.route('/basket')
def view_basket():
    basket = session.get('basket', [])
    quantities = getQuantities(basket)
    totalPrice = gettotalPrice(bike, quantities)
    
    # print(quantities)
    # print(basket)    #TESTING PURPOSESSSSS
    return render_template('basket.html', basket = basket, bike = bike, quantities = quantities, totalPrice = totalPrice)

def gettotalPrice(bike, quantities):
    totalPrice = Decimal(0)
    for i in quantities:
        priceString = bike.query.get(i).price
        # price = ''.join(letter for letter in str(priceString) if letter.isalnum())
        price = Decimal(priceString)
        totalPrice += price*quantities[i]
    return totalPrice.quantize(Decimal('0.00'))

@app.route('/bike/<int:bike_id>', methods = ["GET", "POST"])
def singleProductPage(bike_id):
    selected_bike = bike.query.get(bike_id)
    return render_template("SingleTech.html", bike = selected_bike)

if __name__ == '__main__':
    app.run(debug=True)    