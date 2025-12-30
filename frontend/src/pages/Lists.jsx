import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listsApi, getPosterUrl } from '../api'
import { Plus, Film, Tv, RefreshCw, Trash2, MoreVertical } from 'lucide-react'
import { useState } from 'react'

export default function Lists() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('all')
  
  const { data: lists, isLoading } = useQuery({
    queryKey: ['lists'],
    queryFn: () => listsApi.getAll(),
  })
  
  const deleteMutation = useMutation({
    mutationFn: (id) => listsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['lists'])
    },
  })
  
  const refreshMutation = useMutation({
    mutationFn: (id) => listsApi.refresh(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['lists'])
    },
  })
  
  const filteredLists = lists?.filter(list => {
    if (filter === 'all') return true
    return list.media_type === filter
  }) || []
  
  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    )
  }
  
  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>My Lists</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            Manage your movie and TV show lists
          </p>
        </div>
        <Link to="/lists/new" className="btn btn-primary">
          <Plus size={18} />
          New List
        </Link>
      </div>
      
      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
        <button 
          className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setFilter('all')}
        >
          All ({lists?.length || 0})
        </button>
        <button 
          className={`btn ${filter === 'movie' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setFilter('movie')}
        >
          <Film size={16} />
          Movies
        </button>
        <button 
          className={`btn ${filter === 'tv' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setFilter('tv')}
        >
          <Tv size={16} />
          TV Shows
        </button>
      </div>
      
      {filteredLists.length === 0 ? (
        <div className="empty-state">
          <h3>No lists yet</h3>
          <p>Create your first list to get started!</p>
          <Link to="/lists/new" className="btn btn-primary" style={{ marginTop: '1rem' }}>
            <Plus size={18} />
            Create List
          </Link>
        </div>
      ) : (
        <div className="list-grid">
          {filteredLists.map((list) => (
            <div key={list.id} className="list-card">
              <div className="list-card-header">
                <Link to={`/lists/${list.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <h3 className="list-card-title">{list.name}</h3>
                </Link>
                <span className={`badge badge-${list.media_type}`}>
                  {list.media_type === 'movie' ? <Film size={12} /> : <Tv size={12} />}
                  {list.media_type}
                </span>
              </div>
              
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                {list.description || 'No description'}
              </p>
              
              <div className="list-card-meta" style={{ marginBottom: '1rem' }}>
                <span>{list.item_count} items</span>
                <span>{list.auto_update ? '⚡ Auto-update' : '📴 Manual'}</span>
              </div>
              
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Link to={`/lists/${list.id}`} className="btn btn-secondary" style={{ flex: 1 }}>
                  View
                </Link>
                <button 
                  className="btn btn-ghost btn-icon"
                  onClick={() => refreshMutation.mutate(list.id)}
                  disabled={refreshMutation.isPending}
                >
                  <RefreshCw size={18} className={refreshMutation.isPending ? 'animate-spin' : ''} />
                </button>
                <button 
                  className="btn btn-ghost btn-icon"
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this list?')) {
                      deleteMutation.mutate(list.id)
                    }
                  }}
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
