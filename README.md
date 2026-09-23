# 🎓 UniVault: College Notes & University Exam Material Sharing Portal

A modern, full-stack web application designed for college and university students to share, discover, preview, and download study notes, solved previous year question papers (PYQs), formula cheat sheets, lab manuals, and syllabus blueprints.

Built with a **Python Flask backend** and modern **Tailwind CSS + Lucide Icons** UI, pre-configured for **instant local running** and **1-click zero-configuration deployment to Vercel Serverless**.

---

## ✨ Features

- 🔍 **Instant Live Search & Multi-Facet Filtering**: Filter materials across University (Stanford, MIT, IIT Bombay, Anna Univ, etc.), Department/Branch (CSE, ECE, Mech, Civil, AI/Data Science), Semester (1 to 8), and Material Type.
- ⚡ **Trending Topic Chips**: One-click quick search for Data Structures, Operating Systems, DBMS Normalization, Machine Learning, and Engineering Math.
- 📖 **In-App Document Preview Modal**: Interactive reader view to inspect lecture notes, formulas, and syllabus modules without leaving the page.
- 📥 **Direct Downloads & Tracking**: Real-time download counter and secure file delivery.
- ❤️ **Community Upvotes & Feedback**: Instant upvote animation and student review submission with interactive 5-star ratings.
- 🧰 **"My Exam Study Kit" (Bookmark Drawer)**: Assemble a personal exam revision playlist saved in local storage with one-click access.
- 📤 **Contribution Portal**: Upload notes with drag-and-drop file upload (PDF, DOCX, PPTX) or external cloud storage links (Google Drive, OneDrive, GitHub).
- 🏆 **Contributor Leaderboard**: Hall of Fame celebrating top students and notes contributors with reputation points and badges.
- 🌓 **Dark / Light Mode**: Beautiful glassmorphic modern UI with smooth transitions and persistent theme storage.
- ☁️ **Vercel Serverless Ready**: Automated environment detection with `/tmp` database persistence, pre-seeded sample data, and serverless WSGI routing.

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites
- Python 3.9+ (Installed)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## ⚡ Deployment to Vercel

UniVault comes with full Vercel Serverless configuration (`vercel.json`, `api/index.py`, `.vercelignore`).

### Option A: Deploy via GitHub (Recommended)
1. Push this repository to your GitHub account:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - UniVault Notes Portal"
   git remote add origin https://github.com/your-username/univault-portal.git
   git push -u origin main
   ```
2. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**.
3. Import your GitHub repository.
4. Keep the default settings (Framework Preset: **Other**) and click **"Deploy"**.
5. Vercel will automatically build the Python serverless function and static assets. Your portal will be live in seconds!

### Option B: Deploy via Vercel CLI
If you have Vercel CLI installed:
```bash
vercel
```
To deploy directly to production:
```bash
vercel --prod
```

---

## 📂 Project Architecture

```
├── api/
│   └── index.py            # Vercel Serverless WSGI entrypoint (@vercel/python)
├── static/
│   ├── css/
│   │   └── custom.css      # Glassmorphism, animations, theme styling
│   ├── js/
│   │   └── app.js          # Reactive client controller (search, modals, kit, reviews)
│   └── uploads/            # Uploaded files folder
├── templates/
│   └── index.html          # Responsive single-page application UI with Tailwind CSS
├── app.py                  # Core Flask application & REST API routes
├── database.py             # SQLite manager with auto-init, seeding & Vercel fallback
├── seed_data.py            # Pre-seeded realistic university notes, PYQs, and reviews
├── test_app.py             # Automated test suite (13 unit & integration tests)
├── vercel.json             # Vercel deployment build & route mapping
├── .vercelignore           # Deployment ignore rules
├── requirements.txt        # Minimal production dependencies (Flask, Werkzeug)
└── README.md               # Documentation
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status & environment check |
| `GET` | `/api/materials` | List materials with `search`, `branch`, `semester`, `university`, `material_type`, `sort_by`, `page`, `per_page` |
| `GET` | `/api/materials/<id>` | Full detail for a material, including reviews and preview content |
| `POST` | `/api/materials` | Upload / publish a new note or exam material |
| `POST` | `/api/materials/<id>/upvote` | Upvote a material |
| `POST` | `/api/materials/<id>/download` | Track download and retrieve target link |
| `POST` | `/api/materials/<id>/reviews` | Submit a review (`author_name`, `rating`, `comment`) |
| `GET` | `/api/stats` | Aggregated platform metrics |
| `GET` | `/api/leaderboard` | Top student contributors & hall of fame |
| `GET` | `/api/filter-options` | Dropdown values for universities, branches, and semesters |

---

## 🧪 Testing

Run the automated test suite to verify all endpoints and database transactions:
```bash
python test_app.py
```
Expected output:
```
Ran 13 tests in 0.15s
OK
```

---

## 📜 License
MIT License. Free to use, adapt, and deploy for your college or university community.
