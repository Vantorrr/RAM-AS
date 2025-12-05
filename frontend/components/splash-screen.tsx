"use client"

import { useEffect } from "react"
import { motion } from "framer-motion"
import Image from "next/image"
import { hapticFeedback } from "@/lib/telegram"

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  useEffect(() => {
    // Мощная начальная вибрация
    hapticFeedback('heavy')
    
    // Средняя вибрация каждые 500мс (чаще и сильнее)
    const vibrationInterval = setInterval(() => {
      hapticFeedback('medium')
    }, 500)
    
    // Завершение
    const timer = setTimeout(() => {
      clearInterval(vibrationInterval)
      // Двойная финальная вибрация
      hapticFeedback('heavy')
      setTimeout(() => hapticFeedback('success'), 100)
      onComplete()
    }, 3000)
    
    return () => {
      clearTimeout(timer)
      clearInterval(vibrationInterval)
    }
  }, [onComplete])

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0a0a0a]">
      <div className="relative flex flex-col items-center">
        {/* Animated Rings */}
        <motion.div
          className="absolute h-80 w-80 rounded-full border-4 border-ram-red/30"
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute h-72 w-72 rounded-full border-4 border-ram-silver/20"
          animate={{ scale: [1.1, 0.9, 1.1], rotate: [0, 180, 360] }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />
        
        {/* Logo Image */}
        <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="relative h-64 w-64 z-10"
        >
            <Image 
                src="/logo_new.png"
                alt="RAM US Logo"
                fill
                className="object-contain"
                priority
            />
        </motion.div>
        
         {/* Loading Bar */}
         <motion.div 
            className="mt-12 h-1 w-32 overflow-hidden rounded-full bg-secondary"
         >
             <motion.div
                className="h-full bg-primary"
                initial={{ width: "0%" }}
                animate={{ width: "100%" }}
                transition={{ duration: 2.5, ease: "easeInOut" }}
             />
         </motion.div>
      </div>
    </div>
  )
}
