#!/usr/bin/env python3
"""
Postfix SMTP Test Client – GUI

Simple UI to send test emails through a Postfix SMTP relay.
Requires network connectivity to the relay host.

Usage:
    python smtp_test_client_ui.py
"""

import random
import smtplib
import socket
import threading
import tkinter as tk
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from tkinter import scrolledtext, ttk


# ---------------------------------------------------------------------------
# Mail builders
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _random_ip() -> str:
    return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def build_notification(sender: str, recipient: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Notification] Action required – {_ts()}"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    plain = (
        "Hello,\n\nThis is an automated notification from your application.\n\n"
        f"Event:     User login detected\nTimestamp: {_ts()}\nSource IP: {_random_ip()}\n\n"
        "If this was not you, please contact support immediately.\n\nRegards,\nApplication Team"
    )
    html = f"""\
<html><body>
<p>Hello,</p>
<p>This is an automated notification from your application.</p>
<table border="0" cellpadding="4">
  <tr><td><b>Event</b></td><td>User login detected</td></tr>
  <tr><td><b>Timestamp</b></td><td>{_ts()}</td></tr>
  <tr><td><b>Source IP</b></td><td>{_random_ip()}</td></tr>
</table>
<p>If this was not you, please contact support immediately.</p>
<p>Regards,<br>Application Team</p>
</body></html>"""
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def build_alert(sender: str, recipient: str) -> MIMEMultipart:
    level = random.choice(["WARNING", "CRITICAL", "INFO"])
    service = random.choice(["database", "cache", "api-gateway", "worker", "scheduler"])
    usage = random.randint(85, 99)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{level}] {service} alert – {_ts()}"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg["X-Priority"] = "1" if level == "CRITICAL" else "3"
    plain = (
        f"ALERT LEVEL: {level}\nSERVICE: {service}\nTIMESTAMP: {_ts()}\n\n"
        f"Description: High CPU usage detected on {service}. Current usage at {usage}%.\n\n"
        "Please investigate immediately.\n\n-- Monitoring System"
    )
    html = f"""\
<html><body>
<h2 style="color:{'red' if level=='CRITICAL' else 'orange' if level=='WARNING' else 'blue'}">{level} Alert</h2>
<table border="1" cellpadding="6" cellspacing="0">
  <tr><th>Field</th><th>Value</th></tr>
  <tr><td>Service</td><td>{service}</td></tr>
  <tr><td>Timestamp</td><td>{_ts()}</td></tr>
  <tr><td>CPU Usage</td><td>{usage}%</td></tr>
</table>
<p>Please investigate immediately.</p>
<p><em>-- Monitoring System</em></p>
</body></html>"""
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def build_report(sender: str, recipient: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily Summary Report – {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    rows = random.randint(3, 6)
    table_plain = "\n".join(
        f"  {i+1}.  orders={random.randint(10,500)}  revenue=${random.randint(100,9999)}"
        for i in range(rows)
    )
    table_html = "".join(
        f"<tr><td>{i+1}</td><td>{random.randint(10,500)}</td><td>${random.randint(100,9999)}</td></tr>"
        for i in range(rows)
    )
    plain = (
        f"Daily Summary Report\nGenerated: {_ts()}\n{'='*36}\n\n{table_plain}\n\n"
        "This is an automated report. Do not reply."
    )
    html = f"""\
<html><body>
<h2>Daily Summary Report</h2>
<p><small>Generated: {_ts()}</small></p>
<table border="1" cellpadding="6" cellspacing="0">
  <tr><th>#</th><th>Orders</th><th>Revenue</th></tr>{table_html}
</table>
<p><em>This is an automated report. Do not reply.</em></p>
</body></html>"""
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def build_welcome(sender: str, recipient: str) -> MIMEMultipart:
    username = recipient.split("@")[0]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Welcome to the platform, {username}!"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    plain = (
        f"Hi {username},\n\nWelcome! Your account has been created successfully.\n\n"
        f"  Username:   {username}\n  Created at: {_ts()}\n\n"
        "Get started: https://app.example.com/dashboard\n\nCheers,\nThe Team"
    )
    html = f"""\
<html><body>
<h2>Welcome, {username}!</h2>
<p>Your account has been created successfully.</p>
<ul>
  <li><b>Username:</b> {username}</li>
  <li><b>Created at:</b> {_ts()}</li>
</ul>
<p><a href="https://app.example.com/dashboard">Go to your dashboard</a></p>
<p>Cheers,<br>The Team</p>
</body></html>"""
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


MAIL_BUILDERS = [
    build_notification,
    build_alert,
    build_report,
    build_welcome,
]


# ---------------------------------------------------------------------------
# SMTP send
# ---------------------------------------------------------------------------

def send_one(host: str, port: int, sender: str, recipient: str,
             msg: MIMEMultipart, timeout: int) -> tuple[bool, str]:
    try:
        with smtplib.SMTP(host=host, port=port, timeout=timeout) as server:
            server.ehlo_or_helo_if_needed()
            server.sendmail(sender, [recipient], msg.as_string())
        return True, ""
    except smtplib.SMTPException as exc:
        return False, f"SMTP error: {exc}"
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        return False, f"Connection error: {exc}"


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
ACCENT  = "#7c6af7"
SUCCESS = "#4caf50"
ERROR   = "#f44336"
TEXT    = "#cdd6f4"
MUTED   = "#6c7086"
ENTRY   = "#313244"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Postfix SMTP Test Client")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._sending = False
        self._build_ui()
        self._center()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Postfix SMTP Test Client",
                 bg=ACCENT, fg="white",
                 font=("Helvetica", 15, "bold")).pack()
        tk.Label(hdr, text="Simulate application mail and send to your relay",
                 bg=ACCENT, fg="#ddd",
                 font=("Helvetica", 9)).pack()

        # Form
        form = tk.Frame(self, bg=BG, padx=24, pady=16)
        form.pack(fill="x")

        self.var_host      = self._field(form, "SMTP Relay Host / IP", "127.0.0.1")
        self.var_port      = self._field(form, "Port", "25")
        self.var_sender    = self._field(form, "From Address (sender)", "app@example.com")
        self.var_recipient = self._field(form, "To Address (recipient)", "user@example.com")
        self.var_count     = self._field(form, "Number of Test Emails", "4")

        # Send button
        self.btn = tk.Button(
            form, text="Send Test Emails",
            bg=ACCENT, fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat", cursor="hand2",
            padx=12, pady=8,
            command=self._on_send,
        )
        self.btn.pack(fill="x", pady=(12, 0))

        # Progress
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("P.Horizontal.TProgressbar",
                        troughcolor=PANEL, background=ACCENT,
                        bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT)
        self.progress = ttk.Progressbar(
            self, style="P.Horizontal.TProgressbar",
            orient="horizontal", mode="determinate",
        )
        self.progress.pack(fill="x", padx=24, pady=(0, 8))

        # Stats row
        stats = tk.Frame(self, bg=BG)
        stats.pack(fill="x", padx=24)
        self.lbl_sent   = self._stat(stats, "Sent",   SUCCESS)
        self.lbl_failed = self._stat(stats, "Failed", ERROR)
        self.lbl_total  = self._stat(stats, "Total",  MUTED)

        # Log
        log_frame = tk.Frame(self, bg=BG, padx=24, pady=8)
        log_frame.pack(fill="both", expand=True)
        tk.Label(log_frame, text="OUTPUT LOG",
                 bg=BG, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w")
        tk.Frame(log_frame, bg=MUTED, height=1).pack(fill="x", pady=(2, 6))

        self.log = scrolledtext.ScrolledText(
            log_frame, width=60, height=14,
            bg=PANEL, fg=TEXT,
            insertbackground=TEXT,
            font=("Courier", 10),
            relief="flat", borderwidth=0,
            state="disabled",
        )
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",      foreground=SUCCESS)
        self.log.tag_config("fail",    foreground=ERROR)
        self.log.tag_config("info",    foreground="#5a9af7")
        self.log.tag_config("heading", foreground=ACCENT,
                            font=("Courier", 10, "bold"))

        tk.Frame(self, bg=BG, height=12).pack()

    def _field(self, parent, label: str, default: str) -> tk.StringVar:
        tk.Label(parent, text=label, bg=BG, fg=MUTED,
                 font=("Helvetica", 9)).pack(anchor="w")
        var = tk.StringVar(value=default)
        tk.Entry(parent, textvariable=var,
                 bg=ENTRY, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Helvetica", 11),
                 width=40).pack(anchor="w", pady=(2, 10), ipady=5)
        return var

    def _stat(self, parent, label: str, color: str) -> tk.Label:
        f = tk.Frame(parent, bg=BG)
        f.pack(side="left", expand=True)
        tk.Label(f, text=label, bg=BG, fg=MUTED,
                 font=("Helvetica", 8)).pack()
        lbl = tk.Label(f, text="0", bg=BG, fg=color,
                       font=("Helvetica", 16, "bold"))
        lbl.pack()
        return lbl

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = self.winfo_width()
        h  = self.winfo_height()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ------------------------------------------------------------------
    # Log helpers (thread-safe via after())
    # ------------------------------------------------------------------

    def _log(self, text: str, tag: str = ""):
        self.log.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        if tag:
            self.log.insert("end", f"[{ts}] {text}\n", tag)
        else:
            self.log.insert("end", f"[{ts}] {text}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _tlog(self, text: str, tag: str = ""):
        self.after(0, self._log, text, tag)

    # ------------------------------------------------------------------
    # Send
    # ------------------------------------------------------------------

    def _on_send(self):
        if self._sending:
            return

        try:
            host    = self.var_host.get().strip()
            port    = int(self.var_port.get().strip())
            sender  = self.var_sender.get().strip()
            recip   = self.var_recipient.get().strip()
            count   = int(self.var_count.get().strip())
        except ValueError as exc:
            self._log(f"Invalid input: {exc}", "fail")
            return

        if not host or not sender or not recip:
            self._log("Host, From, and To are required.", "fail")
            return
        if count < 1:
            self._log("Count must be at least 1.", "fail")
            return

        # Reset UI
        self.lbl_sent.config(text="0")
        self.lbl_failed.config(text="0")
        self.lbl_total.config(text="0")
        self.progress["maximum"] = count
        self.progress["value"]   = 0
        self._sending = True
        self.btn.config(state="disabled", text="Sending…")

        self._log("=" * 50, "heading")
        self._log(f"Relay : {host}:{port}", "info")
        self._log(f"From  : {sender}", "info")
        self._log(f"To    : {recip}", "info")
        self._log(f"Count : {count}", "info")
        self._log("=" * 50, "heading")

        threading.Thread(
            target=self._worker,
            args=(host, port, sender, recip, count),
            daemon=True,
        ).start()

    def _worker(self, host, port, sender, recip, count):
        import time
        sent = failed = 0
        builders = MAIL_BUILDERS * (count // len(MAIL_BUILDERS) + 1)
        random.shuffle(builders)
        jobs = builders[:count]

        for i, builder in enumerate(jobs, start=1):
            msg = builder(sender, recip)
            subject = msg["Subject"]
            ok, err = send_one(host, port, sender, recip, msg, timeout=10)

            if ok:
                sent += 1
                self._tlog(f"[{i}/{count}]  OK   {subject}", "ok")
            else:
                failed += 1
                self._tlog(f"[{i}/{count}]  FAIL {subject}  ({err})", "fail")

            self.after(0, self.lbl_sent.config,   {"text": str(sent)})
            self.after(0, self.lbl_failed.config, {"text": str(failed)})
            self.after(0, self.lbl_total.config,  {"text": str(i)})
            self.after(0, self.progress.configure, {"value": i})

        self.after(0, self._done, sent, failed, count)

    def _done(self, sent, failed, total):
        tag = "ok" if failed == 0 else ("info" if sent > 0 else "fail")
        self._log("=" * 50, "heading")
        self._log(f"Done — Sent: {sent}  Failed: {failed}  Total: {total}", tag)
        self._log("=" * 50, "heading")
        self.btn.config(state="normal", text="Send Test Emails")
        self._sending = False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    App().mainloop()
