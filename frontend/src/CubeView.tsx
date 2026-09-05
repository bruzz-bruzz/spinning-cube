import { useEffect, useRef, useState } from 'react'
import { createRenderer, type RendererState } from './renderer'

export interface CubeViewProps {
  /** Whether the cube is currently spinning. */
  spinning: boolean
  /** Rotation speed around X axis, in radians/second. */
  speedX: number
  /** Rotation speed around Y axis, in radians/second. */
  speedY: number
  /** Optional fixed rotation angles (radians). When set, spinning is paused. */
  fixedAngles?: { ax: number; ay: number } | null
  /** CSS class for the outer container. */
  className?: string
}

/**
 * Renders the spinning cube to a <pre> element using the same ASCII
 * shading ramp as the terminal version. Sizes itself to fit the parent
 * container by measuring it and converting pixel size to character-cell
 * size (assumes a ~7px-wide × 14px-tall monospace cell at default font).
 */
export function CubeView({
  spinning,
  speedX,
  speedY,
  fixedAngles,
  className,
}: CubeViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const preRef = useRef<HTMLPreElement | null>(null)
  const rendererRef = useRef<RendererState | null>(null)
  const anglesRef = useRef({ ax: 0, ay: 0 })
  const lastFrameRef = useRef<number>(0)
  const [size, setSize] = useState({ cols: 80, rows: 24 })

  // Measure the container and recompute char-cell size on resize.
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const measure = () => {
      // Approximate char-cell size in pixels for a typical monospace font.
      // 0.6em wide, 1.2em tall is a reasonable default for JetBrains Mono
      // and similar fonts. We measure the <pre> indirectly by setting a
      // probe char and reading its computed font size.
      const probe = document.createElement('span')
      probe.style.fontFamily =
        "'JetBrains Mono', 'Fira Code', Menlo, Monaco, Consolas, monospace"
      probe.style.fontSize = '14px'
      probe.style.position = 'absolute'
      probe.style.visibility = 'hidden'
      probe.style.whiteSpace = 'pre'
      probe.textContent = 'M'
      container.appendChild(probe)
      const rect = probe.getBoundingClientRect()
      container.removeChild(probe)
      const charWidth = rect.width || 8.4
      const charHeight = rect.height || 16.8

      const rect2 = container.getBoundingClientRect()
      // Leave a tiny margin so the cube never touches the edge.
      const cols = Math.max(20, Math.floor((rect2.width - 8) / charWidth))
      const rows = Math.max(10, Math.floor((rect2.height - 8) / charHeight))
      setSize({ cols, rows })
    }

    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  // Create / resize renderer when char-cell dimensions change.
  useEffect(() => {
    if (!rendererRef.current) {
      rendererRef.current = createRenderer(size.cols, size.rows)
    } else {
      rendererRef.current.resize(size.cols, size.rows)
    }
  }, [size.cols, size.rows])

  // Animation loop.
  useEffect(() => {
    let rafId = 0
    const tick = (now: number) => {
      const dt =
        lastFrameRef.current === 0
          ? 1 / 60
          : Math.min(0.1, (now - lastFrameRef.current) / 1000)
      lastFrameRef.current = now

      if (spinning) {
        anglesRef.current.ax += speedX * dt
        anglesRef.current.ay += speedY * dt
      } else if (fixedAngles) {
        anglesRef.current.ax = fixedAngles.ax
        anglesRef.current.ay = fixedAngles.ay
      }

      const renderer = rendererRef.current
      if (renderer && preRef.current) {
        const rows = renderer.render(
          anglesRef.current.ax,
          anglesRef.current.ay,
        )
        preRef.current.textContent = rows.join('\n')
      }
      rafId = requestAnimationFrame(tick)
    }
    rafId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafId)
  }, [spinning, speedX, speedY, fixedAngles])

  return (
    <div
      ref={containerRef}
      className={`flex items-center justify-center w-full h-full overflow-hidden ${className ?? ''}`}
    >
      <pre
        ref={preRef}
        className="cube-output text-zinc-200"
        // Dynamically size the font so each char cell is square.
        style={{
          fontSize: '14px',
          lineHeight: 1,
        }}
      />
    </div>
  )
}
