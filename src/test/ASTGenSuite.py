import unittest
from TestUtils import TestAST
from AST import *


class ASTGenSuite(unittest.TestCase):
    def test_1(self):
        input = """x: integer;"""
        expect = str(Program([VarDecl("x", IntegerType())]))
        self.assertTrue(TestAST.test(input, expect, 301))

    def test_2(self):
        input = """ x: integer;           
                    y: auto = true;      
                    main: function void () {
                    }
                    foo: function boolean (a: float, inherit b: string) {
                        return y || a == 2;
                    }
                    bar: function float (c: boolean, d: auto) {
                        return x + d;
                    }
        """
        expect = """Program([
	VarDecl(x, IntegerType)
	VarDecl(y, AutoType, BooleanLit(True))
	FuncDecl(main, VoidType, [], None, BlockStmt([]))
	FuncDecl(foo, BooleanType, [Param(a, FloatType), InheritParam(b, StringType)], None, BlockStmt([ReturnStmt(BinExpr(==, BinExpr(||, Id(y), Id(a)), IntegerLit(2)))]))
	FuncDecl(bar, FloatType, [Param(c, BooleanType), Param(d, AutoType)], None, BlockStmt([ReturnStmt(BinExpr(+, Id(x), Id(d)))]))
])"""
        self.assertTrue(TestAST.test(input, expect, 302))

    