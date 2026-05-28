export const mockUser = {
  name: "Иван Иванов",
  email: "ivan@example.by",
  region: "Минская область",
  city: "Минск",
  avatarUrl: "https://images.unsplash.com/photo-1599566150163-29194dcaad36?auto=format&fit=crop&q=80&w=200&h=200",
  interests: ["Собственник жилья", "Есть дети", "Авто есть"]
};

export const categories = [
  { id: "all", name: "Все категории", icon: "LayoutGrid" },
  { id: "docs", name: "Документы", icon: "FileText" },
  { id: "home", name: "Жильё и ЖКХ", icon: "Home" },
  { id: "taxes", name: "Налоги", icon: "Wallet" },
  { id: "family", name: "Семья", icon: "Users" },
  { id: "work", name: "Работа", icon: "Briefcase" },
  { id: "health", name: "Здоровье", icon: "Heart" },
  { id: "auto", name: "Авто", icon: "Car" },
  { id: "business", name: "Бизнес/ИП", icon: "Building2" },
];

export const popularProblems = [
  { id: "lost-passport", title: "Потерял паспорт", category: "docs", desc: "Что делать и куда обращаться при утере паспорта гражданина РБ." },
  { id: "med-book", title: "Нужна медкнижка", category: "health", desc: "Порядок оформления медицинской книжки для работы." },
  { id: "no-utility-bill", title: "Не пришла квитанция ЖКХ", category: "home", desc: "Как узнать сумму к оплате и получить квитанцию." },
  { id: "tax-error", title: "Налог начислили неправильно", category: "taxes", desc: "Оспаривание неверно начисленных налогов." },
  { id: "moving", title: "Переезд и регистрация", category: "home", desc: "Смена места жительства и перерегистрация." },
  { id: "childbirth", title: "Рождение ребёнка", category: "family", desc: "Выплаты, регистрация и первые документы малыша." },
];

export const userSituations = [
  { id: "childbirth", title: "Рождение ребёнка", status: "В процессе", progress: 40 },
  { id: "moving", title: "Переезд и регистрация", status: "Запланировано", progress: 0 },
  { id: "buy-home", title: "Покупка жилья", status: "В процессе", progress: 75 },
  { id: "open-ip", title: "Открытие ИП", status: "Завершено", progress: 100 },
];

export const userDocuments = [
  { id: "passport", title: "Паспорт", status: "Активен", icon: "CreditCard", details: "КН 1234567" },
  { id: "med", title: "Медкнижка", status: "Истекает скоро", icon: "Activity", details: "Действ. до 15.06.2026" },
  { id: "auto", title: "Автомобильные документы", status: "Активен", icon: "Car", details: "Вод. удостоверение" },
  { id: "utility", title: "ЖКХ / Лицевой счёт", status: "Требуется обновление", icon: "Home", details: "Необходимо обновить данные" },
];

export const notifications = [
  { id: 1, title: "Медкнижка истекает", desc: "Срок действия медкнижки истекает через 30 дней.", type: "document", isRead: false, date: "Сегодня" },
  { id: 2, title: "Оплата ЖКХ", desc: "Передать показания ЖКХ до 25 числа.", type: "task", isRead: false, date: "Вчера" },
  { id: 3, title: "Новый закон", desc: "Изменения в налогообложении ИП с 1 января.", type: "law", isRead: true, date: "3 дня назад" },
];

export const laws = [
  { id: "law1", title: "Изменения в налоге на профессиональный доход", category: "taxes", date: "01.07.2026", target: "Фрилансеры, самозанятые", short: "Изменена ставка налога для некоторых видов деятельности." },
  { id: "law2", title: "Новые правила оплаты услуг ЖКХ", category: "home", date: "15.08.2026", target: "Собственники жилья", short: "Вводится единый тариф на вывоз мусора в сельской местности." },
  { id: "law3", title: "Увеличение пособия при рождении ребенка", category: "family", date: "01.09.2026", target: "Семьи с детьми", short: "Единовременное пособие увеличивается на 15%." },
];

export const childbirthTasks = [
  { id: 1, title: "Получить справку о рождении в роддоме", completed: true, deadline: "Сразу после выписки" },
  { id: 2, title: "Зарегистрировать ребёнка в ЗАГС", completed: false, deadline: "До 1 месяца" },
  { id: 3, title: "Прописка ребёнка", completed: false, deadline: "До 1 месяца" },
  { id: 4, title: "Оформить пособие", completed: false, deadline: "До 6 месяцев" },
  { id: 5, title: "Оформить медполис", completed: false, deadline: "Как можно скорее" },
];
