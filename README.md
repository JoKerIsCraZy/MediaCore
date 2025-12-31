# MediaCore

MediaCore is a self-hosted media list management system that lets you create dynamic, filter-based lists of movies and TV shows. It combines data from TMDB and IMDb to provide comprehensive filtering capabilities and exports lists in formats compatible with Radarr and Sonarr.

## Features

- **Dynamic Lists**: Create lists based on filters that auto-update
- **Advanced Filtering**: Filter by rating, genre, year, streaming service, language, and more
- **Dual Rating System**: Use both TMDB and IMDb ratings for filtering
- **Radarr/Sonarr Export**: Export lists as JSON for easy import
- **Modern UI**: Clean, responsive React frontend
- **Self-Hosted**: Full control over your data

## Architecture

```
MediaCore/
├── frontend/          # React + Vite UI
├── backend/           # FastAPI server
├── api-central/       # Data import services
└── .env               # Configuration
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React, Vite, TanStack Query | User interface |
| Backend | FastAPI, SQLAlchemy, SQLite | API server, list management |
| API Central | Python, aiohttp, asyncio | TMDB/IMDb data import |

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- TMDB API Key ([get one here](https://www.themoviedb.org/settings/api))

### Option 1: Automated Setup (Recommended)

Run the interactive setup wizard:

```bash
git clone https://github.com/JoKerIsCraZy/MediaCore.git
cd MediaCore
python setup.py
```

The setup wizard will:
- Check prerequisites (Python, Node.js)
- Configure your TMDB API key
- Install all dependencies (backend + frontend)
- Build the frontend
- Optionally import TMDB/IMDb data
- Start the application

### Option 2: Manual Setup

#### 1. Clone & Configure

```bash
git clone https://github.com/JoKerIsCraZy/MediaCore.git
cd MediaCore

# Create .env file in project root
cp .env.example .env
# Edit .env and add your TMDB_API_KEY
```

**.env file:**
```env
TMDB_API_KEY=your_tmdb_api_key_here
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

#### 4. Import IMDb Data (Optional)

For IMDb rating filters to work, you need to import IMDb data:

```bash
cd api-central
pip install -r requirements.txt

# Import IMDb ratings data
python imdb_importer.py
```

Note: This downloads ~500MB of data from IMDb datasets. IMDb filters only work for movies.

#### 5. Run the Application

**Backend (Terminal 1):**
```bash
cd backend
python main.py
```
Server runs at `http://localhost:8000`

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```
UI available at `http://localhost:5173`

**Production Build:**
```bash
cd frontend
npm run build
# Files are output to frontend/dist/
# Copy to backend/static/ to serve from backend
```

## Usage Guide

### Discover Page

Browse trending, popular, and top-rated movies/TV shows. Search for specific titles and add them to your lists.

### Creating Lists

1. Go to **My Lists** > **New List**
2. Enter a name and description
3. Select **Movies** or **TV Shows**
4. Configure filters (see below)
5. Click **Preview** to see matching results
6. Click **Create List** to save

### Available Filters

#### Ratings & Votes
| Filter | Movies | TV Shows | Description |
|--------|--------|----------|-------------|
| TMDB Rating | Yes | Yes | Range 0-10 |
| Minimum Votes | Yes | Yes | Minimum vote count |
| IMDb Rating | Yes | No | Range 0-10 (requires data import) |
| IMDb Votes | Yes | No | Minimum IMDb votes |

#### Release & Dates
| Filter | Movies | TV Shows | Description |
|--------|--------|----------|-------------|
| Year | Yes | Yes | Specific year |
| Release Date Range | Yes | Yes | After/Before dates |
| Release Type | Yes | No | Theatrical, Digital, etc. |
| Show Status | No | Yes | Returning, Ended, Cancelled, etc. |

#### Content
| Filter | Description |
|--------|-------------|
| Include Genres | Only show these genres |
| Exclude Genres | Hide these genres |
| Original Language | Filter by language |
| Origin Country | Filter by country |
| Runtime | Duration in minutes |
| Certification | Age rating (US ratings) |

#### Streaming
| Filter | Description |
|--------|-------------|
| Watch Providers | Netflix, Disney+, Prime Video, etc. |
| Watch Region | Countries to check availability |
| Availability Type | Flatrate, Rent, Buy, Free |

#### Advanced
| Filter | Description |
|--------|-------------|
| Cast | TMDB Person ID |
| Crew | TMDB Person ID |
| Production Company | TMDB Company ID |
| Keywords | TMDB Keyword ID |

### Sorting Options

- Popularity (High/Low)
- TMDB Rating (High/Low)
- IMDb Rating (High/Low)
- Release Date (Newest/Oldest)
- Vote Count (High/Low)

### Exporting Lists

Lists can be exported for use with Radarr/Sonarr:

1. Open a list
2. Click **Export**
3. Choose format:
   - **Radarr JSON**: For movies
   - **Sonarr JSON**: For TV shows
   - **IMDB IDs**: Plain text list

