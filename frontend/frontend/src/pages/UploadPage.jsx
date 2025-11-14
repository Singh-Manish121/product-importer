import { useState } from 'react'
import { uploadCsv } from '../api'

export default function UploadPage() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState(null)

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!file) return
    setStatus('Uploading...')
    try {
      const res = await uploadCsv(file)
      setStatus(`Uploaded. job_id: ${res.job_id}`)
    } catch (err) {
      setStatus(`Error: ${err.message}`)
    }
  }

  return (
    <div>
      <h2>Upload CSV</h2>
      <form onSubmit={onSubmit}>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button type="submit">Upload</button>
      </form>
      {status && <p>{status}</p>}
    </div>
  )
}
