class Node:
    """Class node to AVL and BST tree"""
    def __init__(self, value):
        self.value = value
        self.parent = None
        self.height = 0
        self.LeftChild = None
        self.RightChild = None


    def getValue(self):
        return self.value
    def setValue(self,value):
        self.value = value

    def getParent(self):
        return self.parent
    def setParent(self,parent):
        self.parent = parent

    def getLeftChild(self):
        return self.LeftChild
    def setLeftChild(self,LeftChild):
        self.LeftChild = LeftChild

    def getRightChild(self):
        return self.RightChild
    def setRightChild(self,RightChild):
        self.RightChild = RightChild

    def getHeight(self):
        return self.height
    def setHeight(self,height):
        self.height = height
    

