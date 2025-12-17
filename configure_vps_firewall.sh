#!/bin/bash
# VPS Firewall Configuration
# Run this on the VPS: emo@66.42.93.128

set -e

echo "🔒 VPS Firewall Configuration"
echo "============================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run with sudo"
   echo "Usage: sudo bash configure_vps_firewall.sh"
   exit 1
fi

echo "Configuring UFW firewall..."
echo ""

# Enable UFW
ufw --force enable

# Allow SSH (critical - don't lock yourself out!)
ufw allow 22/tcp
echo "✓ Allowed SSH (22)"

# Allow HTTP
ufw allow 80/tcp
echo "✓ Allowed HTTP (80)"

# Allow HTTPS
ufw allow 443/tcp
echo "✓ Allowed HTTPS (443)"

# Allow LM Studio port (for Computer A tunnel)
ufw allow 1234/tcp
echo "✓ Allowed LM Studio (1234)"

echo ""
echo "Firewall Status:"
ufw status verbose

echo ""
echo "========================================" echo "✅ Firewall Configured Successfully!"
echo "========================================"
echo ""
echo "Open Ports:"
echo "  22   - SSH (admin access)"
echo "  80   - HTTP (web traffic)"
echo "  443  - HTTPS (secure web traffic)"
echo "  1234 - LM Studio (Computer A tunnel)"
echo ""

