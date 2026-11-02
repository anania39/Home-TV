app_file = r"backend/app.py"
with open(app_file, "r", encoding="utf-8") as f:
    text = f.read()

crlf = "\r\n" in text
text_lf = text.replace("\r\n", "\n")

target = """                if src_type == "youtube":
                    # For YouTube HLS (MPEG-TS video + AAC audio): NEVER pass hlsSegmentFormat="aac"!
                    # Setting hlsSegmentFormat="aac" causes Google Cast CAF receiver to treat the stream
                    # as pure audio, disabling video rendering and displaying a black screen.
                    media_info.pop("hlsSegmentFormat", None)
                    media_info.setdefault("hlsVideoSegmentFormat", "mpeg2_ts")"""

replacement = """                if src_type == "youtube":
                    media_info.pop("hlsSegmentFormat", None)
                    media_info.pop("hlsVideoSegmentFormat", None)"""

assert target in text_lf, "Target not found in backend/app.py"
text_lf = text_lf.replace(target, replacement)
if crlf:
    text_lf = text_lf.replace("\n", "\r\n")

with open(app_file, "w", encoding="utf-8") as f:
    f.write(text_lf)

print("Successfully updated backend/app.py!")
