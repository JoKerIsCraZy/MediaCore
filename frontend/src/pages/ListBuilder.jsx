import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listsApi } from '../api'
import { ArrowLeft, Save, Eye, Film, Tv } from 'lucide-react'
import FilterBuilder from '../components/FilterBuilder'
import MediaGrid from '../components/MediaGrid'

const SORT_OPTIONS = [
  { value: 'popularity.desc', label: 'Popularity (High to Low)' },
  { value: 'popularity.asc', label: 'Popularity (Low to High)' },
  { value: 'vote_average.desc', label: 'Rating (High to Low)' },
  { value: 'vote_average.asc', label: 'TMDB Rating (Low to High)' },
  { value: 'imdb_rating.desc', label: 'IMDb Rating (High to Low)' },
  { value: 'imdb_rating.asc', label: 'IMDb Rating (Low to High)' },
  { value: 'release_date.desc', label: 'Release Date (Newest)' },
  { value: 'release_date.asc', label: 'Release Date (Oldest)' },
  { value: 'vote_count.desc', label: 'Vote Count (High to Low)' },
]

export default function ListBuilder() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEditing = !!id
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    media_type: 'movie',
    filters: [],
    filter_operator: 'and',
    sort_by: 'popularity.desc',
    limit: 100,
    auto_update: true,
    update_interval: 6,
  })
  
  const [previewData, setPreviewData] = useState(null)
  const [showPreview, setShowPreview] = useState(false)
  
  // Load existing list if editing
  const { data: existingList } = useQuery({
    queryKey: ['list', id],
    queryFn: () => listsApi.getById(id),
    enabled: isEditing,
  })
  
  useEffect(() => {
    if (existingList) {
      setFormData({
        name: existingList.name,
        description: existingList.description,
        media_type: existingList.media_type,
        filters: existingList.filters || [],
        filter_operator: existingList.filter_operator,
        sort_by: existingList.sort_by,
        limit: existingList.limit,
        auto_update: existingList.auto_update,
        update_interval: existingList.update_interval,
      })
    }
  }, [existingList])
  
  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: (data) => listsApi.preview(data),
    onSuccess: (data) => {
      setPreviewData(data)
      setShowPreview(true)
    },
  })
  
  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: (data) => isEditing
      ? listsApi.update(id, data)
      : listsApi.create(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries(['lists'])
      navigate(`/lists/${result.id}`)
    },
    onError: (error) => {
      console.error('Save error:', error)
      alert(`Error: ${error.message}`)
    },
  })
  
  const handlePreview = () => {
    previewMutation.mutate({
      media_type: formData.media_type,
      filters: formData.filters,
      filter_operator: formData.filter_operator,
      sort_by: formData.sort_by,
      page: 1,
    })
  }
  
  const handleSave = () => {
    if (!formData.name.trim()) {
      alert('Please enter a list name')
      return
    }
    saveMutation.mutate(formData)
  }
  
  return (
    <div className="animate-fade-in">
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
        
        <h1>{isEditing ? 'Edit List' : 'Create New List'}</h1>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Form */}
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <h3>List Details</h3>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="My Awesome List"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea form-input"
                  placeholder="What is this list about?"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Media Type</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className={`btn ${formData.media_type === 'movie' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setFormData({ ...formData, media_type: 'movie' })}
                  >
                    <Film size={16} />
                    Movies
                  </button>
                  <button
                    className={`btn ${formData.media_type === 'tv' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setFormData({ ...formData, media_type: 'tv' })}
                  >
                    <Tv size={16} />
                    TV Shows
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Filters */}
          <div style={{ marginBottom: '1.5rem' }}>
            <FilterBuilder
              filters={formData.filters}
              onChange={(filters) => setFormData({ ...formData, filters })}
              mediaType={formData.media_type}
            />
          </div>
          
          {/* Sorting & Limits */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <h3>Sorting & Limits</h3>
            </div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">Sort By</label>
                <select
                  className="form-select"
                  value={formData.sort_by}
                  onChange={(e) => setFormData({ ...formData, sort_by: e.target.value })}
                >
                  {SORT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label className="form-label">Max Items</label>
                <input
                  type="number"
                  className="form-input"
                  value={formData.limit}
                  onChange={(e) => setFormData({ ...formData, limit: parseInt(e.target.value) || 100 })}
                  min={1}
                  max={1000}
                />
              </div>
              
              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={formData.auto_update}
                    onChange={(e) => setFormData({ ...formData, auto_update: e.target.checked })}
                  />
                  Auto-update list
                </label>
              </div>
              
              {formData.auto_update && (
                <div className="form-group">
                  <label className="form-label">Update Interval (hours)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={formData.update_interval}
                    onChange={(e) => setFormData({ ...formData, update_interval: parseInt(e.target.value) || 6 })}
                    min={1}
                    max={168}
                  />
                </div>
              )}
            </div>
          </div>
          
          {/* Actions */}
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              className="btn btn-secondary" 
              onClick={handlePreview}
              disabled={previewMutation.isPending}
            >
              <Eye size={16} />
              {previewMutation.isPending ? 'Loading...' : 'Preview'}
            </button>
            <button 
              className="btn btn-primary" 
              onClick={handleSave}
              disabled={saveMutation.isPending}
            >
              <Save size={16} />
              {saveMutation.isPending ? 'Saving...' : (isEditing ? 'Update List' : 'Create List')}
            </button>
          </div>
        </div>
        
        {/* Preview */}
        <div>
          <div className="card">
            <div className="card-header">
              <h3>Preview</h3>
              {previewData && (
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                  {previewData.total_results} results found
                </span>
              )}
            </div>
            <div className="card-body">
              {!showPreview ? (
                <div className="empty-state" style={{ padding: '2rem' }}>
                  <p>Click "Preview" to see matching results</p>
                </div>
              ) : (
                <MediaGrid 
                  items={previewData?.results} 
                  loading={previewMutation.isPending}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
