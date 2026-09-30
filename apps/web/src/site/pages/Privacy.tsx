import { Cols } from '../parts/Chrome'
import { PageHead } from '../parts/PageHead'

// What this site and its demo actually keep. Every line here is true of the code that serves it; keep it that way.
const FACTS: [string, string][] = [
  ['No cookies', 'Nothing is stored in your browser.'],
  ['No trackers', 'No analytics, ad or social scripts. Fonts and images come from this site.'],
  ['2 hours', 'A demo session is deleted two hours after you stop using it.'],
  ['Gemini', 'Questions typed in the demo go to Google to be reworded.'],
]

const SECTIONS: { h: string; body: React.ReactNode }[] = [
  { h: 'Reading this site', body: <>
    <p>Every page, font, image and script is served from this domain. There are no cookies, nothing in local storage, no analytics, and no advertising or social pixels. The pages work as plain HTML; scripts only add motion and the live demo.</p>
  </> },
  { h: 'The live demo', body: <>
    <p>Opening the <a href="/demos">demo</a>, or the theme preview on the home page, starts a demo session on the server: a set of fictional orders on a virtual clock. The session holds only what you do in it, such as moving the clock, tapping an action or asking a question. It is kept in a Redis database (Upstash) so any server can pick it up, contains no personal data unless you type some, and is deleted after two hours without use.</p>
  </> },
  { h: 'Questions you type', body: <>
    <p>Cierto works out the answer from the demo order's data using its own rules. To word that answer naturally, your question and the order's facts are sent to <b>Google's Gemini API</b>, and the reply is checked so that no number, time or date changes.</p>
    <p>This demo uses Gemini's unpaid tier. Under Google's terms for it, Google may use what is sent to improve its products, and people at Google may review it. <b>Please don't type names, phone numbers, addresses or anything else personal.</b></p>
    <p>If the day's AI budget runs out, Cierto words the answer itself and nothing is sent to Google.</p>
  </> },
  { h: 'Logs and abuse protection', body: <>
    <p>To keep the service up and fair, the server counts requests per IP address per minute and per day, to apply rate limits and a daily cap on AI use. Those counters expire within 24 hours.</p>
    <p>The hosting provider (Vercel) keeps request logs: the time, the address requested, the response status, your IP address and your browser's name, for the short period its plan sets. Request bodies, including your questions, are not written to the logs.</p>
  </> },
  { h: 'When a business runs Cierto', body: <>
    <p>A business that integrates the SDK sends Cierto order events: order and payment status, courier scans, rider location during a delivery, and refund progress. The business decides what it sends and stays responsible for its shoppers' data. Cierto uses that data only to answer questions about the order and to apply that business's own policy.</p>
    <p>The design keeps shopper data narrow. Shoppers are identified by the business's own opaque reference, not by name, phone or email. A browser only ever holds a short-lived customer session scoped to a single order. Webhooks to the business are signed.</p>
  </> },
  { h: 'Changes', body: <>
    <p>This page changes when the code changes. The date at the top shows the last update.</p>
  </> },
]

export function Privacy() {
  return (
    <main id="main">
      <PageHead title="Privacy" lead="This site keeps almost nothing. Here is exactly what it keeps, for how long, and who else sees it.">
        <p className="label enter d3" style={{ marginTop: 28 }}>Updated 30 Sep 2026</p>
      </PageHead>
      <section className="sec">
        <div className="frame"><Cols />
          <div className="sec-in priv">
            <ul className="priv-facts">{FACTS.map(([b, s]) => <li key={b}><b>{b}</b><span>{s}</span></li>)}</ul>
            <div className="priv-body">
              {SECTIONS.map((x, k) => (
                <section className="dseg" key={x.h} id={x.h.toLowerCase().replace(/[^a-z]+/g, '-')}>
                  <div className="dseg-head"><span className="dseg-n num">{String(k + 1).padStart(2, '0')}</span><h2>{x.h}</h2></div>
                  <div className="dseg-body doc-md">{x.body}</div>
                </section>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
