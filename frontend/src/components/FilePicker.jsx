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

  // Options
  // Week 6: Operation Mode (COPY/MOVE)
  const [operationMode, setOperationMode] = useState('copy')

  // Week 6: Continuous Watch Mode (AUTOMAÇÃO)
  // This is the ONLY watch mode - transfers monitor indefinitely
  const [isContinuousWatch, setIsContinuousWatch] = useState(false)

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
      const transfer = await createTransfer(
        sourcePath,
        destPath,
        false,              // watchMode disabled (removed)
        30,                 // settleTime not used anymore
        operationMode,
        isContinuousWatch
      )
      setSuccess(true)
      setSourcePath('')
      setDestPath('')
      setOperationMode('copy')
      setIsContinuousWatch(false)

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

        {/* Operation Mode: COPY vs MOVE */}
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
            COPY: Keeps files at source (backup scenario)
            MOVE: Deletes files from source after checksum verification (offload scenario)
          </p>
        </div>

        {/* Continuous Watch Mode - PRIMARY AUTOMATION FEATURE */}
        <div className="form-group continuous-watch-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isContinuousWatch}
              onChange={(e) => setIsContinuousWatch(e.target.checked)}
              disabled={isSubmitting}
            />
            <span className="checkbox-text">
              Enable Continuous Monitoring (AUTOMATION)
            </span>
          </label>
          {isContinuousWatch && (
            <div className="automation-info-consolidated">
              <h4>Como Funciona a AUTOMAÇÃO CONTÍNUA:</h4>
              <ol>
                <li><strong>Paths:</strong> Mac: /Volumes/VolumeName/path | Windows: D:\path | Linux: /mnt/path</li>
                <li><strong>Transfer Mode:</strong> Choose COPY (backup) or MOVE (offload)</li>
                <li><strong>Enable Continuous Monitoring:</strong> Checkbox ativará automação indefinida</li>
                <li><strong>Submit:</strong> Transfer criada e monitoramento inicia imediatamente</li>
                <li><strong>Automação:</strong> Pasta monitorada a cada 30 segundos para novos arquivos</li>
                <li><strong>Transferência:</strong> Novos arquivos transferidos automaticamente com triple SHA-256</li>
                <li><strong>Gerenciar:</strong> Ver status em "Transfer History", pausar com "Stop Watch", deletar quando pronto</li>
              </ol>
            </div>
          )}
        </div>

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
    </div>
  )
}

export default FilePicker
