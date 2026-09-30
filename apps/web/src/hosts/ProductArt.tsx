// Authored product minis for the Smytten replica: pastel tile + a drawn bottle, tube, jar or box.
// Drawn, not copied: the replica borrows Smytten's tile language, not any brand's packshots.
type Kind = 'box' | 'bottle' | 'tube' | 'jar'

const TILES: Record<Kind, [string, string]> = {
  box: ['#e9e3ff', '#7b61d6'],
  bottle: ['#dff0ff', '#3b7fcf'],
  tube: ['#dcf5e6', '#2f9a5d'],
  jar: ['#ffe9dc', '#d9793f'],
}

export function ProductArt({ kind, size = 60 }: { kind: Kind; size?: number }) {
  const [bg, ink] = TILES[kind]
  return (
    <svg width={size} height={size} viewBox="0 0 60 60" role="img" aria-hidden="true">
      <rect width="60" height="60" rx="14" fill={bg} />
      {kind === 'box' && (
        <g>
          <rect x="15" y="22" width="30" height="24" rx="3" fill="#fff" stroke={ink} strokeWidth="1.6" />
          <path d="M15 28h30M30 22v24" stroke={ink} strokeWidth="1.6" />
          <path d="M24 22c0-5 6-5 6 0c0-5 6-5 6 0" fill="none" stroke={ink} strokeWidth="1.6" />
          <rect x="18" y="12" width="7" height="9" rx="2" fill={ink} opacity=".35" />
          <rect x="35" y="14" width="6" height="7" rx="2" fill={ink} opacity=".25" />
        </g>
      )}
      {kind === 'bottle' && (
        <g>
          <rect x="25" y="10" width="10" height="7" rx="2" fill={ink} />
          <path d="M22 20c0-2 2-3 4-3h8c2 0 4 1 4 3v26c0 2-2 4-4 4h-8c-2 0-4-2-4-4z" fill="#fff" stroke={ink} strokeWidth="1.6" />
          <rect x="24" y="28" width="12" height="11" rx="2" fill={ink} opacity=".18" />
        </g>
      )}
      {kind === 'tube' && (
        <g>
          <path d="M21 14h18l-3 30h-12z" fill="#fff" stroke={ink} strokeWidth="1.6" strokeLinejoin="round" />
          <rect x="25" y="44" width="10" height="6" rx="1.5" fill={ink} />
          <path d="M22 18h16" stroke={ink} strokeWidth="1.6" />
          <rect x="25" y="25" width="10" height="9" rx="2" fill={ink} opacity=".18" />
        </g>
      )}
      {kind === 'jar' && (
        <g>
          <rect x="17" y="19" width="26" height="8" rx="3" fill={ink} />
          <rect x="15" y="27" width="30" height="20" rx="5" fill="#fff" stroke={ink} strokeWidth="1.6" />
          <rect x="21" y="32" width="18" height="9" rx="2" fill={ink} opacity=".18" />
        </g>
      )}
    </svg>
  )
}
