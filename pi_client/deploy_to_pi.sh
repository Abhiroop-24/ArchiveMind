#!/usr/bin/env bash
# ==============================================================================
# ArchiveMind - Deploy & Autostart on Raspberry Pi 3B+
# Configures headless background camera acquisition daemon via systemd.
# ==============================================================================

set -e

PI_IP="${PI_IP:-10.42.0.116}"
PI_USER="${PI_USER:-abhiroop}"
PI_PASS="${PI_PASS:-240906}"
PI_DIR="/home/${PI_USER}/archivemind_client"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "  Deploying ArchiveMind Acquisition Client to Raspberry Pi"
echo "  Target: ${PI_USER}@${PI_IP}"
echo "=========================================================="

# Check reachability
echo "[1/5] Pinging Raspberry Pi at ${PI_IP}..."
if ! ping -c 2 -W 2 "${PI_IP}" > /dev/null 2>&1; then
    echo "  ✗ Error: Raspberry Pi at ${PI_IP} is not responding."
    echo "    Check Ethernet cable and ensure laptop eno1 is at 10.42.0.1."
    exit 1
fi
echo "  ✓ Pi is reachable"

# Ensure sshpass is available
if ! command -v sshpass &> /dev/null; then
    echo "  Installing sshpass..."
    echo "240906" | sudo -S pacman -S --noconfirm sshpass || true
fi

SSH_CMD="sshpass -p ${PI_PASS} ssh -o StrictHostKeyChecking=no ${PI_USER}@${PI_IP}"
SCP_CMD="sshpass -p ${PI_PASS} scp -o StrictHostKeyChecking=no"

# Create destination directory
echo "[2/5] Creating directory on Pi..."
${SSH_CMD} "mkdir -p ${PI_DIR} /home/${PI_USER}/archivemind_captures/queue"

# Copy python files
echo "[3/5] Syncing client scripts..."
${SCP_CMD} \
    "${LOCAL_DIR}/config.py" \
    "${LOCAL_DIR}/capture.py" \
    "${LOCAL_DIR}/uploader.py" \
    "${LOCAL_DIR}/queue_manager.py" \
    "${LOCAL_DIR}/main_pi.py" \
    "${PI_USER}@${PI_IP}:${PI_DIR}/"

# Copy and install systemd unit file
echo "[4/5] Installing systemd service (archivemind-camera.service)..."
${SCP_CMD} "${LOCAL_DIR}/archivemind-camera.service" "${PI_USER}@${PI_IP}:/tmp/archivemind-camera.service"

${SSH_CMD} << 'REMOTE'
echo "240906" | sudo -S cp /tmp/archivemind-camera.service /etc/systemd/system/archivemind-camera.service
echo "240906" | sudo -S systemctl daemon-reload
echo "240906" | sudo -S systemctl enable archivemind-camera.service
echo "240906" | sudo -S systemctl restart archivemind-camera.service
REMOTE

# Verify service
echo "[5/5] Verifying service status..."
sleep 2
STATUS=$(${SSH_CMD} "systemctl is-active archivemind-camera.service" || true)

if [ "${STATUS}" = "active" ]; then
    echo "  ✓ archivemind-camera.service is ACTIVE and running on boot!"
    echo "=========================================================="
    echo "  Raspberry Pi setup complete."
    echo "  Remote endpoint: http://${PI_IP}:8082/status"
    echo "=========================================================="
else
    echo "  ⚠ Warning: Service status is ${STATUS}. Checking logs:"
    ${SSH_CMD} "journalctl -u archivemind-camera.service -n 15 --no-pager"
fi
