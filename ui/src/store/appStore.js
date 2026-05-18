import { create } from 'zustand';

export const useAppStore = create((set) => ({
  health: null,
  setHealth: (health) => set({ health }),
}));
