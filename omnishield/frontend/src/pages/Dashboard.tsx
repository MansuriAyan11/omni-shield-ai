import { useQuery } from '@tanstack/react-query'
import { analyticsAPI } from '../lib/api'
import { Shield, AlertTriangle, CheckCircle, Activity, Video, Flag, Clock } from 'lucide-react'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await analyticsAPI.getStats()
      return response.data
    },
    refetchInterval: 30000, // Auto-refetch every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-white text-xl">Loading dashboard...</div>
      </div>
    )
  }

  const cards = [
    {
      title: 'Total Requests',
      value: stats?.total_requests || 0,
      icon: Activity,
      bgColor: 'bg-white',
      textColor: 'text-black',
    },
    {
      title: 'Safe Content',
      value: stats?.safe_count || 0,
      icon: CheckCircle,
      bgColor: 'bg-gray-900',
      textColor: 'text-white',
    },
    {
      title: 'Unsafe Content',
      value: stats?.unsafe_count || 0,
      icon: AlertTriangle,
      bgColor: 'bg-gray-800',
      textColor: 'text-white',
    },
    {
      title: 'Active API Keys',
      value: stats?.active_keys || 0,
      icon: Shield,
      bgColor: 'bg-gray-700',
      textColor: 'text-white',
    },
  ]

  const videoCards = [
    {
      title: 'Total Videos Audited',
      value: stats?.total_videos || 0,
      icon: Video,
      bgColor: 'bg-gray-900',
      textColor: 'text-white',
    },
    {
      title: 'Flagged Videos',
      value: stats?.flagged_videos || 0,
      icon: Flag,
      bgColor: 'bg-gray-800',
      textColor: 'text-white',
    },
  ]

  const avgVideoScanLatency = stats?.avg_video_scan_latency ?? null

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-gray-400">Monitor your content moderation statistics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <div
              key={card.title}
              className={`${card.bgColor} ${card.textColor} rounded-lg p-6 border border-gray-700`}
            >
              <div className="flex items-center justify-between mb-4">
                <Icon className="w-8 h-8" />
              </div>
              <div>
                <p className="text-sm opacity-80 mb-1">{card.title}</p>
                <p className="text-3xl font-bold">{card.value.toLocaleString()}</p>
              </div>
            </div>
          )
        })}
      </div>

      <div>
        <h2 className="text-xl font-bold text-white mb-4 flex items-center space-x-2">
          <Video className="w-5 h-5" />
          <span>Video Moderation Metrics</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {videoCards.map((card) => {
            const Icon = card.icon
            return (
              <div
                key={card.title}
                className={`${card.bgColor} ${card.textColor} rounded-lg p-6 border border-gray-700`}
              >
                <div className="flex items-center justify-between mb-4">
                  <Icon className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-sm opacity-80 mb-1">{card.title}</p>
                  <p className="text-3xl font-bold">{card.value.toLocaleString()}</p>
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-4 bg-gray-900 rounded-lg p-6 border border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Clock className="w-6 h-6 text-white" />
            <div>
              <p className="text-sm text-gray-400 mb-1">Avg Video Scan Latency</p>
              <p className="text-lg font-semibold text-white">
                Processing time relative to video duration (lower is faster)
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-white">
              {avgVideoScanLatency !== null ? `${avgVideoScanLatency.toFixed(2)}x` : '—'}
            </p>
            <p className="text-xs text-gray-500">
              {avgVideoScanLatency !== null
                ? `${(avgVideoScanLatency * 100).toFixed(1)}% of real-time`
                : 'No video data yet'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white text-black rounded-lg p-8 border border-gray-200">
        <h2 className="text-2xl font-bold mb-4">Quick Start</h2>
        <div className="space-y-4">
          <div className="flex items-start space-x-3">
            <div className="bg-black text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-1">
              1
            </div>
            <div>
              <h3 className="font-semibold mb-1">Upload an Image</h3>
              <p className="text-gray-600">
                Go to the Moderate page to test image moderation with AI models.
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="bg-black text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-1">
              2
            </div>
            <div>
              <h3 className="font-semibold mb-1">Generate API Keys</h3>
              <p className="text-gray-600">
                Create API keys to integrate moderation into your application.
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="bg-black text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-1">
              3
            </div>
            <div>
              <h3 className="font-semibold mb-1">View Analytics</h3>
              <p className="text-gray-600">
                Monitor usage patterns and moderation results over time.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="bg-black text-white rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-1">
              4
            </div>
            <div>
              <h3 className="font-semibold mb-1">Run Asynchronous Video Audit</h3>
              <p className="text-gray-600">
                Navigate to the Video Moderate panel to split multi-format streams into continuous timeline vectors for deep content extraction.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
