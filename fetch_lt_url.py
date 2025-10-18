import os, time, re, requests, asyncio, subprocess
from dotenv import load_dotenv

load_dotenv()

def get_localtunnel_url():
    try:
        logs = subprocess.check_output(["docker", "logs", "localtunnel"], text=True)
        urls = re.findall(r"https://[a-z0-9-]+\.loca\.lt", logs)
        return urls[-1] if urls else None
    except Exception:
        return None

url = None
for _ in range(20):
    url = get_localtunnel_url()
    if url:
        break
    time.sleep(3)

if not url:
    exit(1)


lines = []
with open(".env") as f:
    for line in f:
        if line.startswith("WEBAPP_URL="):
            lines.append(f"WEBAPP_URL={url}/webapp\n")
        else:
            lines.append(line)
with open(".env", "w") as f:
    f.writelines(lines)


import bot
asyncio.run(bot.main())