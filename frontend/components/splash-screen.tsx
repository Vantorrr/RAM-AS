"use client"

import { useEffect } from "react"
import { motion } from "framer-motion"
import Image from "next/image"

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete()
    }, 3000) // 3 seconds splash
    return () => clearTimeout(timer)
  }, [onComplete])

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#0a0a0a]">
      <div className="relative flex flex-col items-center">
        {/* Animated Rings */}
        <motion.div
          className="absolute h-64 w-64 rounded-full border-4 border-ram-red/30"
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute h-56 w-56 rounded-full border-4 border-ram-silver/20"
          animate={{ scale: [1.1, 0.9, 1.1], rotate: [0, 180, 360] }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />
        
        {/* Logo Image */}
        <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="relative h-48 w-48 z-10"
        >
            <Image 
                src="/logo_new.png"
                alt="RAM US Logo"
                fill
                className="object-contain"
                priority
            />
        </motion.div>
        
        <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="mt-4 text-sm text-ram-silver uppercase tracking-widest font-bold"
        >
            Auto Parts Store
        </motion.p>

         {/* Loading Bar */}
         <motion.div 
            className="mt-8 h-1 w-32 overflow-hidden rounded-full bg-secondary"
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
