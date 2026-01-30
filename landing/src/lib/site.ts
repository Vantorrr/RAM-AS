export const SITE = {
  name: "RAM-US",
  tagline: "Запчасти и тюнинг для американских авто",
  city: "Москва",
} as const

export const LINKS = {
  telegramBot: process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/ram_us_bot",
  telegramCatalog:
    process.env.NEXT_PUBLIC_TELEGRAM_CATALOG_URL || "https://t.me/ram_us_bot/app",
  telegramChannel:
    process.env.NEXT_PUBLIC_TELEGRAM_CHANNEL_URL || "https://t.me/ramus_official",
} as const

