'use client'

import type { ReactNode } from 'react'

type ConnectGitHubLinkProps = {
  className?: string
  children?: ReactNode
}

export default function ConnectGitHubLink({ className, children }: ConnectGitHubLinkProps) {
  const href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/github`

  const handleClick = () => {
    if (typeof window !== 'undefined') {
      window.location.assign(href)
    }
  }

  return (
    <a href={href} onClick={handleClick} className={className}>
      {children || 'Connect GitHub'}
    </a>
  )
}
