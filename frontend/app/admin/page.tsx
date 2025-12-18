"use client"

import { useState, useRef, useCallback, useEffect, Suspense } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  ArrowLeft, Search, Save, Package, DollarSign, 
  Image as ImageIcon, Percent, ShoppingCart, Users,
  TrendingUp, Box, Edit, ChevronRight, Upload, AlertCircle, RefreshCw,
  Handshake, Tag, Check, X, Ban, Eye, Phone, Mail, MessageCircle
} from "lucide-react"
import { API_URL } from "@/lib/config"
import { useSearchParams } from "next/navigation"

export const dynamic = 'force-dynamic'

interface Product {
  id: number
  name: string
  part_number: string
  price_rub: number
  image_url: string | null
  is_in_stock: boolean
  is_installment_available: boolean
  stock_quantity: number
  category_id: number
}

interface Seller {
  id: number
  name: string
  contact_name: string
  phone: string
  email: string
  telegram_id: string
  telegram_username: string
  description: string
  status: string
  is_verified: boolean
  subscription_tier: string
  max_products: number
  created_at: string
}

interface Listing {
  id: number
  title: string
  description: string
  price: number
  city: string
  seller_name: string
  seller_phone: string
  status: string
  is_paid: boolean
  is_promoted: boolean
  views_count: number
  created_at: string
}

interface Stats {
  totalProducts: number
  totalOrders: number
  pendingSellers: number
  pendingListings: number
}

