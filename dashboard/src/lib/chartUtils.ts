export function makeGradient(ctx: CanvasRenderingContext2D, color: string) {
  const g = ctx.createLinearGradient(0, 0, 0, 300);
  g.addColorStop(0, color + "33");
  g.addColorStop(1, color + "00");
  return g;
}