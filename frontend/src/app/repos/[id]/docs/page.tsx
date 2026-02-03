import { redirect } from 'next/navigation'

export default function DocsPage({ params }: { params: { id: string } }) {
  redirect(`/docs/${params.id}`)
}
