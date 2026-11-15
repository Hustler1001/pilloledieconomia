#!/usr/bin/env python3
"""Formato 'lista' (approvato da Gen): card in alto, lupo grigio + ragazza bionda in basso (sprite 2D veri),
sottotitoli a 2 parole sopra i personaggi, barra di avanzamento. Ruoli: lei chiede, il lupo spiega sarcastico.
Uso: SPEC=l_complotto python3 build_lista.py [--preview t1,t2]
Va messo accanto a build_tempo.py e lupo_lib.py (pipeline-video-lupo), con sprites2d/ (vedi make_sprites.py). """
import os, sys, math, subprocess
os.environ.setdefault("SPEC", "l_complotto")
import build_tempo as bt
from build_tempo import *
bt.VOICES = {"narr": "it-IT-ElsaNeural", "wolf": "it-IT-DiegoNeural"}
bt.PITCH = {"narr": "+0Hz", "wolf": "+0Hz"}
S = bt.S
if hasattr(S, 'RATE_TTS'): bt.RATE = S.RATE_TTS
SP = os.path.join(WORK, "sprites2d")
def ld(n): return Image.open(os.path.join(SP, n + ".png")).convert("RGBA")
WOLF = [ld("w0"), ld("w1"), ld("w2")]; NARR = [ld("n0"), ld("n1")]
SC = 0.56
def sc(im): return im.resize((int(im.width * SC), int(im.height * SC)), Image.LANCZOS)
WOLF = [sc(x) for x in WOLF]; NARR = [sc(x) for x in NARR]
CHAR_BOTTOM = 1735
NAVY0, NAVY1 = (10, 14, 40), (24, 34, 92)
def make_bg():
    a = np.zeros((H, W, 3), np.float32)
    for c in range(3): a[:, :, c] = np.linspace(NAVY0[c], NAVY1[c], H)[:, None]
    return Image.fromarray(a.astype(np.uint8))
BG = make_bg()
CARD_BOX = (72, 216, 1008, 1064)
CARD_FILL = (16, 18, 40); CARD_BORDER = (70, 80, 130); GREEN = (52, 211, 153)
CARDS = S.CARDS
NSEG = len([c for c in CARDS if c["kind"] != "END"])

def wrap(d, text, fnt, maxw):
    words = text.split(" "); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=fnt) <= maxw: cur = t
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def ctext(d, cx, y, text, fnt, fill):
    w_ = d.textlength(text, font=fnt); d.text((cx - w_ / 2, y), text, font=fnt, fill=fill)

COL = dict(y=YEL, r=RED, g=GREEN, w=WHITE, p=PURPLE)

