# KingOfTheCastleCZlocalMod

![KingOfTheCastleCZlocalMod — česká lokalizace](assets/readme-banner.svg)

<p align="center">
  <strong>🇨🇿 Čeština</strong> · <a href="README.en.md">🇬🇧 English</a><br>
  <strong>0.1.0 beta</strong> · cs-CZ · Windows / Steam
</p>

---

## O projektu

**KingOfTheCastleCZlocalMod** je neoficiální česká lokalizace hry **King of the Castle**. Převádí místní anglické texty do češtiny: od nabídek a tutoriálu až po příběhy, intriky a otázky hlasování. Součástí projektu jsou překladové slovníky, nástroje pro sestavení a instalátor s možností obnovit původní angličtinu.

Rozhraní a důležité opakované texty mají ručně upravený překlad. Rozsáhlé příběhy vznikly s pomocí místního překladového modelu. Cílem je srozumitelná čeština při zachování herních podmínek, proměnných a příběhové logiky.

> **Zdrojový repozitář a instalační balíček jsou dvě různé podoby projektu.** Klon repozitáře obsahuje překlady a zdrojové kódy. Pro instalaci potřebujete také sestavené soubory v `patched/` a odpovídající `manifest.json`.

## Rozsah překladu

| Oblast | Co zahrnuje |
| :--- | :--- |
| 🎮 Rozhraní | Nabídky, tlačítka, tutoriál, pravidla a herní hlášení |
| 👑 Království | Regiony, statistiky, budovy, intriky a podmínky vítězství |
| 📜 Příběhy | Všech 1 005 nalezených příběhových skriptů Ink a 3 další vložené skripty |
| 🗳️ Hlasování | Otázky a volby vytvořené místní hrou |
| 🔤 České znaky | Náhradní font pro českou diakritiku a překlad textů při zobrazení |

| Rozsah zpracovaných dat | Počet |
| :--- | ---: |
| Nalezené zdrojové texty | 45 224 |
| Položky překladového slovníku | 46 085 |
| Příběhové skripty celkem | 1 008 |
| Slova ve zdrojových textech | 612 271 |

Jména a přezdívky autorů v titulcích, adresy a příkazy pro Twitch zůstávají zachované. Interní identifikátory, podmínky a hodnoty používané herní logikou se nepřekládají; některé názvy se proto počešťují až při zobrazení.

Samostatný web `kotc.app`, rozhraní Steamu a nově stahované zprávy jsou mimo rozsah tohoto modu. Otázky hlasování vytvořené přeloženou hrou se předávají jako součást herních dat.

## Instalace hotového balíčku

Požadovaná je **původní Windows verze hry ze Steamu**, která odpovídá kontrolním součtům v manifestu. Tato beta byla sestavena pro místní instalaci používající Unity **2021.3.45f1**; samotné číslo Unity nezaručuje kompatibilitu jiné verze hry.

1. Zavřete hru.
2. Umístěte složku `KingOfTheCastleCZlocalMod` přímo vedle `KingOfTheCastle.exe`.
3. Ověřte, že balíček obsahuje `patched/`, `manifest.json` a `translations.json`.
4. Spusťte [Nainstalovat.cmd](Nainstalovat.cmd). Instalátor ověří soubory, uloží zálohu a nainstaluje češtinu.
5. Hru spusťte obvyklým způsobem přes Steam.

```text
King of the Castle/
├── KingOfTheCastle.exe
├── KingOfTheCastle_Data/
└── KingOfTheCastleCZlocalMod/
    ├── Nainstalovat.cmd
    ├── Obnovit_anglictinu.cmd
    ├── translations.json
    ├── manifest.json
    ├── patched/
    └── backup/                ← záloha vytvořená instalátorem
```

Čeština nahrazuje anglické texty; v nabídce hry se další jazyk nevybírá. Instalátor hru nespouští. Název složky `KingOfTheCastleCZlocalMod` zachovejte, protože jej používá knihovna pro překlad rozhraní.

