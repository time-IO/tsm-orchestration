import { Notify, type QNotifyCreateOptions } from 'quasar';

export function notifyError(message: string, options: QNotifyCreateOptions = {}) {
  Notify.create({ position: 'top', type: 'negative', message, ...options });
}
