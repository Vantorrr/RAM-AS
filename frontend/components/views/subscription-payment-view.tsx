"use client"

import { useState, useEffect } from "react"
import { Crown, Check, Loader2, ChevronRight, Star, Zap, Rocket } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { getTelegramUser } from "@/lib/telegram"
import { API_URL } from "@/lib/config"

interface SubscriptionPlan {
  tier: string
  name: string
  price: number
  limit: number
  description: string
}

interface SubscriptionPaymentViewProps {
  onBack: () => void
  sellerId: number
  currentTier: string
}

export function SubscriptionPaymentView({ onBack, sellerId, currentTier }: SubscriptionPaymentViewProps) {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTier, setSelectedTier] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPlans()
  }, [])

  const fetchPlans = async () => {
    try {
      const res = await fetch(`${API_URL}/payments/subscription-plans`)
      if (res.ok) {
        const data = await res.json()
        setPlans(data.plans)
      }
    } catch (err) {
      console.error("Failed to fetch plans:", err)
    } finally {
      setLoading(false)
    }
  }

  const handlePayment = async (tier: string) => {
    setSelectedTier(tier)
    setProcessing(true)
    setError(null)

    try {
      const res = await fetch(`${API_URL}/payments/create-invoice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seller_id: sellerId,
          subscription_tier: tier,
          test_mode: true // TODO: Set to false in production
        })
      })

      if (!res.ok) {
        throw new Error("Failed to create payment")
      }

      const data = await res.json()
      
      // Open payment URL in Telegram WebApp
      if (typeof window !== "undefined" && window.Telegram?.WebApp) {
        window.Telegram.WebApp.openLink(data.payment_url)
      } else {
        window.open(data.payment_url, "_blank")
      }
    } catch (err: any) {
      setError(err.message || "Ошибка создания платежа")
    } finally {
      setProcessing(false)
      setSelectedTier(null)
    }
  }

  const getPlanIcon = (tier: string) => {
    switch (tier) {
      case "start": return <Star className="h-6 w-6" />
      case "pro": return <Zap className="h-6 w-6" />
      case "magnate": return <Rocket className="h-6 w-6" />
      default: return <Crown className="h-6 w-6" />
    }
  }

  const getPlanColor = (tier: string) => {
    switch (tier) {
      case "start": return "from-blue-500/20 to-blue-500/5 border-blue-500/30"
      case "pro": return "from-purple-500/20 to-purple-500/5 border-purple-500/30"
      case "magnate": return "from-amber-500/20 to-amber-500/5 border-amber-500/30"
      default: return "from-gray-500/20 to-gray-500/5 border-gray-500/30"
    }
  }

  const getPlanBadgeColor = (tier: string) => {
    switch (tier) {
      case "start": return "bg-blue-500/20 text-blue-400"
      case "pro": return "bg-purple-500/20 text-purple-400"
      case "magnate": return "bg-amber-500/20 text-amber-400"
      default: return "bg-gray-500/20 text-gray-400"
    }
  }

  return (
    <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
      <div className="flex items-center gap-3 mb-2">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ChevronRight className="h-5 w-5 rotate-180" />
        </Button>
        <div>
          <h1 className="text-xl font-bold">💳 Выбор подписки</h1>
          <p className="text-xs text-muted-foreground">Выберите подходящий тариф</p>
        </div>
      </div>

      {error && (
        <Card className="bg-red-500/10 border-red-500/20">
          <CardContent className="p-3">
            <p className="text-sm text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="space-y-3">
          {plans.map((plan) => {
            const isCurrentTier = plan.tier === currentTier
            const isProcessing = processing && selectedTier === plan.tier

            return (
              <Card 
                key={plan.tier}
                className={`bg-gradient-to-br ${getPlanColor(plan.tier)} ${isCurrentTier ? 'ring-2 ring-primary' : ''}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`h-12 w-12 rounded-xl ${getPlanBadgeColor(plan.tier)} flex items-center justify-center`}>
                        {getPlanIcon(plan.tier)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-lg">{plan.name}</h3>
                          {plan.tier === "magnate" && <Crown className="h-4 w-4 text-amber-400" />}
                        </div>
                        <p className="text-xs text-muted-foreground">{plan.description}</p>
                      </div>
                    </div>
                    {isCurrentTier && (
                      <Badge className="bg-green-500/20 text-green-400 border-0 text-xs">
                        <Check className="h-3 w-3 mr-1" />
                        Текущий
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold">{plan.price.toLocaleString()}</span>
                    <span className="text-muted-foreground">₽/мес</span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-green-400 flex-shrink-0" />
                      <span>До <b>{plan.limit === 999999 ? "∞" : plan.limit}</b> товаров</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-green-400 flex-shrink-0" />
                      <span>Статистика продаж</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-green-400 flex-shrink-0" />
                      <span>Приоритетная поддержка</span>
                    </div>
                    {plan.tier === "magnate" && (
                      <>
                        <div className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-400 flex-shrink-0" />
                          <span className="text-amber-400 font-medium">Безлимитные товары</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-400 flex-shrink-0" />
                          <span className="text-amber-400 font-medium">Выделение в каталоге</span>
                        </div>
                      </>
                    )}
                  </div>

                  <Button
                    className="w-full font-bold"
                    onClick={() => handlePayment(plan.tier)}
                    disabled={isCurrentTier || processing}
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Создание счета...
                      </>
                    ) : isCurrentTier ? (
                      "Ваш текущий тариф"
                    ) : (
                      <>
                        Оплатить {plan.price.toLocaleString()} ₽
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <Card className="bg-white/5 border-white/10">
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground text-center">
            💳 <b>Тестовый режим:</b> Используйте карту <code className="text-green-400">4100 0000 0000 0001</code>
          </p>
          <p className="text-xs text-muted-foreground text-center mt-2">
            После оплаты подписка активируется автоматически
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

