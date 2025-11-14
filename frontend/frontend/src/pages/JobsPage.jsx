import { useEffect, useState } from 'react'
import { listJobs, getJob } from '../api'

export default function JobsPage() {
  const [jobs, setJobs] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchJobs()
  }, [])

  async function fetchJobs() {
    try {
      const data = await listJobs()
      setJobs(data.items || data)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Jobs</h2>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      <button onClick={fetchJobs}>Refresh</button>
      <ul>
        {jobs.map((j) => (
          <li key={j.job_id}>
            <strong>{j.job_id}</strong> — status: {j.status} — processed: {j.processed_rows}/{j.total_rows}
          </li>
        ))}
      </ul>
    </div>
  )
}
