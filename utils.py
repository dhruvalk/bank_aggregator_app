import pandas as pd
import numpy as np
import PyPDF2
import re
import tabula 
from datetime import datetime

paylah_categories = {}
paylah_categories['Transfers In'] = ['RECEIVE EGIFT','RECEIVE MONEY FROM']
paylah_categories['Cashback'] = ['CASHBACK']
paylah_categories['Transfer Out'] = ['PAYNOW TO','SEND MONEY TO','SEND EGIFT']

posb_categories = {}
posb_categories['Transport'] = ['BUS/MRT']
posb_categories['Cash withdrawal'] = ['Cash Withdrawal']
posb_categories['Transfers In'] = ['INCOMING PAYNOW']
posb_categories['Transfer Out'] = ["YOUTRIPSI"]

hsbc_categories = {}
hsbc_categories['Groceries/Shopping'] = ['FAIRPRICE', 'FairPrice', 'NTUC']

uob_categories = {}
uob_categories['Transport'] = ['BUS/MRT']
uob_categories['Transfer'] = ["PAYNOW-FAST"]

description_to_remove_set = set(["OTHER", "FAST Payment / Receipt"])

def get_num_pages(file):
    # Create a PDF file reader object
    pdf_reader = PyPDF2.PdfReader(file)
    # Get the number of pages
    num_pages = len(pdf_reader.pages)
    return num_pages

def categorise_transaction(row,dic):
    for category in dic:
        if any([pattern in row['Description'].upper() for pattern in dic[category]]):
            return category
    return None

def get_posb_raw_data(file_name, num_pages):
    # Read first page, with different area coordinates from other pages due to headers
    dfs_page1 = tabula.read_pdf(file_name, pages=[2], silent=True, guess = False, stream = True, multiple_tables=False, area=[173,22,718,565])[0]
    # Initialize an empty list to store DataFrames from other pages
    dfs_others = pd.DataFrame(columns=dfs_page1.columns)
    # Iterate over pages starting from page 3
    for page_num in range(3,num_pages-1):
        # Read the page with the specified area
        df = tabula.read_pdf(file_name, pages=[page_num], silent=True, guess=False, stream=True, multiple_tables=True, area=[94, 30, 737, 564])[0]
        # Append the DataFrame to the list
        dfs_others = pd.concat([dfs_others, df], ignore_index=True)
    dfs = pd.concat([dfs_page1,dfs_others])
    columns_to_drop = [col for col in dfs.columns if col.startswith('Unnamed')]
    dfs.drop(columns=columns_to_drop, inplace=True)
    return dfs

def get_posb_cleaned_data(dfs):
    def convert_date_format(date_str):
        # Split the date string into day and month abbreviation
        day, month_abbr = date_str[:2], date_str[2:]
        # Capitalize the first letter of the month abbreviation
        month_abbr = month_abbr.capitalize()
        return f"{day} {month_abbr}"
    ROWS, i = dfs.shape[0], 0
    res = pd.DataFrame(columns= dfs.columns)
    while i < ROWS:
        description = dfs.iloc[i]["Description"]
        if pd.notna(dfs.iloc[i]["Date"]):
            if description not in description_to_remove_set:
                newDescription = [str(dfs.iloc[i]["Description"])]
            else: 
                newDescription = []
            curr_row = dfs.iloc[i].copy()
            i += 1
            while i < ROWS and pd.isna(dfs.iloc[i]["Date"]):
                description = dfs.iloc[i]["Description"]
                if pd.notna(description) and description not in description_to_remove_set:  # Check if description is not NaN
                    newDescription.append(str(description))
                i += 1
            if newDescription[0] == "Debit Card Transaction":
                newDescription.pop()
                newDescription.pop(0)
                curr_row["Date"] = convert_date_format(newDescription[0][-5:])
                newDescription[0] = newDescription[0][:-5]
            curr_row["Description"] = ' '.join(newDescription)
            res = pd.concat([res, curr_row.to_frame().T])
        else:
            i += 1
    def convert_date_format(date_str):
        try:
            # Attempt to parse the date string
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            # If successful, format the date in "d MMM" format
            return date_obj.strftime('%-d %b')
        except ValueError:
            # If parsing fails, return the original string
            return date_str
    # Convert valid dates to the desired format
    res["Date"] = res["Date"].apply(convert_date_format)
    return res
 

