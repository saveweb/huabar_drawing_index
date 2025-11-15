import httpx
from tqdm import tqdm

ITEMS = open(
    "huabar_items.txt", "r"
).read().splitlines()
ss = httpx.Client(follow_redirects=True)

class Asset:
    # TYPE: str # "ali" or "qiniu"
    KEY: str
    ZIP: str

    def __init__(self, KEY: str, ZIP: str):
        assert KEY and ZIP
        self.KEY = KEY
        self.ZIP = ZIP

def zip2identifier(zip: str) -> str:
    # qiniu-draw-20240124-050235.7653.zip.keys -> huabar_qiniu-draw-20240124-05
    # ali-draw-20240130-000635.2413.zip.keys -> huabar_ali-draw-20240130-00
    if zip.startswith("ali-draw-"):
        return "huabar_" + zip[:len("ali-draw-20240130-00")]
    elif zip.startswith("qiniu-draw-"):
        return "huabar_" + zip[:len("qiniu-draw-20240124-05")]
    else:
        raise ValueError("Unknown zip type")

zipurls = []

for identifier in tqdm(ITEMS):
    print(f"Processing {identifier}")
    item = ss.get(f"https://archive.org/metadata/{identifier}").json()
    for file in item["files"]:
        if file["name"].endswith(".zip.keys"):
            # Process the asset
            # ...
            print(f"Found {file['name']}, identifier: {zip2identifier(file['name'])}")
            assert zip2identifier(file['name']) == identifier
            zip_url = f"https://archive.org/download/{identifier}/{file['name']}"
            zipurls.append(zip_url)

with open("huabar_zipurls.txt", "w") as f:
    f.write("\n".join(zipurls))