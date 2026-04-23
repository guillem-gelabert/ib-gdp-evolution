<template>
  <svg ref="svg" class="block w-full max-w-[1200px] mx-auto max-h-[70vh]"></svg>
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
  yDomain?: [number, number];
  xDomain?: [number, number];
}>();

const WIDTH = 928;
const HEIGHT = 400;
const MARGIN = { top: 16, right: 32, bottom: 36, left: 80 };
const DURATION = 800;

const NOISE_SEED = "balearic-gdp-ib";
const NOISE_AMPLITUDE = 4;
const noise2D = createNoise2D(alea(NOISE_SEED));

let noiseCacheKey = "";
const noiseOffsetByKey = new Map<string, number>();
function keyFor(d: GdpDataPoint) {
  return `${d.source}|${d.year}`;
}
function buildNoiseKey(
  rows: GdpDataPoint[],
  xMin: number,
  xMax: number,
  y0: number,
  y1: number,
) {
  const s = [...rows].sort(
    (a, b) => a.year - b.year || a.source.localeCompare(b.source),
  );
  return `${xMin}|${xMax}|${y0}|${y1}|${s
    .map((r) => `${r.year}:${r.source}`)
    .join(";")}|${NOISE_SEED}`;
}
function ensureNoiseCache(
  rows: GdpDataPoint[],
  xMin: number,
  xMax: number,
  y0: number,
  y1: number,
) {
  const k = buildNoiseKey(rows, xMin, xMax, y0, y1);
  if (k === noiseCacheKey) return;
  noiseCacheKey = k;
  noiseOffsetByKey.clear();
  for (const d of rows) {
    const ny = d.source === "INE" ? 0.1 : 0;
    const nx = d.year / 40;
    noiseOffsetByKey.set(
      keyFor(d),
      noise2D(nx, ny) * NOISE_AMPLITUDE,
    );
  }
}
function getNoiseYOffset(d: GdpDataPoint): number {
  return noiseOffsetByKey.get(keyFor(d)) ?? 0;
}

const yearBisect = d3.bisector((d: GdpDataPoint) => d.year).center;

function seriesForBisect(rows: GdpDataPoint[]): GdpDataPoint[] {
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

let xScale: d3.ScaleTime<number, number>;
let yScale: d3.ScaleLinear<number, number>;
let xAxisG: d3.Selection<SVGGElement, unknown, null, undefined>;
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
let ready = false;
const valueFormat = d3.format(",.0f");
const LINE_COLOR = "#660000";

function sourceColor(_source: string) {
  return LINE_COLOR;
}

const sourceOrder = new Map<string, number>([
  ["RW", 0],
  ["INE", 1],
]);

function sourceWidth(_source: string) {
  return 2.5;
}

function sourceOpacity(_source: string) {
  return 1;
}

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

function applyLineGrow(
  path: d3.Selection<SVGPathElement, unknown, null, undefined>,
  runAnimation: boolean,
) {
  const node = path.node();
  if (!node) return;
  const length = node.getTotalLength();
  path.interrupt();
  path.attr("stroke-dasharray", `${length} ${length}`);
  if (!runAnimation) {
    path.attr("stroke-dashoffset", 0);
    return;
  }
  path
    .attr("stroke-dashoffset", length)
    .transition()
    .duration(DURATION)
    .ease(d3.easeCubicInOut)
    .attr("stroke-dashoffset", 0);
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

  const forBisect = seriesForBisect(newData);
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
    .attr("y1", MARGIN.top)
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
  const svgEl = d3.select(svg.value);
  svgEl.selectAll("*").remove();
  svgEl
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);

  const defs = svgEl.append("defs");
  defs
    .append("marker")
    .attr("id", "series-arrow")
    .attr("viewBox", "0 0 10 10")
    .attr("refX", 9)
    .attr("refY", 5)
    .attr("markerWidth", 8)
    .attr("markerHeight", 8)
    .attr("orient", "auto-start-reverse")
    .attr("markerUnits", "userSpaceOnUse")
    .append("path")
    .attr("d", "M0 0 L0 10 L9 5 Z")
    .attr("fill", "#660000")
    .attr("stroke", "none");

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

  linesG = svgEl.append("g");

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
    pointsG.selectAll("circle").remove();
    hideTooltip();
    return;
  }

  const xMin = props.xDomain?.[0] ?? d3.min(newData, (d) => d.year) ?? 1900;
  const xMax = props.xDomain?.[1] ?? d3.max(newData, (d) => d.year) ?? 1950;
  const [y0d, y1d] = yScale.domain() as [number, number];

  xScale.domain([yearToDate(xMin), yearToDate(xMax)]);

  ensureNoiseCache(newData, xMin, xMax, y0d, y1d);

  const lineGen = d3
    .line<GdpDataPoint>()
    .x((d) => xScale(yearToDate(d.year)))
    .y((d) => yScale(d.gdp_pc) + getNoiseYOffset(d));

  const axis = d3
    .axisBottom(xScale)
    .tickSizeOuter(0)
    .tickSize(0)
    .tickPadding(12);

  if (animate) {
    const t = d3.transition().duration(DURATION).ease(d3.easeCubicInOut);
    (xAxisG.transition(t as any) as any).call(axis).call(styleXAxis);
  } else {
    xAxisG.call(axis as any).call(styleXAxis);
  }

  const groupedSeries = d3
    .groups(newData, (d) => d.source)
    .map(([source, values]) => ({
      source,
      values: [...values].sort((a, b) => a.year - b.year),
    }))
    .sort(
      (a, b) =>
        (sourceOrder.get(a.source) ?? 99) - (sourceOrder.get(b.source) ?? 99),
    );

  linesG
    .selectAll<SVGPathElement, { source: string; values: GdpDataPoint[] }>("path.series-line")
    .data(groupedSeries, (d: any) => d.source)
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
    // UI-SPEC: marker-end can sit at the full path end while stroke-dashoffset reveals the stroke; if the arrowhead looks wrong in UAT, add an overlay at the noised xMax point (see 01-UI-SPEC).
    .attr("marker-end", "url(#series-arrow)")
    .attr("stroke", (d) => sourceColor(d.source))
    .attr("stroke-width", (d) => sourceWidth(d.source))
    .attr("opacity", (d) => sourceOpacity(d.source))
    .attr("d", (d) => lineGen(d.values))
    .each(function () {
      applyLineGrow(d3.select(this), animate);
    });

  const sortedPoints = [...newData].sort(
    (a, b) => (sourceOrder.get(a.source) ?? 99) - (sourceOrder.get(b.source) ?? 99),
  );

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
    .attr("r", 0)
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
</script>
