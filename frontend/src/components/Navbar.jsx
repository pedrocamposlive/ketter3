import React from 'react'

const NAV_ITEMS = [
  { label: 'Dashboard', href: '#dashboard' },
  { label: 'Transfers', href: '#transfers' },
  { label: 'Audit', href: '#audit' },
  { label: 'System Health', href: '#system-health' },
  { label: 'Settings', href: '#settings' },
]

/**
 * Navbar for the operational layout. Stays simplified and link-based.
 */
function Navbar() {
  return (
    <nav className="navbar" aria-label="main navigation">
      <ul className="navbar-links">
        {NAV_ITEMS.map((item) => (
          <li key={item.label}>
            <a href={item.href}>{item.label}</a>
          </li>
        ))}
      </ul>
      <div className="navbar-actions">
        <button className="btn btn-icon" type="button">
          Refresh
        </button>
        <button className="btn btn-icon" type="button">
          Alerts
        </button>
      </div>
    </nav>
  )
}

export default Navbar
