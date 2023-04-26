from Visitor import *
from AST import *
from StaticError import *

from abc import abstractmethod, ABCMeta, ABC
from typing import List, Tuple
from functools import *
import copy

# from main.mt22.utils.Visitor import *
# from main.mt22.utils.AST import *

class Utils:
    def scopes_to_str(global_scope):
        s = "["
        for item in global_scope:
            s += "["
            for mini in item:
                s += "Symbol({}, {})".format(str(mini.name), str(mini.typ)) + ", "
            s += "],"
        s += "]"
        return s
    
    def scope_to_str(o):
        s = '['
        for mini in o:
            s += "Symbol({}, {})".format(str(mini.name), str(mini.typ)) + ", "
        s += ']'
        return s
    
    def dic_name_to_str(dic):
        s = '{'
        for key in dic:
            s += str(key) + ', '
        s += '}'
        return s
    
    def is_coercible(ltype, rtype):
        # không xét auto, không xét array
        if type(ltype) is AutoType or type(rtype) is AutoType:
            return True
        if type(ltype) is ArrayType and type(rtype) is ArrayType:
            return True
        if type(ltype) is type(rtype):
            return True
        if type(ltype) is FloatType and type(rtype) is IntegerType:
            return True
        return False

    def infer(name, typ, o): 
        for symbols in o:
            for symbol in symbols:
                if symbol.name == name:
                    symbol.typ = typ
                    return typ
        return None

    def lookup(name, o):
        for symbols in o:
            for symbol in symbols:
                if symbol.name == name:
                    return symbol
        return None


class Symbol:
    def __init__(self, name, kind: Kind, typ, inherit):
        self.name = name
        self.kind = kind
        self.typ = typ
        self.inherit = inherit
    def __str__(self):
        return "Symbol({}, {})".format(str(self.name), str(self.typ))

class ErrArrayType(Type): pass

