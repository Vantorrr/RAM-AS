"use client"

import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ShoppingCart, Percent, Check, Store, ShieldCheck, Heart } from "lucide-react"
import { useCartStore } from "@/lib/cart-store"
import { useFavoritesStore } from "@/lib/favorites-store"
import { useState } from "react"

interface Product {
  id: number
  name: string
  price_rub: number
  price_usd?: number
  image_url: string
  part_number: string
  is_in_stock: boolean
  is_installment_available?: boolean
  seller?: {
    name: string
    is_verified: boolean
  }
}

interface ProductCardProps {
  product: Product
  onClick?: (productId: number) => void
}

export function ProductCard({ product, onClick }: ProductCardProps) {
  const [added, setAdded] = useState(false)
  const addItem = useCartStore((state) => state.addItem)
  const { isFavorite, toggleFavorite } = useFavoritesStore()
  
  const isFav = isFavorite(product.id)

  // Estimate monthly payment (e.g. 6 months)
  const monthlyPayment = Math.round(product.price_rub / 6);

  const handleAddToCart = () => {
    addItem({
      id: product.id,
      name: product.name,
      price_rub: product.price_rub,
      image_url: product.image_url,
      part_number: product.part_number,
      is_installment_available: product.is_installment_available
    })
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  return (
    <Card 
      className="group relative overflow-hidden border-white/5 bg-white/5 backdrop-blur-sm transition-all hover:-translate-y-1 hover:bg-white/10 hover:shadow-[0_10px_40px_-15px_rgba(0,0,0,0.5)] cursor-pointer flex flex-col h-full"
      onClick={() => onClick?.(product.id)}
    >
      <div className="relative h-32 w-full bg-gradient-to-b from-zinc-800/50 to-zinc-900/50 shrink-0 p-2">
        <Image
          src={product.image_url || "/logo_new.png"}
          alt={product.name}
          fill
          className={`transition-transform duration-500 group-hover:scale-105 object-contain ${!product.image_url ? "p-6 opacity-40" : "p-1"}`}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
        
        {/* Favorite Button */}
        <Button
            size="icon"
            variant="ghost"
            className="absolute top-1.5 left-1.5 h-6 w-6 rounded-full bg-black/40 hover:bg-black/60 z-20"
            onClick={(e) => {
                e.stopPropagation()
                toggleFavorite(product.id)
            }}
        >
            <Heart className={`h-3.5 w-3.5 ${isFav ? "fill-primary text-primary" : "text-white"}`} />
        </Button>

        {!product.is_in_stock && (
             <Badge variant="destructive" className="absolute top-1.5 right-1.5 shadow-lg text-[10px] px-1.5 h-5">Под заказ</Badge>
        )}
        {product.is_in_stock && (
             <Badge className="absolute top-1.5 right-1.5 bg-green-600 hover:bg-green-700 text-white shadow-lg border-0 text-[10px] px-1.5 h-5">В наличии</Badge>
        )}
        
        {product.is_installment_available && (
            <Badge className="absolute bottom-1.5 left-1.5 bg-purple-600 hover:bg-purple-700 text-white shadow-lg border-0 gap-0.5 pl-1 pr-1.5 text-[10px] h-5">
                <Percent className="h-2.5 w-2.5" /> 0%
            </Badge>
        )}
      </div>
      
      <CardContent className="p-3 flex flex-col flex-grow">
        {/* Seller Badge */}
        {product.seller ? (
            <div className="flex items-center gap-1.5 mb-1.5">
                <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-blue-500/30 bg-blue-500/10 text-blue-300 gap-1 rounded-sm font-normal">
                    <Store className="h-2.5 w-2.5" />
                    <span className="truncate max-w-[100px]">{product.seller.name}</span>
                    {product.seller.is_verified && <ShieldCheck className="h-2.5 w-2.5 text-blue-400" />}
                </Badge>
            </div>
        ) : (
            <div className="flex items-center gap-1.5 mb-1.5 opacity-0">
                <Badge className="h-4">Spacer</Badge> {/* Placeholder to align cards */}
            </div>
        )}

        <div className="flex items-center justify-between mb-1">
            <p className="text-[9px] font-mono text-muted-foreground bg-white/5 px-1 py-0.5 rounded truncate max-w-[80px]">{product.part_number}</p>
        </div>
        <h3 className="font-bold text-[13px] leading-[1.2] line-clamp-2 mb-auto group-hover:text-primary transition-colors h-[2.4em]">{product.name}</h3>
        
        <div className="flex flex-col mt-3 gap-1">
            <div className="flex items-baseline gap-2">
                <span className="text-base font-black text-white">{product.price_rub.toLocaleString('ru-RU')} ₽</span>
            </div>
            {product.is_installment_available ? (
                 <span className="text-[10px] text-purple-400 font-medium truncate">от {monthlyPayment.toLocaleString('ru-RU')} ₽/мес</span>
            ) : product.price_usd && (
                <span className="text-[10px] text-muted-foreground/70">~ ${product.price_usd}</span>
            )}
        </div>
      </CardContent>
      
      <CardFooter className="p-3 pt-0 mt-auto">
        <Button 
          className="w-full h-8 text-xs gap-1.5 bg-primary font-bold text-white shadow-[0_0_20px_-5px_rgba(211,47,47,0.5)] hover:bg-red-600 hover:shadow-[0_0_25px_-5px_rgba(211,47,47,0.7)] active:scale-95 transition-all"
          onClick={(e) => {
            e.stopPropagation()
            handleAddToCart()
          }}
          disabled={added}
        >
          {added ? (
            <>
              <Check className="h-3 w-3" />
              В КОРЗИНЕ
            </>
          ) : (
            <>
              <ShoppingCart className="h-3 w-3" />
              КУПИТЬ
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}

export function ProductCardSkeleton() {
    return (
        <Card className="overflow-hidden border-white/5 bg-white/5">
            <div className="aspect-square bg-white/5 animate-pulse" />
            <CardContent className="p-4 space-y-3">
                <div className="h-3 w-1/3 bg-white/10 rounded animate-pulse" />
                <div className="h-4 w-full bg-white/10 rounded animate-pulse" />
                <div className="h-4 w-2/3 bg-white/10 rounded animate-pulse" />
                <div className="h-6 w-1/2 bg-white/10 rounded animate-pulse mt-2" />
            </CardContent>
            <CardFooter className="p-4 pt-0">
                <div className="h-10 w-full bg-white/10 rounded animate-pulse" />
            </CardFooter>
        </Card>
    )
}
