import {
  Category, Scenario, UserSituation, UserDocument, AppNotification, LegalUpdate, UserProfile, Settings, Problem,
  UtilityAccount, TaxObligation
} from "./types";

export const CATEGORIES: Category[] = [
  { id: "documents", name: "Документы" },
  { id: "family", name: "Семья" },
  { id: "work", name: "Работа" },
  { id: "business", name: "ИП и бизнес" },
  { id: "housing", name: "Жильё и ЖКХ" },
  { id: "taxes", name: "Налоги" },
  { id: "health", name: "Здоровье" },
  { id: "auto", name: "Авто" },
];

const rovd = {
  id: "rovd-pervomaisky",
  name: "РОВД Первомайского района",
  address: "ул. Кальварийская, 14, Минск",
  hours: "Пн–Пт · 9:00–18:00",
  phone: "+375 17 200-00-00",
};

const mfc = {
  id: "mfc-minsk",
  name: "МФЦ г. Минск",
  address: "пр. Независимости, 11",
  hours: "Пн–Сб · 8:00–20:00",
};

const tax = {
  id: "tax-minsk",
  name: "ИМНС по Первомайскому району",
  address: "ул. Калиновского, 28",
  hours: "Пн–Пт · 9:00–17:30",
};

export const SCENARIOS: Scenario[] = [
  {
    id: "passport-loss",
    title: "Потеря паспорта",
    category: "documents",
    shortDescription: "Что делать при утере паспорта гражданина РБ.",
    longDescription:
      "Если вы потеряли паспорт, важно как можно скорее обратиться в РОВД по месту жительства. План охватывает все шаги — от подачи заявления до получения нового документа.",
    forWhom: "Граждане Республики Беларусь, потерявшие паспорт на территории страны.",
    estimatedTime: "от 14 дней",
    difficulty: "medium",
    stages: [
      {
        id: "s1", title: "Подготовка",
        tasks: [
          { id: "t1", title: "Получить справку об утере", kind: "visit", durationHint: "1 день", institutionId: rovd.id, documents: ["d-application"] },
          { id: "t2", title: "Сделать фото 4×5", kind: "document", durationHint: "1 час" },
        ],
      },
      {
        id: "s2", title: "Подача документов",
        tasks: [
          { id: "t3", title: "Заполнить заявление по форме", kind: "form", blockedBy: ["t1"] },
          { id: "t4", title: "Подать заявление в РОВД", kind: "visit", institutionId: rovd.id, blockedBy: ["t2","t3"], documents: ["d-application","d-photo"] },
        ],
      },
      {
        id: "s3", title: "Оплата и получение",
        tasks: [
          { id: "t5", title: "Оплатить госпошлину через ЕРИП", kind: "payment", durationHint: "10 минут", blockedBy: ["t4"] },
          { id: "t6", title: "Получить новый паспорт", kind: "visit", durationHint: "до 14 дней", institutionId: rovd.id, blockedBy: ["t5"] },
        ],
      },
    ],
    documents: [
      { id: "d-application", name: "Заявление об утере", required: true },
      { id: "d-photo", name: "Фотография 4×5 (2 шт.)", required: true },
      { id: "d-receipt", name: "Квитанция об оплате госпошлины", required: true, note: "Через ЕРИП" },
    ],
    institutions: [rovd],
    sources: [
      { id: "src-mvd", title: "Официальный сайт МВД РБ", url: "mvd.gov.by", description: "Порядок выдачи и замены паспорта.", checkedAt: "2026-05-12" },
      { id: "src-erip", title: "Платёжная система ЕРИП", url: "raschet.by", description: "Реквизиты для оплаты госпошлины.", checkedAt: "2026-04-20" },
    ],
    relatedIds: ["id-card", "moving"],
  },
  {
    id: "child-birth",
    title: "Рождение ребёнка",
    category: "family",
    shortDescription: "Регистрация ребёнка, пособия и медицинская карта.",
    longDescription:
      "После рождения ребёнка необходимо оформить свидетельство о рождении, прописать ребёнка, оформить детское пособие и медицинскую карту.",
    forWhom: "Родители новорождённого, граждане Республики Беларусь.",
    estimatedTime: "от 30 дней",
    difficulty: "medium",
    stages: [
      {
        id: "s1", title: "Регистрация",
        tasks: [
          { id: "t1", title: "Получить медсправку о рождении", kind: "document" },
          { id: "t2", title: "Получить свидетельство о рождении", kind: "visit", institutionId: mfc.id, blockedBy: ["t1"] },
        ],
      },
      {
        id: "s2", title: "Пособия и регистрация места жительства",
        tasks: [
          { id: "t3", title: "Оформить единое пособие", kind: "form", blockedBy: ["t2"] },
          { id: "t4", title: "Прописать ребёнка", kind: "visit", blockedBy: ["t2"] },
        ],
      },
    ],
    documents: [
      { id: "d-med", name: "Медицинская справка о рождении", required: true },
      { id: "d-birth", name: "Свидетельство о рождении", required: true },
      { id: "d-passport-parents", name: "Паспорта родителей", required: true },
    ],
    institutions: [mfc],
    sources: [
      { id: "src-mintrud", title: "Министерство труда и социальной защиты", url: "mintrud.gov.by", description: "Порядок назначения пособий.", checkedAt: "2026-05-01" },
    ],
    relatedIds: ["moving"],
  },
  {
    id: "ip-open",
    title: "Открытие ИП",
    category: "business",
    shortDescription: "Регистрация индивидуального предпринимателя.",
    longDescription: "План охватывает выбор системы налогообложения, регистрацию и постановку на учёт.",
    forWhom: "Совершеннолетние граждане РБ, планирующие предпринимательскую деятельность.",
    estimatedTime: "от 5 дней",
    difficulty: "easy",
    stages: [
      { id: "s1", title: "Подготовка", tasks: [
        { id: "t1", title: "Выбрать виды деятельности (ОКЭД)", kind: "form" },
        { id: "t2", title: "Выбрать систему налогообложения", kind: "form" },
      ]},
      { id: "s2", title: "Регистрация", tasks: [
        { id: "t3", title: "Подать документы в исполком", kind: "visit", blockedBy: ["t1","t2"], institutionId: mfc.id },
        { id: "t4", title: "Встать на учёт в ИМНС", kind: "visit", blockedBy: ["t3"], institutionId: tax.id },
      ]},
    ],
    documents: [
      { id: "d-application", name: "Заявление о регистрации", required: true },
      { id: "d-passport", name: "Паспорт", required: true },
    ],
    institutions: [mfc, tax],
    sources: [
      { id: "src-nalog", title: "Министерство по налогам и сборам", url: "nalog.gov.by", description: "Налоговые режимы и формы.", checkedAt: "2026-04-15" },
    ],
    relatedIds: [],
  },
  {
    id: "moving",
    title: "Переезд и регистрация",
    category: "housing",
    shortDescription: "Смена места жительства и регистрация.",
    longDescription: "План включает выписку, переезд, регистрацию по новому адресу и обновление документов.",
    forWhom: "Граждане, меняющие место жительства.",
    estimatedTime: "от 7 дней",
    difficulty: "easy",
    stages: [
      { id: "s1", title: "Документы", tasks: [
        { id: "t1", title: "Получить выписку с прежнего адреса", kind: "visit" },
        { id: "t2", title: "Зарегистрироваться по новому адресу", kind: "visit", blockedBy: ["t1"] },
      ]},
    ],
    documents: [{ id: "d-passport", name: "Паспорт", required: true }],
    institutions: [mfc],
    sources: [],
    relatedIds: ["passport-loss"],
  },
  {
    id: "divorce",
    title: "Расторжение брака",
    category: "family",
    shortDescription: "Подача заявления и юридические шаги.",
    longDescription: "План охватывает подачу заявления, рассмотрение в суде и получение свидетельства.",
    forWhom: "Граждане РБ, оформляющие развод.",
    estimatedTime: "от 30 дней",
    difficulty: "hard",
    stages: [
      { id: "s1", title: "Подача", tasks: [{ id: "t1", title: "Подать заявление", kind: "visit" }] },
    ],
    documents: [{ id: "d-marriage", name: "Свидетельство о браке", required: true }],
    institutions: [mfc],
    sources: [],
    relatedIds: [],
  },
  {
    id: "id-card",
    title: "Получение ID-карты",
    category: "documents",
    shortDescription: "Замена паспорта на биометрическую ID-карту.",
    longDescription: "Электронный паспорт нового поколения. Подходит для въезда в страны без виз с РБ.",
    forWhom: "Граждане РБ от 14 лет.",
    estimatedTime: "от 14 дней",
    difficulty: "easy",
    stages: [
      { id: "s1", title: "Подача", tasks: [{ id: "t1", title: "Подать заявление в МФЦ", kind: "visit", institutionId: mfc.id }] },
    ],
    documents: [{ id: "d-passport", name: "Паспорт", required: true }],
    institutions: [mfc],
    sources: [],
    relatedIds: ["passport-loss"],
  },
];

