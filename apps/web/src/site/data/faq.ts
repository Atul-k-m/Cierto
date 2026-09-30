import insights from './insights.json'

// The questions a buyer (and an answer engine) asks first. Rendered on the home page and as FAQPage JSON-LD.
const H = insights.compare.headline
const reviews = H.reduce((a, b) => a + (b.reviews ?? 0), 0).toLocaleString('en-IN')
const lo = Math.min(...H.map((b) => b.wismo_low ?? 0)), hi = Math.max(...H.map((b) => b.wismo_low ?? 0))

export const FAQ: { q: string; a: string }[] = [
  { q: 'What is WISMO?',
    a: `WISMO stands for “Where is my order?”: every message, call or review a shopper sends because they can't tell where an order is, why it's late, or whether it really arrived. In ${reviews} public reviews of Smytten, Swish and Zomato that we classified, WISMO made up ${Math.round(lo)}–${Math.round(hi)}% of all 1–2★ reviews.` },
  { q: 'How does Cierto answer “where is my order?”',
    a: 'It joins courier scans, rider GPS, the dispatch stop sequence, payments and the promise made at checkout into one timeline per order, finds the actual cause (a stuck rider, traffic, a batched order, a bad address, a silent courier, a “delivered” nobody received, a slipping date or a refund not credited) and replies with that cause, a new time, a latest-by time and what happens automatically if it is missed. Every answer names its sources and how fresh they are.' },
  { q: 'Does the AI decide refunds or credits?',
    a: 'No. Refunds, credits, cancellations and reattempts follow a versioned policy the business writes and can simulate before it ships, and anything above its cap waits for a person. The language model only rewords the answer, and a check rejects any rewording that changes a number, a time or a date.' },
  { q: 'How long does integration take?',
    a: 'About an afternoon: install the SDK (5 minutes), forward the events you already get from your courier, rider app and payment gateway (1–2 hours), then drop in the widget or render the headless view in your own screens (30 minutes).' },
  { q: 'Which apps and platforms does it work with?',
    a: 'Any business that ships an order: courier-shipped D2C brands where orders take days, and food delivery or 10-minute quick commerce where they take minutes. It ships as a Web Component, a React component, a headless JSON view, a server events API and signed webhooks. React Native, Android, iOS and Flutter SDKs are designed next.' },
  { q: 'Which languages does it answer in?',
    a: 'English and Hinglish (Hindi written in Latin script) today, with the same facts, times and sources in both.' },
  { q: 'Is Cierto live with Smytten, Swish or Zomato?',
    a: 'No. Cierto is a working proof of concept. The three apps appear only in labelled case studies built from public reviews and in concept demos; Cierto is not affiliated with them and uses none of their data.' },
]
