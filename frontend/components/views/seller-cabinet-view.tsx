"use client"

import { useState, useEffect } from "react"
import { 
  Store, Package, Eye, TrendingUp, Plus, Edit, Trash2, 
  ChevronRight, Loader2, Check, Crown, AlertCircle, Clock,
  Upload, X
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { getTelegramUser } from "@/lib/telegram"
import { API_URL } from "@/lib/config"

interface Seller {
  id: number
  name: string
  status: string
  is_verified: boolean
  subscription_tier: string
  subscription_expires: string | null
  max_products: number
  total_views: number
  total_sales: number
}

interface SellerStats {
  total_products: number
  total_views: number
  total_orders: number
  products_limit: number
  subscription_tier: string
  subscription_expires: string | null
}

interface Product {
  id: number
  name: string
  part_number: string
  price_rub: number
  stock_quantity: number
  is_in_stock: boolean
  views_count: number
  image_url: string | null
}

interface TelegramUser {
  id: number
  first_name: string
  username?: string
}

export function SellerCabinetView({ onBack }: { onBack: () => void }) {
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null)
  const [seller, setSeller] = useState<Seller | null>(null)
  const [stats, setStats] = useState<SellerStats | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Add product form
  const [showAddForm, setShowAddForm] = useState(false)
  const [productForm, setProductForm] = useState({
    name: "",
    part_number: "",
    manufacturer: "",
    price_rub: "",
    stock_quantity: "",
    description: ""
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const user = getTelegramUser()
    if (user) {
      setTgUser(user)
      fetchSellerData(user.id)
    }
  }, [])

  const fetchSellerData = async (userId: number) => {
    try {
      // Get seller profile
      const sellerRes = await fetch(`${API_URL}/marketplace/sellers/me?telegram_id=${userId}`)
      if (!sellerRes.ok) {
        if (sellerRes.status === 404) {
          setError("not_found")
        } else {
          setError("Ошибка загрузки данных")
        }
        setLoading(false)
        return
      }
      
      const sellerData = await sellerRes.json()
      setSeller(sellerData)
      
      if (sellerData.status !== "approved") {
        setLoading(false)
        return
      }

      // Get stats
      const statsRes = await fetch(`${API_URL}/marketplace/sellers/me/stats?telegram_id=${userId}`)
      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }

      // Get products (products with seller_id = this seller)
      // TODO: Add endpoint for seller's products
      // For now we'll show empty
      
    } catch (err) {
      setError("Ошибка сети")
    } finally {
      setLoading(false)
    }
  }

  const getTierLabel = (tier: string) => {
    const labels: Record<string, { name: string; color: string }> = {
      free: { name: "Бесплатный", color: "bg-gray-500/20 text-gray-400" },
      start: { name: "Старт", color: "bg-blue-500/20 text-blue-400" },
      pro: { name: "Профи", color: "bg-purple-500/20 text-purple-400" },
      magnate: { name: "Магнат", color: "bg-amber-500/20 text-amber-400" }
    }
    return labels[tier] || labels.free
  }

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { text: string; color: string; icon: React.ReactNode }> = {
      pending: { text: "На модерации", color: "bg-yellow-500/20 text-yellow-400", icon: <Clock className="h-3 w-3" /> },
      approved: { text: "Активен", color: "bg-green-500/20 text-green-400", icon: <Check className="h-3 w-3" /> },
      rejected: { text: "Отклонен", color: "bg-red-500/20 text-red-400", icon: <X className="h-3 w-3" /> },
      banned: { text: "Заблокирован", color: "bg-red-500/20 text-red-400", icon: <AlertCircle className="h-3 w-3" /> }
    }
    return badges[status] || badges.pending
  }

  // Loading
  if (loading) {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
        <div className="flex items-center gap-3 mb-2">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <Skeleton className="h-6 w-40 bg-white/10" />
        </div>
        <Skeleton className="h-32 w-full bg-white/10" />
        <div className="grid grid-cols-3 gap-2">
          <Skeleton className="h-20 bg-white/10" />
          <Skeleton className="h-20 bg-white/10" />
          <Skeleton className="h-20 bg-white/10" />
        </div>
      </div>
    )
  }

  // Not a seller / Not found
  if (error === "not_found" || !seller) {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
        <div className="flex items-center gap-3 mb-2">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <h1 className="text-xl font-bold">Кабинет партнера</h1>
        </div>
        
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-8 text-center">
            <Store className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
            <h3 className="font-semibold mb-2">Вы ещё не партнер</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Подайте заявку на партнерство, чтобы получить доступ к личному кабинету
            </p>
            <Button onClick={onBack}>
              Подать заявку
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Pending approval
  if (seller.status === "pending") {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
        <div className="flex items-center gap-3 mb-2">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <h1 className="text-xl font-bold">Кабинет партнера</h1>
        </div>
        
        <Card className="bg-gradient-to-br from-yellow-500/10 to-orange-500/10 border-yellow-500/20">
          <CardContent className="p-6 text-center">
            <div className="h-16 w-16 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-4">
              <Clock className="h-8 w-8 text-yellow-400" />
            </div>
            <h2 className="text-lg font-bold text-yellow-400 mb-2">Заявка на рассмотрении</h2>
            <p className="text-sm text-muted-foreground">
              Ваша заявка «{seller.name}» находится на модерации. 
              Мы свяжемся с вами в ближайшее время.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Rejected
  if (seller.status === "rejected") {
    return (
      <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
        <div className="flex items-center gap-3 mb-2">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ChevronRight className="h-5 w-5 rotate-180" />
          </Button>
          <h1 className="text-xl font-bold">Кабинет партнера</h1>
        </div>
        
        <Card className="bg-gradient-to-br from-red-500/10 to-red-500/5 border-red-500/20">
          <CardContent className="p-6 text-center">
            <div className="h-16 w-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
              <X className="h-8 w-8 text-red-400" />
            </div>
            <h2 className="text-lg font-bold text-red-400 mb-2">Заявка отклонена</h2>
            <p className="text-sm text-muted-foreground">
              К сожалению, ваша заявка не была одобрена. 
              Свяжитесь с нами для уточнения деталей.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Main Cabinet (Approved)
  const tierInfo = getTierLabel(seller.subscription_tier)
  const statusInfo = getStatusBadge(seller.status)

  return (
    <div className="flex flex-col gap-4 pb-24 px-4 pt-4 min-h-screen bg-background">
      <div className="flex items-center gap-3 mb-2">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ChevronRight className="h-5 w-5 rotate-180" />
        </Button>
        <h1 className="text-xl font-bold">Кабинет партнера</h1>
      </div>

      {/* Seller Card */}
      <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border-amber-500/20">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                <Store className="h-6 w-6 text-amber-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-bold">{seller.name}</h2>
                  {seller.is_verified && (
                    <Badge className="bg-green-500/20 text-green-400 border-0 text-[10px]">
                      <Check className="h-2 w-2 mr-1" /> Verified
                    </Badge>
                  )}
                </div>
                <Badge className={`${statusInfo.color} border-0 text-xs mt-1`}>
                  {statusInfo.icon}
                  <span className="ml-1">{statusInfo.text}</span>
                </Badge>
              </div>
            </div>
            <Badge className={`${tierInfo.color} border-0`}>
              {seller.subscription_tier === "magnate" && <Crown className="h-3 w-3 mr-1" />}
              {tierInfo.name}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-3 gap-2">
          <Card className="bg-white/5 border-white/10">
            <CardContent className="p-3 text-center">
              <Package className="h-5 w-5 text-primary mx-auto mb-1" />
              <p className="text-lg font-bold">{stats.total_products}</p>
              <p className="text-[10px] text-muted-foreground">из {stats.products_limit}</p>
            </CardContent>
          </Card>
          <Card className="bg-white/5 border-white/10">
            <CardContent className="p-3 text-center">
              <Eye className="h-5 w-5 text-blue-400 mx-auto mb-1" />
              <p className="text-lg font-bold">{stats.total_views}</p>
              <p className="text-[10px] text-muted-foreground">просмотров</p>
            </CardContent>
          </Card>
          <Card className="bg-white/5 border-white/10">
            <CardContent className="p-3 text-center">
              <TrendingUp className="h-5 w-5 text-green-400 mx-auto mb-1" />
              <p className="text-lg font-bold">{stats.total_orders}</p>
              <p className="text-[10px] text-muted-foreground">продаж</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Subscription Info */}
      {seller.subscription_tier === "free" && (
        <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-sm">Хотите больше?</p>
                <p className="text-xs text-muted-foreground">
                  Обновите подписку и размещайте до 1000 товаров
                </p>
              </div>
              <Button size="sm" className="bg-purple-500 hover:bg-purple-600">
                <Crown className="h-4 w-4 mr-1" />
                Upgrade
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Products Section */}
      <div className="flex items-center justify-between mt-2">
        <h2 className="font-semibold">Мои товары</h2>
        <Button 
          size="sm" 
          className="bg-primary"
          onClick={() => setShowAddForm(true)}
          disabled={stats && stats.total_products >= stats.products_limit}
        >
          <Plus className="h-4 w-4 mr-1" />
          Добавить
        </Button>
      </div>

      {products.length > 0 ? (
        <div className="space-y-2">
          {products.map(product => (
            <Card key={product.id} className="bg-white/5 border-white/10">
              <CardContent className="p-3 flex items-center gap-3">
                <div className="h-12 w-12 rounded bg-white/10 flex-shrink-0 overflow-hidden">
                  {product.image_url ? (
                    <img src={product.image_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <Package className="h-6 w-6 text-muted-foreground m-auto" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{product.name}</p>
                  <p className="text-xs text-muted-foreground">{product.part_number}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-primary">{product.price_rub.toLocaleString()} ₽</p>
                  <p className="text-[10px] text-muted-foreground flex items-center justify-end gap-1">
                    <Eye className="h-3 w-3" /> {product.views_count || 0}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-8 text-center">
            <Package className="h-10 w-10 text-muted-foreground mx-auto mb-3 opacity-50" />
            <p className="text-sm text-muted-foreground mb-2">
              У вас пока нет товаров
            </p>
            <Button 
              size="sm"
              onClick={() => setShowAddForm(true)}
            >
              <Plus className="h-4 w-4 mr-1" />
              Добавить первый товар
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Limit Warning */}
      {stats && stats.total_products >= stats.products_limit && (
        <Card className="bg-red-500/10 border-red-500/20">
          <CardContent className="p-3 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
            <p className="text-sm text-red-400">
              Достигнут лимит товаров. Обновите подписку для добавления новых.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

