"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { 
  ArrowLeft, Search, Save, Package, DollarSign, 
  Image as ImageIcon, Percent, ShoppingCart, Users,
  TrendingUp, Box, Edit, ChevronRight
} from "lucide-react"

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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function AdminPage() {
  const [view, setView] = useState<'dashboard' | 'search' | 'edit'>('dashboard')
  const [products, setProducts] = useState<Product[]>([])
  const [recentProducts, setRecentProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [saving, setSaving] = useState(false)
  const [stats, setStats] = useState<Stats>({ totalProducts: 0, totalOrders: 0 })
  const inputRef = useRef<HTMLInputElement>(null)

  // Load dashboard data
  useEffect(() => {
    async function loadDashboard() {
      try {
        const [productsRes, countRes] = await Promise.all([
          fetch(`${API_URL}/products/?limit=5`),
          fetch(`${API_URL}/products/count`)
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
      }
    }
    loadDashboard()
  }, [])

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

  // Save product
  const handleSave = async () => {
    if (!editingProduct) return
    setSaving(true)
    try {
      const res = await fetch(`${API_URL}/products/${editingProduct.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editingProduct)
      })
      if (res.ok) {
        alert("✅ Сохранено!")
        setEditingProduct(null)
        setView('dashboard')
      } else {
        alert("❌ Ошибка сохранения")
      }
    } catch (err) {
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
                URL фото
              </label>
              <Input
                type="url"
                placeholder="https://..."
                value={editingProduct.image_url || ""}
                onChange={e => setEditingProduct({...editingProduct, image_url: e.target.value || null})}
                className="bg-white/5 border-white/10"
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
    <div className="min-h-screen bg-background text-foreground p-4">
      <h1 className="text-xl font-bold mb-4">🔧 Админ-панель</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/30 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <Package className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.totalProducts.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">Товаров</p>
            </div>
          </div>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500/20 to-green-600/10 border-green-500/30 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/20">
              <ShoppingCart className="h-5 w-5 text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.totalOrders}</p>
              <p className="text-xs text-muted-foreground">Заказов</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <h2 className="font-bold mb-3">⚡ Быстрые действия</h2>
      <div className="space-y-2 mb-6">
        <Card 
          className="bg-white/5 border-white/10 p-4 cursor-pointer hover:bg-white/10 transition-all"
          onClick={() => setView('search')}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/20">
                <Search className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">Найти и редактировать товар</p>
                <p className="text-xs text-muted-foreground">Изменить цену, фото, рассрочку</p>
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          </div>
        </Card>

        <Card className="bg-white/5 border-white/10 p-4 cursor-pointer hover:bg-white/10 transition-all">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <TrendingUp className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="font-medium">Массовое изменение цен</p>
                <p className="text-xs text-muted-foreground">Скоро...</p>
              </div>
            </div>
            <Badge className="bg-amber-500/20 text-amber-400 border-0 text-[10px]">Soon</Badge>
          </div>
        </Card>
      </div>

      {/* Recent Products */}
      <h2 className="font-bold mb-3">📦 Последние товары</h2>
      <div className="space-y-2">
        {recentProducts.map(product => (
          <Card 
            key={product.id}
            onClick={() => { setEditingProduct(product); setView('edit') }}
            className="bg-white/5 border-white/10 p-3 cursor-pointer hover:bg-white/10 transition-all"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                <Package className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{product.name}</p>
                <p className="text-xs text-muted-foreground">{product.part_number}</p>
              </div>
              <p className="font-bold text-sm">{product.price_rub?.toLocaleString()} ₽</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
