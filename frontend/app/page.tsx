"use client"

import { SplashScreen } from "@/components/splash-screen"
import { BottomNav } from "@/components/bottom-nav"
import { CatalogView } from "@/components/views/catalog-view"
import { ProfileView } from "@/components/views/profile-view"
import { CartView } from "@/components/views/cart-view"
import { CheckoutView } from "@/components/views/checkout-view"
import { ProductDetailView } from "@/components/views/product-detail-view"
import { HomeView } from "@/components/views/home-view"
import { BaraholkaView } from "@/components/views/baraholka-view"
import { useState, useEffect } from "react"
import { initTelegramWebApp } from "@/lib/telegram"
import { useFavoritesStore } from "@/lib/favorites-store"

export default function Home() {
  const [showSplash, setShowSplash] = useState(true)
  const fetchFavorites = useFavoritesStore(state => state.fetchFavorites)
  
  // Инициализация Telegram WebApp
  useEffect(() => {
    const tg = initTelegramWebApp()
    if (tg) {
      console.log("Telegram WebApp initialized")
      console.log("User:", tg.initDataUnsafe?.user)
      // Загружаем избранное при старте
      fetchFavorites()
    }
  }, [])
  
  const [activeTab, setActiveTab] = useState("home")
  const [showCheckout, setShowCheckout] = useState(false)
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null)

  if (showSplash) {
    return <SplashScreen onComplete={() => setShowSplash(false)} />
  }

  const handleProductClick = (productId: number) => {
    setSelectedProductId(productId)
  }

  const handleCategoryClick = () => {
    setActiveTab("catalog")
  }

  return (
    <div className="h-full bg-background text-foreground flex flex-col font-sans selection:bg-primary/30 overflow-hidden">
      <main className="flex-1 overflow-y-auto overflow-x-hidden">
        {/* Product Detail - поверх всего */}
        {selectedProductId && (
          <div className="absolute inset-0 z-50 bg-background">
            <ProductDetailView 
              productId={selectedProductId} 
              onBack={() => setSelectedProductId(null)} 
            />
          </div>
        )}

        {/* Checkout - поверх всего */}
        {showCheckout && (
          <div className="absolute inset-0 z-50 bg-background">
            <CheckoutView 
              onBack={() => setShowCheckout(false)} 
              onSuccess={() => {
                setShowCheckout(false)
                setActiveTab("home")
                alert("Заказ успешно оформлен! Мы свяжемся с вами в ближайшее время.")
              }}
            />
          </div>
        )}

        {/* Основные вкладки - НЕ размонтируются, просто скрываются! */}
        <div className={activeTab === "catalog" ? "block" : "hidden"}>
          <CatalogView onProductClick={handleProductClick} />
        </div>
        
        <div className={activeTab === "profile" ? "block" : "hidden"}>
          <ProfileView onProductClick={handleProductClick} />
        </div>
        
        <div className={activeTab === "cart" ? "block" : "hidden"}>
          <CartView onCheckout={() => setShowCheckout(true)} />
        </div>
        
        <div className={activeTab === "marketplace" ? "block" : "hidden"}>
          <BaraholkaView onBack={() => setActiveTab("home")} />
        </div>
        
        <div className={activeTab === "home" ? "block" : "hidden"}>
          <HomeView 
            onCategoryClick={handleCategoryClick}
            onProductClick={handleProductClick}
            onViewAllProducts={() => setActiveTab("catalog")}
          />
        </div>
      </main>
      
      {!showCheckout && !selectedProductId && (
        <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
      )}
    </div>
  )
}
