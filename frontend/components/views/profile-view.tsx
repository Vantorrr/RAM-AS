"use client"

import { useState, useEffect } from "react"
import { User, Package, CreditCard, Building2, Phone, Copy, Check, ChevronRight, Info, Crown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { getTelegramUser, getTelegramWebApp } from "@/lib/telegram"

interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  photo_url?: string
  is_premium?: boolean
}

// Реквизиты компании
const REQUISITES = {
  company: "ИП Решетникова Кристина Евгеньевна",
  inn: "519090741487",
  ogrnip: "325784700406601",
  account: "40802810300008948074",
  bank: "АО «ТБанк»",
  bik: "044525974",
  corrAccount: "30101810145250000974",
  address: "г. Санкт-Петербург"
}

export function ProfileView() {
  const [copiedField, setCopiedField] = useState<string | null>(null)
  const [showRequisites, setShowRequisites] = useState(false)
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null)

  useEffect(() => {
    const user = getTelegramUser()
    if (user) {
      setTgUser(user)
    }
  }, [])

  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const CopyButton = ({ value, field }: { value: string, field: string }) => (
    <Button
      variant="ghost"
      size="icon"
      className="h-8 w-8 text-muted-foreground hover:text-primary"
      onClick={() => copyToClipboard(value, field)}
    >
      {copiedField === field ? (
        <Check className="h-4 w-4 text-green-500" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </Button>
  )

  if (showRequisites) {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4">
        <div className="flex items-center gap-3 mb-2">
          <Button variant="ghost" size="icon" onClick={() => setShowRequisites(false)}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <h1 className="text-xl font-bold">Реквизиты для оплаты</h1>
        </div>

        {/* Компания */}
        <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-lg bg-primary/20">
                <Building2 className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Получатель</p>
                <p className="font-semibold text-sm">{REQUISITES.company}</p>
              </div>
            </div>
            <Badge className="bg-green-500/20 text-green-400 border-0 text-xs">
              ✓ Официальный продавец
            </Badge>
          </CardContent>
        </Card>

        {/* Основные реквизиты */}
        <Card className="bg-white/5 border-white/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Реквизиты</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">ИНН</p>
                <p className="font-mono font-medium">{REQUISITES.inn}</p>
              </div>
              <CopyButton value={REQUISITES.inn} field="inn" />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">ОГРНИП</p>
                <p className="font-mono font-medium">{REQUISITES.ogrnip}</p>
              </div>
              <CopyButton value={REQUISITES.ogrnip} field="ogrnip" />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Расчётный счёт</p>
                <p className="font-mono font-medium text-sm">{REQUISITES.account}</p>
              </div>
              <CopyButton value={REQUISITES.account} field="account" />
            </div>
          </CardContent>
        </Card>

        {/* Банк */}
        <Card className="bg-white/5 border-white/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Банк</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-xs text-muted-foreground">Название банка</p>
              <p className="font-medium">{REQUISITES.bank}</p>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">БИК</p>
                <p className="font-mono font-medium">{REQUISITES.bik}</p>
              </div>
              <CopyButton value={REQUISITES.bik} field="bik" />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Корр. счёт</p>
                <p className="font-mono font-medium text-sm">{REQUISITES.corrAccount}</p>
              </div>
              <CopyButton value={REQUISITES.corrAccount} field="corr" />
            </div>
          </CardContent>
        </Card>

        {/* Адрес */}
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <Info className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Адрес</p>
              <p className="font-medium text-sm">{REQUISITES.address}</p>
            </div>
          </CardContent>
        </Card>

        <p className="text-xs text-muted-foreground text-center mt-2">
          Нажмите на иконку копирования, чтобы скопировать значение
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 pb-24 px-4 pt-4">
      <h1 className="text-xl font-bold mb-2">Профиль</h1>

      {/* User Card */}
      <Card className="bg-gradient-to-br from-zinc-800/50 to-zinc-900/50 border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            {tgUser?.photo_url ? (
              <img 
                src={tgUser.photo_url} 
                alt="Avatar" 
                className="h-16 w-16 rounded-full border-2 border-primary/30 object-cover"
              />
            ) : (
              <div className="h-16 w-16 rounded-full bg-primary/20 flex items-center justify-center border-2 border-primary/30">
                <User className="h-8 w-8 text-primary" />
              </div>
            )}
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold">
                  {tgUser ? `${tgUser.first_name}${tgUser.last_name ? ` ${tgUser.last_name}` : ''}` : 'Гость'}
                </h2>
                {tgUser?.is_premium && (
                  <Crown className="h-4 w-4 text-yellow-400" />
                )}
              </div>
              {tgUser?.username ? (
                <p className="text-sm text-muted-foreground">@{tgUser.username}</p>
              ) : (
                <p className="text-sm text-muted-foreground">Telegram WebApp</p>
              )}
              {tgUser && (
                <Badge className="mt-1 bg-green-500/20 text-green-400 border-0 text-xs">
                  ✓ Авторизован
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Orders */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Package className="h-5 w-5 text-primary" />
            Мои заказы
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <Package className="h-10 w-10 text-muted-foreground mb-2 opacity-50" />
            <p className="text-sm text-muted-foreground">Заказов пока нет</p>
            <p className="text-xs text-muted-foreground/70">Сделайте первый заказ в каталоге</p>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="space-y-2">
        <Card 
          className="bg-white/5 border-white/10 cursor-pointer hover:bg-white/10 transition-all"
          onClick={() => setShowRequisites(true)}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/20">
                <CreditCard className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="font-medium">Реквизиты для оплаты</p>
                <p className="text-xs text-muted-foreground">Оплата по счёту</p>
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10 cursor-pointer hover:bg-white/10 transition-all">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Phone className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="font-medium">Связаться с нами</p>
                <p className="text-xs text-muted-foreground">Telegram, WhatsApp</p>
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10 cursor-pointer hover:bg-white/10 transition-all">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Building2 className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="font-medium">О компании</p>
                <p className="text-xs text-muted-foreground">12+ лет на рынке</p>
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
