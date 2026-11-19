<template>
  <div class="q-pa-lg">
    <div class="row items-center no-wrap q-mb-lg">
      <div class="col text-body1 text-weight-bold">Welcome to the {{ t('appname') }}</div>
    </div>

    <p class="text-caption">
      This page lists the
      <external-link-text :href="STA_OGC_URL" text="OGC SensorThings API (STA)" /> endpoints of
      time.IO. Every endpoint gives standardized access to the datastreams and sensor metadata of
      one project.
    </p>
    <p class="text-caption">
      Use the filters to search endpoints by name or, after login, by one of your ingests. Select an
      endpoint in the list to see its details here.
    </p>

    <q-separator class="q-my-lg" />

    <div class="text-body text-weight-bold q-mt-lg q-mb-sm">
      How to serve data via an STA endpoint
    </div>
    <div class="text-caption">
      <p>
        Data of an ingest is served via the STA endpoint of its project once it is linked with
        metadata in the
        <external-link-text :href="SMS_URL" text="Sensor Management System (SMS)" />.
      </p>

      <p>
        Learn more about the detailed connection process on our
        <external-link-text :href="WIKI_URL" text="Wiki page" />.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import ExternalLinkText from '@/components/common/ExternalLinkText.vue';

const WIKI_URL = 'https://codebase.helmholtz.cloud/ufz-tsm/timeio-support/-/wikis/Metadata';
const STA_OGC_URL = 'https://www.ogc.org/standards/sensorthings/';
const SMS_URL = import.meta.env.SMS_URL;

const { t } = useI18n();
</script>
