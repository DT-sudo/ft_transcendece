"""Zásady ochrany osobních údajů a Podmínky používání v češtině (překlad `en.py`)."""

from __future__ import annotations

from .en import CONTACT_EMAIL

LAST_UPDATED = "18. září 2026"

PRIVACY_POLICY = {
    "title": "Zásady ochrany osobních údajů",
    "updated": LAST_UPDATED,
    "intro": [
        "PlanShift je aplikace pro plánování směn týmů placených po hodinách. Tyto zásady přesně "
        "vysvětlují, jaké osobní údaje aplikace uchovává, proč je uchovává, kdo je může vidět a o co "
        "nás můžete požádat.",
        "PlanShift vznikl jako studentský projekt v rámci studijního programu školy 42. Provozuje se "
        "na vlastním serveru: správcem údajů je organizace, která provozuje instanci, kterou "
        "používáte, a autoři PlanShiftu k ní nemají přístup.",
    ],
    "sections": [
        {
            "heading": "1. Jaké údaje shromažďujeme",
            "paragraphs": [
                "Shromažďujeme jen to, co plánování směn skutečně potřebuje. Nepoužíváme žádný "
                "analytický skript, reklamní síť, sledovací pixel ani vložený obsah třetích stran "
                "kromě webového písma poskytovaného službou Google Fonts.",
            ],
            "bullets": [
                "Údaje o účtu — vaše celé jméno, e-mailová adresa (která je zároveň vaším přihlašovacím "
                "jménem), systémem vygenerované ID zaměstnance, vaše role (administrátor, manažer nebo "
                "zaměstnanec), u zaměstnanců pozice, na které pracujete, a kdy byl účet vytvořen a kdy "
                "jste se naposledy přihlásili.",
                "Údaje profilu — volitelná profilová fotografie (převedená do malého formátu WebP, čímž "
                "se odstraní veškerá metadata o fotoaparátu či poloze), volitelný krátký popis, vaši "
                "přátelé a žádosti o přátelství a váš stav online: zda máte PlanShift otevřený a kdy "
                "jste ho měli otevřený naposledy.",
                "Heslo — nikdy se neukládá jako text. Do databáze se zapisuje pouze solený hash "
                "PBKDF2-SHA256, ze kterého nelze vaše heslo zpětně získat.",
                "Dvoufázové ověření, pokud ho zapnete — tajný klíč, který vaše ověřovací aplikace "
                "sdílí s PlanShiftem (server ho potřebuje ke kontrole vašich kódů), okamžik zapnutí a "
                "vaše záložní kódy, z nichž se uchovává pouze klíčovaný hash. Vypnutím dvoufázového "
                "ověření se vše smaže.",
                "Údaje o plánování — směny, ke kterým jste přiřazeni, jejich data, časy, pozice a "
                "kapacita, a dny, které jste si označili jako nedostupné. U manažerů také směny, které "
                "vytvořili.",
                "Oznámení — zprávy v aplikaci o změnách provedených jinými lidmi, které se vás týkají, "
                "například o směně, ke které jste byli přiřazeni, a chybová hlášení, která vám aplikace "
                "zobrazila. Uchovávají se, dokud je nevymažete nebo dokud nebude váš účet smazán.",
                "Jazyk — jazyk, ve kterém PlanShift používáte, uložený u vašeho účtu a v cookie, aby vám "
                "aplikace, e-maily a oznámení přicházely v jazyce, který čtete.",
                "Bezpečnostní záznam — řádek za každé přihlášení (úspěšné i neúspěšné), odhlášení, "
                "změnu účtu nebo role a ukončenou relaci, s číslem účtu, přihlašovacím e-mailem a IP "
                "adresou, ze které požadavek přišel. Zapisuje se do logu serveru, ne do databáze, a "
                "nikdy neobsahuje hesla ani kódy.",
                "Cookies — cookie relace, díky které zůstáváte přihlášeni, cookie CSRF, která chrání "
                "formuláře, cookie jazyka a cookie zpráv, která přenese jednorázové potvrzení nebo "
                "chybové hlášení na další stránku. Popisuje je oddíl 7.",
            ],
        },
        {
            "heading": "2. Proč údaje zpracováváme",
            "bullets": [
                "Abychom vás ověřili a udrželi vaši relaci otevřenou mezi požadavky.",
                "Abychom mohli vytvářet, kontrolovat a zobrazovat pracovní rozpis — včetně kontroly, "
                "že přiřazení odpovídá pozici zaměstnance a nekryje se s jinou směnou ani se dnem, "
                "který označil jako nedostupný.",
                "Aby manažeři viděli rozpis, který vedou, a hodiny, které přiděluje jednotlivým lidem, "
                "a aby administrátor mohl udržovat účty a pozice aktuální.",
                "Abychom vás informovali o změnách, které se vás týkají — v aplikaci, a u exportu "
                "údajů, smazání účtu a změn dvoufázového ověření také e-mailem.",
                "Abychom udrželi aplikaci v bezpečí: odmítáním požadavků z jiných webů, blokováním "
                "opakovaně chybných kódů dvoufázového ověření a vedením bezpečnostního záznamu pro "
                "vyšetření zneužití.",
            ],
            "paragraphs": [
                "Právním základem je plnění vašeho pracovního vztahu s organizací, která instanci "
                "provozuje, spolu s oprávněným zájmem této organizace na vedení pracovního rozpisu a "
                "jeho zabezpečení. Vaše údaje nezpracováváme k žádnému jinému účelu než k vedení "
                "rozpisu.",
            ],
        },
        {
            "heading": "3. Kdo vaše údaje vidí",
            "bullets": [
                "Vy — vše o svém vlastním účtu a jeho úplnou kopii na stránce „Soukromí a moje údaje“.",
                "Kolegové — každý přihlášený manažer a zaměstnanec vidí na vašem profilu vaše jméno, "
                "fotografii, roli nebo pozici a popis. Vaši přátelé navíc vidí váš e-mail, seznam "
                "přátel a to, zda jste online.",
                "Manažeři — celý rozpis včetně konceptů směn, které zaměstnanci zatím nevidí, bez "
                "ohledu na to, který manažer směnu vytvořil; jméno, pozici a dny nedostupnosti "
                "každého zaměstnance; a hodiny, na které je kdo naplánován.",
                "Administrátoři — jméno, e-mail, ID zaměstnance, roli a pozici každého účtu a to, zda "
                "má zapnuté dvoufázové ověření. Tyto údaje mohou měnit, obnovit heslo nebo dvoufázové "
                "ověření a mazat účty.",
                "Technici provozovatele — lidé s přístupem k serveru, jeho databázi a logům.",
            ],
            "paragraphs": [
                "Vaše údaje se nikdy neprodávají, nepronajímají, nesdílejí s inzerenty ani nepoužívají "
                "k trénování modelů strojového učení. Malou část z nich vidí dvě vnější služby: Google "
                "Fonts obdrží vaši IP adresu, když si prohlížeč stahuje písmo, a poštovní server, který "
                "provozovatel nastaví, doručuje výše popsané e-maily.",
            ],
        },
        {
            "heading": "4. Jak dlouho údaje uchováváme",
            "paragraphs": [
                "Údaje o účtu a plánování se uchovávají, dokud váš účet v instanci existuje. Když je "
                "váš účet smazán — vámi nebo administrátorem — záznam účtu, profilová fotografie, "
                "přátelství, oznámení, údaje dvoufázového ověření, přiřazení ke směnám a záznamy o "
                "nedostupnosti se z databáze okamžitě odstraní. Neexistuje žádné měkké smazání ani "
                "archivní kopie. Směny, které vytvořil manažer, zůstávají ve sdíleném rozpisu, už bez "
                "vazby na něj.",
                "Jednorázově vygenerované heslo se uchovává v serverové relaci administrátora jen po "
                "dobu nutnou k jeho jedinému zobrazení a zahodí se, jakmile se stránka vykreslí. "
                "Řádky bezpečnostního záznamu se uchovávají tak dlouho, jak dlouho provozovatel "
                "uchovává logy serveru.",
            ],
        },
        {
            "heading": "5. Jak údaje chráníme",
            "bullets": [
                "Veškerý provoz mezi vaším prohlížečem a aplikací je šifrován pomocí TLS; požadavky "
                "přes nešifrované HTTP jsou přesměrovány na HTTPS.",
                "Hesla se ukládají pouze jako solené hashe PBKDF2-SHA256.",
                "Svůj účet můžete chránit dvoufázovým ověřením: po zadání hesla vyžaduje přihlášení "
                "ještě kód z ověřovací aplikace nebo jednorázový záložní kód. Pět chybných kódů "
                "zablokuje ověření na pět minut a o každé jeho změně vás informujeme e-mailem.",
                "Každý zápis je chráněn tokenem CSRF a každá stránka se odesílá s hlavičkami "
                "X-Frame-Options: DENY a X-Content-Type-Options: nosniff.",
                "Přístup je na serveru omezen podle rolí: zaměstnanci se nedostanou k rozpisu ani ke "
                "stránkám účtů a vždy dostávají jen své vlastní zveřejněné směny; účty může měnit jen "
                "administrátor. Když se vám změní role nebo je obnoveno heslo, vaše otevřené relace "
                "se odhlásí.",
                "Databázové dotazy procházejí přes Django ORM, který parametrizuje každou hodnotu, a "
                "veškerý vykreslovaný obsah je ve výchozím stavu escapován.",
            ],
        },
        {
            "heading": "6. Vaše práva",
            "paragraphs": [
                "Podle GDPR můžete požádat o kopii údajů, které o vás uchováváme, o jejich opravu nebo "
                "výmaz, vznést námitku proti jejich zpracování nebo požádat o omezení zpracování. Máte "
                "také právo podat stížnost u svého národního úřadu pro ochranu osobních údajů.",
                "Většinu z toho zvládnete sami. Na stránce „Soukromí a moje údaje“ si můžete stáhnout "
                "vše, co o vás uchováváme, jako čitelný soubor JSON, a po potvrzení e-mailu a hesla "
                "smazat svůj účet; obojí vám potvrdíme e-mailem. Jméno, e-mail, fotografii a popis "
                "opravíte v Nastavení účtu. S čímkoli dalším se obraťte na "
                f"{CONTACT_EMAIL} nebo na administrátora instance vaší organizace.",
            ],
        },
        {
            "heading": "7. Cookies",
            "paragraphs": [
                "PlanShift nastavuje čtyři cookies, všechny nezbytně nutné pro fungování služby: cookie "
                "relace, díky které zůstáváte přihlášeni (nejdéle dva týdny, nebo dokud se "
                "neodhlásíte), cookie CSRF, která chrání formuláře před odesláním z cizích webů, "
                "cookie jazyka, která si pamatuje zvolený jazyk, a cookie zpráv, která přenese "
                "potvrzení nebo chybové hlášení na další stránku a smaže se, jakmile se zobrazí. Žádná "
                "z nich se nepoužívá ke sledování ani profilování, proto není potřeba lišta se "
                "souhlasem. Pokud je zablokujete, nebudete se moci přihlásit.",
            ],
        },
        {
            "heading": "8. Změny těchto zásad",
            "paragraphs": [
                "Pokud se tyto zásady změní, aktualizuje se datum v horní části stránky. Podstatné "
                "změny oznámíme v aplikaci dříve, než vstoupí v platnost.",
            ],
        },
        {
            "heading": "9. Kontakt",
            "paragraphs": [
                f"Dotazy k těmto zásadám: {CONTACT_EMAIL}. S čímkoli, co se týká vašeho rozpisu, se "
                "obraťte na svého manažera; s vaším účtem na administrátora instance vaší organizace.",
            ],
        },
    ],
}

