import re
import json
from pathlib import Path

def patch_media_resolver():
    mr_path = Path("backend/media_resolver.py")
    code = mr_path.read_text(encoding="utf-8")

    helper_code = '''def normalize_quality_label(width: int = 0, height: int = 0) -> str:
    """
    Normalizes video stream dimensions into industry-standard resolution tiers.
    Accurately maps cropped widescreen / cinemascope aspect ratios (e.g. 2.39:1 / 21:9):
    - 1920x804 / 1920x822 -> 1080p
    - 1280x536 / 1280x546 -> 720p
    - 854x358 -> 480p
    - 640x268 -> 360p
    - 426x178 -> 240p
    """
    w = int(width or 0)
    h = int(height or 0)

    if w >= 3800 or h >= 2000:
        return "4K"
    if w >= 2500 or h >= 1400:
        return "1440p"
    if w >= 1700 or h >= 750:
        return "1080p"
    if w >= 1100 or h >= 500:
        return "720p"
    if w >= 700 or h >= 340:
        return "480p"
    if w >= 500 or h >= 240:
        return "360p"
    if w >= 350 or h >= 160:
        return "240p"
    if h > 0:
        return f"{h}p"
    return "Auto"

QUALITY_TIER_RANK = {
    "4k": 4000, "2160p": 2160, "1440p": 1440,
    "1080p": 1080, "720p": 720, "480p": 480,
    "360p": 360, "240p": 240, "144p": 144
}
'''
    if "def normalize_quality_label" not in code:
        code = code.replace("logger = logging.getLogger(\"media_resolver\")", f"{helper_code}\nlogger = logging.getLogger(\"media_resolver\")")
        print("Added normalize_quality_label to backend/media_resolver.py")

    # Update HLS metadata parsing
    old_hls_block = '''                        elif line.startswith("#EXT-X-STREAM-INF:"):
                            res_m = re.search(r'RESOLUTION=\\d+x(\\d+)', line)
                            if res_m:
                                parsed_qualities.add(f"{res_m.group(1)}p")'''

    new_hls_block = '''                        elif line.startswith("#EXT-X-STREAM-INF:"):
                            res_m = re.search(r'RESOLUTION=(\\d+)x(\\d+)', line)
                            if res_m:
                                w = int(res_m.group(1))
                                h = int(res_m.group(2))
                                parsed_qualities.add(normalize_quality_label(w, h))'''

    if old_hls_block in code:
        code = code.replace(old_hls_block, new_hls_block)
        print("Patched RESOLUTION parsing in backend/media_resolver.py")

    old_sort_block = '''                    def q_sort_key(q_str):
                        try:
                            return int(q_str.replace("p", ""))
                        except Exception:
                            return 0'''

    new_sort_block = '''                    def q_sort_key(q_str):
                        clean = str(q_str).lower().strip()
                        if clean in QUALITY_TIER_RANK:
                            return QUALITY_TIER_RANK[clean]
                        try:
                            return int(clean.replace("p", ""))
                        except Exception:
                            return 0'''

    if old_sort_block in code:
        code = code.replace(old_sort_block, new_sort_block)
        print("Patched q_sort_key in backend/media_resolver.py")

    mr_path.write_text(code, encoding="utf-8")
    print("backend/media_resolver.py updated successfully")