export const INITIAL_SITUATIONS: UserSituation[] = [
  {
    id: "us-1",
    scenarioId: "passport-loss",
    status: "in_progress",
    startedAt: "2026-05-10",
    completedTaskIds: ["t1", "t2"],
    notes: {},
  },
  {
    id: "us-2",
    scenarioId: "ip-open",
    status: "in_progress",
    startedAt: "2026-05-28",
    completedTaskIds: [],
    notes: {},
  },
];

export const INITIAL_DOCUMENTS: UserDocument[] = [
  { id: "passport", type: "passport", title: "Паспорт", number: "КН 1234567", issuedAt: "2020-04-12", expiresAt: "2030-04-12", status: "active" },
  { id: "med", type: "medical", title: "Медкнижка", number: "МК 882134", issuedAt: "2025-06-15", expiresAt: "2026-06-15", status: "expiring" },
  { id: "auto", type: "driver", title: "Автомобильные документы", number: "AB 654321", issuedAt: "2021-03-10", expiresAt: "2031-03-10", status: "active" },
  { id: "utility", type: "housing", title: "ЖКХ / Лицевой счёт", number: "ЛС 00124578", status: "active" },
];

export const INITIAL_NOTIFICATIONS: AppNotification[] = [
  { id: "n1", kind: "document_expiring", title: "Медкнижка истекает", body: "Срок действия медкнижки истекает через 30 дней.", createdAt: "2026-06-05T09:00:00Z", read: false },
  { id: "n2", kind: "task_due", title: "Оплата ЖКХ", body: "Передать показания ЖКХ до 25 числа.", createdAt: "2026-06-04T09:00:00Z", read: false, link: { page: "finance" } },
  { id: "n3", kind: "document_expiring", title: "Паспорт истекает", body: "Паспорт истекает через 120 дней.", createdAt: "2026-06-02T09:00:00Z", read: true },
  { id: "n4", kind: "legal_update", title: "Проверить налоги", body: "Проверьте начисления налогов в личном кабинете.", createdAt: "2026-05-31T09:00:00Z", read: true, link: { page: "legal" } },
];

