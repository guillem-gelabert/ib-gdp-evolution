<template>
  <div class="relative">
    <svg
      class="block w-full max-w-[1200px] mx-auto max-h-[76vh]"
      :viewBox="`0 0 ${WIDTH} ${HEIGHT}`"
      role="img"
      aria-label="Act II GDP comparison chart"
    >
      <g :transform="`translate(${MARGIN.left},${MARGIN.top})`">
        <rect
          v-if="showPeakBand"
          :x="xForYear(1988)"
          :y="0"
          :width="Math.max(0, xForYear(1993) - xForYear(1988))"
          :height="innerHeight"
          fill="#d6c4b6"
          fill-opacity="0.14"
        />

        <line
          v-if="showReferenceLine"
          :x1="0"
          :x2="innerWidth"
          :y1="euReferenceY"
          :y2="euReferenceY"
          stroke="#b2a59a"
          stroke-width="1.25"
          stroke-dasharray="6 5"
          :opacity="modeProgress"
        />

        <path
          v-if="showArrivals && arrivalsPath"
          :d="arrivalsPath"
          fill="none"
          :stroke="ARRIVALS_COLOR"
          stroke-width="2.2"
          opacity="0.75"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <g>
          <path
            v-for="series in renderedSeries"
            :key="series.slug"
            :d="series.path"
            fill="none"
            :stroke="series.stroke"
            :stroke-width="series.strokeWidth"
            :opacity="series.opacity"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </g>

        <g
          v-for="tick in yTicks"
          :key="tick.label"
          :transform="`translate(0, ${tick.y})`"
        >
          <line x1="0" :x2="innerWidth" y1="0" y2="0" stroke="#eee2d8" />
          <text
            x="-14"
            y="4"
            text-anchor="end"
            font-family="DM Mono, monospace"
            font-size="12"
            fill="#7f746d"
          >
            {{ tick.label }}
          </text>
        </g>

        <g
          v-for="tick in xTicks"
          :key="tick"
          :transform="`translate(${xForYear(tick)}, ${innerHeight})`"
        >
          <line x1="0" x2="0" y1="0" y2="8" stroke="#cdbfb4" />
          <text
            y="22"
            text-anchor="middle"
            font-family="DM Mono, monospace"
            font-size="12"
            fill="#7f746d"
          >
            {{ tick }}
          </text>
        </g>

        <g
          v-for="tick in arrivalsYTicks"
          :key="'arr-' + tick.label"
          :transform="`translate(${innerWidth}, ${tick.y})`"
        >
          <text
            x="14"
            y="4"
            text-anchor="start"
            font-family="DM Mono, monospace"
            font-size="11"
            :fill="ARRIVALS_COLOR"
            opacity="0.7"
          >
            {{ tick.label }}
          </text>
        </g>

        <g v-for="label in endLabels" :key="label.slug">
          <text
            :x="label.x"
            :y="label.y"
            font-family="Canela, 'Times New Roman', serif"
            font-size="15"
            :fill="label.color"
          >
            {{ label.text }}
          </text>
        </g>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { extent as d3Extent, scaleLinear } from "d3";
import type { GdpDataPoint } from "./line-chart.vue";
import {
  buildEditorialPath,
  EDITORIAL_EU_COLOR,
  EDITORIAL_GHOST_COLOR,
  EDITORIAL_LINE_COLOR,
  EDITORIAL_MUTED_COLOR,
} from "~/utils/editorial-chart";

type SeriesState = {
  visible: boolean;
  emphasis?: "highlight" | "normal" | "muted";
};

const props = defineProps<{
  seriesMap: Record<string, Array<GdpDataPoint>>;
  axisMode: "real-eur" | "pct-eu15";
  seriesState: Record<string, SeriesState>;
  showPeakBand?: boolean;
  showReferenceLine?: boolean;
  arrivalsData?: Array<GdpDataPoint>;
  arrivalsYDomain?: [number, number];
  showArrivals?: boolean;
}>();

const WIDTH = 980;
const HEIGHT = 460;
const MARGIN = { top: 28, right: 84, bottom: 42, left: 66 };
const innerWidth = WIDTH - MARGIN.left - MARGIN.right;
const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
const modeProgress = computed(() => (props.axisMode === "pct-eu15" ? 1 : 0));

const displayMeta: Record<string, { label: string; color: string }> = {
  balearic_islands: { label: "Balearics", color: EDITORIAL_LINE_COLOR },
  extremadura: { label: "Extremadura", color: "#8b4b24" },
  andalucia: { label: "Andalucia", color: "#9f7f44" },
  portugal: { label: "Portugal", color: "#756a8a" },
  ireland: { label: "Ireland", color: "#2e6f61" },
  france: { label: "France", color: "#4f6485" },
  eu15_avg: { label: "EU-15", color: EDITORIAL_EU_COLOR },
};

