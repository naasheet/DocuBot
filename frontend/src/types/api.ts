export interface User {
  id: number
  email: string
  full_name: string
}

export interface Repository {
  id: number
  name: string
  full_name: string
  description: string
  url: string
}

export interface Documentation {
  id: number
  repository_id: number
  doc_type: string
  content: string
  version: string
}