class StaticChecker(Visitor):
    def __init__(self, ast):
        self.ast = ast
        self.dic = {}
        self.in_loop = 0
        self.scope_level = 0 #lv 0: global, lv 1: in a function
        self.returnWithFuncCall = None
    
        self.dic["readInteger"] = []
        self.dic["printInteger"] = [Symbol("anArg", Parameter(), IntegerType(), False)]   
        
        self.global_env = [
            Symbol("readInteger", Function(), StringType(), None),
            Symbol("printInteger", Function(), VoidType(), None)
        ]
        
    def check(self):
        #print("check")
        return self.visit(self.ast, self.global_env)
    
    def raiseMismatchForCheckFuncCall(self, ast):
        if isinstance(ast, FuncCall):
            if self.returnWithFuncCall:
                raise TypeMismatchInStatement(self.returnWithFuncCall)
            raise TypeMismatchInExpression(ast)
        if isinstance(ast, CallStmt):
            raise TypeMismatchInStatement(ast)
          
    # name: str, args: List[Expr]
    def checkFuncCall(self, ast, o):
        func_sym = None
        for symbols in o:
            for symbol in symbols:
                # nếu tìm được symbol giống tên nhưng không phải hàm
                if symbol.name == ast.name and type(symbol.kind) is not Function:
                    self.raiseMismatchForCheckFuncCall(ast)
                # nếu tìm được symbol là hàm giống tên
                if symbol.name == ast.name and type(symbol.kind) is Function:
                    func_sym = symbol
                    break
            if func_sym != None:
                break
        if func_sym == None:
            raise Undeclared(Function(), ast.name)
        
        # đối chiếu độ dài params và args
        func_scope = self.dic[func_sym.name]
        param_sym = [sym for sym in func_scope if type(sym.kind) is Parameter]
        params_name = [sym.name for sym in func_scope if type(sym.kind) is Parameter]
        params_type = [sym.typ for sym in func_scope if type(sym.kind) is Parameter]
        args_type = [self.visit(arg, o) for arg in ast.args]
        if len(params_type) != len(args_type):
            self.raiseMismatchForCheckFuncCall(ast)
        # so từng cặp param arg
        for idx in range(len(args_type)):
            if not Utils.is_coercible(params_type[idx], args_type[idx]):
                self.raiseMismatchForCheckFuncCall(ast)
            if type(params_type[idx]) is AutoType:
                param_sym[idx].typ = Utils.infer(params_name[idx], args_type[idx], [self.dic[ast.name]])
            if type(args_type[idx]) is AutoType:
                args_type[idx] = Utils.infer(ast.args[idx].name, params_type[idx], o)
                
            if type(params_type[idx]) is ArrayType and type(args_type[idx]) is ArrayType:
                if params_type[idx].dimensions != args_type[idx].dimensions:
                    self.raiseMismatchForCheckFuncCall(ast)
                # if isinstance(params_type[idx].typ, AutoType):
                #     params_type[idx] = Utils.infer(ast.lhs.name, args_type[idx], o)
                # if isinstance(args_type[idx].typ, AutoType):
                #     args_type[idx] = Utils.infer(ast.rhs.name, params_type[idx], o)
        
        return func_sym.typ       
                
    
    # decls: List[Decl]
    def visitProgram(self, ast: Program, o):
        global_scope = [self.global_env]
        # để check redeclared func
        red_func = 0
        red_func_name = None
        red_var = 0
        red_var_name = None
        for decl in ast.decls:
            if isinstance(decl, FuncDecl):
                red_func += self.previsitFuncDecl(decl, global_scope)
                # there is redeclared func
                if red_func < 0: red_func_name = decl.name
            elif isinstance(decl, VarDecl):
                red_var += self.previsitVarDecl(decl, global_scope)
                if red_var < 0: red_var_name = decl.name

        # nếu gặp red_func lại lần nữa, ném lỗi
        meet_red_func = 0
        meet_red_var = 0
        for decl in ast.decls:
            
            if isinstance(decl, FuncDecl):
                if red_func_name == decl.name and meet_red_func == 1:
                    raise Redeclared(Function(), decl.name)
                else: meet_red_func += 1
                self.visit(decl, global_scope)
            elif isinstance(decl, VarDecl):
                if red_var_name == decl.name and meet_red_var == 1:
                    raise Redeclared(Variable(), decl.name)
                else: meet_red_var += 1
                self.visitVarDeclInGlobal(decl, global_scope)
                
        has_entry_point = False
        for symbol in global_scope[0]:
            if symbol.name == "main" and isinstance(symbol.kind, Function) and isinstance(symbol.typ, VoidType) and len(self.dic[symbol.name]) == 0:
                has_entry_point = True
                break
        if not has_entry_point:
            raise NoEntryPoint()

    
    def previsitVarDecl(self, ast, o):
        red_var = False
        for item in o[0]:
            if ast.name == item.name:
                red_var = True
                break
        o[0] += [Symbol(ast.name, Variable(), ast.typ, None)]
        if red_var:
            return -1
        return 0
        
    
    # name: str, typ: Type, init: Expr or None = None
    def visitVarDeclInGlobal(self, ast: VarDecl, o):
        # for item in o[0]:
        #     if ast.name == item.name:
        #         raise Redeclared(Variable(), ast.name)
        
        var_symbol = None
        for symbol in o[0]:
            if ast.name == symbol.name:
                var_symbol = symbol
                break
        if ast.init:
            
            init_type = self.visit(ast.init, o)
            if type(init_type) is ErrArrayType:
                raise IllegalArrayLiteral(ast.init)
            if isinstance(ast.typ, AutoType):
                # o[0] += [Symbol(ast.name, Variable(), init_type, None)]
                var_symbol.typ = init_type
                return
            if type(ast.typ) is ArrayType and type(init_type) is ArrayType:
                if ast.typ.dimensions != init_type.dimensions:
                    raise TypeMismatchInVarDecl(ast)
                if isinstance(ast.typ.typ, AutoType):
                    ast.typ = Utils.infer(ast.name, init_type, o)
                if isinstance(init_type, AutoType):
                    init_type = Utils.infer(ast.init.name, ast.typ, o)
            if Utils.is_coercible(ast.typ, init_type):
                # đã insert ở previsitVarDecl
                # o[0] += [Symbol(ast.name, Variable(), ast.typ, None)]
                return
            else: 
                raise TypeMismatchInVarDecl(ast)
        if isinstance(ast.typ, AutoType):
            raise Invalid(Variable(), ast.name)
        # đã insert ở previsitVarDecl
        # o[0] += [Symbol(ast.name, Variable(), ast.typ, None)]
    
    # name: str, typ: Type, init: Expr or None = None
    def visitVarDecl(self, ast: VarDecl, o):
        for item in o[0]:
            if ast.name == item.name:
                raise Redeclared(Variable(), ast.name)
        
        if ast.init:
            init_type = self.visit(ast.init, o)
            
            # nếu arraylit trả về lỗi
            if type(init_type) is ErrArrayType:
                raise IllegalArrayLiteral(ast.init)
            if isinstance(ast.typ, AutoType):
                o[0] += [Symbol(ast.name, Variable(), init_type, None)]
        
                return
            if type(ast.typ) is ArrayType and type(init_type) is ArrayType:
                if ast.typ.dimensions != init_type.dimensions:
                    raise TypeMismatchInVarDecl(ast)
                if isinstance(ast.typ.typ, AutoType):
                    ast.typ = Utils.infer(ast.name, init_type, o)
                if isinstance(init_type, AutoType):
                    init_type = Utils.infer(ast.init.name, ast.typ, o)
            if Utils.is_coercible(ast.typ, init_type):
                o[0] += [Symbol(ast.name, Variable(), ast.typ, None)]
                return
            else: 
                raise TypeMismatchInVarDecl(ast)
        if isinstance(ast.typ, AutoType):
            raise Invalid(Variable(), ast.name)
        o[0] += [Symbol(ast.name, Variable(), ast.typ, None)]
    
    
    # name: str, typ: Type, out: bool = False, inherit: bool = False
    def visitParamDecl(self, ast, o):
        for item in o[0]:
            if ast.name == item.name:
                raise Redeclared(Parameter(), ast.name)   
        o[0] += [Symbol(ast.name, Parameter(), ast.typ, ast.inherit)]

    
    def previsitFuncDecl(self, ast, o): 
        redeclared_func = False
        for item in o[0]:
            if ast.name == item.name:
                # raise Redeclared(Function(), ast.name)
                redeclared_func = True
                break
        o[0] += [Symbol(ast.name, Function(), ast.return_type, ast.inherit)]
        if redeclared_func: return -1
        
        func_scope = []
        for param_decl in ast.params:
            func_scope += [Symbol(param_decl.name, Parameter(), param_decl.typ, param_decl.inherit)]   
        self.dic[ast.name] = func_scope
        return 0
        
        
    def checkRedeclaredParam(self, scope):
        for idx in range(1, len(scope)):
            if scope[idx].name in [scope[i].name for i in range(idx)]:
                raise Redeclared(Parameter(), scope[idx].name)

                  
    # func_name là tên hàm cha, để đối chiếu với callStmt
    def isSuperStmt(self, ast: CallStmt, func_name, o):
        if ast.name != "super":
            return False
        # đối chiếu list params của func_name (parent) và list args của callStmt
        func_scope = self.dic[func_name]
        param_sym = [sym for sym in func_scope if type(sym.kind) is Parameter]
        params_name = [sym.name for sym in func_scope if type(sym.kind) is Parameter]
        params_type = [sym.typ for sym in func_scope if type(sym.kind) is Parameter]
        args_type = [self.visit(arg, o) for arg in ast.args]
        
        if len(params_type) < len(args_type):
            raise TypeMismatchInExpression(ast.args[len(params_type)])
        if len(params_type) > len(args_type):
            raise TypeMismatchInExpression()
        for idx in range(len(args_type)):
            # if type(params_type[idx]) is not type(args_type[idx]):
            if not Utils.is_coercible(params_type[idx], args_type[idx]):
                raise TypeMismatchInExpression(ast.args[idx])
            if type(params_type[idx]) is AutoType:
                # params_type[idx] = Utils.infer(params_name[idx], args_type[idx], o)
                param_sym[idx].typ = Utils.infer(params_name[idx], args_type[idx], [self.dic[func_name]])
            if type(args_type[idx]) is AutoType:
                args_type[idx] = Utils.infer(ast.args[idx].name, params_type[idx], o)
                
        # print(Utils.scope_to_str(self.dic[func_name]))    
        return True
    
    def isPreventDefaultStmt(self, ast: CallStmt, o):
        if ast.name != "preventDefault":
            return False
        if len(ast.args) != 0:
            raise TypeMismatchInExpression(ast.args[0])
        return True
    
    # name: str, return_type: Type, params: List[ParamDecl], inherit: str or None, body: BlockStmt
    def visitFuncDecl(self, ast: FuncDecl, o):
        # chèn func scope vào o, chút nữa nhớ pop ra
        func_scope = self.dic[ast.name]
        # o = [func_scope] + o
        o.insert(0, func_scope)
        self.scope_level += 1
        # check xem func scope có tồn tại redeclared param
        self.checkRedeclaredParam(o[0])
        # lấy ra symbol của func từ scope ngoài cùng
        
        # print(Utils.scopes_to_str(o))
        
        func_symbol = None
        for symbol in o[-1]:
            if ast.name == symbol.name:
                func_symbol = symbol
                break
        # body có thể là [], tức không có stmt nào
        body = ast.body.body
        # xử lí các TH liên quan đến kế thừa
        # nếu func có inherit hàm khác:
        if ast.inherit:
            # nếu hàm cha không tồn tại
            if ast.inherit not in self.dic:
                raise Undeclared(Function(), ast.inherit)
            parent_func_scope = self.dic[ast.inherit]
            # print(Utils.scope_to_str(parent_func_scope))
            # nếu hàm cha có list param ko rỗng
            if parent_func_scope != []:
                if body == []:
                    self.checkRedeclaredParam(parent_func_scope)
                    # check xem có inherit param nào bị khai báo lại ở func scope
                    inherit_params = [sym for sym in parent_func_scope if sym.inherit == True]
                    for symbol in func_scope:
                        if symbol.name in [sym.name for sym in inherit_params]:
                            raise Invalid(Parameter(), symbol.name)
                    raise InvalidStatementInFunction(ast.name)
                # nếu dòng lệnh đầu tiên của func là super()
                # print(Utils.scope_to_str(self.dic[ast.inherit]))
                if type(body[0]) is CallStmt and self.isSuperStmt(body[0], ast.inherit, o):
                    # check parent scope có redeclared param
                    self.checkRedeclaredParam(parent_func_scope)
                    
                    
                    # check xem có inherit param nào bị khai báo lại ở func scope
                    inherit_params = [sym for sym in parent_func_scope if sym.inherit == True]
                    for symbol in func_scope:
                        if symbol.name in [sym.name for sym in inherit_params]:
                            raise Invalid(Parameter(), symbol.name)
                    # đưa inherit params vào đầu func scope
                    len_ip = len(inherit_params)
                    len_fs = len(func_scope)
                    func_scope = inherit_params + func_scope
                    
                    o.pop(0)
                    o.insert(0, func_scope)
                    self.dic[ast.name] = func_scope
                    # giờ thì chạy hết stmt thôi
                    ignore_returnStmt = False
                    for idx in range(1, len(body)):
                        if type(body[idx]) is CallStmt and body[idx].name in ['super', 'preventDefault']:
                            raise InvalidStatementInFunction(ast.name)
                        if type(body[idx]) is ReturnStmt:
                            if ignore_returnStmt == False: 
                                self.visit(body[idx], o)
                                ignore_returnStmt = True
                            else: ignore_returnStmt
                        else: self.visit(body[idx], o)
                        
                    if not any(isinstance(stmt, ReturnStmt) for stmt in body) and isinstance(func_symbol.typ, AutoType):
                        func_symbol.typ = VoidType()
                    # trả lại func scope chỉ còn param của func thôi
                    new_func_scope = [func_scope[idx] for idx in range(len_ip, len_ip + len_fs)]
                    self.dic[ast.name] = new_func_scope
        
                    o.pop(0)
                    self.scope_level -= 1
                    return
                # nếu dòng lệnh đầu tiên là preventDefault()
                elif type(body[0]) is CallStmt and self.isPreventDefaultStmt(body[0], o):    
                    ignore_returnStmt = False
                    for idx in range(1, len(body)):
                        if type(body[idx]) is CallStmt and body[idx].name in ['super', 'preventDefault']:
                            raise InvalidStatementInFunction(ast.name)
                        if type(body[idx]) is ReturnStmt:
                            if ignore_returnStmt == False: 
                                self.visit(body[idx], o)
                                ignore_returnStmt = True
                            else: ignore_returnStmt
                        else: self.visit(body[idx], o)
                        
                    if not any(isinstance(stmt, ReturnStmt) for stmt in body) and isinstance(func_symbol.typ, AutoType):
                        func_symbol.typ = VoidType()
                    # trả lại func scope chỉ còn param của func thôi
                    new_func_scope = [sym for sym in func_scope if type(sym.kind) is Parameter]
                    self.dic[ast.name] = new_func_scope
                    o.pop(0)
                    self.scope_level -= 1
                    return
                # nếu dòng lệnh đầu tiên là stmt khác
                else: 
                    raise InvalidStatementInFunction(ast.name)
            # nếu hàm cha có list param rỗng
            else:
                if body == []:
                    pass
                # nếu dòng lệnh đầu tiên của func là super()  
                elif type(body[0]) is CallStmt and self.isSuperStmt(body[0], ast.inherit, o):
                    pass
                    # không cần thêm inherit params vào func scope, vì có đâu mà thêm
                # nếu dòng lệnh đầu tiên là preventDefault()
                elif type(body[0]) is CallStmt and self.isPreventDefaultStmt(body[0], o):
                    pass
                    # cũng thế thôi
                # nếu dòng lệnh đầu tiên là stmt khác
                else:
                    self.visit(body[0], o)
                    # cũng không có lỗi
                    
                ignore_returnStmt = False
                for idx in range(1, len(body)):
                    if type(body[idx]) is CallStmt and body[idx].name in ['super', 'preventDefault']:
                        raise InvalidStatementInFunction(ast.name)
                    if type(body[idx]) is ReturnStmt:
                        if ignore_returnStmt == False: 
                            self.visit(body[idx], o)
                            ignore_returnStmt = True
                        else: ignore_returnStmt
                    else: self.visit(body[idx], o)
        
                if not any(isinstance(stmt, ReturnStmt) for stmt in body) and isinstance(func_symbol.typ, AutoType):
                    func_symbol.typ = VoidType()
                
                # trả lại func scope chỉ còn param của func thôi
                new_func_scope = [sym for sym in func_scope if type(sym.kind) is Parameter]
                self.dic[ast.name] = new_func_scope
                
                o.pop(0)
                self.scope_level -= 1
                return
                
                
        # nếu func không có inherit hàm khác:
        ignore_returnStmt = False
        for stmt in body:
            # print("stmt: " + str(type(stmt)))
            if type(stmt) is CallStmt and stmt.name in ['super', 'preventDefault']:
                raise InvalidStatementInFunction(ast.name)
            
            if type(stmt) is ReturnStmt:
                if ignore_returnStmt == False: 
                    self.visit(stmt, o)
                    ignore_returnStmt = True
                else: ignore_returnStmt
            else: self.visit(stmt, o)
            # if type(stmt) is ReturnStmt:
            #     break
        
        if not any(isinstance(stmt, ReturnStmt) for stmt in body) and isinstance(func_symbol.typ, AutoType):
            func_symbol.typ = VoidType()
        
        # trả lại func scope chỉ còn param của func thôi
        new_func_scope = [sym for sym in func_scope if type(sym.kind) is Parameter]
        self.dic[ast.name] = new_func_scope
        
        o.pop(0)
        self.scope_level -= 1
        return        
        
        
    # lhs: LHS, rhs: Expr
    def visitAssignStmt(self, ast, o): 
        ltype = self.visit(ast.lhs, o)
        rtype = self.visit(ast.rhs, o)
        
        if type(rtype) is ErrArrayType:
            raise IllegalArrayLiteral(ast.rhs)
        
        if type(ltype) is AutoType:
            ltype = Utils.infer(ast.lhs.name, rtype, o)
        if type(rtype) is AutoType:
            rtype = Utils.infer(ast.rhs.name, ltype, o)
        if type(ltype) is VoidType or type(rtype) is VoidType:
            raise TypeMismatchInStatement(ast)
        
        if type(ltype) is ArrayType and type(rtype) is ArrayType:
            if ltype.dimensions != rtype.dimensions:
                raise TypeMismatchInStatement(ast)
            if isinstance(ltype.typ, AutoType):
                ltype = Utils.infer(ast.lhs.name, rtype, o)
                return 
            if isinstance(rtype.typ, AutoType):
                rtype = Utils.infer(ast.rhs.name, ltype, o)
                return
            
        if not Utils.is_coercible(ltype, rtype):
            raise TypeMismatchInStatement(ast)    
    
    # body: List[Stmt or VarDecl]
    def visitBlockStmt(self, ast, o): 
        ignore_returnStmt = False
        for stmt in ast.body:
            if type(stmt) is ReturnStmt:
                if ignore_returnStmt == False: 
                    self.visit(stmt, o)
                    ignore_returnStmt = True
                else: ignore_returnStmt
            else: self.visit(stmt, o)
            
    
    # cond: Expr, tstmt: Stmt, fstmt: Stmt or None = None
    def visitIfStmt(self, ast, o):
        cond_type = self.visit(ast.cond, o)
        if not isinstance(cond_type, BooleanType):
            raise TypeMismatchInStatement(ast)
        o.insert(0, [])
        self.scope_level += 1
        self.visit(ast.tstmt, o)
        o.pop(0)
        self.scope_level -= 1
        if ast.fstmt:
            # try:
            #     o.insert(0, [])
            #     self.scope_level += 1
            #     self.visit(ast.fstmt, o)
            #     o.pop(0)
            #     self.scope_level -= 1
            # except TypeMismatchInStatement as err:
            #     if ast.fstmt == err.stmt:
            #         raise TypeMismatchInStatement(ast)
            #     else:
            #         raise err
            o.insert(0, [])
            self.scope_level += 1
            self.visit(ast.fstmt, o)
            o.pop(0)
            self.scope_level -= 1
    
    # init: AssignStmt, cond: Expr, upd: Expr, stmt: Stmt
    def visitForStmt(self, ast, o): 
        init_ltype = self.visit(ast.init.lhs, o)
        init_rtype = self.visit(ast.init.rhs, o)
        cond_type = self.visit(ast.cond, o)
        upd_type = self.visit(ast.upd, o)
        
        if type(init_ltype) is not IntegerType:
            raise TypeMismatchInStatement(ast)
        if type(init_rtype) is not IntegerType:
            raise TypeMismatchInStatement(ast)
        
        if type(cond_type) is not BooleanType:
            raise TypeMismatchInStatement(ast)
        self.in_loop += 1
        o.insert(0, [])
        self.scope_level += 1
        self.visit(ast.stmt, o)
        o.pop(0)
        if type(upd_type) is not IntegerType:
            raise TypeMismatchInStatement(ast)
        self.scope_level -= 1
        self.in_loop -= 1
        
        
    # cond: Expr, stmt: Stmt
    def visitWhileStmt(self, ast, o):
        cond_type = self.visit(ast.cond, o)
        if type(cond_type) is not BooleanType:
            raise TypeMismatchInStatement(ast)
        self.in_loop += 1
        o.insert(0, [])
        self.scope_level += 1
        self.visit(ast.stmt, o)
        o.pop(0)
        self.scope_level -= 1
        self.in_loop -= 1
    
    # cond: Expr, stmt: BlockStmt
    def visitDoWhileStmt(self, ast, o):
        cond_type = self.visit(ast.cond, o)
        if type(cond_type) is not BooleanType:
            raise TypeMismatchInStatement(ast)
        self.in_loop += 1
        o.insert(0, [])
        self.scope_level += 1
        self.visit(ast.stmt, o)
        o.pop(0)
        self.scope_level -= 1
        self.in_loop -= 1
    
    def visitBreakStmt(self, ast, o):
        if self.in_loop == 0:
            raise MustInLoop(ast)
    
    def visitContinueStmt(self, ast, o): 
        if self.in_loop == 0:
            raise MustInLoop(ast)
    
    # expr: Expr or None = None
    def visitReturnStmt(self, ast, o): 
        # print("returnStmt " + str(ast.expr))
        if ast.expr:
            # returnStmt đang ở trong scope_lv s thì o[s-1] scope của func đang chứa returnStmt
            # tìm func
            func_name = None
            for key in self.dic:
                if self.dic[key] is o[self.scope_level - 1]:
                    func_name = key
                    break
            func_sym = None
            for sym in o[-1]:
                if sym.name == func_name and type(sym.kind) is Function:
                    func_sym = sym
                    break
                
            self.returnWithFuncCall = ast
            
            expr_typ = self.visit(ast.expr, o)
            if type(expr_typ) is ErrArrayType:
                raise IllegalArrayLiteral(ast.expr)
            
            if type(func_sym.typ) is AutoType:
                func_sym.typ = expr_typ
            if type(expr_typ) is AutoType:
                expr_typ = Utils.infer(ast.expr.name, func_sym.typ, o)
                
            self.returnWithFuncCall = None

            if not Utils.is_coercible(func_sym.typ, expr_typ):
                raise TypeMismatchInStatement(ast)
        
        return
    
    # name: str, args: List[Expr]
    def visitCallStmt(self, ast, o):
        return_type = self.checkFuncCall(ast, o)
        # đã bỏ auto suy diễn void
        # if type(return_type) is AutoType:
        #     return_type = Utils.infer(ast.name, VoidType(), o)
    
    # op: str, left: Expr, right: Expr
    def visitBinExpr(self, ast, o):
        # print(type(ast.op))
        ltype = self.visit(ast.left, o)
        rtype = self.visit(ast.right, o)
        op = ast.op
        if op in ["+", "-", "*", "/", ">", ">=", "<", "<="]:
            not_allowed = (BooleanType, StringType, ArrayType, VoidType)
            if isinstance(ltype, not_allowed) or isinstance(rtype, not_allowed):
                raise TypeMismatchInExpression(ast)
            if isinstance(ltype, AutoType):
                ltype = Utils.infer(ast.left.name, rtype, o)
            elif isinstance(rtype, AutoType):
                rtype = Utils.infer(ast.right.name, ltype, o)
            if op in [">", ">=", "<", "<="]:
                return BooleanType()
            if isinstance(ltype, FloatType) or isinstance(rtype, FloatType):
                return FloatType()
            return IntegerType()
        else:
            if op in ["%"]:
                if isinstance(ltype, AutoType):
                    ltype = Utils.infer(ast.left.name, rtype, o)
                elif isinstance(rtype, AutoType):
                    rtype = Utils.infer(ast.right.name, ltype, o)
                if not isinstance(ltype, IntegerType) or not isinstance(rtype, IntegerType):
                    raise TypeMismatchInExpression(ast)
            elif op in ["&&", "||"]:
                if isinstance(ltype, AutoType):
                    ltype = Utils.infer(ast.left.name, rtype, o)
                elif isinstance(rtype, AutoType):
                    rtype = Utils.infer(ast.right.name, ltype, o)
                if not isinstance(ltype, BooleanType) or not isinstance(rtype, BooleanType):
                    raise TypeMismatchInExpression(ast)
            elif op in ["==", "!="]:
                if isinstance(ltype, AutoType):
                    ltype = Utils.infer(ast.left.name, rtype, o)
                elif isinstance(rtype, AutoType):
                    rtype = Utils.infer(ast.right.name, ltype, o)
                if type(ltype) is not type(rtype):
                    raise TypeMismatchInExpression(ast)
                if not isinstance(ltype, (IntegerType, BooleanType)):
                    raise TypeMismatchInExpression(ast)
                return BooleanType()
            elif op in ["::"]:
                if isinstance(ltype, AutoType):
                    ltype = Utils.infer(ast.left.name, rtype, o)
                elif isinstance(rtype, AutoType):
                    rtype = Utils.infer(ast.right.name, ltype, o)
                if not isinstance(ltype, StringType) or not isinstance(rtype, StringType):
                    raise TypeMismatchInExpression(ast)
            return ltype
    
    # op: str, val: Expr
    def visitUnExpr(self, ast, o): 
        typ = self.visit(ast.val, o)
        op = ast.op
        if op in ["-"] and not isinstance(typ, (IntegerType, FloatType)):
            raise TypeMismatchInExpression(ast)
        elif op in ["!"]:
            if isinstance(typ, AutoType):
                typ = Utils.infer(ast.val.name, BooleanType())
            if not isinstance(typ, BooleanType):
                raise TypeMismatchInExpression(ast)
        return typ
    
    # name: str
    def visitId(self, ast, o): 
        for symbols in o:
            for symbol in symbols:
                if ast.name == symbol.name and not isinstance(symbol.kind, Function):
                    return symbol.typ
        raise Undeclared(Identifier(), ast.name)
    
    def compareArrayType(self, ltype, rtype, ast, o):
        if isinstance(ltype, ArrayType) and isinstance(rtype, ArrayType):
            if ltype.dimensions == rtype.dimensions:
                if isinstance(ltype.typ, AutoType):
                    ltype = Utils.infer(lexpr.name, rtype, o)
                    return 
                if isinstance(rtype.typ, AutoType):
                    rtype = Utils.infer(rexpr.name, ltype, o)
                    return
        if isinstance(ltype, AutoType) and isinstance(rtype, ArrayType):
            if isinstance(lexpr, Id):
                raise TypeMismatchInStatement(ast)
        if isinstance(rtype, AutoType) and isinstance(ltype, ArrayType):
            if isinstance(rexpr, Id):
                raise TypeMismatchInStatement(ast)
    
    # name: str, cell: List[Expr]
    def visitArrayCell(self, ast, o): 
        this_symbol = None
        for symbols in o:
            for symbol in symbols:
                if ast.name == symbol.name:
                    if isinstance(symbol.typ, ArrayType):
                        this_symbol = symbol
                        break
                    else: TypeMismatchInExpression(ast)
        if this_symbol == None:
            raise Undeclared(Identifier(), ast.name)
        
        indexOp_types = [self.visit(item, o) for item in ast.cell]
        for idx in range(len(indexOp_types)):
            # if isinstance(indexOp_types[idx], AutoType):
            if not isinstance(indexOp_types[idx], IntegerType):
                raise TypeMismatchInExpression(ast)   
        
        # if len(this_symbol.typ.dimensions) != len(indexOp_types):
        #     raise TypeMismatchInExpression(ast)
        
        ele_type = this_symbol.typ
        # while isinstance(ele_type, ArrayType):
        #     ele_type = ele_type.typ
        for idx in range(len(ast.cell)):
            ele_type = ele_type.typ
        return ele_type
    
    # explist: List[Expr]
    def visitArrayLit(self, ast, o):
        ele_type = self.visit(ast.explist[0], o)
        for expr in ast.explist:
            expr_type = self.visit(expr, o)
            if type(expr_type) is not type(ele_type):
                # raise IllegalArrayLiteral(ast)
                return ErrArrayType()
        
            if type(expr_type) is ArrayType and type(ele_type) is ArrayType:
                if expr_type.dimensions != ele_type.dimensions:
                    return ErrArrayType()
                if type(expr_type.typ) is not type(ele_type.typ):
                    return ErrArrayType()
        
        array_dims = [len(ast.explist)]
        if isinstance(ele_type, ArrayType):
            array_dims += ele_type.dimensions
        while isinstance(ele_type, ArrayType):
            ele_type = ele_type.typ
        return ArrayType(array_dims, ele_type)
        
    # val: int
    def visitIntegerLit(self, ast, o):
        return IntegerType()
    
    # val: float
    def visitFloatLit(self, ast, o):
        return FloatType()
    
    # val: str
    def visitStringLit(self, ast, o): 
        return StringType()
    
    # val: bool
    def visitBooleanLit(self, ast, o):
        return BooleanType()
    
    
    
    # name: str, args: List[Expr]
    def visitFuncCall(self, ast, o):
        return self.checkFuncCall(ast, o)

    def visitIntegerType(self, ast, param): pass
    
    def visitFloatType(self, ast, param): pass
    
    def visitBooleanType(self, ast, param): pass
    
    def visitStringType(self, ast, param): pass
    
    # dimensions: List[int], typ: AtomicType
    def visitArrayType(self, ast, param): pass
    
    def visitAutoType(self, ast, param): pass
    
    def visitVoidType(self, ast, param): pass
