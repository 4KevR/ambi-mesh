# ambi-mesh

*Ambi-mesh* is your new local network mesh for self-made ambient lights.
It runs on ESP microcontrollers that are equipped with single-wire-based LED strips (such as the WS2812) and is able to
scale with multiple instances inside your network. This enables more flexible usage by different clients. Currently, a
Python client is available, which makes it possible to replicate screen colors from a personal computer to the network.

## Setup

### Prerequisites

* Python 3.12 (tested; earlier Python versions should also work)
* Arduino IDE

### ESP

Follow these steps to run the mesh software on your ESPs (e.g., on a NodeMCU):

1. Connect your data pin of the LED strip to pin 3 of the ESP (use the GPIO3 pin; do specific research for your board)
2. Set up your Arduino IDE to upload the script to the boards
    * Install the esp8266 package in the board manager
      (add **http://arduino.esp8266.com/stable/package_esp8266com_index.json** to additional board manager URLs
      in preferences)
    * Install the following libraries:
      * Adafruit NeoPixel (Adafruit)
      * ArduinoJson (Benoit Blanchon)
      * UUID (Rob Tillaart)
3. Open **src/esp/esp.ino** in your Arduino IDE
4. Select your board and upload the script
5. Repeat with other ESPs you might have

### Client

This project uses *tkinter* to provide a basic UI for mesh network interactions. Make sure that tkinter works in
your Python environment by executing `python -m tkinter`. It should open a window that shows the current *tcl/tk*
version. If you are on Mac and use *pyenv* to manage Python environments, you can install a new version of *tcl/tk* via
homebrew: `brew install tcl-tk`. After that, you can reinstall your Python version to make sure that the homebrew
version of *tcl/tk* is used.

After you make sure that tkinter works, you can follow these steps to run the local Python client:

```bash
cd src/client
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Usage

The usage, along with some screenshots of the client, is described in the following 
[wiki page](https://github.com/4KevR/ambi-mesh/wiki/Usage).
