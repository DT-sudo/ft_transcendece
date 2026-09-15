"""Zásady ochrany osobních údajů a Podmínky používání v češtině (překlad `en.py`)."""

from __future__ import annotations

from .en import CONTACT_EMAIL

LAST_UPDATED = "14. září 2026"

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
                "jménem), systémem vygenerované ID zaměstnance, vaše role (manažer nebo zaměstnanec) "
                "a u zaměstnanců pozice, na kterou jste kvalifikováni.",
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
                "kapacita, a dny, které jste si označili jako nedostupné.",
                "Oznámení — zprávy v aplikaci o změnách provedených jinými lidmi, které se vás týkají, "
                "například o směně, ke které jste byli přiřazeni. Uchovávají se, dokud je nevymažete "
                "nebo dokud nebude váš účet smazán.",
                "Jazyk — jazyk, ve kterém PlanShift používáte, uložený u vašeho účtu a v cookie, aby vám "
                "aplikace, e-maily a oznámení přicházely v jazyce, který čtete.",
                "Cookie relace — podepsaný identifikátor, díky kterému zůstáváte přihlášeni. Má "
                "nastavené příznaky HttpOnly, SameSite=Lax a Secure, takže je pro JavaScript "
                "nečitelný a nikdy se neposílá přes nešifrované spojení.",
                "Cookie CSRF — náhodný token, který slouží k prokázání, že odeslaný formulář pochází ze "
                "stránky, kterou jsme poskytli. Neobsahuje o vás žádné informace.",
            ],
        },
        {
            "heading": "2. Proč údaje zpracováváme",
            "bullets": [
                "Abychom vás ověřili a udrželi vaši relaci otevřenou mezi požadavky.",
                "Abychom mohli vytvářet, kontrolovat a zobrazovat pracovní rozpisy — včetně kontroly, "
                "že se přiřazení nekryje s existující směnou nebo dnem, který jste označili jako "
                "nedostupný.",
                "Aby váš manažer viděl rozpis, za který odpovídá, a hodiny, které přiděluje jednotlivým "
                "lidem.",
                "Abychom udrželi aplikaci v bezpečí, například odmítáním požadavků z jiných webů.",
            ],
            "paragraphs": [
                "Právním základem je plnění vašeho pracovního vztahu s organizací, která instanci "
                "provozuje, spolu s oprávněným zájmem této organizace na vedení pracovního rozpisu. "
                "Vaše údaje nezpracováváme k žádnému jinému účelu než k vedení rozpisu.",
            ],
        },
        {
            "heading": "3. Kdo vaše údaje vidí",
            "bullets": [
                "Vy — svůj vlastní profil, své zveřejněné směny a svou nedostupnost.",
                "Manažeři ve vaší organizaci — adresář týmu (jméno, e-mail, pozice) a celý rozpis včetně "
                "konceptů směn, které zaměstnanci zatím nevidí.",
                "Vaši přátelé — váš profil, e-mail, seznam přátel a stav online. Kdo s vámi má "
                "nevyřízenou žádost o přátelství, vidí jen vaše jméno, fotografii, roli a popis.",
                "Správci instance — technici s přístupem k serveru nebo databázi.",
            ],
            "paragraphs": [
                "Vaše údaje se nikdy neprodávají, nepronajímají, nesdílejí s inzerenty ani nepředávají "
                "žádné třetí straně. Nepoužívají se k trénování modelů strojového učení.",
            ],
        },
        {
            "heading": "4. Jak dlouho údaje uchováváme",
            "paragraphs": [
                "Údaje o účtu a plánování se uchovávají, dokud váš účet v instanci existuje. Když "
                "manažer smaže účet zaměstnance, záznam účtu, jeho přiřazení ke směnám a záznamy o "
                "nedostupnosti se z databáze odstraní v rámci jedné transakce — neexistuje žádné "
                "měkké smazání ani archivní kopie.",
                "Jednorázově vygenerované heslo se uchovává v serverové relaci manažera jen po dobu "
                "nutnou k jeho jedinému zobrazení a zahodí se, jakmile se stránka vykreslí.",
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
                "Přístup je na serveru omezen podle rolí: zaměstnanec se nedostane ke koncovému bodu "
                "manažera a pokus o zobrazení směny jiného manažera uhodnutím jejího ID vrátí chybu 404.",
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
                f"Kteroukoli z těchto žádostí zašlete na {CONTACT_EMAIL} nebo manažerovi své organizace, "
                "který může váš účet přímo upravit nebo smazat.",
            ],
        },
        {
            "heading": "7. Cookies",
            "paragraphs": [
                "PlanShift nastavuje tři cookies, všechny nezbytně nutné pro fungování služby: cookie "
                "relace, díky které zůstáváte přihlášeni, cookie CSRF, která chrání formuláře před "
                "odesláním z cizích webů, a cookie jazyka, která si pamatuje zvolený jazyk. Žádná z nich "
                "se nepoužívá ke sledování ani profilování, proto není potřeba lišta se souhlasem. "
                "Pokud je zablokujete, nebudete se moci přihlásit.",
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
                f"Dotazy k těmto zásadám: {CONTACT_EMAIL}. S čímkoli, co se týká přímo vašeho rozpisu "
                "nebo účtu, se nejprve obraťte na svého manažera — spravuje instanci vaší organizace.",
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
                "PlanShift umožňuje manažerovi sestavit pracovní rozpis v kalendáři a zveřejnit ho "
                "svému týmu a zaměstnancům umožňuje vidět směny, které jim byly přiřazeny, a označit "
                "dny, kdy nejsou k dispozici. Je to nástroj pro plánování. Není to mzdový systém, "
                "docházkový systém ani závazná evidence skutečně odpracovaných hodin.",
            ],
        },
        {
            "heading": "2. Účty",
            "bullets": [
                "Účty manažerů se zakládají přes registrační stránku. Registrací přebíráte odpovědnost "
                "za tým, který následně vytvoříte.",
                "Účty zaměstnanců vytváří manažer, který obdrží vygenerované heslo zobrazené právě "
                "jednou a odpovídá za jeho bezpečné předání.",
                "Musíte uvést pravdivé jméno a funkční e-mailovou adresu a k držení účtu vám musí být "
                "alespoň 16 let, nebo musíte mít souhlas zákonného zástupce.",
                "Odpovídáte za vše, co se pod vaším účtem děje. Uchovávejte heslo v tajnosti, účet s "
                "nikým nesdílejte, a pokud máte podezření, že k němu má přístup někdo jiný, ihned to "
                "oznamte svému manažerovi.",
            ],
        },
        {
            "heading": "3. Přijatelné použití",
            "paragraphs": ["Zavazujete se, že nebudete:"],
            "bullets": [
                "Přistupovat nebo se pokoušet přistupovat k účtu, směně nebo týmu, který není váš.",
                "Zkoumat, skenovat nebo testovat zabezpečení instance ani obcházet jakoukoli kontrolu "
                "přístupu, omezení počtu požadavků nebo ověření.",
                "Automatizovat požadavky způsobem, který zhoršuje službu ostatním uživatelům.",
                "Nahrávat nebo zadávat nezákonný, urážlivý nebo záměrně zavádějící obsah, včetně "
                "falešných jmen nebo údajů o plánování zadaných s cílem poškodit kolegu.",
                "Kopírovat, stahovat nebo dále šířit údaje jiné organizace.",
            ],
        },
        {
            "heading": "4. Povinnosti manažerů",
            "paragraphs": [
                "Pokud máte účet manažera, rozhodujete o tom, jaké osobní údaje o svých zaměstnancích "
                "do instance zadáte, a jste pro ně správcem údajů. Odpovídáte za to, že máte k jejich "
                "zpracování právní základ, že svůj tým informujete o používání PlanShiftu a že "
                "vyhovíte jeho žádostem o přístup k údajům nebo jejich výmaz. Naše Zásady ochrany "
                "osobních údajů vysvětlují, co aplikace vaším jménem ukládá.",
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
                "Manažer může účet zaměstnance kdykoli deaktivovat nebo smazat, například když někdo z "
                "týmu odejde. Provozovatel instance může pozastavit jakýkoli účet, který tyto podmínky "
                "porušuje. Službu můžete kdykoli přestat používat a požádat manažera o smazání svého "
                "účtu; smazáním se odstraní váš účet, přiřazení a záznamy o nedostupnosti.",
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
