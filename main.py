import random
import smtplib
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SelectField, SubmitField, ValidationError
from wtforms.validators import DataRequired, URL
from flask_sqlalchemy import SQLAlchemy
import config

# ============================================================================
app = Flask(__name__)
app.config.from_object(config.conf)

Bootstrap(app)
csrf = CSRFProtect(app)

# ============================================================================
##Connect to Database
db = SQLAlchemy(app)

class Cafe(db.Model):
    """
        Cafe TABLE Configuration
    """
    __tablename__ = "cafes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        """
            Package all items into a dict in order to more convinient usage afterward.
            For loop and save all columns into a dict, return this dict
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def __repr__(self):
        """Preset the key info to be printed"""
        return f"<{self.id}, {self.name}, {self.location}, {self.map_url}>"

# Create table:
with app.app_context():
    db.create_all()

# ============================================================================
class AddCafeForm(FlaskForm):
    """
        Allow user to add new cafe information to the database.
    """
    name = StringField(label='Cafe name', validators=[DataRequired()])
    map_url = StringField(label='Google Map Link', validators=[DataRequired(), URL()])
    img_url = StringField(label='Image Link', validators=[DataRequired(), URL()])
    location = StringField(label='Location', validators=[DataRequired()])
    seats = StringField(label='Seats', validators=[DataRequired()])
    has_toilet = SelectField(label='Toilet', choices=["YES","NO"], validators=[DataRequired()])
    has_wifi = SelectField(label='Wifi', choices=["YES","NO"], validators=[DataRequired()])
    has_sockets = SelectField(label='Socket', choices=["YES","NO"], validators=[DataRequired()])
    can_take_calls = SelectField(label='Can take calls?', choices=["YES","NO"], validators=[DataRequired()])
    coffee_price = StringField(label='Coffee Price (£)', validators=[DataRequired()])
    submit = SubmitField(label='Submit')

class UpdateCafeForm(FlaskForm):
    """
        Allow user to edit existing cafe information to the database.
    """
    csrf_token = StringField(validators=[DataRequired()])
    name = StringField(label='Cafe name', validators=[DataRequired()])
    map_url = StringField(label='Google Map Link', validators=[DataRequired(), URL()])
    img_url = StringField(label='Image Link', validators=[DataRequired(), URL()])
    location = StringField(label='Location', validators=[DataRequired()])
    seats = StringField(label='Seats', validators=[DataRequired()])
    has_toilet = SelectField(label='Toilet', choices=["YES","NO"], validators=[DataRequired()])
    has_wifi = SelectField(label='Wifi', choices=["YES","NO"], validators=[DataRequired()])
    has_sockets = SelectField(label='Socket', choices=["YES","NO"], validators=[DataRequired()])
    can_take_calls = SelectField(label='Can take calls?', choices=["YES","NO"], validators=[DataRequired()])
    coffee_price = StringField(label='Coffee Price (£)', validators=[DataRequired()])
    submit = SubmitField(label='Comfirm')

    def validate_coffee_price(self, field):
        """
            Validate the format of coffee_price.
        """
        if not field.data.startswith('£'):
            raise ValidationError("Price must starts with '£'.")

class DeletCafeForm(FlaskForm):
    """
        Allow user with APIKey to delete a cate in database.
    """
    csrf_token = StringField(validators=[DataRequired()])
    api_key = StringField(label='Secret-Key:', validators=[DataRequired()])
    submit = SubmitField(label='Delete')

class ReportClosed(FlaskForm):
    """
        Allow user without APIKey to report a cafe closed to site admin.
    """
    sender = StringField(label='Your e-mail:', validators=[DataRequired()])
    message = StringField(label='Message:', validators=[DataRequired()])
    submit = SubmitField(label='Send')

# ============================================================================
@app.route("/")
def home():
    """HTTP Render template"""
    return render_template("index.html")

@app.route('/random')
def get_random_cafe():
    """HTTP GET - Read Record"""
    with app.app_context():
        cafes = db.session.query(Cafe).all()
        random_cafe = random.choice(cafes)
        return jsonify(cafe=random_cafe.to_dict())

@app.route('/cafes')
def get_all_cafes():
    """
        Read all existing cafes's information, save into a list, and show in cafes.html page row by row.
    """
    with app.app_context():
        all_cafes = db.session.query(Cafe).all()
        list_of_rows = []
        for cafe in all_cafes:
            list_of_rows.append(cafe.to_dict())
    return render_template('cafes.html', all_cafes=list_of_rows)

@app.route('/search')
def get_cafe_at_location():
    """
        Use 'loc' as keyword to search particular cafe(s). 
        eg.:
            127.0.0.1:5000/search?loc=Peckham
    """
    # request: get data inputted by user for the parameter of loc
    query_location = request.args.get("loc")

    # Use the keyword 'loc' by user to match the data in database
    with app.app_context():
        cafe = db.session.query(Cafe).filter(Cafe.location == query_location).first()
        # If there's matching result, return it
        if cafe:
            return jsonify(cafe=cafe.to_dict())
        # Else, return an errow message
        else:
            return jsonify(error={"Not Found": "Sorry, we don't have a cafe at this location."})

