import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Moderate from './pages/Moderate'
import VideoModerate from './pages/VideoModerate'
import Analytics from './pages/Analytics'
import APIKeys from './pages/APIKeys'
import Layout from './components/Layout'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    setIsAuthenticated(!!token)
    setLoading(false)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      <Route
        path="/"
        element={
          isAuthenticated ? (
            <Layout setIsAuthenticated={setIsAuthenticated}>
              <Dashboard />
            </Layout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      
      <Route
        path="/moderate"
        element={
          isAuthenticated ? (
            <Layout setIsAuthenticated={setIsAuthenticated}>
              <Moderate />
            </Layout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      
      <Route
        path="/video-moderate"
        element={
          isAuthenticated ? (
            <Layout setIsAuthenticated={setIsAuthenticated}>
              <VideoModerate />
            </Layout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      
      <Route
        path="/analytics"
        element={
          isAuthenticated ? (
            <Layout setIsAuthenticated={setIsAuthenticated}>
              <Analytics />
            </Layout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      
      <Route
        path="/api-keys"
        element={
          isAuthenticated ? (
            <Layout setIsAuthenticated={setIsAuthenticated}>
              <APIKeys />
            </Layout>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
    </Routes>
  )
}

export default App
