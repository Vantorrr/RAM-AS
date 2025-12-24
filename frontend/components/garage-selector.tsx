"use client"

import { useState, useEffect } from "react"
import { Car, ChevronDown, Check, X, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { API_URL } from "@/lib/config"
import { useGarageStore } from "@/lib/garage-store"

interface VehicleConfig {
  make: string
  models: {
    name: string
    years: number[]
    engines: string[]
    generations: string[]
  }[]
}

export function GarageSelector() {
  const [isOpen, setIsOpen] = useState(false)
  const [config, setConfig] = useState<VehicleConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [manualMode, setManualMode] = useState(false)
  
  const { selectedVehicle, setVehicle, clearVehicle } = useGarageStore()
  
  // Selection state
  const [make, setMake] = useState<string>("")
  const [model, setModel] = useState<string>("")
  const [year, setYear] = useState<string>("")
  const [engine, setEngine] = useState<string>("")
  
  // Load config on open
  useEffect(() => {
    if (isOpen && config.length === 0) {
      setLoading(true)
      fetch(`${API_URL}/vehicles/config`)
        .then(res => res.json())
        .then(data => setConfig(data))
        .catch(err => console.error(err))
        .finally(() => setLoading(false))
    }
  }, [isOpen])
  
  // Initialize from store
  useEffect(() => {
    if (selectedVehicle) {
        setMake(selectedVehicle.make)
        setModel(selectedVehicle.model)
        setYear(selectedVehicle.year.toString())
        setEngine(selectedVehicle.engine)
    }
  }, [selectedVehicle, isOpen])

  const handleSave = () => {
    if (make && model && year && engine) {
      setVehicle({
        make,
        model,
        year: parseInt(year),
        engine
      })
      setIsOpen(false)
    }
  }
  
  const handleClear = () => {
    clearVehicle()
    setMake("")
    setModel("")
    setYear("")
    setEngine("")
    setManualMode(false)
    setIsOpen(false)
  }
  
  const toggleMode = () => {
    setManualMode(!manualMode)
    setMake("")
    setModel("")
    setYear("")
    setEngine("")
  }

  // Derived options
  const selectedMakeData = config.find(c => c.make === make)
  const selectedModelData = selectedMakeData?.models.find(m => m.name === model)
  const availableModels = selectedMakeData?.models || []
  const availableYears = selectedModelData?.years || []
  const availableEngines = selectedModelData?.engines || []

  return (
    <>
      {/* Widget Trigger */}
      <div className="px-4 pb-2">
        <Button 
            variant="outline" 
            className={`w-full justify-between border-white/10 ${selectedVehicle ? 'bg-primary/10 border-primary/30' : 'bg-white/5'}`}
            onClick={() => setIsOpen(true)}
        >
          <div className="flex items-center gap-2 overflow-hidden">
            <Car className={`h-4 w-4 ${selectedVehicle ? 'text-primary' : 'text-muted-foreground'}`} />
            {selectedVehicle ? (
              <span className="font-medium truncate text-sm">
                {selectedVehicle.make} {selectedVehicle.model} {selectedVehicle.year}
              </span>
            ) : (
              <span className="text-muted-foreground text-sm">Выбрать автомобиль</span>
            )}
          </div>
          {selectedVehicle ? (
             <Check className="h-4 w-4 text-primary shrink-0" />
          ) : (
             <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0 opacity-50" />
          )}
        </Button>
        {selectedVehicle && (
            <p className="text-[10px] text-primary/70 mt-1 pl-1">
                ✅ Показываем запчасти только для вашего авто
            </p>
        )}
      </div>

      {/* Drawer */}
      <Drawer open={isOpen} onOpenChange={setIsOpen}>
        <DrawerContent className="bg-zinc-900 border-t border-white/10 max-h-[90vh]">
          <DrawerHeader>
            <DrawerTitle className="flex items-center gap-2">
                <Car className="h-5 w-5 text-primary" />
                Гараж
            </DrawerTitle>
          </DrawerHeader>
          
          <div className="p-4 space-y-4">
            {/* Toggle button */}
            <Button 
                variant="outline" 
                size="sm" 
                onClick={toggleMode}
                className="w-full"
            >
                {manualMode ? "📋 Выбрать из списка" : "✍️ Ввести свою машину"}
            </Button>
            
            {manualMode ? (
                /* Manual input mode */
                <>
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Марка *</label>
                        <Input
                            placeholder="Lada, Toyota, BMW..."
                            value={make}
                            onChange={e => setMake(e.target.value)}
                            className="bg-white/5 border-white/10"
                        />
                    </div>
                    
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Модель *</label>
                        <Input
                            placeholder="Granta, Camry, X5..."
                            value={model}
                            onChange={e => setModel(e.target.value)}
                            className="bg-white/5 border-white/10"
                        />
                    </div>
                    
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Год выпуска *</label>
                        <Input
                            type="number"
                            placeholder="2020"
                            value={year}
                            onChange={e => setYear(e.target.value)}
                            className="bg-white/5 border-white/10"
                        />
                    </div>
                    
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Двигатель *</label>
                        <Input
                            placeholder="1.6L 16V, 2.0L Turbo..."
                            value={engine}
                            onChange={e => setEngine(e.target.value)}
                            className="bg-white/5 border-white/10"
                        />
                    </div>
                </>
            ) : loading ? (
                <div className="text-center py-8 text-muted-foreground">Загрузка базы авто...</div>
            ) : config.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                    <p className="mb-2">База авто пуста</p>
                    <Button size="sm" variant="outline" onClick={toggleMode}>
                        Ввести вручную
                    </Button>
                </div>
            ) : (
                /* Select mode */
                <>
                    {/* Make */}
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Марка</label>
                        <Select value={make} onValueChange={(v) => { setMake(v); setModel(""); setYear(""); setEngine("") }}>
                            <SelectTrigger className="bg-white/5 border-white/10">
                                <SelectValue placeholder="Выберите марку" />
                            </SelectTrigger>
                            <SelectContent>
                                {config.map(c => (
                                    <SelectItem key={c.make} value={c.make}>{c.make}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Model */}
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Модель</label>
                        <Select value={model} onValueChange={(v) => { setModel(v); setYear(""); setEngine("") }} disabled={!make}>
                            <SelectTrigger className="bg-white/5 border-white/10">
                                <SelectValue placeholder="Выберите модель" />
                            </SelectTrigger>
                            <SelectContent>
                                {availableModels.map(m => (
                                    <SelectItem key={m.name} value={m.name}>{m.name}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Year */}
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Год выпуска</label>
                        <Select value={year} onValueChange={(v) => { setYear(v); }} disabled={!model}>
                            <SelectTrigger className="bg-white/5 border-white/10">
                                <SelectValue placeholder="Выберите год" />
                            </SelectTrigger>
                            <SelectContent>
                                {availableYears.map(y => (
                                    <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Engine */}
                    <div className="space-y-1">
                        <label className="text-xs text-muted-foreground ml-1">Двигатель</label>
                        <Select value={engine} onValueChange={setEngine} disabled={!model}>
                            <SelectTrigger className="bg-white/5 border-white/10">
                                <SelectValue placeholder="Выберите двигатель" />
                            </SelectTrigger>
                            <SelectContent>
                                {availableEngines.map(e => (
                                    <SelectItem key={e} value={e}>{e}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </>
            )}
            
            {/* Info */}
            <Card className="bg-blue-500/10 border-blue-500/20">
                <CardContent className="p-3 text-xs text-blue-300">
                    {manualMode 
                        ? "Введите данные вашего автомобиля, и мы подберём подходящие запчасти."
                        : `Мы отфильтруем каталог и покажем только те детали, которые точно подходят к вашему ${make ? `${make} ${model}` : 'автомобилю'}.`
                    }
                </CardContent>
            </Card>
          </div>

          <DrawerFooter className="pt-0">
            <Button 
                onClick={handleSave} 
                disabled={!make || !model || !year || !engine}
                className="w-full bg-primary text-primary-foreground font-bold"
            >
                Сохранить авто
            </Button>
            {selectedVehicle && (
                <Button variant="outline" onClick={handleClear} className="w-full">
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Сбросить фильтр
                </Button>
            )}
            <DrawerClose asChild>
              <Button variant="ghost">Отмена</Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  )
}

