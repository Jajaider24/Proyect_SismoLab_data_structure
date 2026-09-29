from src.core.AvlTree.metodos.balance import check_balance

def insert_node(node,currentRoot):
        """Función de insercion de nodos"""

        #verifico que el nodo a insertar no exista o sea la raiz actual
        if node.getValue() == currentRoot.getValue():
            print(f"Value {node.getValue()} alredy exists.")

        #validación para saber si voy por el lado derecho porque el nodo es mayor a la raiz actual
        elif node.getValue() > currentRoot.getValue():
            #valido si el hizo derecho de la raiz es none
            if currentRoot.getRightChild() is None:
                #le asigno a la raiz el hijo derecho (node)
                currentRoot.setRightChild(node)
                #le asigno a el hijo derecho su padre (currentRoot)
                node.setParent(currentRoot)
                #función para balancear el árbol en caso de desbalanceo
                check_balance(currentRoot.getParent())
            #en caso de que el hijo derecho no sea none, se pasa el hijo derecho como raiz(currentRoot)
            #y se hace el llamado recursivo
            else:
                insert_node(currentRoot.getRightChild(),node)
        #voy por la izquierda en caso de que el nodo sea menor a la raiz actual
        else:
            #valido si el hijo izquierdo es none
            if  currentRoot.getLeftChild() is None:
                #le asingo a la raiz el hijo izquierdo (node)
                currentRoot.setLeftChild(node)
                #le asigno a el hijo izquierdo el padre (currentRoot)
                node.setParent(currentRoot)
                #funcion para balancear el árbol en caso de desbalanceo
                check_balance(currentRoot.getParent())
            #en caso de que el hijo izquierdo no sea none, se pasa el hijo izquierdo como raiz (currentRoot)
            #y se hace el llamado recursivo
            else:
                insert_node(currentRoot.LeftChild(),node)