export const LEGAL_UPDATES: LegalUpdate[] = [
  {
    id: "law-1", category: "taxes", title: "Новый порядок имущественного вычета для семей с детьми",
    summary: "Семьи с двумя и более детьми смогут вернуть до 13% от стоимости приобретённого жилья.",
    whoAffected: "Семьи с двумя и более детьми, приобретающие жильё на территории РБ.",
    whatChanged: "Введён единый порядок расчёта вычета, увеличен лимит компенсации.",
    whatToDo: "Подать заявление в ИМНС с подтверждающими документами в течение года с момента покупки.",
    effectiveDate: "2026-07-01",
    source: { id: "src-nalog", title: "Министерство по налогам и сборам", url: "nalog.gov.by", description: "Официальное разъяснение.", checkedAt: "2026-06-01" },
    priority: true, matchesProfile: true,
  },
  {
    id: "law-2", category: "housing", title: "Изменение тарифов на отопление в г. Минск",
    summary: "Тарифы пересмотрены в соответствии с решением Минского горисполкома.",
    whoAffected: "Жители г. Минск, проживающие в квартирах с центральным отоплением.",
    whatChanged: "Тариф пересмотрен на 7%, изменена сетка льгот.",
    whatToDo: "Проверить начисления в первой квитанции после вступления в силу.",
    effectiveDate: "2026-10-01",
    source: { id: "src-minsk", title: "Минский горисполком", url: "minsk.gov.by", description: "Решение горисполкома.", checkedAt: "2026-05-21" },
    priority: false, matchesProfile: true,
  },
  {
    id: "law-3", category: "documents", title: "Электронный паспорт: запуск второй очереди",
    summary: "Возможность получить ID-карту в МФЦ всех областных центров.",
    whoAffected: "Граждане РБ старше 14 лет.",
    whatChanged: "Расширена география пунктов выдачи.",
    whatToDo: "Записаться через портал государственных услуг.",
    effectiveDate: "2026-09-15",
    source: { id: "src-mvd", title: "Министерство внутренних дел", url: "mvd.gov.by", description: "Пресс-релиз.", checkedAt: "2026-05-30" },
    priority: true, matchesProfile: false,
  },
  {
    id: "law-4", category: "family", title: "Расширение списка получателей детских пособий",
    summary: "Включены семьи с приёмными детьми и опекуны.",
    whoAffected: "Опекуны и приёмные семьи.",
    whatChanged: "Добавлены новые категории получателей.",
    whatToDo: "Подать заявление в управление социальной защиты.",
    effectiveDate: "2027-01-01",
    source: { id: "src-mintrud", title: "Министерство труда и социальной защиты", url: "mintrud.gov.by", description: "Постановление №211.", checkedAt: "2026-05-25" },
    priority: false, matchesProfile: false,
  },
];

