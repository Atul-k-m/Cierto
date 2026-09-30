import { ArrowRight } from 'lucide-react'
import { Cols } from '../parts/Chrome'
import { Mist } from '../parts/Mist'

// A real 404 (the server sends it with status 404), written like the rest of the product: the cause, then what to do.
export function NotFound() {
  return (
    <main id="main" className="nf">
      <Mist cell={3} scale={180} bias={-.05} rise={.5} />
      <div className="frame"><Cols />
        <div className="nf-in">
          <p className="label"><b>404</b> · no page at this address</p>
          <h1 className="display enter">Not delivered.<br />Not here.</h1>
          <p className="lead enter d2">The link may be old or mistyped. Nothing was lost; these are the pages that exist.</p>
          <ul className="nf-links enter d3">
            {[['Home', '/'], ['Live demo', '/demos'], ['Case studies', '/case-studies'], ['Quickstart', '/docs/quickstart']].map(([l, h]) => (
              <li key={h}><a href={h}><span>{l}</span><ArrowRight size={16} aria-hidden="true" /></a></li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  )
}
