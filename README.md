# GreenTamilNadu - AI Pollution Analysis & Tree Plantation System

A modern **full-stack React + Flask application** for analyzing air pollution, recommending trees for plantation, and forecasting AQI trends across Tamil Nadu cities.

## 🎯 Core Features

1. **7-Day AQI Forecasting** - ML-powered predictions using Holt-Winters
2. **Satellite Image Analysis** - AI segmentation to identify plantation areas
3. **Smart Tree Recommendations** - ML-based species selection by AQI level
4. **AQI Trend Visualization** - 7-day trend charts with real-time data
5. **Model Evaluation** - Performance metrics and accuracy dashboards

## ✨ Recent Architecture Updates

**Frontend Modernization (React + Tailwind CSS)**
- Migrated from Flask Jinja2 templates to React SPA
- Modern responsive UI with Tailwind CSS
- Client-side routing with React Router v6
- Vite dev server with hot module reload (HMR)

**Backend Optimization**
- Single-model AQI forecasting (Holt-Winters) - fast & accurate
- Extended history to 100 days for better training
- Centralized API client service for consistent communication
- CORS-enabled for cross-origin requests

---

## 🧠 ML Features

1. **Explainable Tree Recommendations**
- Top factors per tree: AQI fit, pollution tolerance, water need fit, canopy score
- Returns model confidence score and estimated PM2.5 impact

2. **Model Evaluation Dashboard**
- Route: `/model-evaluation`
- API: `/api/model/evaluation`
- Shows accuracy, precision, recall, confusion matrix, sample count

3. **City-Profile-Aware Recommendations (Phase 2 Inputs)**
- Added city profile features: temperature, humidity, rainfall, urban density
- Dataset file: `Data/city_profile_dataset.csv`

4. **Impact Prediction Model Output**
- Returns impact score and estimated PM2.5 reduction per 100 trees

5. **Feedback Loop Endpoint**
- API: `POST /api/web/feedback`
- Stores shown vs selected tree IDs for future retraining

6. **Scenario Simulation Endpoint**
- API: `POST /api/web/area/<area_id>/scenario`
- Estimates species mix and tree count to move from current AQI to target AQI

---

## 📋 System Overview

```
┌─────────────────────────────────────┐
│      Frontend (React)                │
│      Port 5173                       │
│  ┌──────────────────────────────┐   │
│  │ • Home Dashboard             │   │
│  │ • Area Analysis              │   │
│  │ • AQI & Trees                │   │
│  │ • About                      │   │
│  └──────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
         HTTP Requests
         (REST API)
               │
┌──────────────▼──────────────────────┐
│      Backend (Flask)                 │
│      Port 5000                       │
│  ┌──────────────────────────────┐   │
│  │ • REST API Endpoints         │   │
│  │ • Static AQI Data            │   │
│  │ • Tree Recommendations       │   │
│  │ • Image Analysis Data        │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🚀 Quick Start (3 Commands)

### Terminal 1 - Backend
```powershell
cd backend
python api.py
```

### Terminal 2 - Frontend
```powershell
cd frontend/project
npm run dev
```

### Browser
Open: **http://localhost:5173**

Done! 🎉

---

## 📦 What You Need

### Downloads
- **Python 3.8+** → https://www.python.org/
- **Node.js 18+** → https://nodejs.org/

### One-Time Setup
```powershell
# Backend
cd backend
pip install -r ../requirements.txt