export const INITIAL_PROFILE: UserProfile = {
  name: "Алексей Иванов",
  email: "aleksei@example.by",
  region: "Минская область",
  city: "Минск",
  district: "Первомайский",
  address: "ул. Кальварийская, 24, кв. 88",
  employment: "Наёмный работник",
  flags: { hasChildren: true, hasCar: true, homeowner: true, tenant: false },
  interests: ["Налоги", "ЖКХ", "Дети"],
  learningProgress: 35,
  achievements: [
    { id: "a1", title: "Первая ситуация создана" },
    { id: "a2", title: "Все документы добавлены" },
  ],
};

export const INITIAL_SETTINGS: Settings = {
  theme: "light",
  lang: "ru",
  notifications: { deadlines: true, documents: true, legal: true, push: false },
  privacy: { maskDocuments: true, quickLogin: false },
  accessibility: { largeFont: false, highContrast: false },
};

export const INITIAL_FAVORITES: string[] = ["child-birth"];

export const LEARNING_CATEGORIES: { id: string; name: string; progress: number }[] = [
  { id: "documents", name: "Документы", progress: 60 },
  { id: "housing", name: "ЖКХ", progress: 40 },
  { id: "taxes", name: "Налоги", progress: 25 },
  { id: "family", name: "Семья", progress: 50 },
  { id: "work", name: "Работа", progress: 30 },
  { id: "health", name: "Здоровье", progress: 15 },
];

export const ACHIEVEMENTS_CATALOG: { id: string; title: string; desc: string; earned: boolean }[] = [
  { id: "first-step", title: "Первый шаг", desc: "Открыта первая карточка проблемы.", earned: true },
  { id: "docs-control", title: "Документы под контролем", desc: "Пройден тест по документам.", earned: true },
  { id: "utility", title: "Разбираюсь в ЖКХ", desc: "Изучены материалы по ЖКХ.", earned: false },
  { id: "law-aware", title: "Закон в курсе", desc: "Прочитан закон-апдейт.", earned: true },
  { id: "moving", title: "Готов к переезду", desc: "Изучен план переезда.", earned: false },
  { id: "calm", title: "Без паники", desc: "Пройден микро-тест без ошибок.", earned: true },
];

