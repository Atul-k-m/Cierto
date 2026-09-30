import { Bike, ChefHat, ChevronLeft, ChevronRight, Headset, House, MapPin, Phone, ShieldCheck, Utensils } from 'lucide-react'
import { ConceptLabel } from '../../shared/ConceptLabel'
import { minutesUntil, useOrder, useSession } from '../../shared/demo'
import type { OrderView } from '../../widget/types'
import '../../widget/element'
import { RouteMap } from '../RouteMap'

const PALETTE = { ground: '#e2eee5', plot: '#e9f3ec', street: '#ffffff', arterial: '#cfe8d6', park: '#c3e4cb', water: '#cde6ee', route: '#1c8743', label: '#5f7667' }
const ADDRESS = '14th Main, HSR Layout Sector 6'

function progress(v: OrderView | null): number {
  if (!v || !v.eta) return 0
  const picked = v.timeline.find((t) => t.text.startsWith('Picked up'))
  if (!picked) return 0
  const start = new Date(picked.at).getTime()
  return Math.min(0.95, (new Date(v.now).getTime() - start) / (new Date(v.eta.due).getTime() - start))
}

function Live({ v }: { v: OrderView | null }) {
  const mins = v?.eta ? minutesUntil(v.eta.due, v.now) : null
  const cooking = !v || v.state === 'preparing'
  return (
    <>
      <div className="map-wrap">
        <RouteMap
          progress={progress(v)} palette={PALETTE} height={300} arterial="27TH MAIN ROAD" area="HSR Layout"
          origin={<span className="pin kitchen"><Utensils size={15} /></span>}
          home={<span className="pin home"><House size={15} /></span>}
          rider={<span className="rider"><Bike size={18} /></span>}
        />
        {mins != null && (
          <p className="arriving" aria-live="polite"><span className="arriving-label">Arriving in</span><span className="arriving-time">{mins} minutes</span></p>
        )}
      </div>
      <section className="deliver-to">
        <p className="green-label">Delivering to</p>
        <p className="address"><strong>Home</strong><MapPin size={14} /> {ADDRESS}</p>
      </section>
      <section className="people">
        <div className="person chef">
          <span className="face"><ChefHat size={20} /></span>
          <p className="strong">{v?.extras.kitchen ?? 'Our chefs'}</p>
          <p className="muted">{cooking ? 'is preparing your order' : 'has prepared your order'}</p>
        </div>
        <div className="person rider-card">
          <span className="face"><Bike size={20} /></span>
          <button className="call" aria-label={`Call ${v?.extras.rider ?? 'rider'}`}><Phone size={16} /></button>
          <p className="strong">{v?.extras.rider ?? 'Your rider'}</p>
          <p className="muted">{cooking ? 'will pick it up next' : 'is on the way to deliver'}</p>
        </div>
      </section>
      <button className="safety"><ShieldCheck size={22} /><span className="grow"><span className="strong">Our kitchen is just minutes away</span>
        <span className="muted block">Learn how we ensure safe delivery</span></span><ChevronRight size={18} /></button>
    </>
  )
}

function AfterDelivery({ session, v }: { session: string; v: OrderView }) {
  return (
    <>
      <section className="after">
        <wismo-order session={session} order="swish" variant="after-delivered" theme="swish" />
      </section>
      <section className="summary">
        <p className="strong">Your order</p>
        <ul>{v.items.map((i) => <li key={i}><span className="veg" aria-label="Veg" />{i}</li>)}</ul>
        <p className="total"><span>Paid</span><span>₹{v.amount_inr}</span></p>
      </section>
      <section className="deliver-to boxed">
        <p className="green-label">Delivered to</p>
        <p className="address"><strong>Home</strong><MapPin size={14} /> {ADDRESS}</p>
      </section>
    </>
  )
}

export function App() {
  const session = useSession()
  const v = useOrder(session, 'swish')
  const claimed = v && v.proof.state !== 'none'
  return (
    <div className="app">
      <ConceptLabel brand="Swish" className="concept" />
      <header className="bar">
        <button className="back" aria-label="Back"><ChevronLeft size={20} /></button>
        <h1>Order status</h1>
        <button className="help"><span>Help</span><Headset size={16} /></button>
      </header>
      <main>{session && claimed ? <AfterDelivery session={session} v={v} /> : <Live v={v} />}</main>
    </div>
  )
}
