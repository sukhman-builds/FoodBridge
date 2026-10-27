<div align="center">

# 🍲 FoodBridge
**Connecting Surplus Food with Communities in Need — in Real Time.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Status](https://img.shields.io/badge/Status-Active_Development-orange.svg)](#)

<p align="center">
  <a href="#about-the-project">About</a> •
  <a href="#key-features">Key Features</a> •
  <a href="#system-architecture">Architecture</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#contributing">Contributing</a>
</p>

</div>

---

## 🌍 The Problem & Our Solution

Every day, restaurants, caterers, and grocery suppliers discard tons of high-grade, edible surplus food due to end-of-day operational overhead. At the same time, local shelters and community kitchens run dangerously short on meals.

**FoodBridge** removes the operational friction of food donation by turning surplus redistribution into an on-demand, hyper-local logistics pipeline:
1. **Donors Post:** Kitchens upload surplus items in seconds with quantity, safe-consumption window, and pickup coordinates.
2. **Smart Matching:** The platform alerts nearby registered NGOs and volunteers based on proximity and food shelf-life urgency.
3. **Dispatch & Trace:** Logistics tracking verifies chain-of-custody from donor handover to shelter distribution.

---

## ✨ Key Features

- **⚡ Zero-Friction Donation Intake:** Quick-log interface designed for busy kitchen staff to register batch donations in under 30 seconds.
- **📍 Proximity & Urgency Matching:** Radius-based geospatial routing prioritizes short shelf-life items to the closest verified distribution points.
- **🛡️ Role-Based Workflows:**
  - **Donors:** Real-time logging, donation logs, and tax/impact receipts.
  - **Shelters & Pantries:** Real-time rescue radar, inventory requests, and fulfillment confirmation.
  - **Volunteers / Runners:** Claim pickup tasks, navigation guidance, and handoff verification.
- **📊 Impact Ledger:** Live dashboard measuring total meals served, weight rescued (kg), and estimated CO₂-equivalent greenhouse emissions diverted from landfills.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React / Next.js, Tailwind CSS, Lucide Icons |
| **Backend & Services** | Node.js / Express *(or Spring Boot)*, REST APIs, WebSockets |
| **Database** | PostgreSQL / MongoDB / Firestore |
| **Mapping & Location** | Mapbox / Google Maps API, Geo-hashing |
| **Auth & Security** | JWT / Firebase Auth, Role-Based Access Control (RBAC) |

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed locally:
- [Node.js](https://nodejs.org/) (v18.0.0 or higher)
- [npm](https://www.npmjs.com/) or [yarn](https://yarnpkg.com/) / [pnpm](https://pnpm.io/)
- A running database instance (e.g., PostgreSQL or MongoDB)

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/sukhman-builds/FoodBridge.git](https://github.com/sukhman-builds/FoodBridge.git)
   cd FoodBridge
