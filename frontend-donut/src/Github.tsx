interface GithubProps {
  /** GitHub user / org name (without the @). */
  user: string
  /** Full URL of the repository. */
  repo: string
}

/**
 * Compact "made by" footer / credit block with links to the GitHub
 * profile and the project repository. Styled to match the dark
 * terminal aesthetic of the rest of the app.
 *
 * Renders as a small horizontal block — drop it inside a footer or
 * anywhere you want to show attribution.
 */
export default function Github({ user, repo }: GithubProps) {
  return (
    <div className="flex items-center justify-center gap-2 text-[10px] sm:text-xs font-mono text-zinc-500">
      <span>made by</span>
      <a
        href={`https://github.com/${user}`}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 text-zinc-300 hover:text-emerald-300 transition-colors"
      >
        <svg
          viewBox="0 0 16 16"
          className="w-3.5 h-3.5 fill-current"
          aria-hidden="true"
        >
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
        </svg>
        <span>@{user}</span>
      </a>
      <span className="text-zinc-700">·</span>
      <a
        href={repo}
        target="_blank"
        rel="noopener noreferrer"
        className="text-zinc-400 hover:text-emerald-300 hover:underline transition-colors"
      >
        source
      </a>
    </div>
  )
}
