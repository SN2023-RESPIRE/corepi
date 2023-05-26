# corepi

## Setup

1. Clone this repo
2. Create a Python venv (optional)
3. Install the packages from `requirements.txt`
4. Create a .env file at the project root
5. Create a `DATABASE_WEBSITE_URI` entry in the .env file with the correct URI
6. Edit main.py if necessary to use the correct serial port and local SQLite database
7. Run

Extra Notes:
- This program is meant to run on a Raspberry Pi, therefore you need to enable UART. Here are the steps to enable UART on a Raspberry Pi:
  - Edit `/boot/config.txt` and add the line `dtoverlay=pi3-disable-bt`
  - Edit `/boot/cmdline.txt` and remove `console=serial0,115200`
  - Reboot the device
