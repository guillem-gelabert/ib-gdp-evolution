<template>
  <div class="relative">
    <svg
      ref="svg"
      class="block w-full mx-auto"
    ></svg>
  </div>
</template>

<script setup lang="ts">
import * as d3 from "d3";
import {
  EDITORIAL_GHOST_COLOR,
  EDITORIAL_LINE_COLOR,
} from "~/utils/editorial-chart";
const svg = ref(null);

export interface GdpDataPoint {
  year: number;
  gdp_pc: number;
  source: string;
  unit?: string;
}

const SECONDARY_COLOR = "#1f6feb";

const props = defineProps<{
  data: Array<GdpDataPoint>;
  comparisonData?: Array<GdpDataPoint>;
  secondaryData?: Array<GdpDataPoint>;
  secondaryYDomain?: [number, number];
  yDomain?: [number, number];
  xDomain?: [number, number];
  chartWidth?: number;
  chartHeight?: number;
}>();

const WIDTH = props.chartWidth ?? 928;
const HEIGHT = props.chartHeight ?? 400;
const MARGIN = { top: 16, right: 80, bottom: 36, left: 80 };

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


let xScale: d3.ScaleTime<number, number>;
let yScale: d3.ScaleLinear<number, number>;
let y2Scale: d3.ScaleLinear<number, number>;
let xAxisG: d3.Selection<SVGGElement, unknown, null, undefined>;
let y2AxisG: d3.Selection<SVGGElement, unknown, null, undefined>;
let secondaryG: d3.Selection<SVGGElement, unknown, null, undefined>;
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
let tooltipTourists: d3.Selection<SVGTextElement, unknown, null, undefined>;
let tooltipTouristSource: d3.Selection<
  SVGTextElement,
  unknown,
  null,
  undefined
>;
let ready = false;
const valueFormat = d3.format(",.0f");
const axisTickFormat = d3.format("~s");
const LINE_COLOR = EDITORIAL_LINE_COLOR;
const GHOST_COLOR = EDITORIAL_GHOST_COLOR;

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

function handlePlotPointerMove(event: Event) {
  const newData = props.data;
  if (newData.length === 0) return;
  const overlayNode = plotOverlay?.node() as Element | null;
  if (!overlayNode) return;
  const pts = d3.pointers(event, overlayNode);
  if (!pts.length) return;
  const [mxRaw] = pts[0]!;
  const forBisect = dedupeByYear(newData);
  if (forBisect.length === 0) return;
  const xLeft = xScale(yearToDate(forBisect[0]!.year));
  const xRight = xScale(yearToDate(forBisect[forBisect.length - 1]!.year));
  const mx = Math.min(Math.max(mxRaw, xLeft), xRight);
  const t = xScale.invert(mx);
  const y0y = t.getFullYear();
  const tStart = +new Date(y0y, 0, 0);
  const tEnd = +new Date(y0y + 1, 0, 0);
  const yearFloat = y0y + (t.getTime() - tStart) / (tEnd - tStart);

  const i = yearBisect(forBisect, yearFloat);
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
  const yNoise = yScale(d.gdp_pc);
  const yearLabel = `${d.year}`;
  const sourceLabel = d.source;
  const valueLabel = valueFormat(d.gdp_pc);

  tooltipYear.text(yearLabel);
  tooltipSource.text(sourceLabel);
  tooltipValue.text(valueLabel);

  const sData = props.secondaryData;
  const touristMatch = sData?.find((t) => t.year === d.year);
  const hasTourist = !!touristMatch;
  tooltipTourists.text(
    hasTourist ? `${valueFormat(touristMatch.gdp_pc)} tourists` : "",
  );
  tooltipTouristSource.text(
    hasTourist && touristMatch.unit ? touristMatch.unit : "",
  );

  const padX = 8;
  const padY = 8;
  const lineGap = 4;
  const yearBox = (tooltipYear.node() as SVGTextElement).getBBox();
  const sourceBox = (tooltipSource.node() as SVGTextElement).getBBox();
  const valueBox = (tooltipValue.node() as SVGTextElement).getBBox();
  const touristBox = (tooltipTourists.node() as SVGTextElement).getBBox();
  const touristSourceBox = (
    tooltipTouristSource.node() as SVGTextElement
  ).getBBox();

  const allWidths = [yearBox.width, sourceBox.width, valueBox.width];
  let totalHeight =
    yearBox.height + lineGap + sourceBox.height + lineGap + valueBox.height;
  if (hasTourist) {
    totalHeight += lineGap + touristBox.height;
    allWidths.push(touristBox.width);
    if (touristMatch.unit) {
      totalHeight += lineGap + touristSourceBox.height;
      allWidths.push(touristSourceBox.width);
    }
  }
  const contentWidth = Math.max(...allWidths);
  const boxWidth = contentWidth + padX * 2;
  const boxHeight = totalHeight + padY * 2;

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

  let cursorY = padY + yearBox.height;
  tooltipYear.attr("x", padX).attr("y", cursorY);
  cursorY += lineGap + sourceBox.height;
  tooltipSource
    .attr("x", padX)
    .attr("y", cursorY)
    .attr("fill", sourceColor(d.source));
  cursorY += lineGap + valueBox.height;
  tooltipValue.attr("x", padX).attr("y", cursorY);

  if (hasTourist) {
    cursorY += lineGap + touristBox.height;
    tooltipTourists.attr("x", padX).attr("y", cursorY);
    if (touristMatch.unit) {
      cursorY += lineGap + touristSourceBox.height;
      tooltipTouristSource.attr("x", padX).attr("y", cursorY);
    }
  }
}

