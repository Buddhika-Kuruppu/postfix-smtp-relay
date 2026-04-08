# Postfix SMTP Test Client

Tools for simulating application mail generation and sending test emails to a Postfix SMTP relay. Includes a command-line client and a graphical UI.

---

## Contents

```
test-client/
├── smtp_test_client.py       # CLI tool
├── smtp_test_client_ui.py    # GUI tool (Tkinter)
└── README.md                 # This file
```

**No external dependencies** — uses Python 3.10+ standard library only (`smtplib`, `tkinter`, `email`).

---

## GUI Tool

### Launch

```bash
python3 smtp_test_client_ui.py
```

![SMTP Test Client main window](images/ui-main.png)
*Main window of the SMTP Test Client GUI*

### How to use

Fill in the four fields and click **Send Test Emails**.

| Field | Description | Default |
|---|---|---|
| SMTP Relay Host / IP | Hostname or IP address of your Postfix server | `127.0.0.1` |
| Port | SMTP port your relay listens on | `25` |
| From Address | Sender address used in the email envelope | `app@example.com` |
| To Address | Recipient address for all test emails | `user@example.com` |
| Number of Test Emails | How many emails to generate and send | `4` |

> **Network requirement:** The machine running this tool must be able to reach the Postfix relay on the specified host and port. Check your `mynetworks` setting in `main.cf` to ensure your client IP is allowed.

### Sending emails

Click **Send Test Emails** to start. Each email is sent sequentially and the result appears in the output log in real time.

![Sending emails in progress](images/ui-sending.png)
*Progress bar and live log during sending*

### Reading the output log

| Colour | Meaning |
|---|---|
| Green `OK` | Email accepted by the Postfix relay |
| Red `FAIL` | Relay rejected the connection or returned an SMTP error |

The stat counters at the bottom show a running tally of **Sent**, **Failed**, and **Total**.

![Successful send result](images/ui-success.png)
*All emails accepted — green OK entries and Sent counter updated*

![Failed send result](images/ui-fail.png)
*Connection refused — red FAIL entries with the error reason*

---

## CLI Tool

### Usage

```bash
python3 smtp_test_client.py --from <sender> --to <recipient> [options]
```

```
options:
  --host HOST      Postfix relay hostname or IP  (default: 127.0.0.1)
  --port PORT      SMTP port                     (default: 25)
  --from ADDRESS   Sender address                (required)
  --to ADDRESS     Recipient address             (required)
  --type TYPE      Mail type to send             (default: notification)
  --count N        Number of emails to send      (default: 1)
  --delay SECS     Pause between emails          (default: 0)
  --timeout SECS   SMTP connection timeout       (default: 10)
  --verbose        Print raw SMTP conversation
```

### Mail types

| `--type` value | Description |
|---|---|
| `notification` | User login detected, with timestamp and source IP |
| `alert` | System monitoring alert — INFO / WARNING / CRITICAL |
| `report` | Daily summary with randomised tabular data |
| `welcome` | New-user onboarding email |
| `bulk` | Random mix, repeated `--count` times |
| `all` | One of each type (4 emails total) |

### Examples

**Send one notification:**

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@example.com \
  --to user@example.com
```

![CLI single email send](images/cli-single.png)
*Sending a single notification email from the terminal*

**Send one of every type:**

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@example.com \
  --to user@example.com \
  --type all
```

**Bulk test — 20 mixed emails, 200 ms apart:**

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@example.com \
  --to user@example.com \
  --type bulk --count 20 --delay 0.2
```

![CLI bulk send result](images/cli-bulk.png)
*Bulk send summary showing sent and failed counts*

**Verbose mode (shows raw SMTP dialogue):**

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@example.com \
  --to user@example.com \
  --type alert --verbose
```

![CLI verbose SMTP output](images/cli-verbose.png)
*Verbose mode displaying the raw SMTP handshake*

### Exit codes

| Code | Meaning |
|---|---|
| `0` | All emails sent successfully |
| `1` | One or more emails failed |

---

## Generated Email Formats

Every test email is sent as a **MIME multipart** message containing both a plain-text and an HTML part — matching the format used by real application mailers.

### Notification

```
Subject: [Notification] Action required – 2024-05-01 14:32:10

Hello,

This is an automated notification from your application.

Event:     User login detected
Timestamp: 2024-05-01 14:32:10
Source IP: 10.42.178.91

If this was not you, please contact support immediately.
```

### Alert

```
Subject: [CRITICAL] database alert – 2024-05-01 14:32:11

ALERT LEVEL: CRITICAL
SERVICE:     database
TIMESTAMP:   2024-05-01 14:32:11
HOST:        app-server-03

Description: High CPU usage detected on database. Current usage at 97%.

Please investigate immediately.
```

### Report

```
Subject: Daily Summary Report – 2024-05-01

Daily Summary Report
Generated: 2024-05-01 14:32:12

    1.  orders=312  revenue=$4821
    2.  orders=87   revenue=$1034
    3.  orders=450  revenue=$9102

Total records: 3
```

### Welcome

```
Subject: Welcome to the platform, alice!

Hi alice,

Welcome! Your account has been created successfully.

  Username:   alice
  Created at: 2024-05-01 14:32:13

Get started: https://app.example.com/dashboard
```

---

## Troubleshooting

**Connection refused**

```
[FAIL] Connection error: [Errno 111] Connection refused
```

- Confirm Postfix is running: `sudo systemctl status postfix`
- Check the relay host and port are correct
- Verify your client IP is in `mynetworks` in `main.cf`

**SMTP relay access denied**

```
[FAIL] SMTP error: (554, b'5.7.1 <user@example.com>: Relay access denied')
```

- Your sender or recipient may be blocked by `sender_access` or `recipient_access` maps
- Run `sudo postmap /etc/postfix/sender_access` after any map changes

**Timeout**

```
[FAIL] Connection error: timed out
```

- Check firewall rules — port 25 must be reachable from the test client host
- Try increasing `--timeout` (CLI) or check network connectivity

**Verify delivery via mail log on the relay server:**

```bash
sudo tail -f /var/log/mail.log
```
