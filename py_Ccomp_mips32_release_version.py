# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 12:50:59 2024

@author: nsash

Version : 15: 
    -> Added do-while manager flow diagram
    -> Added DoWhileManager class
    -> Added chk_do_while_loop_n_upd() method to Program_obj class
    -> Added test C code: test_do_while.c for testing
    
Opens: 
    -> Bug: nested if condition parse event not getting updated
    -> Add back-end handling of merging point after break statement
    -> In expression analysis stage, before creating temporary variables, check if they are already defined by source code 
    -> Add unary operator support
    -> add support for pointers
    -> add support for random code block handling
    -> add support of single line non-parenthesis branch/loop statements
    
Enhancements:
    -> Add support for reporting warnings and different verbosities
    -> Create separate variable scope manager class
    -> Create separate print class?

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
    -> ternary operator not supported
                    

References + credits:
    -> copilot
    -> chatGPT
    -> https://www.programiz.com/c-programming/online-compiler/
    -> https://www.geeksforgeeks.org/c-switch-statement/
    -> https://www.geeksforgeeks.org/c-pointers/
    -> https://www.geeksforgeeks.org/variables-in-c/
    -> https://www.geeksforgeeks.org/decision-making-c-cpp/
    -> https://www.w3schools.com/python/python_regex.asp
    -> https://www.geeksforgeeks.org/scope-rules-in-c/
    -> https://regex101.com/
    -> https://en.wikipedia.org/wiki/Shunting_yard_algorithm
    -> https://stackoverflow.com/questions/24256463/arithmetic-calculation-for-bodmas-in-java
    -> https://stackoverflow.com/questions/1038824/how-do-i-remove-a-substring-from-the-end-of-a-string-remove-a-suffix-of-the-str
    -> https://stackoverflow.com/questions/43106905/what-is-the-best-way-to-check-if-a-variable-is-a-list
    -> https://www.geeksforgeeks.org/c-loops/
    -> C Programming Language, 2nd Edition by Brian W. Kernighan and Dennis M. Ritchie
    -> ISO/IEC 9899:2011 - C11 Standard