function initialize() {
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
    .call(
      d3
        .axisLeft(yScale)
        .ticks(HEIGHT / 60)
        .tickSize(0)
        .tickPadding(12)
        .tickFormat((d) => axisTickFormat(d as number)),
    )
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

  const domainY2: [number, number] = props.secondaryYDomain || [0, 1];
  y2Scale = d3.scaleLinear(domainY2, [HEIGHT - MARGIN.bottom, MARGIN.top]);
  y2AxisG = svgEl
    .append("g")
    .attr("transform", `translate(${WIDTH - MARGIN.right},0)`) as any;
  if (props.secondaryData?.length) {
    y2AxisG
      .call(
        d3
          .axisRight(y2Scale)
          .ticks(HEIGHT / 60)
          .tickSize(0)
          .tickPadding(12)
          .tickFormat((d) => axisTickFormat(d as number)),
      )
      .call((g) => g.select(".domain").remove())
      .call((g) =>
        g
          .selectAll(".tick text")
          .attr("font-family", "DM Mono, Courier New, monospace")
          .attr("font-size", "12px")
          .attr("fill", SECONDARY_COLOR),
      );
  }

  secondaryG = svgEl.append("g").style("pointer-events", "none");
  comparisonG = svgEl.append("g").style("pointer-events", "none");
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
    .style("cursor", "default")
    .on("pointermove", handlePlotPointerMove)
    .on("pointerleave", handlePlotPointerLeave)
    .on("pointercancel", handlePlotPointerLeave);

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

  tooltipTourists = tooltipG
    .append("text")
    .attr("font-family", "DM Mono, Courier New, monospace")
    .attr("font-size", "12px")
    .attr("fill", SECONDARY_COLOR);

  tooltipTouristSource = tooltipG
    .append("text")
    .attr("font-family", "DM Mono, Courier New, monospace")
    .attr("font-size", "11px")
    .attr("fill", SECONDARY_COLOR)
    .attr("opacity", 0.7);

  ready = true;
  update();
}

function renderSecondary() {
  const sData = props.secondaryData;
  if (!sData || sData.length === 0) {
    secondaryG.selectAll("path").remove();
    y2AxisG.selectAll("*").remove();
    return;
  }

  const domainY2: [number, number] = props.secondaryYDomain || [0, 1];
  y2Scale.domain(domainY2);

  y2AxisG
    .call(
      d3
        .axisRight(y2Scale)
        .ticks(HEIGHT / 60)
        .tickSize(0)
        .tickPadding(12)
        .tickFormat((d) => axisTickFormat(d as number)),
    )
    .call((g) => g.select(".domain").remove())
    .call((g) =>
      g
        .selectAll(".tick text")
        .attr("font-family", "DM Mono, Courier New, monospace")
        .attr("font-size", "12px")
        .attr("fill", SECONDARY_COLOR),
    );

  const sorted = [...sData].sort((a, b) => a.year - b.year);
  const secLineGen = d3
    .line<GdpDataPoint>()
    .x((d) => xScale(yearToDate(d.year)))
    .y((d) => y2Scale(d.gdp_pc));

  secondaryG
    .selectAll<SVGPathElement, GdpDataPoint[]>("path.secondary-line")
    .data([sorted])
    .join(
      (enter) =>
        enter
          .append("path")
          .attr("class", "secondary-line")
          .attr("fill", "none")
          .attr("stroke-linejoin", "round")
          .attr("stroke-linecap", "round"),
      (update) => update,
      (exit) => exit.remove(),
    )
    .attr("stroke", SECONDARY_COLOR)
    .attr("stroke-width", 2)
    .attr("opacity", 0.8)
    .attr("d", (d) => secLineGen(d) ?? "");
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
    .selectAll<SVGPathElement, { source: string; values: GdpDataPoint[] }>(
      "path.ghost-line",
    )
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

function update() {
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
    comparisonG.selectAll("path").remove();
    hideTooltip();
    return;
  }

  const xMin = props.xDomain?.[0] ?? d3.min(newData, (d) => d.year) ?? 1900;
  const xMax = props.xDomain?.[1] ?? d3.max(newData, (d) => d.year) ?? 1950;
  const series = dedupeByYear(newData);

  xScale.domain([yearToDate(xMin), yearToDate(xMax)]);

  renderComparison();
  renderSecondary();

  const lineGen = d3
    .line<GdpDataPoint>()
    .x((d) => xScale(yearToDate(d.year)))
    .y((d) => yScale(d.gdp_pc));

  const axis = d3
    .axisBottom(xScale)
    .tickSizeOuter(0)
    .tickSize(0)
    .tickPadding(12);

  linesG
    .selectAll<SVGPathElement, GdpDataPoint[]>("path.series-line")
    .data([series])
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
    .attr("d", (d) => lineGen(d) ?? "");

  xAxisG.call(axis as any).call(styleXAxis);

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
    .attr("r", 0)
    .attr("pointer-events", "none")
    .attr("fill", (d) => sourceColor(d.source))
    .attr("cx", (d) => xScale(yearToDate(d.year)))
    .attr("cy", (d) => yScale(d.gdp_pc));
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
  [() => props.data, () => props.xDomain, () => props.secondaryData],
  () => {
    if (!ready) {
      initialize();
      return;
    }
    update();
  },
  { deep: true },
);
</script>
