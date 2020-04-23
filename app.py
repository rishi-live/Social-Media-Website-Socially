from flask import Flask, render_template, request, session, url_for
import os
import mysql.connector
import datetime
from werkzeug.utils import secure_filename

# allowed file type & uploaded file path

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = '/static/images'

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

conn = mysql.connector.connect(host="localhost", user="root", password="", database="UEMK")
mycursor = conn.cursor()
# app is object of flask.

app.secret_key = os.urandom(24)


# when user search for your website first execute this function.
@app.route('/')
def hello():
    return render_template("login.html")


# ===========================================================================================================
#  LOGIN  route
# ===========================================================================================================
@app.route('/login', methods=['POST'])
def login():
    mycursor.execute("""
    SELECT * FROM `users` WHERE `email` LIKE '{}' AND `password` LIKE '{}'
    """.format(request.form.get("email"), request.form.get("password")))

    info = mycursor.fetchall()

    if len(info) > 0:
        session['user_id'] = info[0][0]
        session['name'] = info[0][1]
        session['profile_pic'] = info[0][4]
        newsfeed_info = fetch_newsfeed()
        friends_status = fetch_status()
        return render_template("profile.html", newsfeed_info=newsfeed_info, friends_status=friends_status)
    else:
        message = "Incorrect email/password"
        return render_template("login.html", message=message)


# ===========================================================================================================
# REGISTER Route
# ===========================================================================================================
@app.route('/register')
def register_form():
    return render_template('register_form.html')


# ===========================================================================================================
# Register route
# ===========================================================================================================
@app.route('/doregister', methods=['POST'])
def register():
    mycursor.execute("""
    SELECT * FROM `users` WHERE `email` LIKE '{}'
    """.format(request.form.get('email')))

    info = mycursor.fetchall()

    if len(info) > 0:
        return render_template('register_form.html', message="Email already exists")
    else:
        mycursor.execute("""
        INSERT INTO `users` (`user_id`, `name`,`email`,`password`) 
        VALUES (NULL, '{}', '{}', '{}')
        """.format(request.form.get('name'), request.form.get('email'), request.form.get('password')))

        conn.commit()

        mycursor.execute("""
            SELECT * FROM `users` WHERE `email` LIKE '{}'
            """.format(request.form.get('email')))

        info = mycursor.fetchall()

        session['user_id'] = info[0][0]
        session['name'] = info[0][1]

        return render_template("profile.html")


# ===========================================================================================================
# My friend route
# ===========================================================================================================

@app.route('/my_friends')
def my_friends():
    mycursor.execute("""
    SELECT * FROM `frequest` f JOIN `users` u ON u.`user_id` = f.`sender_id` JOIN `users` u1 ON
     u1.`user_id` = f.`receiver_id` WHERE (f.`sender_id` LIKE '{}' OR f.`receiver_id` LIKE '{}') AND 
     f.`fstatus` LIKE '1'
    """.format(session['user_id'], session['user_id']))

    friends_info = mycursor.fetchall()

    return render_template('friends.html', friends_info = friends_info)

@app.route('/pending_request')
def pending_request():
    mycursor.execute("""
        SELECT * FROM `frequest` f JOIN `users` u ON u.`user_id` = f.`sender_id` WHERE f.`receiver_id` LIKE '{}' AND 
         f.`fstatus` LIKE '0'
        """.format(session['user_id']))

    pending_info = mycursor.fetchall()
    print("Testing 5")
    print(pending_info)


    return render_template('pending_request.html',pending_info=pending_info)

@app.route('/cancel_request/<string:id>')
def cancel_request(id):
    mycursor.execute("""
    DELETE FROM `frequest` WHERE `sender_id` LIKE '{}' AND `receiver_id` LIKE '{}'
    """.format(id,session['user_id']))

    conn.commit()
    mycursor.execute("""
        SELECT * FROM `users` WHERE `user_id` LIKE '{}'
        """.format(id))

    user_info = mycursor.fetchall()

    print(id)

    return render_template('view_profile.html',message="Friend request canceled",user_info=user_info, flag=0, status=0, flagOne = False)

@app.route('/accept_request/<string:id>')
def accept_request(id):
    mycursor.execute("""
    UPDATE `frequest` SET `fstatus` = '1' WHERE `sender_id` LIKE '{}' AND `receiver_id` LIKE '{}'
    """.format(id,session['user_id']))

    conn.commit()

    mycursor.execute("""
           SELECT * FROM `frequest` f JOIN `users` u ON u.`user_id` = f.`sender_id` WHERE f.`receiver_id` LIKE '{}' AND 
            f.`fstatus` LIKE '0'
           """.format(session['user_id']))

    pending_info = mycursor.fetchall()


    return render_template('pending_request.html',pending_info = pending_info)

# ===========================================================================================================
# Logout route
# ===========================================================================================================

@app.route('/logout')
def logout():
    # update status = 0
    # toggle_status('0')
    session.pop('user_id')
    session.pop('name')
    return render_template('login.html', message="logged out successfully")


# ===========================================================================================================
# search route
# ===========================================================================================================

@app.route('/search', methods=['POST'])
def search():
    mycursor.execute("""SELECT * FROM `users` WHERE `name` LIKE '{}'
    """.format(request.form.get('search_term')))

    search_result = mycursor.fetchall()
    return render_template('search.html', search_result=search_result)