def append_posb_data(FILE_NAME, in_df, out_df):
    num_pages = get_num_pages(FILE_NAME)
    dfs_posb = get_posb_raw_data(FILE_NAME,num_pages)
    df_posb = get_posb_cleaned_data(dfs_posb)

    # Drop any extra columns and rename existing columns
    df_posb.drop(['Balance (SGD)'],axis=1,inplace=True)
    df_posb = df_posb[~df_posb['Description'].str.contains("Funds Transfer TOP-UP TO PAYLAH!")]
    df_posb['Category'] = df_posb.apply(lambda x: categorise_transaction(x,posb_categories), axis=1)

    # Split into incoming and outgoing funds dfs
    outgoing = df_posb[df_posb['Withdrawal (-)'].notna()].copy()
    outgoing.rename({'Withdrawal (-)':"Amount"}, axis='columns',inplace=True)
    outgoing.drop(['Deposit (+)'],axis=1,inplace=True)
    out_df = pd.concat([out_df,outgoing],ignore_index=True)

    incoming = df_posb[df_posb['Withdrawal (-)'].isna()].copy()
    incoming.rename({'Deposit (+)':"Amount"}, axis='columns',inplace=True)
    incoming.drop(['Withdrawal (-)'],axis=1,inplace=True)
    in_df = pd.concat([in_df,incoming],ignore_index=True)
    return in_df, out_df

def get_dbs_raw_data(file_name, num_pages):
    # Read first page, with different area coordinates from other pages due to headers
    dfs_page1 = tabula.read_pdf(file_name, pages=[1], silent=True, guess = False, stream = True, multiple_tables=False, area=[258,26,730,533])[0]
    # Initialize an empty list to store DataFrames from other pages
    dfs_others = pd.DataFrame(columns=dfs_page1.columns)
    # Iterate over pages starting from page 3
    for page_num in range(2,num_pages-1):
        # Read the page with the specified area
        df = tabula.read_pdf(file_name, pages=[page_num], silent=True, guess=False, stream=True, multiple_tables=True, area=[115,28,710,533])[0]
        # Append the DataFrame to the list
        if len(df.columns) == len(dfs_others.columns):
            df.columns = dfs_others.columns
            dfs_others = pd.concat([dfs_others, df], ignore_index=True)
    dfs = pd.concat([dfs_page1,dfs_others])
    columns_to_drop = [col for col in dfs.columns if col.startswith('Unnamed:')]
    dfs.drop(columns=columns_to_drop, inplace=True)
    return dfs

def get_dbs_cleaned_data(dfs):
    def convert_date_format(date_str):
        # Split the date string into day and month abbreviation
        day, month_abbr = date_str[:2], date_str[2:]
        # Capitalize the first letter of the month abbreviation
        month_abbr = month_abbr.capitalize()
        return f"{day} {month_abbr}"   
    ROWS, i = dfs.shape[0], 0
    res = pd.DataFrame(columns= dfs.columns)
    while i < ROWS:
        description = dfs.iloc[i]["DETAILS OF TRANSACTIONS"]
        if pd.notna(dfs.iloc[i]["DATE"]):
            if description not in description_to_remove_set:
                newDescription = [str(description)] 
            else:
                newDescription = []
            curr_row = dfs.iloc[i].copy()
            i += 1
            while i < ROWS and pd.isna(dfs.iloc[i]["DATE"]):
                description = dfs.iloc[i]["DETAILS OF TRANSACTIONS"]
                if pd.notna(description) and description not in description_to_remove_set:  # Check if description is not NaN
                    newDescription.append(str(description))
                i += 1
            if newDescription[0] == "Debit Card Transaction":
                newDescription.pop()
                newDescription.pop(0)
                curr_row["DATE"] = convert_date_format(newDescription[0][-5:])
                newDescription[0] = newDescription[0][:-5]
            curr_row["DETAILS OF TRANSACTIONS"] = ' '.join(newDescription)
            res = pd.concat([res, curr_row.to_frame().T])
        else:
            i += 1
    def is_date_valid(date_str):
        # Define the date pattern (assuming DD MMM format)
        date_pattern = r'\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        # Check if the date string matches the pattern
        return re.fullmatch(date_pattern, str(date_str)) is not None
    def filter_valid_dates(df):
        # Filter rows based on the validity of the "Date" column
        valid_dates_mask = df["DATE"].apply(is_date_valid)
        return df[valid_dates_mask]
    # Filter out rows with invalid dates
    res_filtered = filter_valid_dates(res)
    return res_filtered

