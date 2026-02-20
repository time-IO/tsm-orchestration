import { axiosInstance } from 'src/boot/axios';
import type {
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
  CsvParserTimestampColumnUpdate,
  CsvParserTimestampColumnPublic,
} from 'src/services/parser_csv/types';

const apiPath = 'parser/csv/';

async function getList(){
  return await axiosInstance.get<CsvParserPublic[]>(apiPath)
}

async function getOne(id: number){
  return await axiosInstance.get<CsvParserPublic>(`${apiPath}${id}`)
}

async function create(input: CsvParserCreate){
  return await axiosInstance.post<CsvParserPublic>(apiPath, input)
}

async function update(id:number, input: CsvParserUpdate){
  return await axiosInstance.patch<CsvParserPublic>(`${apiPath}${id}`, input)
}

async function deleteOne(id: number){
  return await axiosInstance.delete(`${apiPath}${id}`)
}

const timestampColumnPath = `${apiPath}timestampcolumn/`;
async function updateTimestampColumn(id: number, input: CsvParserTimestampColumnUpdate)
{
  return await axiosInstance.put<CsvParserTimestampColumnPublic>(
    `${timestampColumnPath}${id}`,
    input,
  );
}
async function deleteTimestampColumn(id: number) {
  return await axiosInstance.delete(`${timestampColumnPath}${id}`);
}


export default {
  getList,
  getOne,
  create,
  update,
  deleteOne,
  updateTimestampColumn,
  deleteTimestampColumn
};
