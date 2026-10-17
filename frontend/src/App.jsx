import { useEffect, useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.DEV
  ? 'http://10.9.1.21:8020'
  : 'https://matchpointai-kerrya0412-dfhucvdjgkerhth6.westus3-01.azurewebsites.net'
function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [expandedMomentId, setExpandedMomentId] = useState(null)
  const [selectedPitchEvent, setSelectedPitchEvent] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSeconds, setPlaybackSeconds] = useState(0)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [goalCelebration, setGoalCelebration] = useState(null)
  const [replayGoal, setReplayGoal] = useState(null)
  const [replayEvents, setReplayEvents] = useState([])
  const [replayStep, setReplayStep] = useState(0)
  const previousPlaybackSeconds = useRef(0)
  const [livePulse, setLivePulse] = useState(null)
  const [liveCommentary, setLiveCommentary] = useState([])
  const [voiceCommentaryEnabled, setVoiceCommentaryEnabled] = useState(false)
  const [commentaryVoice, setCommentaryVoice] = useState('professional')
  const lastSpokenEventId = useRef(null)
  const azureAudioRef = useRef(null)
  const speechRequestRef = useRef(null)
  const [analystData, setAnalystData] = useState(null)
  const [tacticalData, setTacticalData] = useState(null)
  const [selectedAudience, setSelectedAudience] = useState('analyst')
  const [storytellerData, setStorytellerData] = useState(null)
  const [askChatOpen, setAskChatOpen] = useState(false)
  const [askQuestion, setAskQuestion] = useState('')
  const [askMessages, setAskMessages] = useState([])
  const [askLoading, setAskLoading] = useState(false)
  const [askError, setAskError] = useState(null)
  const askGeneration = useRef(0)

  const startGoalReplay = (goal) => {
    if (!data || !goal?.possession_id) return

    const sequence = data.events
      .filter((event) =>
        event.possession_id === goal.possession_id &&
        event.team_id === goal.team_id &&
        event.minute * 60 + event.second <=
          goal.minute * 60 + goal.second
      )
      .sort((a, b) =>
        (a.minute * 60 + a.second) -
        (b.minute * 60 + b.second)
      )

    if (!sequence.some((event) => event.event_id === goal.event_id)) return

    setReplayGoal(goal)
    setReplayEvents(sequence)
    setReplayStep(0)
  }

  useEffect(() => {
    if (!replayGoal || replayEvents.length === 0) return
    if (replayStep >= replayEvents.length - 1) return

    const timer = setTimeout(() => {
      setReplayStep((current) => current + 1)
    }, 1200)

    return () => clearTimeout(timer)
  }, [replayGoal, replayEvents, replayStep])

  useEffect(() => {
    if (!data) return

    const commentaryTypes = [
      'goal',
      'shot_on_target',
      'shot',
      'progressive_pass',
      'penalty_area_entry',
      'save',
      'yellow_card',
      'red_card',
    ]

    const messages = data.events
      .filter((event) =>
        commentaryTypes.includes(event.event_type) &&
        event.minute * 60 + event.second <= playbackSeconds
      )
      .sort((a, b) =>
        (a.minute * 60 + a.second) -
        (b.minute * 60 + b.second)
      )
      .map((event) => {
        const team = event.team_name || 'A team'
        const player = event.player_name
          ? `${event.player_name} for ${team}`
          : team

        const descriptions = {
          goal: `GOAL!!! ${team} have scored!`,
          shot_on_target: `${player} fires a shot on target!`,
          shot: `${player} takes a shot!`,
          progressive_pass: `${team} move forward with an attacking pass.`,
          penalty_area_entry: `${team} break into the penalty area!`,
          save: `A crucial save denies ${team}!`,
          yellow_card: `Yellow card shown to ${player}.`,
          red_card: `RED CARD! ${player} has been sent off!`,
        }

        return {
          id: event.event_id,
          time: `${String(event.minute).padStart(2, '0')}:${String(event.second).padStart(2, '0')}`,
          text: descriptions[event.event_type],
          type: event.event_type,
          intensity: event.event_type === 'goal'
            ? 'maximum'
            : [
                'penalty_area_entry',
                'shot',
                'shot_on_target',
                'save',
                'red_card',
              ].includes(event.event_type)
              ? 'high'
              : 'normal',
        }
      })

    setLiveCommentary(messages.slice(-8).reverse())
  }, [data, playbackSeconds])
  const commentaryQueueRef = useRef([])
  const commentaryPlayingRef = useRef(false)
  const commentarySessionRef = useRef(0)
  const commentarySeenRef = useRef(new Set())
  const commentaryBlobUrlRef = useRef(null)
  const commentaryActiveRef = useRef(false)

  const stopCommentary = () => {
    commentarySessionRef.current += 1
    commentaryQueueRef.current = []
    commentaryPlayingRef.current = false

    speechRequestRef.current?.abort()
    speechRequestRef.current = null

    if (azureAudioRef.current) {
      azureAudioRef.current.pause()
      azureAudioRef.current.removeAttribute('src')
      azureAudioRef.current.load()
      azureAudioRef.current = null
    }

    if (commentaryBlobUrlRef.current) {
      URL.revokeObjectURL(commentaryBlobUrlRef.current)
      commentaryBlobUrlRef.current = null
    }

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
  }

  const playCommentaryQueue = async () => {
    if (commentaryPlayingRef.current) return

    commentaryPlayingRef.current = true
    const session = commentarySessionRef.current

    try {
      while (
        session === commentarySessionRef.current &&
        commentaryQueueRef.current.length > 0
      ) {
        const item = commentaryQueueRef.current.shift()
        const eventVoice = item.intensity === 'high' || item.intensity === 'maximum' ? 'excited' : commentaryVoice
        const controller = new AbortController()
        speechRequestRef.current = controller

        const browserFallback = () => new Promise((resolve) => {
          if (
            controller.signal.aborted ||
            !('speechSynthesis' in window)
          ) {
            resolve()
            return
          }

          const utterance = new SpeechSynthesisUtterance(item.text)
          utterance.rate = eventVoice === 'excited' ? 1.15 : 1
          utterance.pitch = eventVoice === 'excited' ? 1.05 : 1
          utterance.onend = resolve
          utterance.onerror = resolve
          controller.signal.addEventListener('abort', resolve, { once: true })
          window.speechSynthesis.speak(utterance)
        })

        try {
          const response = await fetch(
            `${API_BASE_URL}/api/speech/synthesize`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                text: item.text,
                style: eventVoice,
              }),
              signal: controller.signal,
            }
          )

          if (!response.ok) {
            throw new Error(`Speech API returned ${response.status}`)
          }

          const blob = await response.blob()
          if (controller.signal.aborted) break

          const url = URL.createObjectURL(blob)
          commentaryBlobUrlRef.current = url

          const audio = new Audio(url)
          azureAudioRef.current = audio

          await new Promise((resolve, reject) => {
            audio.onended = resolve
            audio.onerror = () => reject(new Error('Audio playback failed'))
            controller.signal.addEventListener('abort', resolve, { once: true })
            audio.play().catch(reject)
          })
        } catch (error) {
          if (!controller.signal.aborted) {
            console.warn('Azure Speech unavailable; using browser voice.', error)
            await browserFallback()
          }
        } finally {
          if (azureAudioRef.current) {
            azureAudioRef.current.pause()
            azureAudioRef.current = null
          }

          if (commentaryBlobUrlRef.current) {
            URL.revokeObjectURL(commentaryBlobUrlRef.current)
            commentaryBlobUrlRef.current = null
          }

          if (speechRequestRef.current === controller) {
            speechRequestRef.current = null
          }
        }
      }
    } finally {
      if (session === commentarySessionRef.current) {
        commentaryPlayingRef.current = false
      }
    }
  }

  useEffect(() => {
    commentaryActiveRef.current = voiceCommentaryEnabled && isPlaying

    if (!commentaryActiveRef.current) {
      stopCommentary()
      commentarySeenRef.current.clear()
      return
    }

    const newMessages = [...liveCommentary]
      .reverse()
      .filter((item) => !commentarySeenRef.current.has(item.id))

    for (const item of newMessages) {
      commentarySeenRef.current.add(item.id)
      commentaryQueueRef.current.push(item)
    }

    if (commentaryQueueRef.current.length > 0) {
      playCommentaryQueue()
    }
  }, [liveCommentary, voiceCommentaryEnabled, isPlaying, commentaryVoice])

  useEffect(() => {
    return () => stopCommentary()
  }, [])
  const clearAskChat = () => {
    askGeneration.current += 1
    setAskMessages([])
    setAskQuestion('')
    setAskError(null)
    setAskLoading(false)
  }

  useEffect(() => {
    if (!data) return

    const controller = new AbortController()
    const seconds = Math.min(
      Math.floor(playbackSeconds / 5) * 5,
      data.match.minute * 60 + data.match.second
    )

    fetch(
      `${API_BASE_URL}/api/match/storyteller?seconds=${seconds}&audience=${selectedAudience}`,
      { signal: controller.signal }
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Storyteller request failed: ${response.status}`)
        }
        return response.json()
      })
      .then((result) => {
        setStorytellerData(result)
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('Storyteller:', err)
        }
      })

    return () => controller.abort()
  }, [data, Math.floor(playbackSeconds / 5), selectedAudience])
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/match/demo`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API request failed: ${response.status}`)
        }

        return response.json()
      })
      .then((result) => {
        setData(result)
      })
      .catch((err) => {
        setError(err.message)
      })
  }, [])

  useEffect(() => {
    if (!isPlaying || !data) return

    const lastEventSecond = Math.max(
      data.match.minute * 60 + data.match.second,
      ...data.events.map((event) => event.minute * 60 + event.second)
    )

    const timer = setInterval(() => {
      setPlaybackSeconds((current) => {
        return Math.min(current + playbackSpeed, lastEventSecond)
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [isPlaying, data, playbackSpeed])
  useEffect(() => {
    const previous = previousPlaybackSeconds.current
    previousPlaybackSeconds.current = playbackSeconds

    if (!data || !isPlaying || playbackSeconds <= previous) return

    const newGoal = data.events.find((event) => {
      const goalSecond = event.minute * 60 + event.second
      return (
        event.event_type === 'goal' &&
        goalSecond > previous &&
        goalSecond <= playbackSeconds
      )
    })

    if (newGoal) {
      setGoalCelebration(newGoal)
    }
  }, [playbackSeconds, data, isPlaying])

  useEffect(() => {
    if (!goalCelebration) return

    const timer = setTimeout(() => {
      setGoalCelebration(null)
    }, 4000)

    return () => clearTimeout(timer)
  }, [goalCelebration])

  useEffect(() => {
    if (!data || !isPlaying) return

    const matchEndSeconds =
      data.match.minute * 60 + data.match.second

    if (playbackSeconds >= matchEndSeconds) {
      setIsPlaying(false)
    }
  }, [playbackSeconds, isPlaying, data])
  useEffect(() => {
    if (!data) return

    const controller = new AbortController()
    const seconds = Math.min(
      Math.floor(playbackSeconds / 5) * 5,
      data.match.minute * 60 + data.match.second
    )

    fetch(`${API_BASE_URL}/api/match/pulse?seconds=${seconds}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Live Pulse request failed: ${response.status}`)
        }
        return response.json()
      })
      .then((result) => {
        setLivePulse(result.match_pulse)
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('Live Match Pulse:', err)
        }
      })

    return () => controller.abort()
  }, [data, Math.floor(playbackSeconds / 5)])
  useEffect(() => {
    if (!data) return

    const controller = new AbortController()
    const seconds = Math.min(
      Math.floor(playbackSeconds / 5) * 5,
      data.match.minute * 60 + data.match.second
    )

    fetch(`${API_BASE_URL}/api/match/analyst?seconds=${seconds}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Match Analyst request failed: ${response.status}`)
        }
        return response.json()
      })
      .then((result) => {
        setAnalystData(result)
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('Match Analyst:', err)
        }
      })

    return () => controller.abort()
  }, [data, Math.floor(playbackSeconds / 5)])
  useEffect(() => {
    if (!data) return

    const controller = new AbortController()
    const seconds = Math.min(
      Math.floor(playbackSeconds / 5) * 5,
      data.match.minute * 60 + data.match.second
    )

    fetch(`${API_BASE_URL}/api/match/tactical?seconds=${seconds}`, {
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Tactical Intelligence request failed: ${response.status}`)
        }
        return response.json()
      })
      .then((result) => {
        setTacticalData(result)
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('Tactical Intelligence:', err)
        }
      })

    return () => controller.abort()
  }, [data, Math.floor(playbackSeconds / 5)])
  if (error) {
    return (
      <div className="app-shell">
        <main className="dashboard">
          <div className="panel">
            MatchPoint API error: {error}
          </div>
        </main>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="app-shell">
        <main className="dashboard">
          <div className="panel">
            Loading MatchPoint intelligence...
          </div>
        </main>
      </div>
    )
  }

  const match = data.match
  const pulse = livePulse || data.match_pulse
  const pitchEvents = data.events.filter((event) =>
    ['pass', 'progressive_pass', 'shot', 'shot_on_target', 'goal'].includes(event.event_type) &&
    event.x != null &&
    event.y != null &&
    event.minute * 60 + event.second <= playbackSeconds
  )
  const visibleGoals = data.events.filter((event) =>
    event.event_type === 'goal' &&
    event.minute * 60 + event.second <= playbackSeconds
  )

  const liveHomeScore = visibleGoals.filter(
    (event) => event.team_id === match.home_team.team_id
  ).length

  const liveAwayScore = visibleGoals.filter(
    (event) => event.team_id === match.away_team.team_id
  ).length
  const keyMoments = data.key_moments
    .filter((moment) =>
      moment.minute * 60 + moment.second <= playbackSeconds
    )
    .reverse()
  const explanationsById = Object.fromEntries(
    data.why_explanations.map((item) => [item.moment_id, item])
  )
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">MATCHPOINT AI</div>
          <div className="tagline">
            Explainable Football Match Intelligence
          </div>
        </div>

        <div className="live-status">
          <span className="live-dot"></span>
          LIVE INTELLIGENCE
        </div>
      </header>

      <main className="dashboard">
        <section className="scoreboard">
          <div className="team team-home">
            <img
              className="team-logo"
              src="/teams/riverdale-wolves.svg"
              alt="Riverdale Wolves crest"
            />
            <div className="team-identity">
              <span className="team-code">{match.home_team.short_name}</span>
              <span className="team-name">{match.home_team.name}</span>
            </div>
          </div>

          <div className="score-center">
            <div className="match-clock">{String(Math.floor(playbackSeconds / 60)).padStart(2, '0')}:{String(Math.floor(playbackSeconds % 60)).padStart(2, '0')}</div>
            <div className="score">{liveHomeScore} - {liveAwayScore}</div>
            <div className="match-status">LIVE</div>

            <div className="playback-controls">
              <button
                type="button"
                onClick={() => setIsPlaying(true)}
                disabled={isPlaying || playbackSeconds >= match.minute * 60 + match.second}
              >
                Play
              </button>

              <button
                type="button"
                onClick={() => setIsPlaying(false)}
                disabled={!isPlaying}
              >
                Pause
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsPlaying(false)
                  setPlaybackSeconds(0)
                  previousPlaybackSeconds.current = 0
                  setGoalCelebration(null)
                  setReplayGoal(null)
                  setReplayEvents([])
                  setReplayStep(0)
                  setSelectedPitchEvent(null)
                  lastSpokenEventId.current = null
                  if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel()
                  }
                  clearAskChat()
                }}
              >
                Reset
              </button>

              <button
                type="button"
                onClick={() => {
                  const latestGoal = visibleGoals[visibleGoals.length - 1]
                  if (latestGoal) startGoalReplay(latestGoal)
                }}
                disabled={visibleGoals.length === 0}
              >
                Replay Goal
              </button>

              <button
                type="button"
                onClick={() => {
                  if (!voiceCommentaryEnabled) {
                    lastSpokenEventId.current = liveCommentary[0]?.id ?? null
                  } else if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel()
                  }
                  setVoiceCommentaryEnabled((enabled) => !enabled)
                }}
                aria-pressed={voiceCommentaryEnabled}
              >
                {voiceCommentaryEnabled ? 'Disable Voice Commentary' : 'Enable Voice Commentary'}
              </button>

              <label htmlFor="commentary-voice-select">
                Commentator Voice
              </label>
              <select
                id="commentary-voice-select"
                value={commentaryVoice}
                onChange={(event) => setCommentaryVoice(event.target.value)}
              >
                <option value="professional">Professional Broadcaster</option>
                <option value="excited">Excited Sports Commentator</option>
              </select>
            </div>
            <div className="ask-matchpoint-launcher">
              <button
                type="button"
                className="ask-matchpoint-button"
                onClick={() => {
                  if (askChatOpen) clearAskChat()
                  setAskChatOpen((open) => !open)
                }}
                aria-expanded={askChatOpen}
              >
                {askChatOpen ? 'Close MatchPointAI Chat' : 'Ask MatchPointAI'}
              </button>
            </div>

          </div>
          <div className="team team-away">
            <div className="team-identity">
              <span className="team-code">{match.away_team.short_name}</span>
              <span className="team-name">{match.away_team.name}</span>
            </div>
            <img
              className="team-logo"
              src="/teams/southgate-phoenix.svg"
              alt="Southgate Phoenix crest"
            />
          </div>
        </section>

        {askChatOpen && (
          <div
            className="ask-chat-window"
            role="dialog"
            aria-label="Ask MatchPointAI"
          >
            <div className="ask-chat-header">
              <strong>Ask MatchPointAI</strong>
              <button
                type="button"
                onClick={() => {
                  clearAskChat()
                  setAskChatOpen(false)
                }}
                aria-label="Close chat"
              >
                X
              </button>
            </div>

            <div className="ask-chat-messages">
              {askMessages.length === 0 ? (
                <p>
                  Ask a question about the match.
                  Answers will use events from the current playback time.
                </p>
              ) : (
                askMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`ask-chat-message ask-chat-${message.role}`}
                  >
                    <strong>
                      {message.role === 'user' ? 'You' : 'MatchPointAI'}
                    </strong>
                    <p>{message.text}</p>

                    {message.role === 'assistant' && (
                      <div className="ask-chat-evidence">
                        <small>
                          Evidence references:{' '}
                          {message.evidenceValidated
                            ? 'Validated'
                            : 'Not validated'}
                        </small>

                        {message.evidence?.length > 0 && (
                          <ul>
                            {message.evidence.map((item) => (
                              <li key={item.event_id}>
                                {String(item.minute).padStart(2, '0')}:
                                {String(item.second).padStart(2, '0')}
                                {' - '}
                                {item.team_name || 'Unknown team'}
                                {' - '}
                                {item.event_type}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {askLoading && (
  <p className="ask-chat-loading" role="status">
    MatchPointAI is thinking...
  </p>
)}
{askError && <p role="alert">{askError}</p>}

            <form
              className="ask-chat-form"
              onSubmit={async (event) => {
                event.preventDefault()

                const question = askQuestion.trim()
                if (!question || askLoading) return

                const seconds = Math.min(
                  Math.floor(playbackSeconds),
                  605
                )

                setAskQuestion('')
                setAskError(null)
                setAskLoading(true)
                const requestGeneration = askGeneration.current

                setAskMessages((messages) => [
                  ...messages,
                  {
                    role: 'user',
                    text: question,
                    seconds,
                  },
                ])

                try {
                  const response = await fetch(
                    `${API_BASE_URL}/api/match/ask`,
                    {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        question,
                        seconds,
                      }),
                    }
                  )

                  if (!response.ok) {
                    throw new Error(
                      `Question request failed: ${response.status}`
                    )
                  }

                  const result = await response.json()
                  if (requestGeneration !== askGeneration.current) return

                  setAskMessages((messages) => [
                    ...messages,
                    {
                      role: 'assistant',
                      text: result.answer,
                      seconds: result.playback_seconds,
                      evidence: result.evidence_events || [],
                      evidenceValidated: result.evidence_validated,
                    },
                  ])
                } catch (error) {
                  if (requestGeneration === askGeneration.current) {
                    setAskError(error.message)
                  }
                } finally {
                  if (requestGeneration === askGeneration.current) {
                    setAskLoading(false)
                  }
                }
              }}
            >
              <input
                type="text"
                value={askQuestion}
                onChange={(event) => setAskQuestion(event.target.value)}
                placeholder="Ask about the match..."
                maxLength={500}
                disabled={askLoading}
              />
              <button
                type="submit"
                disabled={askLoading || !askQuestion.trim()}
              >
                Send
              </button>
            </form>
          </div>
        )}
        <section className="content-grid">
          <div className="main-column">
            <div className="panel pitch-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">LIVE MATCH</span>
                  <h2>Match Activity</h2>
                </div>
                <div className="pitch-legend">
                  <div className="pitch-legend-item">
                    <span className="legend-dot legend-home-pass"></span>
                    <span>Wolves Pass</span>
                  </div>
                  <div className="pitch-legend-item">
                    <span className="legend-dot legend-away-pass"></span>
                    <span>Phoenix Pass</span>
                  </div>
                  <div className="pitch-legend-item">
                    <span className="legend-dot legend-home-shot"></span>
                    <span>Wolves Shot</span>
                  </div>
                  <div className="pitch-legend-item">
                    <span className="legend-dot legend-away-shot"></span>
                    <span>Phoenix Shot</span>
                  </div>
                  <div className="pitch-legend-item">
                    <span className="legend-dot legend-goal"></span>
                    <span>Goal</span>
                  </div>
                </div>
              </div>

              <div className="pitch">
                <div className="half-line"></div>
                <div className="center-circle"></div>
                <div className="penalty-box left"></div>
                <div className="penalty-box right"></div>
                <div className="center-spot"></div>
                  {pitchEvents.map((event) => (
                    <div
                      key={event.event_id}
                      role="button"
                      tabIndex={0}
                      onClick={() => setSelectedPitchEvent(event)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          setSelectedPitchEvent(event)
                        }
                      }}
                      className={`pitch-event ${event.team_id === match.home_team.team_id ? 'pitch-home' : 'pitch-away'} ${event.event_type === 'goal' ? 'pitch-goal' : ['pass', 'progressive_pass'].includes(event.event_type) ? 'pitch-pass' : 'pitch-shot'}`}
                      style={{
                        left: `${event.team_id === match.away_team.team_id ? 100 - event.x : event.x}%`,
                        top: `${event.y}%`,
                      }}
                      title={`${event.team_name || 'Unknown'} - ${event.event_type.replaceAll('_', ' ')} (${event.minute}:${String(event.second).padStart(2, '0')})`}
                    />
                  ))}
                {replayGoal && replayEvents[replayStep] && (
                  <div
                    className="goal-replay-marker"
                    style={{
                      left: `${
                        replayGoal.team_id === match.away_team.team_id
                          ? 100 - replayEvents[replayStep].x
                          : replayEvents[replayStep].x
                      }%`,
                      top: `${replayEvents[replayStep].y}%`,
                    }}
                    title={`${replayEvents[replayStep].event_type.replaceAll('_', ' ')}`}
                  />
                )}
                {goalCelebration && (
                  <div
                    className={`goal-celebration ${
                      goalCelebration.team_id === match.home_team.team_id
                        ? 'goal-celebration-home'
                        : 'goal-celebration-away'
                    }`}
                    role="status"
                    aria-live="polite"
                  >
                    <div className="goal-celebration-content">
                      <div className="goal-celebration-title">GOAL!!</div>
                      <img
                        className="goal-celebration-crest"
                        src={
                          goalCelebration.team_id === match.home_team.team_id
                            ? '/teams/riverdale-wolves.svg'
                            : '/teams/southgate-phoenix.svg'
                        }
                        alt="Scoring team crest"
                      />
                      <div className="goal-celebration-team">
                        {goalCelebration.team_id === match.home_team.team_id
                          ? match.home_team.name
                          : match.away_team.name}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="momentum-panel">
                <div className="momentum-heading">
                  <span>LIVE MOMENTUM</span>
                  <span>{pulse.momentum === 0 ? 'Even Match' : pulse.momentum > 0 ? 'Wolves Advantage' : 'Phoenix Advantage'}</span>
                </div>

                <div className="momentum-team-labels">
                  <strong>{match.home_team.name}</strong>
                  <strong>{match.away_team.name}</strong>
                </div>

                <div
                  className="momentum-bar"
                  role="img"
                  aria-label={`Momentum: ${match.home_team.name} ${Math.round(50 + Math.max(-100, Math.min(100, pulse.momentum)) / 2)} percent, ${match.away_team.name} ${Math.round(50 - Math.max(-100, Math.min(100, pulse.momentum)) / 2)} percent`}
                >
                  <div
                    className="momentum-home"
                    style={{ width: `${50 + Math.max(-100, Math.min(100, pulse.momentum)) / 2}%` }}
                  />
                  <div
                    className="momentum-away"
                    style={{ width: `${50 - Math.max(-100, Math.min(100, pulse.momentum)) / 2}%` }}
                  />

                </div>
              </div>

              {selectedPitchEvent && (
                <div className="selected-event-panel">
                  <div className="selected-event-header">
                    <h3>Selected Match Event</h3>
                    <button
                      type="button"
                      onClick={() => setSelectedPitchEvent(null)}
                    >
                      Close
                    </button>
                  </div>

                  <p>
                    <strong>Team:</strong> {selectedPitchEvent.team_name || 'Unknown'}
                  </p>

                  <p>
                    <strong>Time:</strong> {String(selectedPitchEvent.minute).padStart(2, '0')}:{String(selectedPitchEvent.second).padStart(2, '0')}
                  </p>

                  <p>
                    <strong>Event:</strong> {selectedPitchEvent.event_type.replaceAll('_', ' ')}
                  </p>

                  {selectedPitchEvent.description && (
                    <p>
                      <strong>Description:</strong> {selectedPitchEvent.description}
                    </p>
                  )}

                  {selectedPitchEvent.expected_goals != null && (
                    <p>
                      <strong>Expected Goals (xG):</strong> {selectedPitchEvent.expected_goals.toFixed(3)}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="panel live-commentary-panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">LIVE BROADCAST</span>
                  <h2>AI Match Commentary</h2>
                </div>
              </div>

              <div className="live-commentary-list">
                {liveCommentary.length > 0 ? (
                  liveCommentary.map((item) => (
                    <div
                      key={item.id}
                      className={`commentary-item ${item.type === 'goal' ? 'commentary-goal' : ''}`}
                    >
                      <span className="commentary-time">{item.time}</span>
                      <span className="commentary-text">{item.text}</span>
                    </div>
                  ))
                ) : (
                  <p>Waiting for match action...</p>
                )}
              </div>
            </div>
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">INTELLIGENCE</span>
                  <h2>Key Moments</h2>
                </div>
              </div>

              <div className="key-moments-list">
                {keyMoments.map((moment) => {
                  const explanation = explanationsById[moment.moment_id]
                  const isExpanded = expandedMomentId === moment.moment_id

                  return (
                    <div className="moment-card" key={moment.moment_id}>
                      <div className="moment-time">
                        {String(moment.minute).padStart(2, '0')}:{String(moment.second).padStart(2, '0')}
                      </div>

                      <div className="moment-content">
                        <div className="moment-type">
                          {moment.moment_type.replaceAll('_', ' ').toUpperCase()}
                        </div>

                        <h3>{moment.title}</h3>
                        <p>{moment.description}</p>

                        <button
                          type="button"
                          className="why-button"
                          onClick={() => setExpandedMomentId(isExpanded ? null : moment.moment_id)}
                        >
                          {isExpanded ? 'HIDE WHY' : 'WHY?'}
                        </button>

                        {isExpanded && explanation && (
                          <div className="why-explanation">
                            <div className="why-title">
                              Why did MatchPoint flag this?
                            </div>

                            <p>{explanation.answer}</p>

                            <div className="why-evidence">
                              <strong>Evidence</strong>
                              <p>{explanation.evidence_summary}</p>
                            </div>

                            <div className="evidence-timeline">
                              <h4>Supporting Event Timeline</h4>

                              {explanation.evidence_events.map((event) => (
                                <div className="evidence-event" key={event.event_id}>
                                  <span className="evidence-time">
                                    {String(event.minute).padStart(2, '0')}:{String(event.second).padStart(2, '0')}
                                  </span>

                                  <div>
                                    <strong>
                                      {event.team_name || 'Match'} - {event.event_type.replaceAll('_', ' ')}
                                    </strong>
                                    {event.description && <p>{event.description}</p>}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          <aside className="side-column">
            <div className="panel">
              <span className="eyebrow">MATCH PULSE</span>
              <h2>Live Intelligence</h2>


              <div className="metric">
                <div className="metric-label">
                  <span>Chaos Index</span>
                  <strong>{pulse.chaos_index.toFixed(1)}</strong>
                </div>
                <div className="metric-note">
                    {pulse.chaos_index < 25
                      ? 'Low match volatility'
                      : pulse.chaos_index < 50
                        ? 'Moderate match volatility'
                        : pulse.chaos_index < 75
                          ? 'Elevated match volatility'
                          : 'High match volatility'}
                </div>
              </div>

              <div className="pressure-grid">
                <div>
                  <span>{pulse.home.team_name}</span>
                  <strong>{pulse.home.recent_pressure.toFixed(2)}</strong>
                  <small>Recent Pressure</small>
                </div>

                <div>
                  <span>{pulse.away.team_name}</span>
                  <strong>{pulse.away.recent_pressure.toFixed(2)}</strong>
                  <small>Recent Pressure</small>
                </div>
              </div>
            </div>

              <div className="panel">
                <span className="eyebrow">AI AGENT</span>
                <h2>Match Analyst</h2>

                {analystData ? (
                  <div className="analyst-content">
                    <p>{analystData.analysis.summary}</p>

                    <p>
                      <strong>Leading Team:</strong>{' '}
                      {analystData.analysis.leading_team || 'Match tied'}
                    </p>

                    <p>
                      <strong>Momentum:</strong>{' '}
                      {analystData.analysis.momentum_team || 'Balanced'}
                    </p>

                    <h3>Key Observations</h3>

                    <ul>
                      {analystData.analysis.key_observations.map(
                        (observation, index) => (
                          <li key={index}>{observation}</li>
                        )
                      )}
                    </ul>

                    <small>
                      Supporting events: {analystData.analysis.evidence_event_ids.length}
                      </small>

                      {analystData.evidence_validation && (
                        <p className="evidence-status">
                          <strong>Evidence:</strong>{' '}
                          {analystData.evidence_validation.valid
                            ? 'Verified'
                            : 'Needs Review'}
                          {' '}(
                          {analystData.evidence_validation.verified_references}
                          /
                          {analystData.evidence_validation.total_references}
                          )
                        </p>
                      )}
                  </div>
                ) : (
                  <p>Waiting for Match Analyst...</p>
                )}
              </div>

              <div className="panel">
                <span className="eyebrow">AI AGENT</span>
                <h2>Tactical Intelligence</h2>

                {tacticalData ? (
                  <div className="tactical-content">
                    <p>{tacticalData.analysis.summary}</p>

                    <p>
                      <strong>Pressure Advantage:</strong>{' '}
                      {tacticalData.analysis.pressure_advantage || 'Balanced'}
                    </p>

                    <p>
                      <strong>Attacking Advantage:</strong>{' '}
                      {tacticalData.analysis.attacking_advantage || 'Balanced'}
                    </p>

                    <h3>Tactical Observations</h3>

                    <ul>
                      {tacticalData.analysis.tactical_observations.map(
                        (observation, index) => (
                          <li key={index}>{observation}</li>
                        )
                      )}
                    </ul>

                    <small>
                      Supporting events: {tacticalData.analysis.evidence_event_ids.length}
                      </small>

                      {tacticalData.evidence_validation && (
                        <p className="evidence-status">
                          <strong>Evidence:</strong>{' '}
                          {tacticalData.evidence_validation.valid
                            ? 'Verified'
                            : 'Needs Review'}
                          {' '}(
                          {tacticalData.evidence_validation.verified_references}
                          /
                          {tacticalData.evidence_validation.total_references}
                          )
                        </p>
                      )}
                  </div>
                ) : (
                  <p>Waiting for Tactical Intelligence...</p>
                )}
              </div>

            <div className="panel">
              <span className="eyebrow">AI AGENT</span>
              <h2>Storyteller</h2>

              {storytellerData ? (
                <div className="analyst-content">
                  <h3>{storytellerData.narrative.headline}</h3>

                  <p>{storytellerData.narrative.narrative}</p>

                  <p>
                    <strong>Audience:</strong>{' '}
                    {storytellerData.audience}
                  </p>

                  <p>
                    <strong>Commentary Engine:</strong>{' '}
                    {storytellerData.commentary_source === 'azure'
                      ? 'Microsoft Foundry / GPT-5-mini'
                      : 'Deterministic Fallback'}
                  </p>

                  <p>
                    <strong>AI Commentary Validated:</strong>{' '}
                    {storytellerData.ai_commentary_validated
                      ? 'Yes'
                      : 'No'}
                  </p>

                  <p className="evidence-status">
                    <strong>Evidence:</strong>{' '}
                    {storytellerData.narrative.evidence_verified
                      ? 'Verified'
                      : 'Needs Review'}
                  </p>
                </div>
              ) : (
                <p>Waiting for Storyteller...</p>
              )}
            </div>

            <div className="panel">
              <span className="eyebrow">VIEW</span>
              <h2>Personalize</h2>

              <label>
                Audience
                <select value={selectedAudience} onChange={(event) => setSelectedAudience(event.target.value)}>
                  <option value="analyst">Analyst</option>
                  <option value="broadcaster">Broadcaster</option>
                  <option value="fan">Fan</option>
                </select>
              </label>

              <label>
                Language
                <select defaultValue="en">
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                </select>
              </label>
            </div>
          </aside>
        </section>
      </main>
    </div>
  )
}

export default App













































