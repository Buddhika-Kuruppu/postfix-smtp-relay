# Monitoring

---

## Log Management

Postfix writes mail logs to `/var/log/mail.log` (or `/var/log/mail/mail.log` on some distributions). Systemd-managed systems can also query logs via `journalctl`.

### View Live Logs

Stream logs in real time to monitor delivery as it happens:

```bash
sudo tail -f /var/log/mail.log
```

Using journalctl (systemd):

```bash
sudo journalctl -u postfix -f
```

![Mail log output](images/mail-log.jpg)
*Monitoring mail logs for delivery status*

### View Recent Log Entries

```bash
# Last 100 lines
sudo tail -n 100 /var/log/mail.log

# Last N lines via journalctl
sudo journalctl -u postfix -n 200
```

### Filter Logs by Time

```bash
# Logs since a specific date/time
sudo journalctl -u postfix --since "2024-01-01 08:00:00"

# Logs between two timestamps
sudo journalctl -u postfix --since "2024-01-01" --until "2024-01-02"

# Logs from the last hour
sudo journalctl -u postfix --since "1 hour ago"
```

### Analyze Logs for Errors and Events

Search for delivery status and common issues:

```bash
# Show all delivery failures
sudo grep -i "status=bounced\|status=deferred" /var/log/mail.log

# Show successful deliveries
sudo grep "status=sent" /var/log/mail.log

# Show authentication errors
sudo grep -i "authentication failed\|SASL" /var/log/mail.log

# Show connection errors to relay host
sudo grep -i "connection refused\|connect to" /var/log/mail.log

# Show TLS-related entries
sudo grep -i "TLS\|certificate" /var/log/mail.log

# Count deliveries by status
sudo grep "status=" /var/log/mail.log | grep -oP "status=\K\w+" | sort | uniq -c | sort -rn
```

### Search Logs for a Specific Recipient or Message

```bash
# Find all log entries for a specific recipient
sudo grep "recipient@example.com" /var/log/mail.log

# Find log entries for a specific queue ID
sudo grep "ABC123DEF" /var/log/mail.log
```

---

## Message Queue Management

Postfix maintains a mail queue for messages that are pending delivery, deferred, or held. Queue IDs are used to reference individual messages across all queue commands.

### Check Queue Status

```bash
mailq
```

Or equivalently:

```bash
postqueue -p
```

![Mail queue status](images/mailq-output.jpg)
*Checking the mail queue for pending messages*

### View Queue Summary

```bash
# Count messages by queue type
postqueue -p | tail -n 1

# Show a summary of deferred mail
postqueue -p | grep "^[A-Z0-9]" | wc -l
```

### Inspect a Specific Message

```bash
# View headers and metadata for a message by queue ID
sudo postcat -q <queue-id>

# View the full message body
sudo postcat -qB <queue-id>
```

### Flush the Queue

Force Postfix to attempt immediate delivery of all queued messages:

```bash
sudo postqueue -f
```

Or via the Postfix control command:

```bash
sudo postfix flush
```

### Delete Messages from the Queue

```bash
# Delete a specific message by queue ID
sudo postsuper -d <queue-id>

# Delete ALL queued messages (use with caution)
sudo postsuper -d ALL

# Delete only deferred messages
sudo postsuper -d ALL deferred
```

### Hold and Release Messages

Holding a message prevents delivery without deleting it:

```bash
# Place a specific message on hold
sudo postsuper -h <queue-id>

# Hold ALL queued messages
sudo postsuper -h ALL

# Release a held message back to the active queue
sudo postsuper -H <queue-id>

# Release ALL held messages
sudo postsuper -H ALL
```

### Re-queue a Message

Move a message back to the incoming queue to force a re-processing attempt:

```bash
sudo postsuper -r <queue-id>

# Re-queue all deferred messages
sudo postsuper -r ALL deferred
```
