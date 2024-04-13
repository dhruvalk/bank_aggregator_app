from flask import render_template, request
from app import app

cache = {'DBS':None, 'Paylah!':None, 'POSB':None, 'UOB':None}
names = {'DBS':'', 'Paylah!':'', 'POSB':'', 'UOB':''}

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
        cache[bank]=file
        
    return render_template('index.html', title='Home', banks=['DBS',"Paylah!","POSB","UOB"], names=names )

@app.route('/files', methods=['GET', 'POST'])
def files():
    print(cache)
    # look at the cache, these are the files with the keys as different banks, you can get the file from each key and do what is needed to it
    return "Look at the python Flask terminal for the files uploaded."

@app.route('/clear', methods=['GET', 'POST'])
def clear():
    cache['DBS'] = None
    cache['Paylah!'] = None
    cache['POSB'] = None
    cache['UOB'] = None
    names['DBS'] = ''
    names['Paylah!'] = ''
    names['POSB'] = ''
    names['UOB'] = ''
    return render_template('index.html', title='Home', banks=['DBS',"Paylah!","POSB","UOB"], names=names )