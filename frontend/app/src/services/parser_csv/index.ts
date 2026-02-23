import { axiosInstance } from 'src/boot/axios';
import type {
  CsvParserPublic,
  CsvParserCreate,
  CsvParserUpdate,
} from 'src/services/parser_csv/types';

const apiPath = 'parser/csv/';

async function getList(){
  return await axiosInstance.get<CsvParserPublic[]>(apiPath)
}
async function getListbyPermissionGroup(permission_group_id: number){
  return await axiosInstance.get<CsvParserPublic[]>(`${apiPath}?permission_group_id=${permission_group_id}`)
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



export default {
  getList,
  getOne,
  create,
  update,
  deleteOne,
  getListbyPermissionGroup,
};
