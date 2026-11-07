"""Pubblica sulla Pagina Facebook i post gia' messi in coda per X (x-poster/queue/*.json).
Per default pubblica solo quelli il cui id contiene FB_FILTER (default "complotto").
FB_FILTER="" pubblica tutti. Niente azioni su altri account: solo contenuti propri programmati."""
import glob, json, os, sys, time, datetime as dt
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE_GLOB = os.environ.get("QUEUE_GLOB", os.path.join(HERE, "..", "x-poster", "queue", "*.json"))
STATE_DIR = os.environ.get("STATE_DIR", HERE)
STATE_FILE = os.path.join(STATE_DIR, "state.json")
DRY = os.environ.get("DRY_RUN", "") == "1"
FILTER = os.environ.get("FB_FILTER", "complotto")
MAX_PER_DAY = int(os.environ.get("MAX_PER_DAY", "6"))
LATE_MAX_H = float(os.environ.get("LATE_MAX_H", "6"))
GRAPH = "https://graph.facebook.com/v21.0"

def log(*a):
    print(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)

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
    for f in sorted(glob.glob(QUEUE_GLOB)):
        try:
            for it in json.load(open(f)):
                if FILTER and FILTER not in it.get("id", ""):
                    continue
                it["_dir"] = os.path.dirname(f)
                items.append(it)
        except Exception as e:
            log("coda illeggibile", f, e)
    return items

def check_text(t):
    if not (t or "").strip():
        return "testo vuoto"
    if len(t) > 5000:
        return "oltre 5000 caratteri"
    return None

def post_fb(page_id, token, text, image_path):
    if image_path:
        with open(image_path, "rb") as fh:
            r = requests.post(f"{GRAPH}/{page_id}/photos", data={"message": text, "access_token": token},
                              files={"source": fh}, timeout=90)
    else:
        r = requests.post(f"{GRAPH}/{page_id}/feed", data={"message": text, "access_token": token}, timeout=60)
    if r.status_code == 200:
        j = r.json()
        return j.get("post_id") or j.get("id")
    raise RuntimeError(f"{r.status_code} {r.text[:300]}")

def publish(it, st, page_id, token):
    err = check_text(it.get("text"))
    if err:
        raise ValueError(err)
    imgs = it.get("images") or []
    path = os.path.join(it["_dir"], imgs[0]) if imgs else None
    if path and not os.path.exists(path):
        raise ValueError(f"immagine mancante: {path}")
    done = st["items"].setdefault(it["id"], {"ids": [], "attempts": 0})
    if DRY:
        log(f"[PROVA] {it['id']}: {it['text'][:80]!r} immagine={imgs[:1]}")
        done["ids"].append("dry")
    else:
        pid = post_fb(page_id, token, it["text"], path)
        done["ids"].append(pid)
        save_state(st)
        log(f"pubblicato {it['id']}: {pid}")
    done["done"] = True

def tick(page_id, token):
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
            publish(it, st, page_id, token)
            st["daily"][today] += 1
        except ValueError as e:
            st["items"][it["id"]]["failed"] = str(e); log("BLOCCATO", it["id"], e)
        except Exception as e:
            a = st["items"][it["id"]]; a["attempts"] = a.get("attempts", 0) + 1; a["last_error"] = str(e)[:400]
            log("ERRORE", it["id"], a["attempts"], e)
            if a["attempts"] >= 3:
                a["failed"] = str(e)[:200]
        save_state(st)

def main():
    page_id = os.environ.get("FB_PAGE_ID", "").strip()
    token = os.environ.get("FB_PAGE_TOKEN", "").strip()
    if not (page_id and token) and not DRY:
        log("ATTENZIONE: mancano FB_PAGE_ID e FB_PAGE_TOKEN: non pubblico niente")
        return
    log("avviato", "PROVA" if DRY else "REALE", "filtro:", repr(FILTER))
    tick(page_id, token)

if __name__ == "__main__":
    main()
