# Integrace MakerBadge a služby Živý obraz v CircuitPython

Pirátský (alernativní) firmware pro službu Živý obraz, která umožňuje vytváře vlastní dashboardy primárně určené pro E-Ink displaye.

Je odladěn pro vývojovou desku **MakerBadge**, který používá ESP32-S2 a B/W E-Ink 250x122px.

Oproti orignálnímu C++ firmware je tato integrace psána v **CircuitPython** a tak **nevyžaduje žádnou kompilaci** - stačí nahrát CircuitPyhton a zdrojový skript na připojený MakerBadge.

API služby Živý obraz vrací obrázek nakonfigurovaného dashboardu ve formátu BMP (v1) nebo komprimovaný RLE (v2.0) a v HTTP hlavičkách předává informaci kdy došlo k poslední změně na dashboardu (a je tak třeba display překreslit) a na jak dlouho má deska přejít do Deep Sleep módu.

Timestamp poslední změny se ukládá do NVM, takže je uchován i po vzbuzení z Deep Sleep a restartu. Pro jednoduchost zde stačí pouze kontrolovat, zda se timestamp změnil a není třeba pracovat s reálným časem.

Pro ušetření zdrojů a opravy stavu, kdy mi služba vracela před samotnými daty BMP souboru řetězec "Neplané ID", je implementován vlastní jenoduchý parser BMP souboru.

Pro novou verzi 2.0 je implementován RLE parser, který kontroluje, že hlavička vrácených dat je Z2 (https://wiki.zivyobraz.eu/doku.php?id=portal:format_z1_a_z2). Kód používá streamovaného HTTP přenosu.

Práce s API, parsování obrázku a zobrazování na E-Ink je v souboru *code.py* (*code-v1.py* pro původní verzi s BMP), v souboru *mb_setup.py* je obecné nastavení periferií MakerBadge a několik pomocných funkcí. V souboru *settings.toml* se nastavuje připojení k WiFi.

- MakerBadge: https://www.makermarket.cz/maker-badge/
- Živý obraz: https://zivyobraz.eu/
- CircuitPython: https://circuitpython.org/board/maker_badge/

![makerbadge-cpy-zivyobraz](https://github.com/MakerClassCZ/MakerBadge_Zivyobraz/assets/3875093/bcbf8335-c2c5-44a0-b281-e7ece09425dd)

## Další ukázky s MakerBadge:
- [Interaktivní visačka s QR vstupenkou](https://github.com/MakerClassCZ/Events/tree/main/2023-09-15-PyconCZ/badge)
