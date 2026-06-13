# 🚢 AquaPath AI: Intelligent Maritime Routing System

AquaPath AI is an advanced, terminal-based Python application designed to optimize global maritime shipping routes. By combining **Graph-Based Pathfinding**, **Live API Integration**, and **Machine Learning**, the system calculates the safest and most efficient path between global ports based on physical distance, live weather conditions, and historical traffic density.

---

## ✨ Key Features

* **🗺️ Geographic Pathfinding (DFS):** Utilizes a Depth-First Search algorithm to map out every possible physical route across a predefined adjacency matrix of global ports and maritime chokepoints.
* **⛈️ Live Weather Telemetry:** Pings the Open-Meteo & Marine APIs to fetch real-time 10m wind speeds and wave heights for the generated routes.
* **🚢 Traffic Congestion Analysis:** Parses a local CSV database to evaluate historical vessel traffic density for specific oceanic legs.
* **🧠 Machine Learning Risk Engine:** Instead of hardcoded rules, safety scores are calculated using a **Linear Regression** algorithm (trained via Orange Data Mining). The AI intelligently weights weather (65%) and traffic (35%) to output a precise 0.0 to 5.0 warning level.
* **⚙️ Multithreaded CLI:** Features a custom background threading engine that runs a smooth terminal loading animation without blocking API requests.
* **🛡️ Bulletproof Failsafes:** Engineered with strict error handling for network drops, API timeouts, missing local databases, and user input typos.

---

## 📂 Project Architecture

* **`main.py`** - The core application engine. Handles the CLI, pathfinding, API requests, and applies the ML mathematical formulas.
* **`train_ai.py`** - The Machine Learning training script. Uses the Orange3 framework to process our training datasets and mathematically derive the optimal Linear Regression coefficients.
* **`weather_training.csv`** - 100-line dataset mapping wind speed and wave height to a continuous weather risk score.
* **`traffic_training.csv`** - 100-line dataset mapping vessel density to a continuous traffic risk score.
* **`traffic_data.csv`** - The local database used by the routing engine to look up traffic density between two specific connected ports.

---

## 🚀 Installation & Setup

**1. Clone or Download the Repository**
Ensure all project files (`main.py`, `.csv` databases) are kept together in the same main folder.

**2. Install Dependencies**
AquaPath AI requires the `requests` library to fetch live weather data. Install it via your terminal:
```bash
pip install requests