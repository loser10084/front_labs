import { useRef } from 'react'
import { BrandMark } from './components/BrandMark.jsx'
import { PersistentChrome } from './components/PersistentChrome.jsx'
import { ProjectChapter } from './components/ProjectChapter.jsx'
import { WorldBackdrop } from './components/WorldBackdrop.jsx'
import { projects } from './data/projects.js'
import { useScrollMotion } from './hooks/useScrollMotion.js'

function Hero() {
  return (
    <section className="hero" id="gateway" aria-labelledby="hero-title">
      <img
        className="hero__image"
        src="/assets/hero/orbital-gateway.webp"
        alt=""
        width="1672"
        height="941"
        fetchPriority="high"
      />
      <div className="hero__brand">
        <BrandMark />
      </div>
      <h1 id="hero-title" className="hero__title">
        Future world
        <br />
        experiences studio
      </h1>
      <a className="hero__scroll" href="#manifesto">
        Scroll down
      </a>
    </section>
  )
}

function Manifesto() {
  return (
    <section className="manifesto" id="manifesto" aria-labelledby="manifesto-title">
      <p className="section-index">Manifesto / 01</p>
      <h2 id="manifesto-title">
        Beyond the known horizon, we imagine places for new forms of life,
        memory and connection.
      </h2>
    </section>
  )
}

function Protocol() {
  return (
    <section className="protocol" id="protocol" aria-labelledby="protocol-title">
      <p className="section-label">Our protocol</p>
      <h2 id="protocol-title">
        Architecture, ecology and technology become one continuous world.
      </h2>
    </section>
  )
}

function Mission() {
  return (
    <section className="mission" id="mission" aria-labelledby="mission-title">
      <p className="section-label">Our mission</p>
      <h2 id="mission-title">
        A future shaped by orbital habitats, synthetic forests, lunar archives
        and ocean colonies.
      </h2>
    </section>
  )
}

function Footer() {
  return (
    <footer className="footer">
      <img
        className="footer__image"
        src="/assets/posters/project-04-ocean-colony.webp"
        alt=""
        width="1672"
        height="941"
        loading="lazy"
        decoding="async"
      />
      <BrandMark />
      <a href="#gateway">Back to gateway ↑</a>
      <p>Orbital · Lunar · Oceanic</p>
    </footer>
  )
}

export default function App() {
  const siteRef = useRef(null)
  useScrollMotion(siteRef)

  return (
    <div ref={siteRef} className="site-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <PersistentChrome />
      <WorldBackdrop />
      <main id="main-content">
        <Hero />
        <Manifesto />
        <Protocol />
        <section className="projects" id="projects" aria-label="Future world projects">
          {projects.map((project, index) => (
            <ProjectChapter key={project.id} project={project} eager={index === 0} />
          ))}
        </section>
        <Mission />
      </main>
      <Footer />
    </div>
  )
}
