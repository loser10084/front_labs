export function PersistentChrome() {
  return (
    <header className="chrome" aria-label="Primary navigation">
      <a className="chrome__menu" href="#protocol">
        Menu
      </a>
      <a className="chrome__projects" href="#projects">
        See all projects <span aria-hidden="true">↘</span>
      </a>
      <div className="chrome__sound" aria-label="Sound is off">
        Off <span className="chrome__dot" aria-hidden="true" />
      </div>
    </header>
  )
}
