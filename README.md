# Student Research Tracking System (SRT)

This is a web-based application developed using Flask and PostgreSQL to track student research progress at the School of Public Health. It supports student registration, supervisor assignment, milestone tracking, and reporting features.

## 🚀 Features

- 📋 Register students and supervisors
- 🧠 Assign research topics and supervisors
- 📅 Track research milestones
- 📊 View analytics on student progress and completion rates
- 📌 Group students by year of intake

## 💻 Tech Stack

- **Backend**: Flask (Python), SQLAlchemy, Alembic
- **Database**: PostgreSQL
- **Frontend**: HTML5, Bootstrap
- **Tools**: Flask-Migrate, Git, GitHub

## 🛠️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/angellanabasirye/masksph_srt.git
cd masksph_srt


Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate  # for Windows

Install dependencies
pip install -r requirements.txt

Configure environment
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://localhost:5432/masksph.db


Initialize the database
flask db upgrade

Run the application
flask run or python run.py

Project Structure
masksph_srt/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── templates/
├── migrations/
├── static/
├── run.py
└── README.md


👩🏽‍💻 Author
Angella Nabasirye
https://github.com/angellanabasirye
Ministry of Health – Uganda | Makerere University School of Public Health

