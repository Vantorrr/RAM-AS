"use client"

import { useState, useEffect, useCallback } from "react"
import { useCartStore } from "@/lib/cart-store"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card } from "@/components/ui/card"
import { ArrowLeft, Package, MapPin, Check, Search, Loader2, Building2 } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { getTelegramUser } from "@/lib/telegram"
import { API_URL } from "@/lib/config"

// Маска телефона
function formatPhoneNumber(value: string): string {
  const digits = value.replace(/\D/g, '')
  let phone = digits
  if (phone.startsWith('7') || phone.startsWith('8')) {
    phone = phone.slice(1)
  }
  phone = phone.slice(0, 10)
  
  if (phone.length === 0) return ''
  if (phone.length <= 3) return `+7 (${phone}`
  if (phone.length <= 6) return `+7 (${phone.slice(0, 3)}) ${phone.slice(3)}`
  if (phone.length <= 8) return `+7 (${phone.slice(0, 3)}) ${phone.slice(3, 6)}-${phone.slice(6)}`
  return `+7 (${phone.slice(0, 3)}) ${phone.slice(3, 6)}-${phone.slice(6, 8)}-${phone.slice(8)}`
}

function isValidPhone(phone: string): boolean {
  const digits = phone.replace(/\D/g, '')
  return digits.length === 11
}

interface City {
  code: number
  city: string
  region: string
}

interface DeliveryOption {
  tariff_code: number
  tariff_name: string
  delivery_sum: number
  period_min: number
  period_max: number
}

interface PVZ {
  code: string
  name: string
  address: string
  work_time: string
  phone: string | null
}

interface CheckoutViewProps {
  onBack: () => void
  onSuccess: () => void
}

