import csv
from tqdm import tqdm
with open('jid_authorname.csv', 'r') as f:
    reader = csv.reader(f)
    # payload.jid,payload.authorname
    next(reader)
    jid_authorname_map = set()
    for row in tqdm(reader, total=19248404):
        jid_authorname_map.add((row[0], row[1]))
    print(len(jid_authorname_map)) # 1945064
with open('jid_authorname_maped.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerows(jid_authorname_map)