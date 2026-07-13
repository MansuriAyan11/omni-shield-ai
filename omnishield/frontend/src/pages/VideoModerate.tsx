import { useState, useRef, useEffect, useCallback } from 'react'
import { Upload, Video, AlertCircle, CheckCircle, Loader2, FileVideo, Clock, ScanLine } from 'lucide-react'
import { moderationAPI } from '../lib/api'

type ViewState = 'IDLE' | 'PROCESSING' | 'COMPLETED'

interface VideoFrameFlag {
  id: string
  timestamp_seconds: number
  frame_index: number
  flag_category: string
  confidence: number
  decision: string
  detected_labels: string[]
  created_at: string
}

interface VideoModerationData {
  job_id: string
  filename: string
  status: string
  overall_status: string | null
  risk_level: string | null
  overall_confidence: number | null
  recommended_action: string | null
  reason: string | null
  total_duration: number | null
  frames_sampled: number
  frames_flagged: number
  frame_interval_seconds: number
  processing_time: number | null
  error_message: string | null
  created_at: string
  completed_at: string | null
  frame_flags: VideoFrameFlag[]
}

interface VideoJobResponse {
  job_id: string
  status: string
  filename: string
  message: string
  status_url: string
}

const ALLOWED_VIDEO_TYPES = [
  'video/mp4',
  'video/avi',
  'video/quicktime',
  'video/webm',
  'video/x-matroska',
]

const ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.webm', '.mkv']

