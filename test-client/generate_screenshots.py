#!/usr/bin/env python3
"""
Generates screenshot images for the test-client README.
Renders the UI layout using PIL — no display or screen recording needed.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ---------------------------------------------------------------------------
# Colours (match the app)
# ---------------------------------------------------------------------------
BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
ACCENT  = "#7c6af7"
SUCCESS = "#4caf50"
ERROR   = "#f44336"
WARNING = "#ff9800"
TEXT    = "#cdd6f4"
MUTED   = "#6c7086"
ENTRY   = "#313244"
BLUE    = "#5a9af7"
BORDER  = "#3a3a5c"

W = 431   # window width
os.makedirs("images", exist_ok=True)


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def _font(size=11, bold=False, mono=False):
    candidates_mono  = ["/System/Library/Fonts/Menlo.ttc",
                        "/System/Library/Fonts/Monaco.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    candidates_sans  = ["/System/Library/Fonts/Helvetica.ttc",
                        "/System/Library/Fonts/SFNSDisplay.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    candidates_bold  = ["/System/Library/Fonts/Helvetica.ttc",
                        "/System/Library/Fonts/SFNSDisplay.ttf",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    pool = candidates_mono if mono else (candidates_bold if bold else candidates_sans)
    for path in pool:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


F_HDR   = _font(15, bold=True)
F_SUB   = _font(9)
F_LBL   = _font(9)
F_ENTRY = _font(11)
F_BTN   = _font(11, bold=True)
F_STAT_V= _font(16, bold=True)
F_STAT_L= _font(8)
F_SEC   = _font(8, bold=True)
F_LOG   = _font(10, mono=True)
F_LOG_B = _font(10, mono=True, bold=True)


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0+radius, y0, x1-radius, y1], fill=fill)
    draw.rectangle([x0, y0+radius, x1, y1-radius], fill=fill)
    draw.ellipse([x0, y0, x0+2*radius, y0+2*radius], fill=fill)
    draw.ellipse([x1-2*radius, y0, x1, y0+2*radius], fill=fill)
    draw.ellipse([x0, y1-2*radius, x0+2*radius, y1], fill=fill)
    draw.ellipse([x1-2*radius, y1-2*radius, x1, y1], fill=fill)


def text_w(draw, txt, font):
    bbox = draw.textbbox((0, 0), txt, font=font)
    return bbox[2] - bbox[0]


def draw_header(draw, y=0):
    draw.rectangle([0, y, W, y+68], fill=hex2rgb(ACCENT))
    draw.text((W//2 - text_w(draw,"Postfix SMTP Test Client",F_HDR)//2, y+12),
              "Postfix SMTP Test Client", fill="white", font=F_HDR)
    sub = "Simulate application mail generation"
    draw.text((W//2 - text_w(draw, sub, F_SUB)//2, y+36),
              sub, fill="#ddd", font=F_SUB)
    return y + 68


def draw_label(draw, x, y, text):
    draw.text((x, y), text, fill=hex2rgb(MUTED), font=F_LBL)
    return y + 14


def draw_entry(draw, x, y, value, width=W-48):
    rounded_rect(draw, [x, y, x+width, y+30], 4, hex2rgb(ENTRY))
    draw.text((x+10, y+8), value, fill=hex2rgb(TEXT), font=F_ENTRY)
    return y + 38


def draw_button(draw, y, label, color=ACCENT):
    rounded_rect(draw, [24, y, W-24, y+38], 5, hex2rgb(color))
    w = text_w(draw, label, F_BTN)
    draw.text(((W-w)//2, y+11), label, fill="white", font=F_BTN)
    return y + 38


def draw_progress(draw, y, value=0, maximum=4):
    draw.rectangle([24, y, W-24, y+8], fill=hex2rgb(PANEL))
    if maximum > 0 and value > 0:
        fill_w = int((W-48) * value / maximum)
        draw.rectangle([24, y, 24+fill_w, y+8], fill=hex2rgb(ACCENT))
    return y + 16


def draw_stats(draw, y, sent=0, failed=0, total=0):
    third = (W-48) // 3
    for i, (label, val, color) in enumerate([
        ("Sent", str(sent), SUCCESS),
        ("Failed", str(failed), ERROR),
        ("Total", str(total), MUTED),
    ]):
        cx = 24 + i*third + third//2
        lw = text_w(draw, label, F_STAT_L)
        vw = text_w(draw, val,   F_STAT_V)
        draw.text((cx - lw//2, y),    label, fill=hex2rgb(MUTED),  font=F_STAT_L)
        draw.text((cx - vw//2, y+12), val,   fill=hex2rgb(color),  font=F_STAT_V)
    return y + 38


def draw_section(draw, y, title):
    draw.text((24, y), title.upper(), fill=hex2rgb(MUTED), font=F_SEC)
    draw.rectangle([24, y+13, W-24, y+14], fill=hex2rgb(BORDER))
    return y + 22


def draw_log(draw, y, lines):
    """lines = list of (text, colour_hex)"""
    log_h = len(lines) * 18 + 12
    draw.rectangle([24, y, W-24, y+log_h], fill=hex2rgb(PANEL))
    cy = y + 6
    for txt, col in lines:
        draw.text((30, cy), txt, fill=hex2rgb(col), font=F_LOG)
        cy += 18
    return y + log_h


# ---------------------------------------------------------------------------
# Image 1: ui-main  (idle, empty log)
# ---------------------------------------------------------------------------

def make_ui_main():
    img = Image.new("RGB", (W, 750), hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    y = draw_header(draw)
    y += 12

    y = draw_label(draw, 24, y, "SMTP Relay Host / IP")
    y = draw_entry(draw, 24, y, "127.0.0.1")
    y = draw_label(draw, 24, y, "Port")
    y = draw_entry(draw, 24, y, "25")
    y = draw_label(draw, 24, y, "From Address (sender)")
    y = draw_entry(draw, 24, y, "app@example.com")
    y = draw_label(draw, 24, y, "To Address (recipient)")
    y = draw_entry(draw, 24, y, "user@example.com")
    y = draw_label(draw, 24, y, "Number of Test Emails")
    y = draw_entry(draw, 24, y, "4")
    y += 12

    y = draw_button(draw, y, "Send Test Emails")
    y += 10

    y = draw_progress(draw, y)
    y += 4

    y = draw_stats(draw, y)
    y += 10

    y = draw_section(draw, y, "Output Log")
    draw.rectangle([24, y, W-24, y+180], fill=hex2rgb(PANEL))

    img = img.crop((0, 0, W, y+190))
    img.save("images/ui-main.png")
    print("  saved ui-main.png")


# ---------------------------------------------------------------------------
# Image 2: ui-sending  (progress mid-way, partial log)
# ---------------------------------------------------------------------------

def make_ui_sending():
    img = Image.new("RGB", (W, 750), hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    y = draw_header(draw)
    y += 12

    y = draw_label(draw, 24, y, "SMTP Relay Host / IP")
    y = draw_entry(draw, 24, y, "192.168.1.10")
    y = draw_label(draw, 24, y, "Port")
    y = draw_entry(draw, 24, y, "25")
    y = draw_label(draw, 24, y, "From Address (sender)")
    y = draw_entry(draw, 24, y, "app@example.com")
    y = draw_label(draw, 24, y, "To Address (recipient)")
    y = draw_entry(draw, 24, y, "user@example.com")
    y = draw_label(draw, 24, y, "Number of Test Emails")
    y = draw_entry(draw, 24, y, "4")
    y += 12

    y = draw_button(draw, y, "Sending…", color="#5a4aaa")
    y += 10

    y = draw_progress(draw, y, value=2, maximum=4)
    y += 4

    y = draw_stats(draw, y, sent=2, failed=0, total=2)
    y += 10

    y = draw_section(draw, y, "Output Log")
    log_lines = [
        ("=" * 48,                                                        ACCENT),
        ("[14:21:03] Relay : 192.168.1.10:25",                           BLUE),
        ("[14:21:03] From  : app@example.com",                           BLUE),
        ("[14:21:03] To    : user@example.com",                          BLUE),
        ("[14:21:03] Count : 4",                                          BLUE),
        ("=" * 48,                                                        ACCENT),
        ("[14:21:03] [1/4]  OK   [Notification] Action required…",       SUCCESS),
        ("[14:21:04] [2/4]  OK   [CRITICAL] database alert…",            SUCCESS),
    ]
    y = draw_log(draw, y, log_lines)

    img = img.crop((0, 0, W, y + 20))
    img.save("images/ui-sending.png")
    print("  saved ui-sending.png")


# ---------------------------------------------------------------------------
# Image 3: ui-success  (all OK)
# ---------------------------------------------------------------------------

def make_ui_success():
    img = Image.new("RGB", (W, 750), hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    y = draw_header(draw)
    y += 12

    y = draw_label(draw, 24, y, "SMTP Relay Host / IP")
    y = draw_entry(draw, 24, y, "192.168.1.10")
    y = draw_label(draw, 24, y, "Port")
    y = draw_entry(draw, 24, y, "25")
    y = draw_label(draw, 24, y, "From Address (sender)")
    y = draw_entry(draw, 24, y, "app@example.com")
    y = draw_label(draw, 24, y, "To Address (recipient)")
    y = draw_entry(draw, 24, y, "user@example.com")
    y = draw_label(draw, 24, y, "Number of Test Emails")
    y = draw_entry(draw, 24, y, "4")
    y += 12

    y = draw_button(draw, y, "Send Test Emails")
    y += 10

    y = draw_progress(draw, y, value=4, maximum=4)
    y += 4

    y = draw_stats(draw, y, sent=4, failed=0, total=4)
    y += 10

    y = draw_section(draw, y, "Output Log")
    log_lines = [
        ("=" * 48,                                                         ACCENT),
        ("[14:21:03] Relay : 192.168.1.10:25",                            BLUE),
        ("[14:21:03] From  : app@example.com",                            BLUE),
        ("[14:21:03] To    : user@example.com",                           BLUE),
        ("[14:21:03] Count : 4",                                           BLUE),
        ("=" * 48,                                                         ACCENT),
        ("[14:21:03] [1/4]  OK   [Notification] Action required…",        SUCCESS),
        ("[14:21:04] [2/4]  OK   [CRITICAL] database alert…",             SUCCESS),
        ("[14:21:04] [3/4]  OK   Daily Summary Report – 2024-05-01",      SUCCESS),
        ("[14:21:05] [4/4]  OK   Welcome to the platform, alice!",        SUCCESS),
        ("=" * 48,                                                         ACCENT),
        ("[14:21:05] Done — Sent: 4  Failed: 0  Total: 4",               SUCCESS),
        ("=" * 48,                                                         ACCENT),
    ]
    y = draw_log(draw, y, log_lines)

    img = img.crop((0, 0, W, y + 20))
    img.save("images/ui-success.png")
    print("  saved ui-success.png")


# ---------------------------------------------------------------------------
# Image 4: ui-fail  (connection refused)
# ---------------------------------------------------------------------------

def make_ui_fail():
    img = Image.new("RGB", (W, 750), hex2rgb(BG))
    draw = ImageDraw.Draw(img)

    y = draw_header(draw)
    y += 12

    y = draw_label(draw, 24, y, "SMTP Relay Host / IP")
    y = draw_entry(draw, 24, y, "10.0.0.99")
    y = draw_label(draw, 24, y, "Port")
    y = draw_entry(draw, 24, y, "25")
    y = draw_label(draw, 24, y, "From Address (sender)")
    y = draw_entry(draw, 24, y, "app@example.com")
    y = draw_label(draw, 24, y, "To Address (recipient)")
    y = draw_entry(draw, 24, y, "user@example.com")
    y = draw_label(draw, 24, y, "Number of Test Emails")
    y = draw_entry(draw, 24, y, "4")
    y += 12

    y = draw_button(draw, y, "Send Test Emails")
    y += 10

    y = draw_progress(draw, y, value=4, maximum=4)
    y += 4

    y = draw_stats(draw, y, sent=0, failed=4, total=4)
    y += 10

    y = draw_section(draw, y, "Output Log")
    err = "Connection error: [Errno 111] Connection refused"
    log_lines = [
        ("=" * 48,                                                          ACCENT),
        ("[14:25:01] Relay : 10.0.0.99:25",                               BLUE),
        ("[14:25:01] From  : app@example.com",                            BLUE),
        ("[14:25:01] To    : user@example.com",                           BLUE),
        ("[14:25:01] Count : 4",                                           BLUE),
        ("=" * 48,                                                         ACCENT),
        (f"[14:25:01] [1/4]  FAIL [Notification]… ({err})",              ERROR),
        (f"[14:25:02] [2/4]  FAIL [CRITICAL]…     ({err})",              ERROR),
        (f"[14:25:03] [3/4]  FAIL Daily Summary…  ({err})",              ERROR),
        (f"[14:25:04] [4/4]  FAIL Welcome…        ({err})",              ERROR),
        ("=" * 48,                                                         ACCENT),
        ("[14:25:04] Done — Sent: 0  Failed: 4  Total: 4",               ERROR),
        ("=" * 48,                                                         ACCENT),
    ]
    y = draw_log(draw, y, log_lines)

    img = img.crop((0, 0, W, y + 20))
    img.save("images/ui-fail.png")
    print("  saved ui-fail.png")


# ---------------------------------------------------------------------------
# Image 5: cli-single
# ---------------------------------------------------------------------------

def make_cli_single():
    lines = [
        ("$ python3 smtp_test_client.py \\",                              TEXT),
        ("    --host 192.168.1.10 \\",                                    TEXT),
        ("    --from app@example.com \\",                                 TEXT),
        ("    --to user@example.com",                                     TEXT),
        ("",                                                               TEXT),
        ("Postfix SMTP Test Client",                                       ACCENT),
        ("=" * 40,                                                         MUTED),
        ("  Relay host : 192.168.1.10:25",                               TEXT),
        ("  Sender     : app@example.com",                                TEXT),
        ("  Recipient  : user@example.com",                               TEXT),
        ("  Mode       : notification",                                   TEXT),
        ("  Count      : 1",                                              TEXT),
        ("=" * 40,                                                         MUTED),
        ("",                                                               TEXT),
        ("[1/1] Sending …   [OK]  [Notification] Action required…",      SUCCESS),
        ("",                                                               TEXT),
        ("=" * 40,                                                         MUTED),
        ("  Sent:   1",                                                   SUCCESS),
        ("  Failed: 0",                                                   TEXT),
        ("  Total:  1",                                                   TEXT),
        ("=" * 40,                                                         MUTED),
    ]
    _make_terminal("images/cli-single.png", lines)
    print("  saved cli-single.png")


# ---------------------------------------------------------------------------
# Image 6: cli-bulk
# ---------------------------------------------------------------------------

def make_cli_bulk():
    lines = [
        ("$ python3 smtp_test_client.py \\",                              TEXT),
        ("    --host 192.168.1.10 --from app@example.com \\",            TEXT),
        ("    --to user@example.com --type bulk --count 6 --delay 0.2", TEXT),
        ("",                                                               TEXT),
        ("Postfix SMTP Test Client",                                       ACCENT),
        ("=" * 40,                                                         MUTED),
        ("  Relay host : 192.168.1.10:25",                               TEXT),
        ("  Mode       : bulk   Count : 6",                              TEXT),
        ("=" * 40,                                                         MUTED),
        ("",                                                               TEXT),
        ("[1/6] Sending …   [OK]  [Notification] Action required…",      SUCCESS),
        ("[2/6] Sending …   [OK]  [CRITICAL] api-gateway alert…",        SUCCESS),
        ("[3/6] Sending …   [OK]  Daily Summary Report – 2024-05-01",    SUCCESS),
        ("[4/6] Sending …   [OK]  Welcome to the platform, bob!",        SUCCESS),
        ("[5/6] Sending …   [OK]  [WARNING] cache alert…",               SUCCESS),
        ("[6/6] Sending …   [OK]  [Notification] Action required…",      SUCCESS),
        ("",                                                               TEXT),
        ("=" * 40,                                                         MUTED),
        ("  Sent:   6",                                                   SUCCESS),
        ("  Failed: 0",                                                   TEXT),
        ("  Total:  6",                                                   TEXT),
        ("=" * 40,                                                         MUTED),
    ]
    _make_terminal("images/cli-bulk.png", lines)
    print("  saved cli-bulk.png")


# ---------------------------------------------------------------------------
# Image 7: cli-verbose
# ---------------------------------------------------------------------------

def make_cli_verbose():
    lines = [
        ("$ python3 smtp_test_client.py --host 192.168.1.10 \\",         TEXT),
        ("    --from app@example.com --to user@example.com --verbose",   TEXT),
        ("",                                                               TEXT),
        ("send: 'ehlo [127.0.0.1]\\r\\n'",                               MUTED),
        ("reply: b'250-ubuntu-server\\r\\n'",                             MUTED),
        ("reply: b'250-PIPELINING\\r\\n'",                                MUTED),
        ("reply: b'250-SIZE 10240000\\r\\n'",                             MUTED),
        ("reply: b'250-VRFY\\r\\n'",                                      MUTED),
        ("reply: b'250-ETRN\\r\\n'",                                      MUTED),
        ("reply: b'250-ENHANCEDSTATUSCODES\\r\\n'",                       MUTED),
        ("reply: b'250 DSN\\r\\n'",                                       MUTED),
        ("reply: retcode (250); Msg: b'ubuntu-server\\nPIPELINING…'",    MUTED),
        ("send: 'mail FROM:<app@example.com> size=1342\\r\\n'",          MUTED),
        ("reply: b'250 2.1.0 Ok\\r\\n'",                                  MUTED),
        ("send: 'rcpt TO:<user@example.com>\\r\\n'",                     MUTED),
        ("reply: b'250 2.1.5 Ok\\r\\n'",                                  MUTED),
        ("send: 'data\\r\\n'",                                            MUTED),
        ("reply: b'354 End data with <CR><LF>.<CR><LF>\\r\\n'",         MUTED),
        ("reply: b'250 2.0.0 Ok: queued as A1B2C3D4\\r\\n'",            MUTED),
        ("",                                                               TEXT),
        ("[1/1] Sending …   [OK]  [Notification] Action required…",      SUCCESS),
    ]
    _make_terminal("images/cli-verbose.png", lines)
    print("  saved cli-verbose.png")


# ---------------------------------------------------------------------------
# Terminal renderer
# ---------------------------------------------------------------------------

def _make_terminal(path, lines):
    PAD   = 16
    LH    = 20
    TH    = PAD + len(lines) * LH + PAD
    TW    = 720

    img  = Image.new("RGB", (TW, TH), (30, 30, 30))
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([0, 0, TW, 28], fill=(50, 50, 50))
    for cx, col in [(14, (255,95,86)), (34, (255,189,46)), (54, (39,201,63))]:
        draw.ellipse([cx-5, 9, cx+5, 19], fill=col)

    y = 36
    for text, color in lines:
        draw.text((PAD, y), text, fill=hex2rgb(color), font=F_LOG)
        y += LH

    img.save(path)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating screenshots…")
    make_ui_main()
    make_ui_sending()
    make_ui_success()
    make_ui_fail()
    make_cli_single()
    make_cli_bulk()
    make_cli_verbose()
    print("Done — all images saved to test-client/images/")
