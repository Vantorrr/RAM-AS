"use client"

// Telegram WebApp types
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready: () => void
        expand: () => void
        close: () => void
        isExpanded: boolean
        viewportHeight: number
        viewportStableHeight: number
        headerColor: string
        backgroundColor: string
        themeParams: {
          bg_color?: string
          text_color?: string
          hint_color?: string
          link_color?: string
          button_color?: string
          button_text_color?: string
          secondary_bg_color?: string
        }
        initData: string
        initDataUnsafe: {
          query_id?: string
          user?: {
            id: number
            is_bot?: boolean
            first_name: string
            last_name?: string
            username?: string
            language_code?: string
            is_premium?: boolean
            photo_url?: string
          }
          auth_date?: number
          hash?: string
        }
        colorScheme: 'light' | 'dark'
        setHeaderColor: (color: string) => void
        setBackgroundColor: (color: string) => void
        enableClosingConfirmation: () => void
        disableClosingConfirmation: () => void
        onEvent: (eventType: string, callback: () => void) => void
        offEvent: (eventType: string, callback: () => void) => void
        MainButton: {
          text: string
          color: string
          textColor: string
          isVisible: boolean
          isActive: boolean
          isProgressVisible: boolean
          setText: (text: string) => void
          onClick: (callback: () => void) => void
          offClick: (callback: () => void) => void
          show: () => void
          hide: () => void
          enable: () => void
          disable: () => void
          showProgress: (leaveActive?: boolean) => void
          hideProgress: () => void
        }
        BackButton: {
          isVisible: boolean
          onClick: (callback: () => void) => void
          offClick: (callback: () => void) => void
          show: () => void
          hide: () => void
        }
        HapticFeedback: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
          notificationOccurred: (type: 'error' | 'success' | 'warning') => void
          selectionChanged: () => void
        }
      }
    }
  }
}

export function getTelegramWebApp() {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    return window.Telegram.WebApp
  }
  return null
}

export function initTelegramWebApp() {
  const tg = getTelegramWebApp()
  if (tg) {
    // Сообщаем Telegram что приложение готово
    tg.ready()
    
    // Разворачиваем на весь экран
    tg.expand()
    
    // Устанавливаем цвета под нашу тему
    tg.setHeaderColor('#0a0a0a')
    tg.setBackgroundColor('#0a0a0a')
    
    return tg
  }
  return null
}

export function getTelegramUser() {
  const tg = getTelegramWebApp()
  if (tg?.initDataUnsafe?.user) {
    return tg.initDataUnsafe.user
  }
  return null
}

export function hapticFeedback(type: 'light' | 'medium' | 'heavy' | 'success' | 'error' | 'warning' | 'selection') {
  const tg = getTelegramWebApp()
  if (!tg?.HapticFeedback) return
  
  switch (type) {
    case 'light':
    case 'medium':
    case 'heavy':
      tg.HapticFeedback.impactOccurred(type)
      break
    case 'success':
    case 'error':
    case 'warning':
      tg.HapticFeedback.notificationOccurred(type)
      break
    case 'selection':
      tg.HapticFeedback.selectionChanged()
      break
  }
}

export function closeTelegramWebApp() {
  const tg = getTelegramWebApp()
  if (tg) {
    tg.close()
  }
}

