<template>
  <q-page>
    <q-layout view="lHh lpR fFf">
      <div class="hero-container" style="position: relative; height: 500px; overflow: hidden">
        <img
          :src="heroImageSrc"
          class="hero-mirror"
          style="
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: 10% 80%;
            display: block;
          "
        />

        <!-- UFZ Logo oben links -->
        <div class="absolute-top-left q-pa-md" style="width: 300px; z-index: 10">
          <img :src="ufzLogoSrc" style="width: 100%; display: block" />
        </div>

        <!-- TimeIO Logo -->
        <div class="absolute" style="top: 3%; right: 6%; width: 30%">
          <img :src="timeIoDarkLogoSrc" style="width: 100%; display: block" />
        </div>
      </div>

      <div
        class="row q-col-gutter-md q-pa-md"
        style="
          width: 90%;
          max-width: 1500px;
          position: relative;
          margin-top: -12em;
          margin-left: auto;
          margin-right: auto;
          z-index: 1;
          padding: 0 3em;
        "
      >
        <div class="col-12">
          <div class="row justify-center q-mb-xs" style="font-weight: bold">
            <div class="col q-px-sm text-center" v-for="card in cards" :key="card.label + '-stat'">
              <div class="text-h5 text-amber-13" style="font-weight: bold; font-size: 1.7em">
                {{ card.count }}
              </div>
              <div
                class="text-h5 text-amber-13"
                style="font-size: 100%; font-weight: bold; font-size: 1.2em"
              >
                {{ card.label }}
              </div>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-6 col-lg-3 q-px-sm" v-for="card in cards" :key="card.label">
          <div style="display: flex; flex-direction: column; height: 100%">
            <div
              class="row justify-center q-mb-sm"
              style="flex-direction: column; align-items: center"
            ></div>

            <q-card
              dark
              class="bg-light-blue-8 text-white shadow-1"
              style="flex: 1; display: flex; flex-direction: column; min-height: 150px"
            >
              <q-card-section style="flex: 1">
                <div class="text-h6">{{ card.title }}</div>
                <div class="text-subtitle2">{{ card.subtitle }}</div>
              </q-card-section>
              <q-separator dark inset />
              <q-card-section class="bg-white text-black" style="flex: 1">
                {{ card.description }}
              </q-card-section>
            </q-card>
          </div>
        </div>

        <div class="row justify-center q-pa-md">
          <div style="width: 80%; max-width: 1500px; padding: 0 3em">
            <q-card class="bg-light-blue-8 text-white shadow-1">
              <q-card-section>
                <div class="text-h6">Data Source Management - Introduction</div>
                <div class="text-subtitle2">Getting Started</div>
              </q-card-section>
              <q-separator dark inset />
              <q-card-section class="bg-white text-black">
                <p>
                  Data Source Management (DSM) is a centralized platform for managing time series
                  data ingestion from various external sources. Configure data ingestion from APIs
                  (Bosch, DWD, The Things Network, T-Systems, UBA), MQTT brokers and SFTP servers.
                </p>
                <p>
                  Organize your data using Permission Groups to control access. Apply Quality
                  Control Settings to validate and filter your time series data. Use parsers to
                  process batch data uploads.
                </p>
                <p>
                  For detailed documentation and guides, visit the
                  <a
                    href="https://codebase.helmholtz.cloud/ufz-tsm/timeio-support/-/wikis/"
                    target="_blank"
                    class="text-primary"
                    style="text-decoration: none"
                    >TimeIO Wiki</a
                  >.
                </p>
              </q-card-section>
            </q-card>

            <q-card flat class="bg-transparent">
              <q-card-section>
                <!-- Bild links -->
                <img
                  :src="timeIoLogoSrc"
                  style="float: left; width: 150px; margin: 0 1.5em 1em 0; display: block"
                />
                <p class="text-justify" style="line-height: 1.6">
                  time.IO provides the infrastructure for storing and managing time series data. It
                  supports the entire lifecycle of time series data, providing efficient data
                  transfer and storage, real-time data visualisation using
                  <a
                    href="https://en.wikipedia.org/wiki/Grafana"
                    target="_blank"
                    style="color: #519ba5; text-decoration: none"
                    >Grafana</a
                  >, and integrated data analysis and quality control with
                  <a
                    href="https://rdm-software.pages.ufz.de/saqc/"
                    target="_blank"
                    style="color: #519ba5; text-decoration: none"
                  >
                    SaQC </a
                  >. The container-based deployment model facilitates easy integration and
                  scalability within existing IT infrastructures, including seamless connection to
                  geospatial infrastructures such as spatial.IO for advanced spatial data analyses.
                  time.IO also links to the
                  <a
                    href="https://web.app.ufz.de/sms/"
                    target="_blank"
                    style="color: #519ba5; text-decoration: none"
                  >
                    SMS
                  </a>
                  for consistent and standardised metadata management, ensuring a cohesive data
                  management process. For data access, the standardised OGC
                  <a
                    href="https://en.wikipedia.org/wiki/SensorThings_API "
                    target="_blank"
                    style="color: #519ba5; text-decoration: none"
                  >
                    SensorThings API
                  </a>
                  is used.
                  <!--                    and utilises the FROST-Server as a reference implementation for the OGC STA-->
                  <!--                    interface.-->
                </p>
              </q-card-section>
            </q-card>

            <div v-if="!authStore.isAuthenticated" class="row justify-center q-mt-md q-mb-xl">
              <q-btn
                unelevated
                no-caps
                icon="login"
                label="Login"
                color="light-blue-8"
                text-color="white"
                size="lg"
                @click="authStore.login()"
              />
            </div>
          </div>
        </div>
      </div>
    </q-layout>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useQuasar } from 'quasar';
