// Compile a DTCG-format token file into CSS custom properties for the widget's shadow root.
// "Custom UI preference" is this file per host, not a fork of the component.
// appearance.variables (camelCase, Stripe-style) override single tokens: colorAction → --w-color-action,
// colorSurface2 → --w-color-surface-2, fontBody → --w-font-body, radiusSurface → --w-radius-surface.
import neutral from './themes/neutral.tokens.json'
import smytten from './themes/smytten.tokens.json'
import swish from './themes/swish.tokens.json'
import zomato from './themes/zomato.tokens.json'

type TokenNode = { $value?: string; [key: string]: unknown }

export const THEMES: Record<string, TokenNode> = { neutral, smytten, zomato, swish }

export type ThemeName = 'neutral' | 'smytten' | 'zomato' | 'swish'

/** The variables a host may set. Everything else in the widget is derived from these. */
export const APPEARANCE_VARIABLES = [
  'colorInk', 'colorMuted', 'colorSurface', 'colorSurface2', 'colorLine', 'colorAction', 'colorActionInk',
  'colorActionStrong', 'colorOk', 'colorOkSoft', 'colorCheck', 'colorCheckSoft', 'colorAlert', 'colorAlertSoft',
  'colorFocus', 'fontBody', 'radiusSurface', 'radiusControl',
] as const

export type AppearanceVariable = (typeof APPEARANCE_VARIABLES)[number]
export type AppearanceVariables = Partial<Record<AppearanceVariable, string>>

function flatten(node: TokenNode, path: string[], out: Record<string, string>) {
  for (const [key, child] of Object.entries(node)) {
    if (key.startsWith('$') || typeof child !== 'object' || child === null) continue
    const token = child as TokenNode
    if (typeof token.$value === 'string') out[[...path, key].join('-')] = token.$value
    else flatten(token, [...path, key], out)
  }
  return out
}

/** colorSurface2 → color-surface-2 */
export const tokenName = (variable: string) => variable.replace(/([A-Z]|\d+)/g, (m) => `-${m.toLowerCase()}`)

// Plain CSS values only: no way to close the declaration or inject markup.
const SAFE = /^[^;{}<>\\]{1,120}$/
const warned = new Set<string>()

/** Keep only known variables with safe values; report the rest once, for the integrator. */
export function cleanVariables(variables: Record<string, string> | undefined): AppearanceVariables {
  const out: AppearanceVariables = {}
  for (const [name, value] of Object.entries(variables ?? {})) {
    if ((APPEARANCE_VARIABLES as readonly string[]).includes(name) && typeof value === 'string' && SAFE.test(value)) {
      out[name as AppearanceVariable] = value
    } else if (!warned.has(name)) {
      warned.add(name)
      console.warn(`[cierto] ignored appearance.variables.${name}: unknown variable or unsafe value`)
    }
  }
  return out
}

export function themeCss(name: string, variables?: AppearanceVariables): string {
  const tokens = flatten(THEMES[name] ?? THEMES.neutral, [], {})
  for (const [variable, value] of Object.entries(variables ?? {})) {
    const token = tokenName(variable)
    if (token in tokens && value) tokens[token] = value
  }
  return `:host { ${Object.entries(tokens).map(([k, v]) => `--w-${k}: ${v};`).join(' ')} }`
}
