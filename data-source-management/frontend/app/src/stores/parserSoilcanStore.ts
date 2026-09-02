import { acceptHMRUpdate } from 'pinia';
import type {
  SoilcanParserCreate,
  SoilcanParserPublic,
  SoilcanParserUpdate,
} from 'src/services/parser_soilcan/types';
import { API } from 'src/services';
import { createIngestStore } from 'stores/factoryIngestStore';

export const useSoilcanParserStore = createIngestStore<
  SoilcanParserPublic,
  SoilcanParserCreate,
  SoilcanParserUpdate
>('soilcanParserStore', API.soilcanParser);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useSoilcanParserStore, import.meta.hot));
}
