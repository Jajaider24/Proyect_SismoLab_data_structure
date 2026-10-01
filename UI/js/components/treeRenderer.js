export function renderTree(treeData, onSelect = () => {}) {
  const canvas = d3.select("#tree-canvas");
  canvas.selectAll("*").remove();
  if (!treeData) return;

  const root = d3.hierarchy(treeData);
  const nodes = root.descendants();
  const width = Math.max(720, canvas.node().clientWidth || 720);
  const height = Math.max(520, (root.height + 1) * 105);
  canvas.attr("viewBox", `0 0 ${width} ${height}`).attr("height", height);
  d3.tree().size([width - 80, height - 100])(root);
  root.descendants().forEach((node) => { node.x += 40; node.y += 45; });

  canvas.append("g").selectAll("path")
    .data(root.links()).join("path")
    .attr("class", "link")
    .attr("d", d3.linkVertical().x((d) => d.x).y((d) => d.y));

  const groups = canvas.append("g").selectAll("g")
    .data(nodes).join("g")
    .attr("class", "node")
    .attr("transform", (d) => `translate(${d.x},${d.y})`);
  groups.on("click", (_event, node) => onSelect(node.data));
  groups.append("circle").attr("r", 24);
  groups.append("text").attr("y", 5).text((d) => d.data.value);
  groups.append("text").attr("class", "height").attr("y", 42)
    .text((d) => `h:${d.data.height}  bf:${d.data.balance_factor}`);
}
