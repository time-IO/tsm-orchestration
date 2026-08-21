import {axiosInstance} from 'boot/axios';
import type {CsvParserUpdate, CsvParserValidationResult} from "src/services/parser_csv/types";
import {createIngestApiService} from "src/services/factoryIngestService";

export function createParserApiService<TPublic, TCreate, TUpdate>(apiPath: string) {

  async function parseFile(settings: CsvParserUpdate, csvFile: File): Promise<CsvParserValidationResult> {
    const payload = new FormData();

    payload.append('settings', JSON.stringify(settings));
    payload.append('file', csvFile);

    try {
      const result = await axiosInstance.post<CsvParserValidationResult>(`${apiPath}parse`, payload)
      return result.data
    } catch {
      return {
        data: [],
        error: "An error occurred trying to parse the file content",
        warnings: [],
        is_valid: false
      }
    }
  }

  return {
    ...createIngestApiService<TPublic, TCreate, TUpdate>(apiPath),
    parseFile
  };
}
