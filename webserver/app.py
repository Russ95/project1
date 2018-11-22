from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, make_response, url_for
import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import flask_login
import logging
from flask_login import LoginManager
import flask_logger

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DB_USER = "tm2977"
DB_PASSWORD = "574u6jh2"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

engine = create_engine(DATABASEURI)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'please login!'
login_manager.session_protection = 'strong'
logger = logging.getLogger(__name__)



# Here we create a test table and insert some values in it
# engine.execute("""DROP TABLE IF EXISTS test;""")
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
class User(flask_login.UserMixin):
    pass
    # def __init__(self, id, active=True):
    #     self.id = id
    #     self.active = active

@login_manager.user_loader
def load_user(user_id):
    cursor = g.conn.execute("SELECT user_name FROM User_")
    uids = []
    for result in cursor:
        uids.append(result['user_name'])
    if user_id not in uids:
        return
    user = User()
    user.id = user_id
    return user

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/', methods=['GET', 'POST'])
@flask_login.login_required
def home():
    # if session.get('UName'):

    cursor = g.conn.execute("SELECT eid, event_name, likes, event_date, tag FROM Event")
    names = []
    likes = []
    event_dates = []
    tags = []
    ids = []
    for result in cursor:
        names.append(result['event_name'])  # can also be accessed using result[0]
        likes.append(result['likes'])
        event_dates.append(result['event_date'])
        tags.append(result['tag'])
        ids.append(result['eid'])
    cursor.close()

    cursor = g.conn.execute("SELECT count(*) FROM Event")
    a = cursor.fetchone()
    count = a[0]

    count_dic = dict(count = count)
    names_dic = dict(names = names)
    user_id_dic = dict(n = flask_login.current_user.id)
    likes_dic = dict(likes=likes)
    event_dates_dic = dict(event_dates=event_dates)
    tags_dic = dict(tags=tags)
    ids_dic = dict(ids=ids)
    return render_template('home.html', **ids_dic, **names_dic, **user_id_dic, **likes_dic, **event_dates_dic, **tags_dic, **count_dic)
    # return render_template('home.html', **datas_dic)
    # else:
    #     return login()
    # if not session.get('logged_in'):
    #     return render_template('login.html')
    # else:
    #     return "Hello Boss!"


# @app.route('/login')
# def login():
#     return render_template('login.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
        if request.method == 'POST':
            logger.debug("login post method")
            t = {"username": request.form['username'], "password" : request.form['password']}


            cursor = g.conn.execute(text(
                """
                    select count(*)
                    from User_
                    where user_name = :username and password = :password
                """
            ),t)
            a = cursor.fetchone()
            if a[0]:
                user = User()
                user.id = request.form["username"]
                flask_login.login_user(user)
                # resp = make_response(render_template('index.html', name=request.form["username"]))
                # resp.set_cookie('username', request.form["username"])
                session['UName'] = request.form['username']
                session['password'] = request.form['password']
                return home()
            else:
                return render_template('login.html')

        return render_template('login.html')


    # else:
    #     print("No")

    # if request.form['password'] == 'password' and request.form['username'] == 'admin':
    #     session['logged_in'] = True
    # else:
    #     flash('wrong password!')

@app.route('/logout')
@flask_login.login_required
def logout():
    logger.debug("logout page")
    flask_login.logout_user()
    return render_template('login.html')


@app.route('/register',methods=['GET'])
def do_register():
    return render_template('register.html')

@app.route('/post',methods=['GET'])
@flask_login.login_required
def post():
    user_id_dic = dict(n = flask_login.current_user.id)
    return render_template('post.html',**user_id_dic)

