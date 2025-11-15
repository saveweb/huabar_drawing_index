# huabar_draws_takeout

## requirements

1. Prepare those files:

```
- draws_index/db/huabar_draws.db
- draws_index/jid_authorname_map/jid_authorname_maped.csv
```

2. Start service

`docker compose up -d`

3. Install Python project and other dependencies

```
uv sync --locked
apt install pandoc zip -y
```

## Usage

`uv run takeout.py`

then enter the jid (user id).

the backup files will be generated in the ./user_backups/ folder.