import { useUsageStatisticsStore } from 'src/stores/usageStatisticsStore';
import { publicAsset } from 'src/utils/public_asset';
import { useAuthStore } from 'src/stores/authStore';

const authStore = useAuthStore();

const heroImageSrc = publicAsset('images/_DCS9779_8bit-JPEG 3000px.jpg');
const ufzLogoSrc = publicAsset('images/UFZ_Logo_RGB_EN_white.png');
const timeIoDarkLogoSrc = publicAsset('images/ufz-timeio_logo_dark.svg');
const timeIoLogoSrc = publicAsset('images/LogoTimeIO.png');

const $q = useQuasar();
const usageStatisticsStore = useUsageStatisticsStore();

const projectDescription = 'Permission Groups to organize projects and manage access control.';
const dataSourcesDescription =
  'Active Ingest Configurations for external APIs, MQTT, SFTP, and S3.';
const usersDescription = 'Registered Users with access to the time series management system.';
const qcSettingsDescription = 'Quality Control Settings to validate and filter time series data.';

const cards = computed(() => [
  {
    label: 'Projects',
    count: usageStatisticsStore.counts?.projects ?? '-',
    title: 'Projects',
    subtitle: 'Permission Groups',
    description: projectDescription,
  },
  {
    label: 'Data Ingests',
    count: usageStatisticsStore.counts?.ingests ?? '-',
    title: 'Data Ingests',
    subtitle: 'Ingest Configurations',
    description: dataSourcesDescription,
  },
  {
    label: 'Users',
    count: usageStatisticsStore.counts?.users ?? '-',
    title: 'Users',
    subtitle: 'Registered Users',
    description: usersDescription,
  },
  {
    label: 'QC Settings',
    count: usageStatisticsStore.counts?.quality_control_setting ?? '-',
    title: 'QC Settings',
    subtitle: 'Quality Control Configurations',
    description: qcSettingsDescription,
  },
]);

onMounted(async () => {
  try {
    await usageStatisticsStore.dispatchGetUsageStatistics();
  } catch {
    $q.notify({
      type: 'negative',
      message: 'Failed to load usage statistics',
    });
  }
});
</script>

<style scoped>
.hero-mirror {
  transform: scaleX(-1);
}
</style>
