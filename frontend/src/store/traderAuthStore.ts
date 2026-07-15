import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface TraderAuthState {
  accessToken: string | null;
  refreshToken: string | null;
  traderId: string | null;
  name: string | null;
  phoneNumber: string | null;

  // Actions
  setAuth: (params: {
    accessToken: string;
    refreshToken: string;
    traderId: string;
    name: string;
    phoneNumber: string;
  }) => void;
  clearAuth: () => void;
  setAccessToken: (token: string) => void;

  // Computed helpers
  isAuthenticated: () => boolean;
}

export const useTraderAuthStore = create<TraderAuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      traderId: null,
      name: null,
      phoneNumber: null,

      setAuth: ({ accessToken, refreshToken, traderId, name, phoneNumber }) =>
        set({ accessToken, refreshToken, traderId, name, phoneNumber }),

      clearAuth: () =>
        set({
          accessToken: null,
          refreshToken: null,
          traderId: null,
          name: null,
          phoneNumber: null,
        }),

      setAccessToken: (token) => set({ accessToken: token }),

      isAuthenticated: () => !!get().accessToken,
    }),
    {
      name: "ghana-tax-trader-auth",
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
