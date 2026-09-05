import { useState, useCallback } from 'react'
import { CubeView, type SceneMode } from './CubeView'
import Github from './Github'

// GitHub user + repo for the attribution footer / header link.
const GH_USER = 'bruzz-bruzz'
const GH_REPO = 'https://github.com/bruzz-bruzz/spinning-cube'

export default function App() {
  const [mode, setMode] = useState<SceneMode>('cube')
  const [spinning, setSpinning] = useState(true)
  const [speedX, setSpeedX] = useState(0.4) // rad/sec
  const [speedY, setSpeedY] = useState(0.6) // rad/sec
  const [showHelp, setShowHelp] = useState(false)

  // Reset the cube to a nice 3/4 view.
  const handleReset = useCallback(() => {
    setSpinning(false)
    // Trigger a re-render with a fixed angle.
    setAngles({ ax: Math.PI / 7, ay: Math.PI / 5 })
  }, [])

  // For "reset", we use fixedAngles to pause and show a specific pose.
  const [angles, setAngles] = useState<{ ax: number; ay: number } | null>(null)

  return (
    <div className="flex flex-col h-screen w-screen bg-terminal-bg text-terminal-fg overflow-hidden">
      {/* Header bar */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-950/60 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]" />
          <h1 className="text-sm font-semibold tracking-wide">
            spinning-cube
          </h1>
          <span className="text-xs text-zinc-500 hidden sm:inline">
            · ASCII 3D renderer
          </span>
          {/* Scene-mode toggle (cube / donut). */}
          <div className="ml-3 flex items-center rounded border border-zinc-700 overflow-hidden text-[11px] font-mono">
            <button
              onClick={() => setMode('cube')}
              aria-pressed={mode === 'cube'}
              className={`px-2 py-0.5 transition-colors ${
                mode === 'cube'
                  ? 'bg-emerald-400/15 text-emerald-300'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              cube
            </button>
            <button
              onClick={() => setMode('donut')}
              aria-pressed={mode === 'donut'}
              className={`px-2 py-0.5 border-l border-zinc-700 transition-colors ${
                mode === 'donut'
                  ? 'bg-emerald-400/15 text-emerald-300'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              donut
            </button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSpinning((s) => !s)}
            className="px-3 py-1 text-xs font-mono rounded border border-zinc-700 hover:border-emerald-400 hover:text-emerald-300 transition-colors"
          >
            {spinning ? '⏸ pause' : '▶ spin'}
          </button>
          <button
            onClick={handleReset}
            className="px-3 py-1 text-xs font-mono rounded border border-zinc-700 hover:border-emerald-400 hover:text-emerald-300 transition-colors"
          >
            ↺ reset
          </button>
          <button
            onClick={() => setShowHelp((s) => !s)}
            className="px-3 py-1 text-xs font-mono rounded border border-zinc-700 hover:border-emerald-400 hover:text-emerald-300 transition-colors"
          >
            ? help
          </button>
          <a
            href={GH_REPO}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="View source on GitHub"
            title="View source on GitHub"
            className="p-1.5 text-zinc-400 hover:text-emerald-300 transition-colors"
          >
            <svg
              viewBox="0 0 16 16"
              className="w-4 h-4 fill-current"
              aria-hidden="true"
            >
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
            </svg>
          </a>
        </div>
      </header>

      {/* Main cube area */}
      <main className="flex-1 relative min-h-0">
        <CubeView
          mode={mode}
          spinning={spinning && angles === null}
          speedX={speedX}
          speedY={speedY}
          fixedAngles={angles}
        />

        {/* Help overlay */}
        {showHelp && (
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-6 z-10 animate-fade-in"
            onClick={() => setShowHelp(false)}
          >
            <div
              className="max-w-md bg-zinc-950 border border-zinc-800 rounded-lg p-6 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-lg font-semibold mb-3 text-emerald-300">
                About
              </h2>
              <p className="text-sm text-zinc-300 leading-relaxed mb-3">
                3D ASCII scenes rendered in pure text, ported from the
                Python terminal version. The cube uses per-pixel Gouraud
                shading on its triangulated faces; the donut uses analytic
                normals on a parametric torus. Both share the same Phong
                lighting (key + fill + specular) and depth buffer.
              </p>
              <p className="text-sm text-zinc-300 leading-relaxed mb-4">
                Use the
                <span className="text-emerald-300 mx-1">cube</span>
                /
                <span className="text-emerald-300 mx-1">donut</span>
                toggle in the header to switch scenes. Drag the sliders to
                change the rotation speed, hit
                <span className="text-emerald-300 mx-1">pause</span>
                to freeze the scene, or
                <span className="text-emerald-300 mx-1">reset</span>
                for the default 3/4 view.
              </p>
              <h3 className="text-sm font-semibold text-zinc-200 mb-2">
                Brightness ramp
              </h3>
              <pre className="text-xs text-zinc-400 bg-zinc-900 p-2 rounded mb-4 overflow-x-auto">
                {' .\'`,:;-+=*#%@$'}
              </pre>
              <button
                onClick={() => setShowHelp(false)}
                className="w-full py-2 text-sm rounded border border-zinc-700 hover:border-emerald-400 hover:text-emerald-300 transition-colors"
              >
                close
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer / controls */}
      <footer className="border-t border-zinc-800 bg-zinc-950/60 backdrop-blur-sm px-4 py-3">
        <div className="max-w-3xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex items-center gap-3">
              <label className="text-xs text-zinc-400 w-12 font-mono">
                X-axis
              </label>
              <input
                type="range"
                min={-2}
                max={2}
                step={0.05}
                value={speedX}
                onChange={(e) => {
                  setSpeedX(Number(e.target.value))
                  setAngles(null)
                }}
                className="flex-1"
              />
              <span className="text-xs text-zinc-500 w-12 text-right font-mono">
                {speedX.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-xs text-zinc-400 w-12 font-mono">
                Y-axis
              </label>
              <input
                type="range"
                min={-2}
                max={2}
                step={0.05}
                value={speedY}
                onChange={(e) => {
                  setSpeedY(Number(e.target.value))
                  setAngles(null)
                }}
                className="flex-1"
              />
              <span className="text-xs text-zinc-500 w-12 text-right font-mono">
                {speedY.toFixed(2)}
              </span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-zinc-800/60">
            <Github user={GH_USER} repo={GH_REPO} />
          </div>
        </div>
      </footer>
    </div>
  )
}
