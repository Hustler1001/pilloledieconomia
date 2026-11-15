# Pensioni 2027: rivalutazione da gennaio (INPS 11/11/2026); DDL Bilancio 2027 art.55 (AC 3174-bis) ancora in esame alla Camera.
# Fasce (puntomagazine 12/11/2026, UPB via informazionefiscale 13/11/2026): fino a 4 volte il minimo 100%; 4-5 volte 85%; poi 53/47/37/32%. Minimo 2026 611,85 EUR.
MIN=611.85; SOGLIA=round(MIN*4,2); assert SOGLIA==2447.40
INF=0.02
a=1000*INF; assert a==20 and a*13==260
assert 3000>SOGLIA and 3000<MIN*5          # fascia 4-5 volte: 85%
piena=3000*INF; ddl=round(3000*INF*0.85,2); assert piena==60 and ddl==51.0
TTS="tts_l_pensioni"; OUT="pillole_pensioni_gennaio_2027.mp4"; FRAMES=""; PART=None; MARK=(1,3,7)
FONTI="Esempio calcolato, inflazione 2% ipotetica · INPS 11/11/2026"
RATE_TTS="+10%"
def N(t): return dict(who="narr",wolf="x",narr="x",text=t)
def W(t): return dict(who="wolf",wolf="x",narr="x",text=t)
LINES=[
 N("^20|venti_euro al mese in più su una pensione da ^1.000|mille_euro? Da gennaio?"),
 W("Quasi. L'INPS dice che la ~rivalutazione parte dalla rata di gennaio. Ma la percentuale non è ancora ufficiale."),
 N("E quanto sarà?"),
 W("Per il ^2026|duemilaventisei era ^1,4%|uno_virgola_quattro_per_cento. Per il ^2027|duemilaventisette facciamo un esempio al ^2%|due_per_cento."),
 N("Quindi con mille euro?"),
 W("Mille per due per cento fa ^20|venti_euro al mese. In ^13|tredici mensilità sono ^260|duecentosessanta_euro lordi."),
 N("E se la pensione è più alta?"),
 W("Fino a ^2.447|duemilaquattrocentoquarantasette_euro lordi al mese la rivalutazione è ^100%|cento_per_cento. Sopra, nel progetto di manovra, scende."),
 N("Scende quanto?"),
 W("Con ^3.000|tremila_euro vale ^85%|ottantacinque_per_cento: ^51|cinquantuno_euro invece di ^60|sessanta."),
 N("Ma la manovra è già legge?"),
 W("No. È in ~esame alla Camera: i numeri possono cambiare."),
 N("Sei sotto o sopra ^2.447|duemilaquattrocentoquarantasette_euro? Scrivi ^A o ^B nei commenti, e dimmi cosa vuoi capire: lo spiego nel prossimo video!"),
]
CARDS=[
 dict(at=0,kind="big",tag="PENSIONI",pill="da gennaio 2027",big="+20 €",label="al mese su 1.000 € di pensione",label2="ipotesi inflazione 2%, non ufficiale",col="g"),
 dict(at=3,kind="compare",tag="PERCENTUALE",pill="non definitiva",sides=[dict(head="2026",big="1,4%",sub="rivalutazione provvisoria",col="y"),dict(head="2027",big="2%?",sub="solo un esempio",col="r")],foot="La percentuale ufficiale non c'è ancora"),
 dict(at=5,kind="big",tag="ALL'ANNO",pill="esempio calcolato",big="260 €",label="lordi su 1.000 € al mese",label2="20 € × 13 mensilità",col="g"),
 dict(at=7,kind="big",tag="FINO A",pill="2.447,40 € lordi",big="100%",label="rivalutazione piena",label2="sopra, nel progetto di manovra, scende",col="y"),
 dict(at=9,kind="compare",tag="PENSIONE 3.000 €",pill="ipotesi 2%",sides=[dict(head="AL 100%",big="60 €",sub="aumento mensile pieno",col="y"),dict(head="ALL'85%",big="51 €",sub="nel progetto di manovra",col="r")],foot="9 € in meno al mese"),
 dict(at=11,kind="big",tag="ATTENZIONE",pill="DDL Bilancio 2027",big="IN ESAME",label="la manovra non è ancora approvata",label2="i numeri possono cambiare",col="y"),
 dict(at=12,kind="END",head="Dove sei?",ab=[("A","Sotto 2.447 € lordi"),("B","Sopra 2.447 € lordi")],l1="Scrivi A o B nei commenti",l2="o cosa vuoi capire: lo spiego io"),
]
