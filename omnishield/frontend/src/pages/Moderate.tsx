import { useState, useRef, useEffect } from 'react'
import { Upload, Image as ImageIcon, AlertCircle, CheckCircle } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { moderationAPI } from '../lib/api'

interface ModerationResult {
  success: boolean
  message: string
  data: {
    decision: string  // 'safe' or 'unsafe'
    risk_level: string
    confidence: number
    detected_labels: string[]
    bounding_boxes: Array<{
      label: string
      box: number[]
      score: number
    }>
    processing_time: number
    recommended_action: string
    reason?: string
    cached: boolean
    categories?: {
      [key: string]: {
        status: string
        confidence: number
        risk_level: string
        detected_labels: string[]
        bounding_boxes: any[]
        reason: string
        model: string
        face_count?: number
        detected_text?: string
        contains_profanity?: boolean
      }
    }
    model_versions?: {
      [key: string]: string
    }
    face_count?: number
    detected_text?: string
    contains_profanity?: string
  }
}

export default function Moderate() {
  const queryClient = useQueryClient()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string>('')
  const [result, setResult] = useState<ModerationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [pipelineSuccess, setPipelineSuccess] = useState(false)
  const [error, setError] = useState('')
  const [scanningStep, setScanningStep] = useState(0)
  const stepTimeoutRefs = useRef<ReturnType<typeof setTimeout>[]>([])
  const successDelayRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const scanningStepRef = useRef(0)

  const CASCADE_STEP_MS = 120
  const REVEAL_DELAY_MS = 400

  const clearPipelineTimers = () => {
    stepTimeoutRefs.current.forEach(clearTimeout)
    stepTimeoutRefs.current = []
    if (successDelayRef.current) {
      clearTimeout(successDelayRef.current)
      successDelayRef.current = null
    }
  }

  useEffect(() => {
    scanningStepRef.current = scanningStep
  }, [scanningStep])

  useEffect(() => () => clearPipelineTimers(), [])

  const scanningSteps = [
    { icon: '⚙️', text: 'INITIALIZING SECURITY PIPELINE', delay: 0 },
    { icon: '🔍', text: 'EXPLICIT CONTENT SCAN', delay: 800 },
    { icon: '🛡️', text: 'CONTEXTUAL SAFETY AUDIT', delay: 1600 },
    { icon: '🎯', text: 'THREAT & WEAPON DETECTION', delay: 2400 },
    { icon: '👤', text: 'BIOMETRIC PRIVACY SCAN', delay: 3200 },
    { icon: '📝', text: 'TEXT & PROFANITY PARSING', delay: 4000 },
    { icon: '✨', text: 'REAL-TIME RISK AGGREGATION', delay: 4800 },
  ]

  const revealResults = (data: ModerationResult) => {
    setResult(data)
    setLoading(false)
    setPipelineSuccess(false)
    setScanningStep(0)
    scanningStepRef.current = 0
  }

  const startCompletionCascade = (data: ModerationResult) => {
    const targetStep = scanningSteps.length + 1
    let step = scanningStepRef.current

    const scheduleReveal = () => {
      setPipelineSuccess(true)
      successDelayRef.current = setTimeout(() => {
        revealResults(data)
        successDelayRef.current = null
      }, REVEAL_DELAY_MS)
    }

    if (step >= targetStep) {
      scheduleReveal()
      return
    }

    const advanceStep = () => {
      step += 1
      setScanningStep(step)
      scanningStepRef.current = step

      if (step < targetStep) {
        const timerId = setTimeout(advanceStep, CASCADE_STEP_MS)
        stepTimeoutRefs.current.push(timerId)
      } else {
        scheduleReveal()
      }
    }

    const timerId = setTimeout(advanceStep, CASCADE_STEP_MS)
    stepTimeoutRefs.current.push(timerId)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setPreview(URL.createObjectURL(file))
      setResult(null)
      setError('')
      setPipelineSuccess(false)
      clearPipelineTimers()
    }
  }

  const handleSubmit = async () => {
    if (!selectedFile) return

    clearPipelineTimers()
    setLoading(true)
    setPipelineSuccess(false)
    setError('')
    setResult(null)
    setScanningStep(0)

    stepTimeoutRefs.current = scanningSteps.map((step, index) =>
      setTimeout(() => setScanningStep(index + 1), step.delay)
    )

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await moderationAPI.moderateComprehensive(formData)

      clearPipelineTimers()

      queryClient.invalidateQueries({ queryKey: ['stats'] })
      queryClient.invalidateQueries({ queryKey: ['timeSeries'] })

      startCompletionCascade(response.data)
    } catch (err: any) {
      clearPipelineTimers()
      setLoading(false)
      setPipelineSuccess(false)
      setScanningStep(0)
      setError(err.response?.data?.detail || 'Moderation failed. Please try again.')
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Image Moderation</h1>
        <p className="text-gray-400">Upload an image to analyze with AI models</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="space-y-6">
          <div className="bg-white text-black rounded-lg p-6 border border-gray-200">
            <h2 className="text-xl font-bold mb-4">Upload Image</h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept="image/*"
                onChange={handleFileSelect}
              />
              
              {!preview ? (
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium mb-2">Click to upload</p>
                  <p className="text-sm text-gray-500">PNG, JPG, WEBP up to 10MB</p>
                </label>
              ) : (
                <div className="relative">
                  <img
                    src={preview}
                    alt="Preview"
                    className="max-h-64 mx-auto rounded mb-4"
                  />
                  
                  {/* Cybersecurity Scanning Overlay */}
                  {loading && (
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm rounded overflow-hidden">
                      {/* Animated Scanning Laser */}
                      <div className="absolute inset-0">
                        <div className="absolute w-full h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent animate-scan-line shadow-[0_0_20px_rgba(34,211,238,0.8)]" 
                             style={{
                               animation: 'scanLine 2s ease-in-out infinite'
                             }}
                        />
                        {/* Grid overlay effect */}
                        <div className="absolute inset-0 bg-[linear-gradient(rgba(34,211,238,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(34,211,238,0.03)_1px,transparent_1px)] bg-[size:20px_20px]" />
                      </div>
                      
                      {/* Corner brackets */}
                      <div className="absolute top-2 left-2 w-8 h-8 border-t-2 border-l-2 border-cyan-400"></div>
                      <div className="absolute top-2 right-2 w-8 h-8 border-t-2 border-r-2 border-cyan-400"></div>
                      <div className="absolute bottom-2 left-2 w-8 h-8 border-b-2 border-l-2 border-cyan-400"></div>
                      <div className="absolute bottom-2 right-2 w-8 h-8 border-b-2 border-r-2 border-cyan-400"></div>
                      
                      {/* Scanning Status */}
                      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
                        <div className={`bg-black/80 backdrop-blur-md rounded-lg px-6 py-4 border shadow-[0_0_30px_rgba(34,211,238,0.3)] transition-colors duration-300 ${
                          pipelineSuccess
                            ? 'border-emerald-500/50 shadow-[0_0_30px_rgba(16,185,129,0.35)]'
                            : 'border-cyan-500/50'
                        }`}>
                          <div className={`flex items-center space-x-2 transition-colors duration-300 ${
                            pipelineSuccess ? 'text-emerald-400' : 'text-cyan-400'
                          }`}>
                            <div className={`w-2 h-2 rounded-full ${
                              pipelineSuccess
                                ? 'bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.8)]'
                                : 'bg-cyan-400 animate-pulse shadow-[0_0_10px_rgba(34,211,238,0.8)]'
                            }`}></div>
                            <span className="text-sm font-mono font-bold tracking-wider">
                              {pipelineSuccess ? 'PIPELINE COMPLETE' : 'SCANNING IN PROGRESS'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {!loading && (
                    <button
                      onClick={() => {
                        setSelectedFile(null)
                        setPreview('')
                        setResult(null)
                      }}
                      className="text-sm text-gray-600 hover:text-black"
                    >
                      Change Image
                    </button>
                  )}
                </div>
              )}
            </div>

            {selectedFile && !result && (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full mt-4 bg-black text-white py-3 rounded font-medium hover:bg-gray-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Analyzing...</span>
                  </span>
                ) : (
                  'Analyze Image'
                )}
              </button>
            )}

            {/* AI Model Progress Checklist */}
            {loading && (
              <div className="mt-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg p-6 border border-cyan-500/30 shadow-[0_0_30px_rgba(34,211,238,0.15)]">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white font-bold text-sm uppercase tracking-widest flex items-center">
                    <span className={`w-2 h-2 rounded-full mr-2 ${
                      pipelineSuccess
                        ? 'bg-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.8)]'
                        : 'bg-cyan-400 animate-pulse shadow-[0_0_10px_rgba(34,211,238,0.8)]'
                    }`}></span>
                    AI Pipeline Status
                  </h3>
                  <div className={`text-xs font-mono font-bold transition-colors duration-300 ${
                    pipelineSuccess
                      ? 'text-emerald-400'
                      : 'text-cyan-400 animate-pulse'
                  }`}>
                    {pipelineSuccess ? 'COMPLETE' : 'LIVE'}
                  </div>
                </div>
                
                <div className="space-y-3">
                  {scanningSteps.map((step, index) => {
                    const isComplete = pipelineSuccess || scanningStep > index + 1
                    const isActive = !pipelineSuccess && scanningStep === index + 1
                    
                    return (
                      <div
                        key={index}
                        className={`flex items-start space-x-3 transition-all duration-150 ease-out ${
                          isComplete || isActive ? 'opacity-100 blur-0' : 'opacity-30 blur-[0.5px]'
                        }`}
                      >
                        <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs transition-all duration-150 ease-out ${
                          isComplete 
                            ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 scale-100' 
                            : isActive
                            ? 'bg-cyan-500/20 border border-cyan-500/50 text-cyan-400 animate-pulse scale-105'
                            : 'bg-slate-700/50 border border-slate-600/50 text-slate-500 scale-95'
                        }`}>
                          {isComplete ? '✓' : isActive ? step.icon : '○'}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-mono leading-tight tracking-wide transition-colors duration-300 ${
                            isComplete
                              ? 'text-emerald-300 font-semibold'
                              : isActive 
                              ? 'text-cyan-300 font-bold animate-pulse' 
                              : 'text-slate-500'
                          }`}>
                            {step.text}
                          </p>
                          
                          {/* Progress bar for active step */}
                          {isActive && (
                            <div className="mt-1.5 w-full h-1 bg-slate-700/50 rounded-full overflow-hidden">
                              <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 animate-pulse shadow-[0_0_10px_rgba(34,211,238,0.5)]" 
                                   style={{
                                     animation: 'progressBar 2s ease-in-out infinite',
                                     width: '70%'
                                   }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
                
                {/* Bottom metrics */}
                <div className="mt-4 pt-4 border-t border-slate-700/50 grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className={`text-2xl font-bold font-mono tabular-nums transition-all duration-150 ${
                      pipelineSuccess ? 'text-emerald-400' : 'text-cyan-400'
                    }`}>
                      {pipelineSuccess
                        ? scanningSteps.length
                        : Math.max(0, Math.min(scanningStep - 1, scanningSteps.length))}
                    </div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider mt-1">Models Complete</div>
                  </div>
                  <div>
                    <div className={`text-2xl font-bold font-mono tabular-nums transition-all duration-150 ${
                      pipelineSuccess ? 'text-emerald-400' : 'text-green-400'
                    }`}>
                      {pipelineSuccess
                        ? '100'
                        : Math.round(
                            (Math.max(0, Math.min(scanningStep - 1, scanningSteps.length)) /
                              scanningSteps.length) *
                              100
                          )}%
                    </div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider mt-1">Complete</div>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
                {error}
              </div>
            )}
          </div>

          {result && (
            <div className={`rounded-lg p-6 border ${
              result.data.decision === 'safe'
                ? 'bg-white text-black border-gray-200' 
                : 'bg-gray-900 text-white border-gray-700'
            }`}>
              <div className="flex items-center space-x-3 mb-4">
                {result.data.decision === 'safe' ? (
                  <CheckCircle className="w-8 h-8 text-green-600" />
                ) : (
                  <AlertCircle className="w-8 h-8 text-red-600" />
                )}
                <div>
                  <h3 className="text-xl font-bold">
                    {result.data.decision === 'safe' ? 'Safe Content' : 'Unsafe Content'}
                  </h3>
                  <p className="text-sm opacity-70">
                    Processed in {result.data.processing_time.toFixed(2)}s
                    {result.data.cached && ' (Cached)'}
                  </p>
                </div>
              </div>
              
              <div className="mt-4 space-y-2">
                <div className="flex justify-between">
                  <span className="font-medium">Risk Level:</span>
                  <span className={`font-bold ${
                    result.data.risk_level === 'critical' ? 'text-red-600' :
                    result.data.risk_level === 'high' ? 'text-orange-600' :
                    result.data.risk_level === 'medium' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {result.data.risk_level.toUpperCase()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Confidence:</span>
                  <span>{(result.data.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Action:</span>
                  <span className="font-bold">{result.data.recommended_action.toUpperCase()}</span>
                </div>
                {result.data.reason && (
                  <div className="mt-2 pt-2 border-t">
                    <p className="text-sm opacity-70">{result.data.reason}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {result && result.data.categories && (
            <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
              <h2 className="text-xl font-bold text-white mb-6">Multi-Model Detection Results</h2>
              
              <div className="grid grid-cols-1 gap-4">
                {Object.entries(result.data.categories).map(([categoryKey, categoryData]) => {
                  const categoryName = categoryKey.charAt(0).toUpperCase() + categoryKey.slice(1)
                  const isUnsafe = categoryData?.status === 'unsafe'
                  const isSafe = categoryData?.status === 'safe'
                  const isSkipped = categoryData?.status === 'skipped'
                  const isError = categoryData?.status === 'error'
                  
                  // Skip rendering error or skipped models
                  if (isSkipped || isError) return null
                  
                  return (
                    <div
                      key={categoryKey}
                      className="bg-slate-800/60 backdrop-blur rounded-xl p-5 border border-slate-700/50 hover:border-slate-600 transition-all duration-200"
                    >
                      {/* Header */}
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base font-bold text-white uppercase tracking-wider">
                          {categoryName} Detection
                        </h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm ${
                          isSafe
                            ? 'bg-green-500/20 text-green-300 border border-green-500/40'
                            : isUnsafe
                            ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                            : 'bg-gray-500/20 text-gray-300 border border-gray-500/40'
                        }`}>
                          {categoryData?.status || 'unknown'}
                        </span>
                      </div>

                      {/* Confidence Bar */}
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wide">Confidence</span>
                          <span className="text-sm font-bold text-white tabular-nums">
                            {((categoryData?.confidence || 0) * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full h-2.5 bg-slate-700/50 rounded-full overflow-hidden shadow-inner">
                          <div
                            className={`h-full transition-all duration-700 ease-out shadow-lg ${
                              isUnsafe 
                                ? 'bg-gradient-to-r from-red-600 to-red-500' 
                                : 'bg-gradient-to-r from-green-600 to-green-500'
                            }`}
                            style={{ width: `${(categoryData?.confidence || 0) * 100}%` }}
                          />
                        </div>
                      </div>

                      {/* Risk Level */}
                      {categoryData?.risk_level && categoryData.risk_level !== 'low' && (
                        <div className="mb-3 flex items-center justify-between bg-slate-900/50 rounded-lg px-3 py-2 border border-slate-700/30">
                          <span className="text-xs text-slate-400 font-medium uppercase tracking-wide">Risk Level</span>
                          <span className={`text-xs font-bold uppercase tracking-wider ${
                            categoryData.risk_level === 'critical' ? 'text-red-400' :
                            categoryData.risk_level === 'high' ? 'text-orange-400' :
                            categoryData.risk_level === 'medium' ? 'text-yellow-400' :
                            'text-green-400'
                          }`}>
                            {categoryData.risk_level}
                          </span>
                        </div>
                      )}

                      {/* Detected Labels */}
                      {categoryData?.detected_labels && categoryData.detected_labels.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wide">Detected:</p>
                          <ul className="space-y-1.5">
                            {categoryData.detected_labels.map((label, idx) => (
                              <li
                                key={idx}
                                className="flex items-center text-sm"
                              >
                                <span className="w-1.5 h-1.5 bg-slate-500 rounded-full mr-2"></span>
                                <span className="text-slate-200 font-medium">{label}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Special: Face Count */}
                      {categoryKey === 'faces' && categoryData?.face_count !== undefined && (
                        <div className="flex items-center justify-between bg-slate-900/50 rounded-lg px-3 py-2 border border-slate-700/30">
                          <span className="text-xs text-slate-400 font-medium">Faces Detected</span>
                          <span className="text-lg font-bold text-white tabular-nums">{categoryData.face_count}</span>
                        </div>
                      )}

                      {/* Special: Text Detection */}
                      {categoryKey === 'text' && categoryData?.detected_text && (
                        <div className="mt-3 pt-3 border-t border-slate-700/50">
                          <p className="text-xs text-slate-400 mb-2 font-semibold uppercase tracking-wide">Extracted Text:</p>
                          <div className="bg-slate-900/70 p-3 rounded-lg border border-slate-700/40">
                            <p className="text-sm text-slate-200 font-mono leading-relaxed break-words">
                              {categoryData.detected_text}
                            </p>
                          </div>
                          {categoryData?.contains_profanity && (
                            <div className="mt-2 flex items-center text-xs text-red-400">
                              <span className="mr-1">⚠</span>
                              <span className="font-semibold">Contains inappropriate language</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Model Info Footer */}
                      <div className="mt-3 pt-3 border-t border-slate-700/30">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-500 uppercase tracking-wide">Model</span>
                          <span className="text-xs text-slate-400 font-mono">
                            {categoryData?.model || 'unknown'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {!result && (
            <div className="bg-white text-black rounded-lg p-12 border border-gray-200 text-center">
              <ImageIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600 font-medium">
                Upload an image to see moderation results
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
