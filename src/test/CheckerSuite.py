import unittest
from TestUtils import TestChecker
from AST import *
from Visitor import *
from StaticError import *
from abc import ABC

class CheckerSuite(unittest.TestCase):
    def test401(self):
        """Simple program"""
        input = """main: function void () {
        }"""
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 401))
        
    def test402(self):
        input = """x: integer;
        main: function void () {
        }"""
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 402))
        
    def test403(self):
        input = """ x: integer;
                    main: function void () {
                    }
                    x: float;"""
        expect = "Redeclared Variable: x"
        self.assertTrue(TestChecker.test(input, expect, 403))
        
    def test404(self):
        input = """x: integer;
        foo: function void () {
        }"""
        expect = "No entry point"
        self.assertTrue(TestChecker.test(input, expect, 404))
        
    def test405(self):
        input = """x: integer;
        main: function integer () {
        }"""
        expect = "No entry point"
        self.assertTrue(TestChecker.test(input, expect, 405))
        
    def test406(self):
        input = """x: integer;
        main: function integer () {
        }
        main: function void () {
        }"""
        expect = "Redeclared Function: main"
        self.assertTrue(TestChecker.test(input, expect, 406))
        
    def test407(self):
        input = """ x: integer;
                    main: function void () {
                        b: float; 
                        b: string;
                    }
                    x: float;
        """
        expect = "Redeclared Variable: b"
        self.assertTrue(TestChecker.test(input, expect, 407))
        
    def test408(self):
        input = """ x: integer;
                    main: function void (b: float, b: string) {
                    }
                    x: float;
        """
        expect = "Redeclared Parameter: b"
        self.assertTrue(TestChecker.test(input, expect, 408))
        
    def test409(self):
        input = """ x: integer;
                    main: function void () {
                        y: float;
                        z: boolean;
                        
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 409))
        
    def test410(self):
        input = """ x: integer;
                    main: function void (b: float, c: string) {
                        x: float = 2.0;
                        z: boolean = 2;
                        
                    }
        """
        expect = "Type mismatch in Variable Declaration: VarDecl(z, BooleanType, IntegerLit(2))"
        self.assertTrue(TestChecker.test(input, expect, 410))
        
    def test411(self):
        input = """ x: integer;
                    main: function void () {
                        x: float = 2.0;
                        z: auto = 2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 411)) 
        
    def test412(self):
        input = """ x: integer;
                    main: function void (b: auto, c: string) {
                        
                        x: float = 2.0;
                        preventDefault();
                        z: auto = 2;
                    }
        """
        expect = "Invalid statement in function: main"
        self.assertTrue(TestChecker.test(input, expect, 412))   
        
    def test413(self):
        input = """ x: integer;
                    main: function void () {
                        x: float = 2.0;
                        printInteger(4);
                        z: auto = 2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 413))  
        
    def test414(self):
        input = """ x: integer;
                    main: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger();
                        z: auto = 2;
                    }
        """
        expect = "Type mismatch in statement: CallStmt(printInteger, )"
        self.assertTrue(TestChecker.test(input, expect, 414))
        
    def test415(self):
        input = """ x: integer;
                    main: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger(2.0);
                        z: auto = 2;
                    }
        """
        expect = "Type mismatch in statement: CallStmt(printInteger, FloatLit(2.0))"
        self.assertTrue(TestChecker.test(input, expect, 415))
        
    def test416(self):
        input = """ x: integer;
                    main: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger(2, "a");
                        z: auto = 2;
                    }
        """
        expect = "Type mismatch in statement: CallStmt(printInteger, IntegerLit(2), StringLit(a))"
        self.assertTrue(TestChecker.test(input, expect, 416))
        
    def test417(self):
        input = """ x: integer;
                    main: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger("a", 2);
                        z: auto = 2;
                    }
        """
        expect = "Type mismatch in statement: CallStmt(printInteger, StringLit(a), IntegerLit(2))"
        self.assertTrue(TestChecker.test(input, expect, 417))
        
    def test418(self):
        input = """ x: integer;
                    main: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger("a", 2);
                        z: auto = 2;
                    }
                    
                    main: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger("a", 2);
                        z: auto = 2;
                    }
        """
        expect = "Type mismatch in statement: CallStmt(printInteger, StringLit(a), IntegerLit(2))"
        self.assertTrue(TestChecker.test(input, expect, 418))
        
    def test419(self):
        input = """ x: integer;
                    foo: function void (b: integer, c: string) {
                        x: float = 2.0;
                        readInteger(2);
                        z: auto = 2;
                    }
        """
        expect = "Type mismatch in statement: CallStmt(readInteger, IntegerLit(2))"
        self.assertTrue(TestChecker.test(input, expect, 419))
        
    def test420(self):
        input = """ x: integer;
                    foo: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void (b: integer, c: string) inherit foo {
                        x: float = 2.0;
                        printInteger("a", 2);
                        z: auto = 2;
                    }
        """
        expect = "Invalid statement in function: main"
        self.assertTrue(TestChecker.test(input, expect, 420))
        
    def test421(self):
        input = """ x: integer;
                    foo: function void (b: integer, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void (b: integer, c: string) inherit foo {
                        super();
                        x: float = 2.0;
                        printInteger("a", 2);
                        z: auto = 2;
                    }
        """
        expect = "Type mismatch in expression: "
        self.assertTrue(TestChecker.test(input, expect, 421))
        
    def test422(self):
        input = """ x: integer;
                    foo: function void (b: float, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void () inherit foo {
                        super(33, "33");
                        x: float = 2.0;
                        z: auto = 2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 422))
    
    def test423(self):
        input = """ x: integer;
                    foo: function void (b: float, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void (b: integer, c: string) inherit foo {
                        super(33, "33");
                        b: float = 2.0;
                        z: auto = 2;
                    }
        """
        expect = "Redeclared Variable: b"
        self.assertTrue(TestChecker.test(input, expect, 423))
        
    def test424(self):
        input = """ x: integer;
                    main: function void (b: integer, c: string) inherit foo {
                        super(33, "33");
                        b: float = 2.0;
                        z: auto = 2;
                    }
        """
        expect = "Undeclared Function: foo"
        self.assertTrue(TestChecker.test(input, expect, 424))
    
    def test425(self):
        input = """ x: integer;
                    foo: function void (inherit b: float, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void (b: integer, c: string) inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        z: auto = 2;
                    }
        """
        expect = "Invalid Parameter: b"
        self.assertTrue(TestChecker.test(input, expect, 425))   
        
    def test426(self):
        input = """ x: integer;
                    foo: function void (inherit b: float, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void () inherit foo {
                        preventDefault();
                        y: float = 2.0;
                        z: auto = 2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 426)) 
        
    def test427(self):
        input = """ x: integer;
                    foo: function void (inherit a: float, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void (b: integer, c: string) inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        a: auto = 2;
                    }
        """
        expect = "Redeclared Variable: a"
        self.assertTrue(TestChecker.test(input, expect, 427)) 
        
    def test428(self):
        input = """ x: integer;
                    foo: function void (inherit a: float, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
                    
                    main: function void () inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        // a: auto = 2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 428)) 
        
    def test429(self):
        input = """ x: integer;                 
                    main: function void (b: integer, c: string) inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        a: auto = 2;
                    }
                    foo: function void (inherit a: float, c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
        """
        expect = "Redeclared Variable: a"
        self.assertTrue(TestChecker.test(input, expect, 429)) 
        
    def test430(self):
        input = """ x: integer;                 
                    main: function void (b: integer, c: string) inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        a: auto = 2;
                    }
                    foo: function void (inherit b: float, inherit b: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
        """
        expect = "Redeclared Parameter: b"
        self.assertTrue(TestChecker.test(input, expect, 430))
        
    def test431(self):
        input = """ x: integer;                 
                    main: function void (b: integer, c: string) inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        a: auto = 2;
                    }
                    foo: function void (b: float, inherit c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
        """
        expect = "Invalid Parameter: c"
        self.assertTrue(TestChecker.test(input, expect, 431))
        
    def test432(self):
        input = """ x: integer;                 
                    main: function void () inherit foo {
                        y: float = 2.0;
                        a: auto = 2;
                        printInteger(2);
                    }
                    foo: function void () {
                        x: float = 2.0;
                        
                        z: auto = 2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 432))
        
    def test433(self):
        input = """ x: integer;                 
                    main: function void () inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        a: auto = 2;
                        c = "str";
                    }
                    foo: function void (b: float, inherit c: string) {
                        x: float = 2.0;
                        printInteger(2);
                        z: auto = 2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 433))
    
    def test434(self):
        input = """ x: integer;                 
                    main: function void () inherit foo {
                        super(33, "33");
                        y: float = 2.0;
                        a: auto = 2;
                    }
                    foo: function void (b: float, inherit d: string) {
                        x: float = 2.0;
                        main();
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 434))
        
    def test435(self):
        input = """ x: integer;           
                    y: auto = true;      
                    main: function void () {
                    }
                    foo: function boolean (a: float, inherit b: string) {
                        return y + true;
                    }
                    bar: function float (c: boolean, d: auto) {
                        return x + d;
                    }
        """
        expect = "Type mismatch in expression: BinExpr(+, Id(y), BooleanLit(True))"
        self.assertTrue(TestChecker.test(input, expect, 435))
        
    def test436(self):
        input = """ x: integer;                 
                    main: function void (b: integer, c: boolean) {
                        y: float = 2.0;
                        a: auto = 2;
                        return 2;
                    }
        """
        expect = "Type mismatch in statement: ReturnStmt(IntegerLit(2))"
        self.assertTrue(TestChecker.test(input, expect, 436))
        
    def test437(self):
        input = """ x: integer;                 
                    main: function void () {
                        y: string = "str";
                        a: auto = 2;
                        foo(a, y);
                    }
                    foo: function boolean (b: float, inherit d: string) {
                        x: float = 2.0;
                        main();
                        return true;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 437))
        
    def test438(self):
        input = """ x: integer;                 
                    main: function void () {
                    }
                    foo: function boolean (b: float, inherit d: string) {
                        x: float = 2.0;
                        main(2, true);
                        return true;
                    }
        """
        expect = "Type mismatch in statement: CallStmt(main, IntegerLit(2), BooleanLit(True))"
        self.assertTrue(TestChecker.test(input, expect, 438))
        
    def test439(self):
        input = """ x: integer;           
                    y: auto = true;      
                    main: function void () {
                    }
                    foo: function boolean (a: boolean, inherit b: string) {
                        return !y && a;
                    }
                    bar: function float (c: float, d: auto) {
                        return x + d;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 439))
        
    def test440(self):
        input = """ x: integer;           
                    y: auto = true;      
                    main: function void () {
                    }
                    foo: function boolean (a: float, inherit b: string) {
                        return y;
                    }
                    bar: function float (c: boolean, d: auto) {
                        return x + d;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 440))
    
    def test441(self):
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
        expect = "Type mismatch in expression: BinExpr(||, Id(y), Id(a))"
        self.assertTrue(TestChecker.test(input, expect, 441))
        
    def test442(self):
        input = """ x: integer;           
                    y: auto = true;      
                    main: function void () {
                    }
                    foo: function boolean (a: float, inherit b: string) {
                        return y || (a == 2.0);
                    }
                    bar: function float (c: boolean, d: auto) {
                        c = foo(2, "2");
                        return x + d;
                    }
        """
        expect = "Type mismatch in expression: BinExpr(==, Id(a), FloatLit(2.0))"
        self.assertTrue(TestChecker.test(input, expect, 442))
        
    def test443(self):
        input = """ x: integer;           
                    y: auto = true;      
                    main: function void () {
                    }
                    foo: function boolean (a: float, inherit b: string) {
                        x: integer = 2;
                        return y || (x == 2);
                    }
                    bar: function float (c: boolean, d: auto) {
                        c = foo(2, "2");
                        s1: string = "s1"; 
                        s2: string = s1 :: "s2";
                        return x + d;
                        return s2;
                    }
        """
        expect = ""
        self.assertTrue(TestChecker.test(input, expect, 443))
        
    def test444(self):
        input = """ x: integer;           
                    y: auto = true;      
                    main: function void () {
                        bar(false, 2);
                    }
                    foo: function boolean (a: float, inherit b: string) {
                        x: integer = 2;
                        return y || (x == 2);
                    }
                    bar: function float (c: boolean, d: auto) {
                        c = foo(2, "2");
                        d = c;
                        return x + d;
                    }
        """
        expect = "Type mismatch in statement: AssignStmt(Id(d), Id(c))"
        self.assertTrue(TestChecker.test(input, expect, 444))
        
    def test445(self):
        input = """ x: array[3] of integer;           
                    y: array[3] of integer = {1, 2, 3, 4}; 
                    foo: function array[3] of integer () {
                    }    
                    main: function void() {} 
        """
        expect = "Type mismatch in Variable Declaration: VarDecl(y, ArrayType([3], IntegerType), ArrayLit([IntegerLit(1), IntegerLit(2), IntegerLit(3), IntegerLit(4)]))"
        self.assertTrue(TestChecker.test(input, expect, 445))
    def test450(self):
        input = """ 
        fact: function auto (m:integer, n: float) inherit foo {
            super(1.0,1.0,true);
            return foo(1,1.0,"true");
        }
        foo: function integer (x:auto, y: auto, z:auto) {}
        main: function void(){
            
        }
        """
        expect = """Type mismatch in statement: ReturnStmt(FuncCall(foo, [IntegerLit(1), FloatLit(1.0), StringLit(true)]))"""
        self.assertTrue(TestChecker.test(input, expect, 450))
    def test451(self):
        input = """ 
        fact: function void (m:integer, n: float) inherit foo {
            super(1.0,1.0,true);
            return foo(1,1.0,"true");
        }
        foo: function integer (x:auto, y: auto, z:auto) {}
        main: function void(){
            
        }
        """
        expect = """Type mismatch in statement: ReturnStmt(FuncCall(foo, [IntegerLit(1), FloatLit(1.0), StringLit(true)]))"""
        self.assertTrue(TestChecker.test(input, expect, 451))
    def test456(self):
        input = """ 
        fact: function integer (m:integer, n: float) inherit foo {
            super(1.0,1.0,true);
            for(m = 0, m < 1.0, m +1){
                if (true) return 1;
                else return "1";
            }
        }
        foo: function integer (inherit x:auto, y: auto, z:auto) {}
        main: function void(){
            
        }
        """
        expect = """Type mismatch in statement: ReturnStmt(StringLit(1))"""
        self.assertTrue(TestChecker.test(input, expect, 456))
        
    def test458(self):
        input = """ 
        fact: function integer (m:integer, n: float) inherit foo {
            super(1.0,1.0,true);
            for(m = 0, m < 1.0, m +1){
                if (true) return 1;
                else return 1;
                do{
                    
                }
                while(1);
            }
        }
        foo: function integer (inherit x:auto, y: auto, z:auto) {}
        main: function void(){
            
        }
        """
        expect = """Type mismatch in statement: DoWhileStmt(IntegerLit(1), BlockStmt([]))"""
        self.assertTrue(TestChecker.test(input, expect, 458))