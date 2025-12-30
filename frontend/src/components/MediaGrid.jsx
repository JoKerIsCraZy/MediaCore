import MediaCard from './MediaCard'

export default function MediaGrid({ items, onItemClick, loading }) {
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    )
  }
  
  if (!items || items.length === 0) {
    return (
      <div className="empty-state">
        <h3>No results found</h3>
        <p>Try adjusting your filters or search query</p>
      </div>
    )
  }
  
  return (
    <div className="media-grid">
      {items.map((item) => (
        <MediaCard 
          key={`${item.media_type}-${item.tmdb_id}`} 
          media={item} 
          onClick={onItemClick}
        />
      ))}
    </div>
  )
}
