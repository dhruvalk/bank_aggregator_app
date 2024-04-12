from flask import render_template, request
from app import app

cache = []
names = {'DBS':'', 'Paylah!':'', 'POSB':'', 'OCBC':''}

@app.route('/',methods=['GET', 'POST'])
@app.route('/index')
def index():
    if request.method == 'POST':
        bank = request.args.get('bank')
        print(bank)
        file = request.files['file']
        print(request.files)
        file_name = file.filename
        names[bank] = file_name
        cache.append(file)
        
    return render_template('index.html', title='Home', banks=['DBS',"Paylah!","POSB","OCBC"], names=names )

@app.route('/files', methods=['GET', 'POST'])
def files():
    print(cache)
    return "Look at the python Flask terminal for the files uploaded."