export const LEARNING_QUIZ: { topic: string; questions: { q: string; options: string[]; answer: number }[] } = {
  topic: "Потеря паспорта",
  questions: [
    {
      q: "Куда обращаться при потере паспорта?",
      options: ["В банк", "В отдел по гражданству и миграции (ОГиМ)", "В поликлинику"],
      answer: 1,
    },
    {
      q: "Что обычно нужно для восстановления?",
      options: ["Только деньги", "Заявление и фотографии", "Загранпаспорт"],
      answer: 1,
    },
    {
      q: "Когда лучше заявить о потере?",
      options: ["Чем раньше, тем лучше", "Через месяц", "Только если паспорт нужен срочно"],
      answer: 0,
    },
  ],
};

export const INITIAL_UTILITY_ACCOUNTS: UtilityAccount[] = [
  {
    id: "util-1",
    address: "ул. Независимости, 25, кв. 14",
    accountNumber: "ЛС 1024-5567",
    provider: "Минский РСЦ",
    payments: [
      {
        id: "upay-1",
        accountId: "util-1",
        period: "Июнь 2026",
        readingsDate: "",
        paymentDate: "",
        amount: 86.4,
        status: "Ожидает",
        readingsDeadline: "2026-06-25",
        paymentDeadline: "2026-07-10",
        comment: "Передать показания счётчиков воды и электроэнергии",
      },
      {
        id: "upay-2",
        accountId: "util-1",
        period: "Май 2026",
        readingsDate: "2026-05-23",
        paymentDate: "2026-06-05",
        amount: 79.1,
        status: "Оплачено",
        readingsDeadline: "2026-05-25",
        paymentDeadline: "2026-06-10",
        comment: "",
      },
    ],
  },
];

export const INITIAL_TAXES: TaxObligation[] = [
  {
    id: "tax-1",
    title: "Налог на недвижимость",
    userType: "individual",
    deadline: "2026-11-15",
    amount: 184,
    status: "Предстоит",
    period: "2026",
    comment: "Извещение приходит из налоговой инспекции",
    receiptPath: "",
  },
  {
    id: "tax-2",
    title: "Земельный налог",
    userType: "individual",
    deadline: "2026-11-15",
    amount: 62,
    status: "Предстоит",
    period: "2026",
    comment: "",
    receiptPath: "",
  },
];

