import { axiosInstance } from 'src/boot/axios';
import type { StaDatastreamRequestParameter } from 'src/services/sta/types';

const apiPath = '/sta/';

async function fetchDatastreams(
  permission_group_id: number,
  parameter: StaDatastreamRequestParameter,
) {
  const {
    pagination: { page, rowsPerPage, sortBy, descending },
    filters = {},
  } = parameter;

  let query = 'Datastreams';

  query += `?$count=true&$select=@iot.id,name,Thing,Sensor,description,@iot.selfLink`;
  query += `&$top=${rowsPerPage}`;
  query += `&$skip=${(page - 1) * rowsPerPage}`;
  query += `&$expand=Thing($select=@iot.id,name)&$expand=Sensor($select=@iot.id,name)`;

  const filterParts: string[] = [];

  if (filters.datastream)
    filterParts.push(
      `substringof('${filters.datastream.toLowerCase()}', tolower(name)) or substringof('${filters.datastream.toLowerCase()}', tolower(@iot.id))`,
    );

  if (filters.thing) {
    const thingFilterParts: string[] = [];
    if (filters.thing['@iot.id'])
      thingFilterParts.push(`Thing/@iot.id eq ${filters.thing['@iot.id']}`);
    if (filters.thing.name)
      thingFilterParts.push(
        `substringof('${filters.thing.name.toLowerCase()}', tolower(Thing/name))`,
      );
    if (thingFilterParts.length) filterParts.push(`(${thingFilterParts.join(' or ')})`);
  }

  if (filterParts.length) query += `&$filter=${filterParts.join(' and ')}`;

  if (sortBy) query += `&$orderby=${sortBy} ${descending ? 'desc' : 'asc'}`;

  const url = `${apiPath}?permission_group_id=${permission_group_id}&q=${encodeURIComponent(query)}`;

  return await axiosInstance.get(url);
}

async function fetchThings(permission_group_id: number, search: string) {
  const query = `Things?$filter=substringof('${search.toLowerCase()}', tolower(name))&$select=@iot.id,name`;
  const url = `${apiPath}?permission_group_id=${permission_group_id}&q=${encodeURIComponent(query)}`;

  return await axiosInstance.get(url);
}

export default {
  fetchDatastreams,
  fetchThings,
};
