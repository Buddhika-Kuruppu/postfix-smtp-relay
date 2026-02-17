#!/usr/bin/env bash
#
# Postfix SMTP Relay - Deployment Script
# Deploys and configures Postfix as an SMTP relay on Ubuntu Server
#
# Usage:
#   sudo bash deploy.sh
#
# The script will prompt for all required configuration values.

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POSTFIX_DIR="/etc/postfix"
CONFIG_SRC="${SCRIPT_DIR}/postfix-config"
LOG_FILE="/var/log/postfix-relay-deploy.log"

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" | tee -a "$LOG_FILE"; }
err() { log "ERROR: $1" >&2; exit 1; }

prompt() {
    local var_name="$1" prompt_text="$2" default="${3:-}"
    local value
    if [[ -n "$default" ]]; then
        read -rp "${prompt_text} [${default}]: " value
        value="${value:-$default}"
    else
        while [[ -z "${value:-}" ]]; do
            read -rp "${prompt_text}: " value
        done
    fi
    eval "$var_name=\$value"
}

prompt_secret() {
    local var_name="$1" prompt_text="$2"
    local value
    while [[ -z "${value:-}" ]]; do
        read -rsp "${prompt_text}: " value
        echo
    done
    eval "$var_name=\$value"
}

# ──────────────────────────────────────────────────────────────────────────────
# Pre-flight checks
# ──────────────────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root. Use: sudo bash deploy.sh"
fi

if ! grep -qi 'ubuntu' /etc/os-release 2>/dev/null; then
    err "This script is designed for Ubuntu Server."
fi

if [[ ! -d "$CONFIG_SRC" ]]; then
    err "Configuration directory not found: ${CONFIG_SRC}"
fi

log "Starting Postfix SMTP Relay deployment"

# ──────────────────────────────────────────────────────────────────────────────
# Gather configuration from user
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "  Postfix SMTP Relay - Configuration"
echo "========================================="
echo ""

echo "── Admin User Setup ──"
prompt ADMIN_USER "Dedicated admin username" "postfix-admin"
prompt_secret ADMIN_PASS "Password for admin user"
echo ""

echo "── SMTP Relay Settings ──"
prompt RELAY_HOST "SMTP relay host (e.g. smtp.office365.com, smtp.gmail.com)" "smtp.office365.com"
prompt RELAY_PORT "SMTP relay port" "587"
prompt SMTP_USER  "SMTP username (email address)"
prompt_secret SMTP_PASS "SMTP password (or app password)"
prompt MY_HOSTNAME "Server hostname" "$(hostname -f)"
prompt MY_DOMAIN   "Your mail domain (e.g. yourdomain.com)"
prompt MY_NETWORKS "Trusted networks (comma-separated CIDR, e.g. 10.0.0.0/8, 172.16.0.0/16)" "127.0.0.0/8"
prompt INET_IFACES "Listen interfaces (loopback-only / all)" "loopback-only"

echo ""
echo "─────────────────────────────────────────"
echo "  Admin user : ${ADMIN_USER}"
echo "  Relay host : [${RELAY_HOST}]:${RELAY_PORT}"
echo "  SMTP user  : ${SMTP_USER}"
echo "  Hostname   : ${MY_HOSTNAME}"
echo "  Domain     : ${MY_DOMAIN}"
echo "  Networks   : ${MY_NETWORKS}"
echo "  Interfaces : ${INET_IFACES}"
echo "─────────────────────────────────────────"
read -rp "Proceed with deployment? [Y/n]: " confirm
if [[ "${confirm,,}" == "n" ]]; then
    log "Deployment cancelled by user."
    exit 0
fi

# ──────────────────────────────────────────────────────────────────────────────
# Step 1 — Update system and install dependencies
# ──────────────────────────────────────────────────────────────────────────────
log "Updating system packages..."
apt-get update -qq

log "Installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
debconf-set-selections <<< "postfix postfix/mailname string ${MY_HOSTNAME}"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"
apt-get install -y -qq \
    postfix \
    libsasl2-modules \
    mailutils \
    ca-certificates \
    bsd-mailx

