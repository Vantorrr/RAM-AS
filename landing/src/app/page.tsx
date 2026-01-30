"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { LINKS, SITE } from "@/lib/site"
import { 
  Bot, 
  ShoppingCart, 
  MessageCircle, 
  Check, 
  X, 
  Star, 
  ChevronDown, 
  Zap, 
  CreditCard, 
  Truck, 
  Clock, 
  Wrench, 
  Package, 
  LifeBuoy,
  Rocket,
  Megaphone
} from "lucide-react"

const REVIEWS = [
  { name: "Александр М.", car: "RAM 1500", text: "Заказал тормозные колодки, подобрали по VIN за 5 минут. Оплатил онлайн, приехало через неделю. Раньше на форумах сидел часами — тут всё чётко.", rating: 5 },
  { name: "Дмитрий К.", car: "Dodge Charger", text: "AI-бот реально работает! Написал артикул — сразу цена и наличие. Без звонков и 'перезвоним'. Рекомендую.", rating: 5 },
  { name: "Михаил В.", car: "Jeep Wrangler", text: "Брал подвеску под заказ. Честно сказали 4-6 недель, пришло за 5. Упаковано идеально. Буду заказывать ещё.", rating: 5 },
  { name: "Сергей П.", car: "RAM 2500", text: "Наконец-то адекватный сервис для американцев! Не надо объяснять что за машина — сами разбираются.", rating: 5 },
  { name: "Андрей Л.", car: "Chrysler 300", text: "Оплата картой прямо в боте — это топ. Не люблю переводы на карту 'Ивану И.'", rating: 5 },
  { name: "Владимир Т.", car: "Dodge RAM", text: "Тюнинг заказывал — крышку кузова. Качество огонь, цена адекватная. Ребята знают своё дело.", rating: 5 },
  { name: "Николай Ф.", car: "Jeep Grand Cherokee", text: "Подбор по VIN — это спасение. Ошибся в артикуле раньше, деньги потерял. Тут такого не будет.", rating: 5 },
  { name: "Павел Р.", car: "RAM 1500 TRX", text: "Скорость ответа бота — секунды. В других местах сутками жду 'менеджер уточнит'.", rating: 5 },
  { name: "Евгений С.", car: "Dodge Durango", text: "Заказываю регулярно. Всё приходит, всё подходит. Проблем не было ни разу за год.", rating: 5 },
  { name: "Игорь Б.", car: "Jeep Gladiator", text: "Редкая запчасть была нужна — нашли и привезли. Другие говорили 'невозможно'. Эти — сделали.", rating: 5 },
]

