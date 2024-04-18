from flask import render_template, request
from app import app
from utils import *
from io import BytesIO

cache = {'DBS':None, 'Paylah!':None, 'POSB':None, 'UOB':None, 'HSBC':None}
names = {'DBS':'', 'Paylah!':'', 'POSB':'', 'UOB':'', 'HSBC':''}
banks = ['DBS',"Paylah!","POSB","UOB","HSBC"]
dfs = {'in_df':pd.DataFrame(), 'out_df':pd.DataFrame()}

@app.route('/',methods=['GET', 'POST'])
@app.route('/index')
def index():
    if request.method == 'POST':
        bank = request.args.get('bank')
        file = request.files['file']
        file_name = file.filename
        names[bank] = file_name
        file_content = BytesIO(file.stream.read())
        cache[bank] = file_content
        # cache[bank]=file
    return render_template('index.html', title='Home', banks=banks, names=names )

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    columns = ['Date','Description','Amount']

    if len(dfs['in_df']) == 0 and len(dfs['out_df']) == 0:
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

        out_df['Date'] = pd.to_datetime(out_df['Date'] + ' 2024', format='%d %b %Y')
        out_df = out_df.sort_values(by='Date')
        in_df['Date'] = pd.to_datetime(in_df['Date'] + ' 2024', format='%d %b %Y')
        in_df = in_df.sort_values(by='Date')
        dfs['in_df'] = in_df
        dfs['out_df'] = out_df

    out_df = dfs['out_df']
    in_df = dfs['in_df']
    in_df['week']=in_df['Date'].dt.isocalendar().week
    in_df['Amount'] = in_df['Amount'].astype(str).str.replace(',','').astype(float)
    inVals = in_df.groupby(['week'])['Amount'].mean().tolist()
    out_df['week']=out_df['Date'].dt.isocalendar().week
    out_df['Amount'] = out_df['Amount'].astype(str).str.replace(',','').astype(float)
    outVals = out_df.groupby(['week'])['Amount'].mean().tolist()
    labels  = ['Week '+ str(x) for x in range(1,1+len(set(in_df['week'].tolist() + out_df['week'].tolist())))]
    while len(inVals) != len(labels):
        inVals.append(0)
    while len(outVals) != len(labels):
        outVals.append(0)
    labels = '<>'.join(labels)
    in_df['Category'].fillna('Others',inplace=True)
    out_df['Category'].fillna('Others',inplace=True)
    categories_in = in_df.groupby(['Category'])['Amount'].mean().to_dict()
    categories_out = out_df.groupby(['Category'])['Amount'].mean().to_dict()
    cat_in_name = '<>'.join(categories_in.keys())
    cat_in_vals = list(categories_in.values())
    cat_out_name = '<>'.join(categories_out.keys())
    cat_out_vals = list(categories_out.values())

    return render_template("summaryTable.html",title='Summary', inGraph=inVals, outGraph=outVals, labels=labels, totalIn=round(sum(inVals),2), totalOut=round(sum(outVals),2), cat_in_name=cat_in_name, cat_in_vals=cat_in_vals, cat_out_name=cat_out_name, cat_out_vals=cat_out_vals)

@app.route('/breakdown', methods=['GET', 'POST'])
def breakdown():
    columns = ['Date','Description','Amount', 'Category']
    if len(dfs['in_df']) == 0 and len(dfs['out_df']) == 0:
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
        dfs['in_df'] = in_df
        dfs['out_df'] = out_df
    in_categories = dfs['in_df']["Category"].unique()
    out_categories = dfs['out_df']["Category"].unique()
    in_categories = np.insert(in_categories, 0, "All")
    out_categories = np.insert(out_categories, 0, "All")
    if "week" in dfs['in_df'].columns:
        in_df = dfs['in_df'].drop(columns=["week"])
    if "week" in dfs['out_df'].columns: 
        out_df = dfs['out_df'].drop(columns=["week"])
    return render_template("breakdownTable.html",title='Breakdown', in_df=in_df, out_df=out_df, in_categories=in_categories, out_categories=out_categories)


    
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
    dfs['in_df'] = pd.DataFrame()
    dfs['out_df'] = pd.DataFrame()
    return render_template('index.html', title='Home', banks=banks, names=names )