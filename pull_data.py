############
# This script pulls WoW AH data from my dropbox to my machine, where
# I'm building a database of this data. 
############
import os
from datetime import datetime
import pandas as pd
import dropbox
from decouple import config
import pandas
import sqlite3
print('after imports')
DROPBOX_ACCESS = config('DROPBOX_ACCESS')
dbx = dropbox.Dropbox(DROPBOX_ACCESS)
print('connect to dbx')
# Had some issues with this script. The only workaround I could find
# was to specify the full directory path.
main_dir = 'F:/Documents/WoWAH_py/WoWAH_python/'
# Download csvs from dropbox
# These go in the temp_csvs folder until they're added to the databse
# then they're deleted
db_files = dbx.files_list_folder("")
print('got dbx files')
for i in db_files.entries:
    with open(main_dir + 'data/temp_csvs/'+ i.name, "wb") as f:
        metadata, res = dbx.files_download(i.path_lower)
        f.write(res.content)
    print('This file downloaded' + i.name)
print('all dbx files downloaded')

# Connect to database and add csvs
conn = sqlite3.connect(main_dir + 'data/WoWAH_db.sqlite')
print('connected to db')
ah_csvs = os.listdir(main_dir + 'data/temp_csvs')
curs = conn.cursor() # Create cursor w/e that is
print('cursor made')
for i in ah_csvs:
    temp_file = pandas.read_csv(main_dir + 'data/temp_csvs/' + i)
    temp_file['id'] = temp_file['id'].map(str)
    temp_file['date_time'] = pd.to_datetime(temp_file['date_time'])
    temp_file.to_sql('auctions', conn, if_exists='append', index = False)
print('files written to dropbox')
print('Finished pulling from dropbox' + datetime.now().strftime('Malfurion_NA-%Y-%m-%d-%H-%M'))
# Once files are in the database, go ahead and delete from dropbox
for i in db_files.entries:
    dbx.files_delete("/" + i.name)
print('Finished deleting from dropbox' + datetime.now().strftime('Malfurion_NA-%Y-%m-%d-%H-%M'))
# And delete  csvs
for i in ah_csvs:
    os.remove(main_dir + 'data/temp_csvs/' + i)
print('Finished deleting from computer' + datetime.now().strftime('Malfurion_NA-%Y-%m-%d-%H-%M'))

# Write a csv to file that contains the most recent 2 (4?) weeks of data
query = curs.execute("""
    SELECT auctions.auction_id,
        auctions.quantity,
        auctions.time_left,
        auctions.date_time,
        auctions.cost_g,
        item_id.name,
        item_id.is_stackable,
        item_id.is_equippable
    FROM auctions
    LEFT JOIN item_id ON auctions.id = item_id.id
    WHERE date_time BETWEEN datetime('now', '-1 month') and datetime('now', 'localtime')
    """)
cols = [column[0] for column in query.description]
results = pd.DataFrame.from_records(data = query.fetchall(), columns = cols)
results.to_csv(main_dir + '/data/latest_month_auctions.csv', index = False)
# Write a smaller version of the data to upload with the app as a test
query = curs.execute("""
    SELECT auctions.auction_id,
        auctions.quantity,
        auctions.time_left,
        auctions.date_time,
        auctions.cost_g,
        item_id.name,
        item_id.is_stackable,
        item_id.is_equippable
    FROM auctions
    LEFT JOIN item_id ON auctions.id = item_id.id
    WHERE date_time BETWEEN datetime('now', '-1 month') and datetime('now', 'localtime')
    AND name IN ('Rising Glory',
            'Widowbloom',
            'Marrowroot',
            "Vigil's Torch",
            'Death Blossom',
            'Nightshade',
            'Laestrite Ore',
            'Elethium Ore',
            'Solenium Ore',
            'Oxxein Ore',
            'Phaedrum Ore',
            'Sinvyr Ore',
            'Angerseye',
            'Oriblase',
            'Umbryl',
            'Desolate Leather',
            'Callous Hide',
            'Pallid Bone',
            'Gaunt Sinew',
            'Heavy Desolate Leather',
            'Heavy Callous Hide',
            'Shrouded Cloth',
            'Lightless Silk',
            'Soul Dust',
            'Sacred Shard',
            'Eternal Crystal')
    """)
cols = [column[0] for column in query.description]
results = pd.DataFrame.from_records(data = query.fetchall(), columns = cols)
results.to_csv(main_dir + 'wowah_app/app_data/latest_month_auctions.csv', index = False)

conn.close()
