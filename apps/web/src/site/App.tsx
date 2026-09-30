import { Footer, Nav } from './parts/Chrome'
import { useSmoothScroll } from './parts/Smooth'

// The shell every page shares. Pages are plain URLs: navigation is a full page load with a cross-document view transition.
export function App({ path, children }: { path: string; children: React.ReactNode }) {
  useSmoothScroll()
  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <Nav path={path} />
      {children}
      <Footer />
    </>
  )
}
