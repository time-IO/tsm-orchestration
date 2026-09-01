import { axiosInstance } from 'boot/axios';
import { createIngestApiService } from 'src/services/factoryIngestService';
import type {
  ParserPayloadCreate,
  ParserPayloadPublic,
  ParserPayloadUpdate,
  ParsingResult,
} from 'src/services/types';

export function createParserApiService<
  TPublic extends ParserPayloadPublic,
  TCreate extends ParserPayloadCreate,
  TUpdate extends ParserPayloadUpdate,
  TParse,
>(apiPath: string) {
  async function parseFile(settings: TParse, csvFile: File): Promise<ParsingResult> {
    const payload = new FormData();

    payload.append('settings', JSON.stringify(settings));
    payload.append('file', csvFile);

    try {
      const result = await axiosInstance.post<ParsingResult>(`${apiPath}parse`, payload);
      return result.data;
    } catch {
      return {
        data: [],
        error: 'An error occurred trying to parse the file content',
        warnings: [],
        is_valid: false,
      };
    }
  }

  return {
    ...createIngestApiService<TPublic, TCreate, TUpdate>(apiPath),
    parseFile,
  };
}