export default function VideoModerate() {
  const [viewState, setViewState] = useState<ViewState>('IDLE')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [result, setResult] = useState<VideoModerationData | null>(null)
  const [error, setError] = useState('')
  const [scanningDots, setScanningDots] = useState(0)

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const dotsRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const clearPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const clearDots = useCallback(() => {
    if (dotsRef.current) {
      clearInterval(dotsRef.current)
      dotsRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      clearPolling()
      clearDots()
    }
  }, [clearPolling, clearDots])

  const isValidVideoFile = (file: File): boolean => {
    if (ALLOWED_VIDEO_TYPES.includes(file.type)) return true
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    return ALLOWED_VIDEO_EXTENSIONS.includes(ext)
  }

  const handleFile = (file: File) => {
    setError('')
    if (!isValidVideoFile(file)) {
      setError('Please upload a valid video file (.mp4, .avi, .mov, .webm, .mkv).')
      return
    }
    setSelectedFile(file)
    startUpload(file)
  }

  const startUpload = async (file: File) => {
    setViewState('PROCESSING')
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await moderationAPI.moderateVideo(formData)
      const job = response.data as VideoJobResponse
      startPolling(job.job_id)
      startScanningAnimation()
    } catch (err: any) {
      setViewState('IDLE')
      setError(err.response?.data?.detail || err.message || 'Failed to upload video.')
    }
  }

  const startPolling = (id: string) => {
    clearPolling()
    pollingRef.current = setInterval(async () => {
      try {
        const response = await moderationAPI.getVideoModerationStatus(id)
        const data = (response.data?.data || response.data) as VideoModerationData

        if (data.status === 'completed' || data.status === 'failed') {
          clearPolling()
          clearDots()
          setResult(data)
          setViewState('COMPLETED')
        } else {
          setResult(data)
        }
      } catch (err: any) {
        clearPolling()
        clearDots()
        setViewState('IDLE')
        setError(err.response?.data?.detail || err.message || 'Failed to poll job status.')
      }
    }, 2000)
  }

  const startScanningAnimation = () => {
    clearDots()
    dotsRef.current = setInterval(() => {
      setScanningDots((prev) => (prev + 1) % 4)
    }, 500)
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0])
    }
  }

  const reset = () => {
    clearPolling()
    clearDots()
    setViewState('IDLE')
    setSelectedFile(null)
    setResult(null)
    setError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatDuration = (seconds: number | null): string => {
    if (seconds === null || seconds === undefined) return '—'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatConfidence = (confidence: number | null): string => {
    if (confidence === null || confidence === undefined) return '—'
    return `${(confidence * 100).toFixed(1)}%`
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center space-x-3">
          <Video className="w-8 h-8" />
          <span>Video Moderation</span>
        </h1>
        <p className="text-gray-400">
          Upload a video to run asynchronous multi-model frame-by-frame moderation.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/30 border border-red-800 rounded-lg flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
          <div>
            <h3 className="text-red-200 font-semibold">Error</h3>
            <p className="text-red-100/80">{error}</p>
          </div>
        </div>
      )}

      {viewState === 'IDLE' && (
        <div
          className={`border-2 border-dashed rounded-xl p-12 text-center transition ${
            dragActive
              ? 'border-white bg-gray-900'
              : 'border-gray-700 hover:border-gray-500 hover:bg-gray-900/50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp4,.avi,.mov,.webm,.mkv,video/*"
            className="hidden"
            onChange={handleInputChange}
          />
          <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <Upload className="w-8 h-8 text-gray-300" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">
            Drag & drop your video here
          </h3>
          <p className="text-gray-400 mb-4">
            or click to browse. Supported formats: MP4, AVI, MOV, WebM, MKV.
          </p>
          <button className="px-6 py-2 bg-white text-black rounded font-medium hover:bg-gray-200 transition">
            Select Video
          </button>
        </div>
      )}

      {viewState === 'PROCESSING' && (
        <div className="border border-gray-800 rounded-xl p-10 text-center bg-black">
          <div className="w-20 h-20 bg-gray-900 rounded-full flex items-center justify-center mx-auto mb-6">
            <Loader2 className="w-10 h-10 text-white animate-spin" />
          </div>
          <h3 className="text-2xl font-semibold text-white mb-2">
            Scanning Video{'.'.repeat(scanningDots)}
          </h3>
          <p className="text-gray-400 mb-6">
            {selectedFile ? selectedFile.name : 'Your video'} is being processed frame by frame.
            This may take a moment.
          </p>

          {result && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl mx-auto text-left">
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <div className="text-gray-400 text-sm mb-1">Status</div>
                <div className="text-white font-medium capitalize">{result.status}</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <div className="text-gray-400 text-sm mb-1">Frames Sampled</div>
                <div className="text-white font-medium">{result.frames_sampled}</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <div className="text-gray-400 text-sm mb-1">Flags Detected</div>
                <div className="text-white font-medium">{result.frames_flagged}</div>
              </div>
            </div>
          )}

          <button
            onClick={reset}
            className="mt-8 px-5 py-2 border border-gray-700 text-gray-300 rounded hover:bg-gray-900 transition"
          >
            Cancel
          </button>
        </div>
      )}

      {viewState === 'COMPLETED' && result && (
        <div className="space-y-6">
          {/* Verdict Card */}
          <div
            className={`rounded-xl p-6 border ${
              result.overall_status === 'unsafe'
                ? 'bg-red-950/30 border-red-800'
                : 'bg-green-950/30 border-green-800'
            }`}
          >
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center space-x-4">
                {result.overall_status === 'unsafe' ? (
                  <AlertCircle className="w-10 h-10 text-red-400" />
                ) : (
                  <CheckCircle className="w-10 h-10 text-green-400" />
                )}
                <div>
                  <h2 className="text-2xl font-bold text-white uppercase">
                    {result.overall_status || 'UNKNOWN'}
                  </h2>
                  <p className="text-gray-300">{result.reason || 'Video moderation complete.'}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-400">Confidence</div>
                <div className="text-3xl font-bold text-white">
                  {formatConfidence(result.overall_confidence)}
                </div>
              </div>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <div className="flex items-center space-x-2 text-gray-400 text-sm mb-1">
                <FileVideo className="w-4 h-4" />
                <span>Filename</span>
              </div>
              <div className="text-white font-medium truncate" title={result.filename}>
                {result.filename}
              </div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <div className="flex items-center space-x-2 text-gray-400 text-sm mb-1">
                <Clock className="w-4 h-4" />
                <span>Duration</span>
              </div>
              <div className="text-white font-medium">{formatDuration(result.total_duration)}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <div className="flex items-center space-x-2 text-gray-400 text-sm mb-1">
                <ScanLine className="w-4 h-4" />
                <span>Frames Sampled</span>
              </div>
              <div className="text-white font-medium">{result.frames_sampled}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
              <div className="flex items-center space-x-2 text-gray-400 text-sm mb-1">
                <ScanLine className="w-4 h-4" />
                <span>Processing Time</span>
              </div>
              <div className="text-white font-medium">
                {result.processing_time !== null && result.processing_time !== undefined
                  ? `${result.processing_time.toFixed(2)}s`
                  : '—'}
              </div>
            </div>
          </div>

          {/* Frame Flags Table */}
          <div className="bg-black border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Flagged Frames</h3>
              <span className="text-sm text-gray-400">
                {result.frame_flags.length} violation{result.frame_flags.length !== 1 ? 's' : ''}
              </span>
            </div>

            {result.frame_flags.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                No policy violations detected in any sampled frame.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-gray-900 text-gray-400 text-sm uppercase">
                    <tr>
                      <th className="px-6 py-3 font-medium">Timestamp (Seconds)</th>
                      <th className="px-6 py-3 font-medium">Flagged Category</th>
                      <th className="px-6 py-3 font-medium">Confidence Score</th>
                      <th className="px-6 py-3 font-medium">Detected Labels</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {result.frame_flags.map((flag) => (
                      <tr key={flag.id} className="hover:bg-gray-900/50">
                        <td className="px-6 py-4 text-white">
                          {flag.timestamp_seconds.toFixed(2)}s
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-red-900/50 text-red-200 border border-red-800 uppercase">
                            {flag.flag_category}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-white">
                          {(flag.confidence * 100).toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 text-gray-300">
                          {flag.detected_labels.length > 0
                            ? flag.detected_labels.join(', ')
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="flex justify-center">
            <button
              onClick={reset}
              className="px-6 py-2 bg-white text-black rounded font-medium hover:bg-gray-200 transition"
            >
              Moderate Another Video
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
