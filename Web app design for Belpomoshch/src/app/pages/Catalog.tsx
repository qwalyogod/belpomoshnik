import React, { useState } from 'react';
import { NavLink, useSearchParams, useNavigate } from 'react-router';
import { Search, ArrowRight, ChevronRight, FileText } from 'lucide-react';
import { categories, popularProblems } from '../mockData';
import { Input, Card, Badge } from '../components/ui';

export const Catalog = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const currentCategory = searchParams.get('category') || 'all';
  const [searchQuery, setSearchQuery] = useState('');

  // Expand popular problems to simulate a larger catalog
  const catalogItems = [
    ...popularProblems,
    { id: "divorce", title: "Расторжение брака", category: "family", desc: "Процедура развода, раздел имущества и алименты." },
    { id: "sick-leave", title: "Оформление больничного", category: "health", desc: "Как получить и оплатить листок нетрудоспособности." },
    { id: "auto-registration", title: "Регистрация автомобиля", category: "auto", desc: "Постановка авто на учет в ГАИ." },
    { id: "open-ip", title: "Открытие ИП", category: "business", desc: "Регистрация индивидуального предпринимателя." },
  ];

  const filteredItems = catalogItems.filter(item => {
    const matchesCat = currentCategory === 'all' || item.category === currentCategory;
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) || item.desc.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-4 md:space-y-8 flex flex-col h-full">
      {/* Top Header / Search */}
      <div className="space-y-4">
        <h1 className="text-2xl md:text-3xl font-bold">Каталог проблем</h1>
        <div className="w-full">
          <Input 
            icon={<Search className="w-5 h-5" />} 
            placeholder="Поиск по проблемам..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-12 rounded-2xl"
          />
        </div>
      </div>

      {/* Horizontal Chips for Mobile & Desktop */}
      <div className="flex overflow-x-auto hide-scrollbar gap-2 pb-2 -mx-4 px-4 md:mx-0 md:px-0">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSearchParams({ category: cat.id })}
            className={`whitespace-nowrap px-4 py-2 rounded-full text-sm font-medium transition-colors ${currentCategory === cat.id ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'}`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-3 md:gap-4 pb-4">
        {filteredItems.map(item => {
          const catName = categories.find(c => c.id === item.category)?.name;
          return (
            <NavLink key={item.id} to={`/problem/${item.id}`}>
              <Card className="p-4 md:p-6 flex flex-col hover:border-emerald-500 transition-colors group rounded-2xl h-full">
                <div className="flex gap-4">
                  <div className="hidden sm:flex w-12 h-12 rounded-full bg-gray-50 items-center justify-center text-gray-400 shrink-0">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div className="flex-grow">
                    <div className="flex justify-between items-start mb-2">
                      <Badge variant="secondary" className="text-[10px] md:text-xs">{catName}</Badge>
                      <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-500 transition-colors md:hidden" />
                    </div>
                    <h3 className="text-base md:text-lg font-bold mb-1 group-hover:text-emerald-600 transition-colors leading-tight">{item.title}</h3>
                    <p className="text-gray-500 text-xs md:text-sm line-clamp-2 leading-relaxed">{item.desc}</p>
                  </div>
                  <div className="hidden md:flex flex-col justify-center">
                    <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-500 transition-colors" />
                  </div>
                </div>
              </Card>
            </NavLink>
          );
        })}
        {filteredItems.length === 0 && (
          <div className="text-center py-12 text-gray-500 bg-white rounded-2xl border border-gray-100">
            По вашему запросу ничего не найдено.
          </div>
        )}
      </div>
    </div>
  );
};