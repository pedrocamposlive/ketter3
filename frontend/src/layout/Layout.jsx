import React from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import Footer from '../components/Footer'

/**
 * Primary layout shell for Ketter 3.0.
 * Wraps page sections with the standard header/main/footer structure.
 */
function Layout({ children }) {
  return (
    <div className="app">
      <header className="header header-corporate">
        <div className="header-content">
          <div className="header-main">
            <h1>Ketter 3.0</h1>
            <p className="header-tagline">
              Enterprise-Grade File Transfer with Verified Integrity
            </p>
            <div className="header-subline">
              <span>Manus Integration · Tier 1 Studio Experience</span>
              <span>Structured on Automation Node · Triple SHA-256</span>
            </div>
          </div>
          <div className="header-ops">
            <div className="header-ops-status">
              <span className="header-status-dot"></span>
              <span>Automation Node · Live</span>
            </div>
            <Navbar />
          </div>
        </div>
      </header>

      <div className="layout-body">
        <Sidebar />
        <main className="main-content">
          <div className="ui-container">
            <div className="page-shell">{children}</div>
          </div>
        </main>
      </div>

      <Footer />
    </div>
  )
}

export default Layout
