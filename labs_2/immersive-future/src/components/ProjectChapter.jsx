export function ProjectChapter({ project, eager = false }) {
  return (
    <article
      className={`project project--${project.align}`}
      id={project.id}
      aria-labelledby={`${project.id}-title`}
    >
      <figure className="project__media">
        <img
          src={project.image}
          alt={project.alt}
          width="1672"
          height="941"
          loading="eager"
          fetchPriority={eager ? 'high' : 'low'}
          decoding="async"
        />
        <figcaption className="project__caption">
          <span>{project.title}</span>
          <span>{project.category}</span>
        </figcaption>
      </figure>

      <div className="project__copy">
        <span className="project__number" aria-hidden="true">
          {project.number}
        </span>
        <h2 id={`${project.id}-title`}>{project.description}</h2>
      </div>
    </article>
  )
}
