from pathlib import Path

code = Path("static/app.js").read_text(encoding="utf-8")
print(f"Total lines in static/app.js: {len(code.splitlines())}")
print(f"Total size: {len(code)} bytes")
# Check for obvious unterminated template strings or syntax issues
open_ticks = code.count("`")
print(f"Backtick count (should be even): {open_ticks} (even: {open_ticks % 2 == 0})")
assert open_ticks % 2 == 0, "Unclosed template literal"
print("JS file sanity check OK!")
