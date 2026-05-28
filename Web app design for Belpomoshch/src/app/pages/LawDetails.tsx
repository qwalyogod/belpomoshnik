import React from 'react';
import { NavLink, useParams, useNavigate } from 'react-router';
import { ArrowLeft, Bookmark, Calendar, Users, CircleAlert, CircleCheck, Link as LinkIcon } from 'lucide-react';
import { laws } from '../mockData';
import { Card, Button, Badge } from '../components/ui';

export const LawDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const law = laws.find(l => l.id === id) || laws[0]; // fallback to first law

  return (
    <div className="max-w-3xl mx-auto space-y-6 md:space-y-8 flex flex-col min-h-full pb-20 md:pb-0">
      {/* Mobile Top Bar */}
      <div className="md:hidden flex items-center gap-3 mb-2 sticky top-0 bg-[#F8FAFC] z-10 py-3 -mx-4 px-4">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-lg font-bold truncate">Подробности</h1>
        <button className="p-2 ml-auto text-gray-600 hover:bg-gray-100 rounded-full">
          <Bookmark className="w-5 h-5" />
        </button>
      </div>

      <div className="hidden md:block">
        <NavLink to="/laws" className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-900 mb-6 text-sm font-medium transition-colors">
          <ArrowLeft className="w-4 h-4" /> Назад к списку
        </NavLink>
      </div>
        
      <div className="space-y-4">
        <Badge variant="blue" className="mb-2">Налоги</Badge>
        <h1 className="text-2xl md:text-4xl font-bold leading-tight">{law.title}</h1>
        
        <div className="flex flex-col sm:flex-row flex-wrap gap-3 md:gap-4 pt-2">
            <div className="flex items-center gap-2 text-gray-600 bg-white px-4 py-3 md:py-2 rounded-xl border border-gray-100 shadow-sm text-sm">
              <Calendar className="w-5 h-5 text-emerald-600" />
              <span className="font-medium">Вступает в силу: <span className="text-gray-900 block sm:inline">{law.date}</span></span>
            </div>
            <div className="flex items-center gap-2 text-gray-600 bg-white px-4 py-3 md:py-2 rounded-xl border border-gray-100 shadow-sm text-sm">
              <Users className="w-5 h-5 text-blue-600" />
              <span className="font-medium">Кого касается: <span className="text-gray-900 block sm:inline">{law.target}</span></span>
            </div>
        </div>
      </div>

      <div className="hidden md:flex gap-3">
        <Button className="gap-2 bg-gray-900 hover:bg-gray-800 text-white">
          <Bookmark className="w-4 h-4" /> Сохранить
        </Button>
        <Button variant="outline" className="gap-2">
          <LinkIcon className="w-4 h-4" /> Источник
        </Button>
      </div>

      <div className="space-y-4 md:space-y-6">
        <Card className="p-5 md:p-8 border-l-4 border-l-blue-500 rounded-2xl rounded-l-none md:rounded-2xl">
          <h2 className="text-lg md:text-xl font-bold mb-3 md:mb-4 flex items-center gap-2">
            <CircleAlert className="w-6 h-6 text-blue-500" />
            Что изменилось
          </h2>
          <div className="prose text-gray-700 leading-relaxed space-y-4 text-sm md:text-base">
            <p>
              В соответствии с новым постановлением, изменяется порядок начисления налога на профессиональный доход. 
              {law.short} Теперь ставка будет зависеть от годового оборота и региона регистрации.
            </p>
            <p>
              Основное нововведение заключается в том, что для доходов до 60 000 BYN в год ставка составит 10%, а для суммы превышения — 20%.
            </p>
          </div>
        </Card>

        <Card className="p-5 md:p-8 border-l-4 border-l-emerald-500 rounded-2xl rounded-l-none md:rounded-2xl">
          <h2 className="text-lg md:text-xl font-bold mb-3 md:mb-4 flex items-center gap-2">
            <CircleCheck className="w-6 h-6 text-emerald-500" />
            Что нужно сделать
          </h2>
          <ul className="space-y-3 md:space-y-4">
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm mt-0.5">1</span>
              <span className="text-gray-800 text-sm md:text-base">Обновить приложение "Налог на профессиональный доход" до последней версии перед началом нового месяца.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm mt-0.5">2</span>
              <span className="text-gray-800 text-sm md:text-base">Проверить свои реквизиты в личном кабинете налогоплательщика.</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-sm mt-0.5">3</span>
              <span className="text-gray-800 text-sm md:text-base">Если ваш оборот превышает лимиты, проконсультироваться с бухгалтером о возможном переходе на ИП.</span>
            </li>
          </ul>
        </Card>
        
        <Button variant="outline" className="w-full md:hidden h-12 rounded-xl text-gray-600 gap-2 mt-2 bg-white">
          <LinkIcon className="w-4 h-4" /> Открыть первоисточник
        </Button>
      </div>
    </div>
  );
};