export const PROBLEMS: Problem[] = [
  {
    id: "p1",
    title: "Потерял паспорт",
    category: "documents",
    shortDescription: "Что делать прямо сейчас, если вы обнаружили пропажу.",
    whatToDoNow: "Как можно скорее обратитесь в ближайшее отделение милиции (РОВД).",
    steps: [
      { id: "ps1", title: "Обратиться в РОВД и написать заявление об утере", checked: false },
      { id: "ps2", title: "Получить справку об обращении", checked: false },
      { id: "ps3", title: "Сфотографироваться (4x5)", checked: false },
      { id: "ps4", title: "Подать документы на новый паспорт", checked: false }
    ],
    documents: ["Справка из милиции", "Фотографии"],
    deadlines: ["Как можно скорее", "Новый паспорт делается до 1 месяца"],
    institutions: ["РОВД по месту жительства", "Отдел по гражданству и миграции"],
    mistakes: ["Откладывать обращение в милицию", "Использовать старые фотографии"]
  },
  {
    id: "p2",
    title: "Нужна медкнижка",
    category: "health",
    shortDescription: "С чего начать оформление санитарной книжки.",
    whatToDoNow: "Уточните у работодателя точный список необходимых врачей.",
    steps: [
      { id: "ps1", title: "Получить направление с работы", checked: false },
      { id: "ps2", title: "Пройти флюорографию", checked: false },
      { id: "ps3", title: "Сдать анализы", checked: false },
      { id: "ps4", title: "Пройти осмотр специалистов", checked: false },
      { id: "ps5", title: "Получить заключение терапевта", checked: false }
    ],
    documents: ["Паспорт", "Направление", "Фотография 3x4"],
    deadlines: ["Обычно занимает от 2 до 5 дней"],
    institutions: ["Поликлиника по месту жительства или частный медцентр"],
    mistakes: ["Сдавать анализы без направления", "Забыть флюорографию"]
  },
  {
    id: "p3",
    title: "Не пришла квитанция ЖКХ",
    category: "housing",
    shortDescription: "Как узнать сумму и оплатить без бумаги.",
    whatToDoNow: "Проверьте сумму через ЕРИП в интернет-банкинге по номеру лицевого счета.",
    steps: [
      { id: "ps1", title: "Зайти в интернет-банкинг", checked: false },
      { id: "ps2", title: "Найти свой адрес или лицевой счет в ЕРИП", checked: false },
      { id: "ps3", title: "Проверить начисленную сумму", checked: false },
      { id: "ps4", title: "Оплатить онлайн", checked: false }
    ],
    documents: ["Номер лицевого счета"],
    deadlines: ["Оплатить нужно до 25 числа месяца"],
    institutions: ["ЕРСЦ", "Ваш банк"],
    mistakes: ["Ждать квитанцию и пропустить срок оплаты"]
  }
];

// Официальные источники (перенесено из Flet OFFICIAL_SOURCES).
export const OFFICIAL_SOURCES: { id: string; title: string; url: string; type: string; description: string; lastChecked: string }[] = [
  { id: "source-pravo", title: "Национальный правовой Интернет-портал Республики Беларусь", url: "https://pravo.by/", type: "law", description: "Официальный источник нормативных правовых актов Республики Беларусь.", lastChecked: "2026-05-24" },
  { id: "source-portal-gov", title: "Единый портал электронных услуг", url: "https://portal.gov.by/", type: "government_portal", description: "Государственный портал административных процедур и электронных услуг.", lastChecked: "2026-05-24" },
  { id: "source-mintrud", title: "Министерство труда и социальной защиты", url: "https://mintrud.gov.by/", type: "ministry", description: "Официальная информация по пособиям, социальной поддержке и трудовым вопросам.", lastChecked: "2026-05-24" },
  { id: "source-nalog", title: "Министерство по налогам и сборам", url: "https://nalog.gov.by/", type: "tax", description: "Официальный источник по налогам, ИП и налоговым сервисам Республики Беларусь.", lastChecked: "2026-05-24" },
  { id: "source-minjust", title: "Министерство юстиции", url: "https://minjust.gov.by/", type: "registry", description: "Официальный источник по ЗАГС, регистрации актов гражданского состояния и правовой информации.", lastChecked: "2026-05-24" },
  { id: "source-mvd", title: "Министерство внутренних дел — ОГиМ", url: "https://mvd.gov.by/ru/structure/departament/departament-grazhdanstva-i-migratsii", type: "government_portal", description: "Информация о паспортах, гражданстве и регистрации по месту жительства.", lastChecked: "2026-05-24" },
  { id: "source-gibdd", title: "ГАИ МВД Республики Беларусь", url: "https://mvd.gov.by/ru/structure/gai", type: "government_portal", description: "Регистрация транспортных средств, техосмотр, водительские удостоверения.", lastChecked: "2026-05-24" },
  { id: "source-court", title: "Верховный Суд Республики Беларусь", url: "https://court.gov.by/", type: "registry", description: "Информация о судебных процедурах, алиментах и семейных спорах.", lastChecked: "2026-05-24" },
  { id: "source-nbki", title: "Государственный реестр недвижимого имущества", url: "https://portal.gov.by/", type: "registry", description: "Сведения о регистрации права собственности на недвижимость.", lastChecked: "2026-05-24" },
];
