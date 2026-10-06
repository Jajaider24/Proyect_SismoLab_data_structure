export function flattenTree(tree, result = []) {
  if (!tree) return result;
  result.push(tree);
  tree.children?.forEach((child) => flattenTree(child, result));
  return result;
}

export function findNode(tree, identifier) {
  if (!tree) return null;
  if (tree.attributes.identificador === identifier) return tree;
  for (const child of tree.children || []) {
    const found = findNode(child, identifier);
    if (found) return found;
  }
  return null;
}

