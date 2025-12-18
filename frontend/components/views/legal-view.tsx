"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ChevronRight, FileText, Scale, Shield, User, Info, AlertTriangle } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"

interface LegalViewProps {
  onBack: () => void
  initialTab?: 'offer' | 'rules' | 'privacy'
}

export function LegalView({ onBack, initialTab = 'offer' }: LegalViewProps) {
  const [activeTab, setActiveTab] = useState<'offer' | 'rules' | 'privacy'>(initialTab)

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-4 pb-2 flex-shrink-0">
        <Button variant="ghost" size="icon" onClick={onBack}>
          <ChevronRight className="h-5 w-5 rotate-180" />
        </Button>
        <h1 className="text-xl font-bold">Правовая информация</h1>
      </div>

      {/* Tabs */}
      <div className="flex px-4 gap-2 mb-4 overflow-x-auto pb-2 flex-shrink-0 scrollbar-hide">
        <TabButton 
          active={activeTab === 'offer'} 
          onClick={() => setActiveTab('offer')}
          label="Оферта"
        />
        <TabButton 
          active={activeTab === 'rules'} 
          onClick={() => setActiveTab('rules')}
          label="Правила"
        />
        <TabButton 
          active={activeTab === 'privacy'} 
          onClick={() => setActiveTab('privacy')}
          label="Конфиденциальность"
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 pb-24">
        {activeTab === 'offer' && <OfferContent />}
        {activeTab === 'rules' && <RulesContent />}
        {activeTab === 'privacy' && <PrivacyContent />}
      </div>
    </div>
  )
}

function TabButton({ active, onClick, label }: { active: boolean, onClick: () => void, label: string }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap",
        active 
          ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
          : "bg-white/5 text-muted-foreground hover:bg-white/10"
      )}
    >
      {label}
    </button>
  )
}

function Section({ title, children, icon: Icon }: { title: string, children: React.ReactNode, icon?: any }) {
  return (
    <div className="mb-6">
      <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-foreground">
        {Icon && <Icon className="h-5 w-5 text-primary" />}
        {title}
      </h3>
      <div className="space-y-3 text-sm text-muted-foreground leading-relaxed">
        {children}
      </div>
    </div>
  )
}

function OfferContent() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <Card className="bg-white/5 border-white/10 mb-6">
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">
            Публичная оферта на заключение договора оказания услуг площадки «RAM-US»
          </p>
        </CardContent>
      </Card>

      <Section title="1. Предмет оферты" icon={FileText}>
        <p>
          ИП Решетникова К.Е. (Оферент) публично предлагает любому Пользователю (Акцептант) заключить договор на оказание следующих услуг:
        </p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Размещение объявлений на условиях тарифа площадки</li>
          <li>Гарантийный сервис «Безопасная сделка»</li>
          <li>Продажа автозапчастей напрямую от юридического лица (физического лица)</li>
        </ul>
      </Section>

      <Section title="2. Существенные условия" icon={Scale}>
        <div className="space-y-4">
          <div className="bg-white/5 p-3 rounded-lg">
            <h4 className="font-semibold text-white mb-2">2.1. Услуга «Размещение объявлений»</h4>
            <ul className="list-disc list-inside space-y-1 ml-1">
              <li>Платные тарифы: продвижение, выделение, расширенные поля — оплачиваются отдельно.</li>
              <li>Оплата: СБП (физлица), счёт (юрлица). Допускается оплата третьим лицом.</li>
              <li>Услуга считается оказанной с момента публикации объявления.</li>
            </ul>
          </div>

          <div className="bg-white/5 p-3 rounded-lg">
            <h4 className="font-semibold text-white mb-2">2.2. Услуга «Безопасная сделка»</h4>
            <ul className="list-disc list-inside space-y-1 ml-1">
              <li>Комиссия: 5% от стоимости товара (минимум 100 руб.), оплачивает покупатель.</li>
              <li>Деньги удерживаются до подтверждения получения товара.</li>
              <li>Услуга оказана — с момента перевода средств продавцу или возврата покупателю.</li>
            </ul>
          </div>

          <div className="bg-white/5 p-3 rounded-lg">
            <h4 className="font-semibold text-white mb-2">2.3. Продажа от ИП</h4>
            <ul className="list-disc list-inside space-y-1 ml-1">
              <li>Товар передаётся после 100% оплаты.</li>
              <li>Возврат брака — при наличии акта от сервиса или заключения с актом о работах.</li>
              <li>Срок возврата/замены — 5 рабочих дней.</li>
            </ul>
          </div>
        </div>
      </Section>

      <Section title="3. Акцепт оферты" icon={User}>
        <p>Акцепт (принятие) осуществляется путём:</p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>регистрации на сайте + прохождения верификации;</li>
          <li>оплаты услуги или оформления заказа.</li>
        </ul>
      </Section>

      <Section title="4. Ответственность" icon={AlertTriangle}>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>За качество товаров, размещённых пользователями, отвечает сам продавец.</li>
          <li>За услуги площадки — ИП Решетникова К.Е.</li>
          <li>Ответственность по «Безопасной сделке» ограничена суммой удерживаемых средств.</li>
        </ul>
      </Section>

      <Section title="5. Срок действия" icon={Info}>
        <p>Оферта действует бессрочно до момента её отзыва (публикация на сайте за 10 дней).</p>
      </Section>

      <Card className="bg-primary/5 border-primary/20 mt-8">
        <CardContent className="p-4">
          <h4 className="font-bold text-white mb-2">Реквизиты Оферента</h4>
          <p className="text-xs text-muted-foreground font-mono">
            ИП Решетникова К.Е.<br/>
            ИНН 519090741487<br/>
            Адрес: 196158, г. Санкт-Петербург, пр. Юрия Гагарина, д. 1, офис 130.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

