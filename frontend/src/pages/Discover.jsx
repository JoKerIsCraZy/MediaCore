import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { mediaApi } from '../api'
import { Search, TrendingUp, Star, Clock, Film, Tv } from 'lucide-react'
import MediaGrid from '../components/MediaGrid'

const CATEGORIES = [
  { id: 'trending', label: 'Trending', icon: TrendingUp },
  { id: 'popular', label: 'Popular', icon: Star },
  { id: 'top_rated', label: 'Top Rated', icon: Star },
  { id: 'upcoming', label: 'Upcoming', icon: Clock },
  { id: 'now_playing', label: 'Now Playing', icon: Film },
]

export default function Discover() {
  const [mediaType, setMediaType] = useState('movie')
  const [category, setCategory] = useState('trending')
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [imdbRating, setImdbRating] = useState(0)
  
  // Fetch category data
  const { data: categoryData, isLoading: categoryLoading } = useQuery({
    queryKey: ['discover', category, mediaType],
    queryFn: () => {
      switch (category) {
        case 'trending':
          return mediaApi.trending(mediaType)
        case 'popular':
          return mediaApi.popular(mediaType)
        case 'top_rated':
          return mediaApi.topRated(mediaType)
        case 'upcoming':
          return mediaType === 'movie' ? mediaApi.upcoming() : mediaApi.airingToday()
        case 'now_playing':
          return mediaType === 'movie' ? mediaApi.nowPlaying() : mediaApi.airingToday()
        default:
          return mediaApi.popular(mediaType)
      }
    },
    enabled: !isSearching,
  })
  
  // Search data
  const { data: searchData, isLoading: searchLoading } = useQuery({
    queryKey: ['search', searchQuery, mediaType],
    queryFn: () => mediaApi.search(searchQuery, mediaType),
    enabled: isSearching && searchQuery.length > 0,
  })

  // Discover data (IMDb filter)
  const { data: discoverData, isLoading: discoverLoading } = useQuery({
    queryKey: ['discover_filter', imdbRating, mediaType],
    queryFn: () => mediaApi.discover(1, [{ field: 'imdb_rating', operator: 'gte', value: imdbRating }], 'popularity.desc'),
    enabled: imdbRating > 0 && !isSearching,
  })
  
  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      setIsSearching(true)
    }
  }
  
  const clearSearch = () => {
    setSearchQuery('')
    setIsSearching(false)
  }
  
  const isFiltering = imdbRating > 0
  const displayData = isSearching ? searchData : (isFiltering ? discoverData : categoryData)
  const isLoading = isSearching ? searchLoading : (isFiltering ? discoverLoading : categoryLoading)
  
  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '2rem' }}>
        <h1>Discover</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
          Find movies and TV shows to add to your lists
        </p>
      </div>
      
      {/* Search */}
      <form onSubmit={handleSearch} style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={18} style={{ 
              position: 'absolute', 
              left: '1rem', 
              top: '50%', 
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)'
            }} />
            <input
              type="text"
              className="form-input"
              placeholder="Search movies or TV shows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '2.75rem' }}
            />
          </div>
          <button type="submit" className="btn btn-primary">
            Search
          </button>
          {isSearching && (
            <button type="button" className="btn btn-secondary" onClick={clearSearch}>
              Clear
            </button>
          )}
        </div>
      </form>
      
      <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        {/* Media Type Toggle */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={`btn ${mediaType === 'movie' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMediaType('movie')}
          >
            <Film size={16} />
            Movies
          </button>
          <button
            className={`btn ${mediaType === 'tv' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMediaType('tv')}
          >
            <Tv size={16} />
            TV Shows
          </button>
        </div>

        {/* IMDb Rating Filter - Hide on Trending tab as requested */ }
        {category !== 'trending' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1, minWidth: '200px' }}>
            <span style={{ whiteSpace: 'nowrap', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Min IMDb Rating: <strong style={{ color: 'var(--text-primary)' }}>{imdbRating > 0 ? imdbRating : 'Any'}</strong>
            </span>
            <input 
              type="range" 
              min="0" 
              max="9" 
              step="0.5" 
              value={imdbRating} 
              onChange={(e) => setImdbRating(parseFloat(e.target.value))}
              style={{ flex: 1, cursor: 'pointer' }}
            />
            {imdbRating > 0 && (
              <button 
                className="btn btn-ghost btn-sm" 
                onClick={() => setImdbRating(0)}
                style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
              >
                Reset
              </button>
            )}
        </div>
        )}
      </div>
      
      {/* Category Tabs (only show when not searching or filtering) */}
      {!isSearching && !isFiltering && (
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
          {CATEGORIES.map((cat) => {
            // Skip movie-only categories for TV
            if (mediaType === 'tv' && ['upcoming', 'now_playing'].includes(cat.id)) {
              return null
            }
            const Icon = cat.icon
            return (
              <button
                key={cat.id}
                className={`btn ${category === cat.id ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setCategory(cat.id)}
              >
                <Icon size={16} />
                {cat.label}
              </button>
            )
          })}
        </div>
      )}
      
      {/* Results */}
      <div>
        {isSearching && (
          <div style={{ marginBottom: '1rem' }}>
            <h3>
              Search results for "{searchQuery}"
              {searchData && <span style={{ color: 'var(--text-secondary)', fontWeight: 'normal' }}> ({searchData.total_results} found)</span>}
            </h3>
          </div>
        )}
        
        <MediaGrid 
          items={displayData?.results} 
          loading={isLoading}
        />
      </div>
    </div>
  )
}