@app.route('/add', methods=['GET', 'POST'])
def add_cafe():
    """
        Add new cafe to the database and display all in the site.
    """
    form = AddCafeForm()
    if form.validate_on_submit():
        print("True")
        new_cafe = Cafe(
            name = request.form.get('name'),
            map_url = request.form.get('map_url'),
            img_url = request.form.get('img_url'),
            location = request.form.get('location'),
            seats = request.form.get('seats'),
            has_toilet = True if request.form.get('has_toilet')=='YES' else False,
            has_wifi = True if request.form.get('has_wifi')=='YES' else False,
            has_sockets = True if request.form.get('has_sockets')=='YES' else False,
            can_take_calls = True if request.form.get('can_take_calls')=='YES' else False,
            coffee_price = f"£{request.form.get('coffee_price')}",
        )
        with app.app_context():
            db.session.add(new_cafe)
            db.session.commit()
            return redirect(url_for('get_all_cafes'))
    return render_template('add.html', form=form)

@app.route('/update-cafe/<int:cafe_id>', methods=["GET", "POST"])
def update_cafe(cafe_id):
    """
        HTTP POST - Update Record to SQL database
        * URL format: http://127.0.0.1:5000/update-cafe/21
        1. Must with csrf_token
        2. Show existing data and update the latest to SQL database, Watch out the data type.
            form.populate_obj(cafe): this can be used to data update but may fail because of data type.
        3. Must use db.session.add() before commit, or else the update may fail.
            db.session.add(cafe)
            db.session.commit()
    """
    with app.app_context():
        cafe = Cafe.query.get_or_404(cafe_id)

    form = UpdateCafeForm(obj=cafe)
    if form.validate_on_submit():
        print('Form validation succeed.')
        cafe.name = form.name.data
        cafe.map_url = form.map_url.data
        cafe.img_url = form.img_url.data
        cafe.location = form.location.data
        cafe.seats = form.seats.data
        cafe.has_toilet = True if form.has_toilet.data=='YES' else False
        cafe.has_wifi = True if form.has_wifi.data=='YES' else False
        cafe.has_sockets = True if form.has_sockets.data=='YES' else False
        cafe.can_take_calls = True if form.can_take_calls.data=='YES' else False
        cafe.coffee_price = form.coffee_price.data
        try:
            db.session.add(cafe)
            db.session.commit()
            print(f'New cafe name: {cafe.name}')
            flash(f"{cafe.name}'s information updated successfully!!!", "success")
            return redirect(url_for('get_all_cafes'))
        except Exception as e:
            flash(f"Failed to update {cafe.name}'s information: {str(e)}", "danger")
            db.session.rollback()
    else:
        print('Form validation failed.')
        for field in form:
            if field.errors: 
                print(f"Field {field.name}: {field.errors}")

    return render_template("edit.html", form=form)


@app.route('/report-closed/<int:cafe_id>', methods=["GET", "POST", "DELETE"])
def delete_cafe(cafe_id):
    """
        HTTP DELETE - Delete Record
        * URL format: http://127.0.0.1:5000/report-close/22
        1. When a user found a cafe already closed, can click "Report Closed" button to inform the site admin.
        2. Or input the "TopSecretAPIKey" to proceed.
        ref: https://youtu.be/MQ-O0Vx5YFw?si=ba-EyIx3p48_QIwM
    """
    del_form = DeletCafeForm()
    report_form = ReportClosed()

    api_key = request.form.get('api_key')
    if api_key == app.config['API_KEY']:
        with app.app_context():
            cafe = Cafe.query.get_or_404(cafe_id)
            db.session.delete(cafe)
            db.session.commit()
            flash(f"{cafe.name} has been deleted!!", "success")
            return redirect(url_for('get_all_cafes'))
    
    if report_form.validate_on_submit():
        with app.app_context():
            cafe = Cafe.query.get_or_404(cafe_id)
        sender = request.form.get('sender')
        message_from_usr = f"{request.form.get('message')}\n-----\nCafe's Info: {cafe}"

        send_email(sender, message_from_usr)
        flash(f"Closed report of {cafe.name} has been sent to site admin seccessfully!!", "success")
        return redirect(url_for('get_all_cafes'))

    return render_template("report.html", del_form=del_form, report_form=report_form)


def send_email(sender, message):
    """Send a report-closed mail to site admin """
    mail_server = app.config['MAIL_SERVER']
    mail_port = app.config['MAIL_PORT']
    email = app.config['OWN_EMAIL']
    pw = app.config['OWN_PW']
    email_message = f"Subject: [Free-wifi-Cafes] A New Report Message!\n\nName: {sender}\n-----\nMessage:{message}"
    try:
        with smtplib.SMTP(mail_server, mail_port) as server:
            server.ehlo(mail_server)
            server.starttls()
            server.login(user=email, password=pw)
            server.sendmail(from_addr=email, to_addrs=email, msg=email_message)
        flash('Email sent successfully', 'success')
    except Exception as e:
        flash(f'Failed to send email: {e}', 'danger')

# ============================================================================
if __name__ == '__main__':
    app.run()
