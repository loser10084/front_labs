export function WorldBackdrop() {
  return (
    <div className="world-backdrop" aria-hidden="true">
      <div className="world-backdrop__ambient" />

      <img
        className="world-backdrop__terrain"
        src="/assets/backdrops/lunar-ocean-transition.webp"
        alt=""
        width="1672"
        height="941"
        loading="eager"
        decoding="async"
      />
      <img
        className="world-backdrop__relief world-backdrop__ring"
        src="/assets/backdrops/relief-orbital-ring.webp"
        alt=""
        width="1800"
        height="1350"
        fetchPriority="high"
        decoding="async"
      />
      <img
        className="world-backdrop__relief world-backdrop__drone"
        src="/assets/backdrops/relief-bio-drone.webp"
        alt=""
        width="1800"
        height="1350"
        loading="eager"
        decoding="async"
      />
      <img
        className="world-backdrop__relief world-backdrop__flora"
        src="/assets/backdrops/relief-data-flora.webp"
        alt=""
        width="1800"
        height="1350"
        loading="eager"
        decoding="async"
      />

      <svg
        className="world-backdrop__traces"
        viewBox="0 0 1440 1000"
        preserveAspectRatio="none"
        focusable="false"
      >
        <g className="world-trace world-trace--orbit">
          <ellipse pathLength="1" cx="1220" cy="110" rx="440" ry="235" />
          <ellipse pathLength="1" cx="1220" cy="110" rx="365" ry="190" />
          <path pathLength="1" d="M760 92C970 230 1190 286 1510 250" />
        </g>
        <g className="world-trace world-trace--flight">
          <path pathLength="1" d="M1510 170C1150 190 920 340 790 520S390 820-90 720" />
          <path pathLength="1" d="M1510 218C1170 242 980 364 842 542S410 770-90 666" />
          <path pathLength="1" d="M1510 264C1220 286 1030 396 900 560S480 724-70 612" />
        </g>
        <g className="world-trace world-trace--flora">
          <path pathLength="1" d="M-40 980C120 740 250 610 440 510S700 300 720 40" />
          <path pathLength="1" d="M170 860C230 690 350 610 520 568" />
          <path pathLength="1" d="M340 650C388 510 490 430 626 390" />
          <path pathLength="1" d="M500 440C548 300 630 220 710 170" />
        </g>
        <g className="world-trace world-trace--sonar">
          <circle pathLength="1" cx="1180" cy="720" r="86" />
          <circle pathLength="1" cx="1180" cy="720" r="168" />
          <circle pathLength="1" cx="1180" cy="720" r="254" />
          <path pathLength="1" d="M780 786C930 690 1030 650 1180 720S1410 828 1520 746" />
        </g>
      </svg>
    </div>
  )
}
