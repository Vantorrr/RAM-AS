"use client"

import { Home, Search, ShoppingCart, User, Tag } from "lucide-react"
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
    <div className="fixed bottom-0 left-0 z-50 w-full pb-safe">
      {/* glass / gradient base */}
      <div className="pointer-events-none absolute inset-0 border-t border-white/10 bg-gradient-to-t from-black/90 via-black/70 to-black/40 backdrop-blur-2xl supports-[backdrop-filter]:bg-black/55" />
      {/* top highlight line */}
      <div className="pointer-events-none absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />

      <div className="relative flex h-16 items-center justify-around px-1">
        <NavButton 
          icon={Home} 
          label="Главная" 
          isActive={activeTab === 'home'} 
          onClick={() => onTabChange('home')} 
        />
        <NavButton 
          icon={Search} 
          label="Поиск" 
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
        
        {/* Барахолка */}
        <NavButton 
          icon={Tag} 
          label="Барахолка" 
          isActive={activeTab === 'marketplace'} 
          onClick={() => onTabChange('marketplace')}
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

function NavButton({ icon: Icon, label, isActive, onClick, badge, className }: any) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn(
        "relative flex h-full flex-1 flex-col items-center justify-center gap-1 rounded-none active:scale-95 transition-all",
        "hover:bg-white/5",
        isActive ? "text-primary" : "text-muted-foreground",
        isActive && className ? className : "", 
        !isActive && className ? "text-purple-400/70" : ""
      )}
      onClick={onClick}
    >
      {/* active pill */}
      {isActive && (
        <span className="pointer-events-none absolute inset-x-2 top-1.5 bottom-1.5 rounded-2xl bg-white/5 ring-1 ring-white/10" />
      )}

      <div className="relative group">
        <Icon className={cn(
            "h-6 w-6 transition-all duration-300",
            isActive && "scale-110 drop-shadow-[0_0_10px_rgba(211,47,47,0.8)]",
            isActive && className?.includes("purple") && "drop-shadow-[0_0_8px_rgba(168,85,247,0.6)]"
        )} />
        {badge > 0 && (
          <span className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white shadow-lg animate-pulse">
            {badge}
          </span>
        )}
      </div>
      <span className={cn(
          "text-[10px] font-medium transition-colors", 
          isActive ? "text-white" : "text-muted-foreground",
          isActive && className?.includes("purple") && "text-purple-400"
      )}>{label}</span>
    </Button>
  )
}
