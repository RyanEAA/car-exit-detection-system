import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'
const TOKEN_KEY = 'car-exit-token'
const USER_KEY = 'car-exit-user'

type User = {
  id: number
  username: string
  is_admin: boolean
  created_at: string
}

type AuthResponse = {
  access_token: string
  token_type: string
  user: User
}

type DetectionRecord = {
  id: number
  user_id: number
  image_path: string
  original_filename: string | null
  media_type: string
  is_car: boolean
  view: string | null
  license_plate: string | null
  exit_date: string
  exit_time: string
  captured_at: string
}

type DetectionResponse = {
  is_car: boolean
  view?: string
  license_plate?: string | null
  media_type?: string
  record?: {
    id: number
    image_url: string
    captured_at: string
    exit_date: string
    exit_time: string
  }
}

type HistoryItem = {
  detection: DetectionRecord
  image_url: string
  media_type: string
}

type HistoryResponse = {
  items: HistoryItem[]
}

type AuthMode = 'login' | 'register'

function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<User | null>(() => {
    const storedUser = localStorage.getItem(USER_KEY)
    return storedUser ? (JSON.parse(storedUser) as User) : null
  })
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [authMessage, setAuthMessage] = useState<string | null>(null)

  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [previewKind, setPreviewKind] = useState<'image' | 'video' | null>(null)
  const [result, setResult] = useState<DetectionResponse | null>(null)
  const [detectionBusy, setDetectionBusy] = useState(false)
  const [detectionMessage, setDetectionMessage] = useState<string | null>(null)

  const [history, setHistory] = useState<HistoryItem[]>([])
  const [historyBusy, setHistoryBusy] = useState(false)
  const [historyMessage, setHistoryMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!preview) {
      return undefined
    }

    return () => URL.revokeObjectURL(preview)
  }, [preview])

  useEffect(() => {
    if (!token) {
      setUser(null)
      setHistory([])
      return
    }

    void loadHistory(token)
  }, [token])

  const apiFetch = async (path: string, init: RequestInit = {}, bearerToken = token) => {
    const headers = new Headers(init.headers ?? {})

    if (bearerToken) {
      headers.set('Authorization', `Bearer ${bearerToken}`)
    }

    if (init.body && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }

    return fetch(`${API_URL}${path}`, {
      ...init,
      headers,
    })
  }

  const loadHistory = async (bearerToken = token) => {
    if (!bearerToken) return

    setHistoryBusy(true)
    setHistoryMessage(null)

    try {
      const response = await apiFetch('/history/', { method: 'GET' }, bearerToken)
      if (!response.ok) {
        throw new Error('Unable to load detection history')
      }

      const data: HistoryResponse = await response.json()
      setHistory(data.items)
    } catch (error) {
      setHistoryMessage(error instanceof Error ? error.message : 'Unable to load detection history')
    } finally {
      setHistoryBusy(false)
    }
  }

  const handleAuthSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAuthBusy(true)
    setAuthMessage(null)

    try {
      const response = await apiFetch(
        authMode === 'login' ? '/auth/login' : '/auth/register',
        {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        },
        undefined,
      )

      if (!response.ok) {
        const errorBody = (await response.json().catch(() => null)) as { detail?: string } | null
        throw new Error(errorBody?.detail ?? 'Authentication failed')
      }

      const data: AuthResponse = await response.json()
      setToken(data.access_token)
      setUser(data.user)
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      setPassword('')
      setAuthMessage(null)
    } catch (error) {
      setAuthMessage(error instanceof Error ? error.message : 'Authentication failed')
    } finally {
      setAuthBusy(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
    setResult(null)
    setHistory([])
    setImage(null)
    setPreview(null)
    setPreviewKind(null)
  }

  const handleImageChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null
    setImage(file)

    if (preview) {
      URL.revokeObjectURL(preview)
    }

    const isVideo = file ? file.type.startsWith('video/') : false
    setPreviewKind(file ? (isVideo ? 'video' : 'image') : null)
    setPreview(file ? URL.createObjectURL(file) : null)
  }

  const handleUpload = async () => {
    if (!image || !token) return

    setDetectionBusy(true)
    setDetectionMessage(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', image)

    try {
      const response = await fetch(`${API_URL}/detect/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const errorBody = (await response.json().catch(() => null)) as { detail?: string } | null
        throw new Error(errorBody?.detail ?? 'Detection failed')
      }

      const data: DetectionResponse = await response.json()
      setResult(data)
      await loadHistory(token)
    } catch (error) {
      setDetectionMessage(error instanceof Error ? error.message : 'Detection failed')
    } finally {
      setDetectionBusy(false)
      setImage(null)
      setPreview(null)
      setPreviewKind(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const historyCards = history.map((entry) => (
    <article key={entry.detection.id} className="history-card">
      {entry.media_type === 'video' ? (
        <video controls preload="metadata" src={`${API_URL}${entry.image_url}`} />
      ) : (
        <img src={`${API_URL}${entry.image_url}`} alt="Saved detection" />
      )}
      <div>
        <p className="eyebrow">
          {entry.detection.exit_date} · {entry.detection.exit_time}
        </p>
        <h3>{entry.detection.license_plate ?? 'No plate detected'}</h3>
        <p>{entry.detection.is_car ? 'Car detected' : 'No car detected'}</p>
        <p>{entry.detection.view ?? 'View unavailable'}</p>
      </div>
    </article>
  ))

  if (!token) {
    return (
      <main className="auth-shell">
        <section className="auth-panel">
          <div className="brand-block">
            <span className="brand-mark">CE</span>
            <div>
              <p className="eyebrow">Car exit monitoring</p>
              <h1>Secure detection history for authorized users.</h1>
            </div>
          </div>

          <p className="lede">
            Log in to record exit detections, store image or video evidence, and review car history by date and time.
          </p>

          <form className="auth-form" onSubmit={handleAuthSubmit}>
            <div className="segmented-control">
              <button
                type="button"
                className={authMode === 'login' ? 'active' : ''}
                onClick={() => setAuthMode('login')}
              >
                Log in
              </button>
              <button
                type="button"
                className={authMode === 'register' ? 'active' : ''}
                onClick={() => setAuthMode('register')}
              >
                Register
              </button>
            </div>

            <label>
              Username
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
                required
              />
            </label>

            {authMessage && <p className="message error">{authMessage}</p>}

            <button className="primary-button" type="submit" disabled={authBusy}>
              {authBusy ? 'Working...' : authMode === 'login' ? 'Log in' : 'Create account'}
            </button>
          </form>
        </section>
      </main>
    )
  }

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Logged in as</p>
          <h1>{user?.username ?? 'Authorized user'}</h1>
        </div>

        <button className="ghost-button" type="button" onClick={handleLogout}>
          Sign out
        </button>
      </header>

      <section className="dashboard-grid">
        <section className="panel accent-panel">
          <p className="eyebrow">Detection</p>
          <h2>Upload an exit image</h2>
          <p className="lede">
            The system records the result, timestamp, image path, and plate data for the current user.
          </p>

          <input ref={fileInputRef} type="file" accept="image/*,video/*" onChange={handleImageChange} />

          {preview && (
            <div className="preview-frame">
              {previewKind === 'video' ? (
                <video controls src={preview} />
              ) : (
                <img src={preview} alt="Upload preview" />
              )}
            </div>
          )}

          <button className="primary-button" type="button" onClick={handleUpload} disabled={!image || detectionBusy}>
            {detectionBusy ? 'Recording...' : 'Run detection'}
          </button>

          {detectionMessage && <p className="message error">{detectionMessage}</p>}

          {result && (
            <div className="result-card">
              <p className="eyebrow">Latest result</p>
              <p><strong>Car detected:</strong> {result.is_car ? 'Yes' : 'No'}</p>
              <p><strong>View:</strong> {result.view ?? 'N/A'}</p>
              <p><strong>Plate:</strong> {result.license_plate ?? 'Not detected'}</p>
              <p><strong>Media:</strong> {result.media_type ?? 'image'}</p>
              {result.record && (
                <p><strong>Recorded:</strong> {result.record.exit_date} at {result.record.exit_time}</p>
              )}
            </div>
          )}
        </section>

        <section className="panel history-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">History</p>
              <h2>Saved exit detections</h2>
            </div>

            <button className="ghost-button" type="button" onClick={() => void loadHistory()} disabled={historyBusy}>
              Refresh
            </button>
          </div>

          {historyMessage && <p className="message error">{historyMessage}</p>}

          <div className="history-list">
            {historyBusy && <p>Loading history...</p>}
            {!historyBusy && historyCards}
            {!historyBusy && history.length === 0 && <p>No saved detections yet.</p>}
          </div>
        </section>
      </section>
    </main>
  )
}

export default App