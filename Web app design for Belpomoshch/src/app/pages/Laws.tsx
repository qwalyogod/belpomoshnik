import React, { useState } from 'react';
import { NavLink } from 'react-router';
import { Calendar, Users, ArrowRight } from 'lucide-react';
import { laws } from '../mockData';
import { Card, Badge, Button } from '../components/ui';

export const Laws = () => {
  const [filter, setFilter] = useState('all');
  
  const filters = [
    { id: 'all', label: 'Все' },
    { id: 'taxes', label: 'Налоги' },
    { id: 'home', label: 'ЖКХ' },
    { id: 'docs', label: 'Документы' },
    { id: 'family', label: 'Семья' },
    { id: 'work', label: 'Работа' },
  ];

  const filteredLaws = filter === 'all' ? laws : laws.filter(l => l.category === filter);

  return (
    <div className="space-y-6 md:space-y-8 max-w-4xl mx-auto flex flex-col min-h-full pb-20 md:pb-0">
      <div className="text-left md:text-center space-y-2 md:space-y-4 mb-4 md:mb-8">
        <h1 className="text-2xl md:text-3xl font-bold">Изменения законодательства</h1>
        <p className="text-sm md:text-lg text-gray-600">Понятно и просто о новых законах и правилах, которые касаются каждого.</p>
      </div>

      <div className="flex overflow-x-auto hide-scrollbar gap-2 pb-2 mb-4 md:mb-8 md:justify-center -mx-4 px-4 md:mx-0 md:px-0">
        {filters.map(f => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`whitespace-nowrap px-4 md:px-5 py-2 rounded-full text-xs md:text-sm font-medium transition-colors ${filter === f.id ? 'bg-gray-900 text-white shadow-sm' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'}`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="space-y-4 md:space-y-6">
        {filteredLaws.map(law => (
          <Card key={law.id} className="p-4 md:p-8 hover:border-emerald-200 transition-colors group rounded-2xl">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 md:gap-6">
              <div className="space-y-3 md:space-y-4 flex-grow">
                <div className="flex flex-wrap items-center gap-2 text-xs md:text-sm text-gray-500">
                  <span className="flex items-center gap-1.5 bg-gray-100 px-2.5 py-1 rounded-full text-gray-700">
                    <Calendar className="w-3.5 h-3.5" /> {law.date}
                  </span>
                  <span className="flex items-center gap-1.5 text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full">
                    <Users className="w-3.5 h-3.5" /> {law.target}
                  </span>
                </div>
                
                <h2 className="text-lg md:text-2xl font-bold group-hover:text-emerald-700 transition-colors leading-tight">
                  {law.title}
                </h2>
                
                <p className="text-sm md:text-lg text-gray-600 leading-relaxed line-clamp-3 md:line-clamp-none">
                  {law.short}
                </p>
              </div>
              
              <div className="shrink-0 mt-2 md:mt-0">
                <NavLink to={`/laws/${law.id}`} className="block">
                  <Button variant="outline" className="w-full md:w-auto h-12 md:h-10 rounded-xl group-hover:bg-emerald-50 group-hover:border-emerald-200 group-hover:text-emerald-700 text-sm">
                    Подробнее <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </NavLink>
              </div>
            </div>
          </Card>
        ))}
        {filteredLaws.length === 0 && (
          <div className="text-center py-12 px-4 text-gray-500 bg-white rounded-2xl border border-gray-100">
            <p className="text-sm">В данной категории пока нет новых законов.</p>
          </div>
        )}
      </div>
    </div>
  );
};