log "All dependencies installed."

# ──────────────────────────────────────────────────────────────────────────────
# Step 2 — Create dedicated admin user
# ──────────────────────────────────────────────────────────────────────────────
if id "$ADMIN_USER" &>/dev/null; then
    log "User '${ADMIN_USER}' already exists — skipping creation."
else
    log "Creating dedicated admin user '${ADMIN_USER}'..."
    useradd \
        --create-home \
        --shell /bin/bash \
        --comment "Postfix SMTP Relay Admin" \
        "$ADMIN_USER"
    echo "${ADMIN_USER}:${ADMIN_PASS}" | chpasswd
    log "User '${ADMIN_USER}' created."
fi

# Add to postfix group (read Postfix configs, view queue)
usermod -aG postfix "$ADMIN_USER"

# Grant limited sudo for Postfix management only
SUDOERS_FILE="/etc/sudoers.d/${ADMIN_USER}"
log "Configuring sudo permissions for '${ADMIN_USER}'..."
cat > "$SUDOERS_FILE" <<SUDOEOF
# Postfix SMTP Relay — admin privileges for ${ADMIN_USER}
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/sbin/postfix *
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/sbin/postmap *
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/sbin/postconf *
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/sbin/postsuper *
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl restart postfix
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl reload postfix
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl status postfix
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl stop postfix
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/systemctl start postfix
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/journalctl -u postfix *
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/tail -f /var/log/mail.log
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/bin/tail -n * /var/log/mail.log
SUDOEOF
chmod 440 "$SUDOERS_FILE"
visudo -cf "$SUDOERS_FILE" || err "Sudoers syntax error in ${SUDOERS_FILE}"
log "Sudo permissions configured."

# ──────────────────────────────────────────────────────────────────────────────
# Step 3 — Back up existing Postfix configuration
# ──────────────────────────────────────────────────────────────────────────────
BACKUP_DIR="${POSTFIX_DIR}/backup-$(date '+%Y%m%d-%H%M%S')"
if [[ -f "${POSTFIX_DIR}/main.cf" ]]; then
    log "Backing up existing Postfix configuration to ${BACKUP_DIR}..."
    mkdir -p "$BACKUP_DIR"
    cp -a "${POSTFIX_DIR}/main.cf" "$BACKUP_DIR/"
    [[ -f "${POSTFIX_DIR}/sasl_passwd" ]] && cp -a "${POSTFIX_DIR}/sasl_passwd" "$BACKUP_DIR/"
    [[ -f "${POSTFIX_DIR}/sender_access" ]] && cp -a "${POSTFIX_DIR}/sender_access" "$BACKUP_DIR/"
    [[ -f "${POSTFIX_DIR}/recipient_access" ]] && cp -a "${POSTFIX_DIR}/recipient_access" "$BACKUP_DIR/"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Step 4 — Deploy configuration files
# ──────────────────────────────────────────────────────────────────────────────
log "Deploying configuration files..."

cp "${CONFIG_SRC}/main.cf" "${POSTFIX_DIR}/main.cf"
cp "${CONFIG_SRC}/sender_access" "${POSTFIX_DIR}/sender_access"
cp "${CONFIG_SRC}/recipient_access" "${POSTFIX_DIR}/recipient_access"

# ──────────────────────────────────────────────────────────────────────────────
# Step 5 — Apply user-provided values to main.cf
# ──────────────────────────────────────────────────────────────────────────────
log "Applying configuration values..."

sed -i "s|^myhostname = .*|myhostname = ${MY_HOSTNAME}|"                       "${POSTFIX_DIR}/main.cf"
sed -i "s|^myorigin = .*|myorigin = ${MY_DOMAIN}|"                             "${POSTFIX_DIR}/main.cf"
sed -i "s|^mynetworks = .*|mynetworks = ${MY_NETWORKS}|"                       "${POSTFIX_DIR}/main.cf"
sed -i "s|^inet_interfaces = .*|inet_interfaces = ${INET_IFACES}|"             "${POSTFIX_DIR}/main.cf"
sed -i "s|^relayhost = .*|relayhost = [${RELAY_HOST}]:${RELAY_PORT}|"          "${POSTFIX_DIR}/main.cf"

