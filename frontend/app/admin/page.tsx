"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  ArrowLeft, Search, Save, Package, DollarSign, 
  Image as ImageIcon, Percent, ShoppingCart, Users,
  TrendingUp, Box, Edit, ChevronRight, Upload, AlertCircle, RefreshCw
} from "lucide-react"
import { API_URL } from "@/lib/config"

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

interface Stats {
  totalProducts: number
  totalOrders: number
}

export default function AdminPage() {
  const [view, setView] = useState<'dashboard' | 'search' | 'edit'>('dashboard')
  const [products, setProducts] = useState<Product[]>([])
  const [recentProducts, setRecentProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [dashboardLoading, setDashboardLoading] = useState(true)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [saving, setSaving] = useState(false)
  const [stats, setStats] = useState<Stats>({ totalProducts: 0, totalOrders: 0 })
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    setDashboardLoading(true)
    setError(null)
    try {
      // Добавляем таймаут или обработку ошибок
      const [productsRes, countRes] = await Promise.all([
        fetch(`${API_URL}/products/?limit=5`).catch(err => { throw new Error("Failed to fetch products") }),
        fetch(`${API_URL}/products/count`).catch(err => { throw new Error("Failed to fetch count") })
      ])
      
      if (productsRes.ok) {
        const data = await productsRes.json()
        setRecentProducts(data)
      }
      
      if (countRes.ok) {
        const countData = await countRes.json()
        setStats(prev => ({ ...prev, totalProducts: countData.count }))
      }
    } catch (err) {
      console.error(err)
      setError("Не удалось подключиться к серверу. Проверьте соединение.")
    } finally {
      setDashboardLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

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
        const updated = await res.json()
        console.log("Saved:", updated)
        alert("✅ Изменения сохранены!")
        setEditingProduct(null)
        setView('dashboard')
      } else {
        const err = await res.text()
        console.error("Error:", err)
        alert("❌ Ошибка сохранения: " + err)
      }
    } catch (err) {
      console.error(err)
      alert("❌ Ошибка сети")
    } finally {
      setSaving(false)
    }
  }

  // Edit view
  if (view === 'edit' && editingProduct) {
    return (
      <div className="min-h-screen bg-background text-foreground p-4">
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
              
              {/* Preview */}
              {editingProduct.image_url && (
                <div className="mb-2 relative w-32 h-32 rounded-lg overflow-hidden bg-white/5">
                  <img 
                    src={editingProduct.image_url} 
                    alt="Preview" 
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
              
              {/* Upload button */}
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
              
              {/* Or enter URL */}
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
      <div className="min-h-screen bg-background text-foreground">
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
    <div className="min-h-screen bg-background text-foreground p-4 pb-24">
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
        
        <Card className="bg-gradient-to-br from-primary/20 to-primary/5 border-primary/20 p-4 relative overflow-hidden group">
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

        <Card className="bg-white/5 border-white/10 p-4 opacity-75 cursor-not-allowed">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                <TrendingUp className="h-6 w-6 text-amber-400/50" />
              </div>
              <div>
                <p className="font-medium text-muted-foreground">Массовое управление</p>
                <p className="text-xs text-muted-foreground/50">Цены, категории, импорт</p>
              </div>
            </div>
            <Badge variant="outline" className="text-[10px] border-white/10 text-muted-foreground">Скоро</Badge>
          </div>
        </Card>
      </div>

      {/* Recent Products */}
      <h2 className="font-bold mb-3 flex items-center gap-2 text-sm uppercase tracking-wider text-muted-foreground">
        📦 Недавно добавленные
      </h2>
      <div className="space-y-2">
        {dashboardLoading ? (
          // Skeletons
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
