import {API} from "src/services";
import {acceptHMRUpdate, defineStore} from "pinia";
import type {Project} from "src/services/project/types";
import {useIngestExternalApiUbaStore} from "stores/ingestExternalApiUbaStore";

export const useProjectStore = defineStore('projectStore', {

  state: () => ({
    projects: [] as Project[]
  }),

  getters:{},

  actions: {
    async dispatchGetList(){
      const response = await API.project.getList()
      this.projects = response.data
    },
    async dispatchGetOne(id:number):Promise<Project> {
      const response = await API.project.getOne(id)
      return response.data
    }
  }
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiUbaStore, import.meta.hot));
}