TERMS_OF_SERVICE = {
    "title": "Podmínky používání",
    "updated": LAST_UPDATED,
    "intro": [
        "Tyto podmínky upravují vaše používání PlanShiftu, webové aplikace pro plánování směn. "
        "Vytvořením účtu nebo přihlášením s nimi souhlasíte. Pokud nesouhlasíte, službu nepoužívejte.",
    ],
    "sections": [
        {
            "heading": "1. Služba",
            "paragraphs": [
                "PlanShift umožňuje manažerům sestavit v kalendáři jeden sdílený pracovní rozpis a "
                "zveřejnit ho týmu, zaměstnancům vidět směny, které jim byly přiřazeny, a označit dny, "
                "kdy nejsou k dispozici, a administrátorovi spravovat účty a pozice. Kolegové si mohou "
                "prohlížet profily a přidávat se mezi přátele. Je to nástroj pro plánování. Není to "
                "mzdový systém, docházkový systém ani závazná evidence skutečně odpracovaných hodin.",
            ],
        },
        {
            "heading": "2. Účty",
            "bullets": [
                "Registrací se zakládá účet manažera. Prvního administrátora jmenuje provozovatel "
                "instance; administrátoři pak zakládají ostatní účty a určují jejich role.",
                "Účty, které založí administrátor, dostanou vygenerované heslo zobrazené "
                "administrátorovi právě jednou; administrátor odpovídá za jeho bezpečné předání.",
                "Musíte uvést pravdivé jméno a funkční e-mailovou adresu a k držení účtu vám musí být "
                "alespoň 16 let, nebo musíte mít souhlas zákonného zástupce.",
                "Odpovídáte za vše, co se pod vaším účtem děje. Uchovávejte heslo v tajnosti, účet s "
                "nikým nesdílejte, a pokud máte podezření, že k němu má přístup někdo jiný, ihned to "
                "oznamte svému administrátorovi.",
            ],
        },
        {
            "heading": "3. Přijatelné použití",
            "paragraphs": ["Zavazujete se, že nebudete:"],
            "bullets": [
                "Přistupovat nebo se pokoušet přistupovat k účtům nebo údajům, ke kterým vám vaše role "
                "přístup nedává.",
                "Zkoumat, skenovat nebo testovat zabezpečení instance ani obcházet jakoukoli kontrolu "
                "přístupu, omezení počtu požadavků nebo ověření.",
                "Automatizovat požadavky způsobem, který zhoršuje službu ostatním uživatelům.",
                "Nahrávat nebo zadávat nezákonný, urážlivý nebo záměrně zavádějící obsah, včetně "
                "urážlivých profilových fotografií nebo popisů, falešných jmen nebo údajů o plánování "
                "zadaných s cílem poškodit kolegu.",
                "Kopírovat, stahovat nebo dále šířit údaje jiné organizace.",
            ],
        },
        {
            "heading": "4. Povinnosti administrátorů a manažerů",
            "paragraphs": [
                "Administrátoři a manažeři jednají za organizaci, která instanci provozuje a je "
                "správcem všech údajů do ní zadaných. Odpovídají za to, že zadávají jen osobní údaje, "
                "které rozpis potřebuje, že k jejich zpracování existuje právní základ, že tým ví o "
                "používání PlanShiftu a že vyhoví jeho žádostem o přístup k údajům, jejich opravu nebo "
                "výmaz. Naše Zásady ochrany osobních údajů vysvětlují, co aplikace ukládá.",
            ],
        },
        {
            "heading": "5. Rozpisy nejsou smlouvy",
            "paragraphs": [
                "Zveřejněná směna je provozní plán, nikoli závazná nabídka práce, záruka počtu hodin "
                "ani pracovní smlouva. Vaše práva zaměstnance vyplývají z vaší pracovní smlouvy a z "
                "právních předpisů vaší země, nikoli z toho, co zobrazuje tato aplikace. Označení "
                "nedostupnosti zabrání přiřazení v nástroji; samo o sobě ale neznamená schválené volno.",
            ],
        },
        {
            "heading": "6. Dostupnost",
            "paragraphs": [
                "Služba je poskytována „tak, jak je“ a „podle dostupnosti“. Nezaručujeme, že bude "
                "fungovat bez přerušení nebo bez chyb, a instance může být odstavena kvůli údržbě, "
                "aktualizacím nebo podle uvážení provozovatele. Vše, o co nesmíte přijít, si evidujte "
                "i sami.",
            ],
        },
        {
            "heading": "7. Duševní vlastnictví",
            "paragraphs": [
                "Zdrojový kód PlanShiftu je vydán pod licencí MIT a lze jej používat, upravovat a šířit "
                "za jejích podmínek. Údaje o plánování a účtech uložené v instanci patří organizaci, "
                "která ji provozuje, nikoli autorům softwaru.",
            ],
        },
        {
            "heading": "8. Pozastavení a ukončení",
            "paragraphs": [
                "Administrátor může kterýkoli účet kdykoli smazat, například když někdo z týmu odejde, "
                "a provozovatel instance může pozastavit jakýkoli účet, který tyto podmínky porušuje. "
                "Službu můžete kdykoli přestat používat a svůj účet sami smazat na stránce „Soukromí a "
                "moje údaje“. Smazáním se odstraní váš účet, profil, přátelství, oznámení, přiřazení a "
                "záznamy o nedostupnosti; směny, které jste vytvořili jako manažer, zůstanou ve "
                "sdíleném rozpisu.",
            ],
        },
        {
            "heading": "9. Omezení odpovědnosti",
            "paragraphs": [
                "V nejširším rozsahu povoleném zákonem nenesou autoři ani provozovatel instance "
                "odpovědnost za nepřímé nebo následné škody vzniklé používáním služby, včetně "
                "zmeškaných směn, ušlé mzdy nebo chyb v plánování. Nic v těchto podmínkách neomezuje "
                "odpovědnost, kterou nelze ze zákona omezit.",
            ],
        },
        {
            "heading": "10. Změny těchto podmínek",
            "paragraphs": [
                "Tyto podmínky můžeme aktualizovat. Datum v horní části stránky ukazuje, kdy se "
                "naposledy změnily, a pokračováním v používání služby po změně přijímáte novou verzi.",
            ],
        },
        {
            "heading": "11. Rozhodné právo a kontakt",
            "paragraphs": [
                "Tyto podmínky se řídí právem země, ve které je instance provozována. Dotazy k nim "
                f"můžete zasílat na {CONTACT_EMAIL}.",
            ],
        },
        {
            "heading": "12. Upozornění na akademický projekt",
            "paragraphs": [
                "PlanShift vznikl jako součást studijního programu školy 42. Jde o demonstrační "
                "projekt: neprošel formálním bezpečnostním auditem ani právní kontrolou, a než se na "
                "něj budete spoléhat při skutečných rozhodnutích souvisejících se mzdami, měl by být "
                "podle toho posouzen.",
            ],
        },
    ],
}

DOCUMENTS = {"privacy": PRIVACY_POLICY, "terms": TERMS_OF_SERVICE}
