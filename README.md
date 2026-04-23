# Esverdant - ESG Reporting Platform for Sustainability

A comprehensive ESG (Environmental, Social, and Governance) reporting platform designed to help small and medium enterprises (SMEs) & Campuses track sustainability metrics and generate GRI-compliant reports effortlessly.

## Overview

Esverdant simplifies sustainability reporting by automating data extraction, calculations, and GRI compliance. From onboarding through monthly check-ins, the platform guides users through sustainability tracking with AI-powered insights and actionable recommendations.

---

## Core Features

### 1. **Onboarding Flow**
- Company information form (industry, size, location)
- Materiality quiz to identify key sustainability risks
- First data upload (electricity bills, fuel receipts, waste invoices, headcount)
- Instant report generation on first submission

### 2. **Data Upload & Input**
- Free text input ("we use 3 tanks of diesel a week")
- File uploads (Excel, PDF, photos of receipts/logbooks/invoices)
- AI-powered data extraction and normalization into structured JSON
- Automatic evidence tagging to specific GRI disclosures

### 3. **AI Extraction Layer**
- Intelligent extraction of 6-8 fixed data points from any format
- Automatic data normalization and validation
- Missing data point detection and flagging
- Structured JSON output: electricity_kwh, diesel_liters, waste_kg, headcount, new_hires, turnover

### 4. **Calculation Engine**
Automated conversions to GRI standards:
- electricity_kwh × 3.6 = MJ → **GRI 302-1**
- diesel_liters × 36.54 = MJ → **GRI 302-1**
- electricity_kwh × 0.6 = CO₂e → **GRI 305-2**
- diesel_liters × 2.68 = CO₂e → **GRI 305-1**
- total_co2e ÷ headcount = intensity → **GRI 305-4**
- waste_kg → **GRI 306**
- Auto-flagged missing data as Reasons for Omission

### 5. **ESG Dashboard**
- Real-time ESG Score (e.g., 72 / Good)
- Compliance status indicators (On Track / Needs Attention)
- 3-8 customizable KPIs based on extracted data
- Goals Overview with progress bars (Good → Better → Best)
- Quick Wins panel with projected cost savings (in ₱)
- Month-on-month progress tracking

### 6. **AI Interpretation Layer**
- Contextual explanations of calculated metrics
- AI-generated Quick Wins aligned with GRI standards
- Smart indicators for improvement pathways
- Dynamic updates on each monthly check-in

### 7. **1-Page ESG Plan**
- Auto-generated from first data upload
- Includes priorities, actions, owners, and timelines
- Updates with each monthly submission
- Included as first page in PDF reports

### 8. **GRI Reporting System**
Comprehensive GRI standard coverage:
- **GRI 302**: Energy (302-1, 302-3)
- **GRI 305**: Emissions (305-1, 305-2, 305-4)
- **GRI 306**: Waste (306-3, 306-4)
- Auto-generated Reasons for Omission
- "With Reference to GRI Standards" reporting option

### 9. **PDF Report Generator**
- 1-page ESG plan (cover page)
- Full GRI disclosures (302, 305, 306)
- Reasons for Omission section
- Evidence references (e.g., "based on uploaded utility bill")
- Company profile header
- Platform branding footer
- Instant download capability

### 10. **Monthly Check-In**
- Streamlined upload workflow ("what changed this month?")
- Simplified compared to initial onboarding
- New evidence uploads (receipts, photos, logs)
- Automated extraction → calculations → dashboard updates

### 11. **Response Library (Database)**
- User profiles with company information
- Timestamped records of all submissions
- Extracted data stored as structured JSON
- Month-on-month comparison capabilities
- Historical data preservation for SMEs

---

## Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Animation**: Framer Motion
- **Build Tool**: Vite
- **Routing**: React Router
- **Charting**: Interactive data visualization components

