"use client"

import { useState, useEffect, useCallback } from "react"
import { ChevronRight, ArrowLeft, Search, Package, Wrench, Fuel, Thermometer, Wind, Settings, Disc, CircleDot, Zap, Snowflake, Sofa, Car, PlusCircle, Sparkles, Warehouse, SlidersHorizontal } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ProductCard, ProductCardSkeleton } from "@/components/product-card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

interface Category {
    id: number
    name: string
    slug: string
    children?: Category[]
}

interface Product {
    id: number
    name: string
    price_rub: number
    price_usd?: number
    image_url: string
    part_number: string
    is_in_stock: boolean
    is_installment_available?: boolean
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const LIMIT = 20

const categoryIcons: Record<string, React.ReactNode> = {
    "Детали для ТО": <Wrench className="h-5 w-5" />,
    "Двигатель": <Settings className="h-5 w-5" />,
    "Топливная система": <Fuel className="h-5 w-5" />,
    "Система охлаждения": <Thermometer className="h-5 w-5" />,
    "Система выпуска": <Wind className="h-5 w-5" />,
    "Трансмиссия": <Disc className="h-5 w-5" />,
    "Ходовая часть": <CircleDot className="h-5 w-5" />,
    "Рулевое управление": <CircleDot className="h-5 w-5" />,
    "Тормозная система": <Disc className="h-5 w-5" />,
    "Электрооборудование": <Zap className="h-5 w-5" />,
    "Отопление / кондиционирование": <Snowflake className="h-5 w-5" />,
    "Детали салона": <Sofa className="h-5 w-5" />,
    "Детали кузова": <Car className="h-5 w-5" />,
    "Дополнительное оборудование": <PlusCircle className="h-5 w-5" />,
    "Тюнинг": <Sparkles className="h-5 w-5" />,
    "📦 Все товары со склада": <Warehouse className="h-5 w-5" />,
}

interface CatalogViewProps {
    onProductClick?: (productId: number) => void
}

export function CatalogView({ onProductClick }: CatalogViewProps) {
    // Categories
    const [categories, setCategories] = useState<Category[]>([])
    const [loadingCats, setLoadingCats] = useState(true)
    const [selectedCategory, setSelectedCategory] = useState<Category | null>(null)
    const [breadcrumbs, setBreadcrumbs] = useState<Category[]>([])
    
    // Products
    const [products, setProducts] = useState<Product[]>([])
    const [loadingProducts, setLoadingProducts] = useState(false)
    const [totalCount, setTotalCount] = useState(0)
    const [currentPage, setCurrentPage] = useState(0)
    
    // Search
    const [searchQuery, setSearchQuery] = useState("")
    const [isSearchMode, setIsSearchMode] = useState(false)
    
    // Filters
    const [showFilters, setShowFilters] = useState(false)
    const [sortBy, setSortBy] = useState("")
    const [inStockOnly, setInStockOnly] = useState(false)
    const [minPrice, setMinPrice] = useState("")
    const [maxPrice, setMaxPrice] = useState("")

    // Load categories
    useEffect(() => {
        fetch(`${API_URL}/categories/tree`)
            .then(res => res.json())
            .then(data => setCategories(data))
            .catch(err => console.error(err))
            .finally(() => setLoadingCats(false))
    }, [])

    // Fetch products function
    const fetchProducts = useCallback(async (categoryId?: number, search?: string, page = 0, append = false) => {
        setLoadingProducts(true)
        
        const params = new URLSearchParams()
        params.set("skip", String(page * LIMIT))
        params.set("limit", String(LIMIT))
        
        if (categoryId) params.set("category_id", String(categoryId))
        if (search) params.set("search", search)
        if (sortBy) params.set("sort_by", sortBy)
        if (inStockOnly) params.set("in_stock", "true")
        if (minPrice) params.set("min_price", minPrice)
        if (maxPrice) params.set("max_price", maxPrice)
        
        try {
            // Fetch products
            const res = await fetch(`${API_URL}/products/?${params.toString()}`)
            const data = await res.json()
            
            if (append) {
                setProducts(prev => [...prev, ...data])
            } else {
                setProducts(data)
            }
            
            // Fetch count
            const countParams = new URLSearchParams()
            if (categoryId) countParams.set("category_id", String(categoryId))
            if (search) countParams.set("search", search)
            if (inStockOnly) countParams.set("in_stock", "true")
            if (minPrice) countParams.set("min_price", minPrice)
            if (maxPrice) countParams.set("max_price", maxPrice)
            
            const countRes = await fetch(`${API_URL}/products/count?${countParams.toString()}`)
            const countData = await countRes.json()
            setTotalCount(countData.count)
            
        } catch (err) {
            console.error(err)
        } finally {
            setLoadingProducts(false)
        }
    }, [sortBy, inStockOnly, minPrice, maxPrice])

    // Handle category click
    const handleCategoryClick = (cat: Category) => {
        setIsSearchMode(false)
        setSearchQuery("")
        
        // Всегда устанавливаем категорию
        setBreadcrumbs([...breadcrumbs, cat])
        setSelectedCategory(cat)
        setCurrentPage(0)
        
        // Всегда загружаем товары категории (включая товары из подкатегорий)
        fetchProducts(cat.id, undefined, 0, false)
    }

    // Handle search
    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (!searchQuery.trim()) return
        
        setIsSearchMode(true)
        setSelectedCategory(null)
        setBreadcrumbs([])
        setCurrentPage(0)
        fetchProducts(undefined, searchQuery, 0, false)
    }

