"use client"

import { useEffect, useState } from "react"
import { ProductCard, ProductCardSkeleton } from "@/components/product-card"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ChevronRight, Wrench, Settings, Fuel, Disc, Zap, Sparkles, Warehouse, Package, Truck, Thermometer, Wind } from "lucide-react"
import Image from "next/image"

interface Product {
  id: number
  name: string
  price_rub: number
  price_usd?: number
  image_url: string
  part_number: string
  is_in_stock: boolean
  is_installment_available?: boolean
}

interface Category {
  id: number
  name: string
  slug: string
  children?: Category[]
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Иконки для категорий
const categoryIcons: Record<string, React.ReactNode> = {
  "Детали для ТО": <Wrench className="h-5 w-5" />,
  "Двигатель": <Settings className="h-5 w-5" />,
  "Топливная система": <Fuel className="h-5 w-5" />,
  "Система охлаждения": <Thermometer className="h-5 w-5" />,
  "Система выпуска": <Wind className="h-5 w-5" />,
  "Трансмиссия": <Disc className="h-5 w-5" />,
  "Электрооборудование": <Zap className="h-5 w-5" />,
  "Тюнинг": <Sparkles className="h-5 w-5" />,
}

interface HomeViewProps {
  onCategoryClick: (categoryId: number) => void
  onProductClick: (productId: number) => void
  onViewAllProducts: () => void
}

export function HomeView({ onCategoryClick, onProductClick, onViewAllProducts }: HomeViewProps) {
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingCats, setLoadingCats] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        // Загружаем категории и товары параллельно
        const [catsRes, prodsRes] = await Promise.all([
          fetch(`${API_URL}/categories/tree`),
          fetch(`${API_URL}/products/?limit=10`)
        ])
        
        if (catsRes.ok) {
          const catsData = await catsRes.json()
          setCategories(catsData)
        }
        
