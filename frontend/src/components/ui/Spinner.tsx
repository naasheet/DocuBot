'use client'

type Props = {
  size?: number
  className?: string
}

export default function Spinner({ size = 20, className = '' }: Props) {
  return (
    <div
      className={`inline-block animate-spin rounded-full border-2 border-white/20 border-t-white ${className}`}
      style={{ width: size, height: size }}
      aria-label="Loading"
      role="status"
    />
  )
}
