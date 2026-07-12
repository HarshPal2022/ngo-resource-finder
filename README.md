# NGOConnect AI

An AI-powered NGO discovery and recommendation platform that helps users find NGOs across Maharashtra based on keywords, district, and social causes.

The project automatically scrapes NGO data, cleans it, stores it in a cloud MySQL-compatible database (TiDB Cloud), and provides a REST API with an AI recommendation engine built using TF-IDF and Cosine Similarity.

---

## Live Demo

https://ngoconnect-ai.onrender.com

---

## Features

- Scrapes NGO information from NGOs India
- Cleans and standardizes raw data
- Stores data in TiDB Cloud (MySQL compatible)
- Search NGOs by:
  - Keyword
  - District
- AI-powered NGO recommendations using Natural Language Processing
- Pagination for search results
- Category filtering
- Responsive Tailwind CSS frontend
- REST API
- Cloud deployment on Render

---

## Tech Stack

### Backend

- Python
- Flask
- REST API

### Frontend

- HTML
- Tailwind CSS
- JavaScript

### Database

- TiDB Cloud (MySQL)

### Data Engineering

- BeautifulSoup
- Requests
- Pandas

### AI / Machine Learning

- Scikit-learn
- TF-IDF Vectorizer
- Cosine Similarity

### Deployment

- Render
- GitHub

---

## Project Structure

```
ngo-resource-finder/

│
├── app.py
├── requirements.txt
├── config.py
│
├── scraper/
│   ├── scrape_listing.py
│   ├── scrape_profiles.py
│   └── clean_data.py
│
├── database/
│   ├── db.py
│   ├── db_config.py
│   └── schema.sql
│
├── recommender/
│   └── recommender.py
│
├── routes/
│   └── ngo_routes.py
│
├── templates/
│
├── static/
│
├── ssl/
│
└── data/
```

---

## Dataset

Current database contains

**1685 NGOs**

Collected from

https://ngosindia.org

Fields include

- Name
- District
- Address
- Phone
- Mobile
- Email
- Website
- Contact Person
- Purpose
- Mission
- Source URL

---

## AI Recommendation Engine

The recommendation engine converts NGO Purpose and Mission into TF-IDF vectors.

User Query

↓

TF-IDF Vectorizer

↓

Cosine Similarity

↓

Top Matching NGOs

Example

Input

```
I need education support for girls
```

Returns NGOs whose objectives are closest to the user's query.

---

## API Endpoints

### Get NGOs

```
GET /api/ngos
```

---

### Search NGOs

```
GET /api/search
```

Parameters

```
keyword
district
page
```

---

### Get Districts

```
GET /api/districts
```

---

### AI Recommendation

```
POST /api/recommend
```

Body

```json
{
    "query":"I need education support for women"
}
```

---

## Installation

Clone repository

```bash
git clone https://github.com/HarshPal2022/ngo-resource-finder.git
```

Create virtual environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Configure

```
.env
```

Run

```bash
python app.py
```

---

## Deployment

Frontend + Backend

- Render

Database

- TiDB Cloud

---

## Future Improvements

- Multi-district search
- Explain why an NGO was recommended
- Automated weekly data refresh using GitHub Actions
- NGO analytics dashboard
- Advanced filtering
- User bookmarks

---

## Author

Harsh Pal

GitHub

https://github.com/HarshPal2022
