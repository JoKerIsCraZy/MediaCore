import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { listsApi } from '../api'
import {
  ArrowLeft, Edit, RefreshCw, Trash2, Download, Copy, Check,
  Film, Tv, Star, Calendar, Clock
} from 'lucide-react'
import MediaGrid from '../components/MediaGrid'

export default function ListDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [copied, setCopied] = useState(false)
  
  const { data: list, isLoading } = useQuery({
    queryKey: ['list', id],
    queryFn: () => listsApi.getById(id),
  })
  
  const refreshMutation = useMutation({
    mutationFn: () => listsApi.refresh(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['list', id])
    },
  })
  
  const deleteMutation = useMutation({
    mutationFn: () => listsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lists'] })
      navigate('/lists')
    },
  })
  
  const handleExport = async (format) => {
    try {
      let data
      if (format === 'json') {
        data = await listsApi.exportJson(id)
      } else if (format === 'radarr') {
        data = await listsApi.exportRadarr(id)
      } else if (format === 'sonarr') {
        data = await listsApi.exportSonarr(id)
      }

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${list.name.replace(/\s+/g, '_')}_${format}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      alert('Export failed: ' + error.message)
    }
  }

  const handleCopyLink = async (format) => {
    const url = `${window.location.origin}/api/lists/${id}/export/${format}`
    try {
      await navigator.clipboard.writeText(url)
      setCopied(format)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      prompt('Copy this URL:', url)
    }
  }
  
  if (isLoading) {
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    )
  }
  
  if (!list) {
    return (
      <div className="empty-state">
        <h3>List not found</h3>
        <Link to="/lists" className="btn btn-primary" style={{ marginTop: '1rem' }}>
          Back to Lists
        </Link>
      </div>
    )
  }
  
  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <Link to="/lists" style={{ 
          display: 'inline-flex', 
          alignItems: 'center', 
          gap: '0.5rem',
          color: 'var(--text-secondary)',
          marginBottom: '1rem'
        }}>
          <ArrowLeft size={18} />
          Back to Lists
        </Link>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
              <h1>{list.name}</h1>
              <span className={`badge badge-${list.media_type}`}>
                {list.media_type === 'movie' ? <Film size={12} /> : <Tv size={12} />}
                {list.media_type}
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)' }}>
              {list.description || 'No description'}
            </p>
            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Film size={14} />
                {list.item_count} items
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Clock size={14} />
                Updates every {list.update_interval}h
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Calendar size={14} />
                {new Date(list.last_updated).toLocaleString()}
              </span>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary"
              style={{ width: '120px', justifyContent: 'center', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', boxSizing: 'border-box' }}
              onClick={() => refreshMutation.mutate()}
              disabled={refreshMutation.isPending}
            >
              <RefreshCw size={16} className={refreshMutation.isPending ? 'animate-spin' : ''} />
              Refresh
            </button>
            <Link to={`/lists/${id}/edit`} className="btn btn-secondary" style={{ width: '120px', justifyContent: 'center', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', boxSizing: 'border-box' }}>
              <Edit size={16} />
              Edit
            </Link>
            <div style={{ position: 'relative', display: 'inline-block' }}>
              <button
                className="btn btn-secondary"
                style={{ width: '120px', justifyContent: 'center', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', boxSizing: 'border-box' }}
                onClick={() => setShowExportMenu(!showExportMenu)}
              >
                <Download size={16} />
                Export
              </button>
              {showExportMenu && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: '0.5rem',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.5rem',
                  width: '200px',
                  zIndex: 10
                }}>
                  <button className="btn btn-ghost" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={() => { handleExport('json'); setShowExportMenu(false); }}>
                    <Download size={14} />
                    JSON (Download)
                  </button>
                  <button className="btn btn-ghost" style={{ width: '100%', justifyContent: 'flex-start' }} onClick={() => { handleCopyLink(list.media_type === 'movie' ? 'radarr' : 'sonarr'); setShowExportMenu(false); }}>
                    {(copied === 'radarr' || copied === 'sonarr') ? <Check size={14} /> : <Copy size={14} />}
                    {(copied === 'radarr' || copied === 'sonarr') ? 'Link kopiert!' : `${list.media_type === 'movie' ? 'Radarr' : 'Sonarr'} (Link kopieren)`}
                  </button>
                </div>
              )}
            </div>
            <button
              className="btn btn-secondary"
              style={{ width: '120px', justifyContent: 'center', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', boxSizing: 'border-box' }}
              onClick={() => {
                if (confirm('Are you sure you want to delete this list?')) {
                  deleteMutation.mutate()
                }
              }}
            >
              <Trash2 size={16} />
              Delete
            </button>
          </div>
        </div>
      </div>
      
      {/* Filters Summary */}
      {list.filters && list.filters.length > 0 && (
        <div style={{ 
          padding: '1rem', 
          background: 'var(--bg-secondary)', 
          borderRadius: 'var(--radius-md)',
          marginBottom: '2rem',
          fontSize: '0.9rem'
        }}>
          <strong>Active Filters:</strong>
          <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
            {list.filters.map((f, i) => (
              <span key={i}>
                {i > 0 && ` ${list.filter_operator.toUpperCase()} `}
                {f.field} {f.operator} {JSON.stringify(f.value)}
              </span>
            ))}
          </span>
        </div>
      )}
      
      {/* List Items */}
      <MediaGrid items={list.items} />
    </div>
  )
}
