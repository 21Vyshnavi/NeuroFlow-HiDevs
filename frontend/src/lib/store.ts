import { create } from 'zustand';

interface AppState {
  sidebarOpen: boolean;
  activePipeline: string | null;
  compareMode: boolean;
  comparePipeline: string | null;

  toggleSidebar: () => void;
  setActivePipeline: (id: string | null) => void;
  toggleCompareMode: () => void;
  setComparePipeline: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  activePipeline: null,
  compareMode: false,
  comparePipeline: null,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setActivePipeline: (id) => set({ activePipeline: id }),
  toggleCompareMode: () =>
    set((state) => ({
      compareMode: !state.compareMode,
      comparePipeline: state.compareMode ? null : state.comparePipeline,
    })),
  setComparePipeline: (id) => set({ comparePipeline: id }),
}));