    // Handle back
    const handleBack = () => {
        if (isSearchMode) {
            setIsSearchMode(false)
            setProducts([])
            setSearchQuery("")
            return
        }
        
        if (breadcrumbs.length > 1) {
            const newBreadcrumbs = breadcrumbs.slice(0, -1)
            setBreadcrumbs(newBreadcrumbs)
            setSelectedCategory(newBreadcrumbs[newBreadcrumbs.length - 1])
            setProducts([])
        } else {
            setBreadcrumbs([])
            setSelectedCategory(null)
            setProducts([])
        }
    }

    // Handle load more
    const handleLoadMore = () => {
        const nextPage = currentPage + 1
        setCurrentPage(nextPage)
        fetchProducts(selectedCategory?.id, isSearchMode ? searchQuery : undefined, nextPage, true)
    }

    // Apply filters
    const applyFilters = () => {
        setShowFilters(false)
        setCurrentPage(0)
        if (selectedCategory) {
            fetchProducts(selectedCategory.id, undefined, 0, false)
        } else if (isSearchMode) {
            fetchProducts(undefined, searchQuery, 0, false)
        }
    }

    // Reset filters
    const resetFilters = () => {
        setSortBy("")
        setInStockOnly(false)
        setMinPrice("")
        setMaxPrice("")
        setShowFilters(false)
        setCurrentPage(0)
        if (selectedCategory) {
            // Need to fetch without filters
            setLoadingProducts(true)
            const params = new URLSearchParams()
            params.set("skip", "0")
            params.set("limit", String(LIMIT))
            params.set("category_id", String(selectedCategory.id))
            
            fetch(`${API_URL}/products/?${params.toString()}`)
                .then(res => res.json())
                .then(data => setProducts(data))
                .finally(() => setLoadingProducts(false))
        }
    }

    const activeFiltersCount = [sortBy, inStockOnly, minPrice, maxPrice].filter(Boolean).length
    const hasMore = products.length < totalCount

    // ============ RENDER ============

    // Products view (category selected or search mode)
    if ((selectedCategory && products.length > 0) || (selectedCategory && loadingProducts) || isSearchMode) {
        return (
            <div className="flex flex-col pb-24 min-h-screen">
                {/* Header */}
                <div className="sticky top-0 z-20 bg-background border-b border-white/5">
                    <div className="px-4 py-3 flex items-center gap-3">
                        <Button variant="ghost" size="icon" onClick={handleBack} className="-ml-2">
                            <ArrowLeft className="h-6 w-6" />
                        </Button>
                        <div className="flex-1 min-w-0">
                            <h2 className="text-lg font-bold truncate">
                                {isSearchMode ? `"${searchQuery}"` : selectedCategory?.name.replace('📦 ', '')}
                            </h2>
                            <p className="text-xs text-muted-foreground">{totalCount.toLocaleString()} товаров</p>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)} className="relative">
                            <SlidersHorizontal className="h-4 w-4" />
                            {activeFiltersCount > 0 && (
                                <Badge className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center bg-primary text-[10px]">
                                    {activeFiltersCount}
                                </Badge>
                            )}
                        </Button>
                    </div>

