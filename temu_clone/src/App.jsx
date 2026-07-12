import React, { useState, useEffect } from 'react'
import { ShoppingCart, Search, Crown, Zap, TrendingUp, Star, ChevronRight } from 'lucide-react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

function App() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProducts()
  }, [category, search])

  const fetchProducts = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (category !== 'all') params.append('category', category)
      if (search) params.append('search', search)
      const res = await fetch(`${API_URL}/api/products?${params}`)
      const data = await res.json()
      setProducts(data.products || [])
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const addToCart = (product) => {
    setCart([...cart, product])
  }

  const categories = ['all', 'digital', 'subscription', 'template', 'course', 'ebook']

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <Crown className="logo-icon" />
          <span>KingLulu</span>
        </div>
        <div className="search-bar">
          <Search className="search-icon" />
          <input 
            type="text" 
            placeholder="Search empire products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="cart-btn">
          <ShoppingCart />
          {cart.length > 0 && <span className="cart-badge">{cart.length}</span>}
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <h1>Build Your Digital Empire</h1>
          <p>AI bots, passive income systems, and money-making tools — all in one place.</p>
          <div className="hero-stats">
            <div><TrendingUp /> <span>$20K/month target</span></div>
            <div><Zap /> <span>AI-powered</span></div>
            <div><Star /> <span>5-star rated</span></div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <div className="categories">
        {categories.map(cat => (
          <button 
            key={cat}
            className={category === cat ? 'active' : ''}
            onClick={() => setCategory(cat)}
          >
            {cat === 'all' ? 'All Products' : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      {/* Products Grid */}
      <div className="products-grid">
        {loading ? (
          <div className="loading">Loading empire products...</div>
        ) : (
          products.map(product => (
            <div key={product.id} className="product-card">
              <div className="product-image" style={{background: `url(${product.image_url}) center/cover`}}>
                <span className="category-tag">{product.category}</span>
              </div>
              <div className="product-info">
                <h3>{product.name}</h3>
                <p>{product.description}</p>
                <div className="product-meta">
                  <span className="price">${product.price}</span>
                  <div className="rating">
                    <Star className="star" />
                    <span>{product.rating}</span>
                  </div>
                </div>
                <button className="buy-btn" onClick={() => addToCart(product)}>
                  Add to Cart <ChevronRight />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <footer className="footer">
        <p>© 2026 KingLulu Digital Empire — Powered by Viktor A.I.</p>
        <p>Money while you sleep. Bots never sleep.</p>
      </footer>
    </div>
  )
}

export default App
