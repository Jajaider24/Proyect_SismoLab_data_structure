function height(node) {
  return node?.height || 0;
}

function updateHeight(node) {
  node.height = Math.max(height(node.left), height(node.right)) + 1;
  return node;
}

function rotateRight(root) {
  const pivot = root.left;
  root.left = pivot.right;
  pivot.right = root;
  updateHeight(root);
  return updateHeight(pivot);
}

function rotateLeft(root) {
  const pivot = root.right;
  root.right = pivot.left;
  pivot.left = root;
  updateHeight(root);
  return updateHeight(pivot);
}

function compareKeys(first, second) {
  for (let index = 0; index < first.length; index += 1) {
    if (first[index] < second[index]) return -1;
    if (first[index] > second[index]) return 1;
  }
  return 0;
}

function insert(root, node, balanced) {
  if (!root) return node;

  if (compareKeys(node.key, root.key) < 0) {
    root.left = insert(root.left, node, balanced);
  } else {
    root.right = insert(root.right, node, balanced);
  }

  updateHeight(root);
  if (!balanced) return root;

  const balance = height(root.left) - height(root.right);
  if (balance > 1) {
    if (compareKeys(node.key, root.left.key) > 0) root.left = rotateLeft(root.left);
    return rotateRight(root);
  }
  if (balance < -1) {
    if (compareKeys(node.key, root.right.key) < 0) root.right = rotateRight(root.right);
    return rotateLeft(root);
  }
  return root;
}

function measure(root) {
  if (!root) return { height: 0, leaves: 0, nodes: 0 };
  const left = measure(root.left);
  const right = measure(root.right);
  return {
    height: Math.max(left.height, right.height) + 1,
    leaves: root.left || root.right ? left.leaves + right.leaves : 1,
    nodes: left.nodes + right.nodes + 1,
  };
}

export function buildComparisonTrees(comparison, orderName) {
  const order = comparison.results.find((item) => item.order === orderName);
  if (!order) throw new Error("No se encontró el orden de inserción solicitado.");

  const keysByIdentifier = new Map(
    comparison.keys.map((key) => [Number(key[2]), key]),
  );
  let avlRoot = null;
  let bstRoot = null;

  order.insertion_order.forEach((identifier) => {
    const key = keysByIdentifier.get(Number(identifier));
    if (!key) return;
    const createNode = () => ({
      identifier: Number(identifier),
      priority: Number(key[0]),
      magnitude: Number(key[1]),
      key,
      height: 1,
      left: null,
      right: null,
    });
    avlRoot = insert(avlRoot, createNode(), true);
    bstRoot = insert(bstRoot, createNode(), false);
  });

  return {
    order,
    avl: { root: avlRoot, metrics: measure(avlRoot) },
    bst: { root: bstRoot, metrics: measure(bstRoot) },
  };
}