@app.route('/do_post',methods=['GET', 'POST'])
@flask_login.login_required
def do_post():
    t1 = {"event_name": request.form['eventname'],"event_date" : request.form['eventdate'], "description" : request.form['description'], "tag": request.form['tag']}
    cursor = g.conn.execute(text(
        """
            insert into  Event(event_name, event_date, description,tag)
            values
            (:event_name, :event_date, :description, :tag)
        """
    ),t1)

    cursor = g.conn.execute(
    """
    select max(eid) from Event
    
    """)


    event = cursor.fetchone()
    eid = event[0]

    t2 = {"eid": eid, "location": request.form['location']}
    g.conn.execute(text(
        """
            insert into  Take_Places(eid, address)
            values
            (:eid, :location)
        """
    ),t2)
    return home()

@app.route('/profile', methods=['GET','POST'])
@flask_login.login_required
def profile():
    # if session.get('UName'):
    # uid = flask_login.current_user.id
    # cursor = g.conn.execute("SELECT user_name,birthday,likes FROM User_ where user_name="+uid)
    t = {"U_Name": flask_login.current_user.id}
    cursor = g.conn.execute(text(
        """
            select user_name,birthday,likes FROM User_
            where user_name= :U_Name
        """
    ),t)
    user_name = []
    birthday = []
    likes = []
    for result in cursor:
        # user_name.append(result['user_name'])  # can also be accessed using result[0]
        # birthday.append(result['birthday'])   
        # likes.append(result['likes'])
        user_name=result['user_name']  # can also be accessed using result[0]
        birthday=result['birthday']   
        likes=result['likes']
    cursor.close()
    user_id_dic = dict(n = flask_login.current_user.id)
    user_name_dic = dict(n1 = user_name)
    birthday_dic=dict(n2=birthday)
    likes_dic = dict(n3=likes)
    return render_template('profile.html', **user_id_dic,**user_name_dic, **birthday_dic,**likes_dic)


@app.route('/friends', methods=['GET','POST'])
@flask_login.login_required
def friends():
    t = {"U_Name2": flask_login.current_user.id}
    cursor = g.conn.execute(
        """
            select uid,user_name,likes
            from User_
            where uid in (
            select fid 
            from Friends_Relation
            where uid in (select uid
            from User_
            where user_name=%s))
        """,flask_login.current_user.id)

    # cursor = g.conn.execute(text(
    #     """
    #        select uid
    #         from User_
    #         where user_name= :U_Name
    #     """
    # ),t)

    
    tmpuid = []
    tmpusername = []
    tmplikes=[]
    for result in cursor:
        tmpuid.append(result['uid'])  # can also be accessed using result[0]
        tmpusername.append(result['user_name'])   
        tmplikes.append(result['likes'])

    cursor.close()

    cursor = g.conn.execute("SELECT count(*) FROM (select fid from Friends_Relation where uid in (select uid from User_ where user_name=%s)) as foo",flask_login.current_user.id)
    a = cursor.fetchone()
    count = a[0]
    user_id_dic = dict(n = flask_login.current_user.id)
    count_dic = dict(count = count)
    tmpuid_dic = dict(n11 = tmpuid)
    tmpusername_dic=dict(n22=tmpusername)
    tmplikes_dic = dict(n33=tmplikes)
    return render_template('friends.html', **user_id_dic,**count_dic,**tmpuid_dic, **tmpusername_dic,**tmplikes_dic)
    # return render_template('friends.html', **count_dic,**tmpuid_dic, **tmpusername_dic,**tmplikes_dic)



@app.route('/blacklist', methods=['GET','POST'])
@flask_login.login_required
def blacklist():
    t = {"U_Name1": flask_login.current_user.id}
    cursor = g.conn.execute(
        """
            select uid,user_name,likes
            from User_
            where uid in (
            select bid 
            from Blacklist_Relation
            where uid in (select uid
            from User_
            where user_name=%s))
        """,flask_login.current_user.id)

    
    blackuid = []
    blackusername = []
    blacklikes=[]
    for result in cursor:
        blackuid.append(result['uid'])  # can also be accessed using result[0]
        blackusername.append(result['user_name'])   
        blacklikes.append(result['likes'])

    cursor.close()

    cursor = g.conn.execute("SELECT count(*) FROM (select bid from blacklist_Relation where uid in (select uid from User_ where user_name=%s)) as foo",flask_login.current_user.id)
    a = cursor.fetchone()
    count = a[0]
    user_id_dic = dict(n = flask_login.current_user.id)
    black_count_dic = dict(ncount = count)
    blackuid_dic = dict(nn11 = blackuid)
    blackusername_dic=dict(nn22=blackusername)
    blacklikes_dic = dict(nn33=blacklikes)
    return render_template('blacklist.html', **user_id_dic,**black_count_dic,**blackuid_dic, **blackusername_dic,**blacklikes_dic)