# Frontend
cd frontend/project
npm install
```

---

## 📖 Documentation

| Guide | Purpose |
|-------|---------|
| **[QUICKSTART.md](QUICKSTART.md)** | 3-minute quick overview (READ THIS FIRST) |
| **[CHECKLIST.md](CHECKLIST.md)** | Step-by-step checklist to verify setup |
| **[SETUP_AND_RUN.md](SETUP_AND_RUN.md)** | Detailed setup guide with troubleshooting |
| **[API_INTEGRATION.md](API_INTEGRATION.md)** | How frontend connects to backend |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System diagrams and data flow |
| **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** | Complete system overview |
| **[SYSTEM_UPDATE.md](SYSTEM_UPDATE.md)** | Static AQI data details |

---

## 🏗️ Project Structure

```
ai-pollution-analyses/
├── backend/
│   ├── api.py                    ✨ Flask REST API (NEW)
│   ├── main.py                   CLI tool for batch processing
│   ├── scripts/
│   │   ├── aqi.py               Static AQI data for 5 areas
│   │   ├── segment.py           Image segmentation
│   │   └── ...
│   ├── Data/                     Input satellite images
│   └── Output/                   Analysis results
│
├── frontend/
│   └── project/
│       ├── src/
│       │   ├── services/
│       │   │   └── api.ts       ✨ API service layer (NEW)
│       │   ├── components/      React components
│       │   ├── pages/           Page components
│       │   ├── utils/
│       │   │   └── mockData.ts  Static data
│       │   └── types.ts         TypeScript definitions
│       ├── vite.config.ts       Vite config with API proxy
│       └── package.json         Dependencies
│
├── QUICKSTART.md               ← Start here!
├── SETUP_AND_RUN.md            Full setup guide
├── CHECKLIST.md                Verification checklist
├── API_INTEGRATION.md          API details
├── ARCHITECTURE.md             Diagrams & data flow
├── FINAL_SUMMARY.md            Complete overview
├── SYSTEM_UPDATE.md            AQI data info
├── requirements.txt            Python dependencies
└── README.md                   This file
```

---

## 🔗 API Endpoints

All endpoints served from: `http://localhost:5000/api/`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check if backend is running |
| `/areas` | GET | Get list of all 5 areas |
| `/area/{id}/aqi` | GET | Get current AQI Index for an area |
| `/area/{id}/aqi-trend` | GET | Get 7-day AQI Index trend |
| `/area/{id}/analysis` | GET | Get segmentation analysis data |
| `/area/{id}/tree-recommendations` | GET | Get recommended trees |
| `/dashboard` | GET | Get all dashboard data |

**Area IDs:** `periyar`, `anna-nagar`, `thiruparankundram`, `mattuthavani`, `kk-nagar`

---

## 📊 Available Areas & Data

| Area | AQI Index | Status | Land % | Est. Trees |
|------|-----|--------|--------|------------|
| **Periyar** | 132 | Poor | 18.5% | 625 |
| **Anna Nagar** | 96 | Moderate | 24.2% | 945 |
| **Thiruparankundram** | 78 | Moderate | 32.8% | 1420 |
| **Mattuthavani** | 110 | Moderate | 15.7% | 510 |
| **KK Nagar** | 88 | Moderate | 21.3% | 835 |

---

## 🌳 Tree Recommendations by AQI Index

| AQI Index Range | Status | Recommended Trees |
|-----------|--------|-------------------|
| 0-50 | Good | Ficus religiosa, Mango, Pongamia, Neem |
| 51-100 | Moderate | Neem, Pongamia, Terminalia, Cassia |
| 101-150 | Poor | Neem, Peepal, Pongamia, Banyan |
| 151-200 | Very Poor | Neem, Pongamia, Palash |
| 201+ | Severe | Neem, Pongamia, Palash |

---

## 🎨 Frontend Features

### Pages
- **Home** - Dashboard with AQI Index and tree recommendations
- **Area Analysis** - Select area and view segmentation results
- **AQI Index & Trees** - Detailed AQI Index trends and tree suggestions
- **About** - Project information

### Components
- Responsive design (works on desktop, tablet, mobile)
- Real-time AQI Index updates
- Interactive area selection
- Beautiful charts and visualizations
- Professional UI with Tailwind CSS

---

## ⚙️ Backend Features

- REST API with Flask
- CORS enabled for frontend communication
- Static AQI Index data (no external API calls)
- Multiple endpoints for different data types
- Auto-reload on code changes (debug mode)
- Clean, organized code structure

---

## 🔧 How to Use

### Starting the System

```powershell
# Terminal 1 - Backend
cd backend
python api.py

# Terminal 2 - Frontend (new terminal)
cd frontend/project
npm run dev

# Browser
http://localhost:5173
```

### Making API Calls from Frontend

```typescript
import { getAQIData, getTreeRecommendations } from '../services/api';

// Get AQI Index for an area
const aqi = await getAQIData('periyar');
console.log(aqi.value);   // 132
console.log(aqi.status);  // "Poor"

// Get tree recommendations
const recommendations = await getTreeRecommendations('periyar');
recommendations.trees.forEach(tree => {
  console.log(`${tree.name}: ${tree.pollutionAbsorption}`);
});
```

### Testing via Command Line

```bash
# Test health
curl http://localhost:5000/api/health

# Test areas
curl http://localhost:5000/api/areas

# Test area-specific data
curl http://localhost:5000/api/area/periyar/aqi
curl http://localhost:5000/api/area/anna-nagar/tree-recommendations
```

---

## 📱 Browser DevTools

### See API Calls in Action

