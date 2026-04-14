# Test Cases

Use these scenarios to verify your relay's access controls are working correctly. Adjust the host, sender, and recipient addresses to match your deployment.

---

### TC-01 — Basic connectivity

Confirm the relay accepts a connection and delivers a test email from an allowed sender and recipient.

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@yourdomain.com \
  --to user@yourdomain.com
```

**Expected:** `[OK]` — email accepted and relayed.

---

### TC-02 — All mail types delivered

Verify all four generated email formats pass through the relay without issue.

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@yourdomain.com \
  --to user@yourdomain.com \
  --type all
```

**Expected:** 4 × `[OK]` — one notification, one alert, one report, one welcome.

---

### TC-03 — Sender blocked by `sender_access`

Confirm the relay rejects a sender from an unauthorised domain. Add a `REJECT` rule to `sender_access` for the test domain first, then rebuild the map:

```bash
# On the relay server
echo "blocked.com  REJECT" | sudo tee -a /etc/postfix/sender_access
sudo postmap /etc/postfix/sender_access && sudo systemctl reload postfix
```

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@blocked.com \
  --to user@yourdomain.com
```

**Expected:** `[FAIL] SMTP error` with a 554 reject code.

---

### TC-04 — Recipient blocked by `recipient_access`

Confirm the relay rejects delivery to a blocked recipient address. Add a `REJECT` rule for the test recipient, then rebuild:

```bash
# On the relay server
echo "blocked@yourdomain.com  REJECT" | sudo tee -a /etc/postfix/recipient_access
sudo postmap /etc/postfix/recipient_access && sudo systemctl reload postfix
```

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@yourdomain.com \
  --to blocked@yourdomain.com
```

**Expected:** `[FAIL] SMTP error` with a 554 reject code.

---

### TC-05 — Client IP blocked by `client_ip_access`

Confirm the relay refuses connections from an IP that is not in the allowlist. Add a `REJECT` rule for your test machine's IP, then rebuild:

```bash
# On the relay server — replace with the test client's actual IP
echo "192.168.1.50  REJECT" | sudo tee -a /etc/postfix/client_ip_access
sudo postmap /etc/postfix/client_ip_access && sudo systemctl reload postfix
```

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@yourdomain.com \
  --to user@yourdomain.com
```

**Expected:** `[FAIL] Connection error` — the relay drops the connection at the network level.

---

### TC-06 — Bulk load test

Send a large batch of mixed emails to check relay throughput and confirm no messages are silently dropped.

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@yourdomain.com \
  --to user@yourdomain.com \
  --type bulk --count 50 --delay 0.1
```

**Expected:** All 50 emails show `[OK]`. Verify on the relay with:

```bash
sudo tail -n 100 /var/log/mail.log | grep "status=sent"
```

---

### TC-07 — SMTP dialogue inspection (verbose)

Inspect the raw SMTP handshake to confirm the relay's banner, EHLO capabilities, and response codes are correct.

```bash
python3 smtp_test_client.py \
  --host 192.168.1.10 \
  --from app@yourdomain.com \
  --to user@yourdomain.com \
  --type alert --verbose
```

**Expected:** The raw SMTP exchange is printed to stdout. Confirm:
- `220` banner from the relay
- `250-` EHLO capability list
- `250 Ok` after `DATA`
- `221` on quit

---

### TC-08 — Connection timeout

Verify the `--timeout` flag works when the relay is unreachable.

```bash
python3 smtp_test_client.py \
  --host 10.255.255.1 \
  --from app@yourdomain.com \
  --to user@yourdomain.com \
  --timeout 3
```

**Expected:** `[FAIL] Connection error: timed out` after approximately 3 seconds. Exit code `1`.
