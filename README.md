# Pokretanje simulacije

## Instalacija

Prije pokretanja simulacije potrebno je instalirati Python ovisnosti navedene u datoteci `requirements.txt`.

U terminalu se iz direktorija projekta pokreće:

```bash
pip install -r requirements.txt
```

Nakon što su sve potrebne ovisnosti instalirane, simulacija se pokreće iz datoteke `main.py`.

### Pokretanje programa

Nakon instalacije potrebnih ovisnosti i konfiguracije parametara, program se pokreće pokretanjem datoteke `main.py`.

Primjer:

```bash
python main.py
```

Dakle, za pokretanje simulacije potrebno je:

1. Instalirati potrebne Python pakete iz `requirements.txt`.
2. Po potrebi promijeniti parametre simulacije.
3. Pokrenuti `main.py`.

---

## Konfiguracija GUI-ja

Grafičko sučelje nalazi se u datoteci `gui.py`. GUI omogućuje pokretanje simulacije bez potrebe za izravnim mijenjanjem parametara u kodu.

Prije pokretanja simulacije u GUI-ju potrebno je odabrati željene parametre.

### Broj ponavljanja (`runs`)

Određuje koliko će se puta svaka simulacija izvršiti.

Veći broj ponavljanja daje pouzdanije prosječne rezultate jer se rezultati računaju na temelju većeg broja simulacija, ali istovremeno povećava ukupno vrijeme izvođenja.

Primjer:

```text
Runs: 5
```

znači da će se svaka odabrana vrsta simulacije izvršiti pet puta.

### Težina PoW-a (`block_hash_difficulty`)

Određuje težinu Proof-of-Work rudarenja.

Vrijednost predstavlja broj vodećih nula koje valjani SHA-256 hash mora sadržavati.

Primjer:

```text
Difficulty: 4
```

znači da hash mora počinjati s četiri nule:

```text
0000................................
```

Povećanjem težine smanjuje se vjerojatnost pronalaska valjanog hasha, zbog čega PoW simulacija u pravilu zahtijeva veći broj hash pokušaja.

### Broj čvorova (`num_of_nodes`)

Određuje broj čvorova koji sudjeluju u simulaciji.

Svaki čvor ima vlastitu brzinu hashiranja (`hash rate`) za PoW i brzinu pretraživanja (`search rate`) za PoUW.

Primjer:

```text
Nodes: 5
```

znači da u simulaciji sudjeluje pet čvorova.

Povećanjem broja čvorova povećava se broj sudionika koji paralelno pokušavaju pronaći rješenje.

### Broj gradova (`num_of_cities`)

Određuje broj gradova koji se koriste za generiranje TSP problema u PoUW simulaciji.

Primjer:

```text
Cities: 10
```

znači da TSP problem sadrži deset gradova.

Povećanjem broja gradova povećava se veličina prostora mogućih rješenja i količina računalnog rada potrebnog za pretraživanje TSP problema.

### Način validacije (`validation_mode`)

Određuje hoće li se nakon pronalaska PoUW rješenja provoditi dodatna validacija.

GUI omogućuje odabir između:

- **No validation** – PoUW rješenje se ne validira.
- **Proof validation** – rješenje se validira pomoću proof-based mehanizma.
- **Council validation** – rješenje se validira pomoću ostalih čvorova simulacije.

Odabrani način validacije utječe na ukupan broj računalnih operacija i vrijeme simulacije.

### Pokretanje simulacije iz GUI-ja

Nakon odabira konfiguracijskih vrijednosti pritiskom na gumb **Run** pokreće se simulacija.

GUI zatim prikazuje napredak izvođenja i nakon završetka otvara prozor s rezultatima.

---

## Evidencija vremena izvođenja (`timing.txt`)

Datoteka `timing.txt` služi za evidenciju vremena izvođenja pojedinih pokretanja simulacije.

Nakon svakog pokretanja programa u datoteku se zapisuje vremenski zapis izvršavanja simulacije. Novi rezultati dodaju se u postojeću datoteku, čime se omogućuje pregled vremena izvođenja kroz više uzastopnih pokretanja programa.

Datoteka `timing.txt` može se koristiti za praćenje i usporedbu trajanja pojedinih pokretanja simulacije pri različitim konfiguracijskim parametrima.

## Ispravci modela i testovi (9. 9. 2026.)

Detalji ispravljenog raspoređivanja, validacije i jedinica rada nalaze se u `MODEL_NOTES.md`. Prije korištenja rezultata u završnom radu potrebno je ponovno pokrenuti mjerenja i obnoviti grafikone.

Regresijski testovi:

```sh
python proof_validation_tests.py
python -m unittest -v test_regressions
```

Svježi dnevnici provjere nalaze se u `test-results/`.


## Ograničenje stvarnog izvođenja

`python main.py` koristi jednog stvarnog radnika. Broj simuliranih čvorova ostaje neovisan.
GUI sadrži **Real worker processes**, **Benchmark repetitions**, **Experiment seed** i **Cancel**.
Jedan stvarni radnik ne stvara procesni bazen. Pri više radnika koristi se ograničeni spawn bazen;
mali transkripti (manje od 10 000 zapisa) provjeravaju se izravno. Sve semantičke provjere ostaju uključene.

Na Windowsu je opcionalno dostupan postotni limit za aplikaciju i njezine potomke:

```sh
python main.py --host-workers 1 --cpu-percent 25
```

Postotni limit nije temperaturni limit. Windows Job Object kod nije izvršno provjeren na Windowsu
u ovoj isporuci; ako Windows odbije postavljanje, program prijavljuje pogrešku i ne nastavlja bez limita.
Bez `--cpu-percent` nema postotnog ograničenja. Linux testovi provjeravaju spawn radnike, ne Windows API.
Mehanički neispravan ventilator potrebno je popraviti prije zahtjevnih izvođenja.

## Ponovljiva evaluacija

U direktoriju `evaluation/` nalaze se 40 uparenih ulaza, mjerene referentne stope, sirovi rezultati,
intervali pouzdanosti, grafovi i metapodaci Linux izvođenja. Korištena je PoW težina 4, ne 6.
Za ponavljanje sa spremljenim ulazima i kalibracijom:

```sh
python experiments.py --replay evaluation --output ponovljeno --host-workers 1
```

Za novu kalibraciju i nove rezultate:

```sh
python experiments.py --output novo-mjerenje --runs 40 --cities 12 --nodes 5 --difficulty 4
```

Izlazni direktorij mora biti prazan. GUI koristi ponovljive ulaze sa zadanim sjemenom,
ali za usporedbu svih validacijskih varijanti uz zajedničku kalibraciju koristite `experiments.py`.
Spremljene stope znače da ponavljanje provjerava isti model referentnog računala, a ne mjeri novo računalo.

Dodatni testovi:

```sh
python -m unittest -v test_regressions test_host_controls
```

Potvrđeno: 29 testnih metoda, uključujući 600 iscrpnih TSP usporedbi; zasebna proof skripta daje 10/10
 očekivanih odluka. Testovi su izvršeni na Linuxu/Pythonu 3.12.14. Izvorni GUI nije pokrenut na Windowsu.