def patch_stream_proxy():
    sp_path = Path("backend/stream_proxy.py")
    code = sp_path.read_text(encoding="utf-8")

    if "def normalize_quality_label" not in code:
        helper_code = '''def normalize_quality_label(width: int = 0, height: int = 0) -> str:
    w = int(width or 0)
    h = int(height or 0)
    if w >= 3800 or h >= 2000: return "4K"
    if w >= 2500 or h >= 1400: return "1440p"
    if w >= 1700 or h >= 750: return "1080p"
    if w >= 1100 or h >= 500: return "720p"
    if w >= 700 or h >= 340: return "480p"
    if w >= 500 or h >= 240: return "360p"
    if w >= 350 or h >= 160: return "240p"
    if h > 0: return f"{h}p"
    return "Auto"
'''
        code = code.replace("logger = logging.getLogger(\"stream_proxy\")", f"{helper_code}\nlogger = logging.getLogger(\"stream_proxy\")")
        print("Added normalize_quality_label to backend/stream_proxy.py")

    old_variant_parse = '''                    elif line_s.startswith("#EXT-X-STREAM-INF:"):
                        inf_line = line_s
                        s_url = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
                        idx += 2
                        res_m = re.search(r'RESOLUTION=\\d+x(\\d+)', inf_line)
                        h = int(res_m.group(1)) if res_m else 0
                        is_avc = "avc1" in inf_line
                        parsed_variants.append({
                            "height": h,
                            "inf": inf_line,
                            "url": urljoin(url, s_url),
                            "is_avc": is_avc
                        })'''

    new_variant_parse = '''                    elif line_s.startswith("#EXT-X-STREAM-INF:"):
                        inf_line = line_s
                        s_url = lines[idx + 1].strip() if idx + 1 < len(lines) else ""
                        idx += 2
                        res_m = re.search(r'RESOLUTION=(\\d+)x(\\d+)', inf_line)
                        if res_m:
                            w = int(res_m.group(1))
                            h = int(res_m.group(2))
                        else:
                            res_m2 = re.search(r'RESOLUTION=\\d+x(\\d+)', inf_line)
                            h = int(res_m2.group(1)) if res_m2 else 0
                            w = 0
                        is_avc = "avc1" in inf_line
                        tier = normalize_quality_label(w, h)
                        parsed_variants.append({
                            "width": w,
                            "height": h,
                            "tier": tier,
                            "inf": inf_line,
                            "url": urljoin(url, s_url),
                            "is_avc": is_avc
                        })'''

    if old_variant_parse in code:
        code = code.replace(old_variant_parse, new_variant_parse)
        print("Patched variant parsing in backend/stream_proxy.py")

    old_filter_block = '''                if request_q and request_q.lower() != "auto":
                    try:
                        target_h = int(str(request_q).lower().replace("p", ""))
                        matches = [v for v in parsed_variants if v["height"] == target_h]
                        if not matches:
                            matches = sorted(parsed_variants, key=lambda v: abs(v["height"] - target_h))[:1]
                        selected = sorted(matches, key=lambda v: (1 if v["is_avc"] else 0), reverse=True)[0]
                        chosen_variants = [selected]
                    except Exception:
                        chosen_variants = parsed_variants
                else:
                    by_height = {}
                    for v in parsed_variants:
                        h = v["height"]
                        if h not in by_height or v["is_avc"]:
                            by_height[h] = v
                    # For Auto: prioritize 720p first so playback starts instantaneously and streams smoothly on 8 Mbps lines without buffer starvation
                    def auto_sort_key(h):
                        if h == 720:
                            return 999999
                        elif h == 1080:
                            return 888888
                        elif h == 480:
                            return 777777
                        return h
                    chosen_variants = [by_height[h] for h in sorted(by_height.keys(), key=auto_sort_key, reverse=True)]'''

    new_filter_block = '''                if request_q and request_q.lower() != "auto":
                    clean_req = str(request_q).lower().strip()
                    target_tier = normalize_quality_label(height=int(clean_req.replace("p", "")) if clean_req.replace("p", "").isdigit() else 0) if ("x" not in clean_req) else clean_req
                    matches = [v for v in parsed_variants if v.get("tier", "").lower() == clean_req or v.get("tier", "").lower() == target_tier.lower()]
                    if not matches:
                        try:
                            target_h = int(clean_req.replace("p", ""))
                            matches = [v for v in parsed_variants if v["height"] == target_h]
                            if not matches:
                                matches = sorted(parsed_variants, key=lambda v: abs(v["height"] - target_h))[:1]
                        except Exception:
                            matches = parsed_variants
                    selected = sorted(matches, key=lambda v: (1 if v["is_avc"] else 0), reverse=True)[0]
                    chosen_variants = [selected]
                else:
                    by_tier = {}
                    for v in parsed_variants:
                        t = v.get("tier", str(v["height"]))
                        if t not in by_tier or v["is_avc"]:
                            by_tier[t] = v
                    # For Auto: prioritize 720p first so playback starts instantaneously and streams smoothly on 8 Mbps lines without buffer starvation
                    def auto_tier_sort_key(v):
                        t = v.get("tier", "").lower()
                        if t == "720p":
                            return 999999
                        elif t == "1080p":
                            return 888888
                        elif t == "480p":
                            return 777777
                        return v.get("height", 0)
                    chosen_variants = sorted(by_tier.values(), key=auto_tier_sort_key, reverse=True)'''

    if old_filter_block in code:
        code = code.replace(old_filter_block, new_filter_block)
        print("Patched filter block in backend/stream_proxy.py")

    sp_path.write_text(code, encoding="utf-8")
    print("backend/stream_proxy.py updated successfully")


