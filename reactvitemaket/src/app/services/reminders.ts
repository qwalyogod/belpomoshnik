// Derived deadline reminders (ТЗ §17) — mirrors Flet notification generator.
// Pure: builds AppNotification items from document expiry, ЖКХ payment/reading
// deadlines and tax deadlines. Ids are deterministic so they never duplicate.
import type { AppNotification, Settings, TaxObligation, UserDocument, UtilityAccount } from "../data/types";

const HORIZON = {
  document: 90,
  utilityPayment: 45,
  utilityReadings: 30,
  tax: 60,
};

function daysUntil(iso?: string): number | null {
  if (!iso) return null;
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.ceil((d.getTime() - today.getTime()) / 86400000);
}

function mk(id: string, kind: AppNotification["kind"], title: string, body: string, createdAt: string): AppNotification {
  return { id, kind, title, body, createdAt, read: false };
}

function leftLabel(days: number): string {
  if (days < 0) return "просрочено";
  if (days === 0) return "сегодня";
  return `осталось ${days} дн.`;
}

export function buildReminders(
  documents: UserDocument[],
  utilityAccounts: UtilityAccount[],
  taxes: TaxObligation[],
  settings: Settings,
): AppNotification[] {
  const out: AppNotification[] = [];
  const flags = settings.notifications;

  if (flags.documents) {
    for (const d of documents) {
      const days = daysUntil(d.expiresAt);
      if (days === null || days > HORIZON.document) continue;
      const title = days < 0 ? `Документ просрочен: ${d.title}` : `Скоро истекает: ${d.title}`;
      out.push(mk(`rem-doc-${d.id}`, "document_expiring", title, `Срок действия — ${d.expiresAt} (${leftLabel(days)}).`, d.expiresAt!));
    }
  }

  if (flags.deadlines) {
    for (const acc of utilityAccounts) {
      for (const p of acc.payments) {
        if (p.status === "Оплачено") continue;
        const pay = daysUntil(p.paymentDeadline);
        if (pay !== null && pay <= HORIZON.utilityPayment) {
          out.push(mk(`rem-util-pay-${p.id}`, "task_due", `Оплата ЖКХ · ${p.period}`,
            `${acc.address} · ${p.amount.toFixed(2)} BYN · ${leftLabel(pay)}`, p.paymentDeadline!));
        }
        const readings = daysUntil(p.readingsDeadline);
        if (readings !== null && readings <= HORIZON.utilityReadings && !p.readingsDate) {
          out.push(mk(`rem-util-read-${p.id}`, "task_due", `Передать показания · ${p.period}`,
            `${acc.address} · до ${p.readingsDeadline} (${leftLabel(readings)})`, p.readingsDeadline!));
        }
      }
    }

    for (const t of taxes) {
      if (t.status === "Оплачено") continue;
      const days = daysUntil(t.deadline);
      if (days === null || days > HORIZON.tax) continue;
      out.push(mk(`rem-tax-${t.id}`, "task_due", `Налог · ${t.title}`,
        `${t.amount.toFixed(2)} BYN · ${t.deadline ? `до ${t.deadline} · ` : ""}${leftLabel(days)}`, t.deadline || ""));
    }
  }

  out.sort((a, b) => (a.createdAt || "").localeCompare(b.createdAt || ""));
  return out;
}
