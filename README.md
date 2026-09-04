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