# ===========================================================================================================
# profile viewing html
# ===========================================================================================================
@app.route('/view/<string:id>', methods=['GET'])
def view(id):
    mycursor.execute("""
    SELECT * FROM `users` WHERE `user_id` LIKE '{}'
    """.format(id))

    print("Testing 2")
    print(id)
    print(session['user_id'])

    user_info = mycursor.fetchall()

    mycursor.execute("""
    SELECT * FROM `frequest` WHERE `sender_id` LIKE '{}' AND `receiver_id` LIKE '{}' OR 
    `receiver_id` LIKE '{}' AND `sender_id` LIKE '{}'
    """.format(session['user_id'], id, session['user_id'], id))



    fr_status = mycursor.fetchall()

    print("Testing")
    print(fr_status)

    if len(fr_status) > 0:
        flag = 1
        status = fr_status[0][3]
    else:
        flag = 0
        status = 0
    return render_template('view_profile.html', user_info=user_info, flag=flag, status=status, flagOne = False)

# ===========================================================================================================
# send message route
# ===========================================================================================================
@app.route('/send_message', methods=['POST'])
def send_message():
    dt = datetime.datetime.now()
    mycursor.execute("""
    INSERT INTO `message` (`msg_id`, `sender_id`, `receiver_id`, `message_text`, `timestamp`)
    VALUES (NULL ,'{}','{}','{}','{}')
    """.format(session['user_id'], request.form.get('receiver_id'), request.form.get('message'), dt))
    conn.commit()

    mycursor.execute("""
        SELECT * FROM `users` WHERE `user_id` LIKE '{}'
        """.format(request.form.get('receiver_id')))

    user_info = mycursor.fetchall()
    conn.commit()

    return render_template('view_profile.html', message="Message send successfully", user_info=user_info)


# ===========================================================================================================
# login user message
# ===========================================================================================================

@app.route('/my_messages')
def my_messages():
    a = []
    message2 = []
    if session['user_id']:
        mycursor.execute("""
        SELECT * FROM `message` m JOIN `users` u ON u.`user_id`=m.`sender_id` JOIN `users` u1 ON
         u1.`user_id` =m.`receiver_id` WHERE `sender_id` LIKE '{}' OR `receiver_id` LIKE '{}'
        """.format(session['user_id'], session['user_id']))

        messages = mycursor.fetchall()
        for i in messages:
            b = str(i[1]) + str(i[2])
            bRev = str(i[2]) + str(i[1])
            if b not in a:
                a.append(b)
                a.append(bRev)
                message2.append(i)

        return render_template('view_messages.html', messages=message2, mydict={})
    else:
        return render_template('login.html')


# ===========================================================================================================
# friend request send route
# ===========================================================================================================

@app.route('/send_request/<string:id>', methods=['GET'])
def send_request(id):
    mycursor.execute("""
    INSERT INTO `frequest`  (`fr_id`, `sender_id`, `receiver_id`, `fstatus`)
    VALUES (NULL ,'{}','{}','{}')
    """.format(session['user_id'], id, 0))

    conn.commit()
    mycursor.execute("""
            SELECT * FROM `users` WHERE `user_id` LIKE '{}'
            """.format(id))
    #conn.commit()
    user_info = mycursor.fetchall()
    flag = True
    return render_template('view_profile.html', message="Friend request send successfully", user_info=user_info, flagOne = flag )

# ===========================================================================================================
# upload file route
# ===========================================================================================================
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_newsfeed', methods=['POST'])
def upload_newsfeed():

    if 'feed_image' not in request.files:
        return "No file found"
    file = request.files['feed_image']
    if file.filename == '':
        return "Error"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save('./static/images' + '/' + filename)
        print("FileName")
        print(type(filename))
    dt = datetime.datetime.now()
    print(type(dt))
    print(request.form.get('feed_text'))
    mycursor.execute("""
    INSERT INTO `newsfeed` (`nfid`, `user_id`, `date`, `text`, `image`) VALUES 
    (NULL, '{}', '{}', '{}','{}')
    """.format(session['user_id'],dt, request.form.get('feed_text'), str(filename)))
    conn.commit()

    newsfeed_info = fetch_newsfeed()
    friends_status = fetch_status()
    return render_template("profile.html", newsfeed_info=newsfeed_info,friends_status=friends_status)

@app.route('/home')
def home():


    newsfeed_info = fetch_newsfeed()
    friends_status = fetch_status()
    return render_template("profile.html", newsfeed_info=newsfeed_info, friends_status=friends_status)

# ==========================================================================================================
# method of newsfeed
# ===========================================================================================================


def fetch_newsfeed():
    mycursor.execute("""
    SELECT * FROM `newsfeed` n JOIN `users` u ON u.`user_id`=n.`user_id`
    """)
    # reverse order news feed
    newsfeed_info = mycursor.fetchall()
    return newsfeed_info


# ===========================================================================================================
# friend status method
# ===========================================================================================================
def fetch_status():
    mycursor.execute("""
    SELECT * FROM `users` WHERE `user_id` NOT LIKE '{}'
    """.format(session['user_id']))

    friends_status = mycursor.fetchall()
    return friends_status


def profile_pic():
    mycursor.execute("""
            SELECT * FROM `message` m JOIN `users` u ON u.`user_id`=m.`sender_id`
            """)

    pic = mycursor.fetchall()

    return pic


app.run(debug=True, port=8000)