export default function Home() {
  const [showSplash, setShowSplash] = useState(true)
  const [expandedReview, setExpandedReview] = useState<number | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 2500)
    return () => clearTimeout(timer)
  }, [])

  return (
    <>
      {/* SPLASH SCREEN */}
      {showSplash && (
        <div className="splash-overlay">
          <div className="flex flex-col items-center gap-8 splash-logo-container">
            {/* Glow effect */}
            <div className="splash-glow" />
            
            {/* Logo */}
            <div className="relative z-10 animate-scale-in">
              <Image 
                src="/logo-nobg.png" 
                alt="RAM-US Logo" 
                width={220} 
                height={220} 
                className="object-contain drop-shadow-[0_0_30px_rgba(214,45,45,0.6)]"
                priority
              />
            </div>

            {/* Text */}
            <div className="text-center z-10 animate-fade-in-up delay-200">
              <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight drop-shadow-lg">RAM-US</h1>
              <p className="text-sm md:text-base text-white/80 mt-2 font-medium tracking-wide uppercase">Запчасти для американцев</p>
            </div>

            {/* Progress Bar */}
            <div className="splash-progress">
              <div className="splash-progress-bar" />
            </div>
          </div>
        </div>
      )}

      <div className={`min-h-screen ${showSplash ? 'opacity-0' : 'opacity-100 transition-opacity duration-500'}`}>
        {/* HEADER */}
        <header className="fixed top-0 left-0 right-0 z-50 glass-strong">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:py-4">
            <div className="flex items-center gap-3 animate-fade-in">
              <div className="relative h-10 w-10 md:h-12 md:w-12 flex items-center justify-center">
                <Image 
                  src="/logo-nobg.png" 
                  alt="RAM-US Logo" 
                  fill
                  className="object-contain"
                />
              </div>
              <div className="leading-tight">
                <div className="text-base md:text-lg font-black text-white">{SITE.name}</div>
                <div className="text-[10px] md:text-xs text-white/50 hidden sm:block">Запчасти • Тюнинг • Доставка</div>
              </div>
            </div>

            <nav className="hidden lg:flex items-center gap-8 text-sm text-white/70">
              <a href="#ai" className="hover:text-white transition-colors">AI-подбор</a>
              <a href="#why" className="hover:text-white transition-colors">Преимущества</a>
              <a href="#how" className="hover:text-white transition-colors">Как заказать</a>
              <a href="#reviews" className="hover:text-white transition-colors">Отзывы</a>
            </nav>

            <div className="flex items-center gap-2 md:gap-3">
              <a
                href={LINKS.telegramChannel}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden md:inline-flex btn-secondary rounded-xl px-4 py-2.5 text-sm font-semibold text-white items-center gap-2"
              >
                <Megaphone className="h-4 w-4" />
                Канал
              </a>
              <a
                href={LINKS.telegramBot}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary rounded-xl px-4 md:px-6 py-2.5 text-sm font-black text-white animate-pulse-glow flex items-center gap-2"
              >
                <Bot className="h-4 w-4" />
                Открыть бота
              </a>
            </div>
          </div>
        </header>

        <main>
          {/* HERO */}
          <section className="relative min-h-screen flex items-center bg-hero-gradient pt-20 overflow-hidden">
            {/* Background effects */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute top-1/4 left-1/4 h-96 w-96 bg-[var(--accent)]/20 rounded-full blur-[120px] animate-float" />
              <div className="absolute bottom-1/4 right-1/4 h-80 w-80 bg-white/5 rounded-full blur-[100px] animate-float delay-500" />
            </div>

            <div className="relative mx-auto max-w-7xl px-4 py-12 md:py-20">
              <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
                {/* Left - Text */}
                <div className="text-center lg:text-left">
                  <div className="inline-flex items-center gap-2 rounded-full glass px-4 py-2 text-xs md:text-sm font-semibold text-white/80 animate-fade-in-up">
                    <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    Работаем 24/7 • AI на связи
                  </div>
                  
                  <h1 className="mt-6 md:mt-8 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black leading-[1.05] tracking-tight animate-fade-in-up delay-100">
                    <span className="text-gradient">Запчасти для</span>
                    <br />
                    <span className="text-gradient-red">американцев</span>
                    <br />
                    <span className="text-gradient">за секунды</span>
                  </h1>
                  
                  <p className="mt-6 md:mt-8 text-base md:text-xl text-white/70 max-w-xl mx-auto lg:mx-0 animate-fade-in-up delay-200">
                    RAM • Dodge • Jeep • Chrysler
                    <br />
                    <span className="text-white font-semibold">AI-подбор по VIN</span> — никаких звонков и ожидания.
                    <br />
                    Оплата онлайн. Доставка по России.
                  </p>

                  <div className="mt-8 md:mt-10 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start animate-fade-in-up delay-300">
                    <a
                      href={LINKS.telegramCatalog}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-primary inline-flex h-14 md:h-16 items-center justify-center rounded-2xl px-8 text-base md:text-lg font-black text-white gap-2"
                    >
                      <ShoppingCart className="h-5 w-5" />
                      Открыть каталог
                    </a>
                    <a
                      href={LINKS.telegramBot}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary inline-flex h-14 md:h-16 items-center justify-center rounded-2xl px-8 text-base md:text-lg font-semibold text-white gap-2"
                    >
                      <MessageCircle className="h-5 w-5" />
                      Написать в бота
                    </a>
                  </div>

                  {/* Stats */}
                  <div className="mt-10 md:mt-14 grid grid-cols-3 gap-4 max-w-lg mx-auto lg:mx-0 animate-fade-in-up delay-400">
                    {[
                      { value: "13K+", label: "Запчастей" },
                      { value: "24/7", label: "AI на связи" },
                      { value: "4-6", label: "Недель под заказ" },
                    ].map((stat) => (
                      <div key={stat.label} className="glass rounded-2xl p-4 text-center card-hover">
                        <div className="text-2xl md:text-3xl font-black text-white">{stat.value}</div>
                        <div className="text-xs md:text-sm text-white/60 mt-1">{stat.label}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right - Phone mockup */}
                <div className="relative animate-slide-in-right delay-200">
                  <div className="absolute inset-0 bg-[var(--accent)]/30 blur-[100px] rounded-full scale-75" />
                  <div className="relative mx-auto w-full max-w-sm">
                    {/* Phone frame */}
                    <div className="glass rounded-[3rem] p-3 md:p-4 glow-red animate-float">
                      <div className="bg-black rounded-[2.5rem] p-4 md:p-6 min-h-[500px] md:min-h-[600px]">
                        {/* Phone header */}
                        <div className="flex items-center justify-between mb-6">
                          <div className="flex items-center gap-2">
                            <div className="relative h-8 w-8 flex items-center justify-center">
                              <Image 
                                src="/logo-nobg.png" 
                                alt="Logo" 
                                fill
                                className="object-contain"
                              />
                            </div>
                            <div>
                              <div className="text-sm font-bold text-white">RAM-US Bot</div>
                              <div className="text-[10px] text-green-400">● онлайн</div>
                            </div>
                          </div>
                        </div>

                        {/* Chat messages */}
                        <div className="space-y-4">
                          <div className="glass rounded-2xl rounded-tl-sm p-4 max-w-[85%] animate-fade-in-up delay-500">
                            <p className="text-sm text-white">Привет! 👋 Я AI-помощник RAM-US. Найду любую запчасть за секунды.</p>
                            <p className="text-sm text-white mt-2">Напиши <span className="text-[var(--accent)] font-bold">VIN</span> или <span className="text-[var(--accent)] font-bold">название детали</span>.</p>
                          </div>

                          <div className="glass rounded-2xl rounded-tr-sm p-4 max-w-[85%] ml-auto bg-[var(--accent)]/20 animate-fade-in-up delay-600">
                            <p className="text-sm text-white">Колодки тормозные RAM 1500 2022</p>
                          </div>

                          <div className="glass rounded-2xl rounded-tl-sm p-4 max-w-[85%] animate-fade-in-up delay-700">
                            <p className="text-sm text-white">✅ Нашёл! 3 варианта:</p>
                            <div className="mt-3 space-y-2 text-xs">
                              <div className="bg-white/5 rounded-xl p-3">
                                <div className="text-white font-semibold">Mopar Original</div>
                                <div className="text-[var(--accent)] font-bold">12,500 ₽ • В наличии</div>
                              </div>
                              <div className="bg-white/5 rounded-xl p-3">
                                <div className="text-white font-semibold">Brembo Performance</div>
                                <div className="text-[var(--accent)] font-bold">18,900 ₽ • В наличии</div>
                              </div>
                            </div>
                            <p className="text-sm text-white mt-3">Какой оформляем? 🚀</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Scroll indicator */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
              <div className="h-14 w-8 rounded-full border-2 border-white/20 flex items-start justify-center p-2">
                <div className="h-3 w-1 rounded-full bg-white/50 animate-pulse" />
              </div>
            </div>
          </section>

          {/* AI SECTION */}
          <section id="ai" className="py-20 md:py-32 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[var(--accent)]/5 to-transparent" />
            
            <div className="relative mx-auto max-w-7xl px-4">
              <div className="text-center mb-16">
                <div className="inline-flex items-center gap-2 rounded-full glass px-4 py-2 text-sm font-semibold text-[var(--accent)] mb-6">
                  <Bot className="h-4 w-4" />
                  🤖 Технология
                </div>
                <h2 className="text-3xl md:text-5xl font-black text-white">
                  AI-подбор за <span className="text-gradient-red">секунды</span>
                </h2>
                <p className="mt-4 text-lg text-white/60 max-w-2xl mx-auto">
                  Забудь про часы в чатах с менеджерами. Наш AI работает мгновенно — 24/7.
                </p>
              </div>

              {/* Comparison */}
              <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
                {/* Old way */}
                <div className="glass rounded-3xl p-6 md:p-8 border-red-500/20 relative overflow-hidden">
                  <div className="absolute top-4 right-4 text-4xl opacity-20">❌</div>
                  <h3 className="text-xl font-bold text-red-400 mb-6">Как было раньше</h3>
                  <ul className="space-y-4 text-white/70">
                    <li className="flex items-start gap-3">
                      <X className="h-5 w-5 text-red-400 mt-0.5" />
                      <span>Ищешь на форумах часами</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <X className="h-5 w-5 text-red-400 mt-0.5" />
                      <span>Звонишь — "перезвоним через час"</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <X className="h-5 w-5 text-red-400 mt-0.5" />
                      <span>Ошибся в артикуле — деньги потерял</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <X className="h-5 w-5 text-red-400 mt-0.5" />
                      <span>Переводы на карту "Ивану И."</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <X className="h-5 w-5 text-red-400 mt-0.5" />
                      <span>Неизвестные сроки доставки</span>
                    </li>
                  </ul>
                </div>

                {/* New way */}
                <div className="glass rounded-3xl p-6 md:p-8 border-green-500/20 relative overflow-hidden glow-red">
                  <div className="absolute top-4 right-4 text-4xl opacity-20">✅</div>
                  <h3 className="text-xl font-bold text-green-400 mb-6">Как с RAM-US</h3>
                  <ul className="space-y-4 text-white">
                    <li className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-green-400 mt-0.5" />
                      <span className="font-semibold">AI находит за 10 секунд</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-green-400 mt-0.5" />
                      <span className="font-semibold">Ответ мгновенно, 24/7</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-green-400 mt-0.5" />
                      <span className="font-semibold">Подбор по VIN — без ошибок</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-green-400 mt-0.5" />
                      <span className="font-semibold">Оплата онлайн безопасно</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-green-400 mt-0.5" />
                      <span className="font-semibold">Честные сроки сразу</span>
                    </li>
                  </ul>
                </div>
              </div>

              <div className="mt-12 text-center">
                <a
                  href={LINKS.telegramBot}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary inline-flex h-16 items-center justify-center rounded-2xl px-10 text-lg font-black text-white gap-2"
                >
                  <Bot className="h-6 w-6" />
                  Попробовать AI-подбор
                </a>
              </div>
            </div>
          </section>

          {/* WHY SECTION */}
          <section id="why" className="py-20 md:py-32">
            <div className="mx-auto max-w-7xl px-4">
              <div className="text-center mb-16">
                <h2 className="text-3xl md:text-5xl font-black text-white">
                  Почему <span className="text-gradient-red">RAM-US</span>
                </h2>
                <p className="mt-4 text-lg text-white/60">
                  Мы не продаём "как получится". Мы закрываем задачу.
                </p>
              </div>

              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { icon: <Zap className="h-8 w-8 text-[var(--accent)]" />, title: "Подбор по VIN", desc: "Точная позиция под вашу комплектацию. Без ошибок." },
                  { icon: <Bot className="h-8 w-8 text-[var(--accent)]" />, title: "AI 24/7", desc: "Ответ за секунды в любое время. Без менеджеров." },
                  { icon: <CreditCard className="h-8 w-8 text-[var(--accent)]" />, title: "Оплата онлайн", desc: "Безопасно картой. Никаких переводов на карту." },
                  { icon: <Truck className="h-8 w-8 text-[var(--accent)]" />, title: "Доставка по РФ", desc: "Отправка по всей России. Отслеживание." },
                  { icon: <Clock className="h-8 w-8 text-[var(--accent)]" />, title: "Честные сроки", desc: "Под заказ — 4-6 недель. Говорим как есть." },
                  { icon: <Wrench className="h-8 w-8 text-[var(--accent)]" />, title: "Тюнинг", desc: "Крышки, обвесы, аксессуары. Всё для вашего авто." },
                  { icon: <Package className="h-8 w-8 text-[var(--accent)]" />, title: "Упаковка", desc: "Проверка и надёжная упаковка перед отправкой." },
                  { icon: <LifeBuoy className="h-8 w-8 text-[var(--accent)]" />, title: "Поддержка", desc: "Если что-то не так — решаем. Без отговорок." },
                ].map((item, i) => (
                  <div
                    key={item.title}
                    className={`glass rounded-3xl p-6 card-hover animate-fade-in-up`}
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <div className="mb-4">{item.icon}</div>
                    <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                    <p className="text-sm text-white/60">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* HOW IT WORKS */}
          <section id="how" className="py-20 md:py-32 bg-gradient-to-b from-transparent via-white/[0.02] to-transparent">
            <div className="mx-auto max-w-7xl px-4">
              <div className="text-center mb-16">
                <h2 className="text-3xl md:text-5xl font-black text-white">
                  Как это <span className="text-gradient-red">работает</span>
                </h2>
                <p className="mt-4 text-lg text-white/60">
                  3 шага — и запчасть едет к вам
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                {[
                  { step: "01", title: "Открываешь бота", desc: "Пишешь VIN или название детали. AI находит варианты за секунды." },
                  { step: "02", title: "Выбираешь и оплачиваешь", desc: "Добавляешь в корзину, вводишь адрес, оплачиваешь онлайн." },
                  { step: "03", title: "Получаешь", desc: "Отправляем по России. Отслеживание в боте. Готово!" },
                ].map((item, i) => (
                  <div key={item.step} className="relative">
                    {i < 2 && (
                      <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-[var(--accent)] to-transparent" />
                    )}
                    <div className="glass rounded-3xl p-8 text-center card-hover h-full">
                      <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--accent)]/20 text-2xl font-black text-[var(--accent)] mb-6">
                        {item.step}
                      </div>
                      <h3 className="text-xl font-bold text-white mb-3">{item.title}</h3>
                      <p className="text-white/60">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-16 text-center">
                <a
                  href={LINKS.telegramCatalog}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary inline-flex h-16 items-center justify-center rounded-2xl px-10 text-lg font-black text-white gap-2"
                >
                  <ShoppingCart className="h-6 w-6" />
                  Перейти в каталог
                </a>
              </div>
            </div>
          </section>

          {/* REVIEWS */}
          <section id="reviews" className="py-20 md:py-32">
            <div className="mx-auto max-w-7xl px-4">
              <div className="text-center mb-16">
                <h2 className="text-3xl md:text-5xl font-black text-white">
                  Отзывы <span className="text-gradient-red">клиентов</span>
                </h2>
                <p className="mt-4 text-lg text-white/60">
                  Реальные люди, реальные заказы
                </p>
              </div>

              <div className="max-w-3xl mx-auto space-y-4">
                {REVIEWS.map((review, i) => (
                  <div
                    key={i}
                    className="glass rounded-2xl overflow-hidden card-hover cursor-pointer"
                    onClick={() => setExpandedReview(expandedReview === i ? null : i)}
                  >
                    <div className="p-5 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-[var(--accent)] to-red-800 flex items-center justify-center text-white font-bold">
                          {review.name.charAt(0)}
                        </div>
                        <div>
                          <div className="font-bold text-white">{review.name}</div>
                          <div className="text-sm text-white/50">{review.car}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex text-yellow-400 text-sm">
                          {[...Array(review.rating)].map((_, i) => (
                            <Star key={i} className="h-4 w-4 fill-current" />
                          ))}
                        </div>
                        <div className={`transition-transform duration-300 ${expandedReview === i ? 'rotate-180' : ''}`}>
                          <ChevronDown className="h-5 w-5 text-white/50" />
                        </div>
                      </div>
                    </div>
                    <div className={`overflow-hidden transition-all duration-300 ${expandedReview === i ? 'max-h-40 pb-5' : 'max-h-0'}`}>
                      <div className="px-5">
                        <p className="text-white/80 leading-relaxed">{review.text}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* FINAL CTA */}
          <section className="py-20 md:py-32 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-[var(--accent)]/10 via-[var(--accent)]/5 to-transparent" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] bg-[var(--accent)]/20 rounded-full blur-[150px]" />
            
            <div className="relative mx-auto max-w-4xl px-4 text-center">
              <div className="glass rounded-[3rem] p-8 md:p-16 glow-red">
                <h2 className="text-3xl md:text-5xl font-black text-white leading-tight">
                  Готов заказать
                  <br />
                  <span className="text-gradient-red">запчасть?</span>
                </h2>
                <p className="mt-6 text-lg md:text-xl text-white/70 max-w-xl mx-auto">
                  Открой бота, напиши VIN или название детали — AI найдёт за секунды.
                  Оплата онлайн, доставка по России.
                </p>

                <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
                  <a
                    href={LINKS.telegramBot}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary inline-flex h-16 items-center justify-center rounded-2xl px-10 text-lg font-black text-white gap-2"
                  >
                    <Rocket className="h-6 w-6" />
                    Открыть бота
                  </a>
                  <a
                    href={LINKS.telegramChannel}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary inline-flex h-16 items-center justify-center rounded-2xl px-10 text-lg font-semibold text-white gap-2"
                  >
                    <Megaphone className="h-6 w-6" />
                    Подписаться на канал
                  </a>
                </div>

                <p className="mt-8 text-sm text-white/40">
                  Бот работает 24/7 • Ответ за секунды • Оплата онлайн
                </p>
              </div>
            </div>
          </section>
        </main>

        {/* FOOTER */}
        <footer className="border-t border-white/10 bg-black/40">
          <div className="mx-auto max-w-7xl px-4 py-12">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-3">
                <div className="relative h-10 w-10 flex items-center justify-center">
                  <Image 
                    src="/logo-nobg.png" 
                    alt="Logo" 
                    fill
                    className="object-contain"
                  />
                </div>
                <div>
                  <div className="font-bold text-white">{SITE.name}</div>
                  <div className="text-xs text-white/50">{SITE.tagline}</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-3 justify-center">
                <a
                  href={LINKS.telegramChannel}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary rounded-xl px-4 py-2.5 text-sm font-semibold text-white flex items-center gap-2"
                >
                  <Megaphone className="h-4 w-4" />
                  Канал
                </a>
                <a
                  href={LINKS.telegramCatalog}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary rounded-xl px-4 py-2.5 text-sm font-semibold text-white flex items-center gap-2"
                >
                  <ShoppingCart className="h-4 w-4" />
                  Каталог
                </a>
                <a
                  href={LINKS.telegramBot}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary rounded-xl px-4 py-2.5 text-sm font-black text-white flex items-center gap-2"
                >
                  <Bot className="h-4 w-4" />
                  Бот
                </a>
              </div>
            </div>

            <div className="mt-8 pt-8 border-t border-white/10 text-center text-sm text-white/40">
              © {new Date().getFullYear()} {SITE.name}. Все права защищены.
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}