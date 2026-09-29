import { useGSAP } from '@gsap/react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(useGSAP, ScrollTrigger)

function createSectionTimeline(
  trigger,
  scrub = true,
  start = 'top 98%',
  end = 'bottom 2%',
) {
  return gsap.timeline({
    defaults: { ease: 'none' },
    scrollTrigger: {
      trigger,
      start,
      end,
      scrub,
      invalidateOnRefresh: true,
    },
  })
}

export function useScrollMotion(scopeRef) {
  useGSAP(
    () => {
      const media = gsap.matchMedia()
      let disposed = false

      media.add(
        {
          desktop: '(min-width: 761px)',
          mobile: '(max-width: 760px)',
          reduceMotion: '(prefers-reduced-motion: reduce)',
        },
        (context) => {
          const { mobile, reduceMotion } = context.conditions
          if (reduceMotion) return undefined

          const root = scopeRef.current
          const target = (selector) => root.querySelector(selector)
          const targets = (...selectors) => selectors.map(target).filter(Boolean)

          const backdropLayers = targets(
            '.world-backdrop__ring',
            '.world-backdrop__drone',
            '.world-backdrop__flora',
            '.world-backdrop__terrain',
            '.world-trace--orbit',
            '.world-trace--flight',
            '.world-trace--flora',
            '.world-trace--sonar',
          )
          const traceStrokes = Array.from(
            root.querySelectorAll('.world-trace > *'),
          )

          gsap.set(backdropLayers, { autoAlpha: 0 })
          gsap.set(traceStrokes, {
            strokeDasharray: 1,
            strokeDashoffset: 1,
          })

          const createBackdropChapter = ({
            id,
            trigger,
            endTrigger,
            layer,
            trace,
            start,
            end,
            opacity,
            fromScale,
            settleScale,
            exitScale,
            fromRotation = 0,
            settleRotation = 0,
            exitRotation = 0,
          }) => {
            const strokes = Array.from(trace.querySelectorAll('*'))
            const timeline = gsap.timeline({
              defaults: { ease: 'none' },
              scrollTrigger: {
                id,
                trigger,
                endTrigger,
                start,
                end,
                scrub: mobile ? 0.35 : 0.65,
                invalidateOnRefresh: true,
              },
            })

            timeline
              .fromTo(
                layer,
                {
                  autoAlpha: 0,
                  scale: fromScale,
                  rotation: fromRotation,
                },
                {
                  autoAlpha: opacity,
                  scale: settleScale,
                  rotation: settleRotation,
                  duration: 0.18,
                  immediateRender: false,
                },
                0,
              )
              .to(
                layer,
                {
                  scale: exitScale,
                  rotation: exitRotation,
                  duration: 0.64,
                },
                0.18,
              )
              .to(
                layer,
                {
                  autoAlpha: 0,
                  duration: 0.18,
                },
                0.82,
              )
              .fromTo(
                trace,
                { autoAlpha: 0 },
                {
                  autoAlpha: mobile ? opacity * 0.64 : opacity * 0.82,
                  duration: 0.16,
                  immediateRender: false,
                },
                0,
              )
              .fromTo(
                strokes,
                { strokeDashoffset: 1 },
                {
                  strokeDashoffset: 0,
                  duration: 0.52,
                  stagger: 0.025,
                  immediateRender: false,
                },
                0,
              )
              .to(trace, { autoAlpha: 0, duration: 0.18 }, 0.82)

            return timeline
          }

          createBackdropChapter({
            id: 'backdrop-orbit',
            trigger: target('.hero'),
            layer: target('.world-backdrop__ring'),
            trace: target('.world-trace--orbit'),
            start: 'top top',
            end: 'bottom 28%',
            opacity: mobile ? 0.1 : 0.17,
            fromScale: 0.94,
            settleScale: 1,
            exitScale: 1.06,
            fromRotation: -8,
            settleRotation: -2,
            exitRotation: 10,
          })

          createBackdropChapter({
            id: 'backdrop-flight',
            trigger: target('.manifesto'),
            layer: target('.world-backdrop__drone'),
            trace: target('.world-trace--flight'),
            start: 'top 72%',
            end: 'bottom 28%',
            opacity: mobile ? 0.1 : 0.17,
            fromScale: 0.82,
            settleScale: 0.94,
            exitScale: 1.08,
            fromRotation: -3,
            settleRotation: -1,
            exitRotation: 2,
          })

          createBackdropChapter({
            id: 'backdrop-flora',
            trigger: target('.protocol'),
            endTrigger: target('#synthetic-forest'),
            layer: target('.world-backdrop__flora'),
            trace: target('.world-trace--flora'),
            start: 'top 72%',
            end: 'bottom 28%',
            opacity: mobile ? 0.1 : 0.18,
            fromScale: 0.96,
            settleScale: 1,
            exitScale: 1.035,
          })

          createBackdropChapter({
            id: 'backdrop-lunar-ocean',
            trigger: target('#lunar-archive'),
            endTrigger: target('.mission'),
            layer: target('.world-backdrop__terrain'),
            trace: target('.world-trace--sonar'),
            start: 'top 82%',
            end: 'bottom 22%',
            opacity: mobile ? 0.24 : 0.32,
            fromScale: 1.015,
            settleScale: 1.025,
            exitScale: 1.055,
          })

          gsap.from(Array.from(root.querySelectorAll('.chrome > *')), {
            autoAlpha: 0,
            y: -8,
            duration: 0.35,
            stagger: 0.035,
            ease: 'power2.out',
          })

          gsap
            .timeline({
              defaults: { ease: 'none' },
              scrollTrigger: {
                trigger: target('.hero'),
                start: 'top top',
                end: 'bottom top',
                scrub: 0.2,
                invalidateOnRefresh: true,
              },
            })
            .to(
              target('.hero__image'),
              { yPercent: mobile ? 4 : 8, scale: 1.04 },
              0,
            )
            .to(
              target('.hero__scroll'),
              { autoAlpha: 0, y: -14, duration: 0.24 },
              0,
            )
            .to(
              targets('.hero__brand', '.hero__title'),
              {
                autoAlpha: 0.22,
                y: mobile ? -18 : -32,
                duration: 0.55,
              },
              0.3,
            )

          createSectionTimeline(target('.manifesto'))
            .fromTo(
              target('.manifesto .section-index'),
              { autoAlpha: 0, y: mobile ? 20 : 28 },
              { autoAlpha: 1, y: 0, duration: 0.04 },
              0,
            )
            .fromTo(
              target('.manifesto h2'),
              { autoAlpha: 0, y: mobile ? 42 : 68 },
              { autoAlpha: 1, y: 0, duration: 0.08 },
              0.01,
            )
            .to(
              targets('.manifesto .section-index', '.manifesto h2'),
              {
                autoAlpha: 0.45,
                y: mobile ? -24 : -42,
                duration: 0.1,
              },
              0.9,
            )

          createSectionTimeline(target('.protocol'))
            .fromTo(
              target('.protocol .section-label'),
              { autoAlpha: 0, y: 24 },
              { autoAlpha: 1, y: 0, duration: 0.04 },
              0,
            )
            .fromTo(
              target('.protocol h2'),
              { autoAlpha: 0, y: mobile ? 38 : 58 },
              { autoAlpha: 1, y: 0, duration: 0.08 },
              0.01,
            )
            .to(
              targets('.protocol .section-label', '.protocol h2'),
              {
                autoAlpha: 0.45,
                y: mobile ? -22 : -38,
                duration: 0.1,
              },
              0.9,
            )

          Array.from(root.querySelectorAll('.project')).forEach((project) => {
            const mediaElement = project.querySelector('.project__media')
            const image = project.querySelector('.project__media img')
            const copy = project.querySelector('.project__copy')

            createSectionTimeline(project)
              .fromTo(
                mediaElement,
                {
                  autoAlpha: 0,
                  yPercent: mobile ? 8 : 13,
                  scale: mobile ? 0.96 : 0.88,
                },
                { autoAlpha: 1, yPercent: 0, scale: 1, duration: 0.06 },
                0,
              )
              .fromTo(
                image,
                { scale: mobile ? 1.035 : 1.07 },
                { scale: 1.01, duration: 0.96 },
                0,
              )
              .fromTo(
                copy,
                { autoAlpha: 0, y: mobile ? 30 : 48 },
                { autoAlpha: 1, y: 0, duration: 0.08 },
                0,
              )
              .to(
                copy,
                {
                  autoAlpha: 0.55,
                  y: mobile ? -22 : -34,
                  duration: 0.07,
                },
                0.93,
              )
              .to(
                mediaElement,
                {
                  autoAlpha: 0.62,
                  yPercent: mobile ? -4 : -7,
                  scale: 1.012,
                  duration: 0.07,
                },
                0.93,
              )
          })

          createSectionTimeline(target('.mission'))
            .fromTo(
              target('.mission .section-label'),
              { autoAlpha: 0, y: 22 },
              { autoAlpha: 1, y: 0, duration: 0.04 },
              0,
            )
            .fromTo(
              target('.mission h2'),
              { autoAlpha: 0, y: mobile ? 38 : 58 },
              { autoAlpha: 1, y: 0, duration: 0.08 },
              0.01,
            )
            .to(
              targets('.mission .section-label', '.mission h2'),
              { y: mobile ? -12 : -20, duration: 0.4 },
              0.72,
            )

          createSectionTimeline(target('.footer'), 0.8)
            .fromTo(
              target('.footer__image'),
              { scale: 1.07, yPercent: -3 },
              { scale: 1, yPercent: 0, duration: 1 },
              0,
            )
            .fromTo(
              targets('.footer .brand-mark', '.footer a', '.footer p'),
              { autoAlpha: 0, y: 24 },
              {
                autoAlpha: 1,
                y: 0,
                duration: 0.08,
                stagger: 0.04,
              },
              0.04,
            )

          return undefined
        },
        scopeRef,
      )

      const images = Array.from(scopeRef.current.querySelectorAll('img'))
      const refresh = () => {
        if (!disposed) ScrollTrigger.refresh()
      }

      images.forEach((image) => {
        if (!image.complete) image.addEventListener('load', refresh, { once: true })
      })

      document.fonts?.ready.then(refresh)
      const refreshFrame = window.requestAnimationFrame(refresh)

      return () => {
        disposed = true
        window.cancelAnimationFrame(refreshFrame)
        images.forEach((image) => image.removeEventListener('load', refresh))
        media.revert()
      }
    },
    { scope: scopeRef },
  )
}
