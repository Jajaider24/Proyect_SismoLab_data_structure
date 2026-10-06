"""Calculo puro de indicadores operativos del catalogo."""

from collections import deque

from src.models.event import AttentionState


class EventMetrics:
    """Deriva contadores y recorridos sin modificar eventos ni estructura."""

    def calculate(self, active, archived, deleted, root, indicators):
        events = list(active.values())
        traversals = {"inorder": [], "preorder": [], "postorder": [], "level_order": []}
        leaves = 0
        costly = []
        if root is not None:
            current = root
            stack = []
            while current is not None or stack:
                while current is not None:
                    stack.append(current)
                    current = current.getLeftChild()
                current = stack.pop()
                traversals["inorder"].append(current.getIdentifier())
                current = current.getRightChild()

            stack = [root]
            while stack:
                node = stack.pop()
                traversals["preorder"].append(node.getIdentifier())
                if node.getLeftChild() is None and node.getRightChild() is None:
                    leaves += 1
                if node.getPriority() == 3 and node.getNodeDepth() > 2:
                    costly.append(node.getIdentifier())
                if node.getRightChild() is not None:
                    stack.append(node.getRightChild())
                if node.getLeftChild() is not None:
                    stack.append(node.getLeftChild())

            stack = [(root, False)]
            while stack:
                node, visited = stack.pop()
                if visited:
                    traversals["postorder"].append(node.getIdentifier())
                    continue
                stack.append((node, True))
                if node.getRightChild() is not None:
                    stack.append((node.getRightChild(), False))
                if node.getLeftChild() is not None:
                    stack.append((node.getLeftChild(), False))

            queue = deque([root])
            while queue:
                node = queue.popleft()
                traversals["level_order"].append(node.getIdentifier())
                if node.getLeftChild() is not None:
                    queue.append(node.getLeftChild())
                if node.getRightChild() is not None:
                    queue.append(node.getRightChild())

        priority_counts = {
            str(priority): sum(event.priority == priority for event in events)
            for priority in (1, 2, 3)
        }
        archived_count = len(archived)
        deleted_count = len(deleted)
        return {
            "active": len(events),
            "archived": archived_count,
            "deleted": deleted_count,
            "historical": archived_count + deleted_count,
            "priority_3": priority_counts["3"],
            "pending": sum(event.attention == AttentionState.PENDING for event in events),
            "priority_counts": priority_counts,
            "height": root.getHeight() if root is not None else -1,
            "leaves": leaves,
            "traversals": traversals,
            "accepted_corrections": indicators["accepted_corrections"],
            "discarded_reports": indicators["discarded_reports"],
            "conflicts": indicators["conflicts"],
            "bulk_archives": indicators["bulk_archives"],
            "archived_events": archived_count,
            "rotation_cases": dict(indicators["rotation_cases"]),
            "simple_rotations": dict(indicators["simple_rotations"]),
            "costly_access_events": len(costly),
            "costly_access_identifiers": sorted(costly),
            "costly_access_depth_limit": 2,
        }
