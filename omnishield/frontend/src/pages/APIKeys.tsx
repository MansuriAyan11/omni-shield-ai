import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { keyAPI } from '../lib/api'
import { Key, Plus, Trash2, Copy, Check, AlertTriangle, X } from 'lucide-react'

interface APIKey {
  id: string
  name: string
  rate_limit: number
  status: string
  created_at: string
  last_used?: string
}

interface NewKeyResponse {
  key_details: APIKey
  raw_key: string
}

export default function APIKeys() {
  const [newKeyName, setNewKeyName] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [copiedKey, setCopiedKey] = useState('')
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null)
  const [showKeyModal, setShowKeyModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: keys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const response = await keyAPI.listKeys()
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: (name: string) => keyAPI.createKey(name),
    onSuccess: (response) => {
      // Extract the raw key from the response
      const newKeyData = response.data as NewKeyResponse
      
      // Store the plaintext key temporarily for the modal
      setNewlyCreatedKey(newKeyData.raw_key)
      setShowKeyModal(true)
      
      // Refresh the keys list to show the new key (with masked preview)
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      
      // Reset form
      setNewKeyName('')
      setShowCreateForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (keyId: string) => keyAPI.revokeKey(keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newKeyName.trim()) {
      createMutation.mutate(newKeyName)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(text)
    setTimeout(() => setCopiedKey(''), 2000)
  }

  const closeKeyModal = () => {
    // Securely discard the plaintext key from memory
    setNewlyCreatedKey(null)
    setShowKeyModal(false)
    setCopiedKey('')
  }

  const copyAndCloseModal = () => {
    if (newlyCreatedKey) {
      copyToClipboard(newlyCreatedKey)
      // Give user visual feedback before closing
      setTimeout(() => {
        closeKeyModal()
      }, 1500)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-white text-xl">Loading API keys...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Secure API Key Modal - One-time view */}
      {showKeyModal && newlyCreatedKey && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full p-8 relative animate-fadeIn">
            {/* Close button */}
            <button
              onClick={closeKeyModal}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition"
              aria-label="Close modal"
            >
              <X className="w-6 h-6" />
            </button>

            {/* Header */}
            <div className="flex items-center space-x-3 mb-6">
              <div className="bg-green-100 p-3 rounded-full">
                <Key className="w-8 h-8 text-green-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">API Key Created Successfully!</h2>
                <p className="text-sm text-gray-600">Your new API key is ready to use</p>
              </div>
            </div>

            {/* Warning Alert */}
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 rounded">
              <div className="flex items-start">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-yellow-800 mb-1">
                    Important Security Notice
                  </h3>
                  <p className="text-sm text-yellow-700">
                    For security reasons, this API key will only be displayed once. 
                    Make sure to copy it now and store it in a secure location. 
                    You will not be able to see it again.
                  </p>
                </div>
              </div>
            </div>

            {/* API Key Display */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your API Key
              </label>
              <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-4 font-mono text-sm break-all select-all">
                {newlyCreatedKey}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                onClick={copyAndCloseModal}
                className="flex-1 flex items-center justify-center space-x-2 bg-black text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-800 transition"
              >
                {copiedKey === newlyCreatedKey ? (
                  <>
                    <Check className="w-5 h-5" />
                    <span>Copied! Closing...</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-5 h-5" />
                    <span>Copy to Clipboard & Close</span>
                  </>
                )}
              </button>
              <button
                onClick={() => copyToClipboard(newlyCreatedKey)}
                className="flex items-center justify-center space-x-2 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition"
              >
                {copiedKey === newlyCreatedKey ? (
                  <>
                    <Check className="w-5 h-5 text-green-600" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-5 h-5" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>

            {/* Manual close option */}
            <div className="mt-4 text-center">
              <button
                onClick={closeKeyModal}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                I've saved my key, close this window
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">API Keys</h1>
          <p className="text-gray-400">Manage your API keys for authentication</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center space-x-2 bg-white text-black px-4 py-2 rounded font-medium hover:bg-gray-200 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Create Key</span>
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-white text-black rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-bold mb-4">Create New API Key</h2>
          <form onSubmit={handleCreateKey} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Key Name</label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-black focus:border-transparent"
                placeholder="Production API Key"
                required
              />
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="bg-black text-white px-6 py-2 rounded font-medium hover:bg-gray-800 transition disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-200 text-black px-6 py-2 rounded font-medium hover:bg-gray-300 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-4">
        {keys && keys.length > 0 ? (
          keys.map((apiKey: APIKey) => {
            // Generate masked preview (e.g., "ak_li...4567")
            const keyId = apiKey.id.toString()
            const maskedPreview = `ak_****...${keyId.substring(keyId.length - 4)}`
            
            return (
              <div
                key={apiKey.id}
                className="bg-white text-black rounded-lg p-6 border border-gray-200 flex items-center justify-between"
              >
                <div className="flex items-center space-x-4">
                  <div className="bg-black text-white p-3 rounded">
                    <Key className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{apiKey.name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <code className="bg-gray-100 px-3 py-1 rounded text-sm font-mono text-gray-600">
                        {maskedPreview}
                      </code>
                      <span className="text-xs text-gray-400 italic">
                        (hidden for security)
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <span>Created: {new Date(apiKey.created_at).toLocaleDateString()}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        apiKey.status === 'active' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {apiKey.status}
                      </span>
                      {apiKey.last_used && (
                        <span>Last used: {new Date(apiKey.last_used).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
                      deleteMutation.mutate(apiKey.id)
                    }
                  }}
                  className="p-2 text-red-600 hover:bg-red-50 rounded transition"
                  title="Delete key"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            )
          })
        ) : (
          <div className="bg-white text-black rounded-lg p-12 border border-gray-200 text-center">
            <Key className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-xl font-bold mb-2">No API Keys</h3>
            <p className="text-gray-600 mb-6">
              Create your first API key to start using the moderation API
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-black text-white px-6 py-2 rounded font-medium hover:bg-gray-800 transition"
            >
              Create API Key
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
