export function renderTree(treeData, onSelect = () => {}) {
  const canvas = d3.select("#tree-canvas");
  const emptyState = document.querySelector("#tree-empty");
  canvas.selectAll("*").remove();
  emptyState.hidden = Boolean(treeData);
  canvas.attr("aria-hidden", String(!treeData));
  if (!treeData) return;

  const root = d3.hierarchy(treeData);
  const nodes = root.descendants();
  const width = Math.max(720, canvas.node().clientWidth || 720);
  const height = Math.max(520, (root.height + 1) * 105);
  canvas.attr("viewBox", `0 0 ${width} ${height}`).attr("height", height);
  d3.tree().size([width - 80, height - 100])(root);
  root.descendants().forEach((node) => {
    node.x += 40;
    node.y += 45;
  });

  canvas
    .append("g")
    .selectAll("path")
    .data(root.links())
    .join("path")
    .attr("class", "link")
    .attr("opacity", 0)
    .attr(
      "d",
      d3
        .linkVertical()
        .x((d) => d.x)
        .y((d) => d.y),
    );
  canvas
    .selectAll(".link")
    .transition()
    .duration(650)
    .delay((_d, index) => index * 55)
    .attr("opacity", 1);

  const groups = canvas
    .append("g")
    .selectAll("g")
    .data(nodes)
    .join("g")
    .attr("class", "node")
    .attr("opacity", 0)
    .attr("transform", (d) => `translate(${d.x},${d.y})`);
  groups.on("click", function (_event, node) {
    groups.classed("selected", false);
    d3.select(this).classed("selected", true);
    onSelect(node.data);
  });
  groups
    .append("circle")
    .attr("r", 24)
    .attr("class", (d) => `priority-${d.data.attributes.priority || 1}`);
  groups
    .append("text")
    .attr("y", 5)
    .text((d) => d.data.value);
  groups
    .append("text")
    .attr("class", "height")
    .attr("y", 42)
    .text((d) => `h:${d.data.height}  bf:${d.data.balance_factor}`);
  groups
    .transition()
    .duration(550)
    .delay((d) => d.depth * 110)
    .attr("opacity", 1);
}

