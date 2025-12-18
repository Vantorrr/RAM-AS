import { create } from 'zustand'
import { API_URL } from './config'
import { getTelegramUser } from './telegram'

interface FavoritesStore {
  favoriteIds: number[]
  isLoading: boolean
  fetchFavorites: () => Promise<void>
  toggleFavorite: (productId: number) => Promise<void>
  isFavorite: (productId: number) => boolean
}

export const useFavoritesStore = create<FavoritesStore>((set, get) => ({
  favoriteIds: [],
  isLoading: false,
  
  fetchFavorites: async () => {
    const user = getTelegramUser()
    if (!user) return
    
    set({ isLoading: true })
    try {
      const res = await fetch(`${API_URL}/favorites/ids?user_telegram_id=${user.id}`)
      if (res.ok) {
        const ids = await res.json()
        set({ favoriteIds: ids })
      }
    } catch (e) {
      console.error("Failed to fetch favorites:", e)
    } finally {
      set({ isLoading: false })
    }
  },

  toggleFavorite: async (productId: number) => {
    const user = getTelegramUser()
    if (!user) return

    // Optimistic update
    const isFav = get().favoriteIds.includes(productId)
    set(state => ({
      favoriteIds: isFav 
        ? state.favoriteIds.filter(id => id !== productId)
        : [...state.favoriteIds, productId]
    }))

    try {
      await fetch(`${API_URL}/favorites/${productId}/toggle?user_telegram_id=${user.id}`, {
        method: 'POST'
      })
    } catch (e) {
      console.error("Failed to toggle favorite:", e)
      // Revert on error
      set(state => ({
        favoriteIds: isFav 
          ? [...state.favoriteIds, productId]
          : state.favoriteIds.filter(id => id !== productId)
      }))
    }
  },

  isFavorite: (productId: number) => {
    return get().favoriteIds.includes(productId)
  }
}))

