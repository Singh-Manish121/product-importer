import { useEffect, useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ProductsPage() {
  const [products, setProducts] = useState([])
  const [newName, setNewName] = useState('')
  const [newSku, setNewSku] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    fetchProducts()
  }, [])

  async function fetchProducts() {
    try {
      const { data } = await axios.get(`${API_BASE}/products`)
      setProducts(data.items || data)
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!newSku || !newName) {
      setError('SKU and name required')
      return
    }
    try {
      await axios.post(`${API_BASE}/products`, {
        sku: newSku,
        name: newName,
        description: newDesc || null,
      })
      setSuccess('Product created')
      setNewSku('')
      setNewName('')
      setNewDesc('')
      fetchProducts()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  async function handleDelete(id) {
    if (window.confirm('Delete?')) {
      try {
        await axios.delete(`${API_BASE}/products/${id}`)
        setSuccess('Product deleted')
        fetchProducts()
      } catch (err) {
        setError(err.message)
      }
    }
  }

  return (
    <div>
      <h2>Products</h2>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {success && <div style={{ color: 'green' }}>{success}</div>}

      <form onSubmit={handleCreate}>
        <input
          type="text"
          placeholder="SKU"
          value={newSku}
          onChange={(e) => setNewSku(e.target.value)}
        />
        <input
          type="text"
          placeholder="Name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
        />
        <input
          type="text"
          placeholder="Description"
          value={newDesc}
          onChange={(e) => setNewDesc(e.target.value)}
        />
        <button type="submit">Create</button>
      </form>

      <button onClick={fetchProducts}>Refresh</button>
      <ul>
        {products.map((p) => (
          <li key={p.id}>
            <strong>{p.sku}</strong> - {p.name}
            <button onClick={() => handleDelete(p.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
