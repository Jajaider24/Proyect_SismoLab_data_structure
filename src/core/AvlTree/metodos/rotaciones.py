#LL
def giroSimpleDerecha(superior):
    # se obtiene el hijo izquierdo de superior porque es L
    mitad = superior.getHijoIzquierdo()

    # hacemos el giro a la derecha
    # se toma como aux al hijo derecho de mitad para ponerlo luego como hijo izquierdo de superior
    aux = mitad.getHijoDerecho()
    # se asigna como padre del aux al superior cuando no es None
    if aux is not None:
        aux.setPadre(superior)
    #se asigna como hijo derecho de mitad a superior, este es el giro
    mitad.setHijoDerecho(superior)
    # se asigna como hijo izquierdo de superior el hijo derecho de mitad
    superior.setHijoIzquierdo(aux)
    # se reasignan los padres entre mitad y y superior
    mitad.setPadre(superior.getPadre())
    superior.setPadre(mitad)

  # giro simple a la izquierda (cuando el desbalanceo es RR)
def giroSimpleIzquierda(superior):
    # se obtiene el hijo derecho de superior porque es R
    mitad = superior.getHijoDerecho()

    # hacemos el giro a la izquierda
    # se toma como aux al hijo izquierdo de mitad para ponerlo luego como hijo derecho de superior
    aux = mitad.getHijoIzquierdo()
    # se asigna como padre del aux al superior cuando no es None
    if aux is not None:
        aux.setPadre(superior)
    #se asigna como hijo izquierdo de mitad a superior, este es el giro
    mitad.setHijoIzquierdo(superior)
    # se asigna como hijo derecho de superior el hijo izquierdo de mitad
    superior.setHijoDerecho(aux)
    # se reasignan los padres entre mitad y y superior
    mitad.setPadre(superior.getPadre())
    superior.setPadre(mitad)
    #revisar asignar hijo izq a la mitad y asignar al antecesor el respectivo hijo