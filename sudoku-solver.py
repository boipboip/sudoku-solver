# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 10:11:08 2023

@author: bip
"""

"""
1 2 3
4 5 6
7 8 9
"""

from tkinter import Tk, Canvas, Frame, Button, BOTH, TOP, BOTTOM, Checkbutton
import tkinter as tki

import random
import copy
import threading
import time


MARGIN = 20  # Pixels around the board
SIDE = 50  # Width of every board cell.
WIDTH = HEIGHT = MARGIN * 2 + SIDE * 9  # Width and height of the whole board


class Sudoku:
    def __init__(self, val=[]):

        # Example sudoku
        """
        self.data = [[0,0,0,8,2,6,0,0,7,],
                     [8,9,2,5,0,1,0,0,4,],
                     [1,6,0,4,0,0,0,0,8,],
                     [0,1,0,0,0,2,0,0,0,],
                     [0,8,6,0,3,0,2,4,9,],
                     [0,0,0,0,0,0,0,0,1,],
                     [0,3,0,0,1,8,0,7,6,],
                     [0,0,0,0,4,0,0,8,2,],
                     [0,4,0,7,0,0,0,1,5,]]
        """

        if(val == []):
            self.data = [[9, 5, 0, 0, 0, 2, 0, 0, 0, ],
                     [0, 3, 1, 4, 5, 9, 0, 6, 0, ],
                     [0, 2, 0, 0, 3, 0, 0, 0, 0, ],
                     [7, 6, 8, 9, 0, 4, 0, 0, 3, ],
                     [0, 0, 3, 0, 0, 7, 0, 0, 6, ],
                     [0, 0, 2, 0, 0, 0, 0, 8, 0, ],
                     [2, 8, 0, 0, 0, 5, 6, 7, 0, ],
                     [0, 7, 6, 0, 9, 0, 0, 0, 5, ],
                     [0, 4, 0, 2, 0, 6, 3, 0, 8, ]]
        else:
            self.data = val

        self.attempt = copy.deepcopy(self.data)

    def printout(self) -> None:
        print("-------------------------")
        rcount = 0
        count = 0
        for row in self.attempt:
            count = 0
            for c in row:
                if (count % 3 == 0):
                    print("| ", end="")
                print(f"{c} ", end="")
                count += 1
            print("|", end="")
            rcount += 1
            if (rcount % 3 == 0):
                print()
                for i in range(count + 3):
                    print("--", end="")
                print("-", end="")
            print()

    # returns the row indexed at r
    def getRow(self, r: int) -> list[int]:
        return self.attempt[r]

    # returns the column indexed at c
    def getCol(self, c: int) -> list[int]:
        res = []
        for i in range(9):
            res.append(self.attempt[i][c])
        return res

    # returns the local 3x3 group at (r,c) as list
    def getLocal(self, r: int, c: int) -> list[int]:
        res = []
        rStart = int(r / 3) * 3
        cStart = int(c / 3) * 3
        for i in range(rStart, rStart + 3):
            for j in range(cStart, cStart + 3):
                res.append(self.attempt[i][j])
        return res

    def getNextEmpty(self) -> tuple[int, int]:
        for r in range(9):
            if (0 in self.attempt[r]):
                return (r, self.attempt[r].index(0))
        return (-1, -1)

    # Will wipe all attempts, beware!
    def restoreOGData(self) -> None:
        self.attempt = copy.deepcopy(self.data)

    # check for erroneous inputs pls
    def fill(self, r: int, c: int, val: int, v=False, guess=False) -> None:
        if ((r not in range(0, 10)) \
                or (c not in range(0, 10)) \
                or (val not in range(1, 10))):
            print(f"ERROR filling ({r},{c}) with {val}")
            return
        if (v):
            if (guess):
                print(f"## filling ({r},{c}) with {val}")
            else:
                print(f"filling ({r},{c}) with {val}")

        self.attempt[r][c] = val

    def isFull(self) -> bool:
        return not any(0 in temp for temp in self.attempt)

    def getPossible(self, r: int, c: int) -> list[int]:
        oneToNineSet = {1, 2, 3, 4, 5, 6, 7, 8, 9, }
        rSet = set(self.getRow(r))
        cSet = set(self.getCol(c))
        bSet = set(self.getLocal(r, c))
        return sorted(list(oneToNineSet - (rSet | cSet | bSet)))

    # returns true if 9x9 passes the rule check, otherwise
    # returns false.
    def checkRule(self) -> bool:
        if not self.isFull():
            return False
        for r in range(9):
            row = self.getRow(r)
            if (len(set(row)) != len(row)):
                return False
        for c in range(9):
            col = self.getCol(c)
            if (len(set(col)) != len(col)):
                return False
        for r in range(3):
            for c in range(3):
                loc = self.getLocal(r * 3, c * 3)
                if (len(set(loc)) != len(loc)):
                    return False
        return True


class SudokuSaveState(Sudoku):

    def __init__(self) -> None:
        super().__init__()


        # Record what assumption was taken
        # to advance to next state.
        # Makes it possible for
        # back tracing.
        self.visited = {}
        for i in range(9):
            for j in range(9):
                self.visited[(i, j)] = []

        # After taking an assumption, the
        # assumed value should be also added
        # to the visited list.
        # When a state exhausted all possible values,
        # a rollback should take place, trying
        # _other_ possible values of previous state.
        # In the case where rollback is impossible,
        # the solution does not exist.


class SudokuSolver:

    def __init__(self, sdk: Sudoku) -> None:
        self.states = []

        self.currentPos = 0  # current position in Savestates

        self.states.append(SudokuSaveState())

        # Copy over data+attempt from sdk to our first SaveState
        self.states[0].data = copy.deepcopy(sdk.data)
        self.states[0].attempt = copy.deepcopy(sdk.attempt)
        
        self.emptyCount = 0
        
        for i in range(9):
            for j in range(9):
                if(self.states[0].data[i][j] == 0):
                    self.emptyCount += 1
        
        self.stateAdvance()

        print("SudokuSolver Ready.")

    # For each tile, if it is not 0, skip.
    # if it is 0, get all possible val, put one in, append to visited
    # go to next tile.
    # if a tile has no possible val, rollback state.
    # if all tiles have been filled, solution is completed.
    def solve(self, verbose=True) -> None:

        while(not self.states[self.currentPos].isFull()):
            # try to make an decision on a tile
            r, c = self.states[self.currentPos].getNextEmpty()
            possibles = self.states[self.currentPos].getPossible(r, c)
            v = self.states[self.currentPos].visited[(r, c)]
            possibles = [t for t in possibles if t not in v]
            
            # Check if we can continue with this tile
            if (len(possibles) == 0):
                chk = self.stateRollback(verbose)
                if (not chk):
                    print("Solution Does not Exist.")
                    return  # no solution found
                continue

            pick = possibles.pop()

            self.states[self.currentPos].fill(r, c, pick, False)
            self.states[self.currentPos].visited[(r, c)].append(pick)
            
            # Advance the state when visited is recorded and
            # the tile has been filled.
            self.stateAdvance(verbose)
        
        if(self.states[self.currentPos].checkRule()):
            print("Solution Complete.")
            self.states[self.currentPos].printout()
        else:
            # This should not happen.
            print("Solution Failed.")
            self.states[self.currentPos].printout()

    # Duplicate the SaveState at currentPos to currentPos+1,
    # then advances currentPos.
    def stateAdvance(self, v=True) -> None:
        #print(f"\tState {self.currentPos} -> State {self.currentPos + 1}")
        self.states.append(SudokuSaveState())
        self.currentPos += 1
        
        if(v):
            print("[",end='')
            for i in range(self.emptyCount):
                if(i in range(self.currentPos)):
                    print("+", end='')
                else:
                    print(".", end='')
            print("]")

        self.states[self.currentPos] = \
            copy.deepcopy(self.states[self.currentPos - 1])

    # Returns False if currentPos is at 0.
    # Recover changes to the attempt using state at currentPos-2
    def stateRollback(self, v=True) -> bool:
        #print(f"\tState {self.currentPos} -> State {self.currentPos - 1}")
        if (self.currentPos == 0):
            return False
        self.states.pop()
        self.currentPos -= 1
        self.states[self.currentPos].attempt = copy.deepcopy( \
            self.states[self.currentPos-1].attempt)  # recover changes

        if(v):
            print("[",end='')
            for i in range(self.emptyCount):
                if(i in range(self.currentPos)):
                    print("+", end='')
                else:
                    print(".", end='')
            print("]")

        return True




class SudokuUI(Frame):
    """
    The Tkinter UI, responsible for drawing the board and accepting user input.
    """
    def __init__(self, parent):
        '''
        self.request = [[0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ],
                     [0, 0, 0, 0, 0, 0, 0, 0, 0, ]]
        '''
        self.request = [[9, 5, 0, 0, 0, 2, 0, 0, 0, ],
                 [0, 3, 1, 4, 5, 9, 0, 6, 0, ],
                 [0, 2, 0, 0, 3, 0, 0, 0, 0, ],
                 [7, 6, 8, 9, 0, 4, 0, 0, 3, ],
                 [0, 0, 3, 0, 0, 7, 0, 0, 6, ],
                 [0, 0, 2, 0, 0, 0, 0, 8, 0, ],
                 [2, 8, 0, 0, 0, 5, 6, 7, 0, ],
                 [0, 7, 6, 0, 9, 0, 0, 0, 5, ],
                 [0, 4, 0, 2, 0, 6, 3, 0, 8, ]]
        
        self.s = Sudoku()
        self.ss = SudokuSolver(self.s)
        
        self.tkVar = tki.IntVar()
        
        Frame.__init__(self, parent)
        self.parent = parent
        self.parent.resizable(False, False)
        self.row, self.col = -1, -1

        self.__initUI()

    def __initUI(self):
        self.parent.title("Sudoku Solver")
        self.pack(fill=BOTH)
        self.canvas = Canvas(self,
                             width=WIDTH,
                             height=HEIGHT)
        self.canvas.pack(fill=BOTH, side=TOP)
        self.buttonsFrame = Frame(self)
        self.buttonsFrame.pack(side=BOTTOM)
        gen_button = Button(self.buttonsFrame,
                              text="Generate Solution",
                              command=self.__gen_solution)
        gen_button.pack(fill="y",side="left")
        
        next_button = Button(self.buttonsFrame,
                              text="this button doesnt work",
                              command=self.__clear)
        next_button.pack(fill="y",side="top")
        
        chkBtn = Checkbutton(self.buttonsFrame, text="Be Quiet", 
                             variable=self.tkVar, onvalue=1, offvalue=0)
        chkBtn.pack(fill="y",side="right")
        
        self.__draw_grid()
        self.__draw_puzzle()

        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __draw_grid(self):
        """
        Draws grid divided with blue lines into 3x3 squares
        """
        for i in range(10):
            color = "blue" if i % 3 == 0 else "gray"

            x0 = MARGIN + i * SIDE
            y0 = MARGIN
            x1 = MARGIN + i * SIDE
            y1 = HEIGHT - MARGIN
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

            x0 = MARGIN
            y0 = MARGIN + i * SIDE
            x1 = WIDTH - MARGIN
            y1 = MARGIN + i * SIDE
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    def __draw_puzzle(self):
        self.canvas.delete("numbers")
        for i in range(9):
            for j in range(9):
                answer = self.request[i][j]
                if answer != 0:
                    x = MARGIN + j * SIDE + SIDE / 2
                    y = MARGIN + i * SIDE + SIDE / 2
                    original = self.request[i][j]
                    color = "black" if answer == original else "red"
                    self.canvas.create_text(
                        x, y, text=answer, tags="numbers", fill=color
                    )

    def __draw_cursor(self):
        self.canvas.delete("cursor")
        if self.row >= 0 and self.col >= 0:
            x0 = MARGIN + self.col * SIDE + 1
            y0 = MARGIN + self.row * SIDE + 1
            x1 = MARGIN + (self.col + 1) * SIDE - 1
            y1 = MARGIN + (self.row + 1) * SIDE - 1
            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                outline="red", tags="cursor"
            )


    def __cell_clicked(self, event):
        x, y = event.x, event.y
        if (MARGIN < x < WIDTH - MARGIN and MARGIN < y < HEIGHT - MARGIN):
            self.canvas.focus_set()

            # get row and col numbers from x,y coordinates
            row, col = int((y - MARGIN) / SIDE), int((x - MARGIN) / SIDE)
            self.row, self.col = row, col
        else:
            self.row, self.col = -1, -1

        self.__draw_cursor()

    def __key_pressed(self, event):
        if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
            self.request[self.row][self.col] = int(event.char)
            self.col, self.row = -1, -1
            self.__draw_puzzle()
            self.__draw_cursor()


    def __gen_solution(self):
        self.s = Sudoku(self.request)
        self.ss = SudokuSolver(self.s)
        
        v = int(self.tkVar.get())
        if(v == 1):
            start_time = time.time()
            self.ss.solve(verbose=False)
            print("\t Took %s Seconds." % (time.time() - start_time))
        else:
            start_time = time.time()
            self.ss.solve(verbose=True)
            print("\t Took %s Seconds." % (time.time() - start_time))
        
        self.canvas.delete("numbers")
        for i in range(9):
            for j in range(9):
                answer = self.ss.states[self.ss.currentPos].attempt[i][j]
                if answer != 0:
                    x = MARGIN + j * SIDE + SIDE / 2
                    y = MARGIN + i * SIDE + SIDE / 2
                    original = self.ss.states[self.ss.currentPos].data[i][j]
                    color = "black" if answer == original else "red"
                    self.canvas.create_text(
                        x, y, text=answer, tags="numbers", fill=color
                    )
                    
    def __clear(self):
        pass

if (__name__ == "__main__"):
    

    root = Tk()
    SudokuUI(root)
    root.geometry("%dx%d" % (WIDTH, HEIGHT + 40))
    root.mainloop()







