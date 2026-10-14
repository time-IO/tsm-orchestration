import { useCsvParserStore } from '@/stores/parserCsvStore';
import { useJsonParserStore } from '@/stores/parserJsonStore';
import { useSoilcanParserStore } from '@/stores/parserSoilcanStore';

export function useParserStoreByType() {
  const csvParserStore = useCsvParserStore();
  const jsonParserStore = useJsonParserStore();
  const soilcanParserStore = useSoilcanParserStore();

  const parserStoresByType: Record<
    string,
    typeof csvParserStore | typeof jsonParserStore | typeof soilcanParserStore
  > = {
    csv: csvParserStore,
    json: jsonParserStore,
    soilcan: soilcanParserStore,
  };

  return { parserStoresByType };
}
