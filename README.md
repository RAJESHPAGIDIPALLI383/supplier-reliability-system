# YottaFlex.ai – Data Quality Monitoring System

A full-stack data quality monitoring platform designed to validate supplier data, monitor data pipelines, identify data quality issues, compare datasets against baselines, and generate actionable reports.

## 🚀 Live Application

- **Frontend Dashboard:** https://yottaflex-dashboard.vercel.app
- **Backend API:** https://yottaflex-api-7smz.onrender.com
- **API Documentation:** https://yottaflex-api-7smz.onrender.com/docs
- **Health Check:** https://yottaflex-api-7smz.onrender.com/health

## 📸 Application Screenshots

Screenshots of the YottaFlex.ai dashboard and its major features.

> Add your actual screenshots to the `screenshots/` directory and update these image paths to match their filenames.

### Dashboard
## 📸 Application Screenshots

### 1. Login Page
![Login Page](screenshots/login-page.png)

### 2. Dashboard Overview
![Dashboard Overview](screenshots/dashboard-overview.png)

### 3. CSV Upload
![CSV Upload](screenshots/csv-upload.png)

### 4. Run Pipeline
![Run Pipeline](screenshots/run-pipeline.png)

### 5. Pipeline Output
![Pipeline Output](screenshots/pipeline-output.png)

### 6. CSV Download
![CSV Download](screenshots/csv-download.png)

### 7. Baseline Comparison
![Baseline Comparison](screenshots/baseline-comparison.png)

### 8. Data Quality
![Data Quality](screenshots/data-quality.png)

### 9. Reports
![Reports](screenshots/reports.png)

### 10. Alerts
![Alerts](screenshots/alerts.png)

## ✨ Key Features

- CSV dataset upload and processing
- Data quality validation and monitoring
- Pipeline execution and monitoring
- Baseline comparison
- Data quality alerts
- Rejected records tracking
- Data quality analytics and charts
- Downloadable reports
- Secure admin authentication
- Supplier reliability monitoring

## 🛠️ Technology Stack

**Frontend**
- React.js
- Vite
- JavaScript
- HTML and CSS

**Backend**
- Python
- FastAPI
- REST APIs
- JWT Authentication

**Database**
- SQLite

**Deployment**
- Vercel – Frontend hosting
- Render – Backend hosting
- GitHub – Source code management

## 📁 Project Structure

```text
supplier-reliability-system/
│
├── backend/
│   ├── auth/
│   └── upload_routes.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── src/
├── data/
├── database/
├── docs/
├── reports/
├── screenshots/
├── tests/
│
├── api.py
├── app.py
├── requirements.txt
├── render.yaml
├── README.md
└── .gitignore
```

## ⚙️ Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/RAJESHPAGIDIPALLI383/supplier-reliability-system.git
cd supplier-reliability-system
```

### 2. Backend setup

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables in a local `.env` file.

### 3. Start the backend

```bash
uvicorn api:app --reload
```

Backend: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

### 4. Frontend setup

```bash
cd frontend
npm install
```

Configure the frontend API URL using `VITE_API_BASE_URL` in the frontend environment configuration.

```bash
npm run dev
```

## 🔐 Environment Variables

Configure these variables in your deployment environment. Never commit actual secret values.

**Backend**
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `JWT_SECRET_KEY`
- `FRONTEND_URL`

**Frontend**
- `VITE_API_BASE_URL`

## ☁️ Deployment

- Frontend deployed using Vercel.
- Backend deployed using Render.
- Source code maintained in GitHub.
- Backend health endpoint available for service monitoring.

## 👨‍💻 Author

**Rajesh Pagidipalli**

GitHub: https://github.com/RAJESHPAGIDIPALLI383

LinkedIn: https://www.linkedin.com/in/rajesh-pagidipalli-926774245

---

⭐ If you find this project useful, consider giving it a star on GitHub.