                    {/* Filters */}
                    {showFilters && (
                        <div className="px-4 pb-4 space-y-4 border-t border-white/5 pt-4">
                            <div>
                                <p className="text-xs text-muted-foreground mb-2">Сортировка</p>
                                <div className="flex flex-wrap gap-2">
                                    <Button size="sm" variant={sortBy === "" ? "default" : "outline"} onClick={() => setSortBy("")}>По умолчанию</Button>
                                    <Button size="sm" variant={sortBy === "price_asc" ? "default" : "outline"} onClick={() => setSortBy("price_asc")}>Сначала дешёвые</Button>
                                    <Button size="sm" variant={sortBy === "price_desc" ? "default" : "outline"} onClick={() => setSortBy("price_desc")}>Сначала дорогие</Button>
                                </div>
                            </div>
                            
                            <div>
                                <p className="text-xs text-muted-foreground mb-2">Цена, ₽</p>
                                <div className="flex gap-2 items-center">
                                    <Input type="number" placeholder="От" value={minPrice} onChange={e => setMinPrice(e.target.value)} className="w-28 bg-white/5 border-white/10" />
                                    <span>—</span>
                                    <Input type="number" placeholder="До" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} className="w-28 bg-white/5 border-white/10" />
                                </div>
                            </div>
                            
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" checked={inStockOnly} onChange={e => setInStockOnly(e.target.checked)} className="rounded" />
                                <span className="text-sm">Только в наличии</span>
                            </label>
                            
                            <div className="flex gap-2">
                                <Button onClick={applyFilters} className="flex-1">Применить</Button>
                                <Button variant="outline" onClick={resetFilters}>Сбросить</Button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Products */}
                <div className="px-4 pt-4">
                    {loadingProducts && products.length === 0 ? (
                        <div className="grid grid-cols-2 gap-3">
                            {Array.from({ length: 6 }).map((_, i) => <ProductCardSkeleton key={i} />)}
                        </div>
                    ) : products.length > 0 ? (
                        <>
                            <div className="grid grid-cols-2 gap-3">
                                {products.map(p => <ProductCard key={p.id} product={p} onClick={onProductClick} />)}
                            </div>
                            
                            {hasMore && (
                                <Button variant="outline" onClick={handleLoadMore} disabled={loadingProducts} className="w-full mt-6">
                                    {loadingProducts ? "Загрузка..." : "Показать ещё"}
                                </Button>
                            )}
                            
                            <p className="text-center text-xs text-muted-foreground mt-4 mb-8">
                                Показано {products.length} из {totalCount}
                            </p>
                        </>
                    ) : (
                        <div className="text-center py-20">
                            <p className="text-lg font-medium">Ничего не найдено</p>
                            <p className="text-sm text-muted-foreground">Попробуйте изменить фильтры</p>
                        </div>
                    )}
                </div>
            </div>
        )
    }

    // Subcategories view
    if (selectedCategory?.children && selectedCategory.children.length > 0) {
        return (
            <div className="flex flex-col pb-24 min-h-screen">
                <div className="sticky top-0 z-10 bg-background border-b border-white/5 px-4 py-3 flex items-center gap-3">
                    <Button variant="ghost" size="icon" onClick={handleBack} className="-ml-2">
                        <ArrowLeft className="h-6 w-6" />
                    </Button>
                    <div>
                        <h2 className="text-lg font-bold">{selectedCategory.name}</h2>
                        <p className="text-xs text-muted-foreground">{selectedCategory.children.length} подкатегорий</p>
                    </div>
                </div>
                
                <div className="px-4 pt-4 space-y-2">
                    {selectedCategory.children.map(sub => (
                        <Card key={sub.id} onClick={() => handleCategoryClick(sub)} className="bg-white/5 border-white/10 p-4 flex items-center justify-between cursor-pointer hover:bg-white/10 active:scale-[0.99] transition-all">
                            <span className="font-medium">{sub.name}</span>
                            <ChevronRight className="h-5 w-5 text-muted-foreground" />
                        </Card>
                    ))}
                </div>
            </div>
        )
    }

    // Main catalog view
    return (
        <div className="flex flex-col pb-24 min-h-screen">
            <div className="sticky top-0 z-10 bg-background border-b border-white/5 px-4 py-4">
                <h2 className="text-xl font-bold mb-3">Каталог</h2>
                <form onSubmit={handleSearch} className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        type="search"
                        placeholder="Поиск по названию или артикулу..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="pl-10 bg-white/5 border-white/10"
                    />
                </form>
            </div>
            
            <div className="px-4 pt-4 space-y-2">
                {loadingCats ? (
                    Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-16 bg-white/5 rounded-xl" />)
                ) : (
                    categories.map(cat => {
                        const icon = categoryIcons[cat.name] || <Package className="h-5 w-5" />
                        const isWarehouse = cat.name.includes("склада")
                        
                        return (
                            <Card 
                                key={cat.id}
                                onClick={() => handleCategoryClick(cat)}
                                className={`p-4 flex items-center gap-3 cursor-pointer hover:bg-white/10 active:scale-[0.99] transition-all ${isWarehouse ? 'bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20' : 'bg-white/5 border-white/10'}`}
                            >
                                <div className={`p-2.5 rounded-xl ${isWarehouse ? 'bg-primary/20 text-primary' : 'bg-white/10'}`}>
                                    {icon}
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-semibold text-sm">{cat.name.replace('📦 ', '')}</h3>
                                    {cat.children && cat.children.length > 0 && (
                                        <p className="text-xs text-muted-foreground">{cat.children.length} подкатегорий</p>
                                    )}
                                </div>
                                <ChevronRight className="h-5 w-5 text-muted-foreground" />
                            </Card>
                        )
                    })
                )}
            </div>
        </div>
    )
}
