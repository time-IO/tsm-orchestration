<template>
  <svg
    :viewBox="`${-PAD} ${-PAD} ${WIDTH + 2 * PAD} ${HEIGHT + 2 * PAD}`"
    class="ingest-data-flow"
    :style="{ aspectRatio: `${WIDTH + 2 * PAD} / ${HEIGHT + 2 * PAD}` }"
    role="img"
    :aria-label="flow.description"
  >
    <title>{{ flow.description }}</title>
    <defs>
      <marker
        v-for="kind in MARKER_KINDS"
        :key="kind"
        :id="`${uid}-arrow-${kind}`"
        :class="`flow-marker--${kind}`"
        viewBox="0 0 10 10"
        refX="9"
        refY="5"
        markerWidth="5"
        markerHeight="5"
        orient="auto-start-reverse"
      >
        <path d="M0,0 L10,5 L0,10 z" />
      </marker>
    </defs>

    <!-- area of time.IO's internal systems; its left edge runs through the time.IO server -->
    <rect
      v-if="internalArea"
      :x="internalArea.x"
      :y="internalArea.y"
      :width="internalArea.width"
      :height="internalArea.height"
      rx="8"
      class="flow-internal-area"
    />

    <!-- connections -->
    <g v-for="edge in edges" :key="edge.key" :class="`flow-edge flow-edge--${edge.kind}`">
      <line
        :x1="edge.x1"
        :y1="edge.y1"
        :x2="edge.x2"
        :y2="edge.y2"
        :class="{ 'flow-edge--active': edge.active }"
        :marker-end="`url(#${uid}-arrow-${edge.kind})`"
      />
      <text
        :transform="`translate(${edge.labelX}, ${edge.labelY}) rotate(${edge.labelAngle})`"
        :y="edge.labelShift"
        class="flow-edge-label"
      >
        {{ edge.label }}
      </text>
    </g>

    <!-- nodes -->
    <g
      v-for="node in displayNodes"
      :key="node.id"
      :transform="`translate(${node.x}, ${node.y})`"
      :class="node.external ? 'flow-node--external' : 'flow-node--internal'"
    >
      <template v-if="node.kind === 'timeio'">
        <!-- time.IO server: server tower with the monochrome time.IO logo -->
        <rect x="-17" y="-22" width="34" height="44" rx="4" class="flow-server-body" />
        <g transform="translate(-13, -19) scale(0.406) translate(-21.6, -24.4)" class="flow-logo">
          <path :d="LOGO_HALF_DISC" />
          <path :d="LOGO_MARK" />
        </g>
        <rect x="-12" y="3" width="24" height="5" rx="1.5" class="flow-server-slot" />
        <rect x="-12" y="11" width="24" height="5" rx="1.5" class="flow-server-slot" />
        <circle
          cx="8"
          cy="5.5"
          r="1.3"
          class="flow-server-led"
          :class="{ 'flow-server-led--on': ledActive }"
        />
        <circle
          cx="8"
          cy="13.5"
          r="1.3"
          class="flow-server-led"
          :class="{ 'flow-server-led--on': ledActive }"
        />

        <!-- schedule -->
        <g v-if="flow.schedule" transform="translate(19, -21)" class="flow-schedule">
          <title>Runs on a schedule</title>
          <circle
            v-if="!reducedMotion && schedulePulse < 1"
            r="8"
            class="flow-schedule-pulse"
            :transform="`scale(${1 + schedulePulse})`"
            :opacity="1 - schedulePulse"
          />
          <circle r="8" class="flow-schedule-face" />
          <line x1="0" y1="0" x2="0" y2="-3.5" class="flow-schedule-hand" />
          <line
            x1="0"
            y1="0"
            x2="0"
            y2="-5.5"
            class="flow-schedule-hand"
            :transform="`rotate(${reducedMotion ? 90 : phase * 360})`"
          />
        </g>
      </template>
      <g v-else transform="translate(-14, -14) scale(1.1667)">
        <path :d="node.icon" class="flow-icon" />
      </g>

      <!-- clear area behind the time.IO label, flush with the bottom of the server -->
      <rect
        v-if="node.kind === 'timeio'"
        :x="-TIMEIO_LABEL_BOX.width / 2"
        :y="SERVER_BOTTOM"
        :width="TIMEIO_LABEL_BOX.width"
        :height="TIMEIO_LABEL_BOX.height"
        rx="3"
        class="flow-label-box"
      />
      <text :y="node.labelOffset" class="flow-node-label">
        <title v-if="node.fullLabel !== node.label">{{ node.fullLabel }}</title>
        {{ node.label }}
      </text>
    </g>

    <!-- moving packets -->
    <template v-if="!reducedMotion">
      <g
        v-for="packet in packets"
        :key="packet.key"
        :transform="`translate(${packet.x}, ${packet.y})`"
        :opacity="packet.opacity"
        :class="`flow-packet flow-packet--${packet.kind}`"
      >
        <path
          v-if="packet.shape === 'file'"
          :d="mdiFileDocument"
          transform="translate(-6, -6) scale(0.5)"
        />
        <circle v-else-if="packet.shape === 'request'" r="3.5" class="flow-packet-ring" />
        <circle v-else r="3.5" />
      </g>
    </template>
  </svg>