def append_dbs_data(FILE_NAME, in_df, out_df):
    num_pages = get_num_pages(FILE_NAME)
    dfs_dbs = get_dbs_raw_data(FILE_NAME,num_pages)
    df_dbs = get_dbs_cleaned_data(dfs_dbs)

    # Drop any extra columns and rename existing columns
    df_dbs.drop(['BALANCE($)'],axis=1,inplace=True)
    df_dbs.rename(columns={'DETAILS OF TRANSACTIONS': 'Description', 'DATE': 'Date'}, inplace=True)
    df_dbs = df_dbs[~df_dbs['Description'].str.contains("Funds Transfer TOP-UP TO PAYLAH!")]
    df_dbs['Category'] = df_dbs.apply(lambda x: categorise_transaction(x,posb_categories), axis=1)  # use same categories as POSB for now

    # Split into incoming and outgoing funds dfs
    outgoing = df_dbs[df_dbs['WITHDRAWAL($)'].notna()].copy()
    outgoing.rename({'WITHDRAWAL($)':"Amount"}, axis='columns',inplace=True)
    outgoing.drop(['DEPOSIT($)'],axis=1,inplace=True)
    out_df = pd.concat([out_df,outgoing],ignore_index=True)

    incoming = df_dbs[df_dbs['WITHDRAWAL($)'].isna()].copy()
    incoming.rename({'DEPOSIT($)':"Amount"}, axis='columns',inplace=True)
    incoming.drop(['WITHDRAWAL($)'],axis=1,inplace=True)
    in_df = pd.concat([in_df,incoming],ignore_index=True)
    return in_df, out_df

def get_paylah_raw_data(FILE_NAME,num_pages):
    # Get data from the first page 
    dfs_page1 = tabula.read_pdf(FILE_NAME, pages="1", silent=True, guess = True, stream = False, multiple_tables=False, area=[225,51,796,551])[0]
    dfs_page1["Date"] = pd.NA
    dfs_page1["Description"] = pd.NA
    # Define a clean up date description column, splitting them into separate columns
    def process_row(row):
        if isinstance(row["DATE DESCRIPTION"],str) and  re.match(r'(\d+\s+\w+)', row["DATE DESCRIPTION"]):
            date, description = re.match(r'(\d+\s+\w+)\s+(.*)', row["DATE DESCRIPTION"]).groups()
            row["Date"] = date
            row["Description"] = description
        elif isinstance(row["DATE DESCRIPTION"],str) and row["DATE DESCRIPTION"].startswith("REF NO:"):
            # If the column starts with REF NO, fill Date with NA and Description with current column value
            row["Date"] = pd.NA
            row["Description"] = row["DATE DESCRIPTION"]
        else:
            # If neither condition is met, drop the row
            row["Date"] = pd.NA
            row["Description"] = pd.NA
        return row
    # Apply the function to each row using apply() function
    dfs_page1 = dfs_page1.apply(process_row, axis=1)
    # Drop columns
    dfs_page1.drop(columns=["DATE DESCRIPTION"], inplace=True)
    dfs_page1.dropna(subset=["Description"], inplace = True)
    columns_to_drop = [col for col in dfs_page1.columns if col.startswith('Unnamed')]
    dfs_page1.drop(columns=columns_to_drop, inplace=True)
    # Get data from remaining pages
    dfs_others = pd.DataFrame(columns=["Date", "Description","AMOUNT(S$)"])
    for page_num in range(2,num_pages+1):
        df = tabula.read_pdf(FILE_NAME, pages=page_num, silent=True, guess = True, stream = False, multiple_tables=False)
        if df:
            df = df[0]
            df.columns = dfs_others.columns
            if not df.empty:
                dfs_others = pd.concat([dfs_others, df], ignore_index=True)
    # Concatenate the first page data with the other pages 
    dfs = pd.concat([dfs_page1,dfs_others]).reset_index(drop=True)
    return dfs

