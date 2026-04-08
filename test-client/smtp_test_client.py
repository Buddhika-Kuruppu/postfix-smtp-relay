#!/usr/bin/env python3
"""
Postfix SMTP Test Client

Simulates application mail generation and sends to a Postfix relay server.
Supports multiple mail types, bulk sending, and HTML/plain-text content.

Usage:
    python smtp_test_client.py --help
    python smtp_test_client.py --host 127.0.0.1 --from app@example.com --to user@example.com
    python smtp_test_client.py --host 127.0.0.1 --from app@example.com --to user@example.com --type bulk --count 5
"""

import argparse
import smtplib
import sys
import time
import random
import socket
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid


# ---------------------------------------------------------------------------
# Mail templates – simulating common application-generated emails
# ---------------------------------------------------------------------------

def build_notification(sender: str, recipient: str) -> MIMEMultipart:
    """Simulate a generic application notification email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Notification] Action required – {_ts()}"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_domain(sender))

    plain = (
        "Hello,\n\n"
        "This is an automated notification from your application.\n\n"
        f"Event:     User login detected\n"
        f"Timestamp: {_ts()}\n"
        f"Source IP: {_random_ip()}\n\n"
        "If this was not you, please contact support immediately.\n\n"
        "Regards,\nApplication Team"
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
    """Simulate a system/monitoring alert email."""
    levels = ["WARNING", "CRITICAL", "INFO"]
    level = random.choice(levels)
    services = ["database", "cache", "api-gateway", "worker", "scheduler"]
    service = random.choice(services)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{level}] {service} alert – {_ts()}"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_domain(sender))
    msg["X-Priority"] = "1" if level == "CRITICAL" else "3"

    plain = (
        f"ALERT LEVEL: {level}\n"
        f"SERVICE:     {service}\n"
        f"TIMESTAMP:   {_ts()}\n"
        f"HOST:        app-server-{random.randint(1, 5):02d}\n\n"
        f"Description: High CPU usage detected on {service}. "
        f"Current usage at {random.randint(85, 99)}%.\n\n"
        "Please investigate immediately.\n\n"
        "-- Monitoring System"
    )
    html = f"""\
<html><body>
<h2 style="color:{'red' if level=='CRITICAL' else 'orange' if level=='WARNING' else 'blue'}">
  {level} Alert</h2>
<table border="1" cellpadding="6" cellspacing="0">
  <tr><th>Field</th><th>Value</th></tr>
  <tr><td>Service</td><td>{service}</td></tr>
  <tr><td>Timestamp</td><td>{_ts()}</td></tr>
  <tr><td>Host</td><td>app-server-{random.randint(1,5):02d}</td></tr>
  <tr><td>CPU Usage</td><td>{random.randint(85,99)}%</td></tr>
</table>
<p>Please investigate immediately.</p>
<p><em>-- Monitoring System</em></p>
</body></html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def build_report(sender: str, recipient: str) -> MIMEMultipart:
    """Simulate a scheduled report email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily Summary Report – {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_domain(sender))

    rows = random.randint(3, 7)
    table_plain = "\n".join(
        f"  {i+1:>3}.  orders={random.randint(10,500)}  revenue=${random.randint(100,9999)}"
        for i in range(rows)
    )
    table_html = "".join(
        f"<tr><td>{i+1}</td><td>{random.randint(10,500)}</td>"
        f"<td>${random.randint(100,9999)}</td></tr>"
        for i in range(rows)
    )

    plain = (
        f"Daily Summary Report\n"
        f"Generated: {_ts()}\n"
        f"{'='*40}\n\n"
        f"{table_plain}\n\n"
        f"Total records: {rows}\n\n"
        "This is an automated report. Do not reply to this email."
    )
    html = f"""\
<html><body>
<h2>Daily Summary Report</h2>
<p><small>Generated: {_ts()}</small></p>
<table border="1" cellpadding="6" cellspacing="0">
  <tr><th>#</th><th>Orders</th><th>Revenue</th></tr>
  {table_html}