</template>

<script setup lang="ts">
import { computed, useId } from 'vue';
import {
  mdiAccessPoint,
  mdiApi,
  mdiBucketOutline,
  mdiChip,
  mdiDatabase,
  mdiFileDocument,
  mdiLaptop,
  mdiServerNetwork,
} from '@quasar/extras/mdi-v7';
import { useSyncedLoop } from '@/composables/useSyncedLoop';
import type { IngestFlowType } from '@/components/ingestDataFlow';

const props = withDefaults(
  defineProps<{
    type: IngestFlowType;
    /** Overrides the label of the external source node, e.g. the selected API. */
    sourceLabel?: string | undefined;
    /** Draw the area that groups time.IO's internal systems (storage, database). */
    showInternalArea?: boolean;
  }>(),
  { sourceLabel: undefined, showInternalArea: true },
);

type EdgeKind = 'data' | 'request' | 'subscribe';
type PacketShape = 'file' | 'message' | 'request';

interface FlowNode {
  id: string;
  kind: 'timeio' | 'icon';
  icon?: string;
  label: string;
  external?: boolean;
  x: number;
  y: number;
}

interface FlowEdge {
  from: string;
  to: string;
  kind: EdgeKind;
  label: string;
  /** Moving packet and its time window as fractions of the shared loop. */
  packet?: PacketShape;
  window?: [number, number];
  /** Vertical shift, used to draw two parallel connections. */
  offset?: number;
  labelBelow?: boolean;
}

interface Flow {
  description: string;
  schedule?: boolean;
  nodes: FlowNode[];
  edges: FlowEdge[];
}

const WIDTH = 520;
const HEIGHT = 150;
/** Margin around the drawing so labels and the schedule pulse stay inside. */
const PAD = 12;
/** Longer source labels (e.g. API names) are shortened to stay inside the drawing. */
const MAX_LABEL = 20;
const MARKER_KINDS: EdgeKind[] = ['data', 'request', 'subscribe'];

// Shared time slots so all flows move in the same rhythm.
const SLOT_1: [number, number] = [0.03, 0.22];
const SLOT_2: [number, number] = [0.28, 0.47];
const SLOT_3: [number, number] = [0.53, 0.72];
const SLOT_4: [number, number] = [0.78, 0.97];

