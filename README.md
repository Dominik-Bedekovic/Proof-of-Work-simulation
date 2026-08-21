# Pokretanje simulacije

Simulacija se pokreće iz datoteke `main.py`. U toj se datoteci definiraju osnovni parametri simulacije koji omogućuju jednostavnu promjenu uvjeta izvođenja bez potrebe za izmjenama ostatka programa.

Trenutno je moguće definirati sljedeće parametre:

- `runs` – broj ponavljanja simulacije i benchmarka, nakon kojih se izračunava prosječna vrijednost rezultata.
- `block_hash_difficulty` – težina PoW rudarenja, definirana brojem vodećih nula koje mora sadržavati valjani hash.
- `num_of_nodes` – broj čvorova koji sudjeluju u simulaciji.
- `num_of_cities` – broj gradova koji se koriste za TSP problem u PoUW simulaciji.

Primjer osnovne konfiguracije:

```python
runs = 5
block_hash_difficulty = 4
num_of_nodes = 5
num_of_cities = 10
```

Nakon definiranja parametara stvara se objekt klase `MainFunctions`, koji je zadužen za pokretanje benchmarka i simulacija:

```python
simulation = MainFunctions(
    num_of_nodes,
    num_of_cities,
    runs,
    block_hash_difficulty
)

simulation.run_simulation()
```

Za pokretanje programa potrebno je pokrenuti datoteku `main.py`. Promjenom vrijednosti navedenih parametara moguće je jednostavno ispitivati ponašanje simulacije pod različitim uvjetima, primjerice s različitim brojem čvorova, različitom težinom PoW rudarenja ili različitim brojem gradova u TSP problemu.

## Izlaz programa

Trenutno se rezultati simulacije prikazuju izravno u terminalu. Program najprije ispisuje rezultate benchmarka, nakon čega se zasebno izvršavaju PoW i PouW simulacije. Budući da se simulacije izvode više puta, na kraju se prikazuju prosječne vrijednosti dobivene iz svih izvršenih ponavljanja.

### Benchmark

Na početku se prikazuju rezultati benchmarka:

```text
PoW Benchmark:
Hashes/sec: 847090

PoUW TSP Benchmark:
Computations/sec: 39871
```

`Hashes/sec` predstavlja prosječan broj SHA-256 hash vrijednosti koje simulacija može izračunati u jednoj sekundi.

`Computations/sec` predstavlja prosječan broj operacija obrade čvorova TSP stabla koje simulacija može izvršiti u jednoj sekundi.

Ove vrijednosti koriste se za određivanje odnosa između brzine PoW i PouW mehanizama te za skaliranje brzine pojedinih čvorova.

### PoW simulacija

Tijekom PoW simulacije prvo se ispisuje brzina svakog čvora:

```text
Hash rate:
node1: 99       node2: 52       node3: 189      node4: 123      node5: 199
```

Vrijednost `hash rate` određuje koliko hash vrijednosti pojedini čvor pokušava izračunati tijekom jedne sekunde simuliranog vremena.

Nakon završetka rudarenja prikazuje se čvor koji je prvi pronašao valjani hash:

```text
Winner is:
Name: node3
Hashes: 45396
Time: 240.19s
Hash: 00009871e76dabce47984536c10e3e8ca4e19f0dde6ac16a4fc145f4804fec1c
```

`Hashes` predstavlja ukupan broj hash pokušaja pobjedničkog čvora, dok `Time` predstavlja vrijeme potrebno tom čvoru da pronađe valjano rješenje. Prikazani `Hash` je pronađena hash vrijednost koja zadovoljava zadanu težinu rudarenja.

Nakon toga prikazuje se broj hash pokušaja svakog čvora:

```text
Mining count:
node1: 23779    node2: 12490    node3: 45396    node4: 29543    node5: 47798

Total mining count: 159006
Simulation time: 240.19 s
```

`Mining count` predstavlja broj hashiranja koje je pojedini čvor izvršio do trenutka pronalaska rješenja. Kod čvorova koji nisu pobjednici uzima se u obzir samo dio posljednje simulirane sekunde koji je protekao prije pronalaska rješenja. `Total mining count` predstavlja ukupan broj hashiranja svih čvorova, odnosno ukupni računalni rad obavljen tijekom simulacije.

### PoUW simulacija

Kod PouW simulacije ispisuje se generirani TSP problem u obliku matrice udaljenosti:

```text
Matrix:
[inf, 700, 300, 590, 60, 50, 900, 30, 10, 600]
[700, inf, 30, 340, 600, 500, 920, 60, 590, 90]
...
```

Svaki element matrice predstavlja udaljenost između dva grada, dok `inf` predstavlja nedostupnu vezu grada sa samim sobom.

Nakon matrice prikazuje se `search rate` svakog čvora:

```text
Search rate:
node1: 6        node2: 5        node3: 3        node4: 8        node5: 7
```

`Search rate` određuje koliko čvorova stabla pretraživanja pojedini čvor obrađuje tijekom jedne sekunde simuliranog vremena.

Nakon završetka pretraživanja prikazuje se pronađeni optimalni obilazak i njegova cijena:

```text
Best path: [0, 4, 6, 5, 3, 7, 9, 1, 2, 8, 0]
Best cost: 440
```

`Best path` predstavlja redoslijed obilaska gradova, uključujući povratak u početni grad. `Best cost` predstavlja ukupnu cijenu pronađenog obilaska.

Zatim se prikazuje broj obrađenih čvorova za svaki čvor simulacije:

```text
Computations:
node1: 718      node2: 598      node3: 359      node4: 957      node5: 838

Total computations: 3470
Simulation time: 119.67s
```

`Computations` predstavlja broj obrađenih čvorova stabla pretraživanja za pojedini čvor simulacije. `Total computations` predstavlja ukupan broj obrađenih čvorova svih čvorova tijekom simulacije.

### Prosječni rezultati

Nakon završetka svih zadanih ponavljanja program prikazuje prosječne rezultate:

```text
Average hashes: 83975.00
Average computation: 4361.00
```

`Average hashes` predstavlja prosječan broj hashiranja potrebnih za završetak PoW simulacije, dok `Average computation` predstavlja prosječan broj obrađenih čvorova potrebnih za završetak PouW TSP simulacije.