def patch_app_js():
    js_path = Path("static/app.js")
    code = js_path.read_text(encoding="utf-8")

    helper_js = '''function formatQualityDisplay(q) {
  if (!q || q === "Auto") return { value: "Auto", tier: "Auto", label: "Auto (Smooth Playback)" };
  const clean = String(q).trim();
  const num = parseInt(clean.replace(/[^\\d]/g, ""), 10);

  let tier = "SD";
  let label = clean;

  if (clean === "4K" || num >= 2000) {
    tier = "4K";
    label = "4K (Ultra HD)";
  } else if (clean === "1440p" || (num >= 1400 && num < 2000)) {
    tier = "1440p";
    label = "1440p (2K Quad HD)";
  } else if (clean === "1080p" || (num >= 750 && num < 1400)) {
    tier = "1080p";
    label = "1080p (Full HD)";
  } else if (clean === "720p" || (num >= 500 && num < 750)) {
    tier = "720p";
    label = "720p (HD)";
  } else if (clean === "480p" || (num >= 340 && num < 500)) {
    tier = "480p";
    label = "480p (SD)";
  } else if (clean === "360p" || (num >= 240 && num < 340)) {
    tier = "360p";
    label = "360p (Data Saver)";
  } else if (clean === "240p" || (num >= 160 && num < 240)) {
    tier = "240p";
    label = "240p (Low)";
  } else {
    label = `${clean}`;
  }

  return { value: q, tier, label };
}
'''
    if "function formatQualityDisplay" not in code:
        code = code.replace("function updateActiveCastDeck(info) {", f"{helper_js}\nfunction updateActiveCastDeck(info) {{\n")
        print("Added formatQualityDisplay to static/app.js")

    old_q_populate = '''      qSelect.innerHTML = '<option value="Auto">Auto (Smooth Playback)</option>';
      activeDeckQualities.forEach(q => {
        if (q !== "Auto") {
          const opt = document.createElement("option");
          opt.value = q;
          const badge = q === "1080p" ? "Full HD" : (q === "720p" ? "HD" : "SD");
          opt.textContent = `${q} ${badge}`;
          qSelect.appendChild(opt);
        }
      });
      if (curVal && activeDeckQualities.includes(curVal)) {
        qSelect.value = curVal;
      }'''

    new_q_populate = '''      const seenTiers = new Set();
      qSelect.innerHTML = '<option value="Auto">Auto (Smooth Playback)</option>';
      activeDeckQualities.forEach(q => {
        if (q !== "Auto") {
          const { value, tier, label } = formatQualityDisplay(q);
          if (!seenTiers.has(tier)) {
            seenTiers.add(tier);
            const opt = document.createElement("option");
            opt.value = value;
            opt.textContent = label;
            qSelect.appendChild(opt);
          }
        }
      });
      if (curVal) {
        const curTier = formatQualityDisplay(curVal).tier;
        for (let i = 0; i < qSelect.options.length; i++) {
          const optVal = qSelect.options[i].value;
          if (optVal === curVal || (optVal !== "Auto" && formatQualityDisplay(optVal).tier === curTier)) {
            qSelect.selectedIndex = i;
            break;
          }
        }
      }'''

    if old_q_populate in code:
        code = code.replace(old_q_populate, new_q_populate)
        print("Patched quality select population in static/app.js")

    # Update qSelect.onchange in static/app.js
    old_q_change = '''    qSelect.onchange = async () => {
      vibrate(20);
      const q = qSelect.value;
      const targetUrl = activeDeckQualityUrls[q] || activeDeckQualityUrls[q.toLowerCase()] || activeDeckQualityUrls["Auto"] || null;
      showToast(`Switching Quality to ${q}...`);
      await safeFetchWithRetry("/api/playback/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "quality", value: q, url: targetUrl, device_id: state.currentTvId })
      });
    };'''

    new_q_change = '''    qSelect.onchange = async () => {
      vibrate(20);
      const q = qSelect.value;
      const displayInfo = formatQualityDisplay(q);
      const targetUrl = activeDeckQualityUrls[q] ||
                        activeDeckQualityUrls[displayInfo.tier] ||
                        activeDeckQualityUrls[displayInfo.value] ||
                        activeDeckQualityUrls["Auto"] || null;
      showToast(`Switching Quality to ${displayInfo.label.split(" ")[0]}...`);
      await safeFetchWithRetry("/api/playback/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "quality", value: q, url: targetUrl, device_id: state.currentTvId })
      });
    };'''

    if old_q_change in code:
        code = code.replace(old_q_change, new_q_change)
        print("Patched qSelect.onchange in static/app.js")

    js_path.write_text(code, encoding="utf-8")
    print("static/app.js updated successfully")


def patch_active_cast():
    ac_path = Path("backend/.active_cast.json")
    if not ac_path.exists():
        return
    data = json.loads(ac_path.read_text(encoding="utf-8"))
    raw_qs = data.get("qualities", [])
    if raw_qs:
        tier_map = {
            "804p": "1080p",
            "536p": "720p",
            "358p": "480p",
            "268p": "360p",
            "178p": "240p"
        }
        new_qs = []
        for q in raw_qs:
            mapped = tier_map.get(q, q)
            if mapped not in new_qs:
                new_qs.append(mapped)
        data["qualities"] = new_qs

        q_urls = data.get("quality_urls", {})
        if q_urls:
            new_q_urls = dict(q_urls)
            for raw_k, tier_k in tier_map.items():
                if raw_k in q_urls and tier_k not in new_q_urls:
                    new_q_urls[tier_k] = q_urls[raw_k]
            data["quality_urls"] = new_q_urls

        ac_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print("backend/.active_cast.json updated with standard tiers!")

if __name__ == "__main__":
    patch_media_resolver()
    patch_stream_proxy()
    patch_app_js()
    patch_active_cast()
