"""Aggiorna stats.json con i numeri pubblici di TikTok, Twitch e Discord.

Se una fonte non risponde tiene il valore precedente, così il sito non mostra
mai zero o numeri vuoti.
"""

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATS = Path(__file__).resolve().parent.parent / "stats.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def tiktok():
    html = get("https://www.tiktok.com/@itsme_officialttv")

    def num(key):
        # La pagina contiene il valore esatto tra virgolette e uno arrotondato senza
        m = re.search(r'"%s":"(\d+)"' % key, html) or re.search(r'"%s":(\d+)' % key, html)
        return int(m.group(1)) if m else None

    data = {"followers": num("followerCount"), "likes": num("heartCount"), "videos": num("videoCount")}
    return data if data["followers"] else None


def twitch():
    text = get("https://decapi.me/twitch/followcount/itsme_officialttv").strip()
    return {"followers": int(text)} if text.isdigit() else None


def discord():
    d = json.loads(get("https://discord.com/api/v10/invites/itsme?with_counts=true"))
    if not d.get("approximate_member_count"):
        return None
    return {"members": d["approximate_member_count"], "online": d["approximate_presence_count"]}


def main():
    stats = json.loads(STATS.read_text()) if STATS.exists() else {}
    changed = False
    for name, fetch in (("tiktok", tiktok), ("twitch", twitch), ("discord", discord)):
        try:
            value = fetch()
        except Exception as e:  # una fonte giù non deve fermare le altre
            print(f"{name}: errore {e}")
            continue
        if not value:
            print(f"{name}: nessun dato, tengo il valore precedente")
            continue
        print(f"{name}: {value}")
        if stats.get(name) != value:
            stats[name] = value
            changed = True
    if changed:
        stats["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        STATS.write_text(json.dumps(stats, indent=2) + "\n")


if __name__ == "__main__":
    main()
