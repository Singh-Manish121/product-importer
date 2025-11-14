const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function uploadCsv(file) {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch(`${API_BASE}/uploads`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Upload failed: ${res.status} ${text}`)
  }
  return res.json()
}

export async function listJobs() {
  const res = await fetch(`${API_BASE}/jobs`)
  if (!res.ok) throw new Error('Failed to fetch jobs')
  return res.json()
}

export async function getJob(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`)
  if (!res.ok) throw new Error('Failed to fetch job')
  return res.json()
}

export default { uploadCsv, listJobs, getJob }
