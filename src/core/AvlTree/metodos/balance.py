from re import match
from .rotaciones import giroSimpleDerecha,giroSimpleIzquierda


def get_height(node):
     if node is None:
          return
     return node.getHeight()

def update_height(node):
     if node is None:
          return 0
     left_height = update_height(node.getLeftChild())
     right_height = update_height(node.getRightChild())
     node.setHeight(1+ max(left_height,right_height))
     return print(f"la altura de el nodo {node.getValue()} fue actualizada")

def balance_factor(node):
     if node is None:
          print(f"el nodo está vacio")
          return 0
     left_height = get_height(node.getHeight())
     right_height = get_height(node.getHeight())
     return (left_height - right_height)


def balance_case(node):
     caso = ""
     if balance_factor(node) > 1:
          if balance_factor(node.getLeftChild()) >= 1:
               caso = "LL"
          else:
               caso = "LR"
     elif balance_factor(node) < -1:
          if balance_factor(node.getRightChild()) <= -1:
               caso = "RR"
          else:
               caso = "RL"
     return caso


def check_balance(node):
     update_height(node)
     balanceFactor = balance_factor(node)
     match(balanceFactor):
          case("LL"):
               giroSimpleIzquierda(node)
          case("RR"):
               giroSimpleDerecha(node)
          case("LR"):
               giroSimpleIzquierda(node.getLeftChild())
               update_height(node)
               giroSimpleDerecha(node)
          case("RL"):
               giroSimpleDerecha(node.RightChild())
               update_height(node)
               giroSimpleIzquierda(node)
     return None