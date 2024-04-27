from flask import Flask, render_template, request
import json
import mysql.connector

db_pwd="your-db-pwd"
#load my database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password=db_pwd
)

app = Flask(__name__)

def database_call(query):
    return query

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_sql_response", methods=['GET', 'POST'])
def get_sql_response():
    if request.method == 'POST':
        #message = request
        message = request.data.decode('utf-8')
    else:  # This handles the GET request case
        message = request.args.get("message")

    message=json.loads(message)
    
    mycursor = mydb.cursor()
    mycursor.execute("use test_db;")
    mycursor.execute(message['message'])
    
    x = [i for i in mycursor]

    #UNCOMMENT THESE LINES TO VIEW THE SQL QUERY AND THE RESPONSE RETURNED
    print(message['message'])
    print(x)
    y = [list(i) for i in x][0:]
    y = "  \n".join([str(i) for i in y])
    print(y)

    return y
if __name__ == "__main__":
    app.run(debug=True)