import { axiosInstance } from 'boot/axios';
import type { ParserEncoding } from 'src/services/parser_encoding/types';

const apiPath = 'parser_encoding/';

async function getList() {
  return await axiosInstance.get<ParserEncoding[]>(apiPath);
}

export default {
  getList,
};