        if (prodsRes.ok) {
          const prodsData = await prodsRes.json()
          setProducts(prodsData)
        }
      } catch (error) {
        console.error("Error loading data:", error)
      } finally {
        setLoading(false)
        setLoadingCats(false)
      }
    }
    fetchData()
  }, [])

  // Берём первые 6 категорий для превью
  const previewCategories = categories.slice(0, 6)

  return (
    <div className="flex flex-col gap-6 pb-24">
      {/* Header with Logo */}
      <div className="px-4 pt-4 pb-2 flex items-center justify-between">
        <div className="relative h-10 w-32">
          <Image 
            src="/logo_new.png" 
            alt="RAM US" 
            fill
            className="object-contain object-left"
            priority
          />
        </div>
      </div>

      {/* Hero Banner */}
      <div className="px-4">
        <div className="relative h-36 w-full bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 rounded-2xl overflow-hidden">
          {/* RAM-US Background Text */}
          <div className="absolute inset-0 flex items-center justify-center select-none pointer-events-none overflow-hidden">
            <span className="text-[90px] font-black tracking-tighter text-white/[0.08] whitespace-nowrap translate-x-6 -translate-y-2">
              RAM-US
            </span>
          </div>
          {/* Red glow effect */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(211,47,47,0.3),transparent_50%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(211,47,47,0.15),transparent_50%)]" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
          {/* Content */}
          <div className="relative z-10 flex flex-col justify-end h-full p-4">
            <Badge className="w-fit mb-2 bg-primary/30 text-primary border-0 text-[10px]">
              ДОСТАВКА ПО ВСЕЙ РОССИИ
            </Badge>
            <h1 className="text-xl font-black tracking-tight text-white">
              Оригинальные запчасти из <span className="text-primary">США</span>
            </h1>
          </div>
        </div>
      </div>

      {/* Quick Categories */}
      <section className="px-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-bold text-white">Категории</h2>
          <Button 
            variant="ghost" 
            size="sm" 
            className="text-xs text-primary hover:text-primary/80 -mr-2"
            onClick={onViewAllProducts}
          >
            Все <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
        
        {loadingCats ? (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex-shrink-0 w-20 h-24 bg-white/5 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
            {previewCategories.map((cat) => {
              const icon = categoryIcons[cat.name] || <Package className="h-5 w-5" />
              return (
                <Card 
                  key={cat.id}
                  onClick={() => onCategoryClick(cat.id)}
                  className="flex-shrink-0 w-20 h-24 bg-white/5 border-white/10 flex flex-col items-center justify-center gap-2 cursor-pointer hover:bg-white/10 transition-all active:scale-95"
                >
                  <div className="p-2 rounded-lg bg-primary/20 text-primary">
                    {icon}
                  </div>
                  <span className="text-[10px] text-center text-muted-foreground leading-tight px-1 line-clamp-2">
                    {cat.name}
                  </span>
                </Card>
              )
            })}
            
            {/* Все товары */}
            <Card 
              onClick={onViewAllProducts}
              className="flex-shrink-0 w-20 h-24 bg-gradient-to-br from-primary/20 to-primary/10 border-primary/30 flex flex-col items-center justify-center gap-2 cursor-pointer hover:from-primary/30 hover:to-primary/20 transition-all active:scale-95"
            >
              <div className="p-2 rounded-lg bg-primary/30 text-primary">
                <Warehouse className="h-5 w-5" />
              </div>
              <span className="text-[10px] text-center text-primary font-medium leading-tight px-1">
                Все товары
              </span>
            </Card>
          </div>
        )}
      </section>

      {/* Stats Row */}
      <section className="px-4">
        <div className="flex gap-2">
          <Card className="flex-1 bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20 p-3 text-center">
            <div className="text-2xl font-black text-blue-400">USA</div>
            <p className="text-[10px] text-white/60">Прямые поставки</p>
          </Card>
          <Card className="flex-1 bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20 p-3 text-center">
            <div className="text-2xl font-black text-white">12<span className="text-amber-400">+</span></div>
            <p className="text-[10px] text-white/60">Лет на рынке</p>
          </Card>
          <Card className="flex-1 bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20 p-3 text-center">
            <div className="text-2xl font-black text-white">13<span className="text-green-400">K</span></div>
            <p className="text-[10px] text-white/60">Товаров</p>
          </Card>
        </div>
      </section>

      {/* Delivery Banner */}
      <section className="px-4">
        <Card className="bg-gradient-to-r from-emerald-500/15 to-teal-500/10 border-emerald-500/20 p-4 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
            <Truck className="w-6 h-6 text-emerald-400" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-white text-sm">Доставка по всей России</h3>
            <p className="text-xs text-emerald-300/70">СДЭК • Почта России • До двери</p>
          </div>
        </Card>
      </section>

      {/* Products Section */}
      <section className="px-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="h-5 w-1 bg-primary rounded-full" />
            Популярные товары
          </h2>
          <Button 
            variant="ghost" 
            size="sm" 
            className="text-xs text-primary hover:text-primary/80 -mr-2"
            onClick={onViewAllProducts}
          >
            Все товары <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
        
        {loading ? (
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <ProductCardSkeleton key={i} />
            ))}
          </div>
        ) : products.length > 0 ? (
          <div className="grid grid-cols-2 gap-3">
            {products.slice(0, 4).map((product) => (
              <ProductCard key={product.id} product={product} onClick={onProductClick} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 border border-dashed border-white/10 rounded-xl bg-white/5">
            <p className="text-muted-foreground mb-2">Загружаем товары...</p>
          </div>
        )}
      </section>

      {/* More Products */}
      {products.length > 4 && (
        <section className="px-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="h-5 w-1 bg-green-500 rounded-full" />
              Новые поступления
            </h2>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            {products.slice(4, 8).map((product) => (
              <ProductCard key={product.id} product={product} onClick={onProductClick} />
            ))}
          </div>
        </section>
      )}

      {/* Bottom CTA */}
      <section className="px-4">
        <Card 
          className="bg-gradient-to-br from-primary/20 to-primary/5 border-primary/30 p-5 text-center cursor-pointer hover:from-primary/30 transition-all"
          onClick={onViewAllProducts}
        >
          <Warehouse className="h-8 w-8 mx-auto mb-2 text-primary" />
          <h3 className="font-bold text-white mb-1">Смотреть весь каталог</h3>
          <p className="text-xs text-muted-foreground">13,476 товаров в наличии</p>
        </Card>
      </section>
    </div>
  )
}

