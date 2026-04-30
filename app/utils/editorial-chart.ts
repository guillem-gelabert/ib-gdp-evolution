import { line as d3Line } from "d3";

export interface ChartPoint {
  x: number;
  y: number;
}

export const EDITORIAL_LINE_COLOR = "#660000";
export const EDITORIAL_GHOST_COLOR = "#C4B9B0";
export const EDITORIAL_MUTED_COLOR = "#8C7A70";
export const EDITORIAL_EU_COLOR = "#9A8F86";

export function buildEditorialPath(points: ChartPoint[]) {
  return (
    d3Line<ChartPoint>()
      .x((d) => d.x)
      .y((d) => d.y)
      (points) ?? ""
  );
}
