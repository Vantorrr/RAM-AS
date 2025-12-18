"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, X, MessageSquare, Loader2, Sparkles, User, Bot } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { API_URL } from "@/lib/config"
import { getTelegramUser } from "@/lib/telegram"

interface Message {
  role: "user" | "assistant"
  content: string
}

export function AIAssistant() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Привет! 👋 Я ИИ-помощник RAM US. Подскажу по запчастям, совместимости и наличию. Что ищем?" }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isOpen])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMsg = { role: "user" as const, content: input }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setIsLoading(true)

    try {
      const history = [...messages, userMsg].map(m => ({ role: m.role, content: m.content }))
      
      const tgUser = getTelegramUser()

      const res = await fetch(`${API_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          messages: history,
          user_info: tgUser ? {
            id: tgUser.id,
            username: tgUser.username,
            first_name: tgUser.first_name,
            last_name: tgUser.last_name
          } : undefined
        })
      })

      if (res.ok) {
        const data = await res.json()
        setMessages(prev => [...prev, { role: "assistant", content: data.content }])
      } else {
        setMessages(prev => [...prev, { role: "assistant", content: "Извините, я сейчас немного перегружен. Попробуйте позже или напишите менеджеру." }])
      }
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { role: "assistant", content: "Ошибка связи с сервером." }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      sendMessage()
    }
  }

  return (
    <>
      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-4 z-[60] w-[350px] max-w-[calc(100vw-32px)] shadow-2xl"
          >
            <Card className="bg-[#121212] border-primary/20 overflow-hidden flex flex-col h-[500px]">
              {/* Header */}
              <div className="bg-gradient-to-r from-primary/20 to-primary/5 p-4 flex items-center justify-between border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center border border-primary/30">
                    <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-white">RAM US AI</h3>
                    <p className="text-[10px] text-green-400 flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />
                      Online
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-white" onClick={() => setIsOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground rounded-br-none"
                          : "bg-white/10 text-white rounded-bl-none"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white/10 rounded-2xl rounded-bl-none px-4 py-3 flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">Печатает...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-3 bg-black/20 border-t border-white/10">
                <div className="relative">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Спросите про запчасть..."
                    className="pr-10 bg-white/5 border-white/10 focus-visible:ring-primary/50"
                  />
                  <Button
                    size="icon"
                    className="absolute right-1 top-1 h-8 w-8 bg-primary hover:bg-primary/90"
                    onClick={sendMessage}
                    disabled={isLoading || !input.trim()}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="fixed bottom-24 right-4 z-[50] h-14 w-14 rounded-full bg-gradient-to-tr from-primary to-orange-600 shadow-lg shadow-primary/20 flex items-center justify-center border-2 border-white/10"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? (
          <X className="h-7 w-7 text-white" />
        ) : (
          <div className="relative">
            <img src="/logo_new.png" alt="AI" className="h-8 w-8 object-contain drop-shadow-md" />
            <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-green-400 border border-black animate-pulse" />
          </div>
        )}
      </motion.button>
    </>
  )
}



