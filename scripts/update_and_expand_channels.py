import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PLAYLIST_FILE = BASE_DIR / "playlists" / "default_channels.m3u"
LOGOS_DIR = BASE_DIR / "static" / "logos"

CHANNELS = [
    # ========================================================
    # 🇬🇪 GEORGIAN CHANNELS (ქართული არხები & სპორტი)
    # ========================================================
    {
        "id": "ge-silk",
        "name": "Silk Universal HD (სილკ უნივერსალი)",
        "tvg_name": "Silk Universal HD",
        "url": "https://streaming-hls3.televiziebi.org/hls/silk.m3u8",
        "group": "Georgian",
        "genre": "Sports",
        "popularity": 100,
        "logo": "/static/logos/ge-silk.svg"
    },
    {
        "id": "ge-rugby",
        "name": "Rugby TV Georgia (რაგბი ტვ HD)",
        "tvg_name": "Rugby TV (რაგბი ტვ)",
        "url": "https://streaming-hls3.televizia.org/hls/ragbitv.m3u8",
        "group": "Georgian",
        "genre": "Sports",
        "popularity": 99,
        "logo": "/static/logos/ge-rugby.svg"
    },
    {
        "id": "ge-setanta1",
        "name": "Setanta Sports 1 HD (სეტანტა 1)",
        "tvg_name": "Setanta Sports 1 HD",
        "url": "http://stream.mcquack.net/234/index.m3u8",
        "group": "Georgian",
        "genre": "Sports",
        "popularity": 98,
        "logo": "/static/logos/ge-setanta1.svg"
    },
    {
        "id": "ge-setanta2",
        "name": "Setanta Sports 2 HD (სეტანტა 2)",
        "tvg_name": "Setanta Sports 2 HD",
        "url": "http://stream.mcquack.net/235/index.m3u8",
        "group": "Georgian",
        "genre": "Sports",
        "popularity": 97,
        "logo": "/static/logos/ge-setanta2.svg"
    },
    {
        "id": "ge-setantaplus",
        "name": "Setanta Sports + HD (სეტანტა +)",
        "tvg_name": "Setanta Sports + HD",
        "url": "http://stream.mcquack.net/236/index.m3u8",
        "group": "Georgian",
        "genre": "Sports",
        "popularity": 96,
        "logo": "/static/logos/ge-setanta1.svg"
    },
    {
        "id": "ge-1tv",
        "name": "1TV First Channel (პირველი არხი HD)",
        "tvg_name": "1TV (პირველი არხი)",
        "url": "https://tv.cdn.xsg.ge/gpb-1tv/index.m3u8",
        "group": "Georgian",
        "genre": "News",
        "popularity": 95,
        "logo": "/static/logos/ge-1tv.svg"
    },
    {
        "id": "ge-imedi",
        "name": "Imedi TV HD (ტელეკომპანია იმედი)",
        "tvg_name": "Imedi TV HD (იმედი)",
        "url": "https://tv.cdn.xsg.ge/imedihd/index.m3u8",
        "group": "Georgian",
        "genre": "Entertainment",
        "popularity": 94,
        "logo": "/static/logos/ge-imedi.svg"
    },
    {
        "id": "ge-formula",
        "name": "Formula TV HD (ფორმულა)",
        "tvg_name": "Formula HD (ფორმულა)",
        "url": "https://c4635.cdn.xsg.ge/c4635/TVFormula/index.m3u8",
        "group": "Georgian",
        "genre": "News",
        "popularity": 93,
        "logo": "/static/logos/ge-formula.svg"
    },
    {
        "id": "ge-rustavi2",
        "name": "Rustavi 2 HD (რუსთავი 2)",
        "tvg_name": "Rustavi 2 (რუსთავი 2)",
        "url": "https://streaming-hls3.televiziebi.org/hls/rustavi2.m3u8",
        "group": "Georgian",
        "genre": "Entertainment",
        "popularity": 92,
        "logo": "/static/logos/ge-rustavi2.svg"
    },
    {
        "id": "ge-pirveli",
        "name": "TV Pirveli (ტვ პირველი)",
        "tvg_name": "TV Pirveli (ტვ პირველი)",
        "url": "http://nue01-edge01.itdc.ge/pirvelitv/mpegts",
        "group": "Georgian",
        "genre": "News",
        "popularity": 91,
        "logo": "/static/logos/ge-pirveli.svg"
    },
    {
        "id": "ge-comedy",
        "name": "Comedy TV HD (კომედი არხი)",
        "tvg_name": "Comedy TV (კომედი არხი)",
        "url": "https://streaming-hls3.televiziebi.org/hls/comedy.m3u8",
        "group": "Georgian",
        "genre": "Entertainment",
        "popularity": 90,
        "logo": "/static/logos/ge-comedy.svg"
    },
    {
        "id": "ge-gds",
        "name": "GDS TV HD (სერიალები & კინო)",
        "tvg_name": "GDS TV (სერიალები & კინო)",
        "url": "https://streaming-hls3.televiziebi.org/hls/gds.m3u8",
        "group": "Georgian",
        "genre": "Movies",
        "popularity": 89,
        "logo": "/static/logos/ge-gds.svg"
    },
    {
        "id": "ge-marao",
        "name": "Marao TV (მარაო)",
        "tvg_name": "Marao TV (მარაო)",
        "url": "https://streaming-hls3.televiziebi.org/hls/marao.m3u8",
        "group": "Georgian",
        "genre": "Entertainment",
        "popularity": 88,
        "logo": "/static/logos/ge-marao.svg"
    },
    {
        "id": "ge-postv",
        "name": "POSTV HD (პოსტვ)",
        "tvg_name": "POSTV HD",
        "url": "https://streaming-hls3.televiziebi.org/hls/postv.m3u8",
        "group": "Georgian",
        "genre": "News",
        "popularity": 87,
        "logo": "/static/logos/ge-postv.svg"
    },
    {
        "id": "ge-bmg",
        "name": "BMG TV (Business Media Georgia)",
        "tvg_name": "BMG TV (ბიზნეს მედია)",
        "url": "https://tv.nucast.tv/lb/ge/bmg/index.m3u8",
        "group": "Georgian",
        "genre": "News",
        "popularity": 86,
        "logo": "/static/logos/ge-bmg.svg"
    },
    {
        "id": "ge-adjara",
        "name": "Adjara TV HD (აჭარის ტელევიზია)",
        "tvg_name": "Adjara TV (აჭარის ტვ)",
        "url": "https://streaming-hls3.televiziebi.org/hls/adjara.m3u8",
        "group": "Georgian",
        "genre": "News",
        "popularity": 85,
        "logo": "/static/logos/ge-adjara.svg"
    },
    {
        "id": "ge-palitra",
        "name": "Palitra News (პალიტრა ნიუსი)",
        "tvg_name": "Palitra News (პალიტრა)",
        "url": "https://streaming-hls3.televiziebi.org/hls/palitra.m3u8",
        "group": "Georgian",
        "genre": "News",
        "popularity": 84,
        "logo": "/static/logos/ge-palitra.svg"
    },
    {
        "id": "ge-2tv",
        "name": "2 TV (მეორე არხი HD)",
        "tvg_name": "2 TV (მეორე არხი)",
        "url": "https://tv.cdn.xsg.ge/gpb-2tv/index.m3u8",
        "group": "Georgian",
        "genre": "Documentaries",
        "popularity": 83,
        "logo": "/static/logos/ge-2tv.svg"
    },
    {
        "id": "ge-euronews",
        "name": "Euronews Georgia",
        "tvg_name": "Euronews Georgia",
        "url": "http://nue01-edge01.itdc.ge/euronewsgeorgia/mpegts",
        "group": "Georgian",
        "genre": "News",
        "popularity": 82,
        "logo": "/static/logos/ge-euronews.svg"
    },
    {
        "id": "ge-ertsulovneba",
        "name": "Ertsulovneba (ერთსულოვნება)",
        "tvg_name": "Ertsulovneba (ერთსულოვნება)",
        "url": "https://stream.sstv.ge/live/sstv/playlist.m3u8",
        "group": "Georgian",
        "genre": "Documentaries",
        "popularity": 80,
        "logo": "/static/logos/ge-ertsulovneba.svg"
    },

    # ========================================================
    # 🇷🇺 RUSSIAN SPORTS & MOVIE CHANNELS (Спорт & Кино)
    # ========================================================
    {
        "id": "ru-match",
        "name": "МАТЧ! ТВ HD (Спорт)",
        "tvg_name": "МАТЧ! ТВ HD",
        "url": "http://stream.mcquack.net/141/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 100,
        "logo": "/static/logos/ru-match.svg"
    },
    {
        "id": "ru-matchpremier",
        "name": "МАТЧ! Премьер HD (РПЛ)",
        "tvg_name": "МАТЧ! Премьер HD",
        "url": "http://stream.mcquack.net/142/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 99,
        "logo": "/static/logos/ru-matchpremier.svg"
    },
    {
        "id": "ru-matchfootball1",
        "name": "МАТЧ! Футбол 1 HD (Еврофутбол)",
        "tvg_name": "МАТЧ! Футбол 1 HD",
        "url": "http://stream.mcquack.net/143/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 98,
        "logo": "/static/logos/ru-matchfootball.svg"
    },
    {
        "id": "ru-matchfootball2",
        "name": "МАТЧ! Футбол 2 HD (Ла Лига & Серия А)",
        "tvg_name": "МАТЧ! Футбол 2 HD",
        "url": "http://stream.mcquack.net/144/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 97,
        "logo": "/static/logos/ru-matchfootball.svg"
    },
    {
        "id": "ru-matchfootball3",
        "name": "МАТЧ! Футбол 3 HD (Бундеслига)",
        "tvg_name": "МАТЧ! Футбол 3 HD",
        "url": "http://stream.mcquack.net/145/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 96,
        "logo": "/static/logos/ru-matchfootball.svg"
    },
    {
        "id": "ru-matchboec",
        "name": "МАТЧ! Боец HD (UFC, MMA, Бокс)",
        "tvg_name": "МАТЧ! Боец HD",
        "url": "http://stream.mcquack.net/146/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 95,
        "logo": "/static/logos/ru-matchboec.svg"
    },
    {
        "id": "ru-khltv",
        "name": "КХЛ ТВ HD (Хоккей)",
        "tvg_name": "КХЛ ТВ HD",
        "url": "http://stream.mcquack.net/150/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 94,
        "logo": "/static/logos/ru-khl.svg"
    },
    {
        "id": "ru-khlprime",
        "name": "КХЛ Prime HD (Прайм Хоккей)",
        "tvg_name": "КХЛ Prime HD",
        "url": "http://stream.mcquack.net/151/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 93,
        "logo": "/static/logos/ru-khl.svg"
    },

    # --- Russian Movies & Cinema ---
    {
        "id": "ru-kinohit",
        "name": "Кинохит HD (Мировые Хиты)",
        "tvg_name": "Кинохит HD",
        "url": "http://stream.mcquack.net/101/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 95,
        "logo": "/static/logos/ru-kinohit.svg"
    },
    {
        "id": "ru-kinokomediya",
        "name": "Кинокомедия HD",
        "tvg_name": "Кинокомедия HD",
        "url": "http://stream.mcquack.net/104/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 94,
        "logo": "/static/logos/ru-kinokomediya.svg"
    },
    {
        "id": "ru-kinomix",
        "name": "Киномикс HD (Экшн & Блокбастеры)",
        "tvg_name": "Киномикс HD",
        "url": "http://stream.mcquack.net/106/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 93,
        "logo": "/static/logos/ru-kinohit.svg"
    },
    {
        "id": "ru-tv1000",
        "name": "Viju TV1000 HD (Кино)",
        "tvg_name": "Viju TV1000 HD",
        "url": "http://stream.mcquack.net/110/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 92,
        "logo": "/static/logos/ru-tv1000.svg"
    },
    {
        "id": "ru-tv1000action",
        "name": "Viju TV1000 Action HD (Боевики & Триллер)",
        "tvg_name": "Viju TV1000 Action HD",
        "url": "http://stream.mcquack.net/111/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 91,
        "logo": "/static/logos/ru-tv1000action.svg"
    },
    {
        "id": "ru-tv1000rus",
        "name": "TV1000 Русское кино HD",
        "tvg_name": "TV1000 Русское кино",
        "url": "http://stream.mcquack.net/112/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 90,
        "logo": "/static/logos/ru-tv1000.svg"
    },
    {
        "id": "ru-domkino",
        "name": "Дом Кино HD (Культовые Фильмы)",
        "tvg_name": "Дом Кино HD",
        "url": "http://stream.mcquack.net/115/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 89,
        "logo": "/static/logos/ru-domkino.svg"
    },
    {
        "id": "ru-domkinopremium",
        "name": "Дом Кино Премиум HD (Премьеры)",
        "tvg_name": "Дом Кино Премиум HD",
        "url": "http://stream.mcquack.net/116/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 88,
        "logo": "/static/logos/ru-domkinopremium.svg"
    },
    {
        "id": "ru-amediahit",
        "name": "Amedia Hit HD (Хитовые Сериалы)",
        "tvg_name": "Amedia Hit HD",
        "url": "http://stream.mcquack.net/120/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 87,
        "logo": "/static/logos/ru-amediahit.svg"
    },
    {
        "id": "ru-amediapremium",
        "name": "Amedia Premium HD (HBO & Blockbusters)",
        "tvg_name": "Amedia Premium HD",
        "url": "http://stream.mcquack.net/121/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 86,
        "logo": "/static/logos/ru-amediahit.svg"
    },
    {
        "id": "ru-mosfilm",
        "name": "Мосфильм (Золотая коллекция)",
        "tvg_name": "Мосфильм",
        "url": "http://stream.mcquack.net/125/index.m3u8",
        "group": "Russian",
        "genre": "Movies",
        "popularity": 85,
        "logo": "/static/logos/ru-mosfilm.svg"
    },

    # --- Russian Entertainment & General ---
    {
        "id": "ru-sts",
        "name": "СТС HD (Телеканал)",
        "tvg_name": "СТС HD",
        "url": "http://stream.mcquack.net/138/index.m3u8",
        "group": "Russian",
        "genre": "Entertainment",
        "popularity": 84,
        "logo": "/static/logos/ru-sts.svg"
    },
    {
        "id": "ru-tnt",
        "name": "ТНТ HD (Телеканал)",
        "tvg_name": "ТНТ HD",
        "url": "http://stream.mcquack.net/135/index.m3u8",
        "group": "Russian",
        "genre": "Entertainment",
        "popularity": 83,
        "logo": "/static/logos/ru-tnt.svg"
    },
    {
        "id": "ru-friday",
        "name": "Пятница! HD (Телеканал)",
        "tvg_name": "Пятница! HD",
        "url": "http://stream.mcquack.net/181/index.m3u8",
        "group": "Russian",
        "genre": "Entertainment",
        "popularity": 82,
        "logo": "/static/logos/ru-friday.svg"
    },
    {
        "id": "ru-tv3",
        "name": "ТВ-3 HD (Мистика & Кино)",
        "tvg_name": "ТВ-3 HD",
        "url": "http://stream.mcquack.net/136/index.m3u8",
        "group": "Russian",
        "genre": "Entertainment",
        "popularity": 81,
        "logo": "/static/logos/ru-tv3.svg"
    },
    {
        "id": "ru-domashniy",
        "name": "Домашний HD (Телеканал)",
        "tvg_name": "Домашний HD",
        "url": "http://stream.mcquack.net/227/index.m3u8",
        "group": "Russian",
        "genre": "Entertainment",
        "popularity": 80,
        "logo": "/static/logos/ru-domashniy.svg"
    },
    {
        "id": "ru-rossiya1",
        "name": "Россия 1 HD (ВГТРК)",
        "tvg_name": "Россия 1 HD",
        "url": "http://chgtrk.ru/pl/stream/hls/R1_360p/index.m3u8",
        "group": "Russian",
        "genre": "News",
        "popularity": 79,
        "logo": "/static/logos/ru-rossiya1.svg"
    },
    {
        "id": "ru-rossiya24",
        "name": "Россия 24 HD (Новости)",
        "tvg_name": "Россия 24 HD",
        "url": "http://77.232.131.211/Rossiya24/index.m3u8",
        "group": "Russian",
        "genre": "News",
        "popularity": 78,
        "logo": "/static/logos/ru-rossiya24.svg"
    },
    {
        "id": "ru-karusel",
        "name": "Карусель HD (Детский)",
        "tvg_name": "Карусель HD",
        "url": "https://stream8.cinerama.uz/1034/index.m3u8",
        "group": "Russian",
        "genre": "Kids",
        "popularity": 77,
        "logo": "/static/logos/ru-karusel.svg"
    },
    {
        "id": "ru-mult",
        "name": "Мульт HD (Мультфильмы)",
        "tvg_name": "Мульт HD",
        "url": "https://stream8.cinerama.uz/1246/index.m3u8",
        "group": "Russian",
        "genre": "Kids",
        "popularity": 76,
        "logo": "/static/logos/ru-mult.svg"
    },
    {
        "id": "ru-stskids",
        "name": "СТС Kids HD",
        "tvg_name": "СТС Kids HD",
        "url": "http://stream.mcquack.net/197/index.m3u8",
        "group": "Russian",
        "genre": "Kids",
        "popularity": 75,
        "logo": "/static/logos/ru-stskids.svg"
    },
    {
        "id": "ru-avto24",
        "name": "Авто 24 HD (Автоспорт)",
        "tvg_name": "Авто 24 HD",
        "url": "http://stream.mcquack.net/78/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 74,
        "logo": "/static/logos/ru-avto24.svg"
    },
    {
        "id": "ru-okhotarybalka",
        "name": "Охота и рыбалка HD",
        "tvg_name": "Охота и рыбалка HD",
        "url": "http://stream.mcquack.net/155/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 73,
        "logo": "/static/logos/ru-okhotarybalka.svg"
    },
    {
        "id": "ru-dikayaokhota",
        "name": "Дикая охота HD",
        "tvg_name": "Дикая охота HD",
        "url": "http://stream.mcquack.net/274/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 72,
        "logo": "/static/logos/ru-dikayaokhota.svg"
    },
    {
        "id": "ru-dikayarybalka",
        "name": "Дикая рыбалка HD",
        "tvg_name": "Дикая рыбалка HD",
        "url": "http://stream.mcquack.net/275/index.m3u8",
        "group": "Russian",
        "genre": "Sports",
        "popularity": 71,
        "logo": "/static/logos/ru-dikayarybalka.svg"
    },

    # ========================================================
    # 🇬🇧 ENGLISH CHANNELS (Sports, Movies & News)
    # ========================================================
    {
        "id": "en-redbull",
        "name": "Red Bull TV (Live Extreme Sports)",
        "tvg_name": "Red Bull TV",
        "url": "https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8",
        "group": "English",
        "genre": "Sports",
        "popularity": 100,
        "logo": "/static/logos/en-redbull.svg"
    },
    {
        "id": "en-bloomberg",
        "name": "Bloomberg TV HD (Global Financial)",
        "tvg_name": "Bloomberg TV HD",
        "url": "https://bloomberg.com/media-manifest/streams/us.m3u8",
        "group": "English",
        "genre": "News",
        "popularity": 99,
        "logo": "/static/logos/en-nasa.svg"
    },
    {
        "id": "en-dw",
        "name": "DW English News HD",
        "tvg_name": "DW English News",
        "url": "https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8",
        "group": "English",
        "genre": "News",
        "popularity": 98,
        "logo": "/static/logos/en-dw.svg"
    },
    {
        "id": "en-murdoch",
        "name": "Murdoch Mysteries 24/7 (Cinema)",
        "tvg_name": "Murdoch Mysteries",
        "url": "https://amagi-streams.akamaized.net/hls/live/2113390/cbcmurdoch/master.m3u8",
        "group": "English",
        "genre": "Movies",
        "popularity": 95,
        "logo": "/static/logos/en-murdoch.svg"
    },
    {
        "id": "en-heartland",
        "name": "Heartland 24/7 Series TV",
        "tvg_name": "Heartland 24/7",
        "url": "https://amagi-streams.akamaized.net/hls/live/2113391/cbcheartland/master.m3u8",
        "group": "English",
        "genre": "Entertainment",
        "popularity": 94,
        "logo": "/static/logos/en-heartland.svg"
    },
    {
        "id": "en-schitt",
        "name": "Schitt's Creek 24/7 (Comedy Series)",
        "tvg_name": "Schitt's Creek",
        "url": "https://amagi-streams.akamaized.net/hls/live/2120484/schittscreek/master.m3u8",
        "group": "English",
        "genre": "Entertainment",
        "popularity": 93,
        "logo": "/static/logos/en-schitt.svg"
    },
    {
        "id": "en-cbc",
        "name": "CBC News 24/7 HD",
        "tvg_name": "CBC News 24/7",
        "url": "https://amagi-streams.akamaized.net/hls/live/2110960/cbcnewsbc/master.m3u8",
        "group": "English",
        "genre": "News",
        "popularity": 92,
        "logo": "/static/logos/en-cbc.svg"
    },
    {
        "id": "en-cbccomedy",
        "name": "CBC Comedy 24/7",
        "tvg_name": "CBC Comedy 24/7",
        "url": "https://amagi-streams.akamaized.net/hls/live/2110963/cbccomedy/master.m3u8",
        "group": "English",
        "genre": "Entertainment",
        "popularity": 91,
        "logo": "/static/logos/en-cbccomedy.svg"
    },
    {
        "id": "en-cbckids",
        "name": "CBC Kids Channel (Cartoons)",
        "tvg_name": "CBC Kids",
        "url": "https://amagi-streams.akamaized.net/hls/live/2120483/cbckids/master.m3u8",
        "group": "English",
        "genre": "Kids",
        "popularity": 90,
        "logo": "/static/logos/en-cbckids.svg"
    },
    {
        "id": "en-cbcexplore",
        "name": "CBC Explore Documentaries",
        "tvg_name": "CBC Explore Docs",
        "url": "https://amagi-streams.akamaized.net/hls/live/2110962/cbcexplore/master.m3u8",
        "group": "English",
        "genre": "Documentaries",
        "popularity": 89,
        "logo": "/static/logos/en-cbcexplore.svg"
    }
]

def generate_m3u():
    lines = ["#EXTM3U\n"]
    current_group = None

    for ch in CHANNELS:
        if ch["group"] != current_group:
            current_group = ch["group"]
            lines.append(f"\n# ========================================================")
            lines.append(f"# {current_group.upper()} CHANNELS")
            lines.append(f"# ========================================================\n")

        extinf = (
            f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["tvg_name"]}" '
            f'tvg-logo="{ch["logo"]}" group-title="{ch["group"]}" '
            f'genre="{ch["genre"]}" popularity="{ch["popularity"]}",{ch["name"]}\n'
            f'{ch["url"]}\n'
        )
        lines.append(extinf)

    PLAYLIST_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"Successfully generated {len(CHANNELS)} premium channels into {PLAYLIST_FILE}!")

if __name__ == "__main__":
    generate_m3u()