const ARRIVALS_COLOR = "#1f6feb";
const xScale = scaleLinear().domain([1900, 2024]).range([0, innerWidth]);
const allRealValues = computed(() =>
  Object.values(props.seriesMap).flatMap((series) =>
    series.map((point) => point.gdp_pc),
  ),
);
const realExtent = computed<[number, number]>(() => {
  const ext = d3Extent(allRealValues.value);
  const min = ext[0] ?? 0;
  const max = ext[1] ?? 1;
  return [Math.max(0, min * 0.88), max * 1.08];
});
const realScale = computed(() =>
  scaleLinear().domain(realExtent.value).range([innerHeight, 0]),
);
const pctScale = computed(() =>
  scaleLinear().domain([45, 165]).range([innerHeight, 0]),
);
const eu15ByYear = computed(() => {
  const map = new Map<number, number>();
  for (const point of props.seriesMap.eu15_avg ?? []) {
    map.set(point.year, point.gdp_pc);
  }
  return map;
});

function xForYear(year: number) {
  return xScale(year);
}

function yForPoint(slug: string, point: GdpDataPoint) {
  const realY = realScale.value(point.gdp_pc);
  const euBase = eu15ByYear.value.get(point.year) ?? point.gdp_pc;
  const pctValue = euBase > 0 ? (point.gdp_pc / euBase) * 100 : 100;
  const pctY = pctScale.value(pctValue);
  return realY + (pctY - realY) * modeProgress.value;
}

const arrivalsScale = computed(() =>
  scaleLinear()
    .domain(props.arrivalsYDomain ?? [0, 20_000_000])
    .range([innerHeight, 0]),
);

const arrivalsPath = computed(() => {
  if (!props.showArrivals || !props.arrivalsData?.length) return "";
  const points = props.arrivalsData.map((d) => ({
    x: xForYear(d.year),
    y: arrivalsScale.value(d.gdp_pc),
  }));
  return buildEditorialPath(points);
});

const arrivalsYTicks = computed(() => {
  if (!props.showArrivals || !props.arrivalsData?.length) return [];
  const [, max] = props.arrivalsYDomain ?? [0, 20_000_000];
  const step = max > 10_000_000 ? 5_000_000 : 2_000_000;
  const ticks: { y: number; label: string }[] = [];
  for (let v = step; v <= max; v += step) {
    ticks.push({
      y: arrivalsScale.value(v),
      label: `${(v / 1_000_000).toFixed(0)}M`,
    });
  }
  return ticks;
});

const renderedSeries = computed(() => {
  return Object.entries(props.seriesMap)
    .filter(([slug]) => props.seriesState[slug]?.visible)
    .map(([slug, series]) => {
      const state = props.seriesState[slug] ?? {
        visible: true,
        emphasis: "normal",
      };
      const meta = displayMeta[slug] ?? {
        label: slug,
        color: EDITORIAL_MUTED_COLOR,
      };
      const points = series.map((point) => ({
        x: xForYear(point.year),
        y: yForPoint(slug, point),
      }));
      const stroke =
        state.emphasis === "highlight"
          ? meta.color
          : state.emphasis === "muted"
            ? EDITORIAL_GHOST_COLOR
            : meta.color;
      return {
        slug,
        path: buildEditorialPath(points),
        stroke,
        opacity: state.emphasis === "muted" ? 0.55 : 0.96,
        strokeWidth:
          slug === "balearic_islands" ? 3.4 : slug === "eu15_avg" ? 2 : 2.4,
      };
    });
});

const yTicks = computed(() => {
  if (modeProgress.value > 0.5) {
    return [50, 75, 100, 125, 150].map((value) => ({
      y: pctScale.value(value),
      label: value === 100 ? "100" : `${value}`,
    }));
  }
  const [min, max] = realExtent.value;
  const span = max - min;
  const ticks = [0.2, 0.45, 0.7, 0.95].map((ratio) => min + span * ratio);
  return ticks.map((value) => ({
    y: realScale.value(value),
    label: `${Math.round(value / 1000)}k`,
  }));
});

const xTicks = [1900, 1930, 1960, 1990, 2024];
const euReferenceY = computed(() => pctScale.value(100));

const endLabels = computed(() => {
  const labels = renderedSeries.value
    .filter((series) => series.slug !== "eu15_avg")
    .map((series) => {
      const raw = props.seriesMap[series.slug] ?? [];
      const last = raw[raw.length - 1];
      const meta = displayMeta[series.slug] ?? {
        label: series.slug,
        color: EDITORIAL_MUTED_COLOR,
      };
      if (!last) return null;
      return {
        slug: series.slug,
        text: meta.label,
        x: xForYear(last.year) + 10,
        y: yForPoint(series.slug, last) + 4,
        color: series.stroke,
      };
    })
    .filter((value): value is NonNullable<typeof value> => Boolean(value));

  if (props.showArrivals && props.arrivalsData?.length) {
    const last = props.arrivalsData[props.arrivalsData.length - 1];
    if (last) {
      labels.push({
        slug: "arrivals",
        text: "Tourist arrivals",
        x: xForYear(last.year) + 10,
        y: arrivalsScale.value(last.gdp_pc) + 4,
        color: ARRIVALS_COLOR,
      });
    }
  }
  return labels;
});
</script>
