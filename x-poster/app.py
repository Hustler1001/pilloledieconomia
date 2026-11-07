"""Pubblica su X (@lupo_dei_soldi) i post messi in coda in queue/*.json.
Niente like, follow o DM automatici: solo contenuti propri programmati."""
import glob, json, os, re, sys, time, datetime as dt
import requests
from requests_oauthlib import OAuth1

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.environ.get("STATE_DIR", HERE)
STATE_FILE = os.path.join(STATE_DIR, "state.json")
DRY = os.environ.get("DRY_RUN", "") == "1"
MAX_PER_DAY = int(os.environ.get("MAX_PER_DAY", "6"))   # tetto di sicurezza
LATE_MAX_H = float(os.environ.get("LATE_MAX_H", "6"))   # non recupera post piu' vecchi di 6 ore
API = "https://api.x.com/2"

def log(*a):
    print(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)

def auth():
    k = [os.environ.get(n, "").strip() for n in ("X_CONSUMER_KEY", "X_CONSUMER_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")]
    if not all(k):
        return None
    return OAuth1(*k)

def load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {"items": {}, "daily": {}}

def save_state(s):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    json.dump(s, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, STATE_FILE)

def load_queue():
    items = []
    for f in sorted(glob.glob(os.path.join(HERE, "queue", "*.json"))):
        try:
            for it in json.load(open(f)):
                it["_dir"] = os.path.dirname(f)
                items.append(it)
        except Exception as e:
            log("coda illeggibile", f, e)
    return items

def check_text(t):
    if re.search(r"https?://|www\.|\.com\b|\.it/", t or ""):
        return "contiene un link (costa 0,20 $ a post): bloccato"
    if len(t or "") > 280:
        return "oltre 280 caratteri"
    if not (t or "").strip():
        return "testo vuoto"
    return None

def upload_image(oa, path):
    data = open(path, "rb").read()
    r = requests.post(f"{API}/media/upload", auth=oa, files={"media": data},
                      data={"media_category": "tweet_image"}, timeout=60)
    if r.status_code in (200, 201):
        j = r.json()
        return str((j.get("data") or j).get("id") or j.get("media_id_string"))
    r2 = requests.post("https://upload.twitter.com/1.1/media/upload.json", auth=oa,
                       files={"media": data}, timeout=60)
    if r2.status_code == 200:
        return r2.json()["media_id_string"]
    raise RuntimeError(f"upload immagine fallito: {r.status_code} {r.text[:200]} | {r2.status_code} {r2.text[:200]}")

def create_tweet(oa, text, media_ids=None, reply_to=None):
    body = {"text": text}
    if media_ids:
        body["media"] = {"media_ids": media_ids}
    if reply_to:
        body["reply"] = {"in_reply_to_tweet_id": reply_to}
    r = requests.post(f"{API}/tweets", auth=oa, json=body, timeout=30)
    if r.status_code in (200, 201):
        return r.json()["data"]["id"]
    raise RuntimeError(f"{r.status_code} {r.text[:300]}")

def publish(oa, it, st):
    parts = [{"text": it["text"], "images": it.get("images", [])}] + it.get("thread", [])
    done = st["items"].setdefault(it["id"], {"ids": [], "attempts": 0})
    prev = done["ids"][-1] if done["ids"] else None
    for i, p in enumerate(parts):
        if i < len(done["ids"]):
            continue
        err = check_text(p.get("text"))
        if err:
            raise ValueError(f"parte {i+1}: {err}")
        if DRY:
            log(f"[PROVA] {it['id']} parte {i+1}: {p['text'][:80]!r} immagini={p.get('images')}")
            done["ids"].append(f"dry{i}")
            prev = f"dry{i}"
            continue
        mids = [upload_image(oa, os.path.join(it["_dir"], im)) for im in p.get("images", [])[:4]]
        tid = create_tweet(oa, p["text"], mids, prev)
        done["ids"].append(tid)
        prev = tid
        save_state(st)           # subito, per non ripubblicare mai due volte
        log(f"pubblicato {it['id']} parte {i+1}: https://x.com/i/status/{tid}")
        time.sleep(2)
    done["done"] = True

def tick(oa):
    st = load_state()
    now = dt.datetime.now(dt.timezone.utc)
    today = now.strftime("%Y-%m-%d")
    st["daily"] = {today: st.get("daily", {}).get(today, 0)}
    for it in sorted(load_queue(), key=lambda x: x["when"]):
        s = st["items"].get(it["id"], {})
        if s.get("done") or s.get("failed"):
            continue
        when = dt.datetime.fromisoformat(it["when"])
        if when > now:
            continue
        if (now - when).total_seconds() > LATE_MAX_H * 3600:
            st["items"][it["id"]] = {"failed": "troppo in ritardo, saltato", "ids": s.get("ids", [])}
            log("saltato (troppo vecchio):", it["id"]); save_state(st); continue
        if st["daily"][today] >= MAX_PER_DAY:
            log("tetto giornaliero raggiunto"); break
        try:
            publish(oa, it, st)
            st["daily"][today] += 1
        except ValueError as e:
            st["items"][it["id"]]["failed"] = str(e); log("BLOCCATO", it["id"], e)
        except Exception as e:
            a = st["items"][it["id"]]; a["attempts"] = a.get("attempts", 0) + 1; a["last_error"] = str(e)[:400]
            log("ERRORE", it["id"], a["attempts"], e)
            if a["attempts"] >= 3:
                a["failed"] = str(e)[:200]
            if any(c in str(e) for c in ("402", "429")):
                save_state(st); break   # niente crediti o troppi tentativi: fermati
        save_state(st)

def main():
    oa = auth()
    if not oa and not DRY:
        log("ATTENZIONE: chiavi X mancanti (X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)")
    log("avviato", "PROVA" if DRY else "REALE", "stato:", STATE_FILE)
    last_beat = 0
    while True:
        if oa or DRY:
            try:
                tick(oa)
            except Exception as e:
                log("errore nel ciclo", e)
        if time.time() - last_beat > 3600:
            log("vivo; post in coda:", len(load_queue())); last_beat = time.time()
        if os.environ.get("ONCE") == "1":
            return
        time.sleep(60)

if __name__ == "__main__":
    main()
