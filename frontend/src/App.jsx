import { useState } from 'react'
import './App.css'

function App() {
  const [jdFile, setJdFile] = useState(null)
  const [resumeFiles, setResumeFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [showDrawer, setShowDrawer] = useState(false)

  const handleJdChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setJdFile(e.target.files[0])
    }
  }

  const handleResumesChange = (e) => {
    if (e.target.files) {
      setResumeFiles(Array.from(e.target.files))
    }
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    if (!jdFile) {
      setError('Please upload a Job Description file.')
      return
    }
    if (resumeFiles.length === 0) {
      setError('Please upload at least one candidate resume.')
      return
    }

    setLoading(true)
    setError(null)
    setData(null)
    setSelectedCandidate(null)
    setShowDrawer(false)

    const formData = new FormData()
    formData.append('jd', jdFile)
    resumeFiles.forEach((file) => {
      formData.append('resumes', file)
    })

    try {
      const response = await fetch('http://localhost:8000/analyze/multiple', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Failed to analyze candidate pool.')
      }

      const result = await response.json()
      setData(result)
    } catch (err) {
      console.error(err)
      setError(err.message || 'An error occurred during evaluation.')
    } finally {
      setLoading(false)
    }
  }

  const openDrawer = (candidate) => {
    setSelectedCandidate(candidate)
    setShowDrawer(true)
  }

  const closeDrawer = () => {
    setShowDrawer(false)
  }

  // Get color for recommendation badge
  const getRecommendationClass = (rec) => {
    if (!rec) return 'badge-gray'
    if (rec.includes('Technical Interview')) return 'badge-emerald'
    if (rec.includes('Review')) return 'badge-amber'
    if (rec.includes('Reject')) return 'badge-rose'
    return 'badge-gray'
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="logo-section">
          <span className="logo-badge">ARIS V2</span>
          <h1 className="logo-title">Recruitment Intelligence</h1>
        </div>
        <p className="subtitle">AI-powered multi-candidate ranking and compliance evaluation</p>
      </header>

      {/* Main Workspace */}
      <main className="main-content">
        <div className="dashboard-grid">
          {/* Left panel: Upload Form */}
          <div className="panel card glass">
            <h2>Evaluate Candidates</h2>
            <p className="panel-desc">Upload a job specification and multiple resumes in PDF format to rank the applicants.</p>

            <form onSubmit={handleFormSubmit} className="upload-form">
              {/* Job Description File Input */}
              <div className="input-group">
                <label className="input-label">Job Description (.txt or .pdf)</label>
                <div className="file-dropzone">
                  <input
                    type="file"
                    id="jd-upload"
                    accept=".txt,.pdf"
                    onChange={handleJdChange}
                    className="file-input-hidden"
                  />
                  <label htmlFor="jd-upload" className="dropzone-label">
                    <svg className="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>{jdFile ? jdFile.name : 'Select Job Description'}</span>
                  </label>
                </div>
              </div>

              {/* Resumes File Input */}
              <div className="input-group">
                <label className="input-label">Candidate Resumes (Multiple PDFs)</label>
                <div className="file-dropzone">
                  <input
                    type="file"
                    id="resumes-upload"
                    accept=".pdf"
                    multiple
                    onChange={handleResumesChange}
                    className="file-input-hidden"
                  />
                  <label htmlFor="resumes-upload" className="dropzone-label">
                    <svg className="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <span>
                      {resumeFiles.length > 0
                        ? `${resumeFiles.length} resume(s) selected`
                        : 'Select Candidate Resumes'}
                    </span>
                  </label>
                </div>
                {resumeFiles.length > 0 && (
                  <div className="selected-files-list">
                    {resumeFiles.map((f, i) => (
                      <span key={i} className="file-chip">
                        {f.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {error && <div className="error-message">{error}</div>}

              <button
                type="submit"
                disabled={loading}
                className={`btn btn-primary ${loading ? 'loading' : ''}`}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Evaluating Candidate Pool...
                  </>
                ) : (
                  'Run Evaluation Pipeline'
                )}
              </button>
            </form>
          </div>

          {/* Right panel: Overview & Stats */}
          {data ? (
            <div className="panel card glass">
              <h2>Recruiter Summary</h2>
              <div className="job-badge-container">
                <span className="job-title-badge">
                  {data.job?.title || 'Software Engineer'}
                </span>
                <span className="job-seniority-badge">
                  {data.job?.seniority_level || 'Mid Level'}
                </span>
              </div>

              {/* Stats Cards */}
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-value">{data.recruiter_summary.total_evaluated}</span>
                  <span className="stat-label">Total Evaluated</span>
                </div>
                <div className="stat-card stat-success">
                  <span className="stat-value text-emerald">{data.recruiter_summary.passed_hard_requirements}</span>
                  <span className="stat-label">Passed Hard Req.</span>
                </div>
                <div className="stat-card stat-fail">
                  <span className="stat-value text-rose">{data.recruiter_summary.failed_hard_requirements}</span>
                  <span className="stat-label">Failed Hard Req.</span>
                </div>
              </div>

              {/* Recommendation Breakdown */}
              <div className="breakdown-section">
                <h3>Decision Breakdown</h3>
                <div className="breakdown-list">
                  {Object.entries(data.recruiter_summary.recommendations_breakdown).map(([label, count]) => (
                    <div key={label} className="breakdown-row">
                      <span className="breakdown-label">{label}</span>
                      <div className="breakdown-bar-bg">
                        <div
                          className={`breakdown-bar-fill ${getRecommendationClass(label)}`}
                          style={{
                            width: `${(count / data.recruiter_summary.total_evaluated) * 100}%`,
                          }}
                        ></div>
                      </div>
                      <span className="breakdown-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="panel card glass placeholder-panel">
              <svg className="placeholder-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3>Awaiting Evaluation</h3>
              <p>Upload a job specification and resumes to rank applicants and review deep candidate explainability metrics.</p>
            </div>
          )}
        </div>

        {/* Candidate Ranking Section */}
        {data && (
          <section className="ranking-section card glass">
            <div className="section-header">
              <h2>Candidate Rankings</h2>
              <span className="info-tip">Click on any candidate row to view detailed breakdown</span>
            </div>
            
            <div className="table-responsive">
              <table className="ranking-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Candidate</th>
                    <th>Overall Score</th>
                    <th>Recommendation</th>
                    <th>Hard Req. Status</th>
                    <th>Semantic Fit</th>
                  </tr>
                </thead>
                <tbody>
                  {data.ranked_candidates.map((c) => (
                    <tr
                      key={c.candidate_name}
                      onClick={() => openDrawer(c)}
                      className={`table-row-interactive ${selectedCandidate?.candidate_name === c.candidate_name ? 'row-selected' : ''}`}
                    >
                      <td>
                        <span className={`rank-badge rank-${c.rank}`}>
                          {c.rank}
                        </span>
                      </td>
                      <td className="candidate-name-cell">{c.candidate_name}</td>
                      <td>
                        <span className="score-badge">
                          {c.overall_score.toFixed(1)}%
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${getRecommendationClass(c.recommendation)}`}>
                          {c.recommendation}
                        </span>
                      </td>
                      <td>
                        <span className={`status-indicator ${c.hard_requirement_status === 'Passed' ? 'status-pass' : 'status-fail'}`}>
                          {c.hard_requirement_status}
                        </span>
                      </td>
                      <td className="semantic-cell">
                        <div className="progress-mini-bg">
                          <div className="progress-mini-bar" style={{ width: `${c.semantic_score}%` }}></div>
                        </div>
                        <span className="mini-score-label">{c.semantic_score.toFixed(0)}%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>

      {/* Backdrop for drawer */}
      {showDrawer && <div className="drawer-backdrop" onClick={closeDrawer}></div>}

      {/* Candidate Details Drawer */}
      <div className={`drawer glass ${showDrawer ? 'drawer-open' : ''}`}>
        {selectedCandidate && (
          <div className="drawer-inner">
            {/* Drawer Header */}
            <div className="drawer-header">
              <div>
                <span className="drawer-rank">RANK #{selectedCandidate.rank}</span>
                <h2>{selectedCandidate.candidate_name}</h2>
              </div>
              <button onClick={closeDrawer} className="close-btn" aria-label="Close panel">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Drawer Body */}
            <div className="drawer-body">
              {/* Score and Recommendation Card */}
              <div className="detail-hero-card">
                <div className="score-circle-container">
                  <div className="score-circle-value">
                    <span className="score-num">{selectedCandidate.overall_score.toFixed(1)}</span>
                    <span className="score-pct">%</span>
                  </div>
                  <span className="score-circle-label">Overall Score</span>
                </div>
                <div className="hero-details">
                  <span className="label">System Recommendation</span>
                  <span className={`badge badge-large ${getRecommendationClass(selectedCandidate.recommendation)}`}>
                    {selectedCandidate.recommendation}
                  </span>
                  <p className="hero-desc">
                    Deterministic decision outcome based on hard requirement status and overall component weights.
                  </p>
                </div>
              </div>

              {/* Why This Score */}
              <div className="drawer-section">
                <h3>Why this score</h3>
                <ul className="why-list">
                  {selectedCandidate.why_score.map((item, idx) => (
                    <li key={idx} className={item.startsWith('✓') ? 'why-pass' : 'why-fail'}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Component Scores Breakdown */}
              <div className="drawer-section">
                <h3>Component Score Breakdown</h3>
                <div className="components-list">
                  {Object.entries(selectedCandidate.component_scores).map(([comp, score]) => (
                    <div key={comp} className="component-row">
                      <div className="component-row-meta">
                        <span className="component-name">{comp.charAt(0).toUpperCase() + comp.slice(1)}</span>
                        <span className="component-score">{score.toFixed(1)}%</span>
                      </div>
                      <div className="progress-bar-bg">
                        <div className="progress-bar-fill" style={{ width: `${score}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Strengths */}
              <div className="drawer-section">
                <h3>Key Strengths</h3>
                <ul className="bullet-list strengths-list">
                  {selectedCandidate.strengths.map((str, idx) => (
                    <li key={idx}>{str}</li>
                  ))}
                </ul>
              </div>

              {/* Missing Skills */}
              <div className="drawer-section">
                <h3>Missing Skills</h3>
                {selectedCandidate.missing_skills.length > 0 ? (
                  <ul className="bullet-list missing-list">
                    {selectedCandidate.missing_skills.map((skill, idx) => (
                      <li key={idx}>{skill}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="no-missing-text">✓ No missing required or preferred skills detected.</p>
                )}
              </div>

              {/* Confidence Summary */}
              <div className="drawer-section">
                <h3>Verified Skills Confidence</h3>
                <div className="skills-summary-grid">
                  {Object.entries(selectedCandidate.confidence_summary).length > 0 ? (
                    Object.entries(selectedCandidate.confidence_summary)
                      .sort((a, b) => b[1] - a[1])
                      .map(([skill, score]) => (
                        <div key={skill} className="skill-confidence-chip">
                          <span className="skill-name">{skill}</span>
                          <span className={`skill-score ${score >= 75 ? 'text-emerald' : score >= 50 ? 'text-amber' : 'text-rose'}`}>
                            {score.toFixed(0)}
                          </span>
                        </div>
                      ))
                  ) : (
                    <p className="no-missing-text">No skill confidence scores calculated.</p>
                  )}
                </div>
              </div>

            </div>
          </div>
        )}
      </div>

    </div>
  )
}

export default App
