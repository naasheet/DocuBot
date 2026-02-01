import { create } from 'zustand'

interface RepoState {
  repos: any[]
  setRepos: (repos: any[]) => void
}

export const useRepoStore = create<RepoState>((set) => ({
  repos: [],
  setRepos: (repos) => set({ repos }),
}))
