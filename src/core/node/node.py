class Node:
    """Node shared by the unbalanced BST and the AVL tree."""

    def __init__(self, value):
        self.value = value
        self.parent = None
        self.height = 0
        self.leftChild = None
        self.rightChild = None

    def getValue(self):
        return self.value

    def setValue(self, value):
        self.value = value

    def getParent(self):
        return self.parent

    def setParent(self, parentNode):
        self.parent = parentNode

    def getLeftChild(self):
        return self.leftChild

    def setLeftChild(self, leftChildNode):
        self.leftChild = leftChildNode

    def getRightChild(self):
        return self.rightChild

    def setRightChild(self, rightChildNode):
        self.rightChild = rightChildNode

    def getHeight(self):
        return self.height

    def setHeight(self, height):
        self.height = height

    @property
    def LeftChild(self):
        return self.leftChild

    @LeftChild.setter
    def LeftChild(self, child):
        self.leftChild = child

    @property
    def RightChild(self):
        return self.rightChild

    @RightChild.setter
    def RightChild(self, child):
        self.rightChild = child