function RulesContent() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <Card className="bg-white/5 border-white/10 mb-6">
        <CardContent className="p-4">
          <h2 className="text-lg font-bold mb-1">ПРАВИЛА РАЗМЕЩЕНИЯ ОБЪЯВЛЕНИЙ</h2>
          <p className="text-xs text-muted-foreground">на площадке «RAM-US»</p>
        </CardContent>
      </Card>

      <Section title="1. Общие требования" icon={FileText}>
        <ul className="list-disc list-inside space-y-2 ml-1">
          <li>1.1. Размещать объявления могут только верифицированные пользователи.</li>
          <li>1.2. Объявления должны касаться автозапчастей, автокомпонентов и сопутствующих товаров, авто/мото техники/спец.техники.</li>
          <li>
            1.3. Запрещено размещение:
            <ul className="list-circle list-inside ml-4 mt-1 text-xs text-muted-foreground/80">
              <li>контрафактной, запрещённой или опасной продукции;</li>
              <li>товаров, не относящихся к тематике площадки;</li>
              <li>дублирующих объявлений.</li>
            </ul>
          </li>
        </ul>
      </Section>

      <Section title="2. Обязанности продавца" icon={User}>
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-white mb-1">2.1. Указать:</h4>
            <ul className="list-disc list-inside ml-2">
              <li>точное наименование товара;</li>
              <li>артикул, совместимость, состояние (новый/б/у);</li>
              <li>стоимость и условия доставки;</li>
              <li>для юрлиц/ИП — реквизиты и данные верификации.</li>
            </ul>
          </div>
          <div>
             <h4 className="font-semibold text-white mb-1">2.2. Не вводить в заблуждение:</h4>
             <p>Запрещены фото несуществующих товаров, завышенные характеристики, фейковые отзывы.</p>
          </div>
        </div>
      </Section>

      <Section title="3. Модерация" icon={Shield}>
        <ul className="list-disc list-inside space-y-1 ml-1">
          <li>3.1. Все объявления проходят предварительную или последующую модерацию.</li>
          <li>3.2. Администрация вправе отклонить, приостановить или удалить объявление без объяснения причин при нарушении Правил.</li>
        </ul>
      </Section>

      <Section title="4. Ответственность" icon={AlertTriangle}>
        <ul className="list-disc list-inside space-y-1 ml-1">
          <li>4.1. Продавец несёт полную ответственность за содержание объявления и качество товара.</li>
          <li>4.2. При выявлении мошенничества аккаунт блокируется навсегда, без права восстановления.</li>
        </ul>
      </Section>

      <Section title="5. Изменение Правил" icon={Info}>
        <p>Администратор может обновлять Правила. Новая редакция публикуется на сайте. Продолжение использования площадки = согласие.</p>
      </Section>
    </div>
  )
}

function PrivacyContent() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
        <Section title="1. Общие положения" icon={Shield}>
            <p>Мы, RAM US Auto Parts, серьезно относимся к конфиденциальности ваших данных. Мы собираем только ту информацию, которая необходима для оформления и доставки заказа.</p>
        </Section>

        <Section title="2. Какие данные мы собираем" icon={User}>
            <ul className="list-disc list-inside space-y-1 ml-1">
                <li>Имя пользователя Telegram</li>
                <li>Номер телефона (для связи по заказу)</li>
                <li>Адрес доставки</li>
            </ul>
        </Section>

        <Section title="3. Использование данных" icon={FileText}>
            <p>Ваши данные используются исключительно для:</p>
            <ul className="list-disc list-inside space-y-1 ml-1 mt-1">
                <li>Обработки заказов</li>
                <li>Связи с вами по статусу доставки</li>
                <li>Улучшения качества сервиса</li>
            </ul>
        </Section>

        <Section title="4. Безопасность" icon={Shield}>
            <p>Мы не передаем ваши данные третьим лицам, за исключением курьерских служб (СДЭК, Почта России) для выполнения доставки вашего заказа.</p>
        </Section>
    </div>
  )
}

