import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Vehicle {
  make: string
  model: string
  year: number
  engine: string
}

interface GarageStore {
  selectedVehicle: Vehicle | null
  setVehicle: (vehicle: Vehicle | null) => void
  clearVehicle: () => void
}

export const useGarageStore = create<GarageStore>()(
  persist(
    (set) => ({
      selectedVehicle: null,
      setVehicle: (vehicle) => set({ selectedVehicle: vehicle }),
      clearVehicle: () => set({ selectedVehicle: null }),
    }),
    {
      name: 'ram-us-garage',
    }
  )
)

