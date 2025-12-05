"use client"

import { useCartStore } from "@/lib/cart-store"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Minus, Plus, Trash2, ShoppingBag } from "lucide-react"
import Image from "next/image"

interface CartViewProps {
  onCheckout?: () => void
}

export function CartView({ onCheckout }: CartViewProps) {
  const { items, updateQuantity, removeItem, getTotalPrice, getTotalItems } = useCartStore()
  const totalPrice = getTotalPrice()
  const totalItems = getTotalItems()

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
        <div className="rounded-full bg-white/5 p-6 mb-6">
          <ShoppingBag className="h-16 w-16 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Корзина пуста</h2>
        <p className="text-muted-foreground mb-6">
          Добавьте товары из каталога, чтобы оформить заказ
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 pb-32 px-4">
      <div className="pt-4">
        <h2 className="text-2xl font-bold text-white">Корзина</h2>
        <p className="text-sm text-muted-foreground">
          {totalItems} {totalItems === 1 ? 'товар' : totalItems < 5 ? 'товара' : 'товаров'}
        </p>
      </div>

      <div className="space-y-3">
        {items.map((item) => (
          <Card key={item.id} className="bg-card/30 backdrop-blur-sm border-white/10 p-3">
            <div className="flex gap-3">
              <div className="relative h-20 w-20 flex-shrink-0 rounded-lg overflow-hidden bg-white/5">
                <Image
                  src={item.image_url || "https://placehold.co/200x200/1a1a1a/666?text=RAM+US"}
                  alt={item.name}
                  fill
                  className="object-cover"
                />
              </div>
              
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-sm line-clamp-2 mb-1">{item.name}</h3>
                <p className="text-xs text-muted-foreground mb-2">Арт: {item.part_number}</p>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 bg-white/5 rounded-lg p-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 text-muted-foreground hover:text-white"
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                    >
                      <Minus className="h-3 w-3" />
                    </Button>
                    <span className="text-sm font-medium w-6 text-center">{item.quantity}</span>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 text-muted-foreground hover:text-white"
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                    >
                      <Plus className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 text-muted-foreground hover:text-red-500"
                    onClick={() => removeItem(item.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <div className="flex flex-col items-end justify-between">
                <p className="text-lg font-bold text-white">
                  {(item.price_rub * item.quantity).toLocaleString('ru-RU')} ₽
                </p>
                {item.is_installment_available && (
                  <p className="text-xs text-purple-400">
                    {((item.price_rub * item.quantity) / 12).toFixed(0)} ₽/мес
                  </p>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Fixed Bottom Bar */}
      <div className="fixed bottom-16 left-0 right-0 bg-background/95 backdrop-blur-xl border-t border-white/10 p-4 z-40">
        <div className="container max-w-2xl mx-auto space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Товары ({totalItems})</span>
            <span className="font-semibold">{totalPrice.toLocaleString('ru-RU')} ₽</span>
          </div>
          
          <Button 
            size="lg" 
            className="w-full bg-primary hover:bg-primary/90 text-white font-bold shadow-lg shadow-primary/30 transition-all hover:shadow-primary/50 hover:scale-[1.02] active:scale-95"
            onClick={onCheckout}
          >
            Оформить заказ
          </Button>
        </div>
      </div>
    </div>
  )
}



