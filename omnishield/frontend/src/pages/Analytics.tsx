import { useQuery } from '@tanstack/react-query'
import { analyticsAPI } from '../lib/api'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, Activity, AlertTriangle, CheckCircle, Loader2, BarChart3 } from 'lucide-react'

export default function Analytics() {
  const { data: timeSeries, isLoading: timeSeriesLoading, error: timeSeriesError } = useQuery({
    queryKey: ['timeSeries'],
    queryFn: async () => {
      const response = await analyticsAPI.getTimeSeries(7)
      console.log('📊 RAW Time Series API Response:', response)
      console.log('📊 Time Series Data:', response.data)
      
      // Log each item in detail
      if (Array.isArray(response.data)) {
        response.data.forEach((item, index) => {
          console.log(`📅 Time Series Item ${index}:`, {
            date: item.date,
            safe_count: item.safe_count,
            unsafe_count: item.unsafe_count,
            total_count: item.total_count
          })
        })
      }
      
      return response.data
    },
    refetchInterval: 30000,
  })

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await analyticsAPI.getStats()
      console.log('📈 RAW Stats API Response:', response)
      console.log('📈 Stats Data:', response.data)
      return response.data
    },
    refetchInterval: 30000,
  })

  // Process chart data with debugging
  const chartData = timeSeries?.map((item: any) => {
    const processed = {
      date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      safe: item.safe_count || 0,
      unsafe: item.unsafe_count || 0,
      total: item.total_count || 0,
    }
    console.log('📅 Processed chart item:', processed)
    return processed
  }) || []

  const hasData = chartData.length > 0 && chartData.some((item: { total: number }) => item.total > 0)
  
  console.log('📊 Final Chart Data:', chartData)
  console.log('✅ Has Data:', hasData)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Analytics</h1>
        <p className="text-gray-400">Track your moderation metrics over time</p>
      </div>

      {/* Debug Info */}
      {(timeSeriesError || statsError) && (
        <div className="bg-red-900 border border-red-600 text-white p-4 rounded-lg">
          <p className="font-bold mb-2">⚠️ Error Loading Data:</p>
          {timeSeriesError && <p className="text-sm">Time Series: {String(timeSeriesError)}</p>}
          {statsError && <p className="text-sm">Stats: {String(statsError)}</p>}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white text-black rounded-lg p-6 border border-gray-200 shadow-lg">
          <Activity className="w-8 h-8 mb-4" />
          <p className="text-sm opacity-80 mb-1">Total Requests</p>
          {statsLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-lg">Loading...</span>
            </div>
          ) : (
            <p className="text-3xl font-bold">{stats?.total_requests ?? stats?.total_scans ?? 0}</p>
          )}
        </div>

        <div className="bg-gray-900 text-white rounded-lg p-6 border border-gray-700 shadow-lg">
          <CheckCircle className="w-8 h-8 mb-4 text-green-400" />
          <p className="text-sm opacity-80 mb-1">Safe Content</p>
          {statsLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-lg">Loading...</span>
            </div>
          ) : (
            <p className="text-3xl font-bold">{stats?.safe_count ?? stats?.safe_scans ?? 0}</p>
          )}
        </div>

        <div className="bg-gray-800 text-white rounded-lg p-6 border border-gray-700 shadow-lg">
          <AlertTriangle className="w-8 h-8 mb-4 text-red-400" />
          <p className="text-sm opacity-80 mb-1">Unsafe Content</p>
          {statsLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-lg">Loading...</span>
            </div>
          ) : (
            <p className="text-3xl font-bold">{stats?.unsafe_count ?? stats?.unsafe_scans ?? 0}</p>
          )}
        </div>

        <div className="bg-gray-700 text-white rounded-lg p-6 border border-gray-600 shadow-lg">
          <TrendingUp className="w-8 h-8 mb-4 text-blue-400" />
          <p className="text-sm opacity-80 mb-1">Detection Rate</p>
          {statsLoading ? (
            <div className="flex items-center space-x-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-lg">Loading...</span>
            </div>
          ) : (
            <p className="text-3xl font-bold">
              {stats?.total_requests 
                ? ((stats.unsafe_count / stats.total_requests) * 100).toFixed(1)
                : 0}%
            </p>
          )}
        </div>
      </div>

      {/* Line Chart */}
      <div className="bg-slate-800 text-white rounded-lg p-6 border border-slate-600 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">Requests Over Time</h2>
          <span className="text-xs text-slate-400">
            {chartData.length} days of data
          </span>
        </div>
        
        {timeSeriesLoading ? (
          <div className="flex items-center justify-center h-[300px]">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-slate-400 mx-auto mb-4" />
              <p className="text-slate-400">Loading chart data...</p>
            </div>
          </div>
        ) : !hasData ? (
          <div className="flex flex-col items-center justify-center h-[300px] text-center">
            <BarChart3 className="w-16 h-16 text-slate-600 mb-4" />
            <h3 className="text-lg font-semibold text-slate-300 mb-2">No Traffic Data Available Yet</h3>
            <p className="text-slate-500 text-sm max-w-md">
              Start moderating images to see your analytics data appear here. 
              Charts will update automatically as you process more requests.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#64748b" strokeOpacity={0.5} />
              <XAxis 
                dataKey="date" 
                stroke="#e2e8f0" 
                tick={{ fill: '#e2e8f0', fontSize: 13 }}
                tickLine={{ stroke: '#64748b' }}
                axisLine={{ stroke: '#64748b' }}
              />
              <YAxis 
                stroke="#e2e8f0" 
                tick={{ fill: '#e2e8f0', fontSize: 13 }}
                tickLine={{ stroke: '#64748b' }}
                axisLine={{ stroke: '#64748b' }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '8px',
                  color: '#fff',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.3)',
                }}
                labelStyle={{ color: '#e2e8f0', fontWeight: 'bold', marginBottom: '8px' }}
                itemStyle={{ color: '#e2e8f0', padding: '4px 0' }}
              />
              <Legend 
                wrapperStyle={{ 
                  paddingTop: '20px',
                }}
                iconType="line"
              />
              <Line 
                type="monotone" 
                dataKey="total" 
                stroke="#60a5fa" 
                strokeWidth={4} 
                name="Total Requests"
                dot={{ fill: '#60a5fa', r: 5, strokeWidth: 2, stroke: '#1e293b' }}
                activeDot={{ r: 7, strokeWidth: 2, stroke: '#1e293b' }}
              />
              <Line 
                type="monotone" 
                dataKey="safe" 
                stroke="#34d399" 
                strokeWidth={4} 
                name="Safe Content"
                dot={{ fill: '#34d399', r: 5, strokeWidth: 2, stroke: '#1e293b' }}
                activeDot={{ r: 7, strokeWidth: 2, stroke: '#1e293b' }}
              />
              <Line 
                type="monotone" 
                dataKey="unsafe" 
                stroke="#f87171" 
                strokeWidth={4} 
                name="Unsafe Content"
                dot={{ fill: '#f87171', r: 5, strokeWidth: 2, stroke: '#1e293b' }}
                activeDot={{ r: 7, strokeWidth: 2, stroke: '#1e293b' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Bar Chart */}
      <div className="bg-slate-800 text-white rounded-lg p-6 border border-slate-600 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">Content Classification</h2>
          <span className="text-xs text-slate-400">
            Last 7 days
          </span>
        </div>
        
        {timeSeriesLoading ? (
          <div className="flex items-center justify-center h-[300px]">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-slate-400 mx-auto mb-4" />
              <p className="text-slate-400">Loading chart data...</p>
            </div>
          </div>
        ) : !hasData ? (
          <div className="flex flex-col items-center justify-center h-[300px] text-center">
            <BarChart3 className="w-16 h-16 text-slate-600 mb-4" />
            <h3 className="text-lg font-semibold text-slate-300 mb-2">No Classification Data Available</h3>
            <p className="text-slate-500 text-sm max-w-md">
              Classification breakdown will appear here once you start processing images through the moderation system.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#64748b" strokeOpacity={0.5} />
              <XAxis 
                dataKey="date" 
                stroke="#e2e8f0" 
                tick={{ fill: '#e2e8f0', fontSize: 13 }}
                tickLine={{ stroke: '#64748b' }}
                axisLine={{ stroke: '#64748b' }}
              />
              <YAxis 
                stroke="#e2e8f0" 
                tick={{ fill: '#e2e8f0', fontSize: 13 }}
                tickLine={{ stroke: '#64748b' }}
                axisLine={{ stroke: '#64748b' }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '8px',
                  color: '#fff',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.3)',
                }}
                labelStyle={{ color: '#e2e8f0', fontWeight: 'bold', marginBottom: '8px' }}
                itemStyle={{ color: '#e2e8f0', padding: '4px 0' }}
              />
              <Legend 
                wrapperStyle={{ 
                  paddingTop: '20px',
                }}
                iconType="rect"
              />
              <Bar 
                dataKey="safe" 
                fill="#34d399" 
                name="Safe Content"
                radius={[8, 8, 0, 0]}
              />
              <Bar 
                dataKey="unsafe" 
                fill="#f87171" 
                name="Unsafe Content"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
