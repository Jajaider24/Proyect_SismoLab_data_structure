const LEVEL_GAP = 96;
const NODE_GAP = 76;

function clearSvg(svg) {
  d3.select(svg).selectAll("*").remove();
}

export function renderComparisonTree(svg, tree, kind) {
  clearSvg(svg);
  if (!tree) {
    svg.setAttribute("viewBox", "0 0 640 220");
    d3.select(svg)
      .append("text")
      .attr("class", "comparison-empty")
      .attr("x", 320)
      .attr("y", 112)
      .attr("text-anchor", "middle")
      .text("No hay eventos para comparar.");
    return;
  }

  const nodes = [];
  const links = [];
  let nextX = 0;
  let maxDepth = 0;
  function place(node, depth = 0) {
    if (node.left) place(node.left, depth + 1);
    const position = {
      data: node,
      depth,
      x: 60 + nextX * NODE_GAP,
      y: 34 + depth * LEVEL_GAP,
    };
    nextX += 1;
    maxDepth = Math.max(maxDepth, depth);
    nodes.push(position);
    if (node.right) place(node.right, depth + 1);
  }
  place(tree);
  const positions = new Map(nodes.map((position) => [position.data, position]));
  links.length = 0;
  nodes.forEach(({ data, depth }) => {
    const source = positions.get(data);
    [data.left, data.right].filter(Boolean).forEach((child) => {
      links.push({ source, target: positions.get(child) });
    });
  });
  const width = Math.max(640, nextX * NODE_GAP + 40);
  const height = Math.max(240, (maxDepth + 1) * LEVEL_GAP + 40);
  const canvas = d3.select(svg);

  canvas
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("width", width)
    .attr("height", height)
    .attr("preserveAspectRatio", "xMidYMin meet");

  canvas
    .append("g")
    .attr("class", "comparison-links")
    .selectAll("path")
    .data(links)
    .join("path")
    .attr("d", (link) => {
      const startY = link.source.y + 21;
      const endY = link.target.y - 21;
      const middleY = (startY + endY) / 2;
      return `M${link.source.x},${startY} C${link.source.x},${middleY} ${link.target.x},${middleY} ${link.target.x},${endY}`;
    });

  const groups = canvas
    .append("g")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .attr("class", `comparison-node comparison-${kind}`)
    .attr("transform", (node) => `translate(${node.x},${node.y})`);

  groups
    .append("title")
    .text(
      (node) =>
        `Evento #${node.data.identifier} · Prioridad ${node.data.priority} · Magnitud ${node.data.magnitude}`,
    );
  groups.append("circle").attr("r", 22);
  groups
    .append("text")
    .attr("class", "comparison-node-id")
    .attr("y", 4)
    .text((node) => node.data.identifier);
  groups
    .append("text")
    .attr("class", "comparison-node-detail")
    .attr("y", 38)
    .text((node) => `P${node.data.priority} · M ${node.data.magnitude}`);
}
