<template>
  <div class="relative">
    <svg ref="svg" class="block w-full max-w-[1200px] mx-auto max-h-[70vh]"></svg>
    <div
      v-if="showNoiseControls"
      class="fixed top-4 right-4 z-40 w-[280px] bg-[rgba(250,247,240,0.95)] border border-[#d6d5d3] rounded p-3 text-xs text-[#2f2f2f] backdrop-blur-sm"
    >
      <div class="font-semibold tracking-wide mb-2">Noise Controls</div>
      <label class="block mb-2">
        <div class="flex justify-between mb-1">
          <span>Amplitude</span>
          <span>{{ noiseControls.amplitude.toFixed(1) }}</span>
        </div>
        <input v-model.number="noiseControls.amplitude" type="range" min="0" max="24" step="0.5" class="w-full" />
      </label>
      <label class="block mb-2">
        <div class="flex justify-between mb-1">
          <span>X Divisor</span>
          <span>{{ noiseControls.xDivisor.toFixed(1) }}</span>
        </div>
        <input v-model.number="noiseControls.xDivisor" type="range" min="2" max="50" step="0.5" class="w-full" />
      </label>
      <label class="block mb-2">
        <div class="flex justify-between mb-1">
          <span>Resample Step (years)</span>
          <span>{{ noiseControls.stepYears.toFixed(2) }}</span>
        </div>
        <input v-model.number="noiseControls.stepYears" type="range" min="0.1" max="2" step="0.1" class="w-full" />
      </label>
      <label class="block mb-2">
        <div class="flex justify-between mb-1">
          <span>Curve Alpha</span>
          <span>{{ noiseControls.curveAlpha.toFixed(2) }}</span>
        </div>
        <input v-model.number="noiseControls.curveAlpha" type="range" min="0" max="1" step="0.05" class="w-full" />
      </label>
      <label class="block mb-2">
        <div class="flex justify-between mb-1">
          <span>Noise Channel</span>
          <span>{{ noiseControls.channel.toFixed(2) }}</span>
        </div>
        <input v-model.number="noiseControls.channel" type="range" min="0" max="2" step="0.05" class="w-full" />
      </label>
      <label class="block">
        <div class="mb-1">Seed</div>
        <input
          v-model="noiseControls.seed"
          type="text"
          class="w-full border border-[#d6d5d3] rounded px-2 py-1 bg-[#faf7f0]"
          spellcheck="false"
        />
      </label>
      <label class="mt-3 flex items-center gap-2">
        <input v-model="noiseControls.showAllPoints" type="checkbox" />
        <span>Show all data points</span>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as d3 from "d3";
import { createNoise2D } from "simplex-noise";
import alea from "alea";
const svg = ref(null);

export interface GdpDataPoint {
  year: number;
  gdp_pc: number;
  source: string;
  unit?: string;
}

const props = defineProps<{
  data: Array<GdpDataPoint>;
  comparisonData?: Array<GdpDataPoint>;
  yDomain?: [number, number];
  xDomain?: [number, number];
  showNoiseControls?: boolean;
}>();

const WIDTH = 928;
const HEIGHT = 400;
const MARGIN = { top: 16, right: 32, bottom: 36, left: 80 };
const LINE_SPEED = 0.15; // SVG user-units per ms
const MAX_DURATION = 2000;
const MIN_DURATION = 120;
let prevPathLength = 0;
let prevMaxDataYear: number | null = null;
let prevXMax: number | null = null;
const runtimeConfig = useRuntimeConfig();

function isTruthyEnvFlag(v: unknown): boolean {
  if (v === true) return true;
  if (typeof v === "string")
    return ["1", "true", "yes", "on"].includes(v.toLowerCase());
  return false;
}

const showNoiseControls = computed(
  () =>
    Boolean(props.showNoiseControls) &&
    isTruthyEnvFlag(runtimeConfig.public.showChartNoiseLeva),
);

const NOISE_SEED = "balearic-gdp-ib";
const DEFAULT_NOISE_AMPLITUDE = 5.5;
const DEFAULT_NOISE_X_DIVISOR = 18;
const DEFAULT_RESAMPLE_STEP_YEARS = 1.8;
const DEFAULT_CURVE_ALPHA = 0.5;
const DEFAULT_NOISE_CHANNEL = 0;
const noiseControls = reactive({
  amplitude: DEFAULT_NOISE_AMPLITUDE,
  xDivisor: DEFAULT_NOISE_X_DIVISOR,
  stepYears: DEFAULT_RESAMPLE_STEP_YEARS,
  curveAlpha: DEFAULT_CURVE_ALPHA,
  channel: DEFAULT_NOISE_CHANNEL,
  seed: NOISE_SEED,
  showAllPoints: false,
});
let noise2D = createNoise2D(alea(noiseControls.seed));