function AdminContent() {
  const searchParams = useSearchParams()
  // Оборачиваем в try-catch или используем дефолт, так как useSearchParams может быть null на сервере (хотя это client component)
  const initialView = (searchParams?.get('view') as 'dashboard' | 'search' | 'edit' | 'sellers' | 'listings' | 'orders') || 'dashboard'
  
  const [view, setView] = useState<'dashboard' | 'search' | 'edit' | 'sellers' | 'listings' | 'orders'>(initialView)
  const [products, setProducts] = useState<Product[]>([])
  const [recentProducts, setRecentProducts] = useState<Product[]>([])
  const [sellers, setSellers] = useState<Seller[]>([])
  const [listings, setListings] = useState<Listing[]>([])
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [dashboardLoading, setDashboardLoading] = useState(true)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [saving, setSaving] = useState(false)
  const [stats, setStats] = useState<Stats>({ totalProducts: 0, totalOrders: 0, pendingSellers: 0, pendingListings: 0 })
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Update view when URL changes
  useEffect(() => {
    const viewParam = searchParams?.get('view') as 'dashboard' | 'search' | 'edit' | 'sellers' | 'listings' | 'orders'
    if (viewParam) {
      setView(viewParam)
      if (viewParam === 'sellers') loadSellers()
      if (viewParam === 'listings') loadListings()
      if (viewParam === 'orders') loadOrders()
    }
  }, [searchParams])

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    setDashboardLoading(true)
    setError(null)
    try {
      const [productsRes, countRes, sellersRes, listingsRes, ordersCountRes] = await Promise.all([
        fetch(`${API_URL}/products/?limit=5`).catch(() => null),
        fetch(`${API_URL}/products/count`).catch(() => null),
        fetch(`${API_URL}/marketplace/sellers/pending`).catch(() => null),
        fetch(`${API_URL}/marketplace/listings/pending`).catch(() => null),
        fetch(`${API_URL}/orders/count`).catch(() => null)
      ])
      
      if (productsRes?.ok) {
        const data = await productsRes.json()
        setRecentProducts(data)
      }
      
      if (countRes?.ok) {
        const countData = await countRes.json()
        setStats(prev => ({ ...prev, totalProducts: countData.count }))
      }

      if (sellersRes?.ok) {
        const sellersData = await sellersRes.json()
        setStats(prev => ({ ...prev, pendingSellers: sellersData.length }))
      }

      if (listingsRes?.ok) {
        const listingsData = await listingsRes.json()
        setStats(prev => ({ ...prev, pendingListings: listingsData.length }))
      }

      if (ordersCountRes?.ok) {
        const ordersData = await ordersCountRes.json()
        setStats(prev => ({ ...prev, totalOrders: ordersData.count }))
      }
    } catch (err) {
      console.error(err)
      setError("Не удалось подключиться к серверу.")
    } finally {
      setDashboardLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  // Load sellers
  const loadSellers = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/marketplace/sellers/`)
      if (res.ok) {
        const data = await res.json()
        setSellers(data)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Load listings
  const loadListings = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/marketplace/listings/pending`)
      if (res.ok) {
        const data = await res.json()
        setListings(data)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Load orders
  const loadOrders = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/orders/`)
      if (res.ok) {
        const data = await res.json()
        setOrders(data)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Update seller status
  const updateSellerStatus = async (sellerId: number, status: string, rejectionReason?: string, maxProducts?: number, subscriptionTier?: string) => {
    try {
      const body: any = { status }
      if (maxProducts) body.max_products = maxProducts
      if (subscriptionTier) body.subscription_tier = subscriptionTier
      
      const res = await fetch(`${API_URL}/marketplace/sellers/${sellerId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (res.ok) {
        let msg = `✅ Статус изменен на: ${status}`
        if (maxProducts) msg = "✅ Лимит обновлен"
        if (subscriptionTier) msg = `✅ Тариф изменен на ${subscriptionTier}`
        
        alert(msg)
        loadSellers()
        loadDashboard()
      } else {
        alert('❌ Ошибка обновления')
      }
    } catch (err) {
      alert('❌ Ошибка сети')
    }
  }

  // Update listing status
  const updateListingStatus = async (listingId: number, status: string, rejectionReason?: string) => {
    try {
      const res = await fetch(`${API_URL}/marketplace/listings/${listingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, rejection_reason: rejectionReason })
      })
      if (res.ok) {
        alert(`✅ Статус изменен на: ${status}`)
        loadListings()
        loadDashboard()
      } else {
        alert('❌ Ошибка обновления')
      }
    } catch (err) {
      alert('❌ Ошибка сети')
    }
  }

  // Search products
  const handleSearch = useCallback(async () => {
    const query = inputRef.current?.value || ""
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/products/?search=${encodeURIComponent(query)}&limit=20`)
      const data = await res.json()
      setProducts(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Upload image
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !editingProduct) return
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const res = await fetch(`${API_URL}/upload/image`, {
        method: 'POST',
        body: formData
      })
      
      if (res.ok) {
        const data = await res.json()
        setEditingProduct({ ...editingProduct, image_url: data.url })
        alert("✅ Фото загружено!")
      } else {
        alert("❌ Ошибка загрузки фото")
      }
    } catch (err) {
      alert("❌ Ошибка сети")
    }
  }

  // Save product
  const handleSave = async () => {
    if (!editingProduct) return
    setSaving(true)
    try {
      const res = await fetch(`${API_URL}/products/${editingProduct.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          price_rub: editingProduct.price_rub,
          stock_quantity: editingProduct.stock_quantity,
          image_url: editingProduct.image_url,
          is_in_stock: editingProduct.is_in_stock,
          is_installment_available: editingProduct.is_installment_available
        })
      })
      
      if (res.ok) {
        alert("✅ Изменения сохранены!")
        setEditingProduct(null)
        setView('dashboard')
      } else {
        const err = await res.text()
        alert("❌ Ошибка сохранения: " + err)
      }
    } catch (err) {
      alert("❌ Ошибка сети")
    } finally {
      setSaving(false)
    }
  }

  // ============ SELLERS VIEW ============
  if (view === 'sellers') {
    return (
      <div className="h-full overflow-y-auto bg-background text-foreground p-4">
        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="icon" onClick={() => setView('dashboard')}>
            <ArrowLeft className="h-6 w-6" />
          </Button>
          <h1 className="text-lg font-bold">🤝 Управление партнерами</h1>
          <Button variant="ghost" size="icon" onClick={loadSellers} className="ml-auto">
            <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-10 text-muted-foreground">Загрузка...</div>
        ) : sellers.length === 0 ? (
          <div className="text-center py-16">
            <Handshake className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">Нет заявок от партнеров</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sellers.map(seller => (
              <Card key={seller.id} className="bg-white/5 border-white/10 p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-bold text-lg">{seller.name}</h3>
                    <p className="text-sm text-muted-foreground">{seller.contact_name}</p>
                  </div>
                  <Badge className={
                    seller.status === 'approved' ? 'bg-green-500/20 text-green-400 border-0' :
                    seller.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400 border-0' :
                    seller.status === 'rejected' ? 'bg-red-500/20 text-red-400 border-0' :
                    'bg-gray-500/20 text-gray-400 border-0'
                  }>
                    {seller.status === 'approved' ? '✅ Одобрен' :
                     seller.status === 'pending' ? '⏳ Ожидает' :
                     seller.status === 'rejected' ? '❌ Отклонен' :
                     seller.status === 'banned' ? '🚫 Заблокирован' : seller.status}
                  </Badge>
                </div>

                <div className="space-y-1 text-sm text-muted-foreground mb-3">
                  {seller.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="h-3 w-3" />
                      <span>{seller.phone}</span>
                    </div>
                  )}
                  {seller.email && (
                    <div className="flex items-center gap-2">
                      <Mail className="h-3 w-3" />
                      <span>{seller.email}</span>
                    </div>
                  )}
                  {seller.telegram_username && (
                    <div className="flex items-center gap-2">
                      <MessageCircle className="h-3 w-3" />
                      <span>@{seller.telegram_username}</span>
                    </div>
                  )}
                </div>

                {seller.description && (
                  <p className="text-xs text-muted-foreground bg-white/5 p-2 rounded mb-3">
                    {seller.description}
                  </p>
                )}

                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                  <Badge variant="outline" className="text-[10px]">
                    {seller.subscription_tier || 'free'}
                  </Badge>
                  <span>•</span>
                  <span>До {seller.max_products} товаров</span>
                </div>

                <div className="flex gap-2">
                  {seller.status === 'pending' && (
                    <>
                      <Button 
                        size="sm" 
                        className="flex-1 bg-green-600 hover:bg-green-700"
                        onClick={() => updateSellerStatus(seller.id, 'approved')}
                      >
                        <Check className="h-4 w-4 mr-1" />
                        Одобрить
                      </Button>
                      <Button 
                        size="sm" 
                        variant="destructive"
                        className="flex-1"
                        onClick={() => updateSellerStatus(seller.id, 'rejected')}
                      >
                        <X className="h-4 w-4 mr-1" />
                        Отклонить
                      </Button>
                    </>
                  )}
                  {seller.status === 'approved' && (
                    <div className="flex flex-col gap-2 w-full">
                      <div className="flex gap-2 w-full">
                        <Button 
                          size="sm" 
                          variant="secondary"
                          className="flex-1"
                          onClick={() => {
                            const newLimit = prompt("Новый лимит товаров:", seller.max_products.toString());
                            if (newLimit) updateSellerStatus(seller.id, 'approved', undefined, parseInt(newLimit));
                          }}
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          Лимит
                        </Button>
                        <Button 
                          size="sm" 
                          variant="destructive"
                          className="flex-1"
                          onClick={() => updateSellerStatus(seller.id, 'banned')}
                        >
                          <Ban className="h-4 w-4 mr-1" />
                          Блок
                        </Button>
                      </div>
                      <div className="flex gap-2 w-full">
                         <select 
                            className="flex-1 h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            value={seller.subscription_tier || 'free'}
                            onChange={(e) => {
                                // @ts-ignore
                                updateSellerStatus(seller.id, seller.status, undefined, undefined, e.target.value)
                            }}
                         >
                            <option value="free">Free</option>
                            <option value="start">Start</option>
                            <option value="pro">Pro</option>
                            <option value="magnate">Magnate</option>
                         </select>
                      </div>
                    </div>
                  )}
                  {(seller.status === 'rejected' || seller.status === 'banned') && (
                    <Button 
                      size="sm" 
                      className="flex-1 bg-green-600 hover:bg-green-700"
                      onClick={() => updateSellerStatus(seller.id, 'approved')}
                    >
                      <Check className="h-4 w-4 mr-1" />
                      Восстановить
                    </Button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ============ LISTINGS VIEW ============
  if (view === 'listings') {
    return (
      <div className="h-full overflow-y-auto bg-background text-foreground p-4">
        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="icon" onClick={() => setView('dashboard')}>
            <ArrowLeft className="h-6 w-6" />
          </Button>
          <h1 className="text-lg font-bold">🏷️ Модерация барахолки</h1>
          <Button variant="ghost" size="icon" onClick={loadListings} className="ml-auto">
            <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-10 text-muted-foreground">Загрузка...</div>
        ) : listings.length === 0 ? (
          <div className="text-center py-16">
            <Tag className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">Нет объявлений на модерации</p>
          </div>
        ) : (
          <div className="space-y-3">
            {listings.map(listing => (
              <Card key={listing.id} className="bg-white/5 border-white/10 p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-bold">{listing.title}</h3>
                  <span className="font-bold text-primary">{listing.price?.toLocaleString()} ₽</span>
                </div>

                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                  {listing.description}
                </p>

                <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                  <span>📍 {listing.city}</span>
                  <span>👤 {listing.seller_name}</span>
                  <span>📞 {listing.seller_phone}</span>
                </div>

                <div className="flex items-center gap-2 mb-3">
                  <Badge className={listing.is_paid ? 'bg-green-500/20 text-green-400 border-0' : 'bg-yellow-500/20 text-yellow-400 border-0'}>
                    {listing.is_paid ? '💰 Оплачено' : '⏳ Не оплачено'}
                  </Badge>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Eye className="h-3 w-3" />
                    {listing.views_count}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    className="flex-1 bg-green-600 hover:bg-green-700"
                    onClick={() => updateListingStatus(listing.id, 'approved')}
                  >
                    <Check className="h-4 w-4 mr-1" />
                    Одобрить
                  </Button>
                  <Button 
                    size="sm" 
                    variant="destructive"
                    className="flex-1"
                    onClick={() => {
                      const reason = prompt('Причина отклонения:')
                      if (reason) updateListingStatus(listing.id, 'rejected', reason)
                    }}
                  >
                    <X className="h-4 w-4 mr-1" />
                    Отклонить
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    )
  }

  // ============ ORDERS VIEW ============
  if (view === 'orders') {
    return (
      <div className="h-full overflow-y-auto bg-background text-foreground p-4">
        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="icon" onClick={() => setView('dashboard')}>
            <ArrowLeft className="h-6 w-6" />
          </Button>
          <h1 className="text-lg font-bold">📦 Все заказы</h1>
          <Button variant="ghost" size="icon" onClick={loadOrders} className="ml-auto">
            <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {loading ? (
          <div className="text-center py-10 text-muted-foreground">Загрузка...</div>
        ) : orders.length === 0 ? (
          <div className="text-center py-16">
            <ShoppingCart className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">Нет заказов</p>
          </div>
        ) : (
          <div className="space-y-3">
            {orders.map((order: any) => (
              <Card key={order.id} className="bg-white/5 border-white/10 p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-bold">Заказ #{order.id}</h3>
                    <p className="text-xs text-muted-foreground">
                      {new Date(order.created_at).toLocaleString('ru-RU')}
                    </p>
                  </div>
                  <Badge className={
                    order.status === 'paid' ? 'bg-green-500/20 text-green-400 border-0' :
                    order.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400 border-0' :
                    'bg-gray-500/20 text-gray-400 border-0'
                  }>
                    {order.status === 'paid' ? '✅ Оплачен' : 
                     order.status === 'pending' ? '⏳ В обработке' : order.status}
                  </Badge>
                </div>

                <div className="flex items-center gap-3 text-xs text-muted-foreground mb-3">
                  <span>👤 {order.user_name || 'Не указано'}</span>
                  <span>📞 {order.user_phone || 'Не указано'}</span>
                </div>

                <div className="text-xs text-muted-foreground mb-3">
                  📍 {order.delivery_address || 'Адрес не указан'}
                </div>

                <div className="border-t border-white/10 pt-3 mt-3">
                  <p className="text-xs text-muted-foreground mb-2">Товары:</p>
                  {order.items?.map((item: any) => (
                    <div key={item.id} className="flex justify-between text-sm mb-1">
                      <span>{item.product?.name || `Товар #${item.product_id}`}</span>
                      <span className="text-muted-foreground">
                        {item.quantity} × {item.price_at_purchase?.toLocaleString()} ₽
                      </span>
                    </div>
                  ))}
                </div>

                <div className="flex justify-between items-center border-t border-white/10 pt-3 mt-3">
                  <span className="text-muted-foreground">Итого:</span>
                  <span className="font-bold text-lg text-primary">
                    {order.total_amount?.toLocaleString()} ₽
                  </span>
                </div>

                <div className="text-xs text-muted-foreground mt-2">
                  TG ID: {order.user_telegram_id}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Edit view
  if (view === 'edit' && editingProduct) {
    return (
      <div className="h-full overflow-y-auto bg-background text-foreground p-4">
        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="icon" onClick={() => { setEditingProduct(null); setView('search') }}>
            <ArrowLeft className="h-6 w-6" />
          </Button>
          <h1 className="text-lg font-bold">✏️ Редактирование</h1>
        </div>

        <div className="space-y-4">
          <Card className="bg-white/5 border-white/10 p-4">
            <p className="text-xs text-muted-foreground mb-1">Название</p>
            <p className="font-medium text-sm">{editingProduct.name}</p>
            <p className="text-xs text-muted-foreground mt-2">Артикул: {editingProduct.part_number}</p>
          </Card>

          <Card className="bg-white/5 border-white/10 p-4 space-y-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                <DollarSign className="h-3 w-3 inline mr-1" />
                Цена (₽)
              </label>
              <Input
                type="number"
                value={editingProduct.price_rub || ""}
                onChange={e => setEditingProduct({...editingProduct, price_rub: parseFloat(e.target.value) || 0})}
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                <Box className="h-3 w-3 inline mr-1" />
                Количество на складе
              </label>
              <Input
                type="number"
                value={editingProduct.stock_quantity || 0}
                onChange={e => setEditingProduct({...editingProduct, stock_quantity: parseInt(e.target.value) || 0})}
                className="bg-white/5 border-white/10"
              />
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                <ImageIcon className="h-3 w-3 inline mr-1" />
                Фото товара
              </label>
              
              {editingProduct.image_url && (
                <div className="mb-2 relative w-32 h-32 rounded-lg overflow-hidden bg-white/5">
                  <img 
                    src={editingProduct.image_url} 
                    alt="Preview" 
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              
              <div className="flex gap-2 mb-2">
                <label className="flex-1 cursor-pointer">
                  <div className="flex items-center justify-center gap-2 p-3 bg-ram-red/20 hover:bg-ram-red/30 border border-ram-red/50 rounded-lg transition-colors">
                    <Upload className="h-4 w-4" />
                    <span className="text-sm font-medium">📷 Загрузить фото</span>
                  </div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                </label>
              </div>
              
              <Input
                type="url"
                placeholder="Или вставьте URL фото..."
                value={editingProduct.image_url || ""}
                onChange={e => setEditingProduct({...editingProduct, image_url: e.target.value || null})}
                className="bg-white/5 border-white/10 text-xs"
              />
            </div>

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={editingProduct.is_in_stock}
                  onChange={e => setEditingProduct({...editingProduct, is_in_stock: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">✅ В наличии</span>
              </label>
            </div>

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={editingProduct.is_installment_available}
                  onChange={e => setEditingProduct({...editingProduct, is_installment_available: e.target.checked})}
                  className="rounded"
                />
                <span className="text-sm">
                  <Percent className="h-3 w-3 inline mr-1" />
                  Рассрочка 0%
                </span>
              </label>
            </div>
          </Card>

          <Button onClick={handleSave} disabled={saving} className="w-full bg-green-600 hover:bg-green-700">
            <Save className="h-4 w-4 mr-2" />
            {saving ? "Сохранение..." : "💾 Сохранить изменения"}
          </Button>
        </div>
      </div>
    )
  }

  // Search view
  if (view === 'search') {
    return (
      <div className="h-full overflow-y-auto bg-background text-foreground">
        <div className="sticky top-0 z-10 bg-background border-b border-white/5 p-4">
          <div className="flex items-center gap-3 mb-3">
            <Button variant="ghost" size="icon" onClick={() => setView('dashboard')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <h1 className="text-lg font-bold">🔍 Поиск товаров</h1>
          </div>
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              placeholder="Название или артикул..."
              onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
              className="bg-white/5 border-white/10"
            />
            <Button onClick={handleSearch} disabled={loading} className="bg-primary">
              <Search className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="p-4 space-y-2">
          {loading ? (
            <p className="text-center text-muted-foreground py-10">Загрузка...</p>
          ) : products.length > 0 ? (
            products.map(product => (
              <Card 
                key={product.id} 
                onClick={() => { setEditingProduct(product); setView('edit') }}
                className="bg-white/5 border-white/10 p-3 cursor-pointer hover:bg-white/10 transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                    {product.image_url ? (
                      <img src={product.image_url} alt="" className="w-full h-full object-cover rounded-lg" />
                    ) : (
                      <Package className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{product.name}</p>
                    <p className="text-xs text-muted-foreground">{product.part_number}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-sm">{product.price_rub?.toLocaleString()} ₽</p>
                    <div className="flex gap-1 mt-1">
                      {product.is_in_stock && <Badge className="text-[9px] bg-green-500/20 text-green-400 border-0">В наличии</Badge>}
                      {product.is_installment_available && <Badge className="text-[9px] bg-purple-500/20 text-purple-400 border-0">Рассрочка</Badge>}
                    </div>
                  </div>
                  <Edit className="h-4 w-4 text-muted-foreground" />
                </div>
              </Card>
            ))
          ) : (
            <div className="text-center py-16">
              <Search className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">Введите название или артикул</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Dashboard view
  return (
    <div className="h-full overflow-y-auto bg-background text-foreground p-4 pb-24">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-ram-red bg-clip-text text-transparent">
          🔧 RAM Admin
        </h1>
        <Button variant="ghost" size="icon" onClick={loadDashboard} disabled={dashboardLoading}>
          <RefreshCw className={`h-5 w-5 ${dashboardLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {error && (
        <Card className="bg-red-500/10 border-red-500/20 p-4 mb-6 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-400" />
          <p className="text-sm text-red-300">{error}</p>
        </Card>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <Card className="bg-gradient-to-br from-white/5 to-white/10 border-white/10 p-4 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
            <Package className="h-12 w-12" />
          </div>
          <div className="relative z-10">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Товаров</p>
            {dashboardLoading ? (
              <Skeleton className="h-8 w-20 bg-white/10" />
            ) : (
              <p className="text-2xl font-bold text-white">{stats.totalProducts.toLocaleString()}</p>
            )}
          </div>
        </Card>
        
        <Card 
          className="bg-gradient-to-br from-primary/20 to-primary/5 border-primary/20 p-4 relative overflow-hidden group cursor-pointer hover:border-primary/40 transition-all"
          onClick={() => { loadOrders(); setView('orders') }}
        >
          <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
            <ShoppingCart className="h-12 w-12 text-primary" />
          </div>
          <div className="relative z-10">
            <p className="text-xs text-primary/80 uppercase tracking-wider mb-1">Заказов</p>
            {dashboardLoading ? (
              <Skeleton className="h-8 w-16 bg-primary/10" />
            ) : (
              <p className="text-2xl font-bold text-primary">{stats.totalOrders}</p>
            )}
          </div>
        </Card>

        {/* Pending sellers */}
        <Card 
          className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border-yellow-500/20 p-4 relative overflow-hidden group cursor-pointer hover:border-yellow-500/40 transition-all"
          onClick={() => { loadSellers(); setView('sellers') }}
        >
          <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
            <Handshake className="h-12 w-12 text-yellow-400" />
          </div>
          <div className="relative z-10">
            <p className="text-xs text-yellow-400/80 uppercase tracking-wider mb-1">Партнеры</p>
            {dashboardLoading ? (
              <Skeleton className="h-8 w-16 bg-yellow-500/10" />
            ) : (
              <p className="text-2xl font-bold text-yellow-400">{stats.pendingSellers}</p>
            )}
            <p className="text-[10px] text-yellow-400/60">ожидают</p>
          </div>
        </Card>

        {/* Pending listings */}
        <Card 
          className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20 p-4 relative overflow-hidden group cursor-pointer hover:border-purple-500/40 transition-all"
          onClick={() => { loadListings(); setView('listings') }}
        >
          <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
            <Tag className="h-12 w-12 text-purple-400" />
          </div>
          <div className="relative z-10">
            <p className="text-xs text-purple-400/80 uppercase tracking-wider mb-1">Барахолка</p>
            {dashboardLoading ? (
              <Skeleton className="h-8 w-16 bg-purple-500/10" />
            ) : (
              <p className="text-2xl font-bold text-purple-400">{stats.pendingListings}</p>
            )}
            <p className="text-[10px] text-purple-400/60">на модерации</p>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <h2 className="font-bold mb-3 flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground">
        ⚡ Действия
      </h2>
      <div className="space-y-3 mb-8">
        <Card 
          className="bg-white/5 border-white/10 p-4 cursor-pointer hover:bg-white/10 transition-all group active:scale-[0.98]"
          onClick={() => setView('search')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/20 shadow-lg shadow-blue-500/10">
                <Search className="h-6 w-6 text-blue-400 group-hover:scale-110 transition-transform" />
              </div>
              <div>
                <p className="font-bold text-lg">Поиск товаров</p>
                <p className="text-xs text-muted-foreground">Редактирование цен, фото, остатков</p>
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-white transition-colors" />
          </div>
        </Card>

        <Card 
          className="bg-white/5 border-white/10 p-4 cursor-pointer hover:bg-white/10 transition-all group active:scale-[0.98]"
          onClick={() => { loadSellers(); setView('sellers') }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-yellow-500/20 to-yellow-600/10 border border-yellow-500/20 shadow-lg shadow-yellow-500/10">
                <Handshake className="h-6 w-6 text-yellow-400 group-hover:scale-110 transition-transform" />
              </div>
              <div>
                <p className="font-bold text-lg">🤝 Партнеры</p>
                <p className="text-xs text-muted-foreground">Одобрение, блокировка, управление</p>
              </div>
            </div>
            {stats.pendingSellers > 0 && (
              <Badge className="bg-yellow-500 text-black font-bold mr-2">{stats.pendingSellers}</Badge>
            )}
            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-white transition-colors" />
          </div>
        </Card>

        <Card 
          className="bg-white/5 border-white/10 p-4 cursor-pointer hover:bg-white/10 transition-all group active:scale-[0.98]"
          onClick={() => { loadListings(); setView('listings') }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/20 shadow-lg shadow-purple-500/10">
                <Tag className="h-6 w-6 text-purple-400 group-hover:scale-110 transition-transform" />
              </div>
              <div>
                <p className="font-bold text-lg">🏷️ Барахолка</p>
                <p className="text-xs text-muted-foreground">Модерация объявлений</p>
              </div>
            </div>
            {stats.pendingListings > 0 && (
              <Badge className="bg-purple-500 text-white font-bold mr-2">{stats.pendingListings}</Badge>
            )}
            <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-white transition-colors" />
          </div>
        </Card>
      </div>

      {/* Recent Products */}
      <h2 className="font-bold mb-3 flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground">
        📦 Недавно добавленные
      </h2>
      <div className="space-y-2">
        {dashboardLoading ? (
          Array(3).fill(0).map((_, i) => (
            <Card key={i} className="bg-white/5 border-white/10 p-3">
              <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded-lg bg-white/10" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4 bg-white/10" />
                  <Skeleton className="h-3 w-1/2 bg-white/10" />
                </div>
              </div>
            </Card>
          ))
        ) : recentProducts.length > 0 ? (
          recentProducts.map(product => (
            <Card 
              key={product.id}
              onClick={() => { setEditingProduct(product); setView('edit') }}
              className="bg-white/5 border-white/10 p-3 cursor-pointer hover:bg-white/10 transition-all active:scale-[0.98]"
            >
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0 overflow-hidden">
                  {product.image_url ? (
                    <img src={product.image_url} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <Package className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{product.name}</p>
                  <p className="text-xs text-muted-foreground font-mono">{product.part_number}</p>
                </div>
                <div className="text-right">
                    <p className="font-bold text-sm">{product.price_rub?.toLocaleString()} ₽</p>
                    {product.stock_quantity > 0 ? (
                        <span className="text-[10px] text-green-400">{product.stock_quantity} шт.</span>
                    ) : (
                        <span className="text-[10px] text-red-400">Нет</span>
                    )}
                </div>
              </div>
            </Card>
          ))
        ) : (
            <div className="text-center py-8 text-muted-foreground text-sm bg-white/5 rounded-lg border border-white/5">
                Нет товаров
            </div>
        )}
      </div>
    </div>
  )
}

export default function AdminPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen bg-background text-foreground">Загрузка...</div>}>
      <AdminContent />
    </Suspense>
  )
}
