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
          start_param?: string  // Параметр из deep link (?startapp=xxx)
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
    
    // Разворачиваем на весь экран НЕМЕДЛЕННО
    tg.expand()
    
    // Повторный expand через небольшую задержку для надёжности
    setTimeout(() => {
      tg.expand()
    }, 100)
    
    // Устанавливаем цвета под нашу тему
    try {
      tg.setHeaderColor('#0a0a0a')
      tg.setBackgroundColor('#0a0a0a')
    } catch (e) {
      console.warn('Could not set TG colors:', e)
    }
    
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

/**
 * Получает start_param из deep link (параметр ?startapp=xxx)
 * Используется для открытия конкретного товара по ссылке от AI бота
 */
export function getStartParam(): string | null {
  const tg = getTelegramWebApp()
  if (tg?.initDataUnsafe?.start_param) {
    return tg.initDataUnsafe.start_param
  }
  return null
}

/**
 * Парсит start_param и возвращает ID товара если это ссылка на товар
 * Формат: product_123 -> возвращает 123
 */
export function parseProductFromStartParam(): number | null {
  const startParam = getStartParam()
  if (!startParam) return null
  
  // Проверяем формат product_ID
  const match = startParam.match(/^product_(\d+)$/)
  if (match && match[1]) {
    return parseInt(match[1], 10)
  }
  
  return null
}

