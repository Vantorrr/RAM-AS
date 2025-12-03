"use client"

import { useState, useRef, useCallback } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Search, Save, Package, DollarSign, Image as ImageIcon, Percent } from "lucide-react"

interface Product {
  id: number
  name: string
  part_number: string
  price_rub: number
  image_url: string | null
  is_in_stock: boolean
  is_installment_available: boolean
  category_id: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function AdminPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [saving, setSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

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
        handleSearch() // Refresh
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
  if (editingProduct) {
    return (
      <div className="min-h-screen bg-background text-foreground p-4">
        <div className="flex items-center gap-3 mb-6">
          <Button variant="ghost" size="icon" onClick={() => setEditingProduct(null)}>
            <ArrowLeft className="h-6 w-6" />
          </Button>
          <h1 className="text-lg font-bold">Редактирование</h1>
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
                <span className="text-sm">В наличии</span>
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

          <Button onClick={handleSave} disabled={saving} className="w-full">
            <Save className="h-4 w-4 mr-2" />
            {saving ? "Сохранение..." : "Сохранить"}
          </Button>
        </div>
      </div>
    )
  }

  // Main admin view
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="sticky top-0 z-10 bg-background border-b border-white/5 p-4">
        <h1 className="text-xl font-bold mb-3">🔧 Админ-панель</h1>
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            placeholder="Поиск по названию или артикулу..."
            onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
            className="bg-white/5 border-white/10"
          />
          <Button onClick={handleSearch} disabled={loading}>
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
              onClick={() => setEditingProduct(product)}
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
              </div>
            </Card>
          ))
        ) : (
          <div className="text-center py-20">
            <Package className="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
            <p className="text-muted-foreground">Введите название или артикул товара</p>
          </div>
        )}
      </div>
    </div>
  )
}

