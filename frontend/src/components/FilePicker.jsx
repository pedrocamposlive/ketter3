import { useState } from 'react'
import { createTransfer } from '../services/api'

/**
 * FilePicker Component
 * Allows operator to create new file transfers with manual path input
 *
 * MRC: Simple form with source/destination paths
 * Week 5: Supports watch mode and settle time configuration
 * Cross-platform: Works with Windows (D:\), Mac (/Volumes/), Linux (/mnt/)
 */
function FilePicker({ onTransferCreated }) {
  // Paths - simple text inputs
  const [sourcePath, setSourcePath] = useState('')
  const [destPath, setDestPath] = useState('')

  // Watch Mode - mutual exclusive options: "none", "once", "continuous"
  const [watchMode, setWatchMode] = useState('none')
  const [settleTime, setSettleTime] = useState(30)

  // Operation Mode: "copy" or "move"
  const [operationMode, setOperationMode] = useState('copy')

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setIsSubmitting(true)

    try {
      // Normalize form state into the API payload schema
      const payload = {
        source_path: sourcePath,
        destination_path: destPath,
        watch_mode: watchMode,
        settle_time_seconds: settleTime,
        operation_mode: operationMode,
      }
      const transfer = await createTransfer(payload)
      setSuccess(true)
      setSourcePath('')
      setDestPath('')
      setWatchMode('none')
      setSettleTime(30)
      setOperationMode('copy')

      // Notify parent component
      if (onTransferCreated) {
        onTransferCreated(transfer)
      }

      // Clear success message after 3s
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="file-picker">
      <form onSubmit={handleSubmit} className="file-picker-form">
        {/* Source Path */}
        <div className="form-group">
          <label htmlFor="sourcePath">Source Path:</label>
          <input
            type="text"
            id="sourcePath"
            value={sourcePath}
            onChange={(e) => setSourcePath(e.target.value)}
            placeholder="Mac: /Volumes/Nexis/Project | Windows: D:\Projects\Audio"
            required
            disabled={isSubmitting}
          />
          <p className="help-text">
            Enter the full path to the source file or folder
          </p>
        </div>

        {/* Destination Path */}
        <div className="form-group">
          <label htmlFor="destPath">Destination Path:</label>
          <input
            type="text"
            id="destPath"
            value={destPath}
            onChange={(e) => setDestPath(e.target.value)}
            placeholder="Mac: /Users/Shared/Backup | Windows: Y:\Backup\2025"
            required
            disabled={isSubmitting}
          />
          <p className="help-text">
            Enter the full path where files should be copied
          </p>
        </div>

        {/* Watch Mode - Radio Buttons (Mutually Exclusive) */}
        <div className="form-group watch-mode-group">
          <label>Watch Mode:</label>
          <div className="radio-group">
            <label className="radio-label">
              <input
                type="radio"
                name="watchMode"
                value="none"
                checked={watchMode === 'none'}
                onChange={(e) => setWatchMode(e.target.value)}
                disabled={isSubmitting}
              />
              <span>No Watch (transfer immediately)</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="watchMode"
                value="once"
                checked={watchMode === 'once'}
                onChange={(e) => setWatchMode(e.target.value)}
                disabled={isSubmitting}
              />
              <span>Watch Once (wait for stability, transfer once)</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="watchMode"
                value="continuous"
                checked={watchMode === 'continuous'}
                onChange={(e) => setWatchMode(e.target.value)}
                disabled={isSubmitting}
              />
              <span>Watch Continuous (monitor indefinitely, auto-transfer)</span>
            </label>
          </div>
          <p className="help-text">
            No Watch: Transfer immediately | Watch Once: Monitor, transfer once | Watch Continuous: Monitor forever, auto-transfer each batch
          </p>
        </div>

        {/* Settle Time - Only show if watch is enabled */}
        {watchMode !== 'none' && (
          <div className="form-group settle-time-group">
            <label htmlFor="settleTime">
              Settle Time (seconds without changes):
            </label>
            <input
              type="number"
              id="settleTime"
              min="5"
              max="300"
              value={settleTime}
              onChange={(e) => setSettleTime(parseInt(e.target.value) || 30)}
              disabled={isSubmitting}
            />
            <p className="help-text">
              How long to wait without file changes before starting transfer (5-300 seconds).
            </p>
          </div>
        )}

        {/* Operation Mode: COPY vs MOVE */}
        {watchMode !== 'none' && (
          <div className="form-group operation-mode-group">
            <label>Transfer Mode:</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="operationMode"
                  value="copy"
                  checked={operationMode === 'copy'}
                  onChange={(e) => setOperationMode(e.target.value)}
                  disabled={isSubmitting}
                />
                <span>COPY (keep originals at source)</span>
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="operationMode"
                  value="move"
                  checked={operationMode === 'move'}
                  onChange={(e) => setOperationMode(e.target.value)}
                  disabled={isSubmitting}
                />
                <span>MOVE (delete originals after transfer)</span>
              </label>
            </div>
            <p className="help-text">
              COPY: Keeps files at source (backup scenario) | MOVE: Deletes files from source after checksum verification (offload scenario)
            </p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isSubmitting || !sourcePath || !destPath}
        >
          {isSubmitting ? 'Creating Transfer...' : 'Create Transfer'}
        </button>

        {/* Error Alert */}
        {error && (
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Success Alert */}
        {success && (
          <div className="alert alert-success">
            <strong>Success!</strong> Transfer created and enqueued.
          </div>
        )}
      </form>

      {/* Instructions */}
      <div className="info-box">
        <h4>Instructions:</h4>
        <ul>
          <li><strong>Mac:</strong> Use /Volumes/VolumeName/path or /Users/Shared/path</li>
          <li><strong>Windows:</strong> Use D:\path or Y:\NetworkDrive\path</li>
          <li><strong>Folders:</strong> Automatically packaged with ZIP Smart (no compression)</li>
          <li><strong>Watch Mode:</strong> Wait for folder to stabilize before transfer</li>
          <li>Transfer will start automatically with triple SHA-256 verification</li>
          <li>Progress will appear in "Active Transfers" section</li>
        </ul>
      </div>
    </div>
  )
}

export default FilePicker
