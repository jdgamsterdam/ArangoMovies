#!/bin/bash


# Define the URL and filename
DEB_URL="https://download.arangodb.com/arangodb312/DEBIAN/amd64/arangodb3-client_3.12.4.3-1_amd64.deb"
DEB_FILE="arangodb3-client_3.12.4.3-1_amd64.deb"

# Download the .deb file
wget -O "$DEB_FILE" "$DEB_URL"

# Install the package
dpkg -i "$DEB_FILE"

# Fix any missing dependencies
apt-get install -f -y

# Cleanup downloaded file
rm "$DEB_FILE"

echo "Installation complete!"


#Set up Python Client . Make Sure VENV Is setup

pip install python-arango --upgrade
pip install python-dotenv
pip install git+https://github.com/plotly/dash.git


