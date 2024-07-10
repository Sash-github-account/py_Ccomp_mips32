# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 12:50:59 2024

@author: nsash

Version : 6: 
    -> conditional expression handling added, all operations except unary operations can be used in expressions
    -> Added initial variable scope handling mechanism

Opens:
    -> Add design spec flow diagram for if...else handling
    -> Update existing flow spec diagrams to include logical operator, mixed conditional-arithmetic expression handling
    -> If...else, switch...case statement handling w/ Full Variable scope/namespace management
    -> Variable declaration event handling?
    -> In expression analysis stage, before creating temporary variables, check if they are already defined by source code 
    -> Add unary operator support
    -> add support for pointers
    -> add support for random code block handling
    
Enhancements:
    -> Add support for reporting warnings and different verbosities

C compiler for MIPS-NS ISA
    -> Targeting 32 bit 5 stage MIPS processor that I implemented on De10-Nano FPGA
    -> Supports only int 32b data type
    -> Supports arithmetic operations PEDMAS priority
    -> No support for pre-processing
    -> No support for function calls, only void main()
    -> Conditionals and loops supported
    -> Comments only supported at start of line, ie., an entire line can be a comment but there can be no comments in lines where there is code
    -> Currently supports only one statement per line
    -> Does not support in-expression increment/decrement operators. Ex:- a= (b++) + d-- + e;
                    

References + credits:
    -> https://www.geeksforgeeks.org/variables-in-c/
    -> https://www.geeksforgeeks.org/decision-making-c-cpp/
    -> https://www.w3schools.com/python/python_regex.asp
    -> https://www.geeksforgeeks.org/scope-rules-in-c/
    -> https://regex101.com/
    -> https://en.wikipedia.org/wiki/Shunting_yard_algorithm
    -> https://stackoverflow.com/questions/24256463/arithmetic-calculation-for-bodmas-in-java
    -> https://stackoverflow.com/questions/1038824/how-do-i-remove-a-substring-from-the-end-of-a-string-remove-a-suffix-of-the-str
