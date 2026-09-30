import { Bike, ChevronDown, ChevronRight, Headset, House, Phone, ReceiptText, RefreshCw, Share2, Utensils } from 'lucide-react'
import { ConceptLabel } from '../../shared/ConceptLabel'
import { minutesUntil, useOrder, useSession } from '../../shared/demo'
import type { OrderView } from '../../widget/types'
import '../../widget/element'
import { RouteMap } from '../RouteMap'

const PALETTE = { ground: '#e6e8e2', plot: '#eceee8', street: '#ffffff', arterial: '#f6d88a', park: '#cfe5c9', water: '#bfd9f2', route: '#2f6cf6', label: '#6e736b' }

// Zomato lets the widget's truth drive its own header (headless tier): the header never says
// "Delivered" in green while the proof is only the rider's tap.
function header(v: OrderView | null): { title: string; chip: string; tone: 'go' | 'check' | 'issue' } {
  if (!v) return { title: 'Getting your order', chip: '', tone: 'go' }
  const mins = v.eta ? minutesUntil(v.eta.due, v.now) : 0
  switch (v.state) {
    case 'preparing': return { title: 'Preparing your order', chip: `${mins} mins • On time`, tone: 'go' }
    case 'rider_assigned': return { title: `${v.extras.rider ?? 'Rider'} is at the restaurant`, chip: `${mins} mins • On time`, tone: 'go' }
    case 'on_the_way': return { title: 'Order is on the way', chip: `${mins} mins • On time`, tone: 'go' }
    case 'delivery_claimed': return { title: 'Marked delivered, not confirmed', chip: 'Did it arrive? Tell us below', tone: 'check' }
    case 'delivery_disputed': return { title: "We're on it", chip: v.issue ? `Issue ${v.issue.id} open` : 'Issue open', tone: 'issue' }
    case 'delivered': return { title: 'Order delivered', chip: 'Enjoy your meal', tone: 'go' }
    default: return { title: 'Order update', chip: '', tone: 'go' }
  }
}

function progress(v: OrderView | null): number {
  if (!v) return 0
  if (v.proof.state !== 'none') return 1
  const picked = v.timeline.find((t) => t.text.startsWith('Picked up'))
  if (!picked || !v.eta) return 0
  const start = new Date(picked.at).getTime()
  const end = new Date(v.eta.due).getTime()
  return Math.min(0.95, (new Date(v.now).getTime() - start) / (end - start))
}

export function App() {
  const session = useSession()
  const v = useOrder(session, 'zomato')
  const h = header(v)
  const riderName = v?.extras.rider ?? 'Your rider'
  return (
    <div className="app">
      <ConceptLabel brand="Zomato" className="concept" />
      <header className={`status ${h.tone}`}>
        <div className="status-bar">
          <button className="icon-btn" aria-label="Minimise"><ChevronDown size={24} /></button>
          <div className="status-text">
            <p className="restaurant">{v?.extras.restaurant ?? ' '}</p>
            <h1 aria-live="polite">{h.title}</h1>
          </div>
          <button className="icon-btn" aria-label="Share"><Share2 size={20} /></button>
        </div>
        {h.chip && (
          <div className="chips"><span className="chip">{h.chip}</span>{h.tone === 'go' && <span className="chip round" aria-hidden="true"><RefreshCw size={14} /></span>}</div>
        )}
      </header>
      <RouteMap
        progress={progress(v)} palette={PALETTE} height={290} arterial="VIKAS MARG" area="Laxmi Nagar"
        showRider={!v || v.proof.state === 'none'}
        origin={<span className="pin food"><Utensils size={15} /></span>}
        home={<span className="pin home"><House size={15} /></span>}
        rider={<span className="rider"><Bike size={18} /></span>}
      />
      <main className="sheet">
        <div className="handle" aria-hidden="true" />
        <section className="row-card">
          <span className="thumb"><Utensils size={20} /></span>
          <div className="grow"><p className="strong">{v?.extras.restaurant ?? 'Restaurant'}</p><p className="muted">{v?.extras.area ?? ''}</p></div>
          <button className="call" aria-label="Call restaurant"><Phone size={18} /></button>
        </section>
        {v && v.proof.state === 'none' && v.state !== 'preparing' && (
          <section className="row-card">
            <span className="thumb rider-thumb"><Bike size={20} /></span>
            <div className="grow"><p className="strong">{riderName}</p><p className="muted">{v.state === 'rider_assigned' ? 'is waiting for your food' : 'is on the way'}</p></div>
            <button className="call" aria-label={`Call ${riderName}`}><Phone size={18} /></button>
          </section>
        )}
        {session && <wismo-order session={session} order="zomato" variant="tracking-card" theme="zomato" />}
        <button className="help-card">
          <span className="help-icon"><Headset size={22} /></span>
          <span className="grow"><span className="strong">Need help with your order</span><span className="muted block">Get help &amp; support</span></span>
          <ChevronRight size={20} />
        </button>
        <button className="line-row"><ReceiptText size={18} /><span className="grow">Order #{v?.order_ref ?? ''}</span><ChevronRight size={18} /></button>
      </main>
    </div>
  )
}
