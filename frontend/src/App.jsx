import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [expandedMomentId, setExpandedMomentId] = useState(null)

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
  const pulse = data.match_pulse
  const pitchEvents = data.events.filter((event) =>
    ['shot', 'shot_on_target', 'goal'].includes(event.event_type) &&
    event.x != null &&
    event.y != null
  )
  const keyMoments = [...data.key_moments].reverse()
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
            <div className="match-clock">{String(match.minute).padStart(2, '0')}:{String(match.second).padStart(2, '0')}</div>
            <div className="score">{match.home_score} - {match.away_score}</div>
            <div className="match-status">LIVE</div>
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
                      className={`pitch-event ${event.event_type === 'goal' ? 'pitch-goal' : 'pitch-shot'}`}
                      style={{
                        left: `${event.x}%`,
                        top: `${event.y}%`,
                      }}
                      title={`${event.team_name || 'Unknown'} - ${event.event_type.replaceAll('_', ' ')} (${event.minute}:${String(event.second).padStart(2, '0')})`}
                    />
                  ))}
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
                  <span>Momentum</span>
                  <strong>{pulse.momentum.toFixed(1)}</strong>
                </div>
                <div className="metric-note">
                  South United advantage
                </div>
              </div>

              <div className="metric">
                <div className="metric-label">
                  <span>Chaos Index</span>
                  <strong>{pulse.chaos_index.toFixed(1)}</strong>
                </div>
                <div className="metric-note">
                  Elevated match volatility
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
              <span className="eyebrow">VIEW</span>
              <h2>Personalize</h2>

              <label>
                Audience
                <select defaultValue="analyst">
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








