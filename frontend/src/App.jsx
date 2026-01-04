import { useState } from 'react'
import axios from 'axios'

function App() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState('')
  const [audioBase64, setAudioBase64] = useState('')
  const [error, setError] = useState('')

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSummary('')
    setAudioBase64('')
    
    if (!url.trim()) {
      setError('Please enter a YouTube URL')
      return
    }

    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/api/summarize`, {
        url: url.trim()
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      })

      setSummary(response.data.summary)
      setAudioBase64(response.data.audio_base64)
    } catch (err) {
      console.error('Error:', err)
      if (err.response) {
        // FastAPI returns error details in response.data.detail
        const errorDetail = err.response.data?.detail || err.response.data?.message || err.response.data?.error || 'An error occurred while processing the video'
        setError(errorDetail)
        console.error('Error details:', err.response.data)
      } else if (err.request) {
        setError('Unable to connect to the server. Please check if the backend is running.')
      } else {
        setError('An unexpected error occurred: ' + (err.message || 'Unknown error'))
      }
    } finally {
      setLoading(false)
    }
  }

  const audioSrc = audioBase64 ? `data:audio/mp3;base64,${audioBase64}` : null

  return (
    <main className="container-main">
      <div className="hero-section">
        <h1 className="hero-title">Voxo</h1>
        <p className="hero-subtitle">
          Transform YouTube videos into concise summaries with AI-powered text-to-speech
        </p>
      </div>

      <div className="search-container">
        <form onSubmit={handleSubmit}>
          <div className="input-group input-group-lg">
            <input
              type="text"
              className="form-control"
              placeholder="Enter YouTube URL..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
            />
            <button
              className="btn btn-light"
              type="submit"
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Summarize'}
            </button>
          </div>
        </form>

        {error && (
          <div className="alert alert-danger mt-3" role="alert">
            {error}
          </div>
        )}
      </div>

      {loading && (
        <div className="spinner-container">
          <div className="spinner-border spinner-border-custom text-light" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p>Processing your video... This may take a moment.</p>
        </div>
      )}

      {summary && (
        <div className="result-container">
          <h2 className="mb-4">Summary</h2>
          <div className="summary-content">
            {summary}
          </div>

          {audioSrc && (
            <div className="audio-player-container">
              <h5 className="mb-3">Audio Summary</h5>
              <audio
                className="audio-player"
                controls
                autoPlay
                src={audioSrc}
              >
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
        </div>
      )}
    </main>
  )
}

export default App

