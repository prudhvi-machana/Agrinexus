from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
from datetime import datetime 
import bcrypt
from flask_mysqldb import MySQL
import MySQLdb

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'jayanthi@21'
app.config['MYSQL_DB'] = 'AgriData'

mysql = MySQL(app)

class RegisterForm(FlaskForm):
    auth_name = StringField("Full Name", validators=[
        DataRequired(), 
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    
    auth_email = StringField("Email", validators=[
        DataRequired(),
        Regexp(r'^[^@]+@[^@]+\.[^@]+$', message="Email must contain '@' and have a valid structure.")
    ])
    
    auth_pass = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long."),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
               message="Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character.")
    ])
    auth_phone_no = StringField("Phone Number", validators=[
        DataRequired(), Length(min=10, max=15),
        Regexp(r'^\d{10,15}$', message="Phone number must be 10-15 digits.")
    ])

    submit = SubmitField("Register")


    def validate_field(self, field, column_name, message):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM auths WHERE {column_name} = %s", (field.data,))
        exists = cursor.fetchone()
        cursor.close()
        if exists:
            raise ValidationError(message)

    def validate_auth_email(self, field):
        self.validate_field(field, 'auth_email', 'Email already exists')

    def validate_auth_phone_no(self, field):
        self.validate_field(field, 'auth_phone_no', 'Phone number already exists')

class LoginForm(FlaskForm):
    auth_email = StringField("Email", validators=[DataRequired()])
    auth_pass = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/auth_register', methods=['GET', 'POST'])
def auth_register():
    form = RegisterForm()
    if form.validate_on_submit():
        auth_name = form.auth_name.data
        auth_email = form.auth_email.data
        auth_pass = form.auth_pass.data
        auth_phone_no =form.auth_phone_no.data

        hashed_auth_pass = bcrypt.hashpw(auth_pass.encode('utf-8'), bcrypt.gensalt())
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO auths (auth_name, auth_email, auth_pass, auth_phone_no) VALUES (%s, %s, %s, %s)",
                       (auth_name, auth_email, hashed_auth_pass, auth_phone_no))
        mysql.connection.commit()
        cursor.close()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth_login'))
    
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f' {error}', 'error')

    return render_template('auth_register.html', form=form)

@app.route('/auth_login', methods=['GET', 'POST'])
def auth_login():
    form = LoginForm()
    if form.validate_on_submit():
        auth_email = form.auth_email.data
        auth_pass = form.auth_pass.data

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) 
        cursor.execute("SELECT * FROM auths WHERE auth_email=%s", (auth_email,))
        auth = cursor.fetchone()
        cursor.close()

        if auth and bcrypt.checkpw(auth_pass.encode('utf-8'), auth['auth_pass'].encode('utf-8')):
            session['auth_id'] = auth['auth_id']
            session['auth_email'] = auth['auth_email']
            session['auth_name'] = auth['auth_name']
            auth_name = auth['auth_name']
            flash('Login successful!', 'success')
            if 'auth_id' in session:
                return redirect(url_for('existingfarmers'))
        else:
            flash('Invalid credentials, please try again.', 'error')

    return render_template('auth_login.html', form=form)

@app.route('/farmer_login', methods=['GET', 'POST'])
def farmer_login():
    if request.method == 'POST':
        aadhar_id = request.form.get('aadhar_id')
        phone_no = request.form.get('phone_no')

        # Query the database without additional input validation
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s AND phone_no = %s", (aadhar_id, phone_no))
        farmer = cursor.fetchone()
        cursor.close()

        if farmer:
            session['aadhar_id'] = farmer['aadhar_id']
            session['farmer_name'] = farmer['farmer_name']
            flash('Login successful!', 'success')
            return redirect(url_for('farmer_details'))
        else:
            flash('Invalid Aadhar ID or Phone Number.', 'error')

    return render_template('farmer_login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('farmer_login'))  # Redirect to the login page

# Route for displaying farmer details
@app.route('/farmer_details')
def farmer_details():
    aadhar_id = session.get('aadhar_id')  # Get AADHAR ID from session
    if not aadhar_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('farmer_login'))

    # Fetch farmer details from the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    cursor.close()

    if not farmer:
        flash("Farmer not found.", "error")
        return redirect(url_for('farmer_login'))

    # Render the farmer details template
    return render_template('farmer_details.html', farmer=farmer)

@app.route('/farmer_lands')
def farmer_lands():
    aadhar_id = session.get('aadhar_id')  # Get AADHAR ID from session
    if not aadhar_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('farmer_login'))

    search_avail_land = request.args.get('search_avail_land')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if search_avail_land:  # If there's a search query
        cursor.execute("SELECT * FROM lands WHERE aadhar_id = %s AND location LIKE %s AND deleted = FALSE", 
                       (aadhar_id, '%' + search_avail_land + '%'))
        lands = cursor.fetchall()
        if not lands:
            flash('No land found for this location.', 'error')

    else:
        cursor.execute("SELECT * FROM lands WHERE aadhar_id = %s AND deleted = FALSE", (aadhar_id,))  # Only present lands
        lands = cursor.fetchall()
    
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    cursor.close()

    # Render the farmer lands template
    return render_template('farmer_lands.html', lands=lands, farmer=farmer)


#Route to crops
@app.route('/farmer_crops')
def farmer_crops():
    aadhar_id = session.get('aadhar_id')  # Get AADHAR ID from session
    if not aadhar_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('farmer_login'))

    search_avail_crop = request.args.get('search_avail_crop')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)


    # Search for specific crops if there's a search query
    if search_avail_crop:
        cursor.execute("""SELECT * FROM crops WHERE aadhar_id = %s AND crop_name LIKE %s """, 
                        (aadhar_id, '%' + search_avail_crop + '%'))
        crops = cursor.fetchall()
        if not crops:
            flash('No crop found for this type.', 'error')
    else:
        # Fetch present crops (deleted = 0)
        cursor.execute("""SELECT * FROM crops WHERE aadhar_id = %s """, (aadhar_id,))
        crops = cursor.fetchall()

    # Fetch farmer details
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    cursor.close()

    # Render the farmer crops template
    return render_template('farmer_crops.html', crops=crops,farmer=farmer)


