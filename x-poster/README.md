# x-lupo-poster
Pubblica su X (@lupo_dei_soldi) i post in `queue/*.json`. Nessuna chiave nel codice: stanno nelle variabili di Railway
(X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET). Stato su volume /data.
Formato coda: [{"id","when"(ISO con fuso),"text","images":["img/x.png"],"thread":[{"text","images"}]}]
Regole: niente link (0,20 $/post), max 280 caratteri, niente like/follow/DM automatici.
