#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 <src_directory>"
    echo "Example: $0 /path/to/src"
    exit 1
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root."
    exit 1
fi

# Check if the user provided a source directory
if [ "$#" -ne 1 ]; then
    usage
fi

SRC_DIR=$(realpath "$1")

# Verify that the source directory exists
if [ ! -d "$SRC_DIR" ]; then
    echo "Source directory '$SRC_DIR' does not exist."
    exit 1
fi

# Copy src content in destination
cp -R "./src/*" $SRC_DIR

# Copy settings to it's destination
mkdir /etc/BackToTheFile/
cp files/settings.conf /etc/BackToTheFile/
chmod 755 /etc/BackToTheFile/
chmod 644 /etc/BackToTheFile/settings.conf

# Define the service file and its destination
SERVICE_FILE="files/backtothefile.service"
DEST_SERVICE_FILE="/etc/systemd/system/backtothefile.service"
TIMER_FILE="files/backtothefile.timer"
DEST_TIMER_FILE="/etc/systemd/system/backtothefile.timer"

# Copy the service file and modify it
if [ -f "$SERVICE_FILE" ]; then
    cp "$SERVICE_FILE" "$DEST_SERVICE_FILE"
    cp "$TIMER_FILE" "$DEST_TIMER_FILE"

    sed -i "s|^ExecStart=.*|ExecStart=$SRC_DIR/BackToTheFile.py|" "$DEST_SERVICE_FILE"

    echo "Service file installed to $DEST_SERVICE_FILE"
else
    echo "Service file '$SERVICE_FILE' does not exist."
    exit 1
fi

# Reload systemd to recognize the new service
systemctl daemon-reload

echo "Installation complete. Please review /etc/BackToTheFile/settings.conf."
echo "To enable this script please run following command"
echo "sudo systemctl enable backtothefile.timer"