// Monochrome time.IO logo mark (from public/logos/timeio.svg, without lettering).
const LOGO_HALF_DISC = 'M38.35,60.56c-9.26,0-16.76-7.5-16.76-16.76s7.5-16.76,16.76-16.76v33.52Z';
const LOGO_MARK =
  'M79.74,36.06c-2.56,0-4.72,1.7-5.42,4.03h-14.34c-.79-8.75-8.16-15.63-17.12-15.63-9.48,0-17.19,7.71-17.19,17.36,0,3.85,1.25,7.5,3.61,10.54,3.28,4.23,8.23,6.65,13.58,6.65,9.01,0,16.42-6.97,17.13-15.8h14.29c.66,2.4,2.85,4.17,5.45,4.17,3.12,0,5.66-2.54,5.66-5.66s-2.54-5.66-5.66-5.66Z' +
  'M56.86,43.38c-.78,7.03-6.75,12.52-13.99,12.52-4.38,0-8.43-1.99-11.12-5.45-1.93-2.49-2.95-5.47-2.95-8.8,0-7.76,6.31-14.08,14.08-14.08,7.29,0,13.31,5.58,14.01,12.69h-14.01v3.11h13.99Z' +
  'M79.74,44.27c-1.4,0-2.55-1.14-2.55-2.55s1.14-2.54,2.55-2.54,2.55,1.14,2.55,2.54-1.14,2.55-2.55,2.55Z';

/** Bottom edge of the time.IO server body, relative to its centre. */
const SERVER_BOTTOM = 22;
/** Clear box behind the time.IO label; `baseline` is measured from its top edge. */
const TIMEIO_LABEL_BOX = { width: 52, height: 18, baseline: 13 };

const ROW = 72;
const STACK_TOP = 30;
const STACK_BOTTOM = 112;

function timeio(x = 260): FlowNode {
  return { id: 'timeio', kind: 'timeio', label: 'time.IO', x, y: ROW };
}

const bucket: FlowNode = {
  id: 'bucket',
  kind: 'icon',
  icon: mdiBucketOutline,
  label: 'File storage',
  x: 460,
  y: STACK_TOP,
};
const databaseStacked: FlowNode = {
  id: 'db',
  kind: 'icon',
  icon: mdiDatabase,
  label: 'Database',
  x: 460,
  y: STACK_BOTTOM,
};
const databaseRow: FlowNode = { ...databaseStacked, y: ROW };

