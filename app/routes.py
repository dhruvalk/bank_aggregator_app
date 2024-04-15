from flask import render_template, request
from app import app
from utils import *
from io import BytesIO

cache = {'DBS':None, 'Paylah!':None, 'POSB':None, 'UOB':None, 'HSBC':None}
names = {'DBS':'', 'Paylah!':'', 'POSB':'', 'UOB':'', 'HSBC':''}
banks = ['DBS',"Paylah!","POSB","UOB","HSBC"]

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
        file_content = BytesIO(file.stream.read())
        print(file_content)
        cache[bank] = file_content
        # cache[bank]=file
    return render_template('index.html', title='Home', banks=banks, names=names )

@app.route('/files', methods=['GET', 'POST'])
def files():
    columns = ['Date','Description','Amount']
    in_df = pd.DataFrame(columns=columns)
    out_df = pd.DataFrame(columns=columns)
    for key,file in cache.items():
        if file is not None:
            if key == "POSB":
                in_df, out_df = append_posb_data(file, in_df, out_df)
            elif key == "DBS":
                in_df, out_df = append_dbs_data(file, in_df, out_df)
            elif key == "UOB":
                in_df, out_df = append_uob_data(file, in_df, out_df)
            elif key == "Paylah!":
                in_df, out_df = append_paylah_data(file, in_df, out_df)
            elif key == "HSBC":
                in_df, out_df = append_hsbc_data(file,in_df,out_df)
    return out_df.to_html() + in_df.to_html()
    
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
    return render_template('index.html', title='Home', banks=banks, names=names )