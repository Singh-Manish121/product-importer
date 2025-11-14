import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import './App.css'
import UploadPage from './pages/UploadPage'
import JobsPage from './pages/JobsPage'
import ProductsPage from './pages/ProductsPage'
import WebhooksPage from './pages/WebhooksPage'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="nav">
          <Link to="/">Upload</Link>
          <Link to="/jobs">Jobs</Link>
          <Link to="/products">Products</Link>
          <Link to="/webhooks">Webhooks</Link>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/webhooks" element={<WebhooksPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
