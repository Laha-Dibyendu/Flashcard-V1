from os import name
from flask import Flask, render_template, request, redirect, url_for
from flask.templating import _render
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import defaultload
from flask_security import Security, SQLAlchemyUserDatastore, login_required, \
    UserMixin, RoleMixin,login_user, logout_user
import datetime 
from flask_security.utils import hash_password, verify_password
import sqlite3
from sqlalchemy.sql import func

#----------------------------------------------------------------------------------------------------------------------#
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECURITY_PASSWORD_SALT'] = 'thisisasecretsalt'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
#---------------------------------------------------------------------------------------------------------------------#

#------------------------------------Log Files Setup--------------------------------------------------------------#
import logging
logging.basicConfig(filename='debug.log', level = logging.DEBUG, format= f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
#---------------------------------------------------------------------------------------------------------------------#



#----------------------------------Models--------------------------------------------------------------------------------#
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    f_name= db.Column(db.String(100),nullable=False)
    l_name= db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    uscore=db.Column(db.Integer, default=0)
    roles = db.relationship('Role', secondary=roles_users,  backref=db.backref('users', lazy='dynamic'))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(255))

class Card(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    front=db.Column(db.String(255),nullable = False)
    back= db.Column(db.String(255),nullable = False)
    deck_id=db.Column(db.Integer, db.ForeignKey("deck.id", ondelete="CASCADE"), nullable = False)
    user_no = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable = False)
    last_review=db.Column(db.DateTime(timezone=True), default=datetime.datetime.now())
    cscore=db.Column(db.Integer, default=0)


class deck(db.Model):
    id= db.Column(db.Integer, primary_key=True, autoincrement=True)
    title= db.Column(db.String(255))
    user_id=db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable = False)
    last_view=db.Column(db.DateTime(timezone=True),default=datetime.datetime.now())
    deck_score=db.Column(db.Integer,default=0)

#----------------------------------------------------------------------------------------------------------#

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
deck_datastore=SQLAlchemyUserDatastore(db,deck,User )
security = Security(app, user_datastore)

#---------------------------------------------Controllers------------------------------------------------------------------------------#

#-------------------------------------------For Index.html-----------------------------------------------------#
@app.route("/",methods=["GET"])
def home():
    return render_template("index.html")

#------------------------------------------------To register a user--------------------------------------------#
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method=="POST":
        password=request.form.get('psw')
        rep=request.form.get('psw-repeat')
        email=request.form.get('email')
        if password.isalnum() and len(password)>7:
            if password==rep:
                if request.method == 'POST':
                    user_datastore.create_user(
                        f_name=request.form.get('f_name'),
                        l_name=request.form.get('l_name'),
                        email=request.form.get('email'),
                        password=hash_password(request.form.get('psw'))
                    )
                    db.session.commit()
                    return redirect(url_for("register"))

            return render_template('error.html')
        return render_template('error.html')
    return render_template('register.html')
    

#------------------------------------------------------Dashboard log in---------------------------------------------------#
@app.route('/dashboard',methods=['POST', 'GET'])
@login_required
def profile():

    return render_template('dashboard.html')
    
