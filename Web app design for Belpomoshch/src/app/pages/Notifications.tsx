import React, { useState } from 'react';
import { Clock, Calendar, FileText, Check, Trash2, CheckCircle2 } from 'lucide-react';
import { notifications as initialNotifs } from '../mockData';
import { Card, Button } from '../components/ui';

export const Notifications = () => {
  const [notifs, setNotifs] = useState(initialNotifs);

  const markAllRead = () => {
    setNotifs(notifs.map(n => ({ ...n, isRead: true })));
  };

  const markRead = (id: number) => {
    setNotifs(notifs.map(n => n.id === id ? { ...n, isRead: true } : n));
  };

  const clearRead = () => {
    setNotifs(notifs.filter(n => !n.isRead));
  };

  const unreadCount = notifs.filter(n => !n.isRead).length;

  return (
    <div className="max-w-3xl mx-auto space-y-4 md:space-y-8 flex flex-col min-h-full pb-20 md:pb-0">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 md:gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center gap-3">
            Уведомления
            {unreadCount > 0 && (
              <span className="bg-emerald-500 text-white text-xs md:text-sm px-2.5 py-0.5 rounded-full font-medium">
                {unreadCount}
              </span>
            )}
          </h1>
        </div>
        <div className="flex w-full sm:w-auto gap-2">
          {unreadCount > 0 && (
            <Button variant="ghost" className="text-xs md:text-sm flex-1 sm:flex-none justify-center" onClick={markAllRead}>
              Прочитать все
            </Button>
          )}
          {notifs.length > unreadCount && (
            <Button variant="ghost" className="text-xs md:text-sm text-gray-400 hover:text-red-500 hidden sm:flex" onClick={clearRead}>
              Очистить
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-3 md:space-y-4">
        {notifs.map(notif => (
          <Card 
            key={notif.id} 
            className={`p-4 md:p-5 transition-all rounded-2xl ${!notif.isRead ? 'border-emerald-200 bg-emerald-50/10 shadow-sm' : 'border-gray-100 bg-white'}`}
            onClick={() => !notif.isRead && markRead(notif.id)}
          >
            <div className="flex gap-3 md:gap-4">
              <div className="mt-1 flex-shrink-0">
                <div className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center ${!notif.isRead ? 'bg-emerald-100 text-emerald-600' : 'bg-gray-100 text-gray-500'}`}>
                  {notif.type === 'document' && <Clock className="w-5 h-5 md:w-6 md:h-6" />}
                  {notif.type === 'task' && <Calendar className="w-5 h-5 md:w-6 md:h-6" />}
                  {notif.type === 'law' && <FileText className="w-5 h-5 md:w-6 md:h-6" />}
                </div>
              </div>
              <div className="flex-grow min-w-0">
                <div className="flex justify-between items-start mb-1">
                  <h3 className={`font-semibold text-sm md:text-base leading-tight truncate mr-2 ${!notif.isRead ? 'text-gray-900' : 'text-gray-700'}`}>
                    {notif.title}
                  </h3>
                  <span className="text-[10px] md:text-xs text-gray-400 whitespace-nowrap flex-shrink-0">{notif.date}</span>
                </div>
                <p className={`text-xs md:text-sm line-clamp-2 md:line-clamp-none ${!notif.isRead ? 'text-gray-700' : 'text-gray-500'}`}>
                  {notif.desc}
                </p>
                
                {!notif.isRead && (
                  <div className="hidden md:flex mt-4 gap-2">
                    <Button variant="outline" size="sm" className="h-8 text-xs rounded-xl" onClick={(e) => { e.stopPropagation(); markRead(notif.id); }}>
                      <Check className="w-3 h-3 mr-1" /> Прочитано
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </Card>
        ))}
        {notifs.length === 0 && (
          <div className="text-center py-12 px-4 text-gray-500 bg-white rounded-2xl border border-gray-100">
            <CheckCircle2 className="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p className="text-sm">У вас нет новых уведомлений.</p>
          </div>
        )}
      </div>

      {notifs.length > unreadCount && notifs.length > 0 && (
        <Button variant="ghost" className="w-full sm:hidden mt-2 h-12 rounded-xl text-gray-500 hover:text-red-500" onClick={clearRead}>
          <Trash2 className="w-4 h-4 mr-2" /> Очистить прочитанные
        </Button>
      )}
    </div>
  );
};