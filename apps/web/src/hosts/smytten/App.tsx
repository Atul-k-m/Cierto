import { ArrowLeft, Clapperboard, Coins, FlaskConical, Headset, Store, UserRound } from 'lucide-react'
import { useState } from 'react'
import { ConceptLabel } from '../../shared/ConceptLabel'
import { useOrder, useSession } from '../../shared/demo'
import '../../widget/element'
import { ProductArt } from '../ProductArt'

// The replica's own order list (in a real integration, from Smytten's order service).
const ORDERS = [
  { key: 'smytten-delivered', art: 'box' as const },
  { key: 'smytten-late', art: 'bottle' as const },
  { key: 'smytten-ok', art: 'tube' as const },
  { key: 'smytten-refund', art: 'jar' as const },
]

const placedFmt = new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short' })

function OrderCard({ session, orderKey, art }: { session: string; orderKey: string; art: 'box' | 'bottle' | 'tube' | 'jar' }) {
  const v = useOrder(session, orderKey)
  return (
    <li className="order">
      <div className="order-head">
        <ProductArt kind={art} />
        <div className="order-meta">
          <p className="order-title">{v?.title ?? ' '}</p>
          <p className="order-sub">{v?.amount_inr != null && <>₹{v.amount_inr} · prepaid</>}</p>
          <p className="order-ref">
            #{v?.order_ref ?? ''}{v?.placed_at && <> · placed {placedFmt.format(new Date(v.placed_at))}</>}
          </p>
        </div>
      </div>
      <wismo-order session={session} order={orderKey} variant="orders-row" theme="smytten" />
    </li>
  )
}

export function App() {
  const session = useSession()
  const [tab, setTab] = useState<'trial' | 'shop'>('trial')
  return (
    <div className="app">
      <ConceptLabel brand="Smytten" className="concept" />
      <header className="top">
        <div className="bar">
          <button className="icon-btn" aria-label="Back"><ArrowLeft size={22} strokeWidth={2} /></button>
          <h1>My Orders</h1>
          <button className="help"><Headset size={16} strokeWidth={2} />Help</button>
        </div>
        <div className="seg" role="tablist" aria-label="Order type">
          <button role="tab" aria-selected={tab === 'trial'} onClick={() => setTab('trial')}>
            <span className="seg-title">Trial orders</span><span className="seg-sub">Minis &amp; trial boxes</span>
          </button>
          <button role="tab" aria-selected={tab === 'shop'} onClick={() => setTab('shop')}>
            <span className="seg-title">Shop orders</span><span className="seg-sub">Full-size products</span>
          </button>
        </div>
      </header>
      <main>
        {session && tab === 'trial' && (
          <ul className="orders">
            {ORDERS.map((o) => <OrderCard key={o.key} session={session} orderKey={o.key} art={o.art} />)}
          </ul>
        )}
        {tab === 'shop' && <p className="empty">No shop orders yet. Full-size products you buy will show up here.</p>}
      </main>
      <nav className="tabs" aria-label="Main">
        <a><FlaskConical size={22} strokeWidth={1.7} /><span>Trial</span></a>
        <a><Store size={22} strokeWidth={1.7} /><span>Shop</span></a>
        <a><Coins size={22} strokeWidth={1.7} /><span>Rewards</span></a>
        <a><Clapperboard size={22} strokeWidth={1.7} /><span>Buzz</span></a>
        <a aria-current="page"><UserRound size={22} strokeWidth={1.9} /><span>Account</span></a>
      </nav>
    </div>
  )
}