1. Open DevTools: Press `F12`
2. Go to **Network** tab
3. Navigate to **Area Analysis**
4. Click **Analyze Area**
5. Watch the API call being made to backend!

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | Make sure Python is installed: `python --version` |
| Frontend won't start | Make sure Node.js is installed: `node --version` |
| "Connection refused" | Both backend and frontend must be running |
| "Port already in use" | Kill the process or use different port |
| CORS errors | Make sure backend is running on port 5000 |
| "Cannot GET /api" | Backend not running - start with `python api.py` |

See **[SETUP_AND_RUN.md](SETUP_AND_RUN.md)** for detailed troubleshooting.

---

## 📚 What Each File Does

| File | Purpose |
|------|---------|
| `backend/api.py` | Flask REST API server |
| `backend/scripts/aqi.py` | Static AQI data lookup |
| `backend/main.py` | CLI tool for batch processing |
| `frontend/src/services/api.ts` | API service layer for React |
| `frontend/src/pages/*.tsx` | React page components |
| `frontend/src/components/*.tsx` | Reusable React components |
| `frontend/vite.config.ts` | Build and dev server config |
| `requirements.txt` | Python package dependencies |
| `frontend/project/package.json` | Node.js dependencies |

---

## 🎯 Key Features

✅ **Real-time Data** - Frontend pulls live data from backend  
✅ **REST API** - Clean, standard API design  
✅ **Static Data** - No external API dependencies  
✅ **Hot Reload** - Changes auto-reload in dev mode  
✅ **CORS Enabled** - Frontend can safely call backend  
✅ **Responsive Design** - Works on all screen sizes  
✅ **Beautiful UI** - Modern design with Tailwind CSS  
✅ **Fully Documented** - 7 comprehensive guides included  

---

## 🚀 Production Deployment

When ready to deploy:

### Backend
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.api:app
```

### Frontend
```bash
cd frontend/project
npm run build
# Upload dist/ folder to Netlify/Vercel
```

---

## 📖 Reading Order

Start with these in order:

1. **[QUICKSTART.md](QUICKSTART.md)** - 3-minute overview
2. **[CHECKLIST.md](CHECKLIST.md)** - Verify your setup
3. **[SETUP_AND_RUN.md](SETUP_AND_RUN.md)** - Detailed guide
4. **[ARCHITECTURE.md](ARCHITECTURE.md)** - How it works
5. **[API_INTEGRATION.md](API_INTEGRATION.md)** - API details
6. **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete reference

---

## 🤝 Contributing

To modify the system:

1. **Backend Changes** - Edit `backend/api.py` or `backend/scripts/aqi.py`
2. **Frontend Changes** - Edit files in `frontend/project/src/`
3. Both auto-reload - just refresh browser!

---

## 💡 Architecture Highlights

- **Separation of Concerns** - Frontend and backend are independent
- **API-First Design** - All data flows through REST API
- **Stateless Backend** - Can restart anytime without losing state
- **Scalable Frontend** - Can add components without changing backend
- **Easy Testing** - Can test API endpoints independently

---

## 📊 Data Flow

```
User Interface (Browser)
    ↓
React Components
    ↓
API Service Layer (services/api.ts)
    ↓
HTTP Requests to Backend
    ↓
Flask API (api.py)
    ↓
Static Data Lookup (scripts/aqi.py)
    ↓
JSON Response
    ↓
Frontend Updates UI
    ↓
User Sees Data
```

---

## ✅ Status

| Component | Status |
|-----------|--------|
| Backend API | ✅ Ready |
| Frontend App | ✅ Ready |
| Documentation | ✅ Complete |
| API Integration | ✅ Connected |
| Static Data | ✅ Configured |
| Deployment Ready | ✅ Yes |

---

## 📞 Support

If you encounter issues:

1. Check **[SETUP_AND_RUN.md](SETUP_AND_RUN.md)** troubleshooting section
2. Review **[CHECKLIST.md](CHECKLIST.md)** to verify setup
3. Look at terminal error messages carefully
4. Try restarting both backend and frontend

---

## 🎓 Learning Resources

- **React** - https://react.dev/
- **Flask** - https://flask.palletsprojects.com/
- **TypeScript** - https://www.typescriptlang.org/
- **Vite** - https://vitejs.dev/
- **Tailwind CSS** - https://tailwindcss.com/

---

## 📄 License

This project is for educational and research purposes.

---

## 🎉 You're Ready!

Everything is set up and ready to go. Follow these steps:

1. Read **[QUICKSTART.md](QUICKSTART.md)** (3 minutes)
2. Run the 2 commands (backend + frontend)
3. Open http://localhost:5173
4. Explore the application!

**Happy coding! 🚀**

---

**Last Updated:** February 1, 2026  
**Status:** ✅ Fully Functional
