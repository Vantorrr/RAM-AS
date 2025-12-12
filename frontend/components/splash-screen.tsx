"use client"

import { useEffect } from "react"
import { motion } from "framer-motion"
import Image from "next/image"
import { hapticFeedback } from "@/lib/telegram"

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  useEffect(() => {
    // Звук (THX Deep Note style)
    const audio = new Audio('/sounds/engine_start.mp3')
    audio.volume = 0.8
    audio.play().catch(e => console.log("Audio autoplay prevented:", e))

    // Начальный удар
    hapticFeedback('heavy')
    
    // Нарастающая вибрация (гул)
    const vibrationInterval = setInterval(() => {
      hapticFeedback('light')
    }, 150)
    
    // Завершение (даем звуку раскрыться)
    const timer = setTimeout(() => {
      clearInterval(vibrationInterval)
      // Финальный аккорд
      hapticFeedback('heavy')
      setTimeout(() => hapticFeedback('heavy'), 150)
      setTimeout(() => hapticFeedback('success'), 400)
      onComplete()
    }, 4500)
    
    return () => {
      clearTimeout(timer)
      clearInterval(vibrationInterval)
      audio.pause()
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

            {/* Glowing Eyes Animation */}
            {/* Left Eye */}
            <motion.div
                className="absolute top-[42%] left-[29%] w-10 h-10 bg-red-600 rounded-full blur-xl mix-blend-screen"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ 
                    opacity: [0, 0, 0.8, 0.4, 0.9],
                    scale: [0.5, 0.5, 1.2, 1, 1.1] 
                }}
                transition={{ 
                    delay: 0.8, 
                    duration: 2.5, 
                    times: [0, 0.1, 0.2, 0.5, 1],
                    repeat: Infinity,
                    repeatType: "reverse"
                }}
            />
            <motion.div
                className="absolute top-[45%] left-[32%] w-3 h-3 bg-orange-500 rounded-full blur-[4px]"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0, 1, 0.6, 1] }}
                transition={{ delay: 0.8, duration: 2.5, repeat: Infinity, repeatType: "reverse" }}
            />
            <motion.div
                className="absolute top-[46%] left-[33%] w-1 h-1 bg-white rounded-full blur-[1px]"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0, 1, 0.8, 1] }}
                transition={{ delay: 0.8, duration: 2.5, repeat: Infinity, repeatType: "reverse" }}
            />

            {/* Right Eye */}
            <motion.div
                className="absolute top-[42%] right-[29%] w-10 h-10 bg-red-600 rounded-full blur-xl mix-blend-screen"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ 
                    opacity: [0, 0, 0.8, 0.4, 0.9],
                    scale: [0.5, 0.5, 1.2, 1, 1.1] 
                }}
                transition={{ 
                    delay: 0.8, 
                    duration: 2.5, 
                    times: [0, 0.1, 0.2, 0.5, 1],
                    repeat: Infinity,
                    repeatType: "reverse"
                }}
            />
             <motion.div
                className="absolute top-[45%] right-[32%] w-3 h-3 bg-orange-500 rounded-full blur-[4px]"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0, 1, 0.6, 1] }}
                transition={{ delay: 0.8, duration: 2.5, repeat: Infinity, repeatType: "reverse" }}
            />
            <motion.div
                className="absolute top-[46%] right-[33%] w-1 h-1 bg-white rounded-full blur-[1px]"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0, 1, 0.8, 1] }}
                transition={{ delay: 0.8, duration: 2.5, repeat: Infinity, repeatType: "reverse" }}
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
                transition={{ duration: 4.5, ease: "easeInOut" }}
             />
         </motion.div>
      </div>
    </div>
  )
}
