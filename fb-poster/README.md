# fb-poster
Pubblica sulla Pagina Facebook i post della coda di X (x-poster/queue) il cui id contiene "complotto" (cambia con la variabile FB_FILTER; vuota = tutti).
Servono due segreti nel repo (Settings > Secrets > Actions): FB_PAGE_ID e FB_PAGE_TOKEN (token di Pagina con permesso pages_manage_posts, meglio a lunga durata).
Senza segreti non pubblica niente. Stato in fb-poster/state.json. Prova: DRY_RUN=1 python3 app.py
