from flask import Flask, flash,render_template,request, session, url_for
import pickle
import numpy as np
import pandas as pd
import os
from tkinter import *
from socket import *
import _thread
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
import secrets
try:
 from StringIO import StringIO
except ImportError:
 from io import StringIO
from flask_socketio import SocketIO, join_room, leave_room, emit 
import csv
from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

user_id=""

popular_df = pickle.load(open('popular.pkl','rb'))
pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))
# path='C:/Users/ronak/Dropbox/PC/Downloads/book-recommender-system-master/book-recommender-system-master'
# USER_DATA_CSV_PATH = os.path.join(os.path.dirname(path), 'Users.csv')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = secrets.token_hex(16)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['username']
        password = request.form['password']
        # with open('Users.csv', 'r') as file:
        #     reader = csv.DictReader(file)
        #     for row in reader:
        #         if row['Name'] == user_id and row['Password'] == password:
        #             session['user_id'] = user_id
        #             message = str(request.form['username'])
        #             print(message)
        #             flash(message)
        #             return redirect('/')
        with open('Users.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Name'] == user_id and row['Password'] == password:
                    session['user_id'] = user_id
                    message = str(request.form['username'])
                    print(message)
                    flash(message) 
                    return redirect('/')
        return render_template('login.html', error='Invalid login credentials')
    else:
        user_id = request.args.get('username')
        if user_id:
            with open('Users.csv', 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['User-ID'] == user_id:
                        session['user_id'] = user_id
                        return redirect('/')
            return render_template('login.html', error='User not found')
        else:
            return render_template('login.html')

@app.route('/home')
def home():
    flash(session['user_id'])
    return redirect('/')

@app.route('/add_to_wishlist/<isbn>')
def add_to_wishlist(isbn):
    user_id=session['user_id']
    book = books.loc[books['ISBN'] == isbn].iloc[0]
    wishlist_path = 'wishlist.csv'
    with open(wishlist_path, mode='a', newline='') as file:
        wishlist_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        wishlist_writer.writerow([user_id, isbn, book['Book-Title'], book['Book-Author'], book['Image-URL-S']])
        flash(session['user_id']) 
    return redirect('/')



@app.route('/wishlist')
def display_wishlist():
    
    wishlist_path = 'wishlist.csv'
    with open(wishlist_path, mode='r', newline='') as file:
        wishlist_reader = csv.reader(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        wishlist_items = []
        for row in wishlist_reader:
            if row[0] == user_id:
                wishlist_items.append(row)
    return render_template('wishlist.html', 
                           user=wishlist_items[0],
                           wishlist_items=wishlist_items,image=wishlist_items[4],
                           title=wishlist_items[3],
                           author=wishlist_items[2],
                           isbn=wishlist_items[1])

@app.route('/logout')
def logout():
    return redirect('/')

@app.route('/rating', methods=['POST'])

def rating():
    return render_template('rating.html', book = list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_rating'].values))
 
def check_logged_in():
    if 'user_id' not in session:
        return render_template('login.html')
    else:
        return render_template('rating.html')
book_data = []
with open('Books.csv', 'r') as file:
    reader = csv.DictReader(file)

    for row in reader:
      book_data.append(row)
    
# route for rating books

@app.route('/contact')
def contact():
 return render_template('contact.html')
 

@app.route('/rate_book/<isbn>')     
def rate_book(isbn):
    if 'user_id' not in session:
        return render_template('login.html')
    else:
       
        book_exists = False
        book_data = []
        for ISBN in books.items():
           book_data.append({'isbn': ISBN, })
        for book in book_data:
            if book['isbn'] == isbn:
                
                book_exists = True
                break
        
        session['isbn'] = isbn
        return render_template('rating.html', isbn=isbn)
        

@app.route('/rate/<isbn>', methods=['POST','GET'])
def rate(isbn):
    user_id = session['user_id']
    isbn = request.args.get('isbn')
    rating = int(request.form['rating'])

    with open('Ratings.csv', mode='a') as ratings_file:
        fieldnames = ['User-ID', 'ISBN', 'Book-Rating']
        writer = csv.DictWriter(ratings_file, fieldnames=fieldnames)
        writer.writerow({'User-ID': user_id, 'ISBN': isbn, 'Book-Rating': rating})

    return redirect(url_for('rating.html', isbn=isbn))

socketio = SocketIO(app)

@app.route('/chat')
def chat():
    return render_template('chat.html')

@socketio.on('connect')
def on_connect():
    username = request.args.get('username')
    join_room(username)
    emit('status', {'msg': session['user_id'] +' with username '+username + ' has joined.'}, room=username)

@socketio.on('disconnect')
def on_disconnect():
    username = request.args.get('username')
    leave_room(username)
    emit('status', {'msg': username + ' has left.'}, room=username)

@socketio.on('message')
def handle_message(msg):
    username = request.args.get('username')
    receiver = msg['receiver']
    message = msg['message']
    emit('chat', {'sender': username, 'receiver': receiver, 'message': message}, room=receiver)


    

    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Get the username and password from the signup form
        username = request.form['username']
        password = request.form['password']
        # Load the user data from the CSV file
        user_data = pd.read_csv('Users.csv')
        # Generate a new ID for the user
        new_id = user_data['User-id'].max() + 1
        # Append the new user data to the CSV file
        session["Name"]= 'username'
        session["Password"]= 'password'
        user_data = user_data.append({'User-id': new_id, 'Name': username, 'Password': password}, ignore_index=True)
        user_data.to_csv('Users.csv', index=False)
        return render_template('login.html')
    else:
        return render_template('signup.html')

@app.route('/chat' )
def initialize_server():
    # initialize socket
    s = socket(AF_INET, SOCK_STREAM)
    # config details of server
    host = 'localhost'  ## to use between devices in the same network eg.192.168.1.5
    port =1234
    # initialize server
    s.bind((host, port))
    # set no. of clients
    s.listen(1)
    # accept the connection from client
    conn, addr = s.accept()

    return conn

# update the chat log
def update_chat(msg, state):
    global chatlog
    chatlog.config(state=NORMAL)
    # update the message in the window
    if state==0:
        chatlog.insert(END, 'YOU: ' + msg)
    else:
        chatlog.insert(END, 'OTHER: ' + msg)
    chatlog.config(state=DISABLED)
    # show the latest messages
    chatlog.yview(END)

# function to send message
def send():
    global textbox
    # get the message
    msg = textbox.get("0.0", END)
    # update the chatlog
    update_chat(msg, 0)
    # send the message
    conn.send(msg.encode('ascii'))
    textbox.delete("0.0", END)

# function to receive message
def receive():
    while 1:
        try:
            data = conn.recv(1024)
            msg = data.decode('ascii')
            if msg != "":
                update_chat(msg, 1)
        except:
            pass

def press(event):
    send()

# GUI function
def GUI():
    global chatlog
    global textbox

    # initialize tkinter object
    gui = Tk()
    # set title for the window
    gui.title("Server Chat")
    # set size for the window
    gui.geometry("380x430")

    # text space to display messages
    chatlog = Text(gui, bg='white')
    chatlog.config(state=DISABLED)

    # button to send messages
    sendbutton = Button(gui, bg='orange', fg='red', text='SEND', command=send)

    # textbox to type messages
    textbox = Text(gui, bg='white')

    # place the components in the window
    chatlog.place(x=6, y=6, height=386, width=370)
    textbox.place(x=6, y=401, height=20, width=265)
    sendbutton.place(x=300, y=401, height=20, width=50)

    # bind textbox to use ENTER Key
    textbox.bind("<KeyRelease-Return>", press)

    # create thread to capture messages continuously
    _thread.start_new_thread(receive, ())

    # to keep the window in loop
    gui.mainloop()

@app.route('/')
def index():
    return render_template('index.html',
                           username=user_id,
                           book_name = list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           book_isbn=list(books['ISBN'].values),
                           rating=list(popular_df['avg_rating'].values)
                           )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books',methods=['post'])
def recommend():
   try:
        user_input = request.form.get('user_input')
        index = np.where(pt.index == user_input)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]
    
        data = []
        for i in similar_items:
            item = []
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
            item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
    
            data.append(item)
        
            print(data)
   except:
       return render_template('error.html')
   else:
       
      return render_template('recommend.html',data=data)

if __name__ == '__main__':
    app.run(debug=True)