# Route for displaying loans taken by the logged-in farmer
@app.route('/farmer_loans_taken')
def farmer_loans_taken():
    aadhar_id = session.get('aadhar_id')  # Get AADHAR ID from session
    if not aadhar_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('farmer_login'))
    
    search_loan_taken = request.args.get('search_loan_taken')  # Get search query from request
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if search_loan_taken:  # If there's a search query
        # Fetch loans taken by the farmer based on the search query
        cursor.execute("SELECT * FROM loans_taken WHERE aadhar_id = %s AND loan_type LIKE %s", 
                       (aadhar_id, '%' + search_loan_taken + '%'))
        
        loans_taken = cursor.fetchall()
        if not loans_taken:
            flash('No loan taken found for this type.', 'error')

    else:
        # Fetch all loans taken by the farmer
        cursor.execute("SELECT * FROM loans_taken WHERE aadhar_id = %s", (aadhar_id,))

        loans_taken = cursor.fetchall()  # Get all loans taken by the farmer

    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    cursor.close()

    # Render the farmer loans taken template
    return render_template('farmer_loans_taken.html', loans_taken=loans_taken, farmer=farmer)

# Route for displaying subsidies taken by the logged-in farmer
@app.route('/farmer_subsidies_taken')
def farmer_subsidies_taken():
    aadhar_id = session.get('aadhar_id')  # Get AADHAR ID from session
    if not aadhar_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('farmer_login'))
    
    search_subsidy_taken = request.args.get('search_subsidy_taken')  # Get search query from request
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if search_subsidy_taken:  # If there's a search query
        # Fetch subsidies taken by the farmer based on the search query
        cursor.execute("SELECT * FROM subsidies_taken WHERE aadhar_id = %s AND subsidy_name LIKE %s", 
                       (aadhar_id, '%' + search_subsidy_taken + '%'))
        subsidies_taken = cursor.fetchall()
        if not subsidies_taken:
            flash('No subsidy taken found for this type.', 'error')

    else:
        # Fetch all subsidies taken by the farmer
        cursor.execute("SELECT * FROM subsidies_taken WHERE aadhar_id = %s", (aadhar_id,))
        subsidies_taken = cursor.fetchall()

    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    cursor.close()

    # Render the farmer subsidies taken template
    return render_template('farmer_subsidies_taken.html', subsidies_taken=subsidies_taken, farmer=farmer)


# Route for displaying schemes taken by the logged-in farmer
@app.route('/farmer_schemes_taken')
def farmer_schemes_taken():
    aadhar_id = session.get('aadhar_id')  # Get AADHAR ID from session
    if not aadhar_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('farmer_login'))
    
    search_scheme_taken = request.args.get('search_scheme_taken')  # Get search query from request
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if search_scheme_taken:  # If there's a search query
        # Fetch schemes taken by the farmer based on the search query
        cursor.execute("SELECT * FROM schemes_taken WHERE aadhar_id = %s AND scheme_name LIKE %s", 
                       (aadhar_id, '%' + search_scheme_taken + '%'))
        schemes_taken = cursor.fetchall()
        if not schemes_taken:
            flash('No scheme taken found for this type.', 'error')

    else:
        # Fetch all schemes taken by the farmer
        cursor.execute("SELECT * FROM schemes_taken WHERE aadhar_id = %s", (aadhar_id,))
        schemes_taken = cursor.fetchall()  # Get all schemes taken by the farmer

    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    cursor.close()

    # Render the farmer schemes taken template
    return render_template('farmer_schemes_taken.html', schemes_taken=schemes_taken, farmer=farmer)



# Route to view available loans without requiring login
@app.route('/available_loans')
def available_loans():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM loans WHERE deleted = FALSE")  # Fetch only active loans
    loans = cur.fetchall()
    cur.close()
    return render_template('available_loans.html', loans=loans)

# Route to search loans by loan type
@app.route('/search_available_loan', methods=['GET'])
def search_available_loan():
    loan_type = request.args.get('loan_type', '')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if loan_type:
        cursor.execute(
            "SELECT * FROM loans WHERE loan_type LIKE %s AND deleted = FALSE",  # Only active loans
            ('%' + loan_type + '%',)
        )
        loans = cursor.fetchall()

        if not loans:
            flash('No loans found for this type.', 'error')
    else:
        cursor.execute("SELECT * FROM loans WHERE deleted = FALSE")  # Only active loans
        loans = cursor.fetchall()

    cursor.close()
    return render_template('available_loans.html', loans=loans)


@app.route('/available_subsidies', methods=['GET'])
def available_subsidies():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM subsidies WHERE deleted = FALSE")
    subsidies = cursor.fetchall()
    cursor.close()
    
    return render_template('available_subsidies.html', subsidies=subsidies)

@app.route('/search_available_subsidy', methods=['GET'])
def search_available_subsidy():
    subsidy_name = request.args.get('subsidy_name', '')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Query the database for subsidies matching the subsidy_name
    if subsidy_name:
        cursor.execute(
            "SELECT * FROM subsidies WHERE subsidy_name LIKE %s AND deleted = FALSE",
            ('%' + subsidy_name + '%',)  # Using LIKE for partial matching
        )
        subsidies = cursor.fetchall()

        if not subsidies:
            flash('No available subsidies found for this name.', 'error')
    else:
        # If no search term is provided, retrieve all subsidies
        cursor.execute("SELECT * FROM subsidies WHERE deleted = FALSE")
        subsidies = cursor.fetchall()

    cursor.close()
    return render_template('available_subsidies.html', subsidies=subsidies)

@app.route('/available_schemes', methods=['GET'])
def available_schemes():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM schemes WHERE deleted = FALSE")
    schemes = cursor.fetchall()
    cursor.close()
    
    return render_template('available_schemes.html', schemes=schemes)

@app.route('/search_available_scheme', methods=['GET'])
def search_available_scheme():
    scheme_name = request.args.get('scheme_name', '')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Query the database for schemes matching the scheme_name
    if scheme_name:
        cursor.execute(
            "SELECT * FROM schemes WHERE scheme_name LIKE %s AND deleted = FALSE",
            ('%' + scheme_name + '%',)  # Using LIKE for partial matching
        )
        schemes = cursor.fetchall()

        if not schemes:
            flash('No available schemes found for this name.', 'error')
    else:
        # If no search term is provided, retrieve all schemes
        cursor.execute("SELECT * FROM schemes WHERE deleted = FALSE")
        schemes = cursor.fetchall()

    cursor.close()
    return render_template('available_schemes.html', schemes=schemes)


