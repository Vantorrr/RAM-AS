"use client"

import { useState, useEffect } from "react"
import { ArrowLeft, ShoppingCart, Check, Package, Truck, Shield, Store, ShieldCheck, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useCartStore } from "@/lib/cart-store"
import Image from "next/image"
import { API_URL } from "@/lib/config"

interface Product {
  id: number
  name: string
  part_number: string
  manufacturer?: string
  description?: string
  price_rub: number
  price_usd?: number
  image_url: string
  images?: string[]  // Дополнительные фото (галерея)
  is_in_stock: boolean
  stock_quantity: number
  is_installment_available?: boolean
  is_preorder: boolean
  seller?: {
    id: number
    name: string
    is_verified: boolean
    logo_url?: string
  }
}

interface ProductDetailViewProps {
  productId: number
  onBack: () => void
}

export function ProductDetailView({ productId, onBack }: ProductDetailViewProps) {
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [added, setAdded] = useState(false)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const addItem = useCartStore((state) => state.addItem)

  useEffect(() => {
    async function fetchProduct() {
      try {
        const res = await fetch(`${API_URL}/products/${productId}`)
        if (!res.ok) throw new Error('Failed to fetch product')
        const data = await res.json()
        setProduct(data)
      } catch (error) {
        console.error("Error loading product:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchProduct()
  }, [productId])

  const handleAddToCart = () => {
    if (!product) return
    addItem({
      id: product.id,
      name: product.name,
      price_rub: product.price_rub,
      image_url: product.image_url,
      part_number: product.part_number,
      is_installment_available: product.is_installment_available,
      is_preorder: product.is_preorder
    })
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-4 pb-24">
        <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-md border-b border-white/5 px-4 py-3">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-6 w-6" />
          </Button>
        </div>
        <div className="px-4 space-y-4">
          <Skeleton className="aspect-square w-full bg-white/5" />
          <Skeleton className="h-8 w-3/4 bg-white/5" />
          <Skeleton className="h-4 w-1/2 bg-white/5" />
          <Skeleton className="h-20 w-full bg-white/5" />
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-4">
        <p className="text-muted-foreground">Товар не найден</p>
        <Button onClick={onBack} className="mt-4">Назад</Button>
      </div>
    )
  }

  const monthlyPayment = product.is_installment_available 
    ? (product.price_rub / 12).toFixed(0) 
    : null

  return (
    <div className="flex flex-col pb-32">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-md border-b border-white/5 px-4 py-3">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={onBack}
          className="-ml-2 text-muted-foreground hover:text-white"
        >
          <ArrowLeft className="h-6 w-6" />
        </Button>
      </div>

      {/* Image Gallery */}
      <div className="relative aspect-[4/3] w-full bg-gradient-to-b from-zinc-900 to-black flex items-center justify-center p-4">
        <Image
          src={selectedImage || product.image_url || "/logo_new.png"}
          alt={product.name}
          fill
          className={`transition-all duration-500 object-contain ${!product.image_url ? "p-12 opacity-50" : "p-2"}`}
        />
        {!product.is_in_stock && (
          <Badge variant="destructive" className="absolute top-4 right-4 shadow-lg">
            Нет в наличии
          </Badge>
        )}
        {product.is_in_stock && (
          <Badge className="absolute top-4 right-4 bg-green-600 hover:bg-green-700 text-white shadow-lg border-0">
            В наличии
          </Badge>
        )}
      </div>
      
      {/* Миниатюры фото */}
      {((product.images && product.images.length > 0) || product.image_url) && (
        <div className="flex gap-2 px-4 py-2 overflow-x-auto">
          {/* Главное фото */}
          {product.image_url && (
            <button
              onClick={() => setSelectedImage(null)}
              className={`relative w-16 h-16 rounded-lg overflow-hidden shrink-0 border-2 transition-all ${
                !selectedImage ? 'border-green-500' : 'border-white/10 opacity-60 hover:opacity-100'
              }`}
            >
              <Image src={product.image_url} alt="Фото 1" fill className="object-cover" />
            </button>
          )}
          
          {/* Дополнительные фото */}
          {product.images?.map((url, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedImage(url)}
              className={`relative w-16 h-16 rounded-lg overflow-hidden shrink-0 border-2 transition-all ${
                selectedImage === url ? 'border-green-500' : 'border-white/10 opacity-60 hover:opacity-100'
              }`}
            >
              <Image src={url} alt={`Фото ${idx + 2}`} fill className="object-cover" />
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      <div className="px-4 pt-6 space-y-6">
        {/* Title & Price */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="outline" className="text-xs font-mono">
              {product.part_number}
            </Badge>
            {product.manufacturer && (
              <Badge variant="secondary" className="text-xs">
                {product.manufacturer}
              </Badge>
            )}
          </div>
          <h1 className="text-2xl font-bold mb-4">{product.name}</h1>
          
          <div className="flex items-baseline gap-3 mb-2">
            <span className="text-3xl font-black text-white">
              {product.price_rub.toLocaleString('ru-RU')} ₽
            </span>
            {product.price_usd && (
              <span className="text-lg text-muted-foreground">
                ~ ${product.price_usd} USD
              </span>
            )}
          </div>

          {product.is_installment_available && monthlyPayment && (
            <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20 p-3 mt-3">
              <p className="text-sm text-purple-400 font-medium">
                💳 Рассрочка 0% — от {monthlyPayment} ₽/мес на 12 месяцев
              </p>
            </Card>
          )}
        </div>

        {/* Seller Info */}
        {product.seller && (
            <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20 p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-blue-500/20 flex items-center justify-center overflow-hidden">
                            {product.seller.logo_url ? (
                                <img src={product.seller.logo_url} alt="" className="w-full h-full object-cover" />
                            ) : (
                                <Store className="h-5 w-5 text-blue-400" />
                            )}
                        </div>
                        <div>
                            <div className="flex items-center gap-1.5">
                                <p className="font-bold text-sm">{product.seller.name}</p>
                                {product.seller.is_verified && (
                                    <ShieldCheck className="h-3.5 w-3.5 text-blue-400" />
                                )}
                            </div>
                            <p className="text-xs text-blue-300/70">Проверенный партнер</p>
                        </div>
                    </div>
                    <Button variant="outline" size="sm" className="h-8 text-xs border-blue-500/30 text-blue-300 hover:bg-blue-500/10">
                        В магазин
                    </Button>
                </div>
            </Card>
        )}

        {/* Description */}
        {product.description && (
          <div>
            <h3 className="font-semibold mb-2">Описание</h3>
            <p className="text-muted-foreground leading-relaxed">
              {product.description}
            </p>
          </div>
        )}

        {/* Features */}
        <div className="grid grid-cols-1 gap-3">
          <Card className="bg-white/5 border-white/10 p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center">
                <Package className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">Оригинальная запчасть</p>
                <p className="text-xs text-muted-foreground">Прямые поставки из США</p>
              </div>
            </div>
          </Card>

          <Card className="bg-white/5 border-white/10 p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                <Truck className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="font-medium">Быстрая доставка</p>
                <p className="text-xs text-muted-foreground">По всей России через СДЭК</p>
              </div>
            </div>
          </Card>

          <Card className="bg-white/5 border-white/10 p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-green-500/20 flex items-center justify-center">
                <Shield className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="font-medium">Гарантия качества</p>
                <p className="text-xs text-muted-foreground">Проверка перед отправкой</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Fixed Bottom Button */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/95 backdrop-blur-xl border-t border-white/10 p-4 z-40">
        {product.is_preorder ? (
          <div className="space-y-2">
            <Button 
              size="lg" 
              className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold shadow-lg shadow-amber-600/30 transition-all hover:shadow-amber-600/50 hover:scale-[1.02] active:scale-95"
              onClick={handleAddToCart}
              disabled={added}
            >
              {added ? (
                <>
                  <Check className="mr-2 h-5 w-5" />
                  Добавлено в корзину
                </>
              ) : (
                <>
                  <Clock className="mr-2 h-5 w-5" />
                  Заказать под заказ
                </>
              )}
            </Button>
            <p className="text-xs text-center text-amber-400">
              ⏱️ Срок поставки: 4-6 недель • Оплата онлайн
            </p>
          </div>
        ) : (
          <Button 
            size="lg" 
            className="w-full bg-primary hover:bg-primary/90 text-white font-bold shadow-lg shadow-primary/30 transition-all hover:shadow-primary/50 hover:scale-[1.02] active:scale-95"
            onClick={handleAddToCart}
            disabled={added || !product.is_in_stock}
          >
            {added ? (
              <>
                <Check className="mr-2 h-5 w-5" />
                Добавлено в корзину
              </>
            ) : (
              <>
                <ShoppingCart className="mr-2 h-5 w-5" />
                {product.is_in_stock ? "Добавить в корзину" : "Нет в наличии"}
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  )
}



