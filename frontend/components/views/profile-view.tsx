"use client"

import { useState, useEffect } from "react"
import { User, Package, CreditCard, Building2, Phone, Copy, Check, ChevronRight, Info, Crown, Shield, Lock, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { getTelegramUser } from "@/lib/telegram"
import { API_URL } from "@/lib/config"

interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  photo_url?: string
  is_premium?: boolean
}

interface Product {
  id: number
  name: string
  image_url: string | null
}

interface OrderItem {
  id: number
  product: Product | null
  quantity: number
  price_at_purchase: number
}

interface Order {
  id: number
  total_amount: number
  status: string
  created_at: string
  items: OrderItem[]
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
  const [showPrivacy, setShowPrivacy] = useState(false)
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const [loadingOrders, setLoadingOrders] = useState(false)
  const [expandedOrderId, setExpandedOrderId] = useState<number | null>(null)

  useEffect(() => {
    const user = getTelegramUser()
    if (user) {
      setTgUser(user)
      fetchOrders(user.id)
    }
  }, [])

  const fetchOrders = async (userId: number) => {
    setLoadingOrders(true)
    try {
      const res = await fetch(`${API_URL}/orders/user/${userId}`)
      if (res.ok) {
        const data = await res.json()
        setOrders(data)
      }
    } catch (err) {
      console.error("Failed to fetch orders:", err)
    } finally {
      setLoadingOrders(false)
    }
  }

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

  // Экран Реквизитов
  if (showRequisites) {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
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

        <p className="text-xs text-muted-foreground text-center mt-2">
          Нажмите на иконку копирования, чтобы скопировать значение
        </p>
      </div>
    )
  }

  // Экран Политики конфиденциальности
  if (showPrivacy) {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
        <div className="flex items-center gap-3 mb-2">
          <Button variant="ghost" size="icon" onClick={() => setShowPrivacy(false)}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <h1 className="text-xl font-bold">Политика конфиденциальности</h1>
        </div>

        <div className="space-y-4 text-sm text-muted-foreground">
            <Card className="bg-white/5 border-white/10 p-4">
                <h3 className="text-white font-bold mb-2 flex items-center gap-2">
                    <Shield className="h-4 w-4 text-green-400" />
                    1. Общие положения
                </h3>
                <p>Мы, RAM US Auto Parts, серьезно относимся к конфиденциальности ваших данных. Мы собираем только ту информацию, которая необходима для оформления и доставки заказа.</p>
            </Card>

            <Card className="bg-white/5 border-white/10 p-4">
                <h3 className="text-white font-bold mb-2 flex items-center gap-2">
                    <User className="h-4 w-4 text-blue-400" />
                    2. Какие данные мы собираем
                </h3>
                <ul className="list-disc list-inside space-y-1 ml-1">
                    <li>Имя пользователя Telegram</li>
                    <li>Номер телефона (для связи по заказу)</li>
                    <li>Адрес доставки</li>
                </ul>
            </Card>

            <Card className="bg-white/5 border-white/10 p-4">
                <h3 className="text-white font-bold mb-2 flex items-center gap-2">
                    <Check className="h-4 w-4 text-primary" />
                    3. Использование данных
                </h3>
                <p>Ваши данные используются исключительно для:</p>
                <ul className="list-disc list-inside space-y-1 ml-1 mt-1">
                    <li>Обработки заказов</li>
                    <li>Связи с вами по статусу доставки</li>
                    <li>Улучшения качества сервиса</li>
                </ul>
            </Card>

            <Card className="bg-white/5 border-white/10 p-4">
                <h3 className="text-white font-bold mb-2 flex items-center gap-2">
                    <Lock className="h-4 w-4 text-amber-400" />
                    4. Безопасность
                </h3>
                <p>Мы не передаем ваши данные третьим лицам, за исключением курьерских служб (СДЭК, Почта России) для выполнения доставки вашего заказа.</p>
            </Card>
        </div>
      </div>
    )
  }

  // Главный экран Профиля
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
      <Card className="bg-white/5 border-white/10 overflow-hidden">
        <CardHeader className="pb-2 bg-white/5">
          <CardTitle className="text-base flex items-center gap-2">
            <Package className="h-5 w-5 text-primary" />
            История заказов
          </CardTitle>
        </CardHeader>
        <div className="divide-y divide-white/5">
          {loadingOrders ? (
            <div className="p-4 space-y-3">
                <Skeleton className="h-12 w-full bg-white/5" />
                <Skeleton className="h-12 w-full bg-white/5" />
            </div>
          ) : orders.length > 0 ? (
            orders.map(order => (
                <div key={order.id} className="bg-black/20">
                    <div 
                        className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
                        onClick={() => setExpandedOrderId(expandedOrderId === order.id ? null : order.id)}
                    >
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-bold text-sm">Заказ #{order.id}</span>
                                <Badge variant="outline" className="text-[10px] border-white/10">
                                    {new Date(order.created_at).toLocaleDateString()}
                                </Badge>
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs text-muted-foreground">{order.items.length} товаров</span>
                                <span className="text-xs font-bold text-primary">
                                    {order.total_amount.toLocaleString()} ₽
                                </span>
                            </div>
                        </div>
                        {expandedOrderId === order.id ? (
                            <ChevronUp className="h-5 w-5 text-muted-foreground" />
                        ) : (
                            <ChevronDown className="h-5 w-5 text-muted-foreground" />
                        )}
                    </div>
                    
                    {/* Expanded Details */}
                    {expandedOrderId === order.id && (
                        <div className="p-4 pt-0 bg-black/40 border-t border-white/5 animate-in slide-in-from-top-2">
                            <div className="space-y-3 mt-3">
                                {order.items.map(item => (
                                    <div key={item.id} className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded bg-white/10 flex-shrink-0 overflow-hidden">
                                            {item.product?.image_url ? (
                                                <img src={item.product.image_url} className="w-full h-full object-cover" alt="" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center">
                                                    <Package className="h-4 w-4 text-muted-foreground" />
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-medium truncate">{item.product?.name || "Товар удален"}</p>
                                            <p className="text-[10px] text-muted-foreground">
                                                {item.quantity} шт x {item.price_at_purchase.toLocaleString()} ₽
                                            </p>
                                        </div>
                                    </div>
                                ))}
                                <div className="pt-2 border-t border-white/10 flex justify-between items-center">
                                    <span className="text-xs text-muted-foreground">Статус:</span>
                                    <Badge className={
                                        order.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
                                        order.status === 'paid' ? 'bg-green-500/20 text-green-400' :
                                        'bg-white/10 text-white'
                                    }>
                                        {order.status === 'pending' ? 'В обработке' : 
                                         order.status === 'paid' ? 'Оплачен' : order.status}
                                    </Badge>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            ))
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center p-4">
              <Package className="h-10 w-10 text-muted-foreground mb-2 opacity-50" />
              <p className="text-sm text-muted-foreground">Заказов пока нет</p>
              <p className="text-xs text-muted-foreground/70">История ваших покупок будет здесь</p>
            </div>
          )}
        </div>
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

        <Card 
          className="bg-white/5 border-white/10 cursor-pointer hover:bg-white/10 transition-all"
          onClick={() => setShowPrivacy(true)}
        >
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Shield className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="font-medium">Конфиденциальность</p>
                <p className="text-xs text-muted-foreground">Политика обработки данных</p>
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