### Návrat k angličtině a aktualizace

Spusťte [Obnovit_anglictinu.cmd](Obnovit_anglictinu.cmd). Původní herní soubory se obnoví ze složky `backup/`, která zůstane uložená.

Před aktualizací hry obnovte angličtinu. Instalátor odmítne přepsat soubory jiné verze nebo soubory změněné dalším modem. Ověření herních souborů ve Steamu může lokalizaci přepsat.

## Kvalita a ověření

**Verze 0.1.0 je první beta.** Základní rozhraní, celý tutoriál, 187 opakovaných popisů cílů intrik, podmínky vítězství a řada důležitých popisů byly ručně upraveny. Příběhy ještě neprošly úplnou jazykovou redakcí; mohou obsahovat nepřesnosti, doslovné obraty nebo chyby ve skloňování doplňovaných jmen a titulů.

Automatické kontroly ověřují zachování instrukcí Ink, odkazů, herních hodnot, identifikátorů, binárních dat Odin a struktury upravených knihoven. Všech 1 008 skriptů se podařilo načíst knihovnou Ink dodanou s hrou. Výsledný mod byl ověřen kódem a porovnáním dat; tyto kontroly nepotvrzují vzhled každé obrazovky ani chování při celém průchodu hrou. Náhradní font se může mírně lišit od původního písma.

Při hlášení chyby přiložte původní text, navržený překlad a místo ve hře, kde se chyba objevila. Snímek obrazovky pomůže s kontextem a délkou textu.

## Překlady a vývoj

| Soubor nebo složka | Účel |
| :--- | :--- |
| [translations.json](translations.json) | Celý překladový slovník |
| [manual.json](manual.json) | Ručně upravené překlady |
| [catalog.json](catalog.json) | Katalog nalezených zdrojových textů |
| [tools/](tools/) | Extrakce, překlad, sestavení a kontroly |
| [tools/Runtime/](tools/Runtime/) | Překlad rozhraní při zobrazení a česká diakritika |
| [Install.ps1](Install.ps1) / [Restore.ps1](Restore.ps1) | Instalace a obnova původních souborů |

Pouhá úprava slovníku nezmění texty již zapsané do příběhových balíčků. Po opravě překladu je potřeba mod znovu sestavit. Před sestavením obnovte původní anglické soubory.

Sestavení vyžaduje původní instalaci hry, připravené prostředí Pythonu a .NET, potřebné závislosti, překladový model a vygenerované inventáře. Velký `tools/field_inventory.json` se obnovuje pomocí `tools/pipeline.py extract`; sestavení a kontroly řídí [tools/finish.ps1](tools/finish.ps1). Úplné automatické nastavení vývojového prostředí zatím není součástí projektu. Pro hraní s hotovým balíčkem model ani vývojové nástroje nepotřebujete.

### Co se ukládá do Gitu

Kořenem repozitáře je složka `KingOfTheCastleCZlocalMod`. [.gitignore](.gitignore) ponechává překlady, zdrojové kódy, skripty a dokumentaci. Zálohy, sestavené herní soubory, manifesty, modely, vývojová prostředí, dekompilované soubory, cache a diagnostické výpisy se do Gitu neukládají. Instalační balíček se připravuje zvlášť.

## Použité nástroje

- Překladový model: [Helsinki-NLP/opus-mt-tc-big-en-ces_slk](https://huggingface.co/Helsinki-NLP/opus-mt-tc-big-en-ces_slk), licence CC BY 4.0. Výstup byl upraven o chráněné proměnné, formátování a ručně přeložené části.
- Herní data: [UnityPy](https://github.com/K0lb3/UnityPy).
- Překlad: [CTranslate2](https://github.com/OpenNMT/CTranslate2).
- Úpravy knihoven: [Mono.Cecil](https://github.com/jbevain/cecil).

---

<p align="center"><strong>KingOfTheCastleCZlocalMod</strong> · Neoficiální česká lokalizace · <a href="README.en.md">English documentation →</a></p>
