from flask import Flask, redirect, url_for, request, render_template, session, flash
from datetime import timedelta
from flask_mysqldb import MySQL
import yaml
import hashlib
import os
import neccessary_functions as nf


app = Flask(__name__)
app.secret_key = "6b8aff760b701265494ae0d98a5058fa"
app.permanent_session_lifetime = timedelta(hours = 6)

db = yaml.safe_load(open("db.yaml"))

app.config["MYSQL_HOST"] = db['mysql_host']
app.config["MYSQL_USER"] = db['mysql_user']
app.config["MYSQL_PASSWORD"] = db['mysql_password']
app.config["MYSQL_DB"] = db['mysql_db']
app.config["FILE_UPLOADS"] = db["file_uploads"]
app.config["ALLOWED_FILE_EXTENSIONS"] = ["PDF"]

mysql = MySQL(app)

@app.route("/")
@app.route("/home")
def home():
    if "user's email" in session:
        login_status = True
    else:
        login_status = False
    return render_template("home.html", login_status=login_status)

@app.route("/login", methods=["GET", "POST"])
def login(): # '%Y-%m-%d %H:%M:%S'
    if request.method == "POST":
        session.permanent = True
        if request.form["email"] == "" or request.form["password"] == "":
            flash("required fields are not filled", category = "danger")
            return redirect(url_for("login"))
        else:
            usr_email = request.form["email"]
            usr_password = hashlib.md5(request.form["password"].encode()).hexdigest()
            cur = mysql.connection.cursor()
            row = cur.execute(f"SELECT * FROM users WHERE user_email='{usr_email}' AND user_password='{usr_password}' LIMIT 1")
            if row > 0:
                found_user = cur.fetchall()
                session["user's id"] = found_user[0][0]
                session["user's name"] = found_user[0][1]
                session["user's email"] = usr_email
                flash("Logged In Successfully!", category = "success")
                cur.execute("SELECT my_reads_list FROM my_reads WHERE user_id={}".format(session["user's id"]))
                my_reads_list = cur.fetchall()
                my_reads_list = str(my_reads_list[0][0])
                with open("testing.txt", "w") as f:
                    f.write(my_reads_list+"\n")
                my_reads_list = eval(my_reads_list)
                i = 0
                while i < len(my_reads_list):
                    found_book = cur.execute("SELECT * FROM books WHERE book_id={}".format(my_reads_list[i][0]))
                    if not found_book:
                        flash("One of your book is removed from My Reads because the admin deleted the book from the database", category="info")
                        my_reads_list.pop(i)
                    i+=1
                my_reads_list = str(my_reads_list)
                cur.execute(''' UPDATE my_reads SET my_reads_list="{}" WHERE user_id={} '''.format(my_reads_list, session["user's id"]))
                mysql.connection.commit()
                with open("testing.txt", "w") as f:
                    f.write(str(my_reads_list))
                cur.close()
                return redirect(url_for("my_account"))
            else: # User not found
                found_user = cur.execute(f"SELECT * FROM users WHERE user_email='{usr_email}' LIMIT 1")
                cur.close()
                if found_user:
                    flash("Entered The Wrong Password!, Please try again", category = "danger")
                    return render_template("login.html", usr_email = usr_email)
                else:
                    flash("User with this email has not yet registered, Register Now!", category="warning")
                    return redirect(url_for("register"))
    else: # GET request
        if "user's email" in session:
            flash("User already Logged In", category = "warning")
            return redirect(url_for("my_account"))
        else:
            return render_template("login.html")


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        session.permanent = True
        if request.form["email"] == "" or request.form["password"] == "":
            flash("required fields are not filled", category = "danger")
            return redirect(url_for("admin_login"))
        else:
            admin_email = request.form["email"]
            admin_password = hashlib.md5(request.form["password"].encode()).hexdigest()
            cur = mysql.connection.cursor()
            row = cur.execute(f"SELECT * FROM admins WHERE admin_email='{admin_email}' AND admin_password='{admin_password}' LIMIT 1")
            if row > 0:
                found_user = cur.fetchall()
                session["user's id"] = found_user[0][0]
                session["user's name"] = found_user[0][1]
                session["user's email"] = admin_email
                session["user is admin"] = None
                flash("Logged In Successfully!", category = "success")
                cur.close()
                return redirect(url_for("my_account"))
            else: # User not found
                found_user = cur.execute(f"SELECT * FROM admins WHERE admin_email='{admin_email}' LIMIT 1")
                cur.close()
                if found_user:
                    flash("Entered The Wrong Password!, Please try again", category = "danger")
                    return render_template("admin_login.html", admin_email = admin_email)
                else:
                    flash("You are not an admin", category="warning")
                    return redirect(url_for("register"))
    else: # GET request
        if "user's email" in session:
            flash("User already Logged In", category = "warning")
            return redirect(url_for("dashboard"))
        else:
            return render_template("admin_login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        
        if request.form["name"] == "" or request.form["email"] == "" or request.form["password"] == "":
            flash("required fields are not filled", category = "danger")
            return redirect(url_for("register"))
        else:
            usr_name = request.form["name"]
            usr_email = request.form["email"]
            usr_password = request.form["password"]
            usr_confirm_password = request.form["password_confirmation"]
            if usr_password == usr_confirm_password:
                #Check if the user has already registered
                cur = mysql.connection.cursor()
                no_of_rows = cur.execute(f"SELECT * FROM users WHERE user_email='{usr_email}' LIMIT 1") # cur.execute("SELECT * FROM users") returns the no.of rows
                if no_of_rows > 0:
                    flash("User with this email address already exists, Please Log in!", category="info")
                    cur.close()
                    return redirect(url_for("login"))
                else: #register the new user
                    usr_password = hashlib.md5(usr_password.encode()).hexdigest()
                    cur.execute(f"INSERT INTO users(user_name, user_email, user_password) VALUES('{usr_name}', '{usr_email}', '{usr_password}')")
                    mysql.connection.commit()
                    cur.execute(f"SELECT user_id FROM users WHERE user_email = '{usr_email}' LIMIT 1")
                    found_user = cur.fetchall()
                    cur.execute("INSERT INTO my_reads(user_id) VALUES({})".format(found_user[0][0])) ###
                    mysql.connection.commit()
                    cur.close()
                    flash("You have been Successfully Registered!", category="success")
                    return redirect(url_for("login"))
            else:
                flash("Both the passwords don't match, Please try again", category = "danger")
                return render_template("register.html", usr_name = usr_name, usr_email = usr_email)
    
    else: # "GET" request
        if "user's email" in session:
            flash("Please logout to go to the register page", category="warning")
            return redirect(url_for("my_account"))
        else:
            return render_template("register.html")

def allowed_filetype(filename):
    if not "." in filename:
        return False
    else:
        extension = filename.rsplit(".", 1)[1]
        if extension.upper() in app.config["ALLOWED_FILE_EXTENSIONS"]:
            return True
        else:
            return False

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard(): # Through dashboard admin can upload books into the database.
    if request.method == "POST":
        if request.files:
            file = request.files["file"]

            if file.filename == "":
                flash("selected file must have a name", category="danger")
                return redirect(url_for('dashboard'))
            elif request.form["book_author"] == "" or request.form["book_searchstring"] == "" or  not bool(request.form["book_cost"]):
                flash("required fields not filled", category="danger")
                return redirect(url_for('dashboard'))
            elif not allowed_filetype(file.filename):
                flash("The Selected file type is not allowed")
                return redirect(url_for('dashboard'))
            elif not request.form["book_name"]:
                flash("The Selected file type is not allowed")
                return redirect(url_for('dashboard'))
            else:
                cur = mysql.connection.cursor()
                if cur.execute(f"""SELECT * FROM books WHERE book_name= "{request.form['book_name']}" """):
                    flash("Book with that name is already present in the database, try another name", category="danger")
                    return redirect(url_for('dashboard')) 
                # Now to save the file in the database
                cur.execute("INSERT INTO books(book_name, upload_admin_id, upload_timestamp, book_author, book_searchstring, book_cost) VALUES('{}', {}, '{}', '{}', '{}', {})".format(request.form["book_name"], session["user's id"], nf.get_current_time(), request.form["book_author"], request.form["book_searchstring"], request.form["book_cost"]))
                cur.close()
                mysql.connection.commit()
                file.save(os.path.join(app.config["FILE_UPLOADS"], request.form["book_name"]+".pdf"))
                print("file saved in the file server")
                flash(f"{request.form['book_name']} inserted into the database successfully!", category="success")
                return redirect(url_for('dashboard'))
    else:
        if "user is admin" in session:
            return render_template("dashboard.html", login_status=True)
        else:
            return redirect(url_for('login'))


@app.route("/my_account", methods=["GET"])
def my_account():
    if "user's email" in session:
        if "user is admin" in session: #admin user
            return render_template("my_account.html", admin_user = True, login_status = True, user_name = session["user's name"])
        else: # regular user
            return render_template("my_account.html", admin_user = False, login_status = True, user_name = session["user's name"])
    else:
        return redirect(url_for('login'))

@app.route("/omni_library", methods=["GET", "POST"])
def omni_library():
    if request.method == "POST":
        if request.form["search_query"]=="":
            flash("Your query was empty pls try searching again", category="info")
            return redirect(url_for('omni_library'))
        else:
            search_query = request.form["search_query"].lower()
            cur = mysql.connection.cursor()
            all_books = cur.execute("SELECT book_id, book_name, book_author, book_searchstring, book_cost FROM books")
            if all_books:
                found_books = cur.fetchall()
            else:
                found_books = None
            if not found_books:
                flash("No books in the library", category="warning")
                return redirect(url_for('omni_library'))
            else:
                # with open("testing.txt", "w") as f:
                #     f.write(str(all_books) + "\n")
                i=0
                count=0
                book_list = []
                while (i < all_books):
                    combined_search_string = (found_books[i][1] + "," + found_books[i][2] + "," + found_books[i][3] + "all").lower()
                    if search_query in combined_search_string:
                        # with open("testing.txt", "a") as f:
                        #     f.write(str(found_books[i][0]))
                        book_list.append( (found_books[i][0], found_books[i][1].replace(".pdf", ""), found_books[i][2], found_books[i][4]) ) # appending the names, authors of books.
                        count+=1
                    i+=1
                if not count>0:
                    flash("No books found", category="danger")
                if "user's email" in session:
                    login_status = True
                else:
                    login_status = False
                if "user is admin" in session:
                    admin_login_status = True
                else:
                    admin_login_status = False
                return render_template("omni_library.html", login_status=login_status, book_list=book_list, admin_login_status=admin_login_status)
    else:
        if "user's email" in session:
            login_status = True
        else:
            login_status = False
        return render_template("omni_library.html", login_status=login_status)

@app.route("/logout", methods=["GET"])
def logout():
    if "user's email" in session:
        session.pop("user's name", None)
        session.pop("user's email", None)
        session.pop("user's id", None)
        if "user is admin" in session:
            session.pop("user is admin", None)
        flash("You have been Logged Out Successfully!", category="success")
        return redirect(url_for("login"))
    else:
        flash("No User Logged In", category = "info")
        return redirect(url_for("login"))

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        if request.form["password"]=="" or request.form["new_password"]=="" or request.form["confirm_password"]=="":
            flash("required fields are not filled", category = "danger")
            return redirect(url_for("change_password"))
        elif request.form["new_password"] != request.form["confirm_password"]:
            flash("Both the passwords don't match, Please try again", category = "danger")
            return redirect(url_for('change_password'))
        else:
            password = hashlib.md5(request.form["password"].encode()).hexdigest()
            email = session["user's email"]
            cur = mysql.connection.cursor()
            new_password = hashlib.md5(request.form["new_password"].encode()).hexdigest()
            if "user is admin" in session:
                found_user = cur.execute("SELECT * FROM admins WHERE admin_email = '{}' AND admin_password = '{}' LIMIT 1".format(email, password))
                if found_user:
                    cur.execute("UPDATE admins SET admin_password = '{}' WHERE admin_email='{}'".format(new_password, email))
                    mysql.connection.commit()
                    flash("Updated password successfully!", category="success")
                    return redirect(url_for('my_account'))
                else:
                    flash("Entered The Wrong Password!, Please try again", category = "danger")
                    return redirect(url_for('change_password'))
            else:
                found_user = cur.execute("SELECT * FROM users WHERE user_email = '{}' AND user_password = '{}' LIMIT 1".format(email, password))
                if found_user:
                    cur.execute("UPDATE users SET user_password = '{}' WHERE user_email='{}'".format(new_password, email))
                    mysql.connection.commit()
                    flash("Updated password successfully!", category="success")
                    return redirect(url_for('my_account'))
                else:
                    flash("Entered The Wrong Password!, Please try again", category = "danger")
                    return redirect(url_for('change_password'))
    else:
        if "user's email" in session:
            login_status = True
        else:
            login_status = False
        return render_template("change_password.html", login_status=login_status)

@app.route("/delete_account", methods=["GET"])
def delete_account():
    if "user's email" in session:
        cur = mysql.connection.cursor()
        var = session["user's email"]
        if "user is admin" in session:
            cur.execute("DELETE FROM admins WHERE admin_email='{}'".format(session["user's email"]))
        else:
            cur.execute("DELETE FROM users WHERE user_email='{}'".format(session["user's email"]))
        mysql.connection.commit()
        cur.close()
        session.pop("user's id", None)
        session.pop("user's name", None)
        session.pop("user's email", None)
        if "user is admin" in session:
            session.pop("user is admin", None)
        flash("Account deleted successfully!", category = "success")
        return redirect(url_for("login"))
    else:
        flash("No User Logged In", category = "info")
        return redirect(url_for("login"))

@app.route("/rent_book", methods=["GET", "POST"])
def rent_book(): # payment gateway goes into this function.
    if request.method == "POST":
        if "user's email" not in session:
            flash("Your have to Log in to rent a book", category="warning")
            return redirect(url_for('login'))
        else:
            book_id = request.form["book_id"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT book_name, book_author, book_cost FROM books WHERE book_id = {}".format(book_id))
            book_info = cur.fetchall()
            cur.execute("SELECT * FROM my_reads WHERE user_id={} LIMIT 1".format(session["user's id"]))
            my_reads_obj = cur.fetchall()
            with open("testing.txt", "w") as f:
                f.write(str(my_reads_obj))
            string1 = my_reads_obj[0][1]
            list1 = eval(string1)
            if len(list1) >= 5:
                flash("Capacity is full more books cannot be added into your my_reads", category="danger")
                flash("try clearing some books to add more", category="danger")
                return redirect(url_for('my_account'))
            else:
                count=0
                i=0
                while i < len(list1):
                    if list1[i][0] == int(book_id):
                        count+=1
                    i+=1
                if count>0: #book is already present
                    flash("The book is already in your my_reads", category="warning")
                    return redirect(url_for('my_account'))
                else:
                    if len(list1) > 2:
                        flash("The books in your my_reads exceed more than 3", category="warning")
                        list1.append( (int(book_id), nf.get_current_time()) )
                    else:
                        list1.append( (int(book_id), nf.get_current_time()) )
            cur.execute(""" UPDATE my_reads SET my_reads_list="{}" WHERE user_id={} """.format(str(list1), session["user's id"]))
            mysql.connection.commit()
            cur.close()
            if book_info[0][2] == 0:
                return redirect(url_for("my_reads"))
            else:
                return redirect("https://buy.stripe.com/fZe4hM92LbC52ti144", code=302)
    else:
        return redirect(url_for('login'))


@app.route("/remove_book_library", methods=["GET", "POST"])
def remove_book_library():
    if request.method == "POST":
        cur = mysql.connection.cursor()
        with open('testing.txt', "w") as f:
            f.write("hello")
        found_book = cur.execute(f"SELECT * FROM books WHERE book_id={request.form['book_id']}")
        if found_book:
            book_info = cur.fetchall()
            # with open('testing.txt', "w") as f:
            #     f.write(str(book_info))
            book_id = request.form['book_id']
            book_name = str(book_info[0][1])
            cur.execute(f"DELETE FROM books WHERE book_id={request.form['book_id']}")
            mysql.connection.commit()
            os.remove(app.config["FILE_UPLOADS"]+"/"+book_name+".pdf")
            flash("Book removed from the database successfully!", category="success")
            return redirect(url_for('omni_library'))
        else:
            flash("Book not found, no book deleted", category="danger")
            return redirect(url_for('omni_library'))
    else:
        return redirect(url_for('omni_library'))


@app.route("/remove_book_my_reads", methods=["GET", "POST"])
def remove_book_my_reads():
    if "user's email" in session:
        if request.method == "POST":
            cur = mysql.connection.cursor()
            found_user = cur.execute("SELECT * FROM my_reads WHERE user_id = {} LIMIT 1".format(session["user's id"]))
            if found_user:
                user_info = cur.fetchall()
                with open("testing.txt", "w") as f:
                    f.write(str(user_info))
                # print(user_info)
                my_reads_string = user_info[0][1]
                my_reads_list = eval(my_reads_string)
                book_id = request.form["book_id"]
                print(my_reads_list)
                with open("testing.txt", "a") as f:
                    f.write(str(my_reads_list))
                i=0
                count = 0
                while i < len(my_reads_list):
                    if int(book_id) == my_reads_list[i][0]:
                        my_reads_list.pop(i)
                        cur.execute(''' UPDATE my_reads SET my_reads_list= "{}" WHERE user_id={} '''.format(str(my_reads_list), session["user's id"]))
                        mysql.connection.commit()
                        count+=1
                    i+=1
                if count>0:
                    flash("The book is removed from your My Reads successfully!", category="success")
                else:
                    flash("Book not found in My Reads!", category="danger")
                return redirect(url_for('my_reads'))
            return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    else:
        flash("Login into your account first", category="warning")
        return redirect(url_for("login"))

@app.route("/my_reads", methods=["GET"])
def my_reads():
    if "user's email" in session:
        if "user is admin" in session:
            return redirect(url_for('dashboard'))
        else:
            user_id = session["user's id"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT my_reads_list FROM my_reads WHERE user_id={} LIMIT 1".format(user_id))
            my_reads_obj = cur.fetchall()
            # print(type(my_reads_obj))
            # my_reads_list = eval(my_reads_list)
            book_id_list = []
            with open("testing.txt", "w") as f:
                f.write(str(my_reads_obj))
            book_info_list=[]
            if len(my_reads_obj) == 0:
                zero_length = True
            else:
                zero_length = False
                my_reads_string = my_reads_obj[0][0]
                my_reads_list = eval(my_reads_string)
                # with open("testing.txt", "w") as f:
                #     f.write(str(my_reads_list))
                i=0
                while i<len(my_reads_list):
                    book_id_list.append( my_reads_list[i][0] )
                    i+=1
                # with open("testing.txt", "w") as f:
                #   f.write(str(book_id_list))
                i=0
                while i<len(book_id_list):
                    cur.execute("SELECT book_id, book_name, book_author FROM books WHERE book_id={} LIMIT 1".format( book_id_list[i] ) )
                    book_info_list.append(cur.fetchall())
                    i+=1
                # print(book_info_list)
            return render_template("my_reads.html", book_info_list=book_info_list, login_status=True, zero_length=zero_length)

    else:
        flash("First log into your account to access your my_reads page", category="warning")
        return redirect(url_for('login'))

@app.route('/view_book', methods=['GET', 'POST'])
def view_book():
    if request.method == "POST":
        book_id = request.form["book_id"]
        cur = mysql.connection.cursor()
        cur.execute(f"SELECT book_name FROM books WHERE book_id={book_id} LIMIT 1;")
        book_name = cur.fetchall()
        with open("testing.txt", "w") as f:
            f.write(str(book_name))
        book_name = str(book_name[0][0])
        with open("testing.txt", "w") as f:
            f.write(str(book_name))
        # print("..static/file_upload_folder/"+book_name)
        return render_template("view_book.html", login_status=True, book_path="file_upload_folder/"+book_name+".pdf")
    else:
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug = True) # "debug = True" helps make simultaneous changes in the website without restarting the server.