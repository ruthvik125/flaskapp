from flask import Flask,render_template, flash,request, redirect, url_for,session,logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form,StringField, TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#create a flask instance
app=Flask(__name__)

#Adding configurations to the instance 
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='ruthvik123'
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'

mysql = MySQL(app)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('Unauthorised','danger')
            return redirect(url_for('login'))
    return wrap
#Adding routes to various pages

Articles = Articles()
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id=id)


#Making a class that creates a form object with all the fields neccessary for us with labels and validated length for the fields
class RegisterForm(Form):
    name=StringField('Name',[validators.Length(min=1,max=50)])
    username=StringField('USername',[validators.Length(min=4,max=25)])
    email=StringField('Email',[validators.Length(min=6,max=50)])
    password=PasswordField('Passowrd',[validators.DataRequired(),validators.EqualTo('confirm',message='No match'),validators.Length(min=4,max=25)])
    confirm=PasswordField("confrim password")
    
#Making a class that creates an article object with necc fields
class ArticleForm(Form):
    title=StringField('Title',[validators.Length(min=1,max=30)])
    body=TextAreaField('Body',[validators.Length(min=10)])
    



@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        #Getting the data from the register form object  details to store
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data)) #Encrypting the password

        #Establish a connection with mysql database and execute insertion

        cur =mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name,email,username,password))
        mysql.connection.commit()
        cur.close()
        
        #Giving a success message with flash module

        flash('you are registered','success')
        redirect(url_for('index'))

        return render_template('register.html',form =form)
    return render_template('register.html',form =form)


@app.route('/login',methods= ['GET','POST'])
def login():
    if request.method == 'POST':
        #Taking the login details
        username = request.form['username']
        password_cd = request.form['password']
        
        cur =mysql.connection.cursor()
        result= cur.execute("SELECT * FROM users WHERE username = %s",[username])
        if result > 0:
            #FEtching the details from sql database
            data = cur.fetchone()
            password = data['PASSWORD']

            #Checking the pwd
            if sha256_crypt.verify(password_cd,password):
                
                app.logger.info("MATCHED")
                session['logged_in']=True
                session['username']=username
                flash('you are logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error="Incorrect Password"
                render_template('login.html',error=error)

        else:
            error="Incoorect username"
            render_template('login.html',error=error)
            app.logger.info("no user avilabale")

        mysql.connection.commit()
        cur.close()

        
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    cur=  mysql.connection.cursor()
    result=cur.execute("SELECT * from articles")
    articles=cur.fetchall()
    if result>0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg="NO ARTICLES HERE"
        return render_template('dashboard.html',msg=msg)

    
    cur.close()
        

    return render_template('dashboard.html')




@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return render_template('dashboard.html')



@app.route('/add_article', methods=['GET', 'POST'])

def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


if __name__=='__main__':
    
    app.secret_key='secret123'
    app.run(debug=True)

