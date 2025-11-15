import httpx
import asyncio
import sys
import os

async def worker(queue: asyncio.Queue, client: httpx.AsyncClient):
    while not queue.empty():
        url = await queue.get()
        if os.path.exists(url.split("/")[-1]):
            print(f"{url} already exists, skipping")
            queue.task_done()
            continue
        print(f"Downloading {url}")
        r = await client.get(url, follow_redirects=True, timeout=60)
        if r.status_code == 200:
            with open(url.split("/")[-1], "wb") as f:
                f.write(r.content)
        else:
            print(f"Failed to download {url}")
        print(f"Reminding {queue.qsize()} urls")
        queue.task_done()

async def main():
    urls = open(sys.argv[1], "r").read().splitlines()
    queue = asyncio.Queue()
    for url in urls:
        queue.put_nowait(url)
    async with httpx.AsyncClient() as client:
        workers = [worker(queue, client) for _ in range(10)]
        await asyncio.gather(*workers)
        await queue.join()

if __name__ == "__main__":
    asyncio.run(main())