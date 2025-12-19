'use client'

import { useState, useEffect } from 'react'
import { Database, Activity, TrendingUp, AlertCircle } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export default function Home() {
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [vitals, setVitals] = useState<any>(null)
  const [metrics, setMetrics] = useState<any[]>([])
  const [connection, setConnection] = useState({
    host: 'localhost',
    port: 3306,
    user: 'root',
    password: '',
    database: 'mysql'
  })

  useEffect(() => {
    checkConnectionStatus()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const checkConnectionStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/connection/status`)
      const data = await res.json()
      setConnected(data.connected)
      if (data.connected) {
        fetchVitals()
        fetchMetrics()
      }
    } catch (error) {
      console.error('Failed to check connection:', error)
    }
  }

  const handleConnect = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/connection/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(connection)
      })

      if (res.ok) {
        setConnected(true)
        fetchVitals()
        fetchMetrics()
      } else {
        const error = await res.json()
        alert(`Connection failed: ${error.detail}`)
      }
    } catch (error) {
      alert(`Connection failed: ${error}`)
    }
    setLoading(false)
  }

  const fetchVitals = async () => {
    try {
      const res = await fetch(`${API_URL}/api/metrics/vitals`)
      const data = await res.json()
      if (data.success) {
        setVitals(data.data)
      }
    } catch (error) {
      console.error('Failed to fetch vitals:', error)
    }
  }

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`${API_URL}/api/metrics/queries?limit=10`)
      const data = await res.json()
      if (data.success) {
        setMetrics(data.data.metrics)
      }
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Database className="w-10 h-10 text-blue-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              MySQLens
            </h1>
          </div>
          <p className="text-slate-600 dark:text-slate-400">
            AI-powered MySQL performance optimization tool
          </p>
        </div>

        {/* Connection Status Card */}
        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Connection Status
            </h2>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
              {connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          {!connected && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Host"
                className="px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600"
                value={connection.host}
                onChange={(e) => setConnection({ ...connection, host: e.target.value })}
              />
              <input
                type="number"
                placeholder="Port"
                className="px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600"
                value={connection.port}
                onChange={(e) => setConnection({ ...connection, port: parseInt(e.target.value) })}
              />
              <input
                type="text"
                placeholder="Username"
                className="px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600"
                value={connection.user}
                onChange={(e) => setConnection({ ...connection, user: e.target.value })}
              />
              <input
                type="password"
                placeholder="Password"
                className="px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600"
                value={connection.password}
                onChange={(e) => setConnection({ ...connection, password: e.target.value })}
              />
              <input
                type="text"
                placeholder="Database"
                className="px-4 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 md:col-span-2"
                value={connection.database}
                onChange={(e) => setConnection({ ...connection, database: e.target.value })}
              />
              <button
                onClick={handleConnect}
                disabled={loading}
                className="md:col-span-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Connecting...' : 'Connect to MySQL'}
              </button>
            </div>
          )}
        </div>

        {/* Vitals Dashboard */}
        {connected && vitals && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-400">QPS</span>
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              <div className="text-3xl font-bold">{vitals.qps?.value || 0}</div>
              <div className="text-sm text-slate-500 mt-1">Queries per second</div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-400">Buffer Pool</span>
                <Activity className="w-5 h-5 text-green-600" />
              </div>
              <div className="text-3xl font-bold">
                {vitals.buffer_pool_hit_ratio?.value?.toFixed(1) || 'N/A'}%
              </div>
              <div className="text-sm text-slate-500 mt-1">Hit ratio</div>
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-600 dark:text-slate-400">Connections</span>
                <Database className="w-5 h-5 text-purple-600" />
              </div>
              <div className="text-3xl font-bold">
                {vitals.active_connections?.value || 0} / {vitals.max_connections?.value || 0}
              </div>
              <div className="text-sm text-slate-500 mt-1">Active / Max</div>
            </div>
          </div>
        )}

        {/* Top Queries */}
        {connected && metrics.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              Top Slow Queries
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b dark:border-slate-700">
                    <th className="text-left py-3 px-4">Query</th>
                    <th className="text-right py-3 px-4">Executions</th>
                    <th className="text-right py-3 px-4">Avg Time (ms)</th>
                    <th className="text-right py-3 px-4">Total Time (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((metric, idx) => (
                    <tr key={idx} className="border-b dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-750">
                      <td className="py-3 px-4 font-mono text-sm truncate max-w-md">
                        {metric.digest_text.substring(0, 80)}...
                      </td>
                      <td className="py-3 px-4 text-right">{metric.count_star.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right">{metric.avg_timer_wait_ms.toFixed(2)}</td>
                      <td className="py-3 px-4 text-right font-semibold">{metric.sum_timer_wait_ms.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-slate-600 dark:text-slate-400 text-sm">
          <p>Built with ❤️ for the MySQL Community</p>
        </div>
      </div>
    </div>
  )
}
