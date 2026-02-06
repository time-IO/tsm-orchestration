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
    async dispatchGetListProject(){
      const response = await API.project.getListProject()
      this.projects = response.data
    },
    async dispatchGetOneProject(id:number):Promise<Project> {
      const response = await API.project.getOneProject(id)
      return response.data
    }
  }
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useIngestExternalApiUbaStore, import.meta.hot));
}