"""
# Import required libs #
import sys
import re

##########################################################
# Class definitions for Objects and data structures used #
##########################################################

# Comment class, stores info about comment lines in a file, in a dict #
# Has method to check if a line is a comment n update the cmnt dict  #
class Comment:
    comment_lines_obj = {}
    
    def __init__(self, svr_lvl):
        self.svr_lvl = svr_lvl

        
    def __str__(self):
        return f"{self.svr_lvl}({self.comment_lines_obj})"
 
    def update_cmnt_obj(self, line, ln_num):
        self.comment_lines_obj[ln_num] = line

    def print_info(self, ln_num, line):
        info_str_chk_cmnt = "INFO: Encountered a comment line:"
        if(self.svr_lvl == 'I'):
            print(info_str_chk_cmnt + '\n'+ "line: " + str(ln_num) + ' ' + line)
        
    def get_comment_ln_num(self, line):
        line_num = {i for i in self.comment_lines_obj if self.comment_lines_obj[i] == line}
        return line_num
    
    def chk_cmnt_n_upd(self, line, ln_num):
        if(re.findall("\s*\/\/", line) != []):
            self.update_cmnt_obj(line, ln_num)
            self.print_info(ln_num, line)
            return 1
        else:
            return 0
        
#--------- END of comment class----------#        
        


# Program_obj class, stores info about comment lines in a file, in a dict #
# 1.  #
class Program_obj:
    re_get_token = "\s*(void|int)"
    re_get_var_name = "[a-zA-Z_]+[0-9a-zA-Z_]*"
    re_get_exp = "=\s*[=<>&!\|a-zA-z_\s\(\)\+\-\/\*\^\%0-9]*\s*"
    re_var_or_num_non_capture = "(?:" + re_get_var_name + "|[0-9]+)"
    re_if_stmt = "if\s*\((.*)\)\s*{?\s*"
    operator_lst_precedence_h2l = ['^', '/', '*', '%', '+', '-', '<', '>', '<=', '>=', '==', '!=', '&&', '||']
    
    def __init__(self, svr_lvl):
        self.main_fn_entered = 0
        self.expecting_opn_cbrace = 0
        self.expecting_cls_cbrace = 0
        self.svr_lvl = svr_lvl
        self.mn_fn_def_ln_num = None
        self.parse_event_sequence_dict = {}
        self.parse_event_seq_cntr = 0
        self.variable_names_lst = []
        self.upper_scope_var_stck = []
        self.used_vars_stk = []
        self.tmp_var_cnt = 0
        self.open_cbrace_cntr = 0
        
    def __str__(self):
        return f"(Main funtion at line: {self.mn_fn_def_ln_num})"


    def print_error_msg_ext(self, msg_strng, line, ln_num):
        print(msg_strng + str(ln_num) + ' ' + line)
        sys.exit()  

    def pedmas_assembler(self, expn_in):
        expn = expn_in
        print("INFO: Entering PEDMAS expression assembler.")
        print(expn)
        for op in range(len(self.operator_lst_precedence_h2l)):
            print(op)
            print(self.operator_lst_precedence_h2l[op])
            if self.operator_lst_precedence_h2l[op] not in [ '<', '>', '<=', '>=', '==', '!=', '&&', '||', '%']:
                list_curr_ops = re.findall('(?:'+self.re_var_or_num_non_capture+'\\'+self.operator_lst_precedence_h2l[op]+')+'+self.re_var_or_num_non_capture, expn)
            else:
                list_curr_ops =re.findall('(?:'+self.re_var_or_num_non_capture+self.operator_lst_precedence_h2l[op]+')+'+self.re_var_or_num_non_capture, expn)
            print(list_curr_ops)
            list_curr_ops_tpl = [tuple(i.split(self.operator_lst_precedence_h2l[op])) for i in list_curr_ops]
            print(list_curr_ops_tpl)
            for item in list_curr_ops_tpl:
                print(item)
                #print('tmpvar'+str(tmp_cnt))
                multi_op_var_lst = list(item)
                for varnum in range(len(item)-1):
                    tmp_var = 'PEDMAStmpvar'+str(self.tmp_var_cnt)
                    var1 = multi_op_var_lst.pop(0)
                    var2 = multi_op_var_lst.pop(0)
                    multi_op_var_lst.insert(0,tmp_var)
                    rplc_str = var1+"\\"+self.operator_lst_precedence_h2l[op]+var2
                    print(rplc_str)
                    self.parse_event_seq_cntr += 1
                    self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ( tmp_var, ''.join(rplc_str.split("\\")))
                    expn = re.sub(rplc_str, tmp_var, expn, count=1)
                    #print(x)
                    self.tmp_var_cnt += 1
        print("INFO: exiting PEDMAS expression assembler")
        return expn
                    
                    
    
    def expn_seq_assembler(self, init_var, var, x1, line, ln_num):       
        num_open_brk = len(re.findall("\(", x1))
        num_cls_brk = len(re.findall("\)", x1))
        print(num_cls_brk)
        if(num_open_brk == num_cls_brk and (num_open_brk > 0)):
            print(x1)
            x = [ i.strip('(').strip(')').strip(' ') for i in re.findall("\([=&\|!<>a-zA-Z0-9\^\+\-\/\*\%_]+\)", x1)]
            print(x)
            for exp in x:
                tmp = exp
                for oper in self.operator_lst_precedence_h2l:
                    if(tmp.find(oper) >= 0):
                        if oper in ['^', '/', '*', '+', '-']:
                            tmp = tmp.replace(oper, '\\'+oper)
                print(x1)
                print(exp)
                chg_var = self.pedmas_assembler(exp)
                x1 = re.sub('\('+tmp+'\)', chg_var, x1)
                print(x1)                        
            self.expn_seq_assembler(init_var, chg_var, x1, line, ln_num)
            return 1
        elif(num_open_brk == num_cls_brk and (num_open_brk == 0)):
            print("INFO: Num Assignment")
            tmp_var = self.pedmas_assembler(x1)
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = (init_var, tmp_var)
            return 1            
        else:
            self.print_error_msg_ext("ERROR: expression syntax error at line: ", line, ln_num)
        
        
    
    def expression_syntax_parser(self, var_n_assignmnt_exp_lst, line, ln_num):
        for var_expn in var_n_assignmnt_exp_lst:
            #[var, expn] =  var_expn.split('=') if len(var_expn.split('=')) == 2 else  [ 1, 1]
            var_expn_tuple_lst = re.findall('^([a-zA-Z_]+[0-9a-zA-Z_]*=)([a-zA-Z_\+\-\(\)\/\*\^\%!\|=0-9]*)', var_expn)
            print(var_expn_tuple_lst)
            var = var_expn_tuple_lst[0][0].strip('=')
            expn = var_expn_tuple_lst[0][1]
            print(var,expn)
            if([var, expn] == [ 1, 1]):
                self.print_error_msg_ext("ERROR: Expression syntax error at line: ", line, ln_num)
            elif(re.search(self.re_get_exp, '='+expn)):
                if 0 in self.chk_var_re_dec_exp_syntx(re.findall(self.re_get_var_name, expn)):
                    self.print_error_msg_ext("ERROR: undeclared variable used at line: ", line, ln_num)                    
                else:
                    self.expn_seq_assembler( var.strip(' '), var.strip(' '), expn, line, ln_num)
                    #return 1
            else:
                return 0
        return 1
                    
  
                    
    def var_declrtn_chkr(self, var):
        if var in self.variable_names_lst:
            return 1
        else:
            return 0


    def chk_var_re_dec_exp_syntx(self, var_lst):
        var_already_declrd_lst = []
        for var in var_lst:
            var_already_declrd_lst.append(self.var_declrtn_chkr(var)) 
        return var_already_declrd_lst


    def chk_if_else_syntx_upd(self, line, ln_num):
        if_stmt_match_obj = re.search("^\s*" + self.re_if_stmt, line)
        print(if_stmt_match_obj)
        if(if_stmt_match_obj):
            cond_temp_var = "COND_var_"+str(self.tmp_var_cnt)
            self.tmp_var_cnt += 1
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('BRANCH', cond_temp_var)
            cond_str_to_parse = [cond_temp_var + '=' +  re.findall("^\s*" + self.re_if_stmt, line)[0].replace(' ', '').strip(' ')]
            if(self.expression_syntax_parser(cond_str_to_parse, line, ln_num)):
                print("INFO: if...else branch statement at line: " + str(ln_num) + ': ' + line)
                self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1)
            else:
                self.print_error_msg_ext("ERROR: Failed condition evaluation at line: ", line, ln_num)
            return 1
        else:
            return 0


    def chk_var_dec_or_assignmnt(self, line, ln_num):
        print("INFO: line : " + line + ': ' + str(ln_num))
        re_str_to_chk = "^" + self.re_get_token + '?' + "(\s*" + self.re_get_var_name + "\s*(" + self.re_get_exp + ")?,?)*;\s*"
        match_obj = re.search(re_str_to_chk, line)
        print(match_obj)
        if(match_obj):
            match_type = 1 if (re.search("^" + self.re_get_token, match_obj.group())) else 0
            print(match_type)
            rm_dec_token = re.sub("^" + self.re_get_token, '', match_obj.group())
            rm_semicoln_nl_sp = rm_dec_token.strip("\n").strip(" ").strip(";")
            if(match_type==1):
                var_n_expn_lst = rm_semicoln_nl_sp.split(',')
                var_only_lst = re.sub(self.re_get_exp, '',  rm_semicoln_nl_sp).replace(' ', '').split(',')
                print(var_n_expn_lst)
                print(var_only_lst)
                if 1 in self.chk_var_re_dec_exp_syntx(var_only_lst):
                    self.print_error_msg_ext("ERROR: Variable re-declaration at line: ", line, ln_num)
                else:
                    self.variable_names_lst += [i.strip(' ') for i in var_only_lst]
                    if(len(var_n_expn_lst) == 1):
                        var_n_expn_lst_filtered = [i.replace(' ', '').strip(' ') for i in [var_n_expn_lst] if '=' in i]
                    else:
                        var_n_expn_lst_filtered = [i.replace(' ', '').strip(' ') for i in var_n_expn_lst if '=' in i]                        
                    print(var_n_expn_lst_filtered)
                    self.expression_syntax_parser(var_n_expn_lst_filtered, line, ln_num)
            else:
                var_n_expn_lst = [rm_semicoln_nl_sp.replace(' ', '').strip(' ')]
                var_only_lst = re.sub(self.re_get_exp, '',  rm_semicoln_nl_sp)
                if 0 in self.chk_var_re_dec_exp_syntx(var_only_lst):
                    self.expression_syntax_parser(var_n_expn_lst, line, ln_num)
                else:
                    self.print_error_msg_ext("ERROR: Undeclared variable at line: ", line, ln_num)
            return 1
        else:
            return 0
        
        
            
    def chk_cbrace_reqmnt_n_upd(self, line, ln_num = None, ln_is_mn_fn = 0):
        ln_splt_at_cbrace = line.split("{")
        if (len(ln_splt_at_cbrace) > 1):
            print("INFO: Found open cbrace at line:" + str(ln_num))
            if(ln_is_mn_fn):
                self.expecting_opn_cbrace = 0
                self.expecting_cls_cbrace = 1
                self.open_cbrace_cntr += 1
                if(self.variable_names_lst != []):
                    self.upper_scope_var_stck.append(self.variable_names_lst)
            else:
                if ((re.search("\s*", ln_splt_at_cbrace[0]))):
                    self.expecting_opn_cbrace = 0
                    self.expecting_cls_cbrace = 1
                    self.open_cbrace_cntr += 1
                    if(self.variable_names_lst != []):
                        self.upper_scope_var_stck.append(self.variable_names_lst)
                    if(re.search("^\s*$", ln_splt_at_cbrace[1]) ):
                        pass
                    else:
                        self.chk_var_dec_or_assignmnt(ln_splt_at_cbrace[1], ln_num)
                else:
                    self.print_error_msg_ext("ERROR: Syntax error at line num: ",  line, ln_num)
        else:
            self.expecting_opn_cbrace = 1



    def chk_cbrace_closure(self, line, ln_num):
        ln_splt_at_cbrace = line.split("}")
        if(len(ln_splt_at_cbrace) > 1):
            if(ln_splt_at_cbrace[1].strip(' ').strip('\n') != ''):
                self.print_error_msg_ext("ERROR: cbrace closure syntax error at line: ", line, ln_num)
            else:
                if(ln_splt_at_cbrace[0] == ''):
                    self.open_cbrace_cntr -= 1
                    if(self.open_cbrace_cntr < 0):
                        self.print_error_msg_ext("ERROR: No corresponding open brace found at line: ", line, ln_num)
                    if(self.variable_names_lst != [] and self.upper_scope_var_stck != []):
                        self.variable_names_lst = []
                        self.variable_names_lst = self.upper_scope_var_stck.pop()
                    if(self.open_cbrace_cntr == 0):
                        self.expecting_cls_cbrace = 0
                    print("INFO: Found cls cbrace at line: " + str(ln_num) + " " + line)
                    return 1
        else:
            return 0
        
        
    def chk_mn_fn_entry_syntx_er(self, line, ln_num):
            if(self.main_fn_entered == 0):
                self.main_fn_entered = 1
                self.mn_fn_def_ln_num = ln_num
                self.chk_cbrace_reqmnt_n_upd(line, ln_is_mn_fn=1)
                self.print_info(line, ln_num)
                return 1
            else:
                self.print_error_msg_ext("ERROR: Main function already defined at line num: ",  line, ln_num)          


    def chk_main_fn_entry(self, line, ln_num):
        void_mn_match_obj = re.search("^\s*(int|void)\s*main\s*\(\s*\)\s*{?\s*" , line)
        if(void_mn_match_obj):
            return self.chk_mn_fn_entry_syntx_er(line, (ln_num))
        else:
            return 0


    def print_info(self, line, ln_num):
        info_str_chk_mnfn_entry = "INFO: Main function entry: "
        if(self.svr_lvl == 'I'):
            print(info_str_chk_mnfn_entry + '\n'+ "line: " + str(ln_num) + ' ' + line)
            
#--------- END of Program_obj class----------#        


##########################################################
##########################################################        
        
# Get file(s) as args
def get_file_list_for_compile():
    file_lst_fr_compile = sys.argv[1:]
    print(file_lst_fr_compile)
    return file_lst_fr_compile

# Global vars to maintain parsed var names, init data, compiler state variables, etc  #
default_svr_lvl = 'I'
Comment_obj = Comment(default_svr_lvl)

# Open file to compile n get lines of the file # #
def get_file_lines_list(flenme):
    fleptr = open(flenme, 'r')
    fl_ln_lst = fleptr.readlines()
    return fl_ln_lst



def start_fl_parse(file_lns):
    prog_obj = Program_obj(default_svr_lvl)
    # Go into loop for each line #
    for line_num in range(len(file_lns)):
        line_n = line_num+1
        print("TEST: Event seq:")
        #print(prog_obj.parse_event_sequence_dict)
        for key, value in prog_obj.parse_event_sequence_dict.items():
            print(f"{key}: {value}")
        # Check if line is a comment => *.split("//")[0] = regex(/s*)  #
        if (Comment_obj.chk_cmnt_n_upd(file_lns[line_num], line_n)):
            continue
        # Check if line is empty *.split(" ")  #
        elif (re.search("^\s*$", file_lns[line_num])):
            print("INFO: line " + str(line_n) + ' is empty')
            continue
        # Previous src code line was entry into main fn but with no open cbrace -> chk for that now #
        elif(prog_obj.expecting_opn_cbrace):
            prog_obj.chk_cbrace_reqmnt_n_upd(file_lns[line_num], ln_num=line_n, ln_is_mn_fn=0)
        # Check if line has close brace #
        elif(prog_obj.chk_cbrace_closure(file_lns[line_num], line_n)):
            continue
        # Check syntax for main func entry -> state vars: mn_fn_entered, expecting_opn_cbrace #
        elif(prog_obj.chk_main_fn_entry(file_lns[line_num], line_n)):
            continue
        # Check for var declaration + optnaly init #
            # If syntx ok =>  push var+val str into var dict #
            # if init has exp, chk exp syntx as well #
        # Check for var assignment#
            # If syntx ok => chk exp syntx #
        # Check if arithmetic/logical operation and upd val in var dict corresponding to appriate var #
        elif(prog_obj.chk_var_dec_or_assignmnt(file_lns[line_num], line_n)):
            continue
        # Check if conditional branch stmt 'if() else if() else' or 'switch() case x:'   and upd brn state vars
        elif(prog_obj.chk_if_else_syntx_upd(file_lns[line_num], line_n)):
            continue
        else:
            print("WIP, line num: " + str(line_n))
                       
        
        
    print(prog_obj.expecting_cls_cbrace)
    if(prog_obj.expecting_cls_cbrace != 0):
        prog_obj.print_error_msg_ext("ERROR: unclosed { in program: line:", file_lns[len(file_lns)-1], len(file_lns)-1)
        # Check for loop syntax and upd loop state var #
    
    
    
# Main script begins #
if(__name__ == "__main__"):
    flist = get_file_list_for_compile()
    for fl in flist:
        fl_lns = get_file_lines_list(fl)
        start_fl_parse(fl_lns)
