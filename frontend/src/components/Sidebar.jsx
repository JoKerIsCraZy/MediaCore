import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  ListVideo, 
  Compass, 
  Settings,
  Joystick
} from 'lucide-react'

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <Joystick size={36} />
          <h1>MediaCore</h1>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={20} />
          Dashboard
        </NavLink>
        
        <NavLink to="/lists" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <ListVideo size={20} />
          My Lists
        </NavLink>
        
        <NavLink to="/discover" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Compass size={20} />
          Discover
        </NavLink>
        
        <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <Settings size={20} />
          Settings
        </NavLink>
      </nav>
    </aside>
  )
}