@app.route('/interest', methods=['GET','POST'])
@flask_login.login_required
def interest():
    cursor = g.conn.execute(
        """
            select name,interest_description
            from Interest
            where name in(
            select name
            from Owns
            where uid in(
            select uid from User_
            where user_name=%s))
        """,flask_login.current_user.id)

    
    i_name = []
    i_description = []
    for result in cursor:
        i_name.append(result['name'])  # can also be accessed using result[0]
        i_description.append(result['interest_description'])   

    cursor.close()

    cursor = g.conn.execute(
        """SELECT count(*) FROM (select name
            from Owns
            where uid in(
            select uid from User_
            where user_name=%s)) as foo""",flask_login.current_user.id)
    a = cursor.fetchone()
    count = a[0]
    user_id_dic = dict(n = flask_login.current_user.id)
    icount_dic = dict(icount = count)
    i_name_dic = dict(nnn11 = i_name)
    i_description_dic=dict(nnn22=i_description)
    return render_template('interests.html', **user_id_dic,**icount_dic,**i_name_dic, **i_description_dic)



@app.route('/search',methods=['GET', 'POST'])
@flask_login.login_required
def search():
    user_id_dic = dict(n = flask_login.current_user.id)
    return render_template("search.html",**user_id_dic)


@app.route('/search_result',methods=['GET', 'POST'])
@flask_login.login_required
def search_result():
    results = []
    t = {"event_search": request.form['event_search']}

    cursor1 = g.conn.execute(text(
        """
            select eid, event_name, likes, tag, description, address
            from Event natural join Take_Places
            where event_name = :event_search or tag = :event_search or address = :event_search 
        """
    ),t)
    for result in cursor1:
        row = []
        row.append(result['event_name'])
        row.append(result['likes'])
        row.append(result['tag'])
        row.append(result['description'])
        row.append(result['address'])
        row.append(result['eid'])
        results.append(row)
    events_dic = dict(events = results)



    cursor2 = g.conn.execute(text(
        """
            select count(*) from Event natural join Take_Places
            where event_name = :event_search or tag = :event_search or address =:event_search 
        """
    ),t)
    tmp = cursor2.fetchone()
    count = tmp[0]
    count_dic = dict(count = count)
    user_id_dic = dict(n = flask_login.current_user.id)
    return render_template("search_result.html", **user_id_dic,**events_dic, **count_dic)


@app.route('/createUser', methods=['GET', 'POST'])
def do_createUser():
    t = {"user_name": request.form['username'], "password": request.form['password']}
    g.conn.execute(text(
        """
            insert into  User_(user_name, password)
            values
            (:user_name, :password)
        """
    ), t)

    return render_template("login.html")

@app.route('/view_event/<ID>',methods=['POST'])
@flask_login.login_required
def view_event(ID):
    results = []
    t = {"event_id": ID}

    cursor = g.conn.execute(text(
        """
            select event_name, likes, tag, description, address
            from Event natural join Take_Places
            where eid= :event_id 
        """
    ),t)
    for result in cursor:
        row = []
        row.append(result['event_name'])
        row.append(result['likes'])
        row.append(result['tag'])
        row.append(result['description'])
        row.append(result['address'])
        results.append(row)
    events_dic = dict(events = results)
    user_id_dic = dict(n = flask_login.current_user.id)
    return render_template('event_view.html', **user_id_dic,**events_dic)

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0', port=4000)