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
2. Po potrebi promijeniti parametre simulacije u `main.py`.
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

# Izlaz GUI-ja

Nakon završetka simulacije GUI otvara **Output** prozor u kojem se prikazuju rezultati benchmarka, PoW simulacije, PoUW simulacije i, ako je odabrana, validacije PoUW rješenja.

## Benchmark

Na početku izlaza prikazuju se rezultati benchmarka:

```text
PoW Benchmark:

Hashes/sec: 847090

PoUW TSP Benchmark:

Computations/sec: 39871
```

`Hashes/sec` predstavlja prosječan broj SHA-256 hash vrijednosti koje računalo može izračunati u jednoj sekundi.

`Computations/sec` predstavlja prosječan broj TSP operacija koje računalo može izvršiti u jednoj sekundi.

Ove vrijednosti koriste se za određivanje brzina čvorova i odnosa računalnog rada između PoW i PoUW simulacija.

## PoW rezultati

U izlaznom prozoru prikazuju se rezultati PoW simulacije, uključujući brzinu čvorova, pobjednički čvor, broj hash pokušaja i vrijeme simulacije.

Primjer:

```text
Hash rate:

node1: 99     node2: 52     node3: 189     node4: 123     node5: 199

Winner:

Name: node3
Hashes: 45396
Time: 240.19s
Hash: 00009871e76dabce47984536c10e3e8ca4e19f0dde6ac16a4fc145f4804fec1c
```

`Hash rate` predstavlja broj hash pokušaja koje pojedini čvor može izvršiti tijekom jedne sekunde simuliranog vremena.

`Hashes` predstavlja broj hash pokušaja pobjedničkog čvora u posljednjem intervalu potrebnih za pronalazak valjanog rješenja.

`Time` predstavlja simulirano vrijeme potrebno za pronalazak valjanog PoW rješenja.

`Hash` predstavlja pronađeni hash koji zadovoljava zadanu težinu.

Nakon toga prikazuje se ukupni računalni rad svih čvorova:

```text
Mining count:

node1: 23779     node2: 12490     node3: 45396     node4: 29543     node5: 47798

Total mining count: 159006

Simulation time: 240.19 s
```

`Mining count` predstavlja broj hashiranja koje je pojedini čvor izvršio do trenutka pronalaska rješenja.

`Total mining count` predstavlja ukupan broj hashiranja svih čvorova tijekom simulacije.

`Simulation time` predstavlja ukupno simulirano vrijeme potrebno za pronalazak PoW rješenja.

## PoUW rezultati

Za PoUW simulaciju GUI prikazuje generirani TSP problem, brzinu pretraživanja čvorova, pronađeno rješenje i broj izvršenih računalnih operacija.

Primjer:

```text
Matrix:

[inf, 700, 300, 590, 60, 50, 900, 30, 10, 600]

[700, inf, 30, 340, 600, 500, 920, 60, 590, 90]

...
```

Svaki element matrice predstavlja udaljenost između dva grada, dok `inf` predstavlja nedostupnu vezu grada sa samim sobom.

Brzina pretraživanja prikazuje se na sljedeći način:

```text
Search rate:

node1: 6        node2: 5        node3: 3        node4: 8        node5: 7
```

`Search rate` predstavlja broj čvorova TSP stabla pretraživanja koje pojedini čvor može obraditi tijekom jedne sekunde simuliranog vremena.

Nakon završetka pretraživanja prikazuje se pronađeni obilazak:

```text
Best path: [0, 4, 6, 5, 3, 7, 9, 1, 2, 8, 0]

Best cost: 440
```

`Best path` predstavlja redoslijed obilaska gradova, uključujući povratak u početni grad.

`Best cost` predstavlja ukupnu cijenu pronađenog obilaska.

Broj izvršenih operacija prikazuje se za svaki čvor:

```text
Computations:

node1: 718      node2: 598      node3: 359      node4: 957      node5: 838

Total computations: 3470

Simulation time: 119.67s
```

`Computations` predstavlja broj obrađenih čvorova TSP stabla pretraživanja za pojedini čvor.

`Total computations` predstavlja ukupan broj obrađenih čvorova svih čvorova tijekom simulacije.

`Simulation time` predstavlja ukupno simulirano vrijeme potrebno za pronalazak PoUW rješenja.

## Validacija PoUW rješenja

Ako je u GUI-ju odabrana jedna od metoda validacije, nakon pronalaska PoUW rješenja prikazuju se i rezultati validacijskog postupka.

Kod **Proof validation** metode dodatni računalni rad potreban za validaciju dokaza uračunava se u ukupan broj računalnih operacija.

Kod **Council validation** metode ostali čvorovi sudjeluju u provjeri pronađenog rješenja, a njihov računalni rad također se uračunava u ukupni trošak.

Na taj se način može usporediti osnovni PoUW mehanizam s PoUW mehanizmom koji uključuje dodatni postupak validacije.

## Prosječni rezultati

Na kraju izlaznog prozora prikazuju se prosječne vrijednosti dobivene iz svih izvršenih ponavljanja.

Primjer:

```text
Average hashes: 83975.00

Average computation: 4361.00
```

`Average hashes` predstavlja prosječan broj hashiranja potrebnih za završetak PoW simulacije.

`Average computation` predstavlja prosječan broj TSP računalnih operacija potrebnih za završetak PoUW simulacije.

Ako je korištena validacija, prikazuju se i prosječne vrijednosti računalnog rada i vremena za PoUW simulaciju zajedno s odabranim postupkom validacije.