const FLOWS: Record<IngestFlowType, Flow> = {
  sftp: {
    description:
      'A logger uploads files to time.IO via SFTP or S3. time.IO stores them in an object storage bucket and parses them into the database.',
    nodes: [
      {
        id: 'src',
        kind: 'icon',
        icon: mdiChip,
        label: 'Data logger',
        external: true,
        x: 60,
        y: ROW,
      },
      timeio(),
      bucket,
      databaseStacked,
    ],
    edges: [
      { from: 'src', to: 'timeio', kind: 'data', label: 'upload', packet: 'file', window: SLOT_1 },
      {
        from: 'timeio',
        to: 'bucket',
        kind: 'data',
        label: 'keep files',
        packet: 'file',
        window: SLOT_2,
      },
      {
        from: 'timeio',
        to: 'db',
        kind: 'data',
        label: 'import',
        packet: 'message',
        window: SLOT_3,
        labelBelow: true,
      },
    ],
  },
  ext_sftp: {
    description:
      'On a schedule, time.IO fetches new files from an external FTP/SFTP server, stores them in an object storage bucket and parses them into the database.',
    schedule: true,
    nodes: [
      {
        id: 'src',
        kind: 'icon',
        icon: mdiServerNetwork,
        label: 'Your file server',
        external: true,
        x: 60,
        y: ROW,
      },
      timeio(),
      bucket,
      databaseStacked,
    ],
    edges: [
      {
        from: 'timeio',
        to: 'src',
        kind: 'request',
        label: 'check',
        packet: 'request',
        window: SLOT_1,
        offset: -8,
      },
      {
        from: 'src',
        to: 'timeio',
        kind: 'data',
        label: 'new files',
        packet: 'file',
        window: SLOT_2,
        offset: 8,
        labelBelow: true,
      },
      {
        from: 'timeio',
        to: 'bucket',
        kind: 'data',
        label: 'keep files',
        packet: 'file',
        window: SLOT_3,
      },
      {
        from: 'timeio',
        to: 'db',
        kind: 'data',
        label: 'import',
        packet: 'message',
        window: SLOT_4,
        labelBelow: true,
      },
    ],
  },
  mqtt: {
    description:
      'A device publishes messages to the time.IO MQTT broker. Each message is parsed into the database.',
    nodes: [
      {
        id: 'src',
        kind: 'icon',
        icon: mdiAccessPoint,
        label: 'Device',
        external: true,
        x: 60,
        y: ROW,
      },
      timeio(),
      databaseRow,
    ],
    edges: [
      {
        from: 'src',
        to: 'timeio',
        kind: 'data',
        label: 'send',
        packet: 'message',
        window: SLOT_1,
      },
      {
        from: 'timeio',
        to: 'db',
        kind: 'data',
        label: 'import',
        packet: 'message',
        window: SLOT_2,
      },
    ],
  },
  ext_mqtt: {
    description:
      'A device publishes messages to an external MQTT broker. time.IO subscribes to the topic and parses each message into the database.',
    nodes: [
      {
        id: 'src',
        kind: 'icon',
        icon: mdiAccessPoint,
        label: 'Device',
        external: true,
        x: 50,
        y: ROW,
      },
      {
        id: 'broker',
        kind: 'icon',
        icon: mdiServerNetwork,
        label: 'Your MQTT broker',
        external: true,
        x: 190,
        y: ROW,
      },
      timeio(330),
      { ...databaseRow, x: 470 },
    ],
    edges: [
      {
        from: 'src',
        to: 'broker',
        kind: 'data',
        label: 'send',
        packet: 'message',
        window: SLOT_1,
      },
      {
        from: 'broker',
        to: 'timeio',
        kind: 'data',
        label: 'forward',
        packet: 'message',
        window: SLOT_2,
      },
      {
        from: 'timeio',
        to: 'db',
        kind: 'data',
        label: 'import',
        packet: 'message',
        window: SLOT_3,
      },
    ],
  },
  http: {
    description:
      'A client posts files to a time.IO HTTP endpoint. time.IO stores them in an object storage bucket and parses them into the database.',
    nodes: [
      {
        id: 'src',
        kind: 'icon',
        icon: mdiLaptop,
        label: 'Your device',
        external: true,
        x: 60,
        y: ROW,
      },
      timeio(),
      bucket,
      databaseStacked,
    ],
    edges: [
      { from: 'src', to: 'timeio', kind: 'data', label: 'send', packet: 'file', window: SLOT_1 },
      {
        from: 'timeio',
        to: 'bucket',
        kind: 'data',
        label: 'keep files',
        packet: 'file',
        window: SLOT_2,
      },
      {
        from: 'timeio',
        to: 'db',
        kind: 'data',
        label: 'import',
        packet: 'message',
        window: SLOT_3,
        labelBelow: true,
      },
    ],
  },
  ext_api: {
    description:
      'On a schedule, time.IO requests new data from an external web API and stores the observations in the database.',
    schedule: true,
    nodes: [
      {
        id: 'src',
        kind: 'icon',
        icon: mdiApi,
        label: 'Web API',
        external: true,
        x: 60,
        y: ROW,
      },
      timeio(),
      databaseRow,
    ],
    edges: [
      {
        from: 'timeio',
        to: 'src',
        kind: 'request',
        label: 'request',
        packet: 'request',
        window: SLOT_1,
        offset: -8,
      },
      {
        from: 'src',
        to: 'timeio',
        kind: 'data',
        label: 'data',
        packet: 'message',
        window: SLOT_2,
        offset: 8,
        labelBelow: true,
      },
      {
        from: 'timeio',
        to: 'db',
        kind: 'data',
        label: 'import',
        packet: 'message',
        window: SLOT_3,
      },
    ],
  },
};