"""
# Import required libs #
import sys
import re
import time

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
        



# IfElseManager class, stores maintains nesting state of IFelse branch statement #
class IfElseManager:
    fsm_states = [
        0, #'waiting for  if ',
        1, #'nxt can be else or else if',
        2, #'waiting for else cls brace',
        3, #'waiting for else if cls brace',
        4, #'waiting for if cls brace',
        5 #'error, exit'
        ]

    fsm_transition_events = [
        0, #'if with '
        1, #any code stmt
        2, #nested if 
        3, #got '}'
        4, #got else if
        5  #got else 
        ]
    
    def __init__(self):
        self.if_nest_level_cntr = 0
        self.current_state = self.fsm_states[0]


    def __str__(self):
        return f"{self.if_nest_level_cntr}({self.current_state})"
 
    
    def transtion_from_waitingForIf_state(self, transition_event):
        if(transition_event == self.fsm_transition_events[0]):
            self.current_state = self.fsm_states[4]
        elif(transition_event == self.fsm_transition_events[5]):
            self.current_state = self.fsm_states[5]
        else:
            self.current_state = self.current_state    
 
    def transition_from_WaitForIfClsBrace(self, transition_event):
        if(transition_event == self.fsm_transition_events[3]):
            self.current_state = self.fsm_states[1]
        elif(transition_event == self.fsm_transition_events[2] or transition_event == self.fsm_transition_events[0]):
            self.if_nest_level_cntr += 1
        elif(transition_event == self.fsm_transition_events[5] or transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[5]
        else:
            self.current_state = self.current_state
 
    
    def transition_from_waitForElseifClsBrace(self, transition_event):
        if(transition_event == self.fsm_transition_events[5] or transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[5]
        elif(transition_event == self.fsm_transition_events[2] or transition_event == self.fsm_transition_events[0]):
            self.current_state = self.fsm_states[4]
            self.if_nest_level_cntr += 1
        elif(transition_event == self.fsm_transition_events[3]):
            self.current_state = self.fsm_states[1]
        else:
            self.current_state = self.current_state

    def transition_from_NxtCanBeElseOrElseif(self, transition_event):
        if(transition_event == self.fsm_transition_events[5]):
            self.current_state = self.fsm_states[2]
        elif(transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[3]
        elif(transition_event == self.fsm_transition_events[1] and self.if_nest_level_cntr > 0):
            self.if_nest_level_cntr -= 1
            self.current_state = self.fsm_states[4]
        elif(transition_event == self.fsm_transition_events[1] and self.if_nest_level_cntr == self.fsm_transition_events[0]):
            self.current_state = self.fsm_states[0]
        else:
            self.current_state =  self.current_state        


    def transition_from_waitForElseClsBrace(self, transition_event):
        if(transition_event == self.fsm_transition_events[5] or transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[5]
        elif(transition_event == self.fsm_transition_events[0] or transition_event == self.fsm_transition_events[2]):
            self.if_nest_level_cntr += 1
            self.current_state = self.fsm_states[4]
        elif(transition_event == self.fsm_transition_events[3] and self.if_nest_level_cntr > 0):
            self.if_nest_level_cntr -= 1
            self.current_state = self.fsm_states[4]
        elif(transition_event == self.fsm_transition_events[1] and self.if_nest_level_cntr == 0):
            self.current_state = self.fsm_states[0]
        else:
            self.current_state =  self.current_state          

    
    def update_fsm_state(self, transition_event):
        if(self.current_state == self.fsm_states[0]):
           self.transtion_from_waitingForIf_state(transition_event)
        elif(self.current_state == self.fsm_states[4]):
            self.transition_from_WaitForIfClsBrace(transition_event)
        elif(self.current_state == self.fsm_states[3]):
            self.transition_from_waitForElseifClsBrace(transition_event)
        elif(self.current_state == self.fsm_states[1]):
            self.transition_from_NxtCanBeElseOrElseif(transition_event)
        elif( self.current_state ==  self.fsm_states[2]):
            self.transition_from_waitForElseClsBrace(transition_event)
        else:
            self.current_state =  self.current_state
#--------- END of IfElseManager class----------#     





# SwitchCaseManager class, stores maintains nesting state of switch-case branch statement #
class SwitchCaseManager:
    fsm_states = [
    0, # waiting for switch,
    1, # waiting for default,
    2, # waiting for switch statement closure,
    3, # error, exit,
    ] 

    fsm_transition_events = [
        0, # got switch w/ valid expn
        1, # got {
        2, # got code stmt
        3, # got default
        4, # got }
        5  # got case
        ]    
     
    def __init__(self):
        self.current_state = self.fsm_states[0]
        self.sw_int_opnbr_stk = []
        self.cur_sw_stmt_cond_expn = ''
        self.switch_nest_lvl = 0
        self.cur_int_opn_brc_cnt = 0
        self.cur_sw_deflt_defnd = 0
        self.cur_sw_case_vals = []

    def __str__(self):
        return f"{self.sw_int_opnbr_stk}({self.switch_nest_lvl})({self.cur_int_opn_brc_cnt})({self.cur_sw_deflt_defnd})({self.cur_sw_case_vals})"
 
    def nstd_sw_push_stk_n_upd(self):
        self.sw_int_opnbr_stk.append((self.cur_int_opn_brc_cnt, self.cur_sw_deflt_defnd, self.cur_sw_case_vals, self.cur_sw_stmt_cond_expn));
        self.cur_int_opn_brc_cnt = 0;
        self.switch_nest_lvl += 1;
        self.cur_int_opn_brc_cnt += 1
        self.cur_sw_stmt_cond_expn = ''

    def chk_int_open_brace_n_upd_state(self):
        if(self.cur_sw_deflt_defnd == 0):
            self.current_state = self.fsm_states[1]
        else:
            self.current_state = self.fsm_states[2]
    
    def process_cls_brace_transitions(self):
        if(self.cur_int_opn_brc_cnt == 1 and self.switch_nest_lvl == 1):
            self.switch_nest_lvl -= 1
            self.cur_int_opn_brc_cnt -= 1
            self.current_state = self.fsm_states[0]
        else:
            if(self.cur_int_opn_brc_cnt > 1):
                self.cur_int_opn_brc_cnt -= 1
                self.chk_int_open_brace_n_upd_state()
            else:
                self.switch_nest_lvl -= 1
                self.cur_int_opn_brc_cnt, self.cur_sw_deflt_defnd, self.cur_sw_case_vals,  self.cur_sw_stmt_cond_expn = self.sw_int_opnbr_stk.pop()
                self.chk_int_open_brace_n_upd_state()
        
        
    def process_case_stmt_for_cur_sw(self, case_value):
        if case_value in self.cur_sw_case_vals:
            self.current_state = self.fsm_states[3]
        else:
            self.cur_sw_case_vals.append(case_value)
    
    
    def transition_from_waitForSwitch_state(self, te, expn):
        if(te == self.fsm_transition_events[0]):
            self.switch_nest_lvl += 1;
            self.cur_int_opn_brc_cnt += 1;
            self.cur_sw_stmt_cond_expn = expn
            self.current_state = self.fsm_states[1]
        elif(te == self.fsm_transition_events[2]):
            self.current_state = self.current_state
        elif(te == self.fsm_transition_events[3] or te == self.fsm_transition_events[5]):
            self.current_state = self.fsm_states[3]
        else:
            self.current_state = self.current_state
            
        
    def transition_from_waitForDefault_state(self, te, case_value):
        if(te == self.fsm_transition_events[0]):
            self.nstd_sw_push_stk_n_upd()
        elif(te == self.fsm_transition_events[1]):
            self.cur_int_opn_brc_cnt += 1
        elif(te == self.fsm_transition_events[2]):
            self.current_state = self.current_state
        elif(te == self.fsm_transition_events[3]):
            self.cur_sw_deflt_defnd = 1
            self.current_state = self.fsm_states[2]
        elif(te == self.fsm_transition_events[4]):
            self.process_cls_brace_transitions()
        elif(te == self.fsm_transition_events[5]):
            self.process_case_stmt_for_cur_sw(case_value)
        else:
            self.current_state = self.current_state
            
        
    def transition_from_waitForSwStmtCls_state(self, te, case_value):
        if(te == self.fsm_transition_events[0]):
            self.nstd_sw_push_stk_n_upd()
            self.cur_sw_deflt_defnd = 0
            self.current_state = self.fsm_states[1]
        elif(te == self.fsm_transition_events[1]):
            self.cur_int_opn_brc_cnt += 1
        elif(te == self.fsm_transition_events[2]):
            self.current_state = self.current_state
        elif(te == self.fsm_transition_events[3]):
            self.current_state = self.fsm_states[3]
        elif(te == self.fsm_transition_events[4]):
            self.process_cls_brace_transitions()
        elif(te == self.fsm_transition_events[5]):
            self.process_case_stmt_for_cur_sw(case_value)
        else:
            self.current_state = self.current_state
            
    
    def update_fsm_state(self, transition_event, sw_expn = '', case_value = ''):
        if(self.current_state == self.fsm_states[0]):
            self.transition_from_waitForSwitch_state(transition_event, sw_expn)
        elif(self.current_state == self.fsm_states[1]):
            self.transition_from_waitForDefault_state(transition_event, case_value)
        elif(self.current_state == self.fsm_states[2]):
            self.transition_from_waitForSwStmtCls_state(transition_event, case_value)
        else:
            self.current_state =  self.current_state
            
    def get_last_sw_cond_expn_val(self):
        print("INFO: get_last_sw_cond_expn_val() from switch case manager called. Sending this value:")
        if self.cur_sw_stmt_cond_expn == '':
            print("from stack: ",self.sw_int_opnbr_stk[len(self.sw_int_opnbr_stk)-1])
            return self.sw_int_opnbr_stk[len(self.sw_int_opnbr_stk)-1][3]
        else:
            print("from attribute: ", self.cur_sw_stmt_cond_expn)
            return self.cur_sw_stmt_cond_expn
#--------- END of SwitchCaseManager class----------#     




# DoWhileManager class, stores maintains nesting state of do-while loop statement #
class DoWhileManager:
    fsm_states = [
    0, # waiting for 'do' stmt,
    1, # waiting for while cls brace,
    2, # nxt should be while,
    3, # error, exit,
    ] 

    fsm_transition_events = [
        0, # got do stmt
        1, # got while stmt
        2, # got code stmt: te[2]
        3, # got {
        4  # got }
        ]   

    def __init__(self):
        self.current_state = self.fsm_states[0]
        self.stck_nst_lvl = []
        self.nstd_do_lvl_cntr = 0
        self.cur_nstd_opn_brace_cntr = 0

    def __str__(self):
        return f"{self.current_state}({self.stck_nst_lvl})({self.nstd_do_lvl_cntr})({self.cur_nstd_opn_brace_cntr})"
  

    def transition_from_waitForDo_state(self, te):
        if(te == self.fsm_transition_events[0]):
            self.nstd_do_lvl_cntr += 1
            self.cur_nstd_opn_brace_cntr += 1
            self.current_state = self.fsm_states[1]
        else:
            self.current_state =self.current_state 
         
    
    def transition_from_waitForWhileClsBrace_state(self, te):
        if(te == self.fsm_transition_events[0]):
            self.nstd_do_lvl_cntr += 1
            self.cur_nstd_opn_brace_cntr += 1
            self.stck_nst_lvl.push(self.cur_nstd_opn_brace_cntr)
        elif(te == self.fsm_transition_events[1]):
            self.current_state = self.fsm_states[3]
        elif(te == self.fsm_transition_events[3]):
            self.cur_nstd_opn_brace_cntr += 1
        elif(te == self.fsm_transition_events[4]):
            if(self.cur_nstd_opn_brace_cntr == 1):
                self.current_state = self.fsm_states[2]
            else:
                self.nstd_do_lvl_cntr -= 1
        else:
            self.current_state =self.current_state 
        
    
    
    def transition_from_nxtSldBeWhile_state(self, te):
        if(te == self.fsm_transition_events[1]):
            if(self.nstd_do_lvl_cntr == 1):
                self.nstd_do_lvl_cntr -= 1
                self.current_state = self.fsm_states[0]
            else:
                self.cur_nstd_opn_brace_cntr = self.stck_nst_lvl.pop()
                self.nstd_do_lvl_cntr -= 1
        

    def update_fsm_state(self, transition_event):
        if(self.current_state == self.fsm_states[0]):
            self.transition_from_waitForDo_state(transition_event)
        elif(self.current_state == self.fsm_states[1]):
            self.transition_from_waitForWhileClsBrace_state(transition_event)
        elif(self.current_state == self.fsm_states[2]):
            self.transition_from_nxtSldBeWhile_state(transition_event)
        else:
            self.current_state =  self.current_state    
#--------- END of DoWhileManager class----------#     



# Program_obj class, stores info about comment lines in a file, in a dict #
# 1.  #
class Program_obj:
    re_get_token = "\s*(void|int)"
    re_get_var_name = "[a-zA-Z_]+[0-9a-zA-Z_]*"
    re_get_exp = "=\s*[=<>&!\|a-zA-z_\s\(\)\+\-\/\*\^\%0-9]*\s*"
    re_var_or_num_non_capture = "(?:" + re_get_var_name + "|[0-9]+)"
    re_if_stmt = "if\s*\((.*)\)\s*{\s*"
    re_elseif_else = "else\s+if\s*\((.*)\)\s*{\s*"
    re_elseif_split_lines_else_chk = '\s*else\s*'
    re_else_only_w_brackt = "\s*else\s*{\s*"
    re_detect_switch_stmt = "^\s*switch\s*\((.*)\)\s*{\s*"
    re_detect_case_n_value = "^\s*case\s*([0-9]+)\s*:\s*"
    re_detect_sw_default_stmt = "^\s*default\s*:\s*"
    re_break_stmt_dtection = "^\s*break\s*;\s*"
    re_detect_do_stmt = "^\s*do\s*{\s*"
    re_detect_while_loop_stmt = "^\s*while\s*\((.*)\)\s*{\s*"
    re_detect_while_from_dowhile = "^\s*while\s*\((.*)\)\s*;\s*"
    operator_lst_precedence_h2l = ['^', '/', '*', '%', '+', '-', '<', '>', '<=', '>=', '==', '!=', '&&', '||']
    
    def __init__(self, svr_lvl):
        self.main_fn_entered = 0
        self.expecting_opn_cbrace = 0
        self.expecting_cls_cbrace = 0
        self.svr_lvl = svr_lvl
        self.mn_fn_def_ln_num = None
        self.parse_event_sequence_dict = {}
        self.parse_event_seq_cntr = 0
        self.current_scope_var_list = []
        self.scope_var_lst_stck = []
        self.done_scope_var_lst_stck = []
        self.tmp_var_cnt = 0
        self.open_cbrace_cntr = 0
        self.if_else_mngr = IfElseManager()
        self.sw_case_mngr = SwitchCaseManager()
        self.do_while_mngr = DoWhileManager()
        
    def __str__(self):
        return f"(Main funtion at line: {self.mn_fn_def_ln_num})"


    def print_error_msg_ext(self, msg_strng, line, ln_num):
        print(msg_strng + str(ln_num) + ' ' + line)
        print("Program runtime:")
        print(f"--- {time.time() - start_time:.6f} seconds ---")
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
            print(init_var)
            tmp_var = self.pedmas_assembler(x1)
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = (init_var, tmp_var)
            return 1            
        else:
            self.print_error_msg_ext("ERROR: expression syntax error at line: ", line, ln_num)
        
        
    
    def expression_syntax_parser(self, var_n_assignmnt_exp_lst, line, ln_num):
        for var_expn in var_n_assignmnt_exp_lst:
            #[var, expn] =  var_expn.split('=') if len(var_expn.split('=')) == 2 else  [ 1, 1]
            var_expn_tuple_lst = re.findall('^([a-zA-Z_]+[0-9a-zA-Z_]*=)([=&\|!<>a-zA-Z_\+\-\(\)\/\*\^\%!\|=0-9]*)', var_expn)
            print(var_expn_tuple_lst)
            var = var_expn_tuple_lst[0][0].strip('=')
            expn = var_expn_tuple_lst[0][1]
            print(var,expn)
            if([var, expn] == [ ]):
                self.print_error_msg_ext("ERROR: Expression syntax error at line: ", line, ln_num)
            elif(re.search(self.re_get_exp, '='+expn)):
                var_only_lst = re.findall(self.re_get_var_name, expn)
                redec_lst = self.chk_var_re_dec_exp_syntx(var_only_lst)
                print(var_only_lst)
                print(redec_lst)
                if 0 in redec_lst:
                    var_lst_to_chk_at_upper_scope = []
                    for i in range(len(redec_lst)):
                        if redec_lst[i] == 0:
                            var_lst_to_chk_at_upper_scope.append(var_only_lst[i])
                    var_present_dict = self.chk_if_var_in_upper_scope(var_lst_to_chk_at_upper_scope)
                    for dictvar in var_present_dict:
                        if(var_present_dict[dictvar] == 0):
                            self.print_error_msg_ext("ERROR: Undeclared variable at line: ", line, ln_num)
                        else:
                            continue
                    print(var, expn)
                    self.expn_seq_assembler( var.strip(' '), var.strip(' '), expn, line, ln_num)
                else:
                    self.expn_seq_assembler( var.strip(' '), var.strip(' '), expn, line, ln_num)
                    #return 1
            else:
                return 0
        return 1
                    



    def upd_var_lst_add_declrtn_event(self, var_lst):
        for var in var_lst:
            self.current_scope_var_list.append(var)
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('DECLARATION', var)
            
            

    def chk_if_var_in_upper_scope(self, var_lst):
        print("ENTERED upper scope chkr: ", var_lst)
        zeros_list = [0 for _ in range(len(var_lst))]
        var_present_at_upper_scope_lst = dict(zip(var_lst, zeros_list))
        print(var_present_at_upper_scope_lst)
        for lst in self.scope_var_lst_stck:
            for var in lst:
                if var in var_lst:
                    var_present_at_upper_scope_lst[var] = 1
        return var_present_at_upper_scope_lst
            
                    
    def var_declrtn_chkr(self, var):
        if var in self.current_scope_var_list:
            return 1
        else:
            return 0


    def chk_var_re_dec_exp_syntx(self, var_lst):
        var_already_declrd_lst = []
        for var in var_lst:
            var_already_declrd_lst.append(self.var_declrtn_chkr(var)) 
        return var_already_declrd_lst



    def chk_break_stmt_n_upd(self, line, ln_num):       
        break_stmt_match_obj = re.search(self.re_break_stmt_dtection, line)
        if(break_stmt_match_obj):
            print("INFO: detected 'break' statement at line: " + str(ln_num) + ': ' + line)
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('BREAK', 'SWITCH')
            return 1
        else:
            return 0


    def condition_chkr(self, line, ln_num, stmt_type):
            cond_temp_var = "COND_var_"+str(self.tmp_var_cnt)
            self.tmp_var_cnt += 1           
            if stmt_type==0:
                chk_stmt = self.re_if_stmt
                print_stmt = "if()"
                event_type = 'BRANCH'
            elif(stmt_type==1):
                chk_stmt = self.re_elseif_else
                print_stmt = "else if()"
                event_type = 'BRANCH'
            elif(stmt_type==2):
                chk_stmt = self.re_detect_switch_stmt  
                print_stmt = "switch()"  
                event_type = 'BRANCH'
            elif(stmt_type == 3):
                chk_stmt = self.re_detect_while_from_dowhile
                print_stmt = "while()"    
                event_type = 'LOOP'
            cond_str_to_parse = [cond_temp_var + '=' +  re.findall("^\s*" + chk_stmt, line)[0].replace(' ', '').strip(' ')]           
            print(cond_str_to_parse)
            if(self.expression_syntax_parser(cond_str_to_parse, line, ln_num)):
                print("INFO: " + print_stmt + " branch statement at line: " + str(ln_num) + ': ' + line)
                self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1, sw_expn=cond_temp_var)
                self.parse_event_seq_cntr += 1
                self.parse_event_sequence_dict[self.parse_event_seq_cntr] = (event_type, cond_temp_var)
            else:
                self.print_error_msg_ext("ERROR: Failed condition evaluation at line: ", line, ln_num)




    def chk_do_while_loop_n_upd(self, line, ln_num):
        do_stmt_match_obj = re.search(self.re_detect_do_stmt, line)
        while_stmt_match_obj = re.search(self.re_detect_while_from_dowhile, line)
        if(do_stmt_match_obj):
            self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1)
            self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[0])
            if(self.do_while_mngr.current_state == self.do_while_mngr.fsm_states[3]):
                return 0
            else:
                return 1
        elif(while_stmt_match_obj):
            self.condition_chkr(line, ln_num, 3)
            self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[1])
            if(self.do_while_mngr.current_state == self.do_while_mngr.fsm_states[3]):
                return 0
            else:
                return 1
        else:
            return 0


    def chk_switch_case_n_upd(self, line, ln_num):
        sw_stmt_match_obj = re.search(self.re_detect_switch_stmt, line)
        case_stmt_match_obj = re.search(self.re_detect_case_n_value, line)
        default_stmt_match_obj = re.search(self.re_detect_sw_default_stmt, line)
        if(sw_stmt_match_obj):
            print("INFO: Detected switch statement: " + line)
            self.condition_chkr(line, ln_num, 2)
            print("INFO: LAST switch_expn value: ", self.parse_event_sequence_dict[self.parse_event_seq_cntr][1])
            expn = self.parse_event_sequence_dict[self.parse_event_seq_cntr][1]
            self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[0], sw_expn=expn, case_value='')
            if(self.sw_case_mngr.current_state == self.sw_case_mngr.fsm_states[3]):
                return 0
            else:
                return 1
        elif(case_stmt_match_obj):
            print("INFO: Detected case statement: line:" + line)
            case_val =  re.findall(self.re_detect_case_n_value, line)[0].replace(' ', '').strip(' ')
            self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[5], case_value=case_val)
            print(self.sw_case_mngr.get_last_sw_cond_expn_val())
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('BRANCH_TARG', self.sw_case_mngr.get_last_sw_cond_expn_val() + '==' + case_val)
            if(self.sw_case_mngr.current_state == self.sw_case_mngr.fsm_states[3]):
                return 0
            else:
                return 1
        elif(default_stmt_match_obj):
            print("INFO: Detected default statement: " + line)
            self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[3])
            if(self.sw_case_mngr.current_state == self.sw_case_mngr.fsm_states[3]):
                return 0
            else:
                return 1
        else:
            return 0
        
        

    def chk_if_else_syntx_upd(self, line, ln_num):
        if_stmt_match_obj = re.search("^\s*" + self.re_if_stmt, line)
        elseif_stmt_mstch_obj = re.search("^\s*" + self.re_elseif_else, line)
        else_w_cbrace_match_obj = re.search("^\s*" + self.re_else_only_w_brackt, line)
        print(if_stmt_match_obj)
        if(if_stmt_match_obj and (self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[0] or self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[2])):
            self.condition_chkr(line, ln_num, stmt_type=0)
            self.if_else_mngr.update_fsm_state(0)
            return 1
        elif(elseif_stmt_mstch_obj and self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[1]):
            self.condition_chkr(line, ln_num, stmt_type=1)
            self.if_else_mngr.update_fsm_state(4)
            return 1
        elif(else_w_cbrace_match_obj and self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[1]):
            self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1)
            self.if_else_mngr.update_fsm_state(5)
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
            print(rm_semicoln_nl_sp)
            if(match_type==1):
                var_n_expn_lst = rm_semicoln_nl_sp.split(',')
                var_only_lst = re.sub(self.re_get_exp, '',  rm_semicoln_nl_sp).replace(' ', '').split(',')
                print(var_n_expn_lst)
                print(var_only_lst)
                var_only_lst_clndup = []
                if 1 in self.chk_var_re_dec_exp_syntx(var_only_lst):
                    self.print_error_msg_ext("ERROR: Variable re-declaration at line: ", line, ln_num)
                else:
                    var_only_lst_clndup += [i.strip(' ') for i in var_only_lst]
                    self.upd_var_lst_add_declrtn_event(var_only_lst_clndup)
                    if(type(var_n_expn_lst) != list):
                        var_n_expn_lst_filtered = [i.replace(' ', '').strip(' ') for i in [var_n_expn_lst] if '=' in i]
                    else:
                        var_n_expn_lst_filtered = [i.replace(' ', '').strip(' ') for i in var_n_expn_lst if '=' in i]                        
                    print(var_n_expn_lst_filtered)
                    self.expression_syntax_parser(var_n_expn_lst_filtered, line, ln_num)
            else:
                var_n_expn_lst = [rm_semicoln_nl_sp.replace(' ', '').strip(' ')]
                var_only_lst = re.sub(self.re_get_exp, '',  rm_semicoln_nl_sp)
                redec_lst = self.chk_var_re_dec_exp_syntx([var_only_lst.strip(' ')])
                print(var_n_expn_lst)
                print(var_only_lst)
                print(redec_lst)
                if 1 in redec_lst:
                    self.expression_syntax_parser(var_n_expn_lst, line, ln_num)
                else:
                    var_lst_to_chk_at_upper_scope = []
                    for i in range(len(redec_lst)):
                        if redec_lst[i] == 0:
                            var_lst_to_chk_at_upper_scope.append(var_only_lst[i])
                    var_present_dict = self.chk_if_var_in_upper_scope(var_lst_to_chk_at_upper_scope)
                    print(var_present_dict)
                    for var in var_present_dict:
                        if(var_present_dict[var] == 0):
                            self.print_error_msg_ext("ERROR: Undeclared variable at line: ", line, ln_num)
                        else:
                            self.expression_syntax_parser(var_n_expn_lst, line, ln_num)
            self.if_else_mngr.update_fsm_state(self.if_else_mngr.fsm_transition_events[1])
            self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[2])
            self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[2])
            return 1
        else:
            return 0
        
        
            
    def chk_cbrace_reqmnt_n_upd(self, line, ln_num = None, ln_is_mn_fn = 0, sw_expn=""):
        ln_splt_at_cbrace = line.split("{")
        if (len(ln_splt_at_cbrace) > 1):
            print("INFO: Found open cbrace at line:" + str(ln_num))
            if(ln_is_mn_fn):
                print("INFO: Cbrace entered ln_is_mn_fn")
                self.opn_expt_set_by_swcase = 0
                self.expecting_opn_cbrace = 0
                self.expecting_cls_cbrace = 1
                self.open_cbrace_cntr += 1
                if(self.current_scope_var_list != []):
                    self.scope_var_lst_stck.append(self.current_scope_var_list)
                    self.current_scope_var_list = []
                self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[1],  case_value='')
                # if(self.sw_case_mngr.current_state > 0):
                #     self.opn_expt_set_by_swcase = 1
                #     self.expecting_opn_cbrace = 1
            else:
                print("INFO: Cbrace entered ln_is_mn_fn else")
                if ((re.search("\s*", ln_splt_at_cbrace[0]))):
                    self.expecting_opn_cbrace = 0
                    self.expecting_cls_cbrace = 1
                    self.open_cbrace_cntr += 1
                    if(self.current_scope_var_list != []):
                        self.scope_var_lst_stck.append(self.current_scope_var_list)
                        self.current_scope_var_list = []
                    self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[1])
                    self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[3])
                    # if(self.sw_case_mngr.current_state > 0):
                    #     self.opn_expt_set_by_swcase = 1
                    #     self.expecting_opn_cbrace = 1
                    if(re.search("^\s*$", ln_splt_at_cbrace[1]) ):
                        pass
                    else:
                        self.chk_var_dec_or_assignmnt(ln_splt_at_cbrace[1], ln_num)
                else:
                    self.print_error_msg_ext("ERROR: Syntax error at line num: ",  line, ln_num)
            return 1
        else:
            self.expecting_opn_cbrace = 1
            return 0



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
                    if(self.current_scope_var_list != [] and self.scope_var_lst_stck != []):
                        self.done_scope_var_lst_stck.append(self.current_scope_var_list)
                        self.current_scope_var_list = []
                        self.current_scope_var_list = self.scope_var_lst_stck.pop()
                    if(self.open_cbrace_cntr == 0):
                        self.expecting_cls_cbrace = 0
                    print("INFO: Found cls cbrace at line: " + str(ln_num) + " " + line)
                    self.if_else_mngr.update_fsm_state(self.if_else_mngr.fsm_transition_events[3])
                    self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[4])
                    self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[4])
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

def join_file_lines(fl_ln_lst):
    file_lines_new_line_rmd = ' '.join([i.strip('\n') for i in  fl_ln_lst])
    return file_lines_new_line_rmd

def splite_file_lines_at_brace_or_semicolon(file_lines_new_line_rmd):
    for_lst = re.findall("\s*for\s*(\(.*?;.*?;.*?\))\s*{\s*", file_lines_new_line_rmd)
    for condlst in for_lst:
        file_lines_new_line_rmd = re.sub(condlst, '_tmp_', file_lines_new_line_rmd)
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace(';', ';\n')
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace(':', ':\n')
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace('{', '{\n')
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace('}', '\n}\n')  
    for condlst in for_lst:
        file_lines_new_line_rmd = file_lines_new_line_rmd.replace('_tmp_', condlst, count=1)
    split_lines = file_lines_new_line_rmd.split('\n')
    return split_lines

def reformat_n_comments_rmd_file_lines(fl_ln_lst):
    fllst_cmnt_rmd = []
    for line_num in range(len(fl_ln_lst)):
        line_n = line_num+1
        if(Comment_obj.chk_cmnt_n_upd(fl_ln_lst[line_num], line_n)):
            continue
        else:
            fllst_cmnt_rmd.append(fl_ln_lst[line_num])
    file_lines_new_line_rmd = join_file_lines(fllst_cmnt_rmd)
    formatted_file_lns = splite_file_lines_at_brace_or_semicolon(file_lines_new_line_rmd)
    return formatted_file_lns

def start_fl_parse(file_lns):
    prog_obj = Program_obj(default_svr_lvl)
    # Go into loop for each line #
    for line_num in range(len(file_lns)):
        line_n = line_num+1
        print("TEST: Event seq:")
        print(prog_obj.current_scope_var_list)
        print(prog_obj.scope_var_lst_stck)
        print(prog_obj.done_scope_var_lst_stck) 
        print("TEST: if..else current state: ", prog_obj.if_else_mngr.current_state)
        print("TEST: switch case current state: ", prog_obj.sw_case_mngr.current_state)
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
        # Check if line has close brace #
        elif(prog_obj.chk_cbrace_closure(file_lns[line_num], line_n)):
            continue
        # Check syntax for main func entry -> state vars: mn_fn_entered, expecting_opn_cbrace #
        elif(prog_obj.chk_main_fn_entry(file_lns[line_num], line_n)):
            continue
        # break statement detection #
        elif(prog_obj.chk_break_stmt_n_upd(file_lns[line_num], line_n)):
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
        elif(prog_obj.chk_switch_case_n_upd(file_lns[line_num], line_n)):
            continue
        # Check for loop syntax and upd loop state var #
        elif(prog_obj.chk_do_while_loop_n_upd(file_lns[line_num], line_n)):
            continue
        # Previous src code line was entry into main fn but with no open cbrace -> chk for that now #
        elif(prog_obj.chk_cbrace_reqmnt_n_upd(file_lns[line_num], ln_num=line_n, ln_is_mn_fn=1)):
            continue
        else:
            prog_obj.print_error_msg_ext("WIP: UNKNOWN syntax at line: ", file_lns[line_num], line_n)          
    print(prog_obj.expecting_cls_cbrace)   
    if(prog_obj.expecting_cls_cbrace != 0):
        prog_obj.print_error_msg_ext("ERROR: unclosed { in program: line:", file_lns[len(file_lns)-1], len(file_lns)-1)
        
    
    
    
# Main script begins #
if(__name__ == "__main__"):
    start_time = time.time()
    flist = get_file_list_for_compile()
    for fl in flist:
        fl_lns = get_file_lines_list(fl)
        print(fl_lns)
        final_fl_lns = reformat_n_comments_rmd_file_lines(fl_lns)
        print('\n'.join(final_fl_lns))
        start_fl_parse(final_fl_lns)
    print("Program runtime:")
    print(f"--- {time.time() - start_time:.6f} seconds ---")