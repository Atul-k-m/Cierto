import { motion, type HTMLMotionProps } from 'motion/react'

// Treated photos in three widths and three formats; the browser takes the smallest one that fits.
const W = [800, 1280, 1800]
const set = (base: string, ext: string) => W.map((w) => `/site/photo/${base}-${w}.${ext} ${w}w`).join(', ')

export function Photo({ base, alt, sizes, width, height, className, motionProps }: {
  base: string; alt: string; sizes: string; width: number; height: number; className?: string; motionProps?: HTMLMotionProps<'img'>
}) {
  return (
    <picture>
      <source type="image/avif" srcSet={set(base, 'avif')} sizes={sizes} />
      <source type="image/webp" srcSet={set(base, 'webp')} sizes={sizes} />
      <motion.img className={className} src={`/site/photo/${base}-1280.jpg`} srcSet={set(base, 'jpg')} sizes={sizes} alt={alt}
        width={width} height={height} loading="lazy" decoding="async" {...motionProps} />
    </picture>
  )
}
