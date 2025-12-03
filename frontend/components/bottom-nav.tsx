"use client"

import { Home, Search, ShoppingCart, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useCartStore } from "@/lib/cart-store"

interface BottomNavProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

export function BottomNav({ activeTab, onTabChange }: BottomNavProps) {
  const cartItems = useCartStore(state => state.getTotalItems())
  
  return (
    <div className="fixed bottom-0 left-0 z-50 w-full border-t border-white/10 bg-black/80 backdrop-blur-xl pb-safe supports-[backdrop-filter]:bg-black/60">
      <div className="flex h-16 items-center justify-around px-2">
        <NavButton 
          icon={Home} 
          label="Главная" 
          isActive={activeTab === 'home'} 
          onClick={() => onTabChange('home')} 
        />
        <NavButton 
          icon={Search} 
          label="Каталог" 
          isActive={activeTab === 'catalog'} 
          onClick={() => onTabChange('catalog')} 
        />
        <NavButton 
          icon={ShoppingCart} 
          label="Корзина" 
          isActive={activeTab === 'cart'} 
          onClick={() => onTabChange('cart')} 
          badge={cartItems}
        />
        <NavButton 
          icon={User} 
          label="Профиль" 
          isActive={activeTab === 'profile'} 
          onClick={() => onTabChange('profile')} 
        />
      </div>
    </div>
  )
}

function NavButton({ icon: Icon, label, isActive, onClick, badge }: any) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn(
        "relative flex h-full flex-1 flex-col items-center justify-center gap-1 rounded-none hover:bg-white/5 active:scale-95 transition-all",
        isActive ? "text-primary" : "text-muted-foreground"
      )}
      onClick={onClick}
    >
      <div className="relative group">
        <Icon className={cn("h-6 w-6 transition-all duration-300", isActive && "scale-110 drop-shadow-[0_0_8px_rgba(211,47,47,0.6)]")} />
        {badge > 0 && (
          <span className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white shadow-lg animate-pulse">
            {badge}
          </span>
        )}
      </div>
      <span className={cn("text-[10px] font-medium transition-colors", isActive ? "text-white" : "text-muted-foreground")}>{label}</span>
    </Button>
  )
}