@app.route('/addfarmer', methods=['GET', 'POST'])
def addfarmer():
    # Ensure user is authenticated before allowing access to this page
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    if request.method == 'POST':
        # Retrieve form data
        farmer_name = request.form.get('f_name')
        date_of_birth = request.form.get('f_dob')
        gender = request.form.get('f_gender')
        phone_no = request.form.get('f_phone')
        address = request.form.get('f_address')
        aadhar_id = request.form.get('f_aadharId')

        # Connect to MySQL database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if Aadhar ID already exists in the database
        cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
        existing_aadhar_id = cursor.fetchone()

        if existing_aadhar_id:
            flash('Aadhar ID already exists', 'error')
            cursor.close()
            return render_template('addfarmer.html', auth_name=session.get('auth_name'))

        # Check if Phone Number already exists in the database
        cursor.execute("SELECT * FROM farmers WHERE phone_no = %s", (phone_no,))
        existing_phone_no = cursor.fetchone()

        if existing_phone_no:
            flash('Phone number already exists', 'error')
            cursor.close()
            return render_template('addfarmer.html', auth_name=session.get('auth_name'))

        # Insert farmer details into the database
        try:
            cursor.execute(
                """INSERT INTO farmers (farmer_name, date_of_birth, gender, phone_no, address, aadhar_id) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (farmer_name, date_of_birth, gender, phone_no, address, aadhar_id)
            )
            mysql.connection.commit()
            flash('Farmer registered successfully!', 'success')
            return redirect(url_for('existingfarmers'))  # Redirect to the 'existingfarmers' page after registration
        except MySQLdb.Error as err:
            mysql.connection.rollback()
            flash(f'Error storing data: {err}', 'error')
        finally:
            cursor.close()

    return render_template('addfarmer.html', auth_name=session.get('auth_name'))


@app.route('/existingfarmers', methods=['GET'])
def existingfarmers():
    if 'auth_email' not in session:
        return redirect(url_for('auth_login'))

    search_aadhar_id = request.args.get('search_f_aadharId')  # Accessing search query from URL
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if search_aadhar_id:
        cursor.execute("SELECT aadhar_id, farmer_name FROM farmers WHERE aadhar_id LIKE %s", ('%' + search_aadhar_id + '%',))
        farmers = cursor.fetchall()


        if not farmers:
            flash('Farmer with this Aadhar ID does not exist.', 'error')
    else:
        cursor.execute("SELECT aadhar_id, farmer_name FROM farmers")
        farmers = cursor.fetchall()

    cursor.close()
    return render_template('existingfarmers.html', auth_name=session.get('auth_name'), farmers=farmers)


@app.route('/editfarmer/<aadhar_id>', methods=['GET', 'POST'])
def editfarmer(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Fetch existing farmer details using Aadhar ID
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()

    if request.method == 'POST':
        farmer_name = request.form.get('f_name')
        date_of_birth = request.form.get('f_dob')
        gender = request.form.get('f_gender')
        phone_no = request.form.get('f_phone')
        address = request.form.get('f_address')
        new_aadhar_id = request.form.get('f_aadharId')

        try:
            # Check if the new Aadhar ID exists for another farmer
            if new_aadhar_id != farmer['aadhar_id']:
                cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s AND aadhar_id != %s", (new_aadhar_id, aadhar_id))
                if cursor.fetchone():
                    flash('Aadhar ID already exists for another farmer.', 'error')
                    return render_template('editfarmer.html', farmer=farmer)

            # Check if the new Phone Number exists for another farmer
            if phone_no != farmer['phone_no']:
                cursor.execute("SELECT * FROM farmers WHERE phone_no = %s AND aadhar_id != %s", (phone_no, aadhar_id))
                if cursor.fetchone():
                    flash('Phone number already exists for another farmer.', 'error')
                    return render_template('editfarmer.html', farmer=farmer)

            # Update farmer details if no conflicts
            cursor.execute("""
                UPDATE farmers
                SET farmer_name = %s, date_of_birth = %s, gender = %s, phone_no = %s, address = %s, aadhar_id = %s
                WHERE aadhar_id = %s
            """, (farmer_name, date_of_birth, gender, phone_no, address, new_aadhar_id, aadhar_id))
            mysql.connection.commit()

            flash('Farmer details updated successfully!', 'success')
            return redirect(url_for('existingfarmers'))

        except MySQLdb.Error as err:
            mysql.connection.rollback()
            flash(f'Error updating data: {err}', 'error')

        finally:
            cursor.close()

    return render_template('editfarmer.html', farmer=farmer)

@app.route('/deletefarmer/<aadhar_id>', methods=['POST'])
def deletefarmer(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Delete farmer based on Aadhar ID
        cursor.execute("DELETE FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
        mysql.connection.commit()

        flash('Farmer deleted successfully!', 'success')
    except MySQLdb.Error as e:
        mysql.connection.rollback()
        flash(f'Error deleting farmer: {str(e)}', 'error')
    finally:
        cursor.close()

    return redirect(url_for('existingfarmers'))


# Route to manage lands based on aadhar_id
@app.route('/manage_lands/<aadhar_id>', methods=['GET'])
def manage_lands(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))
    
    # Get lands owned by the farmer
    cursor.execute("SELECT * FROM lands WHERE aadhar_id = %s and deleted=False", (aadhar_id,))
    lands = cursor.fetchall()

    cursor.close()
    return render_template('manage_lands.html', farmer=farmer, lands=lands)

# Route to search lands owned by a farmer
@app.route('/search_lands/<aadhar_id>', methods=['GET'])
def search_lands(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Search for lands
    search_land = request.args.get('search_land')  # Accessing search query from URL
    if search_land:
        cursor.execute("""
            SELECT * FROM lands 
            WHERE aadhar_id = %s AND location LIKE  %s and deleted=False
        """, (aadhar_id, '%' + search_land + '%'))
    else:
        cursor.execute("SELECT * FROM lands WHERE aadhar_id = %s and deleted=False", (aadhar_id,))

    lands = cursor.fetchall()
    cursor.close()

    return render_template('manage_lands.html', farmer=farmer, lands=lands)

# Route to add a new land for a farmer
@app.route('/add_land/<aadhar_id>', methods=['POST'])
def add_land(aadhar_id):
    if 'auth_email' not in session:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor()

    location = request.form['location']
    soil_type = request.form['soil_type']
    land_size = request.form['land_size']

    try:
        cursor.execute("""
            INSERT INTO lands (aadhar_id, location, soil_type, land_size)
            VALUES (%s, %s, %s, %s)
        """, (aadhar_id, location, soil_type, land_size))
        mysql.connection.commit()
        flash("Land added successfully!", 'success')
    except MySQLdb.Error as err:
        mysql.connection.rollback()
        flash(f"Error adding land: {err}", 'error')
    
    cursor.close()
    print(request.form)  # This will show you what keys are present in the form data
    return redirect(url_for('manage_lands', aadhar_id=aadhar_id))


# Route to update land information
@app.route('/update_land/<aadhar_id>/<int:land_id>', methods=['POST'])
def update_land(aadhar_id, land_id):
    if 'auth_email' not in session :
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor()
    
    location = request.form.get('location')
    soil_type = request.form.get('soil_type')
    land_size = request.form.get('land_size')

    try:
        cursor.execute("""
            UPDATE lands 
            SET location = %s,soil_type=%s,land_size=%s
            WHERE aadhar_id = %s AND land_id = %s
        """, (location,soil_type,land_size ,aadhar_id, land_id))
        mysql.connection.commit()
        flash("Land information updated successfully!", 'success')
    except MySQLdb.Error as err:
        mysql.connection.rollback()
        flash(f"Error updating land information: {err}", 'error')

    cursor.close()
    return redirect(url_for('manage_lands', aadhar_id=aadhar_id))



# Route to delete a land record
@app.route('/delete_land/<aadhar_id>/<int:land_id>', methods=['POST'])
def delete_land(aadhar_id, land_id):
    if 'auth_email' not in session:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor()

    try:
        # Soft delete by setting the deleted flag to TRUE
        cursor.execute("""
            UPDATE lands 
            SET deleted = TRUE 
            WHERE aadhar_id = %s AND land_id = %s and deleted=False
        """, (aadhar_id, land_id))
        mysql.connection.commit()
        flash("Land deleted successfully!", 'success')
    except MySQLdb.Error as err:
        mysql.connection.rollback()  # Rollback in case of error
        flash(f"Error deleting land: {err}", 'error')
    finally:
        cursor.close()

    return redirect(url_for('manage_lands', aadhar_id=aadhar_id))


#route to manage_crops

@app.route('/manage_crops/<aadhar_id>', methods=['GET'])
def manage_crops(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))
    
    # Get lands owned by the farmer
    cursor.execute("SELECT land_id FROM lands WHERE aadhar_id = %s AND deleted = FALSE", (aadhar_id,))
    available_lands = cursor.fetchall()
  
    # Get crops owned by the farmer
    cursor.execute("SELECT * FROM crops WHERE aadhar_id = %s", (aadhar_id,))
    crops = cursor.fetchall()

    cursor.close()
    return render_template('manage_crops.html', farmer=farmer, crops=crops, available_lands=available_lands)

# Route to add a new crop
@app.route('/add_crop/<aadhar_id>', methods=['POST'])
def add_crop(aadhar_id):
    if 'auth_email' not in session:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    land_id = request.form['land_id']
    crop_name = request.form['crop_name']
    crop_size = float(request.form['crop_size'])
    N_percent = float(request.form['N_percent'])
    P_percent = float(request.form['P_percent'])
    K_percent = float(request.form['K_percent'])
    soil_ph = float(request.form['soil_ph'])
    planting_date = request.form['planting_date']
    harvest_date = request.form.get('harvest_date') or None
    crop_suggestion = request.form.get('crop_suggestion') or None
    
    # Get land size
    cursor.execute("SELECT land_size FROM lands WHERE land_id = %s", (land_id,))
    land = cursor.fetchone()
    planting_date_obj = datetime.strptime(planting_date, '%Y-%m-%d')
    if harvest_date:
        harvest_date_obj = datetime.strptime(harvest_date, '%Y-%m-%d')
        
        # Check if planting_date is before harvest_date
        if planting_date_obj >= harvest_date_obj:
            flash("Planting date must be earlier than harvest date.", "error")
            return redirect(url_for('manage_crops', aadhar_id=aadhar_id))  # Redirect back to the form page

    
    if not (0 <= N_percent <= 100):
        flash("Invalid Nitogen Percent value. Value sholud be in between 0 and 100", 'error')
        return redirect(url_for('manage_crops', aadhar_id=aadhar_id))
    if not (0 <= P_percent <= 100):
        flash("Invalid Phosphorus Percent value. Value sholud be in between 0 and 100", 'error')
        return redirect(url_for('manage_crops', aadhar_id=aadhar_id))
    if not (0 <= K_percent <= 100):
        flash("Invalid Pottasium Percent value. Value sholud be in between 0 and 100", 'error')
        return redirect(url_for('manage_crops', aadhar_id=aadhar_id))
    if not (0 <= soil_ph <= 14):
        flash("Invalid soil pH value. Value sholud be in between 0 and 14", 'error')
        return redirect(url_for('manage_crops', aadhar_id=aadhar_id))

    if land:
        land_size = land['land_size']

        # Check if the total crop size exceeds the land size
        cursor.execute("""
            SELECT SUM(crop_size) AS total_crop_size
            FROM crops 
            WHERE land_id = %s AND aadhar_id = %s 
        """, (land_id, aadhar_id))
        result = cursor.fetchone()
        total_crop_size = result['total_crop_size'] or 0

        if float(total_crop_size) + float(crop_size) > float(land_size):
            flash(f"Cannot add crop. Total crop size exceeds land size ({land_size} acres).", 'error')
            return redirect(url_for('manage_crops', aadhar_id=aadhar_id))
        
    cursor.execute("""SELECT * FROM crops WHERE land_id = %s AND crop_name = %s AND planting_date = %s AND aadhar_id = %s""",(land_id, crop_name,planting_date, aadhar_id))
    existing_crop = cursor.fetchone()

    if existing_crop:
        flash("A crop with this name and planting date already exists for this farmer.", 'error')
        return redirect(url_for('manage_crops', aadhar_id=aadhar_id))
    try:
        # Insert new crop into the database
        cursor.execute("""
            INSERT INTO crops (land_id, crop_name, crop_size,N_percent,P_percent,K_percent,soil_ph,planting_date, harvest_date, crop_suggestion, aadhar_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s,%s,%s)
        """, (land_id, crop_name, crop_size, N_percent,P_percent,K_percent,soil_ph, planting_date, harvest_date, crop_suggestion, aadhar_id))

        mysql.connection.commit()
        flash('Crop added successfully.', 'success')
    except MySQLdb as e:
        mysql.connection.rollback()
        flash(f'Error storing data: {e}', 'error')

    cursor.close()
    return redirect(url_for('manage_crops', aadhar_id=aadhar_id))

#Route to search the crop
@app.route('/search_crops/<aadhar_id>', methods=['GET'])
def search_crops(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Get search query from URL
    search_crop = request.args.get('search_crop')  # Accessing search query from URL
    if search_crop:
        # Search for crops with name like the search query
        cursor.execute("""
            SELECT * FROM crops 
            WHERE aadhar_id = %s AND crop_name LIKE %s 
        """, (aadhar_id, '%' + search_crop + '%'))
    else:
        # If no search query is provided, return all crops
        cursor.execute("SELECT * FROM crops WHERE land_id = %s", (aadhar_id,))

    crops = cursor.fetchall()
    cursor.close()

    return render_template('manage_crops.html', farmer=farmer, crops=crops)


# Route to update a crop
@app.route('/update_crop/<aadhar_id>/<land_id>/<crop_name>/<planting_date>', methods=['POST'])
def update_crop(aadhar_id, land_id, crop_name, planting_date):
    if 'auth_email' not in session:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    harvest_date = request.form.get('harvest_date')
    crop_suggestion = request.form.get('crop_suggestion')

    cursor.execute("""
        UPDATE crops
        SET harvest_date = %s, crop_suggestion = %s
        WHERE land_id = %s AND crop_name = %s AND planting_date = %s
    """, (harvest_date, crop_suggestion, land_id, crop_name, planting_date))

    mysql.connection.commit()
    cursor.close()
    flash('Crop updated successfully.', 'success')

    return redirect(url_for('manage_crops', aadhar_id=aadhar_id))

# Route to delete a crop
@app.route('/delete_crop/<aadhar_id>/<land_id>/<crop_name>/<planting_date>', methods=['POST'])
def delete_crop(aadhar_id, land_id, crop_name, planting_date):
    if 'auth_email' not in session:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        DELETE FROM crops 
        WHERE land_id = %s AND crop_name = %s AND planting_date = %s
    """, (land_id, crop_name, planting_date))

    mysql.connection.commit()
    cursor.close()
    flash('Crop deleted successfully.', 'success')

    return redirect(url_for('manage_crops', aadhar_id=aadhar_id))