# Update sender_access and recipient_access with the actual domain
sed -i "s|^yourdomain\.com|${MY_DOMAIN}|" "${POSTFIX_DIR}/sender_access"
sed -i "s|^yourdomain\.com|${MY_DOMAIN}|" "${POSTFIX_DIR}/recipient_access"

# ──────────────────────────────────────────────────────────────────────────────
# Step 6 — Configure SMTP credentials
# ──────────────────────────────────────────────────────────────────────────────
log "Writing SMTP credentials..."

cat > "${POSTFIX_DIR}/sasl_passwd" <<EOF
[${RELAY_HOST}]:${RELAY_PORT} ${SMTP_USER}:${SMTP_PASS}
EOF

# ──────────────────────────────────────────────────────────────────────────────
# Step 7 — Build hash maps and secure files
# ──────────────────────────────────────────────────────────────────────────────
log "Building hash maps..."

postmap "${POSTFIX_DIR}/sasl_passwd"
postmap "${POSTFIX_DIR}/sender_access"
postmap "${POSTFIX_DIR}/recipient_access"

log "Securing credential files..."

chmod 600 "${POSTFIX_DIR}/sasl_passwd" "${POSTFIX_DIR}/sasl_passwd.db"
chown root:root "${POSTFIX_DIR}/sasl_passwd" "${POSTFIX_DIR}/sasl_passwd.db"

# ──────────────────────────────────────────────────────────────────────────────
# Step 8 — Set mailname
# ──────────────────────────────────────────────────────────────────────────────
echo "${MY_HOSTNAME}" > /etc/mailname

# ──────────────────────────────────────────────────────────────────────────────
# Step 9 — Update CA certificates
# ──────────────────────────────────────────────────────────────────────────────
log "Updating CA certificates..."
update-ca-certificates --fresh >/dev/null 2>&1 || true

# ──────────────────────────────────────────────────────────────────────────────
# Step 10 — Validate and restart Postfix
# ──────────────────────────────────────────────────────────────────────────────
log "Validating Postfix configuration..."

if ! postfix check 2>&1 | tee -a "$LOG_FILE"; then
    err "Postfix configuration check failed. Review the output above."
fi

log "Restarting Postfix..."
systemctl restart postfix
systemctl enable postfix

# ──────────────────────────────────────────────────────────────────────────────
# Step 11 — Verify service is running
# ──────────────────────────────────────────────────────────────────────────────
if systemctl is-active --quiet postfix; then
    log "Postfix is running."
else
    err "Postfix failed to start. Check: journalctl -u postfix -n 50"
fi

# ──────────────────────────────────────────────────────────────────────────────
# Done
# ──────────────────────────────────────────────────────────────────────────────
echo ""
echo "========================================="
echo "  Deployment Complete"
echo "========================================="
echo ""
echo "  Admin user: ${ADMIN_USER}"
echo "    Login:  ssh ${ADMIN_USER}@<server-ip>"
echo "    Sudo:   limited to Postfix commands only"
echo ""
echo "  Send a test email (as ${ADMIN_USER}):"
echo "    echo \"Test from Postfix relay\" | mail -s \"Test\" recipient@example.com"
echo ""
echo "  Manage Postfix (as ${ADMIN_USER}):"
echo "    sudo systemctl status postfix"
echo "    sudo systemctl restart postfix"
echo "    sudo postfix flush"
echo "    sudo tail -f /var/log/mail.log"
echo "    mailq"
echo ""
echo "  Deployment log: ${LOG_FILE}"
echo "  Config backup:  ${BACKUP_DIR:-none}"
echo ""

log "Deployment finished successfully."
