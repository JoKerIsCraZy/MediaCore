import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Lists from './pages/Lists'
import ListDetail from './pages/ListDetail'
import ListBuilder from './pages/ListBuilder'
import Discover from './pages/Discover'
import Settings from './pages/Settings'

function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/lists" element={<Lists />} />
          <Route path="/lists/new" element={<ListBuilder />} />
          <Route path="/lists/:id" element={<ListDetail />} />
          <Route path="/lists/:id/edit" element={<ListBuilder />} />
          <Route path="/discover" element={<Discover />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