let noiseCacheKey = "";
const noiseOffsetByYear = new Map<number, number>();
function buildNoiseKey(rows: GdpDataPoint[]) {
  const s = [...rows].sort(
    (a, b) => a.year - b.year || a.source.localeCompare(b.source),
  );
  return `${s.map((r) => `${r.year}:${r.source}`).join(";")}|${noiseControls.seed}|${noiseControls.amplitude}|${noiseControls.xDivisor}|${noiseControls.channel}`;
}
function sampleNoise(year: number, channel = 0): number {
  const xDivisor = Math.max(0.001, noiseControls.xDivisor);
  return (
    noise2D(year / xDivisor, channel + noiseControls.channel) *
    noiseControls.amplitude
  );
}
function ensureNoiseCache(rows: GdpDataPoint[]) {
  const k = buildNoiseKey(rows);
  if (k === noiseCacheKey) return;
  noiseCacheKey = k;
  noiseOffsetByYear.clear();
  for (const d of rows) {
    noiseOffsetByYear.set(d.year, 0);
  }
}
function getNoiseYOffset(d: GdpDataPoint): number {
  return noiseOffsetByYear.get(d.year) ?? 0;
}

const yearBisect = d3.bisector((d: GdpDataPoint) => d.year).center;

function dedupeByYear(rows: GdpDataPoint[]): GdpDataPoint[] {
  const sorted = [...rows].sort(
    (a, b) =>
      a.year - b.year ||
      (sourceOrder.get(a.source) ?? 99) - (sourceOrder.get(b.source) ?? 99),
  );
  const m = new Map<number, GdpDataPoint>();
  for (const d of sorted) {
    m.set(d.year, d);
  }
  return [...m.values()].sort((a, b) => a.year - b.year);
}

interface SampledPoint {
  year: number;
  gdp_pc: number;
  noiseOffset: number;
}

function buildResampledSeries(
  series: GdpDataPoint[],
  stepYears = DEFAULT_RESAMPLE_STEP_YEARS,
): SampledPoint[] {
  if (series.length === 0) return [];
  if (series.length === 1) {
    const only = series[0]!;
    return [
      {
        year: only.year,
        gdp_pc: only.gdp_pc,
        noiseOffset: 0,
      },
    ];
  }

  const sampled: SampledPoint[] = [];
  for (let i = 0; i < series.length - 1; i += 1) {
    const start = series[i]!;
    const end = series[i + 1]!;
    if (i === 0) {
      sampled.push({
        year: start.year,
        gdp_pc: start.gdp_pc,
        noiseOffset: 0,
      });
    }

    const gap = end.year - start.year;
    if (gap > stepYears) {
      for (let y = start.year + stepYears; y < end.year; y += stepYears) {
        const t = (y - start.year) / gap;
        const gdpPc = start.gdp_pc + (end.gdp_pc - start.gdp_pc) * t;
        const falloff = Math.sin(Math.PI * t);
        sampled.push({
          year: Number(y.toFixed(3)),
          gdp_pc: gdpPc,
          noiseOffset: sampleNoise(y) * falloff,
        });
      }
    }

    sampled.push({
      year: end.year,
      gdp_pc: end.gdp_pc,
      noiseOffset: 0,
    });
  }

  return sampled;
}

let xScale: d3.ScaleTime<number, number>;
let yScale: d3.ScaleLinear<number, number>;
let xAxisG: d3.Selection<SVGGElement, unknown, null, undefined>;
let comparisonG: d3.Selection<SVGGElement, unknown, null, undefined>;
let linesG: d3.Selection<SVGGElement, unknown, null, undefined>;
let hoverLine: d3.Selection<SVGLineElement, unknown, null, undefined>;
let pointsG: d3.Selection<SVGGElement, unknown, null, undefined>;
let plotOverlay: d3.Selection<SVGRectElement, unknown, null, undefined>;
let highlightDot: d3.Selection<SVGCircleElement, unknown, null, undefined>;
let tooltipG: d3.Selection<SVGGElement, unknown, null, undefined>;
let tooltipBg: d3.Selection<SVGRectElement, unknown, null, undefined>;
let tooltipYear: d3.Selection<SVGTextElement, unknown, null, undefined>;
let tooltipSource: d3.Selection<SVGTextElement, unknown, null, undefined>;
let tooltipValue: d3.Selection<SVGTextElement, unknown, null, undefined>;
let arrowPath: d3.Selection<SVGPathElement, unknown, null, undefined>;
let ready = false;
const valueFormat = d3.format(",.0f");
const LINE_COLOR = "#660000";
const GHOST_COLOR = "#C4B9B0";