def get_paylah_cleaned_data(df_paylah):
    # # Get if amount is DB/CR 
    def assign_cr_db(x):
        if isinstance(x,str) and x[-2:] == 'CR':
            return 'CR'
        if isinstance(x,str) and x[-2:] == 'DB':
            return 'DB'
        if pd.isna(x):
            return x
    def clean_amount(x):
        if isinstance(x,str) and x[-2:] == 'CR':
            return x[:-2]
        elif isinstance(x,str) and x[-2:] == 'DB':
            return x[:-2]
        else:
            return x
    df_paylah["DB/CR"] = df_paylah["AMOUNT(S$)"].apply(assign_cr_db)
    df_paylah["AMOUNT(S$)"] = df_paylah["AMOUNT(S$)"].apply(clean_amount)
    df_copy = df_paylah.copy()
    # Create 'Ref No' column with default values
    df_copy['Ref No'] = np.nan
    i, n = 0, len(df_copy)
    # Combine ref no and transaction details
    while i < n:
        if isinstance(df_copy.iloc[i]["Description"], str) and df_copy.iloc[i]["Description"].startswith("REF NO:"):
            df_copy.loc[i-1, 'Ref No'] = df_copy.loc[i , 'Description']
            df_copy.drop(i,inplace=False)
        i += 1
    df_copy = df_copy[pd.notna(df_copy["AMOUNT(S$)"])]
    df_copy["Ref No"] = df_copy['Ref No'].str.split(".").str.get(1)
    df_copy = df_copy.reset_index(drop=True)
    return df_copy

def append_paylah_data(FILE_NAME, in_df, out_df):
    num_pages = get_num_pages(FILE_NAME)
    dfs_paylah = get_paylah_raw_data(FILE_NAME,num_pages)
    df_paylah = get_paylah_cleaned_data(dfs_paylah)

    # Drop any extra columns and rename existing columns
    df_paylah.drop(['Ref No'],axis=1,inplace=True)
    df_paylah.rename({'AMOUNT(S$)':"Amount"}, axis='columns',inplace=True)

    # Clean the data and remove unncessary transactions
    df_paylah = df_paylah[df_paylah['Description']!="TOP UP WALLET FROM MY ACCOUNT"]
    df_paylah['Category'] = df_paylah.apply(lambda x: categorise_transaction(x,paylah_categories), axis=1)

    # Split into incoming and outgoing funds dfs
    outgoing = df_paylah[df_paylah['DB/CR']=='DB'].copy()
    outgoing.drop(['DB/CR'],axis=1,inplace=True)
    out_df = pd.concat([out_df,outgoing],ignore_index=True)

    incoming = df_paylah[df_paylah['DB/CR']=='CR'].copy()
    incoming.drop(['DB/CR'],axis=1,inplace=True)
    in_df = pd.concat([in_df,incoming],ignore_index=True)
    return in_df, out_df

def get_uob_raw_data(FILE_NAME, numPages):
    dfs = pd.DataFrame()
    for page_num in range(3,numPages-1):
        df = tabula.read_pdf(FILE_NAME, pages=page_num, silent=True, guess = True, stream = False, multiple_tables=False, area=[147,46,744,560])[0]
        dfs = pd.concat([dfs, df]).reset_index(drop=True)
    columns_to_drop = [col for col in dfs.columns if col.startswith('Unnamed')]
    dfs.drop(columns=columns_to_drop, inplace=True)
    return dfs

def get_uob_cleaned_data(dfs): 
    def convert_date_format(date_str):
        # Split the date string into day and month abbreviation
        day, month_abbr = date_str.split()
        # Capitalize the first letter of the month abbreviation
        month_abbr = month_abbr.capitalize()
        return f"{day} {month_abbr}"

    ROWS, i = dfs.shape[0], 0
    res = pd.DataFrame(columns= dfs.columns)
    while i < ROWS:
        description = dfs.iloc[i]["Description"]
        if description != "BALANCE B/F" and pd.notna(dfs.iloc[i]["Date"]):
            newDescription = [str(dfs.iloc[i]["Description"])]
            curr_row = dfs.iloc[i].copy()
            i += 1
            while i < ROWS and pd.isna(dfs.iloc[i]["Date"]):
                description = dfs.iloc[i]["Description"]
                if pd.notna(description):  # Check if description is not NaN
                    newDescription.append(str(description))
                i += 1
            # Make the transactions look nicer for debit card transactions
            if newDescription[0] == "Misc DR-Debit Card":
                newDescription.pop(0)
                if newDescription:
                    curr_row["Date"] = convert_date_format(newDescription[0][:6])
                    newDescription.pop(0)
            elif newDescription[0] == "PAYNOW-FAST":
                newDescription.pop(1)
            curr_row["Description"] = ' '.join(newDescription)
            res = pd.concat([res, curr_row.to_frame().T])
        else:
            i += 1
    def is_date_valid(date_str):
        # Define the date pattern (assuming DD MMM format)
        date_pattern = r'\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        # Check if the date string matches the pattern
        return re.fullmatch(date_pattern, str(date_str)) is not None
    def filter_valid_dates(df):
        # Filter rows based on the validity of the "Date" column
        valid_dates_mask = df["Date"].apply(is_date_valid)
        return df[valid_dates_mask]
    # Filter out rows with invalid dates
    res_filtered = filter_valid_dates(res)
    return res_filtered

