import React from 'react'

const SIDEBAR_LINKS = [
  { label: 'Overview', subtitle: 'Dashboard', key: 'dashboard' },
  { label: 'Transfers', subtitle: 'Create & Monitor', key: 'transfers' },
  { label: 'Audit', subtitle: 'History & Logs', key: 'audit' },
  { label: 'System Health', subtitle: 'Status & Queues', key: 'system-health' },
  { label: 'Settings', subtitle: 'Config & Profiles', key: 'settings' },
]

/**
 * Sidebar navigation for the core operational screens.
 */
function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span>Ketter</span>
        <strong>Operator</strong>
      </div>

      <nav className="sidebar-links" aria-label="secondary navigation">
        {SIDEBAR_LINKS.map((link) => (
          <a key={link.key} href={`#${link.key}`} className="sidebar-link">
            <span className="sidebar-link-title">{link.label}</span>
            <small className="sidebar-link-subtitle">{link.subtitle}</small>
          </a>
        ))}
      </nav>

      <div className="sidebar-footer">
        <p className="sidebar-footer-title">Queue Health</p>
        <p className="sidebar-footer-value">Nominal · 2 alerts</p>
        <p className="sidebar-footer-note">Auto-rollback ready</p>
      </div>
    </aside>
  )
}

export default Sidebar
