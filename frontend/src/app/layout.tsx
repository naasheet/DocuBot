import type { Metadata } from 'next'
import { Space_Grotesk, Playfair_Display } from 'next/font/google'
import './globals.css'
import Toaster from '../components/ui/Toaster'
import AppHeader from '../components/layout/AppHeader'
import AppFooter from '../components/layout/AppFooter'
import TaskCenter from '../components/TaskCenter'

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-sans',
})
const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-display',
})

export const metadata: Metadata = {
  title: 'DocuBot - AI Documentation Generator',
  description: 'Auto-generate documentation for your GitHub repositories',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${spaceGrotesk.variable} ${playfair.variable} font-sans`}>
        <AppHeader />
        {children}
        <AppFooter />
        <Toaster />
        <TaskCenter />
      </body>
    </html>
  )
}
