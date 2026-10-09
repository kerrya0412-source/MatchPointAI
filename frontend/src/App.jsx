import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [expandedMomentId, setExpandedMomentId] = useState(null)
  const [selectedPitchEvent, setSelectedPitchEvent] = useState(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSeconds, setPlaybackSeconds] = useState(0)
  const [playbackSpeed, setPlaybackSpeed] = useState(1)
  const [livePulse, setLivePulse] = useState(null)
  const [analystData, setAnalystData] = useState(null)
  const [tacticalData, setTacticalData] = useState(null)
  const [selectedAudience, setSelectedAudience] = useState('analyst')
  const [storytellerData, setStorytellerData] = useState(null)

  useEffect(() => {
    if (!data) return

    const controller = new AbortController()
    const seconds = Math.min(
      Math.floor(playbackSeconds / 5) * 5,
      data.match.minute * 60 + data.match.second
    )

    fetch(
      `http://localhost:8020/api/match/storyteller?seconds=${seconds}&audience=${selectedAudience}`,
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
    fetch('http://localhost:8020/api/match/demo')
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

    fetch(`http://localhost:8020/api/match/pulse?seconds=${seconds}`, {
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

    fetch(`http://localhost:8020/api/match/analyst?seconds=${seconds}`, {
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

    fetch(`http://localhost:8020/api/match/tactical?seconds=${seconds}`, {
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
    ['shot', 'shot_on_target', 'goal'].includes(event.event_type) &&
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
          <div className="team">
            <span className="team-code">{match.home_team.short_name}</span>
            <span className="team-name">{match.home_team.name}</span>
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
                  setSelectedPitchEvent(null)
                }}
              >
                Reset
              </button>
            </div>
          </div>

          <div className="team team-away">
            <span className="team-code">{match.away_team.short_name}</span>
            <span className="team-name">{match.away_team.name}</span>
          </div>
        </section>

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
                    <span className="legend-dot legend-shot"></span>
                    <span>Shots</span>
                  </div>
                  <div className="pitch-legend-item">
                    <span className="legend-dot legend-goal"></span>
                    <span>Goals</span>
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
                      className={`pitch-event ${event.event_type === 'goal' ? 'pitch-goal' : 'pitch-shot'}`}
                      style={{
                        left: `${event.x}%`,
                        top: `${event.y}%`,
                      }}
                      title={`${event.team_name || 'Unknown'} - ${event.event_type.replaceAll('_', ' ')} (${event.minute}:${String(event.second).padStart(2, '0')})`}
                    />
                  ))}
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
                  <span>Momentum</span>
                  <strong>{pulse.momentum.toFixed(1)}</strong>
                </div>
                <div className="metric-note">
                    {pulse.momentum > 0
                      ? `${pulse.home.team_name} advantage`
                      : pulse.momentum < 0
                        ? `${pulse.away.team_name} advantage`
                        : 'Balanced momentum'}
                </div>
              </div>

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
                  <span>North City</span>
                  <strong>{pulse.home.recent_pressure.toFixed(2)}</strong>
                  <small>Recent Pressure</small>
                </div>

                <div>
                  <span>South United</span>
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
































