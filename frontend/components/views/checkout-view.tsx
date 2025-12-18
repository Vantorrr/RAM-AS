"use client"

import { useState } from "react"
import { useCartStore } from "@/lib/cart-store"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { ArrowLeft, Package, CreditCard, Truck, MapPin, Check } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { getTelegramUser } from "@/lib/telegram"

interface CheckoutViewProps {
  onBack: () => void
  onSuccess: () => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export function CheckoutView({ onBack, onSuccess }: CheckoutViewProps) {
  const { items, getTotalPrice, clearCart } = useCartStore()
  const [loading, setLoading] = useState(false)
  const [deliveryMethod, setDeliveryMethod] = useState<'delivery' | 'pickup'>('delivery')
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    address: "",
    comment: ""
  })

  const totalPrice = getTotalPrice()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const tgUser = getTelegramUser()
      const userId = tgUser?.id ? String(tgUser.id) : "web_user"

      const orderData = {
        user_telegram_id: userId,
        user_name: formData.name,
        user_phone: formData.phone,
        delivery_address: deliveryMethod === 'pickup' 
          ? "Самовывоз (г. Санкт-Петербург)" 
          : formData.address,
        total_amount: totalPrice,
        items: items.map(item => ({
          product_id: item.id,
          quantity: item.quantity,
          price_at_purchase: item.price_rub
        }))
      }

      const response = await fetch(`${API_URL}/orders/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(orderData)
      })

      if (!response.ok) throw new Error("Failed to create order")

      const order = await response.json()

      // Создаем invoice PayMaster для оплаты
      const paymentResponse = await fetch(`${API_URL}/payments/create-order-invoice`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          order_id: order.id,
          test_mode: true  // TODO: Изменить на false для продакшена
        })
      })

      if (!paymentResponse.ok) {
        alert(`✅ Заказ #${order.id} создан!\n\n⚠️ Не удалось открыть страницу оплаты.\nСвяжитесь с нами для получения реквизитов.`)
        clearCart()
        onSuccess()
        return
      }

      const paymentData = await paymentResponse.json()

      // Открываем страницу оплаты PayMaster
      window.open(paymentData.payment_url, "_blank")

      clearCart()
      onSuccess()
    } catch (error) {
      console.error("Error creating order:", error)
      alert("Ошибка при оформлении заказа. Попробуйте еще раз.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 pb-24 px-4">
      <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-md border-b border-white/5 -mx-4 px-4 py-3 flex items-center gap-3">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={onBack}
          className="-ml-2 text-muted-foreground hover:text-white"
        >
          <ArrowLeft className="h-6 w-6" />
        </Button>
        <div>
          <h2 className="text-lg font-bold leading-none">Оформление заказа</h2>
          <p className="text-xs text-muted-foreground">Заполните данные</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 pt-4">
        {/* Order Summary */}
        <Card className="bg-card/30 backdrop-blur-sm border-white/10 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center">
              <Package className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold">Ваш заказ</h3>
              <p className="text-sm text-muted-foreground">{items.length} товаров</p>
            </div>
          </div>
          <div className="flex items-center justify-between pt-3 border-t border-white/10">
            <span className="text-muted-foreground">Итого:</span>
            <span className="text-2xl font-bold text-white">{totalPrice.toLocaleString('ru-RU')} ₽</span>
          </div>
        </Card>

        {/* Contact Info */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-8 w-8 rounded-full bg-white/5 flex items-center justify-center">
              <span className="text-sm font-bold">1</span>
            </div>
            <h3 className="font-semibold">Контактные данные</h3>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="name">Имя</Label>
            <Input
              id="name"
              placeholder="Иван Иванов"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="bg-white/5 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Телефон</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="+7 (999) 123-45-67"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              required
              className="bg-white/5 border-white/10"
            />
          </div>
        </div>

        {/* Delivery Method */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-8 w-8 rounded-full bg-white/5 flex items-center justify-center">
              <span className="text-sm font-bold">2</span>
            </div>
            <h3 className="font-semibold">Способ получения</h3>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div 
              className={cn(
                "cursor-pointer rounded-xl border p-4 transition-all flex flex-col items-center justify-center gap-2 text-center",
                deliveryMethod === 'delivery' 
                  ? "bg-primary/20 border-primary text-primary" 
                  : "bg-white/5 border-white/10 hover:bg-white/10"
              )}
              onClick={() => setDeliveryMethod('delivery')}
            >
              <Truck className="h-6 w-6" />
              <span className="font-bold text-sm">Доставка</span>
            </div>
            <div 
              className={cn(
                "cursor-pointer rounded-xl border p-4 transition-all flex flex-col items-center justify-center gap-2 text-center",
                deliveryMethod === 'pickup' 
                  ? "bg-primary/20 border-primary text-primary" 
                  : "bg-white/5 border-white/10 hover:bg-white/10"
              )}
              onClick={() => setDeliveryMethod('pickup')}
            >
              <MapPin className="h-6 w-6" />
              <span className="font-bold text-sm">Самовывоз</span>
            </div>
          </div>

          {deliveryMethod === 'delivery' ? (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
              <Label htmlFor="address">Адрес доставки</Label>
              <Textarea
                id="address"
                placeholder="Город, улица, дом, квартира"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                required
                className="bg-white/5 border-white/10 min-h-[80px]"
              />
            </div>
          ) : (
            <Card className="bg-white/5 border-white/10 p-4 animate-in fade-in slide-in-from-top-2">
              <div className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-primary mt-0.5" />
                <div>
                  <p className="font-bold">Пункт выдачи RAM US</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    г. Санкт-Петербург<br />
                    (адрес уточнит менеджер)
                  </p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-green-400">
                    <Check className="h-3 w-3" />
                    Бесплатно
                  </div>
                </div>
              </div>
            </Card>
          )}

          <div className="space-y-2">
            <Label htmlFor="comment">Комментарий (необязательно)</Label>
            <Textarea
              id="comment"
              placeholder="Дополнительная информация"
              value={formData.comment}
              onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
              className="bg-white/5 border-white/10"
            />
          </div>
        </div>

        {/* Payment Info */}
        <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20 p-4">
          <div className="flex items-center gap-3 mb-2">
            <CreditCard className="h-5 w-5 text-primary" />
            <h3 className="font-semibold">Оплата</h3>
          </div>
          <p className="text-sm text-muted-foreground">
            После оформления заказа с вами свяжется менеджер для подтверждения и выбора способа оплаты.
          </p>
        </Card>

        <Button 
          type="submit" 
          size="lg" 
          className="w-full bg-primary hover:bg-primary/90 text-white font-bold shadow-lg shadow-primary/30 transition-all hover:shadow-primary/50 hover:scale-[1.02] active:scale-95"
          disabled={loading}
        >
          {loading ? "Оформление..." : "Оформить заказ"}
        </Button>
      </form>
    </div>
  )
}



