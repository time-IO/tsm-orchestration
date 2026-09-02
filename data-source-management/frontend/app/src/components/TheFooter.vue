<template>
  <q-footer
    class="bg-grey-2 text-grey-7"
    bordered
    style="left: 0 !important; width: 100% !important"
  >
    <div class="row items-center q-px-md q-py-sm" style="width: 100%">
      <div class="col-auto row items-center q-gutter-sm">
        <a href="https://www.ufz.de" target="_blank">
          <img :src="ufzLogoSrc" alt="UFZ" style="height: 50px; opacity: 0.85" />
        </a>

        <a href="https://www.ufz.de/index.php?de=45348" target="_blank">
          <img :src="rdmLogoSrc" alt="RDM" style="height: 50px; opacity: 0.85" />
        </a>
      </div>

      <div class="col-grow row justify-center q-gutter-x-md">
        <div class="row items-center q-gutter-x-sm">
          <router-link
            :to="{ name: 'legal_notice' }"
            class="text-grey-8"
            style="text-decoration: none"
          >
            Legal Notice
          </router-link>
          <span class="text-grey-5">|</span>
          <a
            href="https://www.ufz.de/index.php?en=44326"
            target="_blank"
            class="text-grey-8"
            style="text-decoration: none"
          >
            Privacy Policy
          </a>
          <span class="text-grey-5">|</span>
          <router-link
            :to="{ name: 'terms_of_use' }"
            class="text-grey-8"
            style="text-decoration: none"
          >
            Terms of Use
          </router-link>
        </div>
      </div>

      <div class="col-auto row q-gutter-x-md">
        <a
          href="https://codebase.helmholtz.cloud/ufz-tsm"
          target="_blank"
          class="row items-center q-gutter-xs text-grey-7"
          style="text-decoration: none"
          title="time.IO Repository"
        >
          <q-icon name="lab la-gitlab" :size="$q.screen.lt.md ? '1.2rem' : '1.5rem'" color="grey" />
        </a>
        <a
          :href="apiDocsHref"
          target="_blank"
          class="row items-center q-gutter-xs text-grey-7"
          style="text-decoration: none"
          title="time.IO API"
        >
          <q-icon name="mdi-api" :size="$q.screen.lt.md ? '1.2rem' : '1.5rem'" color="grey" />
        </a>
        <a
          href="mailto:rdm-tsm@ufz.de"
          target="_blank"
          class="row items-center q-gutter-xs text-grey-7"
          style="text-decoration: none"
          title="Request Support"
        >
          <q-icon
            name="las la-envelope-open"
            :size="$q.screen.lt.md ? '1.2rem' : '1.5rem'"
            color="grey"
          />
        </a>

        <a
          href="https://codebase.helmholtz.cloud/ufz-tsm/timeio-support"
          target="_blank"
          class="row items-center q-gutter-xs text-grey-7"
          style="text-decoration: none"
          title="time.IO Wiki"
        >
          <q-icon name="auto_stories" :size="$q.screen.lt.md ? '1.2rem' : '1.5rem'" color="grey" />
        </a>
      </div>
    </div>
  </q-footer>
</template>

<script setup lang="ts">
import { publicAsset } from 'src/utils/public_asset';

const ufzLogoSrc = publicAsset('images/UFZ_Logo_RGB_EN.png');
const rdmLogoSrc = publicAsset('images/259253_RDM_subline_fullcolor_rgb.png');
const apiDocsHref = publicAsset('api/docs');
</script>
