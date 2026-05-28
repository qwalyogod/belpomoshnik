import React from 'react';
import { Plus, CreditCard, Activity, Car, Home, MoreVertical, ChevronRight } from 'lucide-react';
import { userDocuments } from '../mockData';
import { Card, Button, Badge } from '../components/ui';

const iconMap = { CreditCard, Activity, Car, Home };

export const MyDocuments = () => {
  return (
    <div className="space-y-6 md:space-y-8 flex flex-col min-h-full pb-20 md:pb-0">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 md:gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold mb-1 md:mb-2">Мои документы</h1>
          <p className="text-sm md:text-base text-gray-500">Управляйте сроками действия ваших документов.</p>
        </div>
        <Button className="hidden md:flex gap-2 shrink-0 h-12 rounded-2xl">
          <Plus className="w-5 h-5" /> Добавить документ
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-6">
        {userDocuments.map(doc => {
          const Icon = iconMap[doc.icon as keyof typeof iconMap];
          
          let statusBadge = "default";
          let iconColorClass = "text-gray-600 bg-gray-50";
          
          if (doc.status === "Активен") {
            statusBadge = "success";
            iconColorClass = "text-emerald-600 bg-emerald-50";
          }
          if (doc.status === "Истекает скоро") {
            statusBadge = "warning";
            iconColorClass = "text-orange-600 bg-orange-50";
          }
          if (doc.status === "Требуется обновление") {
            statusBadge = "error";
            iconColorClass = "text-red-600 bg-red-50";
          }

          return (
            <Card key={doc.id} className="p-4 md:p-6 rounded-2xl border-gray-200 cursor-pointer hover:shadow-md transition-shadow group flex flex-col justify-between">
              <div className="flex justify-between items-start mb-4 md:mb-6">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border border-gray-100/50 shadow-sm ${iconColorClass}`}>
                    {Icon && <Icon className="w-6 h-6" />}
                  </div>
                  <div>
                    <h3 className="text-base md:text-xl font-bold leading-tight group-hover:text-emerald-600 transition-colors">{doc.title}</h3>
                    <p className="text-xs md:text-sm text-gray-500 mt-1">{doc.details}</p>
                  </div>
                </div>
                <button className="text-gray-400 hover:text-gray-600 p-1 md:hidden">
                  <ChevronRight className="w-5 h-5 group-hover:text-emerald-500 transition-colors" />
                </button>
                <button className="hidden md:block text-gray-400 hover:text-gray-600 p-1">
                  <MoreVertical className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex items-center justify-between border-t border-gray-100 pt-3 md:pt-4">
                <Badge variant={statusBadge as any} className="text-[10px] md:text-xs font-medium px-2.5 py-1">{doc.status}</Badge>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Mobile Fixed Floating Action Button */}
      <div className="md:hidden fixed bottom-[80px] right-4 z-40">
        <button className="w-14 h-14 bg-emerald-600 text-white rounded-full flex items-center justify-center shadow-lg hover:bg-emerald-700 active:scale-95 transition-all">
          <Plus className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};