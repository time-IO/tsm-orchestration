import { axiosInstance } from 'src/boot/axios';
import type { JournalQuery, JournalResponse } from 'src/services/ingest_journal/types';

const apiPath = '/ingest';

async function fetchJournal(ingestId: number, query: JournalQuery = {}) {
  const params = new URLSearchParams();
  if (query.limit != null) params.set('limit', String(query.limit));
  if (query.level) params.set('level', query.level);
  if (query.datetime_from) params.set('datetime_from', query.datetime_from);
  if (query.datetime_to) params.set('datetime_to', query.datetime_to);

  const queryString = params.toString();
  const url = `${apiPath}/${ingestId}/journal${queryString ? `?${queryString}` : ''}`;

  return await axiosInstance.get<JournalResponse>(url);
}

export default {
  fetchJournal,
};
