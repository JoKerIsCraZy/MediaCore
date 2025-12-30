import { useState, useEffect } from 'react'
import { Save, Key, Clock, Server } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState({
    tmdbApiKey: '',
    updateInterval: 6,
    backendUrl: 'http://127.0.0.1:8000',
  })
  const [saved, setSaved] = useState(false)
  
  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('mediacore_settings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    }
  }, [])
  
  const handleSave = () => {
    localStorage.setItem('mediacore_settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }
  
  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '2rem' }}>
        <h1>Settings</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
          Configure MediaCore
        </p>
      </div>
      
      <div style={{ maxWidth: '600px' }}>
        {/* API Settings */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header">
            <h3><Key size={18} style={{ marginRight: '0.5rem' }} />API Configuration</h3>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label className="form-label">Backend URL</label>
              <input
                type="text"
                className="form-input"
                value={settings.backendUrl}
                onChange={(e) => setSettings({ ...settings, backendUrl: e.target.value })}
                placeholder="http://127.0.0.1:8000"
              />
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                URL of the MediaCore backend API
              </p>
            </div>
          </div>
        </div>
        
        {/* Update Settings */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header">
            <h3><Clock size={18} style={{ marginRight: '0.5rem' }} />Update Settings</h3>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label className="form-label">Default Update Interval (hours)</label>
              <input
                type="number"
                className="form-input"
                value={settings.updateInterval}
                onChange={(e) => setSettings({ ...settings, updateInterval: parseInt(e.target.value) || 6 })}
                min={1}
                max={168}
              />
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                How often lists should auto-update (1-168 hours)
              </p>
            </div>
          </div>
        </div>
        
        {/* Integration Info */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-header">
            <h3><Server size={18} style={{ marginRight: '0.5rem' }} />Integrations</h3>
          </div>
          <div className="card-body">
            <h4 style={{ marginBottom: '0.75rem' }}>Radarr / Sonarr</h4>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              To import lists into Radarr or Sonarr, use the export URLs:
            </p>
            <div style={{ 
              background: 'var(--bg-tertiary)', 
              padding: '1rem', 
              borderRadius: 'var(--radius-md)',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              wordBreak: 'break-all'
            }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Radarr:</strong><br />
                {settings.backendUrl}/api/lists/[ID]/export/radarr
              </div>
              <div>
                <strong>Sonarr:</strong><br />
                {settings.backendUrl}/api/lists/[ID]/export/sonarr
              </div>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
              Replace [ID] with your list ID. Add this URL as a Custom List in Radarr/Sonarr settings.
            </p>
          </div>
        </div>
        
        <button className="btn btn-primary" onClick={handleSave}>
          <Save size={16} />
          {saved ? 'Saved!' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}
