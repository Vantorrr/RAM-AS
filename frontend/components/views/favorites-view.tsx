"use client"

import { useState, useEffect } from "react"
import { ArrowLeft } from "lucide-react"
import { ProductCard, ProductCardSkeleton } from "@/components/product-card"
import { Button } from "@/components/ui/button"
import { API_URL } from "@/lib/config"
import { getTelegramUser } from "@/lib/telegram"

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

interface FavoritesViewProps {
    onBack: () => void
    onProductClick: (productId: number) => void
}

export function FavoritesView({ onBack, onProductClick }: FavoritesViewProps) {
    const [products, setProducts] = useState<Product[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchFavorites = async () => {
            const user = getTelegramUser()
            if (!user) {
                setLoading(false)
                return
            }

            try {
                const res = await fetch(`${API_URL}/favorites/${user.id}`)
                if (res.ok) {
                    const data = await res.json()
                    setProducts(data)
                }
            } catch (err) {
                console.error("Failed to fetch favorites:", err)
            } finally {
                setLoading(false)
            }
        }

        fetchFavorites()
    }, [])

    return (
        <div className="flex flex-col pb-24 min-h-screen">
            {/* Header */}
            <div className="sticky top-0 z-20 bg-background border-b border-white/5">
                <div className="px-4 py-3 flex items-center gap-3">
                    <Button variant="ghost" size="icon" onClick={onBack} className="-ml-2">
                        <ArrowLeft className="h-6 w-6" />
                    </Button>
                    <div className="flex-1">
                        <h2 className="text-lg font-bold">Избранное</h2>
                        <p className="text-xs text-muted-foreground">{products.length} товаров</p>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="px-4 pt-4">
                {loading ? (
                    <div className="grid grid-cols-2 gap-3">
                        {Array.from({ length: 6 }).map((_, i) => <ProductCardSkeleton key={i} />)}
                    </div>
                ) : products.length > 0 ? (
                    <div className="grid grid-cols-2 gap-3">
                        {products.map(p => (
                            <ProductCard key={p.id} product={p} onClick={onProductClick} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-20">
                        <p className="text-lg font-medium">В избранном пусто</p>
                        <p className="text-sm text-muted-foreground mt-2">
                            Добавляйте товары, нажимая на сердечко ❤️
                        </p>
                        <Button variant="outline" className="mt-6" onClick={onBack}>
                            Перейти в каталог
                        </Button>
                    </div>
                )}
            </div>
        </div>
    )
}

