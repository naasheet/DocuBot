export default function DocViewer({ content }: { content: string }) {
  return (
    <div className="prose max-w-none p-4">
      <div dangerouslySetInnerHTML={{ __html: content }} />
    </div>
  )
}
