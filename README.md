# HerRoute 🛡️

HerRoute is a crowd-sourced safety and navigation web application designed to help users find the safest walking routes. It analyzes real-time incident reports, lighting, crowd density, and safe spaces to calculate dynamic safety scores for alternative paths.

## 🚀 Features

* **Smart Route Navigation:** Compares multiple walking routes and highlights the safest option.
* **Dynamic Safety Scoring:** Calculates a 0-100 score based on weighted safety factors (lighting, crowds, establishments, and incident history).
* **"Unreported" Route Detection:** Clearly identifies routes lacking historical data, warning users to proceed with caution rather than assuming safety.
* **Crowd-Sourced Reporting:** Users can drop pins to report unsafe areas, harassment, poor lighting, or suspicious activities.
* **Emergency Support Mapping:** Locates nearby hospitals, police stations, and pharmacies using the Overpass API within a 1km radius.
* **Adaptive UI:** Built-in Light/Dark mode toggle for comfortable viewing at night.

## 💻 Tech Stack

* **Backend:** Python, Django
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Mapping & APIs:** Leaflet.js, OpenStreetMap, Overpass API
* **Deployment:** Render, Gunicorn

## 🛠️ Local Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/HERROUTE-.git](https://github.com/yourusername/HERROUTE-.git)
   cd HERROUTE-
