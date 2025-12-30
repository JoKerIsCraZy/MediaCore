import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listsApi, mediaApi, getPosterUrl } from '../api'
import { ListVideo, Film, Tv, TrendingUp, Plus } from 'lucide-react'
import MediaGrid from '../components/MediaGrid'

export default function Dashboard() {
  const { data: lists } = useQuery({
    queryKey: ['lists'],
    queryFn: () => listsApi.getAll(),
  })
  
  const { data: trending, isLoading: trendingLoading } = useQuery({
    queryKey: ['trending', 'movie'],
    queryFn: () => mediaApi.trending('movie', 'week'),
  })
  
  const movieLists = lists?.filter(l => l.media_type === 'movie').length || 0
  const tvLists = lists?.filter(l => l.media_type === 'tv').length || 0
  const totalItems = lists?.reduce((sum, l) => sum + l.item_count, 0) || 0
  
  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Welcome to MediaCore - Your Media List Manager
          </p>
        </div>
        <Link to="/lists/new" className="btn btn-primary">
          <Plus size={18} />
          New List
        </Link>
      </div>
      
      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3><ListVideo size={18} style={{ marginRight: '0.5rem' }} />Total Lists</h3>
          <div className="value">{lists?.length || 0}</div>
        </div>
        <div className="stat-card">
          <h3><Film size={18} style={{ marginRight: '0.5rem' }} />Movie Lists</h3>
          <div className="value">{movieLists}</div>
        </div>
        <div className="stat-card">
          <h3><Tv size={18} style={{ marginRight: '0.5rem' }} />TV Lists</h3>
          <div className="value">{tvLists}</div>
        </div>
        <div className="stat-card">
          <h3><TrendingUp size={18} style={{ marginRight: '0.5rem' }} />Total Items</h3>
          <div className="value">{totalItems}</div>
        </div>
      </div>
      
      {/* Recent Lists */}
      {lists && lists.length > 0 && (
        <section style={{ marginBottom: '3rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>Recent Lists</h2>
            <Link to="/lists" style={{ color: 'var(--text-secondary)' }}>View all →</Link>
          </div>
          <div className="list-grid">
            {lists.slice(0, 3).map((list) => (
              <Link key={list.id} to={`/lists/${list.id}`} style={{ textDecoration: 'none' }}>
                <div className="list-card">
                  <div className="list-card-header">
                    <h3 className="list-card-title">{list.name}</h3>
                    <span className={`badge badge-${list.media_type}`}>
                      {list.media_type === 'movie' ? <Film size={12} /> : <Tv size={12} />}
                      {list.media_type}
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    {list.description || 'No description'}
                  </p>
                  <div className="list-card-meta">
                    <span>{list.item_count} items</span>
                    <span>Updated {new Date(list.last_updated).toLocaleDateString()}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
      
      {/* Trending */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2>Trending This Week</h2>
          <Link to="/discover" style={{ color: 'var(--text-secondary)' }}>Discover more →</Link>
        </div>
        <MediaGrid 
          items={trending?.results?.slice(0, 10)} 
          loading={trendingLoading}
        />
      </section>
    </div>
  )
}
