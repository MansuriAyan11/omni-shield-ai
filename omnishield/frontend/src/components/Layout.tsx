import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Home, Image, BarChart3, Key, LogOut, Shield, Video } from 'lucide-react'
import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
  setIsAuthenticated: (value: boolean) => void
}

export default function Layout({ children, setIsAuthenticated }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
    navigate('/login')
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="bg-black border-b border-gray-800">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="w-8 h-8 text-white" />
              <span className="text-xl font-bold">OmniShield</span>
            </div>
            
            <nav className="hidden md:flex space-x-6">
              <Link
                to="/"
                className={`flex items-center space-x-2 px-4 py-2 rounded transition ${
                  isActive('/') 
                    ? 'bg-white text-black' 
                    : 'hover:bg-gray-900'
                }`}
              >
                <Home className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              
              <Link
                to="/moderate"
                className={`flex items-center space-x-2 px-4 py-2 rounded transition ${
                  isActive('/moderate') 
                    ? 'bg-white text-black' 
                    : 'hover:bg-gray-900'
                }`}
              >
                <Image className="w-4 h-4" />
                <span>Moderate</span>
              </Link>

              <Link
                to="/video-moderate"
                className={`flex items-center space-x-2 px-4 py-2 rounded transition ${
                  isActive('/video-moderate')
                    ? 'bg-white text-black'
                    : 'hover:bg-gray-900'
                }`}
              >
                <Video className="w-4 h-4" />
                <span>Video Moderate</span>
              </Link>
              
              <Link
                to="/analytics"
                className={`flex items-center space-x-2 px-4 py-2 rounded transition ${
                  isActive('/analytics') 
                    ? 'bg-white text-black' 
                    : 'hover:bg-gray-900'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Analytics</span>
              </Link>
              
              <Link
                to="/api-keys"
                className={`flex items-center space-x-2 px-4 py-2 rounded transition ${
                  isActive('/api-keys') 
                    ? 'bg-white text-black' 
                    : 'hover:bg-gray-900'
                }`}
              >
                <Key className="w-4 h-4" />
                <span>API Keys</span>
              </Link>
            </nav>

            <button
              onClick={handleLogout}
              className="flex items-center space-x-2 px-4 py-2 bg-white text-black rounded hover:bg-gray-200 transition"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-black border-t border-gray-800 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-gray-500">
          <p>&copy; 2026 OmniShield. AI-Powered Content Moderation Platform.</p>
        </div>
      </footer>
    </div>
  )
}