def append_uob_data(FILE_NAME, in_df, out_df):
    num_pages = get_num_pages(FILE_NAME)
    dfs_uob = get_uob_raw_data(FILE_NAME, num_pages)
    df_uob = get_uob_cleaned_data(dfs_uob)
    # Drop extra column
    df_uob.drop(['Balance'],axis=1,inplace=True)

    # Categorise
    df_uob['Category'] = df_uob.apply(lambda x: categorise_transaction(x,uob_categories), axis=1)

    # Split into incoming and outgoing funds dfs
    outgoing = df_uob[df_uob['Withdrawals'].notna()].copy()
    outgoing.rename({'Withdrawals':"Amount"}, axis='columns',inplace=True)
    outgoing.drop(['Deposits'],axis=1,inplace=True)
    out_df = pd.concat([out_df,outgoing],ignore_index=True)

    incoming = df_uob[df_uob['Withdrawals'].isna()].copy()
    incoming.rename({'Deposits':"Amount"}, axis='columns',inplace=True)
    incoming.drop(['Withdrawals'],axis=1,inplace=True)
    in_df = pd.concat([in_df,incoming],ignore_index=True)
    return in_df, out_df

def get_hsbc_raw_data(FILE_NAME, num_pages):
    page1_hsbc = tabula.read_pdf(FILE_NAME, pages="1", silent=False, guess = False, stream = True, multiple_tables=False, area=[242,49,558,382])[0]
    page1_hsbc.columns = ["Date Date Description", "Amount"]
    dfs_others = pd.DataFrame(columns=page1_hsbc.columns)
    # skips page 2 as it is usually some t&c page 
    for page_num in range(3,num_pages+1):
        df = tabula.read_pdf(FILE_NAME, pages=[page_num], silent=True, guess=False, stream=True, multiple_tables=True, area=[153, 39, 816, 382])[0]
        df.columns = ["Date Date Description", "Amount"]
        dfs_others = pd.concat([dfs_others, df], ignore_index=True)
    dfs = pd.concat([page1_hsbc,dfs_others])
    return dfs 

def get_hsbc_cleaned_data(dfs):
    dfs = dfs[pd.notna(dfs["Amount"])]
    dfs[["Post Date", "Trans Date", "Description"]] = dfs["Date Date Description"].str.extract(r'(\d+\s+\w+)\s+(\d+\s+\w+)\s+(.*)')
    dfs.drop("Date Date Description", axis=1, inplace=True)
    dfs.dropna(subset=['Description'], inplace=True)
    desired_order = ["Post Date", "Trans Date", "Description", "Amount"]
    dfs = dfs.reindex(columns = desired_order)
    def assign_cr_db(x):
        if x[-2:] == 'CR':
            return 'CR'
        else:
            return 'DB'
    def clean_amount(x):
        if x[-2:] == 'CR':
            return x[:-2]  
        else:
            return x
    dfs["DB/CR"] = dfs["Amount"].apply(assign_cr_db)
    dfs["Amount"] = dfs["Amount"].apply(clean_amount)
    dfs = dfs.reset_index(drop=True)
    return dfs

def append_hsbc_data(FILE_NAME, in_df, out_df):
    num_pages = get_num_pages(FILE_NAME)
    dfs_hsbc = get_hsbc_raw_data(FILE_NAME, num_pages)
    df_hsbc = get_hsbc_cleaned_data(dfs_hsbc)
    # Drop any extra columns and rename existing columns
    df_hsbc.drop(['Post Date'],axis=1,inplace=True)
    df_hsbc.rename({'Trans Date':"Date"}, axis='columns',inplace=True)
    # Add categories
    df_hsbc['Category'] = df_hsbc.apply(lambda x: categorise_transaction(x,hsbc_categories), axis=1)

    # Split into incoming and outgoing funds dfs
    outgoing = df_hsbc[df_hsbc['DB/CR']=='DB'].copy()
    outgoing.drop(['DB/CR'],axis=1,inplace=True)
    out_df = pd.concat([out_df,outgoing],ignore_index=True)

    incoming = df_hsbc[df_hsbc['DB/CR']=='CR'].copy()
    incoming.drop(['DB/CR'],axis=1,inplace=True)
    in_df = pd.concat([in_df,incoming],ignore_index=True)
    return in_df, out_df