const uid = useId();
const { phase, reducedMotion } = useSyncedLoop();

const flow = computed(() => FLOWS[props.type]);

/** Spans from the centre of the time.IO server to the right edge of the drawing. */
const internalArea = computed(() => {
  if (!props.showInternalArea) return null;
  const server = flow.value.nodes.find((node) => node.kind === 'timeio');
  if (!server) return null;
  return { x: server.x, y: -6, width: WIDTH + 6 - server.x, height: HEIGHT + 12 };
});

/** Distance between a node centre and the start/end of a connection. */
function nodeRadius(node: FlowNode) {
  return node.kind === 'timeio' ? 30 : 26;
}

const nodes = computed(() =>
  flow.value.nodes.map((node) => ({
    ...node,
    fullLabel: node.id === 'src' && props.sourceLabel ? props.sourceLabel : node.label,
  })),
);

const displayNodes = computed(() =>
  nodes.value.map((node) => ({
    ...node,
    label: shorten(node.fullLabel),
    labelOffset: node.kind === 'timeio' ? SERVER_BOTTOM + TIMEIO_LABEL_BOX.baseline : 28,
  })),
);

function shorten(label: string) {
  return label.length > MAX_LABEL ? `${label.slice(0, MAX_LABEL - 1).trimEnd()}…` : label;
}

/** Angle in degrees for text along a line, flipped so the text is never upside down. */
function readableAngle(radians: number) {
  const degrees = (radians * 180) / Math.PI;
  if (degrees > 90) return degrees - 180;
  if (degrees < -90) return degrees + 180;
  return degrees;
}

function easeInOut(t: number) {
  return t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
}

/** Progress of an edge's packet in [0, 1], or null outside its time window. */
function progress(edge: FlowEdge): number | null {
  if (!edge.window || reducedMotion.value) return null;
  const [start, end] = edge.window;
  if (phase.value < start || phase.value > end) return null;
  return (phase.value - start) / (end - start);
}

const geometry = computed(() =>
  flow.value.edges.map((edge, index) => {
    const from = flow.value.nodes.find((n) => n.id === edge.from)!;
    const to = flow.value.nodes.find((n) => n.id === edge.to)!;
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const length = Math.hypot(dx, dy);
    const ux = dx / length;
    const uy = dy / length;
    const offset = edge.offset ?? 0;
    const x1 = from.x + ux * nodeRadius(from);
    const y1 = from.y + uy * nodeRadius(from) + offset;
    const x2 = to.x - ux * nodeRadius(to);
    const y2 = to.y - uy * nodeRadius(to) + offset;
    return {
      edge,
      key: `${edge.from}-${edge.to}-${index}`,
      x1,
      y1,
      x2,
      y2,
      labelX: (x1 + x2) / 2,
      labelY: (y1 + y2) / 2,
      labelAngle: readableAngle(Math.atan2(y2 - y1, x2 - x1)),
      /** Distance from the line, perpendicular to it (text sits above or below). */
      labelShift: edge.labelBelow ? 11 : -5,
    };
  }),
);

const edges = computed(() =>
  geometry.value.map((g) => ({
    key: g.key,
    kind: g.edge.kind,
    label: g.edge.label,
    x1: g.x1,
    y1: g.y1,
    x2: g.x2,
    y2: g.y2,
    labelX: g.labelX,
    labelY: g.labelY,
    labelAngle: g.labelAngle,
    labelShift: g.labelShift,
    active: g.edge.kind === 'subscribe' || progress(g.edge) !== null,
  })),
);