## API Central - IMDb Data Import

The `api-central` component handles importing IMDb rating data for enhanced filtering capabilities. TMDB data is fetched live by the backend API.

### IMDb Importer

Import IMDb ratings from official IMDb datasets. This enables IMDb Rating and IMDb Votes filters for movies.

```bash
cd api-central
python imdb_importer.py
```

The importer will automatically:
1. Download datasets from [IMDb Datasets](https://datasets.imdbws.com/):
   - `title.ratings.tsv.gz` (~25MB)
   - `title.basics.tsv.gz` (~500MB)
2. Extract and import data into SQLite database
3. Create indexes for fast lookups

**Note:** IMDb data only works for movies. TV show ratings are provided by TMDB.

### Database

Data is stored in SQLite databases:

| Database | Location | Content |
|----------|----------|---------|
| IMDb DB | `api-central/media_database.db` | IMDb ratings and title data |
| App DB | `backend/data/mediacore.db` | Lists, list items, settings |

TMDB data (movies, TV shows, genres, providers) is fetched live from the TMDB API.

## API Endpoints

### Lists
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/lists` | Get all lists |
| POST | `/api/lists` | Create new list |
| GET | `/api/lists/{id}` | Get list details |
| PUT | `/api/lists/{id}` | Update list |
| DELETE | `/api/lists/{id}` | Delete list |
| POST | `/api/lists/{id}/refresh` | Refresh list items |
| GET | `/api/lists/{id}/export` | Export list |
| POST | `/api/lists/preview` | Preview filter results |

### Discover
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/discover/trending/{type}` | Trending movies/TV |
| GET | `/api/discover/popular/{type}` | Popular movies/TV |
| GET | `/api/discover/top-rated/{type}` | Top rated movies/TV |
| POST | `/api/discover` | Filter-based discovery |

### Media
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/media/{type}/{id}` | Get media details |
| GET | `/api/media/search` | Search movies/TV |
| GET | `/api/genres/{type}` | Get genre list |
| GET | `/api/providers/{type}` | Get streaming providers |

## Configuration

All configuration is done via the `.env` file in the project root:

```env
# Required
TMDB_API_KEY=your_api_key

# Optional - Database paths (defaults work fine)
DATABASE_URL=sqlite+aiosqlite:///./backend/data/mediacore.db
MEDIA_DATABASE_URL=sqlite+aiosqlite:///./api-central/media_database.db

# Optional - Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Optional - List update interval (hours)
UPDATE_INTERVAL=6
```

## Development

### Frontend Development

```bash
cd frontend
npm run dev      # Development server with HMR
npm run build    # Production build
npm run preview  # Preview production build
```

### Backend Development

```bash
cd backend
python main.py   # Runs with auto-reload in debug mode
```

### Project Structure

```
frontend/src/
├── components/
│   ├── FilterBuilder.jsx   # Filter configuration UI
│   ├── MediaCard.jsx       # Movie/TV card component
│   ├── MediaGrid.jsx       # Grid layout for media
│   └── Sidebar.jsx         # Navigation sidebar
├── pages/
│   ├── Dashboard.jsx       # Home dashboard
│   ├── Discover.jsx        # Browse & search
│   ├── Lists.jsx           # List management
│   ├── ListBuilder.jsx     # Create/edit lists
│   ├── ListDetail.jsx      # View list contents
│   └── Settings.jsx        # App settings
├── api.js                  # API client
└── App.jsx                 # Main app component

backend/
├── routers/
│   ├── lists.py            # List CRUD endpoints
│   ├── discover.py         # Discovery endpoints
│   └── media.py            # Media endpoints
├── services/
│   ├── filter_engine.py    # Filter processing
│   ├── local_discover.py   # Local DB queries
│   ├── tmdb.py             # TMDB API client
│   └── scheduler.py        # Background updates
├── models.py               # Database models
├── schemas.py              # Pydantic schemas
├── database.py             # DB connection
└── main.py                 # FastAPI app

api-central/
├── imdb_importer.py        # IMDb data import
├── models.py               # IMDb database models
├── database.py             # DB connection
└── config.py               # Configuration
```

## Troubleshooting

### IMDb filters not working
- Make sure you've run `imdb_importer.py` to import IMDb data
- IMDb filters only work for movies (TV show data not available)

### "No results" when filtering
- Check if your filter combination is too restrictive
- Try removing filters one by one to identify the issue
- Use the Preview button to test filters before saving

### Rate limiting errors
- TMDB allows ~40 requests per 10 seconds
- The backend handles rate limiting automatically
- If you see rate limit errors, wait a moment and retry

### Database errors
- Delete the `.db` files and re-run imports
- Check file permissions on the data directories

## License

[MIT](LICENSE)

## Credits

- [TMDB](https://www.themoviedb.org/) - Movie and TV data
- [IMDb](https://www.imdb.com/) - Ratings data
- Built with FastAPI, React, and Vite
