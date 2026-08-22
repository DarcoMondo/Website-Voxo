import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

// Flag shown next to each language in the picker. Purely cosmetic — the
// backend only knows language codes, not flags, so this stays on the
// frontend. Falls back to a globe if a new language is added server-side
// before this map is updated.
const FLAGS = {
  it: '🇮🇹',
  en: '🇬🇧',
  es: '🇪🇸',
  fr: '🇫🇷',
  de: '🇩🇪',
  pt: '🇵🇹',
  nl: '🇳🇱',
  pl: '🇵🇱',
  ru: '🇷🇺',
  ja: '🇯🇵',
  ko: '🇰🇷',
  zh: '🇨🇳',
  hi: '🇮🇳',
  ar: '🇸🇦',
  tr: '🇹🇷',
}

function ChevronIcon() {
  return (
    <svg className="lang-chevron" width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path d="M2.5 4.5L6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// Trigger shows the language's name (not just its code) so it's clear on
// its own what picking it does. Fully keyboard-operable: arrow keys move
// between options, Home/End jump to the ends, Escape closes and returns
// focus to the trigger — the pattern screen reader and keyboard users
// expect from a listbox.
function LanguagePicker({ language, languages, onChange, disabled }) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)
  const triggerRef = useRef(null)
  const optionRefs = useRef([])

  const closeAndRefocusTrigger = () => {
    setIsOpen(false)
    triggerRef.current?.focus()
  }

  useEffect(() => {
    function handleClickOutside(e) {
      if (!containerRef.current?.contains(e.target)) setIsOpen(false)
    }
    function handleEscape(e) {
      if (e.key === 'Escape') closeAndRefocusTrigger()
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  // Move focus into the list when it opens, landing on the current selection.
  useEffect(() => {
    if (!isOpen) return
    const selectedIndex = Math.max(0, languages.findIndex((lang) => lang.code === language))
    optionRefs.current[selectedIndex]?.focus()
  }, [isOpen])

  // Options use tabIndex={-1} (focusable only programmatically, via arrow
  // keys below) so they aren't individual Tab stops — pressing Tab just
  // closes the panel and lets focus continue naturally to whatever comes
  // after the picker, instead of tabbing through every language first.
  const handleOptionKeyDown = (e, index) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      optionRefs.current[(index + 1) % languages.length]?.focus()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      optionRefs.current[(index - 1 + languages.length) % languages.length]?.focus()
    } else if (e.key === 'Home') {
      e.preventDefault()
      optionRefs.current[0]?.focus()
    } else if (e.key === 'End') {
      e.preventDefault()
      optionRefs.current[languages.length - 1]?.focus()
    } else if (e.key === 'Tab') {
      setIsOpen(false)
    }
  }

  const flag = FLAGS[language] || '🌐'
  const selected = languages.find((lang) => lang.code === language)

  return (
    <div className="lang-picker" ref={containerRef}>
      <button
        ref={triggerRef}
        type="button"
        id="lang-trigger-btn"
        className="lang-trigger"
        onClick={() => setIsOpen((open) => !open)}
        disabled={disabled || languages.length === 0}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-labelledby="lang-field-label lang-trigger-btn"
      >
        <span className="lang-flag" aria-hidden="true">{flag}</span>
        <span className="lang-trigger-name">{selected ? selected.name : language.toUpperCase()}</span>
        <ChevronIcon />
      </button>

      {isOpen && (
        <div className="lang-panel" role="listbox" aria-labelledby="lang-field-label">
          {languages.map((lang, index) => (
            <button
              type="button"
              key={lang.code}
              ref={(el) => (optionRefs.current[index] = el)}
              tabIndex={-1}
              className="lang-option"
              role="option"
              aria-selected={lang.code === language}
              onClick={() => {
                onChange(lang.code)
                closeAndRefocusTrigger()
              }}
              onKeyDown={(e) => handleOptionKeyDown(e, index)}
            >
              <span className="lang-flag" aria-hidden="true">{FLAGS[lang.code] || '🌐'}</span>
              <span className="lang-option-name">{lang.name}</span>
              <span className="lang-option-code">{lang.code.toUpperCase()}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function App() {
  const [url, setUrl] = useState('')
  const [language, setLanguage] = useState('en')
  const [languages, setLanguages] = useState([])
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState('')
  const [audioBase64, setAudioBase64] = useState('')
  const [error, setError] = useState('')
  const [languagesError, setLanguagesError] = useState(false)
  const urlInputRef = useRef(null)

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Fetch the supported languages from the backend instead of hardcoding
  // them here, so the picker always matches what the API can actually
  // summarize and synthesize (single source of truth: SUPPORTED_LANGUAGES
  // in backend/main.py). Sorted alphabetically by display name for the
  // dropdown, since the backend's order is just insertion order.
  const loadLanguages = () => {
    setLanguagesError(false)
    axios.get(`${API_URL}/api/languages`)
      .then((res) => {
        const sorted = [...res.data.languages].sort((a, b) => a.name.localeCompare(b.name))
        setLanguages(sorted)
      })
      .catch((err) => {
        console.error('Failed to load languages:', err)
        setLanguagesError(true)
      })
  }

  useEffect(() => {
    loadLanguages()
  }, [])

  // Runs after a summary lands and the form is re-enabled (loading is only
  // set back to false once this render commits). Clears the URL and hands
  // focus back to it so pasting the next link is obvious — the language
  // stays as picked, since there's no reason to reset it.
  useEffect(() => {
    if (!summary) return
    setUrl('')
    urlInputRef.current?.focus()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [summary])

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
        url: url.trim(),
        language
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
    <main className="page">
      <div className="brand">voxo<span className="dot">.</span></div>

      <h1 className="intro-title">YouTube video, summarized.</h1>
      <p className="intro-subtitle">
        Pick a language, paste a link, get a summary back — written and narrated.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="lang-field">
          <span className="lang-field-label" id="lang-field-label">Summarize in</span>
          <LanguagePicker
            language={language}
            languages={languages}
            onChange={setLanguage}
            disabled={loading}
          />
        </div>

        {languagesError && (
          <p className="lang-error">
            Couldn't load languages.{' '}
            <button type="button" className="lang-retry" onClick={loadLanguages}>Retry</button>
          </p>
        )}

        <label htmlFor="url-input" className="sr-only">YouTube video URL</label>
        <input
          ref={urlInputRef}
          id="url-input"
          type="text"
          className="url-input"
          placeholder="https://www.youtube.com/watch?v=..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading}
        />

        <button className="submit-btn" type="submit" disabled={loading}>
          {loading ? 'Working…' : 'Summarize'}
        </button>
      </form>

      {loading && (
        <div className="status-row" role="status" aria-live="polite">
          <span className="dot-pulse" aria-hidden="true"><span /><span /><span /></span>
          <span>Fetching the transcript and generating your summary</span>
        </div>
      )}

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      {summary && (
        <div className="result">
          {audioSrc && (
            <div className="audio-section">
              <h3 className="eyebrow">Listen</h3>
              <audio className="audio-player" controls autoPlay src={audioSrc}>
                Your browser does not support the audio element.
              </audio>
            </div>
          )}

          <h2 className="eyebrow">Summary</h2>
          <div className="summary-content">{summary}</div>
        </div>
      )}
    </main>
  )
}

export default App