# Route to view/manage loans
@app.route('/manage_loans')
def manage_loans():
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM loans WHERE deleted = FALSE")  # Fetch only active loans
    loans = cur.fetchall()
    cur.close()
    return render_template('manage_loans.html', loans=loans, auth_name=session.get('auth_name'))

# Route to search loans by loan type
@app.route('/search_loan', methods=['GET'])
def search_loan():
    loan_type = request.args.get('loan_type', '')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if loan_type:
        cursor.execute(
            "SELECT * FROM loans WHERE loan_type LIKE %s AND deleted = FALSE",  # Only active loans
            ('%' + loan_type + '%',)
        )
        loans = cursor.fetchall()

        if not loans:
            flash('No loans found for this type.', 'error')
    else:
        cursor.execute("SELECT * FROM loans WHERE deleted = FALSE")  # Only active loans
        loans = cursor.fetchall()

    cursor.close()
    return render_template('manage_loans.html', loans=loans, auth_name=session.get('auth_name'))

# Route to add a new loan
@app.route('/add_loan', methods=['GET', 'POST'])
def add_loan():
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    if request.method == 'POST':
        loan_type = request.form.get('loan_type')
        description = request.form.get('description')
        eligibility = request.form.get('eligibility')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM loans WHERE loan_type = %s AND deleted = FALSE", (loan_type,))  # Check only active loans
        existing_loan = cursor.fetchone()

        if existing_loan:
            flash('Loan type already exists', 'error')
            cursor.close()
            return redirect(url_for('manage_loans'))

        try:
            cursor.execute(
                """INSERT INTO loans (loan_type, description, eligibility) 
                   VALUES (%s, %s, %s)""",
                (loan_type, description, eligibility)
            )
            mysql.connection.commit()
            flash('Loan added successfully!', 'success')
            return redirect(url_for('manage_loans'))
        except MySQLdb.Error as err:
            mysql.connection.rollback()
            flash(f'Error storing data: {err}', 'error')
        finally:
            cursor.close()

    return render_template('manage_loans.html', auth_name=session.get('auth_name'))