</table>
<p><em>This is an automated report. Do not reply to this email.</em></p>
</body></html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def build_welcome(sender: str, recipient: str) -> MIMEMultipart:
    """Simulate a new-user welcome email."""
    username = recipient.split("@")[0]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Welcome to the platform, {username}!"
    msg["From"] = sender
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_domain(sender))

    plain = (
        f"Hi {username},\n\n"
        "Welcome! Your account has been created successfully.\n\n"
        f"  Username:   {username}\n"
        f"  Created at: {_ts()}\n\n"
        "Get started by visiting: https://app.example.com/dashboard\n\n"
        "Cheers,\nThe Team"
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


# Mail type registry
MAIL_TYPES = {
    "notification": build_notification,
    "alert":        build_alert,
    "report":       build_report,
    "welcome":      build_welcome,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _domain(address: str) -> str:
    parts = address.split("@")
    return parts[1] if len(parts) == 2 else "example.com"


def _random_ip() -> str:
    return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


# ---------------------------------------------------------------------------
# SMTP send
# ---------------------------------------------------------------------------

def send_email(
    host: str,
    port: int,
    sender: str,
    recipient: str,
    msg: MIMEMultipart,
    timeout: int,
    verbose: bool,
) -> bool:
    subject = msg["Subject"]
    try:
        with smtplib.SMTP(host=host, port=port, timeout=timeout) as server:
            if verbose:
                server.set_debuglevel(1)
            server.ehlo_or_helo_if_needed()
            server.sendmail(sender, [recipient], msg.as_string())
        print(f"  [OK]  {subject}")
        return True
    except smtplib.SMTPException as exc:
        print(f"  [FAIL] SMTP error – {exc}  |  subject: {subject}")
        return False
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        print(f"  [FAIL] Connection error – {exc}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Postfix SMTP Test Client – simulates application mail generation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send one notification
  python smtp_test_client.py --host 127.0.0.1 --from app@example.com --to user@example.com

  # Send 10 mixed emails with a 0.5 s delay between each
  python smtp_test_client.py --host 127.0.0.1 --from app@example.com --to user@example.com \\
      --type bulk --count 10 --delay 0.5

  # Send only alert emails
  python smtp_test_client.py --host 127.0.0.1 --from app@example.com --to user@example.com \\
      --type alert --count 3
""",
    )

    parser.add_argument("--host",    default="127.0.0.1",
                        help="Postfix relay hostname or IP (default: 127.0.0.1)")
    parser.add_argument("--port",    type=int, default=25,
                        help="SMTP port (default: 25)")
    parser.add_argument("--from",    dest="sender", required=True,
                        metavar="ADDRESS", help="Envelope/From address")
    parser.add_argument("--to",      dest="recipient", required=True,
                        metavar="ADDRESS", help="Recipient address")
    parser.add_argument("--type",    choices=list(MAIL_TYPES) + ["bulk", "all"],
                        default="notification",
                        help=(
                            "Mail type to send. "
                            "'bulk' sends a random mix; "
                            "'all' sends one of each type. "
                            f"Specific types: {', '.join(MAIL_TYPES)}. "
                            "(default: notification)"
                        ))
    parser.add_argument("--count",   type=int, default=1,
                        help="Number of emails to send (default: 1; ignored when --type=all)")
    parser.add_argument("--delay",   type=float, default=0.0,
                        help="Seconds to wait between emails (default: 0)")
    parser.add_argument("--timeout", type=int, default=10,
                        help="SMTP connection timeout in seconds (default: 10)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable SMTP debug output")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"\nPostfix SMTP Test Client")
    print(f"{'='*40}")
    print(f"  Relay host : {args.host}:{args.port}")
    print(f"  Sender     : {args.sender}")
    print(f"  Recipient  : {args.recipient}")
    print(f"  Mode       : {args.type}")
    if args.type != "all":
        print(f"  Count      : {args.count}")
    print(f"{'='*40}\n")

    sent = failed = 0

    # Build the list of (builder_fn, label) to send
    if args.type == "all":
        jobs = [(fn, name) for name, fn in MAIL_TYPES.items()]
    elif args.type == "bulk":
        builders = list(MAIL_TYPES.values())
        jobs = [(random.choice(builders), "") for _ in range(args.count)]
    else:
        fn = MAIL_TYPES[args.type]
        jobs = [(fn, args.type) for _ in range(args.count)]

    for i, (builder, _) in enumerate(jobs, start=1):
        print(f"[{i}/{len(jobs)}] Sending …", end=" ", flush=True)
        msg = builder(args.sender, args.recipient)
        ok = send_email(
            host=args.host,
            port=args.port,
            sender=args.sender,
            recipient=args.recipient,
            msg=msg,
            timeout=args.timeout,
            verbose=args.verbose,
        )
        if ok:
            sent += 1
        else:
            failed += 1

        if args.delay > 0 and i < len(jobs):
            time.sleep(args.delay)

    print(f"\n{'='*40}")
    print(f"  Sent:   {sent}")
    print(f"  Failed: {failed}")
    print(f"  Total:  {len(jobs)}")
    print(f"{'='*40}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
