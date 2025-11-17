import React, { useState, useEffect } from 'react'
import { getVolumes, getAvailableVolumes } from '../services/api'

const SETTINGS_SECTIONS = [
  {
    title: 'Volumes',
    detail: 'Lock down permitted mounts and enforce SHA-256 hashes on each transfer.',
    items: ['/Volumes/Nexis - Read/Write', '/Shared/Export - Read Only'],
  },
  {
    title: 'Profiles',
    detail: 'Operator profiles with automation node permissions.',
    items: ['Ops Lead – full control', 'Archivist – transfers + audit'],
  },
  {
    title: 'Global Controls',
    detail: 'Settle time, watch mode defaults, and alerts.',
    items: ['Default settle: 30s', 'Watch Mode: continuous', 'Alert channel: Slack'],
  },
]

/**
 * Settings page with structural controls for volumes, profiles, and global defaults.
 */
function SettingsPage() {
  const [volumes, setVolumes] = useState([])
  const [available, setAvailable] = useState([])
  const [status, setStatus] = useState('Loading volumes...')

  useEffect(() => {
    let active = true
    Promise.all([getVolumes(), getAvailableVolumes()])
      .then(([all, availableList]) => {
        if (!active) return
        const allVolumes = Array.isArray(all?.volumes) ? all.volumes : []
        const availableVolumes = Array.isArray(availableList?.volumes)
          ? availableList.volumes
          : availableList || []
        setVolumes(allVolumes)
        setAvailable(availableVolumes)
        setStatus('Volumes synchronized')
      })
      .catch((err) => {
        console.error('Failed to load volumes', err)
        if (active) {
          setStatus('Volumes offline')
        }
      })

    return () => {
      active = false
    }
  }, [])

  const primaryVolumes = volumes.length ? volumes : [{ id: 'vol-nexis', label: 'Nexis Main', status: 'mounted' }]

  return (
    <div id="settings" className="settings-page">
      <div className="ui-container settings-page-shell">
        <section className="settings-section card-panel">
          <header className="settings-page-header">
            <p className="settings-page-eyebrow">Enterprise Controls</p>
            <h2>Policy Settings</h2>
            <p className="settings-page-lede">
              Adjust volume access, operator profiles, and automation defaults within the Manus governance model.
            </p>
          </header>
          <div className="settings-fieldset-grid">
            <fieldset className="settings-fieldset">
              <legend>Volumes</legend>
              <p className="settings-fieldset-status">{status}</p>
              <ul>
                {primaryVolumes.map((volume) => (
                  <li key={volume.id}>
                    <label>
                      <input type="checkbox" defaultChecked={available.includes(volume.id)} />
                      <span>{`${volume.label} · ${volume.status}`}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </fieldset>

            {SETTINGS_SECTIONS.slice(1).map((section) => (
              <fieldset key={section.title} className="settings-fieldset">
                <legend>{section.title}</legend>
                <p className="settings-fieldset-status">{section.detail}</p>
                <ul>
                  {section.items.map((item) => (
                    <li key={item}>
                      <label>
                        <input type="checkbox" defaultChecked />
                        <span>{item}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </fieldset>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default SettingsPage