# Route to update an existing loan
@app.route('/update_loan/<int:id>', methods=['POST'])
def update_loan(id):
    description = request.form.get('description')
    eligibility = request.form.get('eligibility')

    if not description or not eligibility:
        flash('All fields must be filled!', 'error')
        return redirect(url_for('manage_loans'))

    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(""" 
            UPDATE loans 
            SET description = %s, eligibility = %s 
            WHERE loan_id = %s
        """, (description, eligibility, id))
        mysql.connection.commit()
        flash('Loan updated successfully!', 'success')
    except Exception as e:
        flash('Error updating loan: {}'.format(e), 'danger')
    finally:
        cur.close()

    return redirect(url_for('manage_loans'))

# Route to logically delete a loan
@app.route('/delete_loan/<int:loan_id>', methods=['POST'])
def delete_loan(loan_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Logically delete the loan by setting the deleted flag to TRUE
        cur.execute("UPDATE loans SET deleted = TRUE WHERE loan_id = %s", (loan_id,))
        mysql.connection.commit()
        flash('Loan deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting loan: {}'.format(e), 'danger')
    finally:
        cur.close()
    return redirect(url_for('manage_loans'))


# Route to view/manage loans taken by farmers
@app.route('/manage_loans_taken/<aadhar_id>', methods=['GET'])
def manage_loans_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Get active loan types
    cursor.execute("SELECT loan_type FROM loans WHERE deleted = FALSE")
    active_loans = cursor.fetchall()

    # Get loans taken by the farmer
    cursor.execute("""SELECT lt.*, l.loan_type FROM loans_taken lt 
                      JOIN loans l ON lt.loan_type = l.loan_type 
                      WHERE lt.aadhar_id = %s""", (aadhar_id,))
    loans_taken = cursor.fetchall()

    cursor.close()
    return render_template('manage_loans_taken.html', farmer=farmer, active_loans=active_loans, loans_taken=loans_taken)

# Route to search loans taken by a farmer
@app.route('/search_loans_taken/<aadhar_id>', methods=['GET'])
def search_loans_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Search for loans taken
    search_loan_taken = request.args.get('search_loan_taken')  # Accessing search query from URL
    if search_loan_taken:
        cursor.execute("SELECT lt.*, l.loan_type FROM loans_taken lt "
                       "JOIN loans l ON lt.loan_type = l.loan_type "
                       "WHERE lt.aadhar_id = %s AND l.loan_type LIKE %s",
                       (aadhar_id, '%' + search_loan_taken + '%'))
    else:
        cursor.execute("""SELECT lt.*, l.loan_type FROM loans_taken lt 
                          JOIN loans l ON lt.loan_type = l.loan_type 
                          WHERE lt.aadhar_id = %s""", (aadhar_id,))

    loans_taken = cursor.fetchall()
    cursor.close()

    return render_template('manage_loans_taken.html', farmer=farmer, loans_taken=loans_taken)

# Route to add a loan taken by a farmer
@app.route('/add_loan_taken/<aadhar_id>', methods=['POST'])
def add_loan_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor()

    loan_type = request.form['loan_type']
    bank_name = request.form['bank_name']
    sanction_date = request.form['sanction_date']
    due_date = request.form['due_date']
    amount_taken = request.form['amount_taken']
    status = request.form['status']

    # Validate dates
    if datetime.strptime(due_date, "%Y-%m-%d") <= datetime.strptime(sanction_date, "%Y-%m-%d"):
        flash("Due date must be later than the sanction date.", 'error')
        return redirect(url_for('manage_loans_taken', aadhar_id=aadhar_id))

    # Check if the loan with the same loan_type and sanction_date already exists
    cursor.execute("""SELECT * FROM loans_taken 
                      WHERE loan_type = %s AND sanction_date = %s AND aadhar_id = %s""",
                   (loan_type, sanction_date, aadhar_id))
    existing_loan = cursor.fetchone()

    if existing_loan:
        flash("A loan with this type and sanction date already exists for this farmer.", 'error')
        return redirect(url_for('manage_loans_taken', aadhar_id=aadhar_id))

    # Insert loan taken
    try:
        cursor.execute("""INSERT INTO loans_taken (loan_type, aadhar_id, bank_name, sanction_date, due_date, amount_taken, status)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                       (loan_type, aadhar_id, bank_name, sanction_date, due_date, amount_taken, status))
        mysql.connection.commit()
        flash("Loan taken added successfully!", 'success')
    except MySQLdb.Error as err:
        mysql.connection.rollback()
        flash(f'Error storing data: {err}', 'error')
    
    cursor.close()
    return redirect(url_for('manage_loans_taken', aadhar_id=aadhar_id))

# Route to update loan taken status
@app.route('/update_loan_taken/<aadhar_id>/<loan_type>/<sanction_date>', methods=['POST'])
def update_loan_taken(aadhar_id, loan_type, sanction_date):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    new_status = request.form.get('status') 
    
    if new_status not in ['paid', 'unpaid']:  # Adjust this list as needed
        flash('Invalid status provided.', 'error')
        return redirect(url_for('manage_loans_taken', aadhar_id=aadhar_id))
    
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(""" 
            UPDATE loans_taken 
            SET status = %s 
            WHERE aadhar_id = %s AND loan_type = %s AND sanction_date = %s
        """, (new_status, aadhar_id, loan_type, sanction_date))
        mysql.connection.commit()
        flash("Loan status updated successfully!", 'success')
    except Exception as e:
        mysql.connection.rollback()  # Rollback in case of error
        flash(f'Error updating loan status: {e}', 'error')
    finally:
        cursor.close()
    
    return redirect(url_for('manage_loans_taken', aadhar_id=aadhar_id))

# Route to logically delete a loan taken
@app.route('/delete_loan_taken/<aadhar_id>/<loan_type>/<sanction_date>', methods=['POST'])
def delete_loan_taken(aadhar_id, loan_type, sanction_date):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(""" 
            DELETE FROM loans_taken 
            WHERE aadhar_id = %s AND loan_type = %s AND sanction_date = %s
        """, (aadhar_id, loan_type, sanction_date))
        mysql.connection.commit()
        flash("Loan taken deleted successfully!", 'success')
    except Exception as e:
        flash(f'Error deleting loan: {e}', 'error')
    finally:
        cursor.close()
    
    return redirect(url_for('manage_loans_taken', aadhar_id=aadhar_id))

@app.route('/manage_subsidies')
def manage_subsidies():
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM subsidies WHERE deleted = FALSE")
    subsidies = cur.fetchall()
    cur.close()
    return render_template('manage_subsidies.html', subsidies=subsidies)


@app.route('/search_subsidy', methods=['GET'])
def search_subsidy():
    subsidy_name = request.args.get('subsidy_name', '')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Query the database for subsidies matching the subsidy_type
    if subsidy_name:
        # Search for subsidies based on subsidy_type
        cursor.execute(
            "SELECT * FROM subsidies WHERE subsidy_name LIKE %s AND deleted = FALSE",
            ('%' + subsidy_name + '%',)  # Using LIKE for partial matching
        )
        subsidies = cursor.fetchall()

        if not subsidies:
            flash('No subsidies found for this type.', 'error')
    else:
        # If no search term is provided, retrieve all subsidies
        cursor.execute("SELECT * FROM subsidies WHERE deleted = FALSE")
        subsidies = cursor.fetchall()

    cursor.close()
    return render_template('manage_subsidies.html', subsidies=subsidies)


@app.route('/add_subsidy', methods=['GET', 'POST'])
def add_subsidy():
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    if request.method == 'POST':
        subsidy_name = request.form.get('subsidy_name')
        description = request.form.get('description')
        eligibility = request.form.get('eligibility')
        last_date_apply = request.form.get('last_date_apply')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("SELECT * FROM subsidies WHERE subsidy_name = %s AND deleted = FALSE", (subsidy_name,))
        existing_subsidy_type = cursor.fetchone()

        if existing_subsidy_type:
            flash('Subsidy name already exists', 'error')
            cursor.close()
            return redirect(url_for('manage_subsidies'))

        try:
            cursor.execute(
                """INSERT INTO subsidies (subsidy_name, description, eligibility, last_date_apply) 
                   VALUES (%s, %s, %s, %s)""",
                (subsidy_name, description, eligibility, last_date_apply)
            )
            mysql.connection.commit()
            flash('Subsidy added successfully!', 'success')
            return redirect(url_for('manage_subsidies'))
        except MySQLdb.Error as err:
            mysql.connection.rollback()
            flash(f'Error storing data: {err}', 'error')
        finally:
            cursor.close()

    return render_template('manage_subsidies.html', auth_name=session.get('auth_name'))


@app.route('/update_subsidy/<int:id>', methods=['POST'])
def update_subsidy(id):
    description = request.form.get('description')
    eligibility = request.form.get('eligibility')
    last_date_apply = request.form.get('last_date_apply')

    if not description or not eligibility or not last_date_apply:
        flash('All fields must be filled!', 'error')
        return redirect(url_for('manage_subsidies'))

    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("""
            UPDATE subsidies 
            SET description = %s, eligibility = %s, last_date_apply = %s 
            WHERE subsidy_id = %s
        """, (description, eligibility, last_date_apply, id))
        mysql.connection.commit()
        flash('Subsidy updated successfully!', 'success')
    except Exception as e:
        flash('Error updating subsidy: {}'.format(e), 'danger')
    finally:
        cur.close()

    return redirect(url_for('manage_subsidies'))


@app.route('/delete_subsidy/<int:subsidy_id>', methods=['POST'])
def delete_subsidy(subsidy_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Logically delete the subsidy by setting the deleted flag to TRUE
        cur.execute("UPDATE subsidies SET deleted = TRUE WHERE subsidy_id = %s", (subsidy_id,))
        mysql.connection.commit()
        flash('Subsidy deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting subsidy: {}'.format(e), 'danger')
    finally:
        cur.close()
    return redirect(url_for('manage_subsidies'))

# Route to view/manage subsidies taken by farmers
@app.route('/manage_subsidies_taken/<aadhar_id>', methods=['GET'])
def manage_subsidies_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Get active subsidies types
    cursor.execute("SELECT subsidy_name FROM subsidies WHERE deleted = FALSE")
    active_subsidies = cursor.fetchall()

    # Get subsidies taken by the farmer
    cursor.execute("""SELECT sut.*, su.subsidy_name FROM subsidies_taken sut 
                      JOIN subsidies su ON sut.subsidy_name = su.subsidy_name 
                      WHERE sut.aadhar_id = %s""", (aadhar_id,))
    subsidies_taken = cursor.fetchall()

    cursor.close()
    return render_template('manage_subsidies_taken.html', farmer=farmer, active_subsidies=active_subsidies, subsidies_taken=subsidies_taken)

# Route to search subsidies taken by a farmer
@app.route('/search_subsidies_taken/<aadhar_id>', methods=['GET'])
def search_subsidies_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Search for loans taken
    search_subsidy_taken = request.args.get('search_subsidy_taken')  # Accessing search query from URL
    if search_subsidy_taken:
        cursor.execute("""SELECT sut.*, su.subsidy_name FROM subsidies_taken sut 
                      JOIN subsidies su ON sut.subsidy_name = su.subsidy_name 
                      WHERE sut.aadhar_id = %s AND su.subsidy_name LIKE %s""", 
                      (aadhar_id, '%' + search_subsidy_taken + '%'))
    else:
        cursor.execute("""SELECT sut.*, su.subsidy_name FROM subsidies_taken sut 
                      JOIN subsidies su ON sut.subsidy_name = su.subsidy_name 
                      WHERE sut.aadhar_id = %s""", (aadhar_id,))

    subsidies_taken = cursor.fetchall()
    cursor.close()

    return render_template('manage_subsidies_taken.html', farmer=farmer, subsidies_taken=subsidies_taken)

# Route to add a subsidy taken by a farmer
@app.route('/add_subsidy_taken/<aadhar_id>', methods=['POST'])
def add_subsidy_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    subsidy_name = request.form['subsidy_name']
    sanction_date = request.form['sanction_date']

    # Check if the subsidy with the same subsidy_name and sanction_date already exists
    cursor.execute("""SELECT * FROM subsidies_taken 
                      WHERE subsidy_name = %s AND sanction_date = %s AND aadhar_id = %s""",
                   (subsidy_name, sanction_date, aadhar_id))
    existing_subsidy = cursor.fetchone()

    if existing_subsidy:
        flash("A subsidy with this name and sanction date already exists for this farmer.", 'error')
        return redirect(url_for('manage_subsidies_taken', aadhar_id=aadhar_id))
    
    # Retrieve last_date_apply and ensure it's a date object
    cursor.execute("SELECT last_date_apply FROM subsidies WHERE subsidy_name = %s", (subsidy_name,))
    last_date_apply = cursor.fetchone()

    if last_date_apply:
        last_date_apply = last_date_apply['last_date_apply']

        # Ensure both dates are datetime.date objects
        if isinstance(last_date_apply, str):
            last_date_apply = datetime.strptime(last_date_apply, "%Y-%m-%d").date()

        sanction_date_obj = datetime.strptime(sanction_date, "%Y-%m-%d").date()

        # Validate that the approval date is before the last date to apply
        if sanction_date_obj >= last_date_apply:
            flash("Sanction date must be before the last date to apply.", 'error')
            cursor.close()
            return redirect(url_for('manage_subsidies_taken', aadhar_id=aadhar_id))

    # Insert subsidy taken
    try:
        cursor.execute("""INSERT INTO subsidies_taken (subsidy_name, aadhar_id, sanction_date)
                          VALUES (%s, %s, %s)""",
                       (subsidy_name, aadhar_id, sanction_date))
        mysql.connection.commit()
        flash("Subsidy taken added successfully!", 'success')
    except MySQLdb.Error as err:
        mysql.connection.rollback()
        flash(f'Error storing data: {err}', 'error')
    
    cursor.close()
    return redirect(url_for('manage_subsidies_taken', aadhar_id=aadhar_id))

# Route to logically delete a subsidy taken
@app.route('/delete_subsidy_taken/<aadhar_id>/<subsidy_name>/<sanction_date>', methods=['POST'])
def delete_subsidy_taken(aadhar_id, subsidy_name, sanction_date):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(""" 
            DELETE FROM subsidies_taken 
            WHERE aadhar_id = %s AND subsidy_name = %s AND sanction_date = %s
        """, (aadhar_id, subsidy_name, sanction_date))
        mysql.connection.commit()
        flash("Subsidy taken deleted successfully!", 'success')
    except Exception as e:
        flash(f'Error deleting subsidy: {e}', 'error')
    finally:
        cursor.close()
    
    return redirect(url_for('manage_subsidies_taken', aadhar_id=aadhar_id))



@app.route('/manage_schemes')
def manage_schemes():
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))
    
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM schemes WHERE deleted = FALSE")
    schemes = cur.fetchall()
    cur.close()
    return render_template('manage_schemes.html', schemes=schemes)


@app.route('/search_scheme', methods=['GET'])
def search_scheme():
    scheme_name = request.args.get('scheme_name', '')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Query the database for schemes matching the scheme_name
    if scheme_name:
        # Search for schemes based on scheme_name
        cursor.execute(
            "SELECT * FROM schemes WHERE scheme_name LIKE %s AND deleted = FALSE",
            ('%' + scheme_name + '%',)  # Using LIKE for partial matching
        )
        schemes = cursor.fetchall()

        if not schemes:
            flash('No schemes found for this type.', 'error')
    else:
        # If no search term is provided, retrieve all schemes
        cursor.execute("SELECT * FROM schemes AND deleted = FALSE")
        schemes = cursor.fetchall()

    cursor.close()
    return render_template('manage_schemes.html', schemes=schemes)


@app.route('/add_scheme', methods=['GET', 'POST'])
def add_scheme():
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    if request.method == 'POST':
        scheme_name = request.form.get('scheme_name')
        description = request.form.get('description')
        eligibility = request.form.get('eligibility')
        last_date_apply = request.form.get('last_date_apply')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        cursor.execute("SELECT * FROM schemes WHERE scheme_name = %s AND deleted = FALSE", (scheme_name,))

        existing_scheme = cursor.fetchone()

        if existing_scheme:
            flash('Scheme name already exists', 'error')
            cursor.close()
            return redirect(url_for('manage_schemes'))

        try:
            cursor.execute(
                """INSERT INTO schemes (scheme_name, description, eligibility, last_date_apply) 
                   VALUES (%s, %s, %s, %s)""",
                (scheme_name, description, eligibility, last_date_apply)
            )
            mysql.connection.commit()
            flash('Scheme added successfully!', 'success')
            return redirect(url_for('manage_schemes'))
        except MySQLdb.Error as err:
            mysql.connection.rollback()
            flash(f'Error storing data: {err}', 'error')
        finally:
            cursor.close()

    return render_template('manage_schemes.html', auth_name=session.get('auth_name'))


@app.route('/update_scheme/<int:id>', methods=['POST'])
def update_scheme(id):
    description = request.form.get('description')
    eligibility = request.form.get('eligibility')
    last_date_apply = request.form.get('last_date_apply')

    if not description or not eligibility or not last_date_apply:
        flash('All fields must be filled!', 'error')
        return redirect(url_for('manage_schemes'))

    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(""" 
            UPDATE schemes 
            SET description = %s, eligibility = %s, last_date_apply = %s 
            WHERE scheme_id = %s
        """, (description, eligibility, last_date_apply, id))
        mysql.connection.commit()
        flash('Scheme updated successfully!', 'success')
    except Exception as e:
        flash('Error updating scheme: {}'.format(e), 'danger')
    finally:
        cur.close()

    return redirect(url_for('manage_schemes'))


@app.route('/delete_scheme/<int:scheme_id>', methods=['POST'])
def delete_scheme(scheme_id):
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Logically delete the scheme by setting the deleted flag to TRUE
        cur.execute("UPDATE schemes SET deleted = TRUE WHERE scheme_id = %s", (scheme_id,))
        mysql.connection.commit()
        flash('Scheme deleted successfully!', 'success')
    except Exception as e:
        flash('Error deleting scheme: {}'.format(e), 'danger')
    finally:
        cur.close()
    return redirect(url_for('manage_schemes'))

# Route to view/manage schemes taken by farmers
@app.route('/manage_schemes_taken/<aadhar_id>', methods=['GET'])
def manage_schemes_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Get active scheme types
    cursor.execute("SELECT scheme_name FROM schemes WHERE deleted = FALSE")
    active_schemes = cursor.fetchall()

    # Get schemes taken by the farmer
    cursor.execute("""SELECT sct.*, sc.scheme_name FROM schemes_taken sct 
                      JOIN schemes sc ON sct.scheme_name = sc.scheme_name 
                      WHERE sct.aadhar_id = %s""", (aadhar_id,))
    schemes_taken = cursor.fetchall()

    cursor.close()
    return render_template('manage_schemes_taken.html', farmer=farmer, active_schemes=active_schemes, schemes_taken=schemes_taken)

# Route to search schemes taken by a farmer
@app.route('/search_schemes_taken/<aadhar_id>', methods=['GET'])
def search_schemes_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if farmer exists by aadhar_id
    cursor.execute("SELECT * FROM farmers WHERE aadhar_id = %s", (aadhar_id,))
    farmer = cursor.fetchone()
    if not farmer:
        flash("Farmer not found.", 'error')
        return redirect(url_for('home'))

    # Search for schemes taken
    search_scheme_taken = request.args.get('search_scheme_taken')  # Accessing search query from URL
    if search_scheme_taken:
        cursor.execute("""SELECT sct.*, sc.scheme_name FROM schemes_taken sct 
                          JOIN schemes sc ON sct.scheme_name = sc.scheme_name 
                          WHERE sct.aadhar_id = %s AND sc.scheme_name LIKE %s""", 
                          (aadhar_id, '%' + search_scheme_taken + '%'))
    else:
        cursor.execute("""SELECT sct.*, sc.scheme_name FROM schemes_taken sct 
                          JOIN schemes sc ON sct.scheme_name = sc.scheme_name 
                          WHERE sct.aadhar_id = %s""", (aadhar_id,))

    schemes_taken = cursor.fetchall()  
    cursor.close()

    return render_template('manage_schemes_taken.html', farmer=farmer, schemes_taken=schemes_taken)


@app.route('/add_scheme_taken/<aadhar_id>', methods=['POST'])
def add_scheme_taken(aadhar_id):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    scheme_name = request.form['scheme_name']
    approval_date = request.form['approval_date']

    # Check if the scheme with the same scheme_name and approval_date already exists
    cursor.execute("""SELECT * FROM schemes_taken 
                      WHERE scheme_name = %s AND approval_date = %s AND aadhar_id = %s""",
                   (scheme_name, approval_date, aadhar_id))
    existing_scheme = cursor.fetchone()

    if existing_scheme:
        flash("A scheme with this name and approval date already exists for this farmer.", 'error')
        cursor.close()
        return redirect(url_for('manage_schemes_taken', aadhar_id=aadhar_id))
    
     # Retrieve last_date_apply and ensure it's a date object
    cursor.execute("SELECT last_date_apply FROM schemes WHERE scheme_name = %s", (scheme_name,))
    last_date_apply = cursor.fetchone()

    if last_date_apply:
        last_date_apply = last_date_apply['last_date_apply']

        # Ensure both dates are datetime.date objects
        if isinstance(last_date_apply, str):
            last_date_apply = datetime.strptime(last_date_apply, "%Y-%m-%d").date()

        approval_date_obj = datetime.strptime(approval_date, "%Y-%m-%d").date()

        # Validate that the approval date is before the last date to apply
        if approval_date_obj >= last_date_apply:
            flash("Approval date must be before the last date to apply.", 'error')
            cursor.close()
            return redirect(url_for('manage_schemes_taken', aadhar_id=aadhar_id))

    # Insert scheme taken
    try:
        cursor.execute("""INSERT INTO schemes_taken (scheme_name, aadhar_id, approval_date)
                          VALUES (%s, %s, %s)""",
                       (scheme_name, aadhar_id, approval_date))
        mysql.connection.commit()
        flash("Scheme taken added successfully!", 'success')
    except MySQLdb.Error as err:
        mysql.connection.rollback()
        flash(f'Error storing data: {err}', 'error')
    
    cursor.close()
    return redirect(url_for('manage_schemes_taken', aadhar_id=aadhar_id))


# Route to logically delete a scheme taken
@app.route('/delete_scheme_taken/<aadhar_id>/<scheme_name>/<approval_date>', methods=['POST'])
def delete_scheme_taken(aadhar_id, scheme_name, approval_date):
    if 'auth_email' not in session:
        flash('You need to log in to access this page.', 'error')
        return redirect(url_for('auth_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute(""" 
            DELETE FROM schemes_taken 
            WHERE aadhar_id = %s AND scheme_name = %s AND approval_date = %s
        """, (aadhar_id, scheme_name, approval_date))
        mysql.connection.commit()
        flash("Scheme taken deleted successfully!", 'success')
    except Exception as e:
        flash(f'Error deleting scheme: {e}', 'error')
    finally:
        cursor.close()
    
    return redirect(url_for('manage_schemes_taken', aadhar_id=aadhar_id))



if __name__ == '__main__':
    app.run(debug=True)
