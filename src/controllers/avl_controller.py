from src.services.Avlservice import avl_tree_service


def insert_value(value: int):
    inserted = avl_tree_service.insert_node(value)
    return {
        "inserted": inserted,
        "value": value,
        "values": avl_tree_service.get_values(),
    }