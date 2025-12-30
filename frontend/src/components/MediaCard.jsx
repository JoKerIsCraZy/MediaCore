import { Star } from 'lucide-react'
import { getPosterUrl } from '../api'

export default function MediaCard({ media, onClick }) {
  const posterUrl = getPosterUrl(media.poster_path)
  const year = media.release_date ? media.release_date.substring(0, 4) : ''
  
  return (
    <div className="media-card" onClick={() => onClick?.(media)}>
      {posterUrl ? (
        <img src={posterUrl} alt={media.title} loading="lazy" />
      ) : (
        <div style={{ 
          width: '100%', 
          height: '100%', 
          background: 'var(--bg-tertiary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)'
        }}>
          No Image
        </div>
      )}
      
      <div className="ratings-container" style={{ position: 'absolute', top: '0.5rem', right: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: 'flex-end', zIndex: 10 }}>
        {media.vote_average > 0 && (
          <div className="rating" style={{ position: 'static', display: 'flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', borderRadius: '4px', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', fontSize: '0.8rem', fontWeight: '500' }}>
            <Star size={12} fill="currentColor" className="text-yellow-400" style={{ color: '#facc15' }} />
            <span style={{ fontSize: '0.7rem' }}>TMDB</span>
            <span>{media.vote_average.toFixed(1)}</span>
          </div>
        )}
        {media.imdb_rating > 0 && (
          <div className="rating imdb" style={{ position: 'static', display: 'flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', borderRadius: '4px', background: 'rgba(245, 197, 24, 0.9)', color: '#000', fontSize: '0.8rem', fontWeight: 'bold' }}>
            <span style={{ fontSize: '0.7rem' }}>IMDb</span>
            <span>{media.imdb_rating.toFixed(1)}</span>
          </div>
        )}
      </div>
      
      <div className="overlay">
        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>
          {media.title}
        </h4>
        {year && (
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            {year}
          </span>
        )}
      </div>
    </div>
  )
}