export function CheckoutView({ onBack, onSuccess }: CheckoutViewProps) {
  const { items, getTotalPrice, clearCart } = useCartStore()
  const [loading, setLoading] = useState(false)
  const [deliveryType, setDeliveryType] = useState<'cdek_pvz' | 'cdek_door' | 'pickup'>('cdek_pvz')
  
  // Форма
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    address: "",
    comment: ""
  })
  
  // Поиск города
  const [cityQuery, setCityQuery] = useState("")
  const [cities, setCities] = useState<City[]>([])
  const [selectedCity, setSelectedCity] = useState<City | null>(null)
  const [searchingCity, setSearchingCity] = useState(false)
  
  // Варианты доставки
  const [deliveryOptions, setDeliveryOptions] = useState<DeliveryOption[]>([])
  const [selectedTariff, setSelectedTariff] = useState<DeliveryOption | null>(null)
  const [loadingDelivery, setLoadingDelivery] = useState(false)
  
  // ПВЗ
  const [pvzList, setPvzList] = useState<PVZ[]>([])
  const [selectedPvz, setSelectedPvz] = useState<PVZ | null>(null)
  const [loadingPvz, setLoadingPvz] = useState(false)

  const totalPrice = getTotalPrice()
  const deliveryCost = selectedTariff?.delivery_sum || 0
  const totalWithDelivery = totalPrice + deliveryCost

  // Поиск городов
  const searchCities = useCallback(async (query: string) => {
    if (query.length < 2) {
      setCities([])
      return
    }
    setSearchingCity(true)
    try {
      const res = await fetch(`${API_URL}/cdek/cities?query=${encodeURIComponent(query)}`)
      const data = await res.json()
      setCities(data.slice(0, 10))
    } catch (e) {
      console.error("Error searching cities:", e)
    } finally {
      setSearchingCity(false)
    }
  }, [])

  // Debounce поиска города
  useEffect(() => {
    const timer = setTimeout(() => {
      if (cityQuery && !selectedCity) {
        searchCities(cityQuery)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [cityQuery, selectedCity, searchCities])

  // Загрузка тарифов при выборе города
  useEffect(() => {
    if (!selectedCity) {
      setDeliveryOptions([])
      setSelectedTariff(null)
      return
    }
    
    const loadTariffs = async () => {
      setLoadingDelivery(true)
      try {
        const res = await fetch(`${API_URL}/cdek/calculate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            to_city_code: selectedCity.code,
            weight: Math.max(1000, items.reduce((acc, item) => acc + (item.quantity * 500), 0))
          })
        })
        const data = await res.json()
        
        // Фильтруем только нужные тарифы (ПВЗ или до двери)
        const pvzTariffs = data.filter((t: DeliveryOption) => 
          t.tariff_name.toLowerCase().includes('склад') || 
          t.tariff_name.toLowerCase().includes('пвз') ||
          t.tariff_code === 136 || t.tariff_code === 137 || t.tariff_code === 234
        )
        const doorTariffs = data.filter((t: DeliveryOption) => 
          t.tariff_name.toLowerCase().includes('дверь') ||
          t.tariff_code === 137 || t.tariff_code === 139 || t.tariff_code === 233
        )
        
        setDeliveryOptions(deliveryType === 'cdek_pvz' ? (pvzTariffs.length ? pvzTariffs : data.slice(0, 3)) : (doorTariffs.length ? doorTariffs : data.slice(0, 3)))
        
        // Автовыбор самого дешёвого
        const cheapest = data.reduce((min: DeliveryOption, t: DeliveryOption) => 
          t.delivery_sum < min.delivery_sum ? t : min, data[0])
        setSelectedTariff(cheapest)
      } catch (e) {
        console.error("Error loading tariffs:", e)
      } finally {
        setLoadingDelivery(false)
      }
    }
    
    loadTariffs()
  }, [selectedCity, deliveryType, items])

  // Загрузка ПВЗ при выборе города
  useEffect(() => {
    if (!selectedCity || deliveryType !== 'cdek_pvz') {
      setPvzList([])
      setSelectedPvz(null)
      return
    }
    
    const loadPvz = async () => {
      setLoadingPvz(true)
      try {
        const res = await fetch(`${API_URL}/cdek/pvz?city_code=${selectedCity.code}`)
        const data = await res.json()
        setPvzList(data.slice(0, 20))
        if (data.length > 0) {
          setSelectedPvz(data[0])
        }
      } catch (e) {
        console.error("Error loading PVZ:", e)
      } finally {
        setLoadingPvz(false)
      }
    }
    
    loadPvz()
  }, [selectedCity, deliveryType])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!isValidPhone(formData.phone)) {
      alert("Введите корректный номер телефона")
      return
    }
    
    if (deliveryType !== 'pickup' && !selectedCity) {
      alert("Выберите город доставки")
      return
    }
    
    if (deliveryType === 'cdek_pvz' && !selectedPvz) {
      alert("Выберите пункт выдачи")
      return
    }
    
    setLoading(true)

    try {
      const tgUser = getTelegramUser()
      const userId = tgUser?.id ? String(tgUser.id) : "web_user"

      const orderData = {
        user_telegram_id: userId,
        user_name: formData.name,
        user_phone: formData.phone,
        delivery_address: deliveryType === 'pickup' 
          ? "Самовывоз (адрес уточнит менеджер)" 
          : deliveryType === 'cdek_pvz'
            ? selectedPvz?.address
            : formData.address,
        total_amount: totalWithDelivery,
        delivery_type: deliveryType,
        delivery_cost: deliveryCost,
        cdek_city_code: selectedCity?.code,
        cdek_city_name: selectedCity?.city,
        cdek_pvz_code: selectedPvz?.code,
        cdek_pvz_address: selectedPvz?.address,
        cdek_tariff_code: selectedTariff?.tariff_code,
        items: items.map(item => ({
          product_id: item.id,
          quantity: item.quantity,
          price_at_purchase: item.price_rub
        }))
      }

      const response = await fetch(`${API_URL}/orders/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderData)
      })

      if (!response.ok) throw new Error("Failed to create order")

      const order = await response.json()

      // Создаем оплату через T-Bank
      const paymentResponse = await fetch(`${API_URL}/payments/tbank/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: order.id
        })
      })

      if (!paymentResponse.ok) {
        alert(`✅ Заказ #${order.id} создан!\n\n⚠️ Не удалось открыть страницу оплаты.\nМенеджер свяжется с вами.`)
        clearCart()
        onSuccess()
        return
      }

      const paymentData = await paymentResponse.json()

      // Открываем оплату
      if (typeof window !== 'undefined') {
        const tg = (window as any).Telegram?.WebApp
        if (tg?.openLink) {
          tg.openLink(paymentData.payment_url)
        } else {
          window.open(paymentData.payment_url, "_blank")
        }
      }

      clearCart()
      onSuccess()
    } catch (error) {
      console.error("Error:", error)
      alert("Ошибка при оформлении заказа")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-md border-b border-white/5 px-4 py-3 flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={onBack} className="-ml-2">
          <ArrowLeft className="h-6 w-6" />
        </Button>
        <div>
          <h2 className="text-lg font-bold">Оформление заказа</h2>
          <p className="text-xs text-muted-foreground">Заполните данные</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-4 pb-32 space-y-6 pt-4">
        {/* Итого */}
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
          <div className="space-y-2 pt-3 border-t border-white/10">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Товары:</span>
              <span>{totalPrice.toLocaleString('ru-RU')} ₽</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Доставка:</span>
              <span className={deliveryCost === 0 ? "text-green-400" : ""}>
                {deliveryCost === 0 ? "Бесплатно" : `${deliveryCost.toLocaleString('ru-RU')} ₽`}
              </span>
            </div>
            <div className="flex justify-between pt-2 border-t border-white/10">
              <span className="font-bold">Итого:</span>
              <span className="text-xl font-bold text-primary">{totalWithDelivery.toLocaleString('ru-RU')} ₽</span>
            </div>
          </div>
        </Card>

        {/* Контакты */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-white/5 flex items-center justify-center">
              <span className="text-sm font-bold">1</span>
            </div>
            <h3 className="font-semibold">Контактные данные</h3>
          </div>
          
          <div className="space-y-2">
            <Label>Имя</Label>
            <Input
              placeholder="Иван Иванов"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="bg-white/5 border-white/10"
            />
          </div>

          <div className="space-y-2">
            <Label>Телефон</Label>
            <Input
              type="tel"
              placeholder="+7 (999) 123-45-67"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: formatPhoneNumber(e.target.value) })}
              required
              className="bg-white/5 border-white/10"
            />
            {formData.phone && !isValidPhone(formData.phone) && (
              <p className="text-xs text-red-400">Введите полный номер</p>
            )}
          </div>
        </div>

        {/* Способ доставки */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-white/5 flex items-center justify-center">
              <span className="text-sm font-bold">2</span>
            </div>
            <h3 className="font-semibold">Способ получения</h3>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { type: 'cdek_pvz' as const, icon: Building2, label: 'ПВЗ СДЭК' },
              { type: 'pickup' as const, icon: MapPin, label: 'Самовывоз' },
            ].map(({ type, icon: Icon, label }) => (
              <div 
                key={type}
                className={cn(
                  "cursor-pointer rounded-xl border p-3 transition-all flex flex-col items-center gap-2 text-center",
                  deliveryType === type 
                    ? "bg-primary/20 border-primary text-primary" 
                    : "bg-white/5 border-white/10 hover:bg-white/10"
                )}
                onClick={() => setDeliveryType(type)}
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium text-xs">{label}</span>
              </div>
            ))}
          </div>

          {/* Выбор города для СДЭК */}
          {deliveryType !== 'pickup' && (
            <div className="space-y-3 animate-in fade-in">
              <Label>Город доставки</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Начните вводить город..."
                  value={selectedCity ? selectedCity.city : cityQuery}
                  onChange={(e) => {
                    setCityQuery(e.target.value)
                    setSelectedCity(null)
                  }}
                  className="bg-white/5 border-white/10 pl-10"
                />
                {searchingCity && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin" />
                )}
              </div>
              
              {/* Результаты поиска */}
              {cities.length > 0 && !selectedCity && (
                <Card className="bg-white/5 border-white/10 divide-y divide-white/5 max-h-48 overflow-y-auto">
                  {cities.map((city) => (
                    <div
                      key={city.code}
                      className="p-3 cursor-pointer hover:bg-white/10 transition-colors"
                      onClick={() => {
                        setSelectedCity(city)
                        setCities([])
                      }}
                    >
                      <p className="font-medium">{city.city}</p>
                      <p className="text-xs text-muted-foreground">{city.region}</p>
                    </div>
                  ))}
                </Card>
              )}

              {/* Тарифы */}
              {selectedCity && (
                <div className="space-y-2 animate-in fade-in">
                  <Label>Стоимость доставки</Label>
                  {loadingDelivery ? (
                    <div className="flex items-center gap-2 text-muted-foreground p-4">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Расчёт стоимости...</span>
                    </div>
                  ) : deliveryOptions.length > 0 ? (
                    <div className="space-y-2">
                      {deliveryOptions.slice(0, 3).map((opt) => (
                        <Card
                          key={opt.tariff_code}
                          className={cn(
                            "p-3 cursor-pointer transition-all",
                            selectedTariff?.tariff_code === opt.tariff_code
                              ? "bg-primary/20 border-primary"
                              : "bg-white/5 border-white/10 hover:bg-white/10"
                          )}
                          onClick={() => setSelectedTariff(opt)}
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-sm">{opt.tariff_name}</p>
                              <p className="text-xs text-muted-foreground">
                                {opt.period_min === opt.period_max 
                                  ? `${opt.period_min} дн.` 
                                  : `${opt.period_min}-${opt.period_max} дн.`}
                              </p>
                            </div>
                            <span className="font-bold text-primary">
                              {opt.delivery_sum.toLocaleString('ru-RU')} ₽
                            </span>
                          </div>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">Нет доступных тарифов</p>
                  )}
                </div>
              )}

              {/* Выбор ПВЗ */}
              {deliveryType === 'cdek_pvz' && selectedCity && (
                <div className="space-y-2 animate-in fade-in">
                  <Label>Пункт выдачи</Label>
                  {loadingPvz ? (
                    <div className="flex items-center gap-2 text-muted-foreground p-4">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Загрузка ПВЗ...</span>
                    </div>
                  ) : pvzList.length > 0 ? (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {pvzList.map((pvz) => (
                        <Card
                          key={pvz.code}
                          className={cn(
                            "p-3 cursor-pointer transition-all",
                            selectedPvz?.code === pvz.code
                              ? "bg-primary/20 border-primary"
                              : "bg-white/5 border-white/10 hover:bg-white/10"
                          )}
                          onClick={() => setSelectedPvz(pvz)}
                        >
                          <p className="font-medium text-sm">{pvz.address}</p>
                          <p className="text-xs text-muted-foreground mt-1">{pvz.work_time}</p>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">Нет ПВЗ в этом городе</p>
                  )}
                </div>
              )}

            </div>
          )}

          {/* Самовывоз */}
          {deliveryType === 'pickup' && (
            <Card className="bg-white/5 border-white/10 p-4 animate-in fade-in">
              <div className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-primary mt-0.5" />
                <div>
                  <p className="font-bold">Самовывоз</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Адрес уточнит менеджер после оформления
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
            <Label>Комментарий</Label>
            <Textarea
              placeholder="Дополнительная информация"
              value={formData.comment}
              onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
              className="bg-white/5 border-white/10"
            />
          </div>
        </div>

      </form>

      {/* Sticky кнопка оплаты */}
      <div className="sticky bottom-0 left-0 right-0 bg-background/95 backdrop-blur-md border-t border-white/10 p-4 z-20">
        <Button 
          type="submit" 
          size="lg" 
          className="w-full bg-primary hover:bg-primary/90 font-bold shadow-lg mb-2"
          disabled={loading || !isValidPhone(formData.phone) || (deliveryType !== 'pickup' && !selectedCity)}
          onClick={handleSubmit}
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Оформление...
            </>
          ) : (
            `Оформить заказ`
          )}
        </Button>
        <p className="text-xs text-center text-muted-foreground">
          После нажатия кнопки вы перейдёте на безопасную страницу оплаты T-Bank. Принимаем карты и СБП.
        </p>
      </div>
    </div>
  )
}
