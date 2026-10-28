import os
from pathlib import Path

logos_dir = Path("static/logos")
logos_dir.mkdir(parents=True, exist_ok=True)

logos = {
    # ========================================================
    # 🇬🇪 GEORGIAN CHANNELS
    # ========================================================
    "ge-silk.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="silk_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4a154b"/>
      <stop offset="100%" stop-color="#1f0724"/>
    </linearGradient>
    <linearGradient id="silk_curl" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#e056fd"/>
      <stop offset="100%" stop-color="#be2edd"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#silk_bg)"/>
  <circle cx="100" cy="78" r="42" fill="none" stroke="url(#silk_curl)" stroke-width="12" stroke-dasharray="180 50" transform="rotate(-35 100 78)"/>
  <circle cx="100" cy="78" r="22" fill="none" stroke="#ffffff" stroke-width="8" stroke-dasharray="100 30" transform="rotate(45 100 78)"/>
  <circle cx="100" cy="78" r="8" fill="#e056fd"/>
  <text x="100" y="146" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">SILK</text>
  <text x="100" y="172" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif" font-size="14" font-weight="800" fill="#e056fd" text-anchor="middle" letter-spacing="2.5">UNIVERSAL</text>
</svg>""",

    "ge-rugby.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="rugby_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#020617"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#rugby_bg)"/>
  <ellipse cx="100" cy="76" rx="46" ry="28" fill="#dc2626" transform="rotate(-28 100 76)"/>
  <ellipse cx="100" cy="76" rx="40" ry="23" fill="#ef4444" transform="rotate(-28 100 76)"/>
  <path d="M84 54 C94 70, 106 82, 116 98" stroke="#ffffff" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M92 68 L98 66 M96 74 L102 72 M100 80 L106 78" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
  <rect x="80" y="130" width="40" height="20" rx="4" fill="#dc2626"/>
  <text x="100" y="145" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="900" fill="#ffffff" text-anchor="middle">TV</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">რაგბი TV</text>
</svg>""",

    "ge-setanta1.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="setanta1_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#111827"/>
      <stop offset="100%" stop-color="#030712"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#setanta1_bg)"/>
  <circle cx="100" cy="76" r="42" fill="none" stroke="#eab308" stroke-width="10"/>
  <path d="M116 60 C108 50, 88 52, 86 66 C84 80, 116 78, 114 94 C112 106, 92 106, 84 96" fill="none" stroke="#eab308" stroke-width="9" stroke-linecap="round"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1.5">SETANTA</text>
  <rect x="65" y="154" width="70" height="22" rx="4" fill="#eab308"/>
  <text x="100" y="170" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="900" fill="#000000" text-anchor="middle" letter-spacing="1">SPORTS 1</text>
</svg>""",

    "ge-setanta2.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="setanta2_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#111827"/>
      <stop offset="100%" stop-color="#030712"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#setanta2_bg)"/>
  <circle cx="100" cy="76" r="42" fill="none" stroke="#38bdf8" stroke-width="10"/>
  <path d="M116 60 C108 50, 88 52, 86 66 C84 80, 116 78, 114 94 C112 106, 92 106, 84 96" fill="none" stroke="#38bdf8" stroke-width="9" stroke-linecap="round"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1.5">SETANTA</text>
  <rect x="65" y="154" width="70" height="22" rx="4" fill="#38bdf8"/>
  <text x="100" y="170" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="900" fill="#000000" text-anchor="middle" letter-spacing="1">SPORTS 2</text>
</svg>""",

    "ge-1tv.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="1tv_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#1tv_bg)"/>
  <circle cx="100" cy="78" r="44" fill="#0284c7"/>
  <circle cx="100" cy="78" r="38" fill="#0f172a"/>
  <path d="M92 66 L104 54 L104 102 M88 102 L114 102" stroke="#38bdf8" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <text x="100" y="150" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle">1TV</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#38bdf8" text-anchor="middle">პირველი არხი</text>
</svg>""",

    "ge-2tv.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="2tv_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#134e4a"/>
      <stop offset="100%" stop-color="#042f2e"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#2tv_bg)"/>
  <circle cx="100" cy="78" r="42" fill="#14b8a6"/>
  <circle cx="100" cy="78" r="36" fill="#042f2e"/>
  <text x="100" y="96" font-family="-apple-system, Arial, sans-serif" font-size="46" font-weight="900" fill="#2dd4bf" text-anchor="middle">2</text>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle">2TV</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#2dd4bf" text-anchor="middle">მეორე არხი</text>
</svg>""",

    "ge-imedi.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="imedi_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ea580c"/>
      <stop offset="100%" stop-color="#9a3412"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#imedi_bg)"/>
  <circle cx="100" cy="54" r="12" fill="#ffffff"/>
  <path d="M88 78 C88 78, 112 78, 112 106 C112 124, 88 124, 88 124" fill="none" stroke="#ffffff" stroke-width="16" stroke-linecap="round"/>
  <text x="100" y="156" font-family="-apple-system, Arial, sans-serif" font-size="26" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">IMEDI</text>
  <text x="100" y="178" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="700" fill="#fed7aa" text-anchor="middle">იმედი HD</text>
</svg>""",

    "ge-formula.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="formula_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0891b2"/>
      <stop offset="100%" stop-color="#164e63"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#formula_bg)"/>
  <path d="M70 48 L130 48 L120 70 L92 70 L88 86 L116 86 L108 106 L80 106 L66 140 L42 140 Z" fill="#ffffff"/>
  <text x="100" y="162" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">FORMULA</text>
  <text x="100" y="182" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#a5f3fc" text-anchor="middle">ფორმულა</text>
</svg>""",

    "ge-rustavi2.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="r2_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#dc2626"/>
      <stop offset="100%" stop-color="#991b1b"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#r2_bg)"/>
  <text x="100" y="112" font-family="-apple-system, Arial, sans-serif" font-size="94" font-weight="900" fill="#ffffff" text-anchor="middle">2</text>
  <text x="100" y="154" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1.5">RUSTAVI 2</text>
  <text x="100" y="176" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fecaca" text-anchor="middle">რუსთავი 2</text>
</svg>""",

    "ge-pirveli.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#000000"/>
  <rect x="30" y="35" width="140" height="78" rx="16" fill="#facc15"/>
  <text x="100" y="96" font-family="-apple-system, Arial, sans-serif" font-size="62" font-weight="900" fill="#000000" text-anchor="middle">1</text>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#facc15" text-anchor="middle" letter-spacing="1">TV PIRVELI</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="700" fill="#ffffff" text-anchor="middle">ტვ პირველი</text>
</svg>""",

    "ge-comedy.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="comedy_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#comedy_bg)"/>
  <circle cx="100" cy="76" r="44" fill="#ffffff"/>
  <circle cx="84" cy="66" r="7" fill="#000000"/>
  <circle cx="116" cy="66" r="7" fill="#000000"/>
  <path d="M78 84 Q100 112 122 84 Z" fill="#dc2626"/>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">COMEDY</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#fef3c7" text-anchor="middle">კომედი არხი</text>
</svg>""",

    "ge-gds.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="gds_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#gds_bg)"/>
  <rect x="35" y="48" width="130" height="58" rx="14" fill="none" stroke="#38bdf8" stroke-width="4"/>
  <text x="100" y="92" font-family="-apple-system, Arial, sans-serif" font-size="36" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="4">GDS</text>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#38bdf8" text-anchor="middle" letter-spacing="2">TV HD</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#93c5fd" text-anchor="middle">სერიალები &amp; კინო</text>
</svg>""",

    "ge-marao.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="marao_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#db2777"/>
      <stop offset="100%" stop-color="#9d174d"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#marao_bg)"/>
  <path d="M60 98 Q100 45 140 98 Z" fill="#ffffff" opacity="0.9"/>
  <path d="M75 98 L100 56 L125 98" stroke="#db2777" stroke-width="3" fill="none"/>
  <circle cx="100" cy="98" r="8" fill="#ffffff"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">MARAO</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="15" font-weight="700" fill="#fbcfe8" text-anchor="middle">მარაო TV</text>
</svg>""",

    "ge-postv.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="postv_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#dc2626"/>
      <stop offset="100%" stop-color="#18181b"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#postv_bg)"/>
  <polygon points="100,40 155,62 145,115 100,135 55,115 45,62" fill="none" stroke="#ffffff" stroke-width="6"/>
  <text x="100" y="98" font-family="-apple-system, Arial, sans-serif" font-size="26" font-weight="900" fill="#ffffff" text-anchor="middle">POS</text>
  <text x="100" y="160" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">POSTV</text>
  <text x="100" y="182" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fca5a5" text-anchor="middle">პოსტვ HD</text>
</svg>""",

    "ge-bmg.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="bmg_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#020617"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#bmg_bg)"/>
  <path d="M50 96 L85 62 L115 92 L145 48" stroke="#84cc16" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="130,48 145,48 145,62" stroke="#84cc16" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="34" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="3">BMG</text>
  <text x="100" y="170" font-family="-apple-system, Arial, sans-serif" font-size="12" font-weight="800" fill="#84cc16" text-anchor="middle" letter-spacing="1.5">BUSINESS MEDIA</text>
</svg>""",

    "ge-adjara.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="adj_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#0369a1"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#adj_bg)"/>
  <path d="M50 82 Q75 58 100 82 T150 82" stroke="#ffffff" stroke-width="8" fill="none" stroke-linecap="round"/>
  <path d="M60 98 Q80 78 100 98 T140 98" stroke="#bae6fd" stroke-width="6" fill="none" stroke-linecap="round"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">ADJARA</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="15" font-weight="700" fill="#e0f2fe" text-anchor="middle">აჭარის ტვ HD</text>
</svg>""",

    "ge-palitra.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#1e293b"/>
  <circle cx="65" cy="62" r="14" fill="#ef4444"/>
  <circle cx="100" cy="50" r="14" fill="#3b82f6"/>
  <circle cx="135" cy="62" r="14" fill="#eab308"/>
  <circle cx="80" cy="88" r="14" fill="#10b981"/>
  <circle cx="120" cy="88" r="14" fill="#a855f7"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">PALITRA</text>
  <text x="100" y="170" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="700" fill="#94a3b8" text-anchor="middle">პალიტრა ნიუსი</text>
</svg>""",

    "ge-euronews.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#000000"/>
  <text x="100" y="90" font-family="-apple-system, Arial, sans-serif" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="-0.5">euronews.</text>
  <rect x="50" y="112" width="100" height="24" rx="6" fill="#0284c7"/>
  <text x="100" y="129" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">GEORGIA</text>
  <text x="100" y="168" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="600" fill="#94a3b8" text-anchor="middle">ევრონიუსი</text>
</svg>""",

    "ge-ertsulovneba.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="ert_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#ert_bg)"/>
  <path d="M100 45 L100 115 M80 65 L120 65" stroke="#f59e0b" stroke-width="10" stroke-linecap="round"/>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="16" font-weight="900" fill="#ffffff" text-anchor="middle">ერთსულოვნება</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fcd34d" text-anchor="middle">SSTV GEORGIA</text>
</svg>""",

    # ========================================================
    # 🇷🇺 RUSSIAN CHANNELS
    # ========================================================
    "ru-match.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="match_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#dc2626"/>
      <stop offset="100%" stop-color="#991b1b"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#match_bg)"/>
  <text x="100" y="112" font-family="-apple-system, Arial, sans-serif" font-size="44" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">МАТЧ!</text>
  <rect x="55" y="134" width="90" height="24" rx="4" fill="#000000"/>
  <text x="100" y="151" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">СПОРТ HD</text>
</svg>""",

    "ru-matchpremier.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#000000"/>
  <text x="100" y="96" font-family="-apple-system, Arial, sans-serif" font-size="38" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">МАТЧ!</text>
  <rect x="35" y="120" width="130" height="26" rx="4" fill="#d97706"/>
  <text x="100" y="138" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="900" fill="#000000" text-anchor="middle" letter-spacing="2">ПРЕМЬЕР</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="12" font-weight="700" fill="#d97706" text-anchor="middle" letter-spacing="1">РПЛ ФУТБОЛ</text>
</svg>""",

    "ru-matchfootball.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="mf_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#15803d"/>
      <stop offset="100%" stop-color="#14532d"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#mf_bg)"/>
  <circle cx="100" cy="74" r="34" fill="none" stroke="#ffffff" stroke-width="6"/>
  <polygon points="100,54 116,66 110,84 90,84 84,66" fill="#ffffff"/>
  <text x="100" y="140" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">МАТЧ!</text>
  <text x="100" y="168" font-family="-apple-system, Arial, sans-serif" font-size="15" font-weight="900" fill="#86efac" text-anchor="middle" letter-spacing="1.5">ФУТБОЛ HD</text>
</svg>""",

    "ru-matchboec.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="mb_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#991b1b"/>
      <stop offset="100%" stop-color="#450a0a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#mb_bg)"/>
  <polygon points="100,38 135,52 148,88 135,124 100,138 65,124 52,88 65,52" fill="none" stroke="#f87171" stroke-width="6"/>
  <text x="100" y="96" font-family="-apple-system, Arial, sans-serif" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle">БОЕЦ</text>
  <text x="100" y="162" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">МАТЧ! БОЕЦ</text>
</svg>""",

    "ru-khl.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="khl_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#khl_bg)"/>
  <path d="M60 48 L140 48 L130 110 L100 130 L70 110 Z" fill="#0284c7" stroke="#ffffff" stroke-width="4"/>
  <text x="100" y="92" font-family="-apple-system, Arial, sans-serif" font-size="26" font-weight="900" fill="#ffffff" text-anchor="middle">КХЛ</text>
  <text x="100" y="112" font-family="-apple-system, Arial, sans-serif" font-size="12" font-weight="800" fill="#facc15" text-anchor="middle">PRIME</text>
  <text x="100" y="166" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">ХОККЕЙ HD</text>
</svg>""",

    "ru-sts.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="sts_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#sts_bg)"/>
  <text x="100" y="116" font-family="-apple-system, Arial, sans-serif" font-size="64" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">СТС</text>
  <text x="100" y="162" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">ТЕЛЕКАНАЛ</text>
</svg>""",

    "ru-tnt.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#0f172a"/>
  <!-- 3 Blocks Red, Blue, Red -->
  <rect x="34" y="60" width="40" height="56" rx="8" fill="#dc2626"/>
  <text x="54" y="102" font-family="-apple-system, Arial, sans-serif" font-size="38" font-weight="900" fill="#ffffff" text-anchor="middle">Т</text>
  <rect x="80" y="60" width="40" height="56" rx="8" fill="#2563eb"/>
  <text x="100" y="102" font-family="-apple-system, Arial, sans-serif" font-size="38" font-weight="900" fill="#ffffff" text-anchor="middle">Н</text>
  <rect x="126" y="60" width="40" height="56" rx="8" fill="#dc2626"/>
  <text x="146" y="102" font-family="-apple-system, Arial, sans-serif" font-size="38" font-weight="900" fill="#ffffff" text-anchor="middle">Т</text>
  <text x="100" y="156" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="3">ТНТ HD</text>
</svg>""",

    "ru-friday.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="friday_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#c026d3"/>
      <stop offset="100%" stop-color="#701a75"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#friday_bg)"/>
  <text x="100" y="106" font-family="-apple-system, Arial, sans-serif" font-size="34" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">пятница!</text>
  <rect x="65" y="132" width="70" height="24" rx="6" fill="#06b6d4"/>
  <text x="100" y="149" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="900" fill="#000000" text-anchor="middle" letter-spacing="1.5">HD TV</text>
</svg>""",

    "ru-rossiya1.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="r1_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1d4ed8"/>
      <stop offset="100%" stop-color="#1e3a8a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#r1_bg)"/>
  <rect x="35" y="44" width="130" height="70" rx="10" fill="#0f172a"/>
  <!-- Tricolor Bar -->
  <rect x="45" y="54" width="40" height="50" rx="4" fill="#ffffff"/>
  <rect x="45" y="70" width="40" height="17" fill="#2563eb"/>
  <rect x="45" y="87" width="40" height="17" rx="2" fill="#dc2626"/>
  <text x="126" y="96" font-family="-apple-system, Arial, sans-serif" font-size="52" font-weight="900" fill="#ffffff" text-anchor="middle">1</text>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">РОССИЯ 1</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#93c5fd" text-anchor="middle">ВГТРК HD</text>
</svg>""",

    "ru-rossiya24.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#dc2626"/>
  <text x="100" y="92" font-family="-apple-system, Arial, sans-serif" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">РОССИЯ</text>
  <rect x="60" y="110" width="80" height="36" rx="6" fill="#ffffff"/>
  <text x="100" y="137" font-family="-apple-system, Arial, sans-serif" font-size="32" font-weight="900" fill="#dc2626" text-anchor="middle">24</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#ffffff" text-anchor="middle">ИНФОРМ КАНАЛ</text>
</svg>""",

    "ru-tv3.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="tv3_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#581c87"/>
      <stop offset="100%" stop-color="#2e1065"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#tv3_bg)"/>
  <circle cx="100" cy="78" r="42" fill="none" stroke="#a855f7" stroke-width="8"/>
  <circle cx="100" cy="78" r="32" fill="none" stroke="#d8b4fe" stroke-width="4"/>
  <text x="100" y="96" font-family="-apple-system, Arial, sans-serif" font-size="52" font-weight="900" fill="#ffffff" text-anchor="middle">3</text>
  <text x="100" y="150" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">ТВ-3</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="12" font-weight="700" fill="#d8b4fe" text-anchor="middle">ВСЁ КРОМЕ ОБЫЧНОГО</text>
</svg>""",

    "ru-domashniy.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="domash_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#be123c"/>
      <stop offset="100%" stop-color="#881337"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#domash_bg)"/>
  <path d="M100 85 C95 70, 75 70, 75 88 C75 105, 100 118, 100 118 C100 118, 125 105, 125 88 C125 70, 105 70, 100 85 Z" fill="#ffffff"/>
  <text x="100" y="150" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">ДОМАШНИЙ</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fecdd3" text-anchor="middle">ТЕЛЕКАНАЛ HD</text>
</svg>""",

    "ru-mosfilm.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="mf_bg2" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#mf_bg2)"/>
  <circle cx="100" cy="74" r="42" fill="#000000" stroke="#f59e0b" stroke-width="4"/>
  <!-- Stylized Star/Monument -->
  <polygon points="100,44 107,64 128,64 111,76 117,96 100,84 83,96 89,76 72,64 93,64" fill="#f59e0b"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">МОСФИЛЬМ</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fcd34d" text-anchor="middle">ЗОЛОТАЯ КОЛЛЕКЦИЯ</text>
</svg>""",

    "ru-domkino.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="dk_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#881337"/>
      <stop offset="100%" stop-color="#4c0519"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#dk_bg)"/>
  <rect x="45" y="45" width="110" height="70" rx="8" fill="#18181b" stroke="#f59e0b" stroke-width="4"/>
  <path d="M45 65 L155 65" stroke="#f59e0b" stroke-width="3"/>
  <line x1="70" y1="45" x2="60" y2="65" stroke="#ffffff" stroke-width="3"/>
  <line x1="100" y1="45" x2="90" y2="65" stroke="#ffffff" stroke-width="3"/>
  <line x1="130" y1="45" x2="120" y2="65" stroke="#ffffff" stroke-width="3"/>
  <text x="100" y="100" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#f59e0b" text-anchor="middle">КИНО</text>
  <text x="100" y="150" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">ДОМ КИНО</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fed7aa" text-anchor="middle">ЛУЧШИЕ ФИЛЬМЫ</text>
</svg>""",

    "ru-domkinopremium.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#0a0a0a"/>
  <rect x="35" y="40" width="130" height="75" rx="10" fill="#171717" stroke="#eab308" stroke-width="4"/>
  <text x="100" y="86" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle">ДОМ КИНО</text>
  <rect x="50" y="98" width="100" height="20" rx="4" fill="#eab308"/>
  <text x="100" y="113" font-family="-apple-system, Arial, sans-serif" font-size="12" font-weight="900" fill="#000000" text-anchor="middle" letter-spacing="2">ПРЕМИУМ</text>
  <text x="100" y="162" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#eab308" text-anchor="middle" letter-spacing="1">PREMIUM HD</text>
</svg>""",

    "ru-kinokomediya.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="kkom_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ea580c"/>
      <stop offset="100%" stop-color="#9a3412"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#kkom_bg)"/>
  <circle cx="100" cy="74" r="40" fill="#ffffff"/>
  <circle cx="86" cy="65" r="6" fill="#000000"/>
  <circle cx="114" cy="65" r="6" fill="#000000"/>
  <path d="M80 82 Q100 108 120 82 Z" fill="#ea580c"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">КИНОКОМЕДИЯ</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#fed7aa" text-anchor="middle">ТЕЛЕКАНАЛ HD</text>
</svg>""",

    "ru-kinohit.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="khit_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#2563eb"/>
      <stop offset="100%" stop-color="#1e3a8a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#khit_bg)"/>
  <polygon points="100,38 110,64 138,64 116,80 124,106 100,90 76,106 84,80 62,64 90,64" fill="#38bdf8"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">КИНОХИТ</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#93c5fd" text-anchor="middle">МИРОВЫЕ ХИТЫ</text>
</svg>""",

    "ru-kinosemya.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="ksem_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#16a34a"/>
      <stop offset="100%" stop-color="#14532d"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#ksem_bg)"/>
  <circle cx="85" cy="70" r="16" fill="#ffffff"/>
  <circle cx="115" cy="70" r="16" fill="#ffffff"/>
  <path d="M70 106 C70 94, 85 94, 100 94 C115 94, 130 94, 130 106 Z" fill="#ffffff"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">КИНОСЕМЬЯ</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#bbf7d0" text-anchor="middle">ДЛЯ ВСЕЙ СЕМЬИ</text>
</svg>""",

    "ru-kinouzhas.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="kuzh_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#7f1d1d"/>
      <stop offset="100%" stop-color="#450a0a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#kuzh_bg)"/>
  <circle cx="84" cy="70" r="10" fill="#ffffff"/>
  <circle cx="116" cy="70" r="10" fill="#ffffff"/>
  <circle cx="84" cy="70" r="4" fill="#000000"/>
  <circle cx="116" cy="70" r="4" fill="#000000"/>
  <path d="M80 96 C90 108, 110 108, 120 96" stroke="#ffffff" stroke-width="6" fill="none" stroke-linecap="round"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">КИНОУЖАС</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#fca5a5" text-anchor="middle">ТРИЛЛЕРЫ &amp; УЖАСЫ</text>
</svg>""",

    "ru-tv1000.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="tv1000_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e1b4b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#tv1000_bg)"/>
  <text x="100" y="76" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#a855f7" text-anchor="middle" letter-spacing="2">VIJU</text>
  <text x="100" y="118" font-family="-apple-system, Arial, sans-serif" font-size="34" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">TV1000</text>
  <text x="100" y="162" font-family="-apple-system, Arial, sans-serif" font-size="16" font-weight="900" fill="#f59e0b" text-anchor="middle" letter-spacing="2">CINEMA HD</text>
</svg>""",

    "ru-tv1000action.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#09090b"/>
  <text x="100" y="70" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#a855f7" text-anchor="middle" letter-spacing="2">VIJU</text>
  <text x="100" y="106" font-family="-apple-system, Arial, sans-serif" font-size="30" font-weight="900" fill="#ffffff" text-anchor="middle">TV1000</text>
  <rect x="50" y="122" width="100" height="24" rx="4" fill="#dc2626"/>
  <text x="100" y="139" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">ACTION</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#f87171" text-anchor="middle">БОЕВИКИ &amp; КИНО</text>
</svg>""",

    "ru-amediahit.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#18181b"/>
  <polygon points="100,45 130,105 70,105" fill="#dc2626"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">AMEDIA</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="16" font-weight="900" fill="#dc2626" text-anchor="middle" letter-spacing="2">HIT HD</text>
</svg>""",

    "ru-karusel.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="karusel_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#karusel_bg)"/>
  <!-- Merry go round roof -->
  <polygon points="100,38 145,68 55,68" fill="#facc15"/>
  <circle cx="100" cy="94" r="22" fill="#ffffff"/>
  <text x="100" y="104" font-family="-apple-system, Arial, sans-serif" font-size="28" font-weight="900" fill="#ec4899" text-anchor="middle">★</text>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">КАРУСЕЛЬ</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#facc15" text-anchor="middle">ДЕТСКИЙ ТЕЛЕКАНАЛ</text>
</svg>""",

    "ru-mult.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="mult_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#mult_bg)"/>
  <circle cx="80" cy="65" r="14" fill="#ffffff"/>
  <circle cx="120" cy="65" r="14" fill="#ffffff"/>
  <circle cx="80" cy="65" r="7" fill="#000000"/>
  <circle cx="120" cy="65" r="7" fill="#000000"/>
  <path d="M75 85 Q100 115 125 85 Z" fill="#ffffff"/>
  <text x="100" y="150" font-family="-apple-system, Arial, sans-serif" font-size="34" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">МУЛЬТ</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fef3c7" text-anchor="middle">МУЛЬТФИЛЬМЫ</text>
</svg>""",

    "ru-stskids.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="stskids_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f97316"/>
      <stop offset="100%" stop-color="#ea580c"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#stskids_bg)"/>
  <text x="100" y="96" font-family="-apple-system, Arial, sans-serif" font-size="52" font-weight="900" fill="#ffffff" text-anchor="middle">СТС</text>
  <rect x="55" y="115" width="90" height="28" rx="8" fill="#3b82f6"/>
  <text x="100" y="135" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">KIDS</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fef08a" text-anchor="middle">ДЛЯ ДЕТЕЙ</text>
</svg>""",

    "ru-discovery.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="disc_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#0369a1"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#disc_bg)"/>
  <circle cx="100" cy="75" r="38" fill="none" stroke="#ffffff" stroke-width="8"/>
  <circle cx="100" cy="75" r="24" fill="#38bdf8"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">Discovery</text>
  <text x="100" y="170" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#bae6fd" text-anchor="middle">CHANNEL HD</text>
</svg>""",

    "ru-natgeo.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#000000"/>
  <rect x="75" y="40" width="50" height="70" rx="4" fill="none" stroke="#facc15" stroke-width="12"/>
  <text x="100" y="142" font-family="-apple-system, Arial, sans-serif" font-size="16" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">NATIONAL</text>
  <text x="100" y="164" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#ffffff" text-anchor="middle" letter-spacing="1">GEOGRAPHIC</text>
</svg>""",

    "ru-muztv.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="muz_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ec4899"/>
      <stop offset="100%" stop-color="#8b5cf6"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#muz_bg)"/>
  <text x="100" y="106" font-family="-apple-system, Arial, sans-serif" font-size="52" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">МУЗ</text>
  <rect x="65" y="125" width="70" height="26" rx="6" fill="#ffffff"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="16" font-weight="900" fill="#ec4899" text-anchor="middle" letter-spacing="2">МУЗ-ТВ</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fdf2f8" text-anchor="middle">ХИТЫ 24/7</text>
</svg>""",

    "ru-rutv.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="rutv_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#db2777"/>
      <stop offset="100%" stop-color="#9d174d"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#rutv_bg)"/>
  <circle cx="100" cy="75" r="42" fill="#ffffff"/>
  <text x="100" y="85" font-family="-apple-system, Arial, sans-serif" font-size="28" font-weight="900" fill="#db2777" text-anchor="middle">RU</text>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="26" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">RU.TV</text>
  <text x="100" y="174" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fbcfe8" text-anchor="middle">РУССКАЯ МУЗЫКА</text>
</svg>""",

    "ru-avto24.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#09090b"/>
  <path d="M50 100 A50 50 0 0 1 150 100" stroke="#ef4444" stroke-width="8" fill="none" stroke-linecap="round"/>
  <line x1="100" y1="100" x2="130" y2="70" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>
  <circle cx="100" cy="100" r="10" fill="#ef4444"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">АВТО 24</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#f87171" text-anchor="middle">АВТОСПОРТ HD</text>
</svg>""",

    "ru-okhotarybalka.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="or_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#15803d"/>
      <stop offset="100%" stop-color="#052e16"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#or_bg)"/>
  <!-- Target crosshair & fish -->
  <circle cx="100" cy="74" r="36" fill="none" stroke="#facc15" stroke-width="6"/>
  <line x1="100" y1="32" x2="100" y2="116" stroke="#facc15" stroke-width="3"/>
  <line x1="58" y1="74" x2="142" y2="74" stroke="#facc15" stroke-width="3"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle">ОХОТА И РЫБАЛКА</text>
  <text x="100" y="170" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fde047" text-anchor="middle">ДИКАЯ ПРИРОДА HD</text>
</svg>""",

    "ru-dikayaokhota.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="do_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#365314"/>
      <stop offset="100%" stop-color="#14532d"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#do_bg)"/>
  <circle cx="100" cy="74" r="38" fill="none" stroke="#ef4444" stroke-width="6"/>
  <circle cx="100" cy="74" r="20" fill="none" stroke="#ef4444" stroke-width="4"/>
  <circle cx="100" cy="74" r="6" fill="#ef4444"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle">ДИКАЯ ОХОТА</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#fca5a5" text-anchor="middle">ТЕЛЕКАНАЛ HD</text>
</svg>""",

    "ru-dikayarybalka.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="dr_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0369a1"/>
      <stop offset="100%" stop-color="#082f49"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#dr_bg)"/>
  <path d="M70 70 Q100 45 130 70 Q110 95 70 70 Z" fill="#38bdf8"/>
  <polygon points="128,70 145,55 145,85" fill="#38bdf8"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="18" font-weight="900" fill="#ffffff" text-anchor="middle">ДИКАЯ РЫБАЛКА</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="700" fill="#7dd3fc" text-anchor="middle">ТЕЛЕКАНАЛ HD</text>
</svg>""",

    # ========================================================
    # 🇬🇧 ENGLISH CHANNELS
    # ========================================================
    "en-nasa.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="nasa_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e3a8a"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#nasa_bg)"/>
  <circle cx="100" cy="74" r="42" fill="#0b3d91"/>
  <!-- Stars -->
  <circle cx="85" cy="58" r="2" fill="#ffffff"/>
  <circle cx="118" cy="62" r="2" fill="#ffffff"/>
  <circle cx="92" cy="85" r="1.5" fill="#ffffff"/>
  <!-- Red Chevron -->
  <path d="M70 82 L100 52 L130 82" stroke="#fc3d21" stroke-width="7" fill="none" stroke-linecap="round"/>
  <!-- Orbit Ring -->
  <ellipse cx="100" cy="74" rx="46" ry="16" fill="none" stroke="#ffffff" stroke-width="3" transform="rotate(-25 100 74)"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="3">NASA</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#38bdf8" text-anchor="middle" letter-spacing="2">TELEVISION HD</text>
</svg>""",

    "en-redbull.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#080811"/>
  <!-- Sun -->
  <circle cx="100" cy="74" r="34" fill="#fbbf24"/>
  <!-- Charging Bulls silhouette -->
  <path d="M75 75 Q85 62 100 75 Q85 88 75 75 Z" fill="#dc2626"/>
  <path d="M125 75 Q115 62 100 75 Q115 88 125 75 Z" fill="#dc2626"/>
  <text x="100" y="144" font-family="-apple-system, Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">Red Bull</text>
  <text x="100" y="170" font-family="-apple-system, Arial, sans-serif" font-size="15" font-weight="900" fill="#ef4444" text-anchor="middle" letter-spacing="2">TV SPORTS</text>
</svg>""",

    "en-dw.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="dw_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#0369a1"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#dw_bg)"/>
  <circle cx="100" cy="76" r="42" fill="#ffffff"/>
  <text x="100" y="90" font-family="-apple-system, Arial, sans-serif" font-size="40" font-weight="900" fill="#0369a1" text-anchor="middle" letter-spacing="-1">DW</text>
  <text x="100" y="148" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">DEUTSCHE WELLE</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#bae6fd" text-anchor="middle" letter-spacing="1.5">ENGLISH NEWS HD</text>
</svg>""",

    "en-cbc.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#000000"/>
  <!-- CBC Gem Rosette -->
  <circle cx="100" cy="74" r="14" fill="#dc2626"/>
  <circle cx="75" cy="74" r="8" fill="#ef4444"/>
  <circle cx="125" cy="74" r="8" fill="#ef4444"/>
  <circle cx="100" cy="49" r="8" fill="#ef4444"/>
  <circle cx="100" cy="99" r="8" fill="#ef4444"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="28" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="2">CBC</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="14" font-weight="800" fill="#ef4444" text-anchor="middle" letter-spacing="2">NEWS 24/7</text>
</svg>""",

    "en-cbccomedy.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="cbcc_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#b45309"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#cbcc_bg)"/>
  <circle cx="100" cy="74" r="40" fill="#ffffff"/>
  <circle cx="86" cy="66" r="6" fill="#000000"/>
  <circle cx="114" cy="66" r="6" fill="#000000"/>
  <path d="M80 84 Q100 110 120 84 Z" fill="#b45309"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">CBC COMEDY</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fef3c7" text-anchor="middle">LAUGHS 24/7</text>
</svg>""",

    "en-cbckids.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="cbck_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#ec4899"/>
      <stop offset="100%" stop-color="#8b5cf6"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#cbck_bg)"/>
  <circle cx="100" cy="74" r="38" fill="#facc15"/>
  <text x="100" y="86" font-family="-apple-system, Arial, sans-serif" font-size="34" font-weight="900" fill="#ec4899" text-anchor="middle">★</text>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">CBC KIDS</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fdf2f8" text-anchor="middle">CARTOONS 24/7</text>
</svg>""",

    "en-heartland.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="hl_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#d97706"/>
      <stop offset="100%" stop-color="#78350f"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#hl_bg)"/>
  <!-- Sunset & Mountain -->
  <polygon points="100,45 145,100 55,100" fill="#fef3c7" opacity="0.9"/>
  <circle cx="100" cy="65" r="14" fill="#f59e0b"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">HEARTLAND</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fed7aa" text-anchor="middle">SERIES 24/7</text>
</svg>""",

    "en-murdoch.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#1c1917"/>
  <!-- Magnifying glass -->
  <circle cx="92" cy="70" r="28" fill="none" stroke="#f59e0b" stroke-width="6"/>
  <line x1="112" y1="90" x2="135" y2="113" stroke="#f59e0b" stroke-width="8" stroke-linecap="round"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">MURDOCH</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#fcd34d" text-anchor="middle">MYSTERIES 24/7</text>
</svg>""",

    "en-schitt.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <rect width="200" height="200" rx="36" fill="#000000"/>
  <rect x="35" y="45" width="130" height="60" rx="8" fill="none" stroke="#eab308" stroke-width="4"/>
  <text x="100" y="86" font-family="Georgia, serif" font-size="22" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">SCHITT'S</text>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#eab308" text-anchor="middle" letter-spacing="2">CREEK 24/7</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="12" font-weight="700" fill="#ffffff" text-anchor="middle">AWARD WINNING COMEDY</text>
</svg>""",

    "en-cbcexplore.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%">
  <defs>
    <linearGradient id="exp_bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d9488"/>
      <stop offset="100%" stop-color="#115e59"/>
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="36" fill="url(#exp_bg)"/>
  <!-- Compass -->
  <circle cx="100" cy="74" r="38" fill="none" stroke="#ffffff" stroke-width="6"/>
  <polygon points="100,48 110,74 100,70" fill="#f87171"/>
  <polygon points="100,100 110,74 100,70" fill="#ffffff"/>
  <text x="100" y="146" font-family="-apple-system, Arial, sans-serif" font-size="20" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1">CBC EXPLORE</text>
  <text x="100" y="172" font-family="-apple-system, Arial, sans-serif" font-size="13" font-weight="800" fill="#99f6e4" text-anchor="middle">DOCUMENTARIES</text>
</svg>"""
}

count = 0
for filename, svg in logos.items():
    dest = logos_dir / filename
    dest.write_text(svg.strip(), encoding="utf-8")
    count += 1

print(f"Successfully generated {count} authentic SVG channel logos in {logos_dir}!")