### Backend
- **Language**: Python 3.x
- **Framework**: FastAPI
- **Database**: Configurable (SQLite/PostgreSQL)
- **AI/LLM Integration**: Prompt-based extraction and interpretation
- **Data Validation**: Pydantic schemas

### Design System
- **Color Palette**: Sage, Moss, Sand, Forest, Charcoal, Cloud
- **Typography**: Display and Body font families
- **Components**: Reusable UI component library

---

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Git

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Backend runs on `http://localhost:8000`

For detailed setup instructions, see [Frontend README](frontend/README.md) and [Backend README](backend/README.md).

---

## Project Structure

```
techofusion-2026/
├── frontend/                          # React TypeScript application
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   ├── pages/                    # Page components
│   │   ├── lib/                      # Utilities and helpers
│   │   ├── stores/                   # State management
│   │   └── types/                    # TypeScript definitions
│   └── vite.config.ts
├── backend/                           # Python FastAPI application
│   ├── src/
│   │   ├── app.py                    # Main application
│   │   ├── dependencies/             # Dependency injection
│   │   ├── schemas/                  # Pydantic data models
│   │   └── gris/                     # GRI calculation engine
│   ├── storage/                       # Data storage
│   └── requirements.txt
└── README.md                          # This file
```

---

## Data Flow

1. **User Input** → Onboarding or Monthly Check-in
2. **AI Extraction** → Converts any format to structured JSON
3. **Calculations** → Applies GRI conversion formulas
4. **Dashboard** → Real-time metrics and KPIs
5. **AI Interpretation** → Generates insights and Quick Wins
6. **Report Generation** → PDF with GRI disclosures
7. **Database Storage** → Preserves history for future comparisons

---

## GRI Standards Coverage

The platform automates reporting for:
- **GRI 302 (Energy)**: Tracks electricity and fuel consumption
- **GRI 305 (Emissions)**: Calculates direct and indirect emissions
- **GRI 306 (Waste)**: Monitors waste generation and management
- **Reasons for Omission**: Auto-generated for missing data points

---

## Key Metrics

The system extracts and tracks:
- **Electricity consumption** (kWh)
- **Fuel usage** (liters)
- **Waste generation** (kg)
- **Headcount**
- **New hires**
- **Employee turnover**
- **Calculated intensity metrics**

---

## AI-Powered Features

### Data Extraction (Prompt 1)
Intelligently extracts 6-8 data points from free text, files, or images

### Interpretation (Prompt 2)
Generates contextual explanations and actionable Quick Wins

---

## Security & Compliance

- GRI Standards compliance built-in
- Evidence tracking for audit trails
- Secure data storage
- User authentication and authorization

---

## Usage Workflow

### First Time User
1. Sign up and complete onboarding form
2. Take materiality assessment
3. Upload first set of sustainability data
4. Platform generates ESG score, KPIs, and 1-page plan
5. Download PDF report

### Monthly Users
1. Log in and click "Monthly Check-in"
2. Upload new data (simplified form)
3. System updates all calculations and dashboard
4. Compare against previous months
5. Review Quick Wins and ESG plan updates

---

## Development

### Running Tests
```bash
# Frontend
cd frontend
npm run test

# Backend
cd backend
pytest
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build

# Backend
python main.py --prod
```

---

## Contributing

Contributions are welcome! Please:
1. Create a feature branch (`git checkout -b feature/AmazingFeature`)
2. Commit your changes (`git commit -m 'Add AmazingFeature'`)
3. Push to the branch (`git push origin feature/AmazingFeature`)
4. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Vision

Esverdant embrace sustainability reporting not as a compliance burden, but as a strategic opportunity. By automating GRI reporting and providing AI-driven insights, we help businesses track what matters, measure progress, and unlock cost savings while contributing to global sustainability goals.

---

## Support

For questions or issues, please:
- Check the [Frontend README](frontend/README.md) for UI-related questions
- Check the [Backend README](backend/README.md) for API-related questions
- Create an issue on the project repository

---

**Built with passion for sustainable business practices.**