def paper(size, rot, title, big, bigcol, sub, stamp=None, stamp_k=0):
    w_, h_ = size; im = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w_ - 1, h_ - 1), radius=26, fill=(250, 243, 225), outline=(214, 204, 176), width=3)
    d.text((34, 26), title, font=font(F_FRED6, 34), fill=(150, 140, 120))
    d.line([(34, 78), (w_ - 34, 78)], fill=(190, 180, 150), width=3)
    fb = font(F_FRED7, 84)
    while d.textlength(big, font=fb) > w_ - 60 and fb.size > 40: fb = font(F_FRED7, fb.size - 4)
    ctext(d, w_ / 2, 110, big, fb, bigcol)
    fs = font(F_FRED5, 34)
    for i, l in enumerate(wrap(d, sub, fs, w_ - 70)): ctext(d, w_ / 2, 215 + 42 * i, l, fs, (90, 86, 100))
    if stamp and stamp_k > 0:
        fz = font(F_MONT9, 58); tw = d.textlength(stamp, font=fz)
        st = Image.new("RGBA", (int(tw + 60), 110), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((0, 0, st.width - 1, 109), radius=14, outline=(200, 50, 60, 230), width=8)
        sd.text((30, 22), stamp, font=fz, fill=(200, 50, 60, 230))
        st = st.rotate(-9, expand=True, resample=Image.BICUBIC)
        k = clamp(stamp_k); sc_ = 1.6 - 0.6 * ease_out_cubic(k)
        st = st.resize((int(st.width * sc_), int(st.height * sc_)), Image.LANCZOS)
        st.putalpha(st.getchannel("A").point(lambda v: int(v * clamp(k * 2.5))))
        im.alpha_composite(st, ((w_ - st.width) // 2, h_ - st.height - 40))
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)

def card_content(c, lt, idx, t_abs):
    cw, ch = CARD_BOX[2] - CARD_BOX[0], CARD_BOX[3] - CARD_BOX[1]
    L = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    k = c["kind"]
    if k == "END" and c.get("ab"):
        ctext(d, cw / 2, 90, c.get("head", "Tu quale scegli?"), font(F_FRED6, 64), (230, 236, 255))
        bw, bh, gp = 396, 300, 50
        for j, (letter, txt) in enumerate(c["ab"][:2]):
            t0 = 0.3 + 0.7 * j
            if lt < t0: continue
            a = clamp(ease_out_back((lt - t0) / 0.4), 0, 1.1)
            x = (cw - 2 * bw - gp) // 2 + j * (bw + gp)
            box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            col = COL["y" if j == 0 else "r"]
            bd.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=34, fill=(24, 30, 66), outline=col, width=6)
            ctext(bd, bw / 2, 18, letter, font(F_MONT9, 110), col)
            fs = font(F_FRED6, 38)
            for i, l in enumerate(wrap(bd, txt, fs, bw - 50)[:3]): ctext(bd, bw / 2, 170 + 42 * i, l, fs, WHITE)
            box = box.resize((max(1, int(bw * a)), max(1, int(bh * a))), Image.LANCZOS)
            L.alpha_composite(box, (x + (bw - box.width) // 2, 220 + (bh - box.height) // 2))
        ctext(d, cw / 2, 590, c.get("l1", "Scrivi A o B nei commenti"), font(F_FRED7, 56), WHITE)
        ctext(d, cw / 2, 680, c.get("l2", "e nel prossimo video ti dico il conto"), font(F_FRED6, 42), (200, 210, 235))
        ctext(d, cw / 2, 780, "Esempi ipotetici: non è consulenza finanziaria", font(F_FRED5, 29), (150, 160, 200))
        return L, True
    if k == "END":
        ctext(d, cw / 2, 120, c.get("head", "Cosa ti spiego dopo?"), font(F_FRED6, 64), (230, 236, 255))
        ctext(d, cw / 2, 290, c.get("l1", "Scrivilo nei commenti"), font(F_FRED7, 66), WHITE)
        pw = int(clamp((lt - 0.3) / 0.5) * 740)
        if pw > 10:
            d.rounded_rectangle((cw / 2 - pw / 2, 390, cw / 2 + pw / 2, 600), radius=105, fill=YEL)
            if pw > 700:
                ptxt = c.get("pilltxt", "TUA SCELTA"); fp = font(F_MONT9, 118)
                while d.textlength(ptxt, font=fp) > 660 and fp.size > 30: fp = font(F_MONT9, fp.size - 4)
                ctext(d, cw / 2, 438 + (118 - fp.size) * 0.5, ptxt, fp, (40, 34, 20))
        ctext(d, cw / 2, 665, c.get("l2", "e lo spiego nel prossimo video"), font(F_FRED6, 46), WHITE)
        ctext(d, cw / 2, 780, "Esempi ipotetici: non è consulenza finanziaria", font(F_FRED5, 29), (150, 160, 200))
        return L, True
    d.text((42, 28), c.get("tag", ""), font=font(F_FRED7, 78), fill=YEL)
    if c.get("pill"):
        p = pill(c["pill"], fnt=font(F_FRED5, 30), color=(170, 180, 240), fill=(16, 18, 40), pad=(24, 10))
        L.alpha_composite(p, (cw - p.width - 42, 52))
    if k == "big":
        fb = font(F_MONT9, 170)
        while d.textlength(c["big"], font=fb) > cw - 100 and fb.size > 60: fb = font(F_MONT9, fb.size - 6)
        s_ = clamp(ease_out_back(lt / 0.5), 0, 1.1)
        big = Image.new("RGBA", (cw, 240), (0, 0, 0, 0)); ImageDraw.Draw(big).text((cw / 2 - d.textlength(c["big"], font=fb) / 2, 20), c["big"], font=fb, fill=COL[c.get("col", "y")])
        f = 1.0
        if idx == 0:
            f += 0.10 * math.sin(math.pi * clamp((t_abs - 0.4) / 0.6)) + 0.05 * math.sin(math.pi * clamp((t_abs - 1.6) / 0.6))
        w0, h0 = max(1, int(cw * f)), max(1, int(240 * max(s_, .01) * f))
        bigr = big.resize((w0, h0), Image.LANCZOS)
        tmp = Image.new("RGBA", (cw, 320), (0, 0, 0, 0)); tmp.paste(bigr, ((cw - w0) // 2, (320 - h0) // 2), bigr)
        L.alpha_composite(tmp, (0, 180))
        if lt > 0.8: ctext(d, cw / 2, 520, c["label"], font(F_FRED6, 44), WHITE)
        if c.get("label2") and lt > 1.2: ctext(d, cw / 2, 590, c["label2"], font(F_FRED5, 38), (190, 200, 230))
    elif k == "compare":
        bw, bh, gp = 396, 400, 50
        for j, side in enumerate(c["sides"]):
            t0 = 0.25 + 0.9 * j
            if lt < t0: continue
            a = clamp(ease_out_back((lt - t0) / 0.4), 0, 1.1)
            x = (cw - 2 * bw - gp) // 2 + j * (bw + gp)
            box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            col = COL[side.get("col", "y")]
            bd.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=34, fill=(24, 30, 66), outline=col, width=6)
            ctext(bd, bw / 2, 30, side["head"], font(F_FRED7, 42), col)
            fb = font(F_MONT9, 78)
            while bd.textlength(side["big"], font=fb) > bw - 40 and fb.size > 36: fb = font(F_MONT9, fb.size - 4)
            ctext(bd, bw / 2, 120, side["big"], fb, WHITE)
            fs = font(F_FRED5, 33)
            for i, l in enumerate(wrap(bd, side["sub"], fs, bw - 50)): ctext(bd, bw / 2, 245 + 42 * i, l, fs, (200, 210, 235))
            box = box.resize((max(1, int(bw * a)), max(1, int(bh * a))), Image.LANCZOS)
            L.alpha_composite(box, (x + (bw - box.width) // 2, 190 + (bh - box.height) // 2))
        if c.get("foot") and lt > 1.8: ctext(d, cw / 2, 640, c["foot"], font(F_FRED6, 42), WHITE)
    elif k == "stamp":
        pp = paper((760, 520), 3, c["doc"], c["big"], (30, 30, 60), c["label"], stamp=c["stamp"], stamp_k=(lt - 0.9) / 0.35)
        s_ = clamp(ease_out_back(lt / 0.5), 0, 1.1)
        pp = pp.resize((max(1, int(pp.width * s_)), max(1, int(pp.height * s_))), Image.LANCZOS)
        L.alpha_composite(pp, ((cw - pp.width) // 2, 150 + (520 - pp.height) // 2))
    elif k == "bars":
        base_y, maxh, bw = 560, 330, 250
        for j, b in enumerate(c["bars"]):
            t0 = 0.3 + 0.8 * j
            if lt < t0: continue
            p = ease_out_cubic((lt - t0) / 0.9); h_ = max(8, maxh * b["h"] * p); x = [120, 566][j]
            d.rounded_rectangle((x, base_y - h_, x + bw, base_y), radius=22, fill=COL[b.get("col", "y")])
            ctext(d, x + bw / 2, base_y - h_ - 62, b["val"], font(F_FRED7, 52), WHITE)
            ctext(d, x + bw / 2, base_y + 16, b["name"], font(F_FRED6, 38), (210, 220, 245))
        d.line([(80, base_y), (cw - 80, base_y)], fill=(80, 95, 140), width=4)
        if c.get("foot") and lt > 2.0: ctext(d, cw / 2, 700, c["foot"], font(F_FRED7, 48), YEL)
    if c.get("cap"):
        fc = font(F_FRED6, 42)
        for i, l in enumerate(wrap(d, c["cap"], fc, cw - 120)): ctext(d, cw / 2, 700 + 52 * i + (40 if k == "big" else 0), l, fc, WHITE)
    ctext(d, cw / 2, ch - 64, S.FONTI, font(F_FRED5, 27), (120, 130, 170))
    return L, False

def draw_header(f, d, t, cur_card, ncur, end):
    shadow_text(f, (W / 2 - d.textlength("Pillole di Economia", font=font(F_FRED7, 54)) / 2, 118), "Pillole di Economia", font(F_FRED7, 54), YEL, stroke=0)
    d.line([(450, 138), (630, 138)], fill=YEL, width=6)
    gap = 12; x0 = 70; n = NSEG + 1; segw = (940 - gap * (n - 1)) / n
    for i in range(n):
        done = 1.0 if (end or i < ncur) else (0.0 if i > ncur else clamp((t - cur_card[1]) / max(0.1, cur_card[2])))
        x = x0 + i * (segw + gap)
        d.rounded_rectangle((x, 168, x + segw, 184), radius=8, fill=(62, 72, 120))
        if done > 0.01: d.rounded_rectangle((x, 168, x + max(16, segw * done), 184), radius=8, fill=YEL)

def render(tl, total, t):
    f = BG.copy(); d = ImageDraw.Draw(f)
    L = active_line(tl, t); speaker = L["who"] if L and t <= L["end"] + 0.12 else None
    starts = [tl[c["at"]]["start"] + 0.1 for c in CARDS]
    ci = 0
    for j, s_ in enumerate(starts):
        if t >= s_: ci = j
    c = CARDS[ci]; lt = t - starts[ci]
    end = c["kind"] == "END"
    nxt = starts[ci + 1] if ci + 1 < len(starts) else total
    draw_header(f, d, t, (ci, starts[ci], nxt - starts[ci]), ci, end)
    d.rounded_rectangle(CARD_BOX, radius=52, fill=CARD_FILL, outline=GREEN if end else CARD_BORDER, width=5)
    layer, _ = card_content(c, max(0, lt) if ci > 0 else max(lt, 2.2), ci, t)
    a = clamp(lt / 0.2)
    if a < 0.999 and ci > 0: layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    f.paste(layer, CARD_BOX[:2], layer)
    def mouth(who):
        if speaker != who or not L: return 0
        lt_ = t - L["start"]
        for (a_, b_) in L["words"]:
            if a_ - 0.02 <= lt_ <= b_ + 0.03:
                ph = int((lt_ - a_) * 11) % 4
                return [2, 1, 2, 1][ph] if who == "wolf" else [1, 0, 1, 0][ph]
        return 0
    bw_ = 5 * math.sin(2 * math.pi * t / 2.0) if speaker == "wolf" else 2 * math.sin(2 * math.pi * t / 3.0)
    bn_ = 5 * math.sin(2 * math.pi * t / 2.0 + 1) if speaker == "narr" else 2 * math.sin(2 * math.pi * t / 3.2 + 1)
    chars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    w_im = WOLF[mouth("wolf")]; n_im = NARR[mouth("narr")]
    chars.alpha_composite(w_im, (-70, int(1100 - 143 * SC + bw_)))
    chars.alpha_composite(n_im, (W - n_im.width + 55 - 27, int(1100 - 57 * SC + bn_)))
    ca = np.array(chars.getchannel("A"), dtype=np.float32)
    ramp = np.clip((CHAR_BOTTOM - np.arange(H)) / (CHAR_BOTTOM - 1640), 0, 1)[:, None]
    chars.putalpha(Image.fromarray((ca * ramp).astype(np.uint8)))
    f.paste(chars, (0, 0), chars)
    if L and L["start"] <= t <= L["end"] + 0.25:
        lt_ = t - L["start"]; shown = None
        for ch in chunk_tokens(L["toks"]):
            if lt_ >= ch[0]["t0"] - 0.03: shown = ch
        if shown: draw_sub(f, shown)
    return f

def draw_sub(frame, toks):
    d = ImageDraw.Draw(frame); fnt = font(F_FRED7, 92); gap = 24
    widths = [d.textlength(k["disp"], font=fnt) for k in toks]; total = sum(widths) + gap * (len(toks) - 1)
    while total > 980 and fnt.size > 60:
        fnt = font(F_FRED7, fnt.size - 4); widths = [d.textlength(k["disp"], font=fnt) for k in toks]; total = sum(widths) + gap * (len(toks) - 1)
    x = (W - total) / 2
    for k, w_ in zip(toks, widths):
        shadow_text(frame, (x, 1650), k["disp"], fnt, k["color"] or WHITE, stroke=8); x += w_ + gap

def music(n, total, seed=3):
    """Base musicale originale generata: pluck arpeggiati su Am-F-C-G + beat leggero (104 bpm)."""
    rng = np.random.default_rng(seed); bpm = 104; step = 60 / bpm / 2
    prog = [(57, [0, 3, 7]), (53, [0, 4, 7]), (60, [0, 4, 7]), (55, [0, 4, 7])]
    out = np.zeros(n, dtype=np.float32)
    def hz(m): return 440 * 2 ** ((m - 69) / 12)
    def pluck(m, dur, amp):
        L = int(dur * SR); tt = np.arange(L) / SR; f0 = hz(m)
        y = sum(a * np.sin(2 * np.pi * f0 * k * tt) for k, a in ((1, 1), (2, .35), (3, .12)))
        y = y * np.exp(-tt * 5.5) * np.minimum(1, tt / 0.004); return (y * amp).astype(np.float32)
    def add(sig, t0):
        s_ = int(t0 * SR)
        if s_ < n: out[s_:s_ + len(sig)] += sig[: n - s_]
    t = 0.0; k = 0; pat = [0, 2, 1, 2, 0, 2, 1, 2]
    while t < total:
        root, iv = prog[(k // 8) % 4]; notes = [root + 12 + i for i in iv]
        add(pluck(notes[pat[k % 8] % 3] + (12 if pat[k % 8] == 1 and k % 16 == 5 else 0), 0.7, 0.5), t)
        if k % 8 == 0: add(pluck(root - 12, 1.6, 0.9), t)
        if k % 2 == 0:
            L = int(0.22 * SR); tt = np.arange(L) / SR; add((np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14) * 0.55).astype(np.float32), t)
        else:
            L = int(0.05 * SR); add(rng.standard_normal(L).astype(np.float32) * np.exp(-np.arange(L) / SR * 90) * 0.12, t)
        t += step; k += 1
    tt = np.arange(n) / SR
    env = np.minimum(1, tt / 1.5) * np.minimum(1, np.maximum(0, total - tt) / 2.0)
    return out * env / (np.abs(out).max() + 1e-9)

def build_audio2(tl, total, path):
    n = int((total + 0.2) * SR); mix = np.zeros(n, dtype=np.float32)
    for L in tl:
        a = decode_mp3(os.path.join(TTS_DIR, f"line{L['i']}.mp3")); s = int(L["start"] * SR); mix[s:s + len(a)] += a[: n - s]
    vp = np.abs(mix).max(); m = music(n, total)
    gain = np.full(n, 1.0, dtype=np.float32)
    for L in tl: gain[int(L["start"] * SR):int(L["end"] * SR)] = 0.55
    k = np.ones(int(0.15 * SR)) / int(0.15 * SR); gain = np.convolve(gain, k, mode="same").astype(np.float32)
    mix += m * gain * 0.20 * vp
    for tm in (0.2, MARKS["g0"] - 0.1, MARKS["f0"], total - 6):
        s_ = int(tm * SR); w = whoosh(0.5, seed=int(tm * 10) % 997) * 0.08 * vp; mix[s_:s_ + len(w)] += w[: n - s_]
    mix = np.clip(mix, -1, 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())

def check_hook():
    import re
    if "--no-hook-check" in sys.argv: return
    first = S.CARDS[0]
    shown = first.get("big", "") if first["kind"] == "big" else " ".join(s.get("big", "") for s in first.get("sides", []))
    errs = []
    if first.get("at", 0) != 0 or first["kind"] not in ("big", "compare") or not re.search(r"\d", shown):
        errs.append("la prima card (at=0) deve essere big o compare con una cifra")
    if not re.search(r"\^[^\s|]*\d", S.LINES[0]["text"]):
        errs.append("la prima battuta deve contenere una cifra evidenziata (^)")
    if re.match(r"\s*(parte|episodio|ep\.?)\s*\d", S.LINES[0]["text"].replace("^", "").replace("~", ""), re.I):
        errs.append("la prima battuta non deve aprire con etichette tipo 'Parte 1/2'")
    if not any(re.search(r"\^[^\s|]*\d", L["text"]) for L in S.LINES[:2]):
        errs.append("cifra evidenziata (^) richiesta entro le prime 2 battute (~8 s)")
    if not getattr(S, "FONTI", ""):
        errs.append("manca FONTI (ente + data) nello spec")
    end = [c for c in S.CARDS if c["kind"] == "END"]
    if not end or not end[-1].get("ab"):
        print("[avviso] la card finale non usa la domanda A/B")
    if errs: raise SystemExit("[gancio] " + "; ".join(errs))
    print("[gancio] ok")

def main():
    check_hook()
    tl, total = build_timeline()
    print(f"[timeline] {total:.1f}s")
    if "--preview" in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index("--preview") + 1].split(",")]
        frames = [render(tl, total, t) for t in ts]
        cols = min(len(frames), 4); rows = math.ceil(len(frames) / cols); sw, sh = 405, 720
        sheet = Image.new("RGB", (sw * cols, sh * rows))
        for k, fr in enumerate(frames): sheet.paste(fr.resize((sw, sh), Image.LANCZOS), ((k % cols) * sw, (k // cols) * sh))
        sheet.save(os.path.join(WORK, "preview_sheet.png")); return
    wav = os.path.join(WORK, "audio_" + S.TTS + ".wav"); build_audio2(tl, total, wav)
    out = os.path.join(OUT_DIR, S.OUT)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-i", wav,
           "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-movflags", "+faststart", "-shortest", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); n = int(total * 30)
    for i in range(n):
        p.stdin.write(render(tl, total, i / 30).tobytes())
        if i % 300 == 0: print(f" frame {i}/{n}", flush=True)
    p.stdin.close(); p.wait(); print("fatto:", out)
if __name__ == "__main__": main()