#----------------------------------------------------------for Sign in Page----------------------------------------------#
@app.route('/signin',methods = ['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        email=request.form.get('email')
        
        password=request.form.get('pasw')
        
        user=User.query.filter_by(email=email).first()
        
        if user:
            id=user.id
            if verify_password(password, user.password):
                login_user(user,remember=True)
                return redirect(url_for('signin',id=id))
            else:
                return '<h2>Your password is incorrect</h2>'
           
        else:
            return render_template("error.html")
    return render_template('login.html')


# -----------------------------dOING sIGN IN----------------------------------------------------------------#-
@app.route('/signin/<id>',methods = ['GET'])
@login_required
def signin(id):
    conn=None
    try:
        conn=sqlite3.connect('db.sqlite3')
        curr=conn.cursor()
        curr.execute("select title,deck_score from deck where user_id='%s' order by deck_score desc limit 1"%id)
        rows=curr.fetchone()
        print(rows)
        curr.execute("select title,JULIANDAY(?) - JULIANDAY(last_view),deck_score from deck where user_id=?",(datetime.datetime.now(),id))
        dash=curr.fetchall()
        curr.close() 
        return render_template('dashboard.html',rows=rows,dash=dash)
    except (Exception,sqlite3.DatabaseError) as error:
        print(error)
        return '<h1>There is error above line 149 this</h1>'
    

#--------------------------------------------Addidng Deck from Dash board --------------------------



@app.route('/signin/deck/<id>',methods = ['GET', 'POST'])
@login_required
def deckk(id):
    if request.method == 'POST':
        dname=request.form.get('dname')
        user=User.query.filter_by(id=id).first()
        Id=user.id
        Deck=deck.query.filter_by(user_id=Id).all()
        
        if dname:
            for i in Deck:
                if i.title==dname:
                    return render_template("error.html")
            conn=None
            try:
                conn=sqlite3.connect('db.sqlite3')
                curr=conn.cursor()
                curr.execute("INSERT INTO deck(title, user_id) values(?,?);",(dname,Id))
                conn.commit()
                curr.execute("select title from deck where user_id='%s'"%id)
                rows=curr.fetchall()
                curr.close() 
                return redirect(url_for('signin',id=id))
               
            except (Exception,sqlite3.DatabaseError) as error:
                print(error)
                return '<h1>There is error above line 182 this</h1>'  
    else:
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            curr.execute("select deck.title,deck_score,JULIANDAY(?) - JULIANDAY(last_view) from deck where user_id=?",(datetime.datetime.now(),id))
            rows=curr.fetchall()
            curr.close() 
            return render_template('deck.html',rows=rows)
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is error above line 194 this</h1>'

#-----------------------------------------------------------------Add deck from deck page --------------------------

@app.route('/signin/deck/add/<id>',methods = ['GET', 'POST'])
@login_required
def deckk2(id):
    if request.method == 'POST':
        dname=request.form.get('dname')
        user=User.query.filter_by(id=id).first()
        Id=user.id
        Deck=deck.query.filter_by(user_id=Id).all()
    
        if dname:
            for i in Deck:
                if i.title==dname:
                    return render_template("error.html")
            conn=None
            try:
                conn=sqlite3.connect('db.sqlite3')
                curr=conn.cursor()

                curr.execute("INSERT INTO deck(title, user_id) values(?,?);",(dname,Id))
                conn.commit()
                
                curr.close() 
                return redirect(url_for('deckk',id=id))
            except (Exception,sqlite3.DatabaseError) as error:
                print(error)
                return '<h1>There is error above line 223 this</h1>'
    
#-----------------------------------------------------------Deleting Deck from deck view page--------------------------------------#

@app.route('/signin/deck/delete/<id>',methods = ['GET', 'POST'])
@login_required
def deletedeck(id):
    if request.method == 'POST':
        dname=request.form.get('dname1')
        
        Deck=deck.query.filter_by(user_id=id,title=dname).first()
        if Deck:
            deck_id=Deck.id
            conn=None
            try:
                conn=sqlite3.connect('db.sqlite3')
                curr=conn.cursor()

                curr.execute("DELETE from card where deck_id=? and user_no=?",(deck_id,id))
                conn.commit()

                curr.execute("DELETE from deck where id=%s"%deck_id)
                conn.commit()
                
                curr.execute("select title,deck_score from deck where user_id='%s' order by deck_score desc limit 1"%id)
                rows=curr.fetchone()
                if rows==None:
                    uscore=0
                    uql="update user set uscore=? where id=?"
                    curr.execute(uql,(uscore,id))
                else:
                    uql="update user set uscore=? where id=?"
                    curr.execute(uql,(rows[1],id))
                    curr.close() 
                
                return redirect(url_for('signin',id=id))
            except (Exception,sqlite3.DatabaseError) as error:
                print(error)
                return '<h1>There is error above line 264 this</h1>'
        else:
            return "<h2> There is no Deck go back </h2>" 

#---------------------------------------Deleting Account from the app-------------------------------------------------------#

@app.route('/signin/deck/delete/acc/<id>',methods = ['GET', 'POST'])
@login_required
def deleteacc(id):
    if request.method == 'POST':
        # dname=request.form.get('dname3')
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            logout_user()
            curr.execute("DELETE from user where id=%s"%id)
            conn.commit()
            curr.close() 
            return render_template("index.html")
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is error above line 279 this</h1>'
    return render_template("index.html")
#-------------------------------------------------------Adding Card--------------------------------------------------------------#


@app.route('/signin/deck/card/<id>/<p>',methods = ['GET', 'POST'])
@login_required
def cards(id,p):
    if request.method == 'POST':
        front=request.form.get("front")
        back=request.form.get("back")
        Deck=deck.query.filter_by(title=p,user_id=id).one()
        deck_id=Deck.id
        card=Card.query.filter_by(deck_id=deck_id,user_no=id).all()

        if front and back:
            for i in card:
                if i.front==front and i.back==back:
                    return render_template("error.html")
            conn=None
            try:
                conn=sqlite3.connect('db.sqlite3')
                curr=conn.cursor()

                curr.execute("INSERT INTO card(front,back,deck_id, user_no,last_review) values(?,?,?,?,?);",(front,back,deck_id,id,datetime.datetime.now()))
                conn.commit()
                curr.execute("select deck.title,deck_score,JULIANDAY(?) - JULIANDAY(last_view) from deck where user_id=?",(datetime.datetime.now(),id))
                rows=curr.fetchall()
                curr.close() 
                return redirect(url_for('deckk',id=id))
            except (Exception,sqlite3.DatabaseError) as error:
                print(error)
                return '<h1>There is error above line 311 this</h1>' 
    else:
        Deck=deck.query.filter_by(title=p,user_id=id).one()
        deck_id=Deck.id
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            curr.execute("select * from card where user_no=? and deck_id=?",(id,deck_id))
            rows=curr.fetchall()
            curr.close() 
            return render_template("card.html",rows=rows,p=p)
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is error above line 325 for this</h1>'

    return render_template("error.html",p=p)


#-----------------------------TAKING qUIZ----------------------------------------------------------------------------------#--

@app.route("/signin/deck/quiz/<id>/<p>",methods = ['GET', 'POST'])
@login_required
def quiz(id,p):
    if request.method=="GET":
        Deck=deck.query.filter_by(title=p,user_id=id).one()
        #print(Deck)
        deck_id=Deck.id
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            curr.execute("select * from card where user_no=? and deck_id=?",(id,deck_id))
            rows=curr.fetchall()

            curr.execute("select deck_score from deck where id='%s'"%deck_id)
            s=curr.fetchone()
            
            ds=s[0]
            
           
            curr.close() 
            return render_template("quiz.html",rows=rows,p=p,ds=ds)
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is error above line 356 this</h1>'

#-------------------------------------Quiz marks giving and updating ----------------------------------------------------------#-


@app.route('/signin/deck/quiz/<id>/<p>/card/<r>',methods = ['GET', 'POST'])
@login_required
def score_card(id,p,r):
    if request.method=="POST":
        Deck=deck.query.filter_by(title=p,user_id=id).one()
        
        deck_id=Deck.id
        
        score=0
        clicks=request.form.get("click")
        if clicks=='easy':#10
            score+=10
        elif clicks=='medium':#7
            score+=7
        elif clicks=='hard':#4
            score+=4
        else:#2
            score+=2
        
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            
            sql="UPDATE card set cscore = ? , last_review =? where id = ?"
            curr.execute(sql, (score,datetime.datetime.now(), r))
            conn.commit()
            
            curr.execute("select cscore from card where deck_id ='%s'"%deck_id)
            rows=curr.fetchall()
            dscore=0
            cou=len(rows)
            for row in rows:
                if row[0]:
                    dscore+=row[0]
            
            deck_score=round(dscore/cou,2)
            

            fql="update deck set deck_score=?,last_view=? where id=?"
            curr.execute(fql,(deck_score,datetime.datetime.now(),deck_id))
            conn.commit()

            curr.execute("select deck_score from deck where user_id='%s' order by deck_score desc limit 1"%id)
            uscore=curr.fetchone()
            uql="update user set uscore=? where id=?"
            curr.execute(uql,(uscore[0],id))
            conn.commit()

            curr.close()
            return redirect(url_for("quiz",p=p,id=id,ds=deck_score))
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is error above line 414 this</h1>'



#----------------------------------------------------------Card Edit Delete-----------------------------------------------#

@app.route('/signin/deck/quiz/<id>/<deckname>/card/<cardid>/delete',methods = ['GET', 'POST'])
@login_required
def carddelete(id,deckname,cardid):
    if request.method=="POST":
        Deck=deck.query.filter_by(title=deckname,user_id=id).one()
        
        deck_id=Deck.id
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            curr.execute("delete from card where user_no=? and deck_id=? and id=?",(id,deck_id,cardid))
            
            conn.commit()
            curr.close() 
            
            return redirect(url_for("cards",id=id,p=deckname))
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is error above line 439 this</h1>'


#-------------------------------------------Card Edit-------------------------------------------------------------#
@app.route("/signin/deck/quiz/<user_id>/<deckname>/card/<cardid>/edit",methods = ['GET', 'POST'])
@login_required
def cardadd(user_id,deckname,cardid):
    if request.method=="POST":
        Deck=deck.query.filter_by(title=deckname,user_id=user_id).one()
        front=request.form.get("fronte")
        back=request.form.get("backe")
        deck_id=Deck.id
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            gql="update  card set front = ?,back = ?  where id = ?"
            curr.execute(gql,(front,back,cardid))
            conn.commit()
            curr.close()
            return redirect(url_for("cards",id=user_id,p=deckname))
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is eror abover line 462 this</h1>'

#-------------------------------------------Deck Edit------------------------------------------------------------------#-
@app.route("/signin/deck/<id>/<p>/edit" ,methods = ['GET', 'POST'])
@login_required
def  deckedit(id,p):
    if request.method=="POST":
        Deck=deck.query.filter_by(title=p,user_id=id).one()
        front=request.form.get("frontd")
        #back=request.form.get("backd")
        deck_id=Deck.id
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            gql="update deck set title = ?  where id = ?"
            curr.execute(gql,(front,deck_id))
            conn.commit()
            curr.close()
            return redirect(url_for("deckk",id=id))
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There is error above line 484 this</h1>'

#--------------------------------------------Deck Delete-----------------------------------------------------------------#

@app.route("/signin/deck/<id>/<p>/delete" ,methods = ['GET', 'POST'])
@login_required
def  deck_delete(id,p):
    if request.method=="POST":
        Deck=deck.query.filter_by(title=p,user_id=id).one()
        deck_id=Deck.id
        conn=None
        try:
            conn=sqlite3.connect('db.sqlite3')
            curr=conn.cursor()
            curr.execute("DELETE from card where deck_id=? and user_no=?",(deck_id,id))
            conn.commit()
            curr.execute("delete from deck where id = %s"%deck_id,)
            conn.commit()
            curr.close()
            return redirect(url_for("deckk",id=id))
        except (Exception,sqlite3.DatabaseError) as error:
            print(error)
            return '<h1>There error above line 506 this</h1>'

#---------------------------------------------------------Log out---------------------------------------------------------------#

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')



if __name__=="__main__":
    app.run(debug=True)