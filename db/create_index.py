import os
import sqlite3
from tqdm import tqdm

DB_FILE = 'huabar_draws.db'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

def create_table():
    c.execute('CREATE TABLE IF NOT EXISTS huabar_draws (file_key TEXT, zipname TEXT)')
    conn.commit()

create_table()

# 两个字段：
# file_key, zipname
def create_index():
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_file_key_zipname ON huabar_draws (file_key, zipname)')
    conn.commit()

create_index()

def insert_data(data):
    try:
        c.executemany('INSERT INTO huabar_draws (file_key, zipname) VALUES (?, ?)', data)
        conn.commit()
    except sqlite3.IntegrityError:
        print('Duplicate entry found')

for keys_file in tqdm(os.listdir('./keys')):
    if not keys_file.endswith('.keys'):
        raise ValueError(f"Unexpected file {keys_file}")
    zipname = keys_file[:-5]
    assert zipname.endswith('.zip')
    data = []
    for key in open(f'keys/{keys_file}', 'r').read().splitlines():
        data.append((key, zipname))
    insert_data(data)


conn.close()