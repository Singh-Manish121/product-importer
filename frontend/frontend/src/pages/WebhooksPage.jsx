import { useEffect, useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState([])
  const [newUrl, setNewUrl] = useState('')
  const [newEvents, setNewEvents] = useState('product.created,product.updated')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    fetchWebhooks()
  }, [])

  async function fetchWebhooks() {
    try {
      const { data } = await axios.get(`${API_BASE}/webhooks`)
      setWebhooks(data.items || data)
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!newUrl) {
      setError('URL required')
      return
    }
    try {
      const events = newEvents.split(',').map((e) => e.trim()).filter((e) => e)
      await axios.post(`${API_BASE}/webhooks`, {
        url: newUrl,
        event_types: events,
        enabled: true,
      })
      setSuccess('Webhook created')
      setNewUrl('')
      setNewEvents('product.created,product.updated')
      fetchWebhooks()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  async function handleDelete(id) {
    if (window.confirm('Delete?')) {
      try {
        await axios.delete(`${API_BASE}/webhooks/${id}`)
        setSuccess('Webhook deleted')
        fetchWebhooks()
      } catch (err) {
        setError(err.message)
      }
    }
  }

  return (
    <div>
      <h2>Webhooks</h2>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {success && <div style={{ color: 'green' }}>{success}</div>}

      <form onSubmit={handleCreate}>
        <input
          type="text"
          placeholder="URL (e.g., http://example.com/webhook)"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
        />
        <input
          type="text"
          placeholder="Events (comma-separated, e.g., product.created,product.updated)"
          value={newEvents}
          onChange={(e) => setNewEvents(e.target.value)}
        />
        <button type="submit">Create</button>
      </form>

      <button onClick={fetchWebhooks}>Refresh</button>
      <ul>
        {webhooks.map((w) => (
          <li key={w.id}>
            <strong>{w.url}</strong>
            <br />
            Events: {w.event_types.join(', ')}
            <br />
            Status: {w.enabled ? 'enabled' : 'disabled'} | Last response: {w.last_response_status || 'never'}
            <button onClick={() => handleDelete(w.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
