# TV Hub — Channel Logos Pack

Generated for Antigravity from a live read of the Cloudflare tunnel app on **2026-10-27** (Asia/Tbilisi).

## Summary

- **Channels:** 62
- **Logos found & HTTP-verified (image/*):** 62/62
- **Streams live (direct):** 18
- **Streams live only via hub `/api/stream/proxy`:** 40
- **Streams dead / broken:** 4 — `ge-pirveli` (TV Pirveli (ტვ პირველი)), `ru-rossiya1` (Россия 1 HD), `ru-rossiya24` (Россия 24 HD), `ge-euronews` (Euronews Georgia)
- **Languages:** English=10, Georgian=19, Russian=33

## Important notes about current app logos

Every channel currently points at a local SVG under `/static/logos/*.svg`. Those files are **AI-generated placeholders**, not real brand marks. Example bug: Bloomberg TV uses `en-nasa.svg` which literally draws the NASA meatball + the word "NASA TELEVISION HD". Replace them with the `logo_url` column below.

Prefer hosting logos yourself (download into `/static/logos/real/` or a CDN) because many iptv-org entries are Imgur links that can expire. Wikimedia Commons URLs are more stable.

## Channel table

| # | ID | Name | tvg-id | Lang | Genre | Stream | Logo (verified) | Source |
|---|----|------|--------|------|-------|--------|-----------------|--------|
| 1 | `ge-silk` | Silk Universal HD | `SilkUniversal.ge` | Georgian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/z0XHsPE.png) | imgur |
| 2 | `ru-match` | МАТЧ! ТВ HD | `Match.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/iKZvKyP.png) | imgur |
| 3 | `en-bloomberg` | Bloomberg TV HD | `BloombergTV.us` | English | News | `live` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/New_Bloomberg_Logo.svg/960px-New_Bloomberg_Logo.svg.png) | wikimedia |
| 4 | `ge-rugby` | Rugby TV (რაგბი ტვ) | `RugbyTV.ge` | Georgian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/FLh1Brr.png) | imgur |
| 5 | `ru-matchpremier` | МАТЧ! Премьер HD | `MatchPremier.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/GQPyHYK.png) | imgur |
| 6 | `ge-setanta1` | Setanta Sports 1 HD | `SetantaSportsGeorgia.ge` | Georgian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/VwQnBqa.png) | iptv-org |
| 7 | `ru-matchfootball` | МАТЧ! Футбол 2 HD | `MatchFutbol2.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/WhdGfSo.png) | iptv-org |
| 8 | `en-redbull` | Red Bull TV | `RedBullTV.at` | English | Sports | `live` / hls | [link](https://i.postimg.cc/8c78JM28/image.png) | imgur |
| 9 | `ge-setanta2` | Setanta Sports 2 HD | `SetantaSportsPlusGeorgia.ge` | Georgian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/ZtoZQUV.png) | iptv-org |
| 10 | `ru-matchboec` | МАТЧ! Боец HD | `MatchBoets.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/DogOkA4.png) | imgur |
| 11 | `ge-1tv` | 1TV (პირველი არხი) | `1TV.ge` | Georgian | News | `live` / hls | [link](https://i.imgur.com/FSkYLPK.png) | imgur |
| 12 | `ru-khl` | КХЛ Prime (KHL) | `KHL.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/RgdHdOV.png) | imgur |
| 13 | `en-dw` | DW English News | `DW.de` | English | News | `live` / hls | [link](https://i.imgur.com/MNKkgfa.png) | imgur |
| 14 | `ge-imedi` | Imedi TV HD (იმედი) | `ImediTV.ge` | Georgian | Entertainment | `live` / hls | [link](https://i.imgur.com/94hNyxZ.png) | imgur |
| 15 | `ru-sts` | СТС HD | `STS.ru` | Russian | Entertainment | `live_via_proxy` / hls | [link](https://i.imgur.com/ilUzAeb.png) | imgur |
| 16 | `en-cbc` | CBC News 24/7 | `CBCNewsNetwork.ca` | English | News | `live` / hls | [link](https://i.imgur.com/SjTdhvJ.png) | imgur |
| 17 | `ge-formula` | Formula HD (ფორმულა) | `Formula.ge` | Georgian | News | `live` / hls | [link](https://i.imgur.com/fsqBn8G.png) | imgur |
| 18 | `ru-tnt` | ТНТ HD | `TNT.ru` | Russian | Entertainment | `live_via_proxy` / hls | [link](https://i.ibb.co/HDmdRFR1/N-Baltic-2025.webp) | imgur |
| 19 | `ge-rustavi2` | Rustavi 2 (რუსთავი 2) | `Rustavi2.ge` | Georgian | Entertainment | `live_via_proxy` / hls | [link](https://i.imgur.com/rPqd1Cx.png) | imgur |
| 20 | `ru-friday` | Пятница! HD | `Friday.ru` | Russian | Entertainment | `live_via_proxy` / hls | [link](https://antifriz.tv/storage/images/pack_logos/71e74d77d2a9f55f496870623e5f7203.png) | iptv-org |
| 21 | `ge-pirveli` | TV Pirveli (ტვ პირველი) | `TVPirveli.ge` | Georgian | News | `dead` / mpegts | [link](https://i.imgur.com/cGHsM1x.png) | imgur |
| 22 | `ru-rossiya1` | Россия 1 HD | `Russia1.ru` | Russian | News | `dead` / hls | [link](https://uut-telecom.ru/wp-content/uploads/2021/12/rossiya-1-hd.png) | iptv-org |
| 23 | `en-cbccomedy` | CBC Comedy 24/7 | `—` | English | Entertainment | `live` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png) | wikimedia |
| 24 | `ru-rossiya24` | Россия 24 HD | `Russia24.ru` | Russian | News | `dead` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Rossiya-24_Logo.svg/960px-Rossiya-24_Logo.svg.png) | wikimedia |
| 25 | `en-cbckids` | CBC Kids | `CBCKids.ca` | English | Kids | `live` / hls | [link](https://cbc-centredepresse.tor1.digitaloceanspaces.com/upload/site/en/article_picture/3984/CBC_Kids_Logo.jpg) | iptv-org |
| 26 | `ge-comedy` | Comedy TV (კომედი არხი) | `ComedyTV.ge` | Georgian | Entertainment | `live_via_proxy` / hls | [link](https://i.imgur.com/i1TANKv.png) | imgur |
| 27 | `ru-tv3` | ТВ-3 HD | `TV3.ru` | Russian | Entertainment | `live_via_proxy` / hls | [link](https://i.imgur.com/JLAvq8O.png) | imgur |
| 28 | `en-heartland` | Heartland 24/7 | `—` | English | Entertainment | `live` / hls | [link](https://upload.wikimedia.org/wikipedia/en/b/ba/Heartland_TV_logo.png) | wikimedia |
| 29 | `ge-gds` | GDS TV (სერიალები & კინო) | `GDSTV.ge` | Georgian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/gv61tFf.png) | imgur |
| 30 | `ru-domashniy` | Домашний HD | `Domashniy.ru` | Russian | Entertainment | `live_via_proxy` / hls | [link](https://i.imgur.com/WaLwOyt.jpeg) | imgur |
| 31 | `en-murdoch` | Murdoch Mysteries | `—` | English | Movies | `live` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png) | wikimedia |
| 32 | `ge-marao` | Marao TV (მარაო) | `MaraoTV.ge` | Georgian | Entertainment | `live_via_proxy` / hls | [link](https://i.imgur.com/Nurmw1G.png) | imgur |
| 33 | `ru-mosfilm` | Мосфильм | `MosfilmGoldCollection.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/95Y8jb6.png) | imgur |
| 34 | `en-schitt` | Schitt's Creek | `—` | English | Entertainment | `live` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/4/40/Schitt%27s_Creek_logo.png) | wikimedia |
| 35 | `ge-postv` | POSTV HD | `PosTV.ge` | Georgian | News | `live_via_proxy` / hls | [link](https://i.imgur.com/UOiXFEW.png) | imgur |
| 36 | `ru-domkino` | Дом Кино HD | `Domkino.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/%D0%9B%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF_%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB%D0%B0_%D0%94%D0%BE%D0%BC_%D0%9A%D0%B8%D0%BD%D0%BE.png/960px-%D0%9B%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF_%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB%D0%B0_%D0%94%D0%BE%D0%BC_%D0%9A%D0%B8%D0%BD%D0%BE.png) | wikimedia |
| 37 | `ge-bmg` | BMG TV (ბიზნეს მედია) | `BMGTV.ge` | Georgian | News | `live` / hls | [link](https://i.imgur.com/vGLkTPA.png) | imgur |
| 38 | `ru-domkinopremium` | Дом Кино Премиум HD | `DomkinoPremium.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/rJpQtvK.png) | imgur |
| 39 | `en-cbcexplore` | CBC Explore Docs | `—` | English | Documentaries | `live` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png) | wikimedia |
| 40 | `ge-adjara` | Adjara TV (აჭარის ტვ) | `AjaraTV.ge` | Georgian | News | `live_via_proxy` / hls | [link](https://i.imgur.com/Isrc9KE.png) | iptv-org |
| 41 | `ru-kinokomediya` | Кинокомедия HD | `Kinokomedija.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/dVjtth0.png) | imgur |
| 42 | `ge-palitra` | Palitra News (პალიტრა) | `PalitraNews.ge` | Georgian | News | `live_via_proxy` / hls | [link](https://i.imgur.com/BW95PMF.png) | imgur |
| 43 | `ru-kinohit` | Кинохит HD | `KinoHit.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/Ge8vkQM.png) | imgur |
| 44 | `ge-2tv` | 2 TV (მეორე არხი) | `2TV.ge` | Georgian | Documentaries | `live` / hls | [link](https://i.imgur.com/FJBL6zI.png) | iptv-org |
| 45 | `ru-kinosemya` | Киносемья HD | `Kinosemja.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/4BF5VeK.png) | imgur |
| 46 | `ge-euronews` | Euronews Georgia | `EuronewsGeorgia.ge` | Georgian | News | `dead` / mpegts | [link](https://i.imgur.com/VNJ4soR.png) | imgur |
| 47 | `ru-kinouzhas` | Киноужас HD | `Kinouzhas.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/mAcAAQF.png) | imgur |
| 48 | `ru-tv1000` | Viju TV1000 HD | `vijuTV1000.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/ZMsyjSr.png) | imgur |
| 49 | `ge-ertsulovneba` | Ertsulovneba (ერთსულოვნება) | `Ertsulovneba.ge` | Georgian | Documentaries | `live` / hls | [link](https://i.imgur.com/KuuODMM.png) | imgur |
| 50 | `ru-tv1000action` | Viju TV1000 Action HD | `vijuTV1000action.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/TMmyuzh.png) | imgur |
| 51 | `ru-amediahit` | Amedia Hit HD | `AmediaHit.ru` | Russian | Movies | `live_via_proxy` / hls | [link](https://i.imgur.com/a8ZBGBw.png) | imgur |
| 52 | `ru-karusel` | Карусель HD | `Carousel.ru` | Russian | Kids | `live` / hls | [link](https://i.imgur.com/4wmnx1W.png) | imgur |
| 53 | `ru-mult` | Мульт HD | `Mult.ru` | Russian | Kids | `live` / hls | [link](https://i.imgur.com/xi351Fx.png) | imgur |
| 54 | `ru-stskids` | СТС Kids HD | `STSkids.ru` | Russian | Kids | `live_via_proxy` / hls | [link](https://i.imgur.com/o9kLpAL.png) | imgur |
| 55 | `ru-discovery` | Discovery Channel HD | `DiscoveryChannel.ru` | Russian | Documentaries | `live_via_proxy` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/2019_Discovery_logo.svg/960px-2019_Discovery_logo.svg.png) | wikimedia |
| 56 | `ru-natgeo` | National Geographic HD | `NationalGeographic.ru` | Russian | Documentaries | `live_via_proxy` / hls | [link](https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Natgeologo.svg/960px-Natgeologo.svg.png) | wikimedia |
| 57 | `ru-muztv` | МУЗ-ТВ HD | `MuzTV.ru` | Russian | Music | `live_via_proxy` / hls | [link](https://i.imgur.com/BtqrHmz.png) | imgur |
| 58 | `ru-rutv` | RU.TV HD | `RUTV.ru` | Russian | Music | `live_via_proxy` / hls | [link](https://rutv.by/wp-content/uploads/2020/09/logo.png) | iptv-org |
| 59 | `ru-avto24` | Авто 24 HD | `Avto24.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/GXSXmN2.png) | imgur |
| 60 | `ru-okhotarybalka` | Охота и рыбалка HD | `Okhotairybalka.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/nZwBaeW.png) | imgur |
| 61 | `ru-dikayaokhota` | Дикая охота HD | `Dikayaokhota.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/EOue13e.png) | imgur |
| 62 | `ru-dikayarybalka` | Дикая рыбалка HD | `Dikayarybalka.ru` | Russian | Sports | `live_via_proxy` / hls | [link](https://i.imgur.com/e3BFVgt.png) | imgur |

## Full logo URL list (copy-paste TSV)

```
ge-silk	Silk Universal HD	SilkUniversal.ge	https://i.imgur.com/z0XHsPE.png
ru-match	МАТЧ! ТВ HD	Match.ru	https://i.imgur.com/iKZvKyP.png
en-bloomberg	Bloomberg TV HD	BloombergTV.us	https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/New_Bloomberg_Logo.svg/960px-New_Bloomberg_Logo.svg.png
ge-rugby	Rugby TV (რაგბი ტვ)	RugbyTV.ge	https://i.imgur.com/FLh1Brr.png
ru-matchpremier	МАТЧ! Премьер HD	MatchPremier.ru	https://i.imgur.com/GQPyHYK.png
ge-setanta1	Setanta Sports 1 HD	SetantaSportsGeorgia.ge	https://i.imgur.com/VwQnBqa.png
ru-matchfootball	МАТЧ! Футбол 2 HD	MatchFutbol2.ru	https://i.imgur.com/WhdGfSo.png
en-redbull	Red Bull TV	RedBullTV.at	https://i.postimg.cc/8c78JM28/image.png
ge-setanta2	Setanta Sports 2 HD	SetantaSportsPlusGeorgia.ge	https://i.imgur.com/ZtoZQUV.png
ru-matchboec	МАТЧ! Боец HD	MatchBoets.ru	https://i.imgur.com/DogOkA4.png
ge-1tv	1TV (პირველი არხი)	1TV.ge	https://i.imgur.com/FSkYLPK.png
ru-khl	КХЛ Prime (KHL)	KHL.ru	https://i.imgur.com/RgdHdOV.png
en-dw	DW English News	DW.de	https://i.imgur.com/MNKkgfa.png
ge-imedi	Imedi TV HD (იმედი)	ImediTV.ge	https://i.imgur.com/94hNyxZ.png
ru-sts	СТС HD	STS.ru	https://i.imgur.com/ilUzAeb.png
en-cbc	CBC News 24/7	CBCNewsNetwork.ca	https://i.imgur.com/SjTdhvJ.png
ge-formula	Formula HD (ფორმულა)	Formula.ge	https://i.imgur.com/fsqBn8G.png
ru-tnt	ТНТ HD	TNT.ru	https://i.ibb.co/HDmdRFR1/N-Baltic-2025.webp
ge-rustavi2	Rustavi 2 (რუსთავი 2)	Rustavi2.ge	https://i.imgur.com/rPqd1Cx.png
ru-friday	Пятница! HD	Friday.ru	https://antifriz.tv/storage/images/pack_logos/71e74d77d2a9f55f496870623e5f7203.png
ge-pirveli	TV Pirveli (ტვ პირველი)	TVPirveli.ge	https://i.imgur.com/cGHsM1x.png
ru-rossiya1	Россия 1 HD	Russia1.ru	https://uut-telecom.ru/wp-content/uploads/2021/12/rossiya-1-hd.png
en-cbccomedy	CBC Comedy 24/7		https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png
ru-rossiya24	Россия 24 HD	Russia24.ru	https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Rossiya-24_Logo.svg/960px-Rossiya-24_Logo.svg.png
en-cbckids	CBC Kids	CBCKids.ca	https://cbc-centredepresse.tor1.digitaloceanspaces.com/upload/site/en/article_picture/3984/CBC_Kids_Logo.jpg
ge-comedy	Comedy TV (კომედი არხი)	ComedyTV.ge	https://i.imgur.com/i1TANKv.png
ru-tv3	ТВ-3 HD	TV3.ru	https://i.imgur.com/JLAvq8O.png
en-heartland	Heartland 24/7		https://upload.wikimedia.org/wikipedia/en/b/ba/Heartland_TV_logo.png
ge-gds	GDS TV (სერიალები & კინო)	GDSTV.ge	https://i.imgur.com/gv61tFf.png
ru-domashniy	Домашний HD	Domashniy.ru	https://i.imgur.com/WaLwOyt.jpeg
en-murdoch	Murdoch Mysteries		https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png
ge-marao	Marao TV (მარაო)	MaraoTV.ge	https://i.imgur.com/Nurmw1G.png
ru-mosfilm	Мосфильм	MosfilmGoldCollection.ru	https://i.imgur.com/95Y8jb6.png
en-schitt	Schitt's Creek		https://upload.wikimedia.org/wikipedia/commons/4/40/Schitt%27s_Creek_logo.png
ge-postv	POSTV HD	PosTV.ge	https://i.imgur.com/UOiXFEW.png
ru-domkino	Дом Кино HD	Domkino.ru	https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/%D0%9B%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF_%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB%D0%B0_%D0%94%D0%BE%D0%BC_%D0%9A%D0%B8%D0%BD%D0%BE.png/960px-%D0%9B%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF_%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB%D0%B0_%D0%94%D0%BE%D0%BC_%D0%9A%D0%B8%D0%BD%D0%BE.png
ge-bmg	BMG TV (ბიზნეს მედია)	BMGTV.ge	https://i.imgur.com/vGLkTPA.png
ru-domkinopremium	Дом Кино Премиум HD	DomkinoPremium.ru	https://i.imgur.com/rJpQtvK.png
en-cbcexplore	CBC Explore Docs		https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png
ge-adjara	Adjara TV (აჭარის ტვ)	AjaraTV.ge	https://i.imgur.com/Isrc9KE.png
ru-kinokomediya	Кинокомедия HD	Kinokomedija.ru	https://i.imgur.com/dVjtth0.png
ge-palitra	Palitra News (პალიტრა)	PalitraNews.ge	https://i.imgur.com/BW95PMF.png
ru-kinohit	Кинохит HD	KinoHit.ru	https://i.imgur.com/Ge8vkQM.png
ge-2tv	2 TV (მეორე არხი)	2TV.ge	https://i.imgur.com/FJBL6zI.png
ru-kinosemya	Киносемья HD	Kinosemja.ru	https://i.imgur.com/4BF5VeK.png
ge-euronews	Euronews Georgia	EuronewsGeorgia.ge	https://i.imgur.com/VNJ4soR.png
ru-kinouzhas	Киноужас HD	Kinouzhas.ru	https://i.imgur.com/mAcAAQF.png
ru-tv1000	Viju TV1000 HD	vijuTV1000.ru	https://i.imgur.com/ZMsyjSr.png
ge-ertsulovneba	Ertsulovneba (ერთსულოვნება)	Ertsulovneba.ge	https://i.imgur.com/KuuODMM.png
ru-tv1000action	Viju TV1000 Action HD	vijuTV1000action.ru	https://i.imgur.com/TMmyuzh.png
ru-amediahit	Amedia Hit HD	AmediaHit.ru	https://i.imgur.com/a8ZBGBw.png
ru-karusel	Карусель HD	Carousel.ru	https://i.imgur.com/4wmnx1W.png
ru-mult	Мульт HD	Mult.ru	https://i.imgur.com/xi351Fx.png
ru-stskids	СТС Kids HD	STSkids.ru	https://i.imgur.com/o9kLpAL.png
ru-discovery	Discovery Channel HD	DiscoveryChannel.ru	https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/2019_Discovery_logo.svg/960px-2019_Discovery_logo.svg.png
ru-natgeo	National Geographic HD	NationalGeographic.ru	https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Natgeologo.svg/960px-Natgeologo.svg.png
ru-muztv	МУЗ-ТВ HD	MuzTV.ru	https://i.imgur.com/BtqrHmz.png
ru-rutv	RU.TV HD	RUTV.ru	https://rutv.by/wp-content/uploads/2020/09/logo.png
ru-avto24	Авто 24 HD	Avto24.ru	https://i.imgur.com/GXSXmN2.png
ru-okhotarybalka	Охота и рыбалка HD	Okhotairybalka.ru	https://i.imgur.com/nZwBaeW.png
ru-dikayaokhota	Дикая охота HD	Dikayaokhota.ru	https://i.imgur.com/EOue13e.png
ru-dikayarybalka	Дикая рыбалка HD	Dikayarybalka.ru	https://i.imgur.com/e3BFVgt.png
```

## JSON mapping (id → logo)

```json
{
  "ge-silk": {
    "name": "Silk Universal HD",
    "tvg_id": "SilkUniversal.ge",
    "logo": "https://i.imgur.com/z0XHsPE.png"
  },
  "ru-match": {
    "name": "МАТЧ! ТВ HD",
    "tvg_id": "Match.ru",
    "logo": "https://i.imgur.com/iKZvKyP.png"
  },
  "en-bloomberg": {
    "name": "Bloomberg TV HD",
    "tvg_id": "BloombergTV.us",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/New_Bloomberg_Logo.svg/960px-New_Bloomberg_Logo.svg.png"
  },
  "ge-rugby": {
    "name": "Rugby TV (რაგბი ტვ)",
    "tvg_id": "RugbyTV.ge",
    "logo": "https://i.imgur.com/FLh1Brr.png"
  },
  "ru-matchpremier": {
    "name": "МАТЧ! Премьер HD",
    "tvg_id": "MatchPremier.ru",
    "logo": "https://i.imgur.com/GQPyHYK.png"
  },
  "ge-setanta1": {
    "name": "Setanta Sports 1 HD",
    "tvg_id": "SetantaSportsGeorgia.ge",
    "logo": "https://i.imgur.com/VwQnBqa.png"
  },
  "ru-matchfootball": {
    "name": "МАТЧ! Футбол 2 HD",
    "tvg_id": "MatchFutbol2.ru",
    "logo": "https://i.imgur.com/WhdGfSo.png"
  },
  "en-redbull": {
    "name": "Red Bull TV",
    "tvg_id": "RedBullTV.at",
    "logo": "https://i.postimg.cc/8c78JM28/image.png"
  },
  "ge-setanta2": {
    "name": "Setanta Sports 2 HD",
    "tvg_id": "SetantaSportsPlusGeorgia.ge",
    "logo": "https://i.imgur.com/ZtoZQUV.png"
  },
  "ru-matchboec": {
    "name": "МАТЧ! Боец HD",
    "tvg_id": "MatchBoets.ru",
    "logo": "https://i.imgur.com/DogOkA4.png"
  },
  "ge-1tv": {
    "name": "1TV (პირველი არხი)",
    "tvg_id": "1TV.ge",
    "logo": "https://i.imgur.com/FSkYLPK.png"
  },
  "ru-khl": {
    "name": "КХЛ Prime (KHL)",
    "tvg_id": "KHL.ru",
    "logo": "https://i.imgur.com/RgdHdOV.png"
  },
  "en-dw": {
    "name": "DW English News",
    "tvg_id": "DW.de",
    "logo": "https://i.imgur.com/MNKkgfa.png"
  },
  "ge-imedi": {
    "name": "Imedi TV HD (იმედი)",
    "tvg_id": "ImediTV.ge",
    "logo": "https://i.imgur.com/94hNyxZ.png"
  },
  "ru-sts": {
    "name": "СТС HD",
    "tvg_id": "STS.ru",
    "logo": "https://i.imgur.com/ilUzAeb.png"
  },
  "en-cbc": {
    "name": "CBC News 24/7",
    "tvg_id": "CBCNewsNetwork.ca",
    "logo": "https://i.imgur.com/SjTdhvJ.png"
  },
  "ge-formula": {
    "name": "Formula HD (ფორმულა)",
    "tvg_id": "Formula.ge",
    "logo": "https://i.imgur.com/fsqBn8G.png"
  },
  "ru-tnt": {
    "name": "ТНТ HD",
    "tvg_id": "TNT.ru",
    "logo": "https://i.ibb.co/HDmdRFR1/N-Baltic-2025.webp"
  },
  "ge-rustavi2": {
    "name": "Rustavi 2 (რუსთავი 2)",
    "tvg_id": "Rustavi2.ge",
    "logo": "https://i.imgur.com/rPqd1Cx.png"
  },
  "ru-friday": {
    "name": "Пятница! HD",
    "tvg_id": "Friday.ru",
    "logo": "https://antifriz.tv/storage/images/pack_logos/71e74d77d2a9f55f496870623e5f7203.png"
  },
  "ge-pirveli": {
    "name": "TV Pirveli (ტვ პირველი)",
    "tvg_id": "TVPirveli.ge",
    "logo": "https://i.imgur.com/cGHsM1x.png"
  },
  "ru-rossiya1": {
    "name": "Россия 1 HD",
    "tvg_id": "Russia1.ru",
    "logo": "https://uut-telecom.ru/wp-content/uploads/2021/12/rossiya-1-hd.png"
  },
  "en-cbccomedy": {
    "name": "CBC Comedy 24/7",
    "tvg_id": null,
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png"
  },
  "ru-rossiya24": {
    "name": "Россия 24 HD",
    "tvg_id": "Russia24.ru",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Rossiya-24_Logo.svg/960px-Rossiya-24_Logo.svg.png"
  },
  "en-cbckids": {
    "name": "CBC Kids",
    "tvg_id": "CBCKids.ca",
    "logo": "https://cbc-centredepresse.tor1.digitaloceanspaces.com/upload/site/en/article_picture/3984/CBC_Kids_Logo.jpg"
  },
  "ge-comedy": {
    "name": "Comedy TV (კომედი არხი)",
    "tvg_id": "ComedyTV.ge",
    "logo": "https://i.imgur.com/i1TANKv.png"
  },
  "ru-tv3": {
    "name": "ТВ-3 HD",
    "tvg_id": "TV3.ru",
    "logo": "https://i.imgur.com/JLAvq8O.png"
  },
  "en-heartland": {
    "name": "Heartland 24/7",
    "tvg_id": null,
    "logo": "https://upload.wikimedia.org/wikipedia/en/b/ba/Heartland_TV_logo.png"
  },
  "ge-gds": {
    "name": "GDS TV (სერიალები & კინო)",
    "tvg_id": "GDSTV.ge",
    "logo": "https://i.imgur.com/gv61tFf.png"
  },
  "ru-domashniy": {
    "name": "Домашний HD",
    "tvg_id": "Domashniy.ru",
    "logo": "https://i.imgur.com/WaLwOyt.jpeg"
  },
  "en-murdoch": {
    "name": "Murdoch Mysteries",
    "tvg_id": null,
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png"
  },
  "ge-marao": {
    "name": "Marao TV (მარაო)",
    "tvg_id": "MaraoTV.ge",
    "logo": "https://i.imgur.com/Nurmw1G.png"
  },
  "ru-mosfilm": {
    "name": "Мосфильм",
    "tvg_id": "MosfilmGoldCollection.ru",
    "logo": "https://i.imgur.com/95Y8jb6.png"
  },
  "en-schitt": {
    "name": "Schitt's Creek",
    "tvg_id": null,
    "logo": "https://upload.wikimedia.org/wikipedia/commons/4/40/Schitt%27s_Creek_logo.png"
  },
  "ge-postv": {
    "name": "POSTV HD",
    "tvg_id": "PosTV.ge",
    "logo": "https://i.imgur.com/UOiXFEW.png"
  },
  "ru-domkino": {
    "name": "Дом Кино HD",
    "tvg_id": "Domkino.ru",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/%D0%9B%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF_%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB%D0%B0_%D0%94%D0%BE%D0%BC_%D0%9A%D0%B8%D0%BD%D0%BE.png/960px-%D0%9B%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF_%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB%D0%B0_%D0%94%D0%BE%D0%BC_%D0%9A%D0%B8%D0%BD%D0%BE.png"
  },
  "ge-bmg": {
    "name": "BMG TV (ბიზნეს მედია)",
    "tvg_id": "BMGTV.ge",
    "logo": "https://i.imgur.com/vGLkTPA.png"
  },
  "ru-domkinopremium": {
    "name": "Дом Кино Премиум HD",
    "tvg_id": "DomkinoPremium.ru",
    "logo": "https://i.imgur.com/rJpQtvK.png"
  },
  "en-cbcexplore": {
    "name": "CBC Explore Docs",
    "tvg_id": null,
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/CBCT-DT_2017.svg/960px-CBCT-DT_2017.svg.png"
  },
  "ge-adjara": {
    "name": "Adjara TV (აჭარის ტვ)",
    "tvg_id": "AjaraTV.ge",
    "logo": "https://i.imgur.com/Isrc9KE.png"
  },
  "ru-kinokomediya": {
    "name": "Кинокомедия HD",
    "tvg_id": "Kinokomedija.ru",
    "logo": "https://i.imgur.com/dVjtth0.png"
  },
  "ge-palitra": {
    "name": "Palitra News (პალიტრა)",
    "tvg_id": "PalitraNews.ge",
    "logo": "https://i.imgur.com/BW95PMF.png"
  },
  "ru-kinohit": {
    "name": "Кинохит HD",
    "tvg_id": "KinoHit.ru",
    "logo": "https://i.imgur.com/Ge8vkQM.png"
  },
  "ge-2tv": {
    "name": "2 TV (მეორე არხი)",
    "tvg_id": "2TV.ge",
    "logo": "https://i.imgur.com/FJBL6zI.png"
  },
  "ru-kinosemya": {
    "name": "Киносемья HD",
    "tvg_id": "Kinosemja.ru",
    "logo": "https://i.imgur.com/4BF5VeK.png"
  },
  "ge-euronews": {
    "name": "Euronews Georgia",
    "tvg_id": "EuronewsGeorgia.ge",
    "logo": "https://i.imgur.com/VNJ4soR.png"
  },
  "ru-kinouzhas": {
    "name": "Киноужас HD",
    "tvg_id": "Kinouzhas.ru",
    "logo": "https://i.imgur.com/mAcAAQF.png"
  },
  "ru-tv1000": {
    "name": "Viju TV1000 HD",
    "tvg_id": "vijuTV1000.ru",
    "logo": "https://i.imgur.com/ZMsyjSr.png"
  },
  "ge-ertsulovneba": {
    "name": "Ertsulovneba (ერთსულოვნება)",
    "tvg_id": "Ertsulovneba.ge",
    "logo": "https://i.imgur.com/KuuODMM.png"
  },
  "ru-tv1000action": {
    "name": "Viju TV1000 Action HD",
    "tvg_id": "vijuTV1000action.ru",
    "logo": "https://i.imgur.com/TMmyuzh.png"
  },
  "ru-amediahit": {
    "name": "Amedia Hit HD",
    "tvg_id": "AmediaHit.ru",
    "logo": "https://i.imgur.com/a8ZBGBw.png"
  },
  "ru-karusel": {
    "name": "Карусель HD",
    "tvg_id": "Carousel.ru",
    "logo": "https://i.imgur.com/4wmnx1W.png"
  },
  "ru-mult": {
    "name": "Мульт HD",
    "tvg_id": "Mult.ru",
    "logo": "https://i.imgur.com/xi351Fx.png"
  },
  "ru-stskids": {
    "name": "СТС Kids HD",
    "tvg_id": "STSkids.ru",
    "logo": "https://i.imgur.com/o9kLpAL.png"
  },
  "ru-discovery": {
    "name": "Discovery Channel HD",
    "tvg_id": "DiscoveryChannel.ru",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f1/2019_Discovery_logo.svg/960px-2019_Discovery_logo.svg.png"
  },
  "ru-natgeo": {
    "name": "National Geographic HD",
    "tvg_id": "NationalGeographic.ru",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Natgeologo.svg/960px-Natgeologo.svg.png"
  },
  "ru-muztv": {
    "name": "МУЗ-ТВ HD",
    "tvg_id": "MuzTV.ru",
    "logo": "https://i.imgur.com/BtqrHmz.png"
  },
  "ru-rutv": {
    "name": "RU.TV HD",
    "tvg_id": "RUTV.ru",
    "logo": "https://rutv.by/wp-content/uploads/2020/09/logo.png"
  },
  "ru-avto24": {
    "name": "Авто 24 HD",
    "tvg_id": "Avto24.ru",
    "logo": "https://i.imgur.com/GXSXmN2.png"
  },
  "ru-okhotarybalka": {
    "name": "Охота и рыбалка HD",
    "tvg_id": "Okhotairybalka.ru",
    "logo": "https://i.imgur.com/nZwBaeW.png"
  },
  "ru-dikayaokhota": {
    "name": "Дикая охота HD",
    "tvg_id": "Dikayaokhota.ru",
    "logo": "https://i.imgur.com/EOue13e.png"
  },
  "ru-dikayarybalka": {
    "name": "Дикая рыбалка HD",
    "tvg_id": "Dikayarybalka.ru",
    "logo": "https://i.imgur.com/e3BFVgt.png"
  }
}
```

## Antigravity prompt — wire real logos

```text
You are editing my TV Hub app (FastAPI + static frontend).

GOAL: Replace the AI-generated /static/logos/*.svg placeholders with real channel logos.

DATA FILES (already prepared):
- channel-logos.json
- channel-logos.csv
- channel-logos.md

Each channel has: id, name, tvg_id (iptv-org, may be null), logo_url (HTTP-verified image), logo_source.

IMPLEMENTATION:
1. Prefer storing logos locally for reliability:
   - Download each logo_url into /static/logos/real/{id}.png (convert SVG/WebP to PNG if needed).
   - Update the channel catalog so logo = /static/logos/real/{id}.png
2. Matching rules when applying logos:
   - Primary key: channel id
   - Fallback: normalize name (lowercase, strip HD/TV/(...), collapse spaces) and match
   - Fallback: match tvg-id / iptv-org id
3. Frontend (app.js renderChannels):
   - Keep loading="lazy" and referrerpolicy="no-referrer"
   - Keep monogram fallback onerror (handleImgError) — do NOT remove it
   - Add decoding="async" and fixed width/height (e.g. 72) to reduce CLS
4. Do NOT keep the broken Bloomberg → en-nasa.svg mapping (it draws NASA).
5. CBC FAST channels without a dedicated mark (Comedy/Explore/Murdoch) may use the CBC Television gem; Schitt's Creek has a real Commons logo in the JSON.
6. After change, hard-refresh and confirm every card shows a real logo, not initials.

```

Companion files: `channel-logos.json`, `channel-logos.csv`.