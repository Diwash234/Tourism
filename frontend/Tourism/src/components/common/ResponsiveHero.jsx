import useResponsive from '../../hooks/useResponsive'

/**
 * Responsive Hero component that adapts to different screen sizes.
 * - Mobile: Stacked layout with smaller text
 * - Tablet: Side-by-side with medium text
 * - Desktop: Full-width with large text
 */
const ResponsiveHero = ({
  title,
  subtitle,
  description,
  image,
  primaryCta,
  secondaryCta,
  backgroundImage,
  overlay = true,
  align = 'center',
  className = '',
}) => {
  const { isMobile, isTablet, isDesktop } = useResponsive()

  const alignments = {
    left: 'text-left items-start',
    center: 'text-center items-center',
    right: 'text-right items-end',
  }

  return (
    <section
      className={`relative overflow-hidden ${className}`}
      style={{
        backgroundImage: backgroundImage ? `url(${backgroundImage})` : undefined,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Overlay */}
      {overlay && (
        <div className="absolute inset-0 bg-gradient-to-b from-black/50 to-black/70" />
      )}

      {/* Content */}
      <div
        className={`relative z-10 mx-auto px-4 ${
          isMobile ? 'py-16 max-w-lg' : isTablet ? 'py-24 max-w-2xl' : 'py-32 max-w-4xl'
        } flex flex-col ${alignments[align]}`}
      >
        {subtitle && (
          <p
            className={`text-emerald-400 font-medium mb-4 ${
              isMobile ? 'text-sm' : 'text-base'
            }`}
          >
            {subtitle}
          </p>
        )}

        <h1
          className={`text-white font-bold leading-tight mb-6 ${
            isMobile ? 'text-3xl' : isTablet ? 'text-4xl' : 'text-5xl lg:text-6xl'
          }`}
        >
          {title}
        </h1>

        {description && (
          <p
            className={`text-gray-200 mb-8 ${
              isMobile ? 'text-base' : isTablet ? 'text-lg' : 'text-xl'
            }`}
          >
            {description}
          </p>
        )}

        {/* CTAs */}
        {(primaryCta || secondaryCta) && (
          <div
            className={`flex gap-4 ${
              isMobile ? 'flex-col w-full' : 'flex-row'
            }`}
          >
            {primaryCta && (
              <a
                href={primaryCta.href}
                className={`inline-flex items-center justify-center px-6 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors ${
                  isMobile ? 'w-full' : ''
                }`}
              >
                {primaryCta.label}
              </a>
            )}
            {secondaryCta && (
              <a
                href={secondaryCta.href}
                className={`inline-flex items-center justify-center px-6 py-3 border-2 border-white text-white font-medium rounded-lg hover:bg-white/10 transition-colors ${
                  isMobile ? 'w-full' : ''
                }`}
              >
                {secondaryCta.label}
              </a>
            )}
          </div>
        )}
      </div>

      {/* Decorative elements */}
      {isDesktop && (
        <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/50 to-transparent" />
      )}
    </section>
  )
}

export default ResponsiveHero
