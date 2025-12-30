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
      
      {media.vote_average > 0 && (
        <div className="rating">
          <Star size={14} />
          {media.vote_average.toFixed(1)}
        </div>
      )}
      
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
