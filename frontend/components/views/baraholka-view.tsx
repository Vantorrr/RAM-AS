"use client"

import { useState, useEffect } from "react"
import { Tag, Plus, MapPin, Eye, Clock, ChevronRight, ImagePlus, Send, Loader2, X, Check, Star } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { getTelegramUser } from "@/lib/telegram"
import { API_URL } from "@/lib/config"

interface Listing {
  id: number
  title: string
  description: string | null
  price: number
  city: string | null
  images: string | null
  seller_name: string | null
  seller_telegram_username: string | null
  is_promoted: boolean
  views_count: number
  created_at: string
}

interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
}

// Список запрещенных слов (корни слов)
const PROHIBITED_WORDS = [
  'нарко', 'меф', 'гашиш', 'кокаин', 'героин', 'спайс', 'мариху', 'шишк', 'бошк', // Наркотики
  'оружие', 'травмат', 'патрон', 'кастет', 'взрыв', 'бомба', 'гранат', // Оружие
  'порно', 'секс', 'интим', 'проститу', // 18+
  'экстреми', 'террор', 'смерт', 'убий', // Насилие
  'пробив', 'обнал', 'документ' // Нелегальные услуги (аккуратно с документами)
]

export function BaraholkaView({ onBack }: { onBack: () => void }) {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null)
  
  // Create form state
  const [form, setForm] = useState({
    title: "",
    description: "",
    price: "",
    city: "",
    seller_name: "",
    seller_phone: ""
  })
  const [submitting, setSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [createdListingId, setCreatedListingId] = useState<number | null>(null)
  const [paymentLoading, setPaymentLoading] = useState(false)
  const [selectedImages, setSelectedImages] = useState<File[]>([])
  const [uploadingImages, setUploadingImages] = useState(false)

  useEffect(() => {
    const user = getTelegramUser()
    if (user) {
      setTgUser(user)
      setForm(prev => ({
        ...prev,
        seller_name: `${user.first_name}${user.last_name ? ` ${user.last_name}` : ''}`
      }))
    }
    fetchListings()
  }, [])

  const fetchListings = async () => {
    try {
      const res = await fetch(`${API_URL}/marketplace/listings/`)
      if (res.ok) {
        const data = await res.json()
        setListings(data)
      }
    } catch (err) {
      console.error("Failed to fetch listings:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) {
      const newFiles = Array.from(files).slice(0, 5 - selectedImages.length) // Max 5 images
      setSelectedImages(prev => [...prev, ...newFiles])
    }
  }

  const removeImage = (index: number) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index))
  }

  const uploadImages = async (): Promise<string | null> => {
    if (selectedImages.length === 0) return null
    
    setUploadingImages(true)
    try {
      const formData = new FormData()
      selectedImages.forEach(file => {
        formData.append("files", file)
      })
      
      const res = await fetch(`${API_URL}/upload/`, {
        method: "POST",
        body: formData
      })
      
      if (res.ok) {
        const data = await res.json()
        // Возвращаем URL через запятую
        return data.urls?.join(",") || null
      }
      return null
    } catch (err) {
      console.error("Image upload error:", err)
      return null
    } finally {
      setUploadingImages(false)
    }
  }

  const submitListing = async () => {
    if (!tgUser) return
    if (!form.title || !form.price) {
      setSubmitError("Заполните название и цену")
      return
    }

    // Проверка на запрещенные слова
    const fullText = (form.title + " " + (form.description || "")).toLowerCase()
    const foundBadWord = PROHIBITED_WORDS.find(word => fullText.includes(word))
    
    if (foundBadWord) {
      setSubmitError("Обнаружен запрещенный контент! Мы размещаем только автозапчасти.")
      return
    }

    setSubmitting(true)
    setSubmitError(null)

    try {
      // Сначала загружаем фото если есть
      let imagesUrl: string | null = null
      if (selectedImages.length > 0) {
        imagesUrl = await uploadImages()
      }

      const res = await fetch(`${API_URL}/marketplace/listings/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: form.title,
          description: form.description || null,
          price: parseFloat(form.price),
          city: form.city || null,
          seller_name: form.seller_name || null,
          seller_phone: form.seller_phone || null,
          seller_telegram_id: String(tgUser.id),
          seller_telegram_username: tgUser.username || null,
          images: imagesUrl
        })
      })

      if (res.ok) {
        const data = await res.json()
        console.log("Listing created:", data)
        const listingId = data.id
        if (listingId) {
          console.log("Got listing ID:", listingId)
          // Важно: сначала сохраняем ID, потом показываем success
          setCreatedListingId(listingId)
          // Небольшая задержка чтобы state обновился
          setTimeout(() => {
            setSubmitSuccess(true)
          }, 100)
        } else {
          console.error("No ID in response:", data)
          setSubmitError("Ошибка: не получен ID объявления")
        }
      } else {
        const data = await res.json()
        setSubmitError(data.detail || "Ошибка создания объявления")
      }
    } catch (err) {
      setSubmitError("Ошибка сети. Попробуйте позже.")
    } finally {
      setSubmitting(false)
    }
  }

  const handleListingPayment = async () => {
    console.log("handleListingPayment called, createdListingId:", createdListingId)
    if (!createdListingId) {
      console.error("No createdListingId!")
      alert("Ошибка: ID объявления не найден. Попробуйте создать объявление заново.")
      return
    }
    
    setPaymentLoading(true)
    try {
      const res = await fetch(`${API_URL}/payments/create-listing-invoice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          listing_id: createdListingId,
          test_mode: true
        })
      })

      if (!res.ok) {
        throw new Error("Failed to create payment")
      }

      const data = await res.json()
      
      // Открываем страницу оплаты
      const tgWebApp = window.Telegram?.WebApp as any
      if (tgWebApp?.openLink) {
        tgWebApp.openLink(data.payment_url)
      } else {
        window.open(data.payment_url, "_blank")
      }
    } catch (err) {
      console.error("Payment error:", err)
      alert("Ошибка создания платежа. Попробуйте позже.")
    } finally {
      setPaymentLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    
    if (diffHours < 1) return "Только что"
    if (diffHours < 24) return `${diffHours}ч назад`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays === 1) return "Вчера"
    return `${diffDays} дн. назад`
  }

  // Create Listing Form
  if (showCreateForm) {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
        <div className="flex items-center gap-3 mb-2">
          <Button variant="ghost" size="icon" onClick={() => setShowCreateForm(false)}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <h1 className="text-xl font-bold">Новое объявление</h1>
        </div>

        {submitSuccess ? (
          <Card className="bg-gradient-to-br from-green-500/20 to-green-500/5 border-green-500/30">
            <CardContent className="p-6 text-center">
              <div className="h-16 w-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
                <Check className="h-8 w-8 text-green-400" />
              </div>
              <h2 className="text-lg font-bold text-green-400 mb-2">Объявление создано!</h2>
              <p className="text-sm text-muted-foreground mb-2">
                После оплаты размещения (200₽) и модерации ваше объявление появится в ленте.
              </p>
              <p className="text-xs text-green-400/60 mb-4">
                ID: {createdListingId || "не получен"}
              </p>
              <div className="space-y-2">
                <Button 
                  className="w-full bg-green-500 hover:bg-green-600 text-white font-bold"
                  onClick={handleListingPayment}
                  disabled={paymentLoading}
                >
                  {paymentLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Создание платежа...
                    </>
                  ) : (
                    "💳 Оплатить 200 ₽"
                  )}
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={() => { setShowCreateForm(false); setSubmitSuccess(false); setCreatedListingId(null) }}
                >
                  Оплатить позже
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            <Card className="bg-cyan-500/10 border-cyan-500/20">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-cyan-500/20 mt-0.5">
                    <Tag className="h-5 w-5 text-cyan-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-cyan-400 mb-1">Как это работает</h3>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>1. Заполните форму объявления</li>
                      <li>2. Оплатите размещение (200₽)</li>
                      <li>3. Модератор проверит объявление</li>
                      <li>4. Объявление появится в ленте на 30 дней</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">Детали объявления</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Название *</label>
                  <Input 
                    placeholder="Например: Двигатель 5.7 HEMI"
                    value={form.title}
                    onChange={e => setForm({...form, title: e.target.value})}
                    className="bg-black/20 border-white/10"
                  />
                </div>

                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Цена (₽) *</label>
                  <Input 
                    type="number"
                    placeholder="150000"
                    value={form.price}
                    onChange={e => setForm({...form, price: e.target.value})}
                    className="bg-black/20 border-white/10"
                  />
                </div>

                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Город</label>
                  <Input 
                    placeholder="Москва"
                    value={form.city}
                    onChange={e => setForm({...form, city: e.target.value})}
                    className="bg-black/20 border-white/10"
                  />
                </div>

                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Описание</label>
                  <Textarea 
                    placeholder="Состояние, пробег, причина продажи..."
                    value={form.description}
                    onChange={e => setForm({...form, description: e.target.value})}
                    className="bg-black/20 border-white/10 min-h-[100px]"
                  />
                </div>

                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">
                    <ImagePlus className="h-3 w-3 inline mr-1" />
                    Фото (до 5 шт.)
                  </label>
                  <div className="space-y-2">
                    {selectedImages.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {selectedImages.map((file, index) => (
                          <div key={index} className="relative">
                            <img 
                              src={URL.createObjectURL(file)} 
                              alt={`Photo ${index + 1}`}
                              className="w-16 h-16 object-cover rounded-lg border border-white/20"
                            />
                            <button
                              type="button"
                              onClick={() => removeImage(index)}
                              className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center"
                            >
                              <X className="h-3 w-3 text-white" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                    {selectedImages.length < 5 && (
                      <label className="flex items-center justify-center w-full h-20 border-2 border-dashed border-white/20 rounded-lg cursor-pointer hover:border-cyan-500/50 transition-colors">
                        <div className="text-center">
                          <ImagePlus className="h-6 w-6 mx-auto text-muted-foreground mb-1" />
                          <span className="text-xs text-muted-foreground">Добавить фото</span>
                        </div>
                        <input
                          type="file"
                          accept="image/*"
                          multiple
                          onChange={handleImageSelect}
                          className="hidden"
                        />
                      </label>
                    )}
                  </div>
                </div>

                <div className="border-t border-white/10 pt-4">
                  <p className="text-xs text-muted-foreground mb-3">Контактные данные</p>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Ваше имя</label>
                      <Input 
                        placeholder="Иван"
                        value={form.seller_name}
                        onChange={e => setForm({...form, seller_name: e.target.value})}
                        className="bg-black/20 border-white/10"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-muted-foreground mb-1 block">Телефон</label>
                      <Input 
                        placeholder="+7 (999) 123-45-67"
                        value={form.seller_phone}
                        onChange={e => setForm({...form, seller_phone: e.target.value})}
                        className="bg-black/20 border-white/10"
                      />
                    </div>
                  </div>
                </div>

                {submitError && (
                  <p className="text-sm text-red-400">{submitError}</p>
                )}

                <Button 
                  className="w-full bg-cyan-500 hover:bg-cyan-600 text-black font-bold"
                  onClick={submitListing}
                  disabled={submitting || uploadingImages}
                >
                  {submitting || uploadingImages ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      {uploadingImages ? "Загрузка фото..." : "Создание..."}
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Создать объявление
                    </>
                  )}
                </Button>
                <p className="text-[10px] text-muted-foreground text-center mt-2 px-2">
                  Нажимая кнопку, вы соглашаетесь с <span className="underline">Правилами размещения</span> и <span className="underline">Офертой</span>
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    )
  }

  // Main Listings Feed
  return (
    <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <h1 className="text-xl font-bold">Барахолка</h1>
        </div>
        <Button 
          size="sm" 
          className="bg-cyan-500 hover:bg-cyan-600 text-black"
          onClick={() => setShowCreateForm(true)}
        >
          <Plus className="h-4 w-4 mr-1" />
          Продать
        </Button>
      </div>

      {/* Info Banner */}
      <Card className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border-cyan-500/20">
        <CardContent className="p-3">
          <p className="text-xs text-muted-foreground">
            <Tag className="h-3 w-3 inline mr-1" />
            Частные объявления от пользователей. Размещение — 200₽
          </p>
        </CardContent>
      </Card>

      {/* Listings */}
      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => (
            <Card key={i} className="bg-white/5 border-white/10">
              <CardContent className="p-4">
                <Skeleton className="h-4 w-3/4 bg-white/10 mb-2" />
                <Skeleton className="h-6 w-1/3 bg-white/10 mb-3" />
                <Skeleton className="h-3 w-1/2 bg-white/10" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : listings.length > 0 ? (
        <div className="space-y-3">
          {listings.map(listing => (
            <Card 
              key={listing.id} 
              className={`bg-white/5 border-white/10 overflow-hidden ${
                listing.is_promoted ? 'ring-1 ring-amber-500/50' : ''
              }`}
            >
              {listing.is_promoted && (
                <div className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 px-3 py-1 flex items-center gap-1">
                  <Star className="h-3 w-3 text-amber-400 fill-amber-400" />
                  <span className="text-xs text-amber-400 font-medium">Продвигается</span>
                </div>
              )}
              <CardContent className="p-4">
                <h3 className="font-semibold mb-1 line-clamp-1">{listing.title}</h3>
                <p className="text-xl font-bold text-primary mb-2">
                  {listing.price.toLocaleString()} ₽
                </p>
                
                {listing.description && (
                  <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                    {listing.description}
                  </p>
                )}
                
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <div className="flex items-center gap-3">
                    {listing.city && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {listing.city}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Eye className="h-3 w-3" />
                      {listing.views_count}
                    </span>
                  </div>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDate(listing.created_at)}
                  </span>
                </div>

                {listing.seller_telegram_username && (
                  <div className="mt-3 pt-3 border-t border-white/10">
                    <a 
                      href={`https://t.me/${listing.seller_telegram_username}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-cyan-400 hover:underline"
                    >
                      Написать @{listing.seller_telegram_username}
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-8 text-center">
            <Tag className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-50" />
            <h3 className="font-semibold mb-1">Пока пусто</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Будьте первым, кто разместит объявление!
            </p>
            <Button 
              className="bg-cyan-500 hover:bg-cyan-600 text-black"
              onClick={() => setShowCreateForm(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Разместить объявление
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}


