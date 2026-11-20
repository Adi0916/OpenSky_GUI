## Project Description
This system is designed for the automatic collection and analysis of real-time air traffic data using the [OpenSky Network API](https://openskynetwork.github.io/opensky-api/rest.html). The project implements a complete ETL (Extract, Transform, Load) process – from data extraction through API, data validation and archiving in a relational database, to analytical processing.

## Installation and Usage

This project uses **`uv`** for dependency and environment management.

If you do not have `uv` installed:

* **Linux/macOS:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
* **Windows:** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

### Visualisation with data download:
To run visualisation with data download run the commands bellow in your terminal.
```bash
# Clone git repository
git clone https://github.com/Adi0916/OpenSky_GUI

# Change directory to the git repository
cd OpenSky_GUI/

# Start the main gui window with scheduler in the background
uv run ./src/opensky_gui/__init__.py
```