function sourceColor(_source: string) {
  return LINE_COLOR;
}

const sourceOrder = new Map<string, number>([
  ["RW", 0],
  ["INE", 1],
]);

function yearToDate(y: number) {
  return new Date(y, 0, 0);
}

function styleXAxis(g: d3.Selection<SVGGElement, unknown, null, undefined>) {
  g.select(".domain").attr("stroke", "#D6D5D3");
  g.selectAll(".tick text")
    .attr("font-family", "DM Mono, Courier New, monospace")
    .attr("font-size", "12px")
    .attr("fill", "#6B6B6B")
    .attr("text-anchor", "end")
    .attr("transform", "rotate(-45)")
    .attr("dx", "-0.4em")
    .attr("dy", "0.6em");
}

/**
 * Binary-search the arc length at which the path reaches `targetX`.
 * Assumes the path is monotonically left-to-right (true for a time-series).
 */
function pathLengthAtX(node: SVGPathElement, targetX: number): number {
  const total = node.getTotalLength();
  if (total <= 0) return 0;
  if (targetX <= node.getPointAtLength(0).x) return 0;
  if (targetX >= node.getPointAtLength(total).x) return total;
  let lo = 0;
  let hi = total;
  for (let i = 0; i < 48; i++) {
    const mid = (lo + hi) / 2;
    if (node.getPointAtLength(mid).x < targetX) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

function applyLineGrow(
  path: d3.Selection<SVGPathElement, unknown, null, undefined>,
  runAnimation: boolean,
  alreadyDrawn = 0,
): number {
  const node = path.node();
  if (!node) return 0;
  const newLength = node.getTotalLength();
  if (!Number.isFinite(newLength) || newLength <= 0) {
    arrowPath.style("display", "none");
    return 0;
  }

  const drawArrowAtProgress = (progress: number) => {
    const clamped = Math.max(0, Math.min(1, progress));
    const at = newLength * clamped;
    const tip = node.getPointAtLength(at);
    const prev = node.getPointAtLength(Math.max(0, at - 1));
    const angle = Math.atan2(tip.y - prev.y, tip.x - prev.x) * (180 / Math.PI);
    arrowPath
      .style("display", null)
      .attr("d", "M-10 -6 L0 0 L-10 6")
      .attr("transform", `translate(${tip.x},${tip.y}) rotate(${angle})`);
  };

  path.interrupt();
  arrowPath.interrupt();
  path.attr("stroke-dasharray", `${newLength} ${newLength}`);

  if (!runAnimation) {
    path.attr("stroke-dashoffset", 0);
    prevPathLength = newLength;
    drawArrowAtProgress(1);
    return 0;
  }

  const safeStart = Math.max(0, Math.min(alreadyDrawn, newLength));
  const delta = Math.max(0, newLength - safeStart);
  const duration = Math.min(
    MAX_DURATION,
    Math.max(MIN_DURATION, delta / LINE_SPEED),
  );
  const startOffset = delta; // = newLength - safeStart

  const startFraction = newLength > 0 ? safeStart / newLength : 0;

  path
    .attr("stroke-dashoffset", startOffset)
    .transition()
    .duration(duration)
    .ease(d3.easeCubicInOut)
    .attr("stroke-dashoffset", 0)
    .tween("arrow-follow", () => (t: number) => {
      drawArrowAtProgress(startFraction + t * (1 - startFraction));
    });

  prevPathLength = newLength;
  return duration;
}

function handlePlotPointerMove(event: Event) {
  const newData = props.data;
  if (newData.length === 0) return;
  const overlayNode = plotOverlay?.node() as Element | null;
  if (!overlayNode) return;
  const pts = d3.pointers(event, overlayNode);
  if (!pts.length) return;
  const [mx] = pts[0]!;
  const t = xScale.invert(mx);
  const y0y = t.getFullYear();
  const tStart = +new Date(y0y, 0, 0);
  const tEnd = +new Date(y0y + 1, 0, 0);
  const yearFloat = y0y + (t.getTime() - tStart) / (tEnd - tStart);

  const forBisect = dedupeByYear(newData);
  if (forBisect.length === 0) return;
  const rawIdx = yearBisect(forBisect, yearFloat);
  const i = Math.max(
    0,
    Math.min(Math.round(rawIdx), forBisect.length - 1),
  );
  const d = forBisect[i]!;
  showTooltip(d);
}

function handlePlotPointerLeave() {
  hideTooltip();
}

function hideTooltip() {
  tooltipG.style("display", "none");
  hoverLine.style("display", "none");
  highlightDot.style("display", "none");
}

function showTooltip(d: GdpDataPoint) {
  const px = xScale(yearToDate(d.year));
  const yNoise = yScale(d.gdp_pc) + getNoiseYOffset(d);
  const yearLabel = `${d.year}`;
  const sourceLabel = d.source;
  const valueLabel = valueFormat(d.gdp_pc);

  tooltipYear.text(yearLabel);
  tooltipSource.text(sourceLabel);
  tooltipValue.text(valueLabel);

  const padX = 8;
  const padY = 8;
  const lineGap = 4;
  const yearBox = (tooltipYear.node() as SVGTextElement).getBBox();
  const sourceBox = (tooltipSource.node() as SVGTextElement).getBBox();
  const valueBox = (tooltipValue.node() as SVGTextElement).getBBox();
  const contentWidth = Math.max(yearBox.width, sourceBox.width, valueBox.width);
  const contentHeight = yearBox.height + lineGap + sourceBox.height + lineGap + valueBox.height;
  const boxWidth = contentWidth + padX * 2;
  const boxHeight = contentHeight + padY * 2;

  let tx = px + 12;
  let ty = yNoise - boxHeight - 10;
  const rightLimit = WIDTH - MARGIN.right - boxWidth;
  const topLimit = MARGIN.top;

  if (tx > rightLimit) tx = px - boxWidth - 12;
  if (ty < topLimit) ty = yNoise + 12;

  hoverLine
    .attr("x1", px)
    .attr("x2", px)
    .attr("y1", yNoise)
    .attr("y2", HEIGHT - MARGIN.bottom)
    .style("display", null);

  highlightDot
    .attr("cx", px)
    .attr("cy", yNoise)
    .attr("r", 4)
    .style("display", null);

  tooltipG.attr("transform", `translate(${tx},${ty})`).style("display", null);
  tooltipBg.attr("width", boxWidth).attr("height", boxHeight);
  tooltipYear.attr("x", padX).attr("y", padY + yearBox.height);
  tooltipSource
    .attr("x", padX)
    .attr("y", padY + yearBox.height + lineGap + sourceBox.height)
    .attr("fill", sourceColor(d.source));
  tooltipValue
    .attr("x", padX)
    .attr("y", padY + yearBox.height + lineGap + sourceBox.height + lineGap + valueBox.height);
}

function initialize() {
  noiseCacheKey = "";
  prevPathLength = 0;
  prevMaxDataYear = null;
  prevXMax = null;
  const svgEl = d3.select(svg.value);
  svgEl.selectAll("*").remove();
  svgEl
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);

  const domainY: [number, number] = props.yDomain || [0, 1];
  yScale = d3.scaleLinear(domainY, [HEIGHT - MARGIN.bottom, MARGIN.top]);

  const xMin = props.xDomain?.[0] ?? d3.min(props.data, (d) => d.year) ?? 1900;
  const xMax = props.xDomain?.[1] ?? d3.max(props.data, (d) => d.year) ?? 1950;
  xScale = d3.scaleTime(
    [yearToDate(xMin), yearToDate(xMax)],
    [MARGIN.left, WIDTH - MARGIN.right],
  );

  svgEl
    .append("g")
    .attr("transform", `translate(${MARGIN.left},0)`)
    .call(d3.axisLeft(yScale).ticks(HEIGHT / 60).tickSize(0).tickPadding(12))
    .call((g) => g.select(".domain").remove())
    .call((g) =>
      g
        .selectAll(".tick line")
        .clone()
        .attr("x2", WIDTH - MARGIN.left - MARGIN.right)
        .attr("stroke", "#D6D5D3")
        .attr("stroke-opacity", 0.5)
        .attr("stroke-dasharray", "2,4"),
    )
    .call((g) =>
      g
        .selectAll(".tick text")
        .attr("font-family", "DM Mono, Courier New, monospace")
        .attr("font-size", "12px")
        .attr("fill", "#6B6B6B"),
    );

  xAxisG = svgEl
    .append("g")
    .attr("transform", `translate(0,${HEIGHT - MARGIN.bottom})`) as any;

  comparisonG = svgEl.append("g").style("pointer-events", "none");
  linesG = svgEl.append("g");
  arrowPath = svgEl
    .append("path")
    .attr("fill", "none")
    .attr("stroke", LINE_COLOR)
    .attr("stroke-width", 2.5)
    .attr("stroke-linecap", "round")
    .attr("stroke-linejoin", "round")
    .style("display", "none")
    .style("pointer-events", "none");

  pointsG = svgEl.append("g");

  hoverLine = svgEl
    .append("line")
    .attr("stroke", "#8C8A85")
    .attr("stroke-width", 1)
    .attr("stroke-dasharray", "2,4")
    .style("display", "none")
    .style("pointer-events", "none");

  highlightDot = svgEl
    .append("circle")
    .attr("fill", "#660000")
    .attr("stroke", "#FAF7F0")
    .attr("stroke-width", 1.2)
    .attr("r", 0)
    .style("display", "none")
    .style("pointer-events", "none");

  plotOverlay = svgEl
    .append("rect")
    .attr("x", MARGIN.left)
    .attr("y", MARGIN.top)
    .attr("width", WIDTH - MARGIN.left - MARGIN.right)
    .attr("height", HEIGHT - MARGIN.top - MARGIN.bottom)
    .attr("fill", "transparent")
    .style("pointer-events", "all")
    .style("cursor", "crosshair")
    .on("pointermove", handlePlotPointerMove)
    .on("pointerleave", handlePlotPointerLeave);

  tooltipG = svgEl
    .append("g")
    .style("display", "none")
    .style("pointer-events", "none");

  tooltipBg = tooltipG
    .append("rect")
    .attr("fill", "#FAF7F0")
    .attr("stroke", "#D6D5D3")
    .attr("rx", 4)
    .attr("ry", 4);

  tooltipYear = tooltipG
    .append("text")
    .attr("font-family", "DM Mono, Courier New, monospace")
    .attr("font-size", "11px")
    .attr("fill", "#2F2F2F");

  tooltipSource = tooltipG
    .append("text")
    .attr("font-family", "DM Mono, Courier New, monospace")
    .attr("font-size", "11px");

  tooltipValue = tooltipG
    .append("text")
    .attr("font-family", "DM Mono, Courier New, monospace")
    .attr("font-size", "12px")
    .attr("fill", "#2F2F2F");

  ready = true;
  update(true);
}

function renderComparison() {
  const cData = props.comparisonData;
  if (!cData || cData.length === 0) {
    comparisonG.selectAll("path").remove();
    return;
  }

  const ghostLineGen = d3
    .line<GdpDataPoint>()
    .x((d) => xScale(yearToDate(d.year)))
    .y((d) => yScale(d.gdp_pc));

  const grouped = d3
    .groups(cData, (d) => d.source)
    .map(([source, values]) => ({
      source,
      values: [...values].sort((a, b) => a.year - b.year),
    }));

  comparisonG
    .selectAll<SVGPathElement, { source: string; values: GdpDataPoint[] }>("path.ghost-line")
    .data(grouped, (d) => d.source)
    .join(
      (enter) =>
        enter
          .append("path")
          .attr("class", "ghost-line")
          .attr("fill", "none")
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round"),
      (update) => update,
      (exit) => exit.remove(),
    )
    .attr("stroke", GHOST_COLOR)
    .attr("stroke-width", 1.2)
    .attr("opacity", 0.55)
    .attr("d", (d) => ghostLineGen(d.values));
}

function update(animate: boolean) {
  const newData = props.data;
  if (!ready) return;

  if (newData.length === 0) {
    const xMin = props.xDomain?.[0] ?? 1900;
    const xMax = props.xDomain?.[1] ?? 1930;
    xScale.domain([yearToDate(xMin), yearToDate(xMax)]);
    const axis = d3
      .axisBottom(xScale)
      .tickSizeOuter(0)
      .tickSize(0)
      .tickPadding(12);
    xAxisG.call(axis as any).call(styleXAxis);
    linesG.selectAll("path").remove();
    arrowPath.style("display", "none");
    pointsG.selectAll("circle").remove();
    comparisonG.selectAll("path").remove();
    hideTooltip();
    return;
  }

  const xMin = props.xDomain?.[0] ?? d3.min(newData, (d) => d.year) ?? 1900;
  const xMax = props.xDomain?.[1] ?? d3.max(newData, (d) => d.year) ?? 1950;
  const series = dedupeByYear(newData);
  const newMaxDataYear = d3.max(series, (d) => d.year) ?? xMin;

  // Capture current rendered path before any DOM mutations (used for backward animation).
  const savedOldPathD =
    linesG.select<SVGPathElement>("path.series-line").node()?.getAttribute("d") ?? "";

  xScale.domain([yearToDate(xMin), yearToDate(xMax)]);

  renderComparison();

  ensureNoiseCache(series);
  const sampledSeries = buildResampledSeries(
    series,
    Math.max(0.05, noiseControls.stepYears),
  );

  function makeLineGen(scale: d3.ScaleTime<number, number>) {
    return d3
      .line<SampledPoint>()
      .curve(
        d3.curveCatmullRom.alpha(
          Math.max(0, Math.min(1, noiseControls.curveAlpha)),
        ),
      )
      .x((d) => scale(yearToDate(d.year)))
      .y((d) => yScale(d.gdp_pc) + d.noiseOffset);
  }

  const lineGen = makeLineGen(xScale);

  const axis = d3
    .axisBottom(xScale)
    .tickSizeOuter(0)
    .tickSize(0)
    .tickPadding(12);

  let axisDuration = MIN_DURATION;

  // ── Domain-changed: zoom animation where arrow stays at right edge ──────────
  // Handles both expand (1990→2024) and collapse (2024→1990). We tween a
  // separate animScale from [xMin, prevXMax] → [xMin, xMax] so the arrow's x
  // stays pinned to the right edge throughout (only y changes).
  const domainChanged = animate && prevXMax !== null && xMax !== prevXMax;
  // When scrolling backward within the same x-domain, the line should "erase"
  // from the right back to the new tip rather than re-drawing from scratch.
  const dataShrunk =
    animate && prevMaxDataYear !== null && newMaxDataYear < prevMaxDataYear;

  if (domainChanged && prevXMax !== null) {
    axisDuration = MAX_DURATION;

    // Axis transitions to final scale (xScale already has the new domain).
    const axisT = d3.transition().duration(MAX_DURATION).ease(d3.easeCubicInOut);
    (xAxisG.transition(axisT as any) as any).call(axis).call(styleXAxis);

    // Animated scale starts at the OLD domain and expands to the new one.
    const animScale = d3.scaleTime(
      [yearToDate(xMin), yearToDate(prevXMax)],
      [MARGIN.left, WIDTH - MARGIN.right],
    );

    const pathSel = linesG
      .selectAll<SVGPathElement, SampledPoint[]>("path.series-line")
      .data([sampledSeries])
      .join(
        (enter) =>
          enter
            .append("path")
            .attr("class", "series-line")
            .attr("fill", "none")
            .attr("stroke-linejoin", "round")
            .attr("stroke-linecap", "round"),
        (update) => update,
        (exit) => exit.remove(),
      )
      .attr("stroke", LINE_COLOR)
      .attr("stroke-width", 2.5)
      .attr("opacity", 1);

    pathSel.interrupt();
    arrowPath.interrupt();
    (pathSel as any).attr("stroke-dasharray", null).attr("stroke-dashoffset", null);

    // Initial path: old data on old scale (arrow will be at right edge).
    const oldSamples = sampledSeries.filter((s) => s.year <= prevXMax!);
    pathSel.attr("d", makeLineGen(animScale)(oldSamples) ?? "");

    const initNode = pathSel.node();
    if (initNode && initNode.getTotalLength() > 0) {
      const l = initNode.getTotalLength();
      const tip = initNode.getPointAtLength(l);
      const prv = initNode.getPointAtLength(Math.max(0, l - 1));
      arrowPath
        .style("display", null)
        .attr("d", "M-10 -6 L0 0 L-10 6")
        .attr(
          "transform",
          `translate(${tip.x},${tip.y}) rotate(${Math.atan2(tip.y - prv.y, tip.x - prv.x) * (180 / Math.PI)})`,
        );
    }

    const t0 = +yearToDate(prevXMax);
    const t1 = +yearToDate(xMax);

    pathSel
      .transition()
      .duration(MAX_DURATION)
      .ease(d3.easeCubicInOut)
      .tween("zoom-domain", function () {
        const node = this;
        return (t: number) => {
          const currentEnd = new Date(t0 + (t1 - t0) * t);
          animScale.domain([yearToDate(xMin), currentEnd]);
          const currentMaxYear =
            currentEnd.getFullYear() + currentEnd.getMonth() / 12;
          const visible = sampledSeries.filter(
            (s) => s.year <= currentMaxYear + 0.1,
          );
          node.setAttribute("d", makeLineGen(animScale)(visible) ?? "");
          const l = node.getTotalLength();
          if (l > 0) {
            const tip = node.getPointAtLength(l);
            const prv = node.getPointAtLength(Math.max(0, l - 1));
            arrowPath
              .style("display", null)
              .attr("d", "M-10 -6 L0 0 L-10 6")
              .attr(
                "transform",
                `translate(${tip.x},${tip.y}) rotate(${Math.atan2(tip.y - prv.y, tip.x - prv.x) * (180 / Math.PI)})`,
              );
          }
        };
      })
      .on("end", () => {
        // Switch path to final xScale so the chart is in a clean state.
        pathSel.attr("d", lineGen(sampledSeries) ?? "");
        prevPathLength = pathSel.node()?.getTotalLength() ?? 0;
      });

    prevMaxDataYear = newMaxDataYear;
    prevXMax = xMax;

    // ── Data points ──────────────────────────────────────────────────────────
    const sortedPoints = [...series].sort((a, b) => a.year - b.year);
    pointsG
      .selectAll<SVGCircleElement, GdpDataPoint>("circle")
      .data(sortedPoints, (d: any) => `${d.source}-${d.year}`)
      .join((enter) =>
        enter
          .append("circle")
          .attr("stroke", "#FAF7F0")
          .attr("stroke-width", 1.2),
      )
      .attr("r", noiseControls.showAllPoints ? 2.75 : 0)
      .attr("pointer-events", "none")
      .attr("fill", (d) => sourceColor(d.source))
      .attr("cx", (d) => xScale(yearToDate(d.year)))
      .attr("cy", (d) => yScale(d.gdp_pc) + getNoiseYOffset(d));

    return;
  }

  // ── Backward shrink: erase line from right when scrolling up ─────────────────
  // Same x-domain, fewer data years. Start from the old rendered path and
  // animate dashoffset so the line "shrinks" back to the new tip.
  if (dataShrunk && !domainChanged && savedOldPathD && prevPathLength > 0) {
    const pathSel = linesG
      .selectAll<SVGPathElement, SampledPoint[]>("path.series-line")
      .data([sampledSeries])
      .join(
        (enter) =>
          enter
            .append("path")
            .attr("class", "series-line")
            .attr("fill", "none")
            .attr("stroke-linejoin", "round")
            .attr("stroke-linecap", "round"),
        (update) => update,
        (exit) => exit.remove(),
      )
      .attr("stroke", LINE_COLOR)
      .attr("stroke-width", 2.5)
      .attr("opacity", 1);

    pathSel.interrupt();
    arrowPath.interrupt();
    (pathSel as any).attr("stroke-dasharray", null).attr("stroke-dashoffset", null);

    // Revert to the old (longer) path as animation starting point.
    pathSel.attr("d", savedOldPathD);
    const oldNode = pathSel.node()!;
    const oldLen = prevPathLength;

    // Find where the new tip year sits on the old path.
    const anchorX = xScale(yearToDate(newMaxDataYear));
    const startLen = pathLengthAtX(oldNode, anchorX);
    const delta = Math.max(0, oldLen - startLen);
    const duration = Math.min(MAX_DURATION, Math.max(MIN_DURATION, delta / LINE_SPEED));
    axisDuration = duration;

    // Reveal the full old path initially, then erase from the right.
    pathSel
      .attr("stroke-dasharray", `${oldLen} ${oldLen}`)
      .attr("stroke-dashoffset", 0);

    // Place arrow at the current (old) tip.
    if (oldLen > 0) {
      const tip = oldNode.getPointAtLength(oldLen);
      const prv = oldNode.getPointAtLength(Math.max(0, oldLen - 1));
      arrowPath
        .style("display", null)
        .attr("d", "M-10 -6 L0 0 L-10 6")
        .attr(
          "transform",
          `translate(${tip.x},${tip.y}) rotate(${Math.atan2(tip.y - prv.y, tip.x - prv.x) * (180 / Math.PI)})`,
        );
    }

    pathSel
      .transition()
      .duration(duration)
      .ease(d3.easeCubicInOut)
      .attr("stroke-dashoffset", delta)
      .tween("shrink-follow", function () {
        const node = this;
        return (t: number) => {
          // visible right boundary slides from oldLen back to startLen.
          const visibleUpTo = startLen + (oldLen - startLen) * (1 - t);
          if (visibleUpTo > 0) {
            const tip = node.getPointAtLength(visibleUpTo);
            const prv = node.getPointAtLength(Math.max(0, visibleUpTo - 1));
            arrowPath
              .style("display", null)
              .attr("d", "M-10 -6 L0 0 L-10 6")
              .attr(
                "transform",
                `translate(${tip.x},${tip.y}) rotate(${Math.atan2(tip.y - prv.y, tip.x - prv.x) * (180 / Math.PI)})`,
              );
          }
        };
      })
      .on("end", () => {
        // Switch to the final (shorter) path so the chart is in a clean state.
        const newD = lineGen(sampledSeries) ?? "";
        pathSel
          .attr("d", newD)
          .attr("stroke-dasharray", null)
          .attr("stroke-dashoffset", null);
        const newNode = pathSel.node();
        if (newNode) {
          prevPathLength = newNode.getTotalLength();
          if (prevPathLength > 0) {
            const tip = newNode.getPointAtLength(prevPathLength);
            const prv = newNode.getPointAtLength(Math.max(0, prevPathLength - 1));
            arrowPath.attr(
              "transform",
              `translate(${tip.x},${tip.y}) rotate(${Math.atan2(tip.y - prv.y, tip.x - prv.x) * (180 / Math.PI)})`,
            );
          }
        }
      });

    if (animate) {
      const t = d3.transition().duration(axisDuration).ease(d3.easeCubicInOut);
      (xAxisG.transition(t as any) as any).call(axis).call(styleXAxis);
    } else {
      xAxisG.call(axis as any).call(styleXAxis);
    }

    prevMaxDataYear = newMaxDataYear;
    prevXMax = xMax;

    const sortedPts = [...series].sort((a, b) => a.year - b.year);
    pointsG
      .selectAll<SVGCircleElement, GdpDataPoint>("circle")
      .data(sortedPts, (d: any) => `${d.source}-${d.year}`)
      .join((enter) =>
        enter.append("circle").attr("stroke", "#FAF7F0").attr("stroke-width", 1.2),
      )
      .attr("r", noiseControls.showAllPoints ? 2.75 : 0)
      .attr("pointer-events", "none")
      .attr("fill", (d) => sourceColor(d.source))
      .attr("cx", (d) => xScale(yearToDate(d.year)))
      .attr("cy", (d) => yScale(d.gdp_pc) + getNoiseYOffset(d));

    return;
  }
  // ────────────────────────────────────────────────────────────────────────────

  linesG
    .selectAll<SVGPathElement, SampledPoint[]>("path.series-line")
    .data([sampledSeries])
    .join(
      (enter) =>
        enter
          .append("path")
          .attr("class", "series-line")
          .attr("fill", "none")
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round"),
      (update) => update,
      (exit) => exit.remove(),
    )
    .attr("stroke", LINE_COLOR)
    .attr("stroke-width", 2.5)
    .attr("opacity", 1)
    .attr("d", (d) => lineGen(d) ?? "")
    .each(function () {
      let startLen = 0;
      if (animate && prevMaxDataYear !== null) {
        if (prevMaxDataYear < newMaxDataYear) {
          // Growing forward: find where the previously-visible year sits on
          // the new path.
          startLen = pathLengthAtX(this, xScale(yearToDate(prevMaxDataYear)));
        } else {
          // Same extent (prevMaxDataYear === newMaxDataYear): already fully
          // drawn, skip re-animation. dataShrunk case exits early above.
          startLen = this.getTotalLength();
        }
      }
      axisDuration = applyLineGrow(d3.select(this), animate, startLen);
    });

  prevMaxDataYear = newMaxDataYear;
  prevXMax = xMax;

  if (animate) {
    const t = d3.transition().duration(axisDuration).ease(d3.easeCubicInOut);
    (xAxisG.transition(t as any) as any).call(axis).call(styleXAxis);
  } else {
    xAxisG.call(axis as any).call(styleXAxis);
  }

  const sortedPoints = [...series].sort((a, b) => a.year - b.year);

  const points = pointsG
    .selectAll<SVGCircleElement, GdpDataPoint>("circle")
    .data(sortedPoints, (d: any) => `${d.source}-${d.year}`);

  points.exit().remove();

  points
    .join((enter) =>
      enter
        .append("circle")
        .attr("stroke", "#FAF7F0")
        .attr("stroke-width", 1.2),
    )
    .attr("r", noiseControls.showAllPoints ? 2.75 : 0)
    .attr("pointer-events", "none")
    .attr("fill", (d) => sourceColor(d.source))
    .attr("cx", (d) => xScale(yearToDate(d.year)))
    .attr("cy", (d) => yScale(d.gdp_pc) + getNoiseYOffset(d));
}

onMounted(() => {
  initialize();
});

watch(
  () => props.yDomain,
  () => {
    if (ready) initialize();
  },
  { deep: true },
);

watch(
  [() => props.data, () => props.xDomain],
  () => {
    if (!ready) {
      initialize();
      return;
    }
    update(true);
  },
  { deep: true },
);

watch(
  noiseControls,
  () => {
    noise2D = createNoise2D(alea(noiseControls.seed || NOISE_SEED));
    noiseCacheKey = "";
    if (ready) update(false);
  },
  { deep: true },
);
</script>
