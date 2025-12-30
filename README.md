# MediaCore

MediaCore is a comprehensive media management system designed to centralize movie and TV show data. It consists of a modern web frontend, a robust Python backend, and a specialized data ingestion engine.

## 🏗️ Architecture

The project is divided into three main components:

- **Frontend**: A modern React-based user interface (built with Vite) for browsing and managing the media library.
- **Backend**: A Python API server (FastAPI) responsible for serving data to the frontend and handling business logic.
- **API Central**: A dedicated data aggregation service that imports and normalizes data from external sources like IMDb and TMDB.

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (v3.10+ recommended)
- **Docker** (Optional, for containerized deployment)

### 📦 Installation

#### 1. Clone the repository

```bash
git clone https://github.com/JoKerIsCraZy/MediaCore.git
cd MediaCore
```

#### 2. Backend Setup

```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
```

#### 4. API Central Imports

The `api-central` component handles large dataset imports.

```bash
cd api-central
# Ensure you have your IMDb datasets in the imdb_data/ directory
python main.py  # (Or specific script name)
```

## 🛠️ Usage

### Running Locally

**Start the Backend:**

```bash
cd backend
python main.py
```

**Start the Frontend:**

```bash
cd frontend
npm run dev
```

The application will typically be accessible at `http://localhost:5173`.

## 🔒 Configuration

Environment variables are managed via `.env` files.

- Copy `.env.example` to `.env` in the root (or respective subdirectories) and configure your API keys (TMDB, etc.) and database paths.

## 📄 License

[MIT](LICENSE)
