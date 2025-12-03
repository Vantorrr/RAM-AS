"use client"

import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ShoppingCart, Percent, Check } from "lucide-react"
import { useCartStore } from "@/lib/cart-store"
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
}

interface ProductCardProps {
  product: Product
  onClick?: (productId: number) => void
}

export function ProductCard({ product, onClick }: ProductCardProps) {
  const [added, setAdded] = useState(false)
  const addItem = useCartStore((state) => state.addItem)
  
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
      className="group relative overflow-hidden border-white/5 bg-white/5 backdrop-blur-sm transition-all hover:-translate-y-1 hover:bg-white/10 hover:shadow-[0_10px_40px_-15px_rgba(0,0,0,0.5)] cursor-pointer"
      onClick={() => onClick?.(product.id)}
    >
      <div className="aspect-square relative bg-black/20">
        <Image
          src={product.image_url || "/placeholder.svg"}
          alt={product.name}
          fill
          className="object-cover transition-transform duration-500 group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
        
        {!product.is_in_stock && (
             <Badge variant="destructive" className="absolute top-2 right-2 shadow-lg">Нет в наличии</Badge>
        )}
        {product.is_in_stock && (
             <Badge className="absolute top-2 right-2 bg-green-600 hover:bg-green-700 text-white shadow-lg border-0">В наличии</Badge>
        )}
        
        {product.is_installment_available && (
            <Badge className="absolute bottom-2 left-2 bg-purple-600 hover:bg-purple-700 text-white shadow-lg border-0 gap-1 pl-1 pr-2">
                <Percent className="h-3 w-3" /> Рассрочка 0%
            </Badge>
        )}
      </div>
      
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-1">
            <p className="text-[10px] font-mono text-muted-foreground bg-white/5 px-1.5 py-0.5 rounded">{product.part_number}</p>
        </div>
        <h3 className="font-bold text-sm leading-tight line-clamp-2 min-h-[2.5rem] mb-3 group-hover:text-primary transition-colors">{product.name}</h3>
        <div className="flex flex-col">
            <div className="flex items-baseline gap-2">
                <span className="text-lg font-black text-white">{product.price_rub.toLocaleString('ru-RU')} ₽</span>
            </div>
            {product.is_installment_available ? (
                 <span className="text-xs text-purple-400 font-medium">от {monthlyPayment.toLocaleString('ru-RU')} ₽ / мес</span>
            ) : product.price_usd && (
                <span className="text-xs text-muted-foreground/70">~ ${product.price_usd} USD</span>
            )}
        </div>
      </CardContent>
      
      <CardFooter className="p-4 pt-0">
        <Button 
          className="w-full gap-2 bg-primary font-bold text-white shadow-[0_0_20px_-5px_rgba(211,47,47,0.5)] hover:bg-red-600 hover:shadow-[0_0_25px_-5px_rgba(211,47,47,0.7)] active:scale-95 transition-all"
          onClick={(e) => {
            e.stopPropagation()
            handleAddToCart()
          }}
          disabled={added}
        >
          {added ? (
            <>
              <Check className="h-4 w-4" />
              ДОБАВЛЕНО
            </>
          ) : (
            <>
              <ShoppingCart className="h-4 w-4" />
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
