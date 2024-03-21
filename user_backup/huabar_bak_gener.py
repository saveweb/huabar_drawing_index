import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
import urllib.parse

import httpx

from url_type import (
    A, Q, B, W,
    get_urltype
)

API_BASE = "http://localhost:8080/api/"

def is_keyable(url: str)->bool:
    if not url:
        return False
    return get_urltype(url) in [A, Q]

def get_key(url: str)->str:
    parsed = urllib.parse.urlparse(url)
    return parsed.path.lstrip("/").replace("haowanlab/", "")

def write_user_bak_meta(jid: str, notes: list[dict]):
    usr_dir = jid.split('@')[0]
    os.makedirs(f'{usr_dir}', exist_ok=True)

    with open(f'{usr_dir}/notes.json', 'w') as f:
        f.write(json.dumps(notes, ensure_ascii=False, indent=2))

async def download_to_bak(sem:asyncio.Semaphore, client:httpx.AsyncClient, ia_url, jid, key):
    usr_dir = jid.split('@')[0]
    path = f'{usr_dir}/notes_data/{key}'
    if os.path.exists(path):
        return
    os.makedirs(f'{usr_dir}/notes_data/', exist_ok=True)
    async with sem:
        print("downloading", key)
        r = await client.get(ia_url, follow_redirects=True)
        r.raise_for_status()
        with open(path, 'wb') as f:
            f.write(r.content)

async def get_zipname(client:httpx.AsyncClient, key:str):
    # qiniu-draw-20240127-072800.3565.zip
    # ali-draw-20240127-072800.3565.zip
    r = await client.get(API_BASE+"get_zipname", params={"key": key})
    r_json = r.json()
    if 'error' in r_json:
        print(r_json)
        return None
    return r_json["zipname"]

def zipname2identifier(zipname:str):
    # qiniu-draw-20240127-072800.3565.zip
    # ali-draw-20240127-072800.3565.zip
    # ->>
    # huabar_ali-draw-20240130-00
    # huabar_qiniu-draw-20240130-00
    sp = zipname.split('-')
    sp[3] = sp[3][:2]
    return 'huabar_' + '-'.join(sp)


async def main():
    jid = input("jid: ") # zeg97iab-0@zhizhiyaya.com/HuaLiao
    from_local = input("from_local:") # 0
    
    async with httpx.AsyncClient(timeout=60) as client:
        if from_local:
            with open(f'{jid.split("@")[0]}/notes.json', 'r') as f:
                notes = json.load(f)
        else:
            r = await client.get(API_BASE+"notes", params={"jid": jid})
            notes = r.json()
            write_user_bak_meta(jid, notes)
        await download_notes_data(client, jid, notes)
        gen_markdown(jid, notes)

def gen_markdown(jid, notes):
    usr_dir = jid.split('@')[0]
    os.makedirs(f'{usr_dir}', exist_ok=True)
    with open(f'{usr_dir}/notes.md', 'w') as f:
        f.write(f"""\
# {notes[0]['payload']['authorname']} 的画吧作品备份

```
jid: {jid}
注册时间: {notes[0]['payload']['registertime']}
作品数: {len(notes)}
(作品详细元数据见 notes.json)
```
""")
        for note in notes:
            noteid       = note["payload"]["noteid"]
            noteossurl   = note["payload"]["noteossurl"]
            original_url = note["payload"]["original_url"]
            notename     = note["payload"]["notename"]
            notestatus   = note["payload"]["notestatus"]
            notebrief   = note["payload"]["notebrief"]
            notetime     = note["payload"]["notetime"]
            strokecount = note["payload"]["strokecount"] # 画笔数
            width = note["payload"]["width"]
            high = note["payload"]["high"]
            usedcbnum = note["payload"]["usedcbnum"] # 含 X 款自定义笔刷
            praise = note["payload"]["praise"] # 收到的投花数
            comnum = note["payload"]["comnum"] # 评论数
            f.write(f"""\
---

```
作品ID: {noteid}
上传时间: {datetime.fromtimestamp(notetime, tz=timezone.utc).astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)
作品名: {notename}
作品状态: {"正常" if notestatus == 0 else "已删除" if notestatus == 2 else notestatus}
描述: {notebrief}
画笔数: {strokecount}
宽x高: {width}x{high}
自定义笔刷数: {usedcbnum}
投花数: {praise}
评论数: {comnum}
```

""")
            f.write("原图: ")
            if is_keyable(original_url):
                key = get_key(original_url)
                f.write(f"![{key}](notes_data/{key})"+'{loading="lazy"}\n\n')
            else:
                f.write(f"不可用 ({original_url})\n\n")
            f.write("原始工程文件: \n")
            if is_keyable(noteossurl):
                key = get_key(noteossurl)
                f.write(f"[{key}](notes_data/{key})\n\n")
            else:
                f.write(f"不可用 ({noteossurl})\n\n")

async def download_notes_data(client, jid, notes):
    sem = asyncio.Semaphore(10)
    cors = []
    for note in notes:
        noteossurl   = note["payload"]["noteossurl"]
        original_url = note["payload"]["original_url"]
        for url in [noteossurl, original_url]:
            if not url:
                continue
            urltype = get_urltype(url)
            if urltype in [A, Q]:
                key = get_key(url)
                zipname = await get_zipname(client, key)
                if not zipname:
                    print(url, key, "木有ZIP包")
                    continue
                identifier = zipname2identifier(zipname)
                # https://archive.org/download/huabar_qiniu-draw-20240120-18/qiniu-draw-20240120-184331.3072.zip/qiniu%2F0a3aab2963b53de19fc043182cfeee0d
                # https://archive.org/download/huabar_ali-draw-20240130-00/ali-draw-20240130-000635.2413.zip/ali%2F0b9274cd8384cc3d936d2341c7f7bdbd.data
                ia_url = f"https://archive.org/download/{identifier}/{zipname}/{urltype}/{key}"
                cors.append(
                    download_to_bak(sem=sem, client=client, ia_url=ia_url, jid=jid, key=key)
                )
            elif url == "http://huaba-operate.oss-cn-hangzhou.aliyuncs.com/deletepic.png":
                pass
            elif urltype == W:
                assert False, url
            elif urltype == B:
                assert False, url
    
    await asyncio.gather(*cors)

if __name__ == "__main__":
    asyncio.run(main())