const packets = computed(() =>
  geometry.value.flatMap((g) => {
    const t = progress(g.edge);
    if (t === null || !g.edge.packet) return [];
    const eased = easeInOut(t);
    return [
      {
        key: g.key,
        kind: g.edge.kind,
        shape: g.edge.packet,
        x: g.x1 + (g.x2 - g.x1) * eased,
        y: g.y1 + (g.y2 - g.y1) * eased,
        opacity: Math.min(1, t * 8, (1 - t) * 8),
      },
    ];
  }),
);

/** The server LEDs light up while data arrives at or leaves time.IO. */
const ledActive = computed(() =>
  flow.value.edges.some(
    (edge) =>
      edge.kind === 'data' &&
      (edge.from === 'timeio' || edge.to === 'timeio') &&
      progress(edge) !== null,
  ),
);

/** Expanding ring when the schedule fires at the start of each loop. */
const schedulePulse = computed(() => Math.min(1, phase.value / 0.12));
</script>

<style scoped lang="scss">
// Palette: blue (time.IO, data), black/white (text, external parts, requests), white.
.ingest-data-flow {
  --flow-bg: #fff;
  --flow-fg: #000;
  --flow-blue: var(--q-primary);

  display: block;
  width: 100%;
  max-width: 680px;
  height: auto;
  margin: 0 auto;
  overflow: hidden;
  font-family: inherit;
  color: var(--flow-fg);
}

:global(.body--dark) .ingest-data-flow {
  --flow-bg: var(--q-dark);
  --flow-fg: #fff;
}

.flow-internal-area {
  fill: var(--flow-blue);
  fill-opacity: 0.08;
  stroke: var(--flow-blue);
  stroke-width: 1.5;
}

.flow-node--internal .flow-icon {
  fill: var(--flow-blue);
}

.flow-node--external .flow-icon {
  fill: var(--flow-fg);
}

.flow-server-body {
  fill: var(--flow-blue);
}

.flow-logo {
  fill: #fff;
}

.flow-server-slot {
  fill: none;
  stroke: #fff;
  stroke-width: 1;
}

.flow-server-led {
  fill: var(--flow-blue);
  stroke: #fff;
  stroke-width: 0.8;
}

.flow-server-led--on {
  fill: #fff;
}

.flow-node-label,
.flow-edge-label {
  fill: var(--flow-fg);
  text-anchor: middle;
}

.flow-node-label {
  paint-order: stroke;
  stroke: var(--flow-bg);
  stroke-width: 3px;
  stroke-linejoin: round;
  font-size: 11px;
  font-weight: 500;
}

// Clear box behind the time.IO label where the internal area's border crosses it.
.flow-label-box {
  fill: var(--flow-bg);
}

.flow-edge-label {
  font-size: 9.5px;
}

.flow-edge line {
  stroke-width: 1.5;
  transition: stroke-width 0.2s;
}

.flow-edge line.flow-edge--active {
  stroke-width: 2.5;
}

.flow-edge--data line {
  stroke: var(--flow-blue);
}

.flow-edge--request line {
  stroke: var(--flow-fg);
  stroke-dasharray: 4 3;
}

.flow-edge--subscribe line {
  stroke: var(--flow-fg);
  stroke-dasharray: 2 3;
}

.flow-edge--subscribe line.flow-edge--active {
  stroke-width: 1.5;
}

.flow-marker--data path {
  fill: var(--flow-blue);
}

.flow-marker--request path,
.flow-marker--subscribe path {
  fill: var(--flow-fg);
}

.flow-packet--data {
  fill: var(--flow-blue);
}

.flow-packet-ring {
  fill: var(--flow-bg);
  stroke: var(--flow-fg);
  stroke-width: 2;
}

.flow-schedule-face {
  fill: var(--flow-bg);
  stroke: var(--flow-fg);
  stroke-width: 1.5;
}

.flow-schedule-pulse {
  fill: none;
  stroke: var(--flow-fg);
  stroke-width: 1.5;
}

.flow-schedule-hand {
  stroke: var(--flow-fg);
  stroke-width: 1.5;
  stroke-linecap: round;
}
</style>
