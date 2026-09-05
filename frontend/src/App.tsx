import { useState, useCallback } from 'react'
import { CubeView } from './CubeView'

export default function App() {
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
        </div>
      </header>

      {/* Main cube area */}
      <main className="flex-1 relative min-h-0">
        <CubeView
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
                A 3D spinning cube rendered in pure ASCII, ported from the
                Python terminal version. Each frame rasterises the visible
                faces with per-pixel Gouraud shading, Phong-style lighting
                (key + fill + specular), and a depth buffer.
              </p>
              <p className="text-sm text-zinc-300 leading-relaxed mb-4">
                Drag the sliders to change the rotation speed, hit
                <span className="text-emerald-300 mx-1">pause</span>
                to freeze the cube, or
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
        <div className="max-w-3xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-3">
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
      </footer>
    </div>
  )
}
