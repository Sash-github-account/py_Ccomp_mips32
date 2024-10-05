# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 12:50:59 2024

@author: nsash

Version : 19: 
    -> bug fix: inc/dec operation in a direct assignment through a single line needed parse event updation
    
Opens:     
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
    -> No in-line comments: Comments only supported at start of line, ie., an entire line can be a comment but there can be no comments in lines where there is code
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

#===== Comment class, stores info about comment lines in a file, in a dict =====#
#===== Has method to check if a line is a comment n update the cmnt dict  =====#
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
        



#===== IfElseManager class, stores maintains nesting state of IFelse branch statement =====#
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
        self.cond_var_stack = []

    def __str__(self):
        return f"{self.if_nest_level_cntr}({self.current_state})"

    def push_cond_var(self, cond_var_label):
        self.cond_var_stack.append(cond_var_label)
        
        
    def pop_cond_var(self):
        condvar = self.cond_var_stack.pop() if len(self.cond_var_stack) > 0 else 0
        return condvar 
    
    def transtion_from_waitingForIf_state(self, transition_event):
        if(transition_event == self.fsm_transition_events[0]):
            self.current_state = self.fsm_states[4]
        elif(transition_event == self.fsm_transition_events[5]):
            self.current_state = self.fsm_states[5]
        else:
            self.current_state = self.current_state 
        return None
 
    def transition_from_WaitForIfClsBrace(self, transition_event):
        if(transition_event == self.fsm_transition_events[3]):
            self.current_state = self.fsm_states[1]
            return self.pop_cond_var()
        elif(transition_event == self.fsm_transition_events[2] or transition_event == self.fsm_transition_events[0]):
            self.if_nest_level_cntr += 1
        elif(transition_event == self.fsm_transition_events[5] or transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[5]
        else:
            self.current_state = self.current_state
        return None
 
    
    def transition_from_waitForElseifClsBrace(self, transition_event):
        if(transition_event == self.fsm_transition_events[5] or transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[5]
        elif(transition_event == self.fsm_transition_events[2] or transition_event == self.fsm_transition_events[0]):
            self.current_state = self.fsm_states[4]
            self.if_nest_level_cntr += 1
        elif(transition_event == self.fsm_transition_events[3]):
            self.current_state = self.fsm_states[1]
            return self.pop_cond_var()
        else:
            self.current_state = self.current_state
        return None

    def transition_from_NxtCanBeElseOrElseif(self, transition_event):
        if(transition_event == self.fsm_transition_events[5]):
            self.current_state = self.fsm_states[2]
        elif(transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[3]
        elif(transition_event == self.fsm_transition_events[1] and self.if_nest_level_cntr > 0):
            self.if_nest_level_cntr -= 1
            self.current_state = self.fsm_states[4]
            return self.pop_cond_var()
        elif(transition_event == self.fsm_transition_events[1] and self.if_nest_level_cntr == self.fsm_transition_events[0]):
            self.current_state = self.fsm_states[0]
        else:
            self.current_state =  self.current_state    
        return None


    def transition_from_waitForElseClsBrace(self, transition_event):
        if(transition_event == self.fsm_transition_events[5] or transition_event == self.fsm_transition_events[4]):
            self.current_state = self.fsm_states[5]
        elif(transition_event == self.fsm_transition_events[0] or transition_event == self.fsm_transition_events[2]):
            self.if_nest_level_cntr += 1
            self.current_state = self.fsm_states[4]
        elif(transition_event == self.fsm_transition_events[3] and self.if_nest_level_cntr > 0):
            self.if_nest_level_cntr -= 1
            self.current_state = self.fsm_states[4]
            return self.pop_cond_var()
        elif(transition_event == self.fsm_transition_events[1] and self.if_nest_level_cntr == 0):
            self.current_state = self.fsm_states[0]
        else:
            self.current_state =  self.current_state          
        return None

    
    def update_fsm_state(self, transition_event):
        ret_popd_condvar = ''
        if(self.current_state == self.fsm_states[0]):
            ret_popd_condvar = self.transtion_from_waitingForIf_state(transition_event)
        elif(self.current_state == self.fsm_states[4]):
            ret_popd_condvar = self.transition_from_WaitForIfClsBrace(transition_event)
        elif(self.current_state == self.fsm_states[3]):
            ret_popd_condvar = self.transition_from_waitForElseifClsBrace(transition_event)
        elif(self.current_state == self.fsm_states[1]):
            ret_popd_condvar = self.transition_from_NxtCanBeElseOrElseif(transition_event)
        elif( self.current_state ==  self.fsm_states[2]):
            ret_popd_condvar = self.transition_from_waitForElseClsBrace(transition_event)
        else:
            ret_popd_condvar = self.current_state =  self.current_state
        return ret_popd_condvar
#--------- END of IfElseManager class----------#     





#===== SwitchCaseManager class, stores maintains nesting state of switch-case branch statement =====#
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
        self.cond_var_stack = []
        
    def __str__(self):
        return f"{self.sw_int_opnbr_stk}({self.switch_nest_lvl})({self.cur_int_opn_brc_cnt})({self.cur_sw_deflt_defnd})({self.cur_sw_case_vals})"
 
    def push_cond_var(self, cond_var_label):
        self.cond_var_stack.append(cond_var_label)
        
        
    def pop_cond_var(self):
        condvar = self.cond_var_stack.pop() if len(self.cond_var_stack) > 0 else 0
        return condvar 
    
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
            return self.pop_cond_var()
        else:
            if(self.cur_int_opn_brc_cnt > 1):
                self.cur_int_opn_brc_cnt -= 1
                self.chk_int_open_brace_n_upd_state()
                return None
            else:
                self.switch_nest_lvl -= 1
                self.cur_int_opn_brc_cnt, self.cur_sw_deflt_defnd, self.cur_sw_case_vals,  self.cur_sw_stmt_cond_expn = self.sw_int_opnbr_stk.pop()
                self.chk_int_open_brace_n_upd_state()
                return self.pop_cond_var()
        
        
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
        return None
            
        
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
            condvar = self.process_cls_brace_transitions()
            return condvar
        elif(te == self.fsm_transition_events[5]):
            self.process_case_stmt_for_cur_sw(case_value)
        else:
            self.current_state = self.current_state
        return None
            
        
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
            condvar = self.process_cls_brace_transitions()
            return condvar
        elif(te == self.fsm_transition_events[5]):
            self.process_case_stmt_for_cur_sw(case_value)
        else:
            self.current_state = self.current_state
        return None
            
    
    def update_fsm_state(self, transition_event, sw_expn = '', case_value = ''):
        if(self.current_state == self.fsm_states[0]):
            self.transition_from_waitForSwitch_state(transition_event, sw_expn)
        elif(self.current_state == self.fsm_states[1]):
            condvar = self.transition_from_waitForDefault_state(transition_event, case_value)
            return condvar
        elif(self.current_state == self.fsm_states[2]):
            condvar = self.transition_from_waitForSwStmtCls_state(transition_event, case_value)
            return condvar
        else:
            self.current_state =  self.current_state
        return None
            
    def get_last_sw_cond_expn_val(self):
        print("INFO: get_last_sw_cond_expn_val() from switch case manager called. Sending this value:")
        if self.cur_sw_stmt_cond_expn == '':
            print("from stack: ",self.sw_int_opnbr_stk[len(self.sw_int_opnbr_stk)-1])
            return self.sw_int_opnbr_stk[len(self.sw_int_opnbr_stk)-1][3]
        else:
            print("from attribute: ", self.cur_sw_stmt_cond_expn)
            return self.cur_sw_stmt_cond_expn
#--------- END of SwitchCaseManager class----------#     




#===== DoWhileManager class, stores maintains nesting state of do-while loop statement =====#
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
        self.cond_var_stack = []

    def __str__(self):
        return f"{self.current_state}({self.stck_nst_lvl})({self.nstd_do_lvl_cntr})({self.cur_nstd_opn_brace_cntr})"
  
    def push_cond_var(self, cond_var_label):
        self.cond_var_stack.append(cond_var_label)
        
        
    def pop_cond_var(self):
        condvar = self.cond_var_stack.pop() if len(self.cond_var_stack) > 0 else 0
        return condvar
    
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
            self.stck_nst_lvl.append(self.cur_nstd_opn_brace_cntr)
        elif(te == self.fsm_transition_events[1]):
            self.current_state = self.fsm_states[3]
        elif(te == self.fsm_transition_events[3]):
            self.cur_nstd_opn_brace_cntr += 1
        elif(te == self.fsm_transition_events[4]):
            if(self.cur_nstd_opn_brace_cntr == 1):
                self.cur_nstd_opn_brace_cntr = 0
                self.current_state = self.fsm_states[2]
            else:
                self.cur_nstd_opn_brace_cntr -= 1
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
            return self.pop_cond_var()
        

    def update_fsm_state(self, transition_event):
        if(self.current_state == self.fsm_states[0]):
            self.transition_from_waitForDo_state(transition_event)
        elif(self.current_state == self.fsm_states[1]):
            self.transition_from_waitForWhileClsBrace_state(transition_event)
            return self.pop_cond_var()
        elif(self.current_state == self.fsm_states[2]):
            condvar = self.transition_from_nxtSldBeWhile_state(transition_event)
            return condvar
        else:
            self.current_state =  self.current_state    
        return None
#--------- END of DoWhileManager class----------#     


#===== WhileManager class, stores maintains nesting state of do-while loop statement =====#
class ForWhileLoopManager:
    fsm_states = [
        0, # wait for while/for stmt:
        1, # wait for while cls brace:
        ]

    fsm_transition_events = [
        0, # got while/for stmt
        1, # got }:
        2, # got code stmt:
        3, # got {:
        ]

    def __init__(self):
        self.current_state = self.fsm_states[0]
        self.while_for_nst_lvl_cntr = 0
        self.cur_nst_lvl_opn_brc = 0
        self.stk_cur_nst_lvl_opn_brc =[]
        self.cond_var_stack = []

    def __str__(self):
        return f"{self.current_state}({self.stk_cur_nst_lvl_opn_brc})({self.while_for_nst_lvl_cntr})({self.cur_nst_lvl_opn_brc})"
 
    
 
    def push_cond_var(self, cond_var_label):
        self.cond_var_stack.append(cond_var_label)
        
        
    def pop_cond_var(self):
        condvar = self.cond_var_stack.pop() #if len(self.cond_var_stack) > 0 else 0
        return condvar

    def transition_from_waitForWhile_state(self, te):
        if(te == self.fsm_transition_events[0]):
            self.while_for_nst_lvl_cntr += 1
            self.cur_nst_lvl_opn_brc += 1
            self.current_state = self.fsm_states[1]
        else:
            self.current_state =self.current_state 
         
    
    def transition_from_waitForWhileClsBrace_state(self, te):
        if(te == self.fsm_transition_events[0]):
            self.while_for_nst_lvl_cntr += 1
            self.cur_nst_lvl_opn_brc += 1
            self.stk_cur_nst_lvl_opn_brc.append(self.cur_nst_lvl_opn_brc)
            self.cur_nst_lvl_opn_brc = 0
        elif(te == self.fsm_transition_events[1]):
            if(self.cur_nst_lvl_opn_brc == 1):       
                if(self.while_for_nst_lvl_cntr == 1):
                    self.while_for_nst_lvl_cntr -= 1
                    self.current_state = self.fsm_states[0]
                else:                 
                    self.cur_nst_lvl_opn_brc = self.stk_cur_nst_lvl_opn_brc.pop()
                    self.while_for_nst_lvl_cntr -= 1
                    self.current_state = self.fsm_states[1]
                return self.pop_cond_var()
            else:
                self.cur_nst_lvl_opn_brc -= 1
                self.current_state = self.fsm_states[1]
        elif(te == self.fsm_transition_events[3]):
            self.cur_nst_lvl_opn_brc += 1
        else:
            self.current_state =self.current_state 
        return None
    

    def update_fsm_state(self, transition_event):
        if(self.current_state == self.fsm_states[0]):
            self.transition_from_waitForWhile_state(transition_event)
        elif(self.current_state == self.fsm_states[1]):
            condvar = self.transition_from_waitForWhileClsBrace_state(transition_event)
            return condvar
        else:
            self.current_state =  self.current_state   
        return None
#--------- END of WhileManager class----------#     



#===== Program_obj class, stores info about comment lines in a file, in a dict =====#
class ParserNOperationSeqr:
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
    re_post_inc_or_dec_stmt = "^\s*" + re_get_var_name + '(\+\+|\-\-)\s*;\s*'
    re_pre_inc_or_dec_stmt = "^\s*" + '(\+\+|\-\-)'+ re_get_var_name + '\s*;\s*'
    re_for_stmt = "^\s*for\s*\((.*);(.*);(.*)\)\s*{\s*"
    re_var_w_inc_or_dec = '([a-zA-Z_]+[0-9a-zA-Z_]*(?:\+\+|\-\-)|(?:\+\+|\-\-)[a-zA-Z_]+[0-9a-zA-Z_]*)'
    operator_lst_precedence_h2l = [ '/', '*', '%', '+', '-', '<<', '>>', '<', '>', '<=', '>=', '==', '!=', '&', '^', '|', '&&', '||']
    
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
        self.while_mngr = ForWhileLoopManager()
        self.for_mngr = ForWhileLoopManager()
        
    def __str__(self):
        return f"(Main funtion at line: {self.mn_fn_def_ln_num})"


    def print_error_msg_ext(self, msg_strng, line, ln_num):
        print(msg_strng + str(ln_num) + ' ' + line)
        print("Program runtime:")
        print(f"--- {time.time() - start_time:.6f} seconds ---")
        sys.exit()  


    def pre_process_increment_or_decrement(self, expn):
        expn_incdec_replcd = expn
        inc_dec_op_lst = re.findall(self.re_var_w_inc_or_dec, expn)
        for varop in inc_dec_op_lst:
            if(re.search('\+\+'+ self.re_get_var_name, varop)):
                op_type = '_TMPPRE_TEMPINC'
            elif(re.search('\-\-'+ self.re_get_var_name, varop)):
                op_type = '_TMPPRE_TEMPDEC'
            elif(re.search(self.re_get_var_name + '\+\+', varop)):
                op_type = '_TMPPOST_TEMPINC'
            elif(re.search(self.re_get_var_name + '\-\-', varop)):
                op_type = '_TMPPOST_TEMPDEC'
            var = re.search(self.re_get_var_name, varop).group()
            expn_incdec_replcd = expn_incdec_replcd.replace(varop, var + op_type)
        return expn_incdec_replcd



    def pre_or_post_inc_dec_parse_event_handlr(self, var, is_pre):
        if(is_pre):
            pre_post_str = 'PRE'
        else:
            pre_post_str = 'POST'
        if '_TMP'+ pre_post_str +'_TEMPINC' in var:
            var_extrt = re.search(self.re_get_var_name, var).group().replace('_TMP'+ pre_post_str +'_TEMPINC', '').replace(" ", '').strip(' ')
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ( var_extrt, var_extrt+'+1')
            return var_extrt
        elif '_TMP'+ pre_post_str +'_TEMPDEC' in var:
            var_extrt = re.search(self.re_get_var_name, var).group().replace('_TMP'+ pre_post_str +'_TEMPDEC', '').replace(" ", '').strip(' ')
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ( var_extrt, var_extrt+'-1')
            return var_extrt
        elif '_TMP'+ pre_post_str + '_TEMPINC' in var:
            var_extrt = re.search(self.re_get_var_name, var).group().replace('_TMP'+ pre_post_str + '_TEMPINC', '').replace(" ", '').strip(' ')
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ( var_extrt, var_extrt+'+1')
            return var_extrt
        elif '_TMP'+ pre_post_str + '_TEMPDEC' in var:
            var_extrt = re.search(self.re_get_var_name, var).group().replace('_TMP'+ pre_post_str + '_TEMPDEC', '').replace(" ", '').strip(' ')
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ( var_extrt, var_extrt+'-1')
            return var_extrt
        else:
            return var




    def pedmas_assembler(self, expn_in):      
        print("INFO: Entering PEDMAS expression assembler.")
        expn = self.pre_process_increment_or_decrement(expn_in)
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
                multi_op_var_lst = list(item)
                for varnum in range(len(item)-1):
                    tmp_var = 'PEDMAStmpvar'+str(self.tmp_var_cnt)
                    var1_pre = multi_op_var_lst.pop(0)
                    print("INFO: var1_pre: ", var1_pre)
                    var1 = self.pre_or_post_inc_dec_parse_event_handlr(var1_pre, 1) 
                    print("INFO: var1: ", var1)
                    expn = expn.replace(var1_pre, var1.replace('_TMPPOST_TEMPINC', '').replace('_TMPPOST_TEMPDEC', ''))
                    print("INFO: expn: ", expn)
                    var2_pre = multi_op_var_lst.pop(0)
                    print("INFO: var2_pre: ", var2_pre)
                    var2 = self.pre_or_post_inc_dec_parse_event_handlr(var2_pre, 1) 
                    print("INFO: var2: ", var2)
                    expn = expn.replace(var2_pre, var2.replace('_TMPPOST_TEMPINC', '').replace('_TMPPOST_TEMPDEC', ''))
                    print("INFO: expn: ", expn)
                    multi_op_var_lst.insert(0,tmp_var)
                    rplc_str = var1.replace('_TMPPOST_TEMPINC', '').replace('_TMPPOST_TEMPDEC', '')+"\\"+self.operator_lst_precedence_h2l[op]+var2.replace('_TMPPOST_TEMPINC', '').replace('_TMPPOST_TEMPDEC', '')
                    print(rplc_str)
                    self.parse_event_seq_cntr += 1
                    self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ( tmp_var, ''.join(rplc_str.split("\\")))
                    expn = re.sub(rplc_str, tmp_var, expn, count=1)
                    self.tmp_var_cnt += 1
                    var1_post = self.pre_or_post_inc_dec_parse_event_handlr(var1_pre, 0)
                    expn = expn.replace(var1_pre, var1_post)
                    var2_post = self.pre_or_post_inc_dec_parse_event_handlr(var2_pre, 0)
                    expn = expn.replace(var2_pre, var2_post)
        print("INFO: exiting PEDMAS expression assembler")
        return expn
                    
                    
    
    def expn_seq_assembler(self, init_var, var, x1, line, ln_num): 
        print("INFO: identifing sequence of operations in expression")
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
            var_extr = self.pre_or_post_inc_dec_parse_event_handlr(tmp_var, 1)
            var_to_print = var_extr.replace('_TMPPOST_TEMPINC', '').replace('_TMPPOST_TEMPDEC', '')
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = (init_var, var_to_print)
            self.pre_or_post_inc_dec_parse_event_handlr(var_extr, 0)
            return 1            
        else:
            self.print_error_msg_ext("ERROR: expression syntax error at line: ", line, ln_num)
        
        
    
    def expression_syntax_parser(self, var_n_assignmnt_exp_lst, line, ln_num):
        print("INFO: parsing expression syntax")
        for var_expn in var_n_assignmnt_exp_lst:
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
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('@DECLARATION', var)
            
            

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
                print_stmt = "while() from do-while"    
                event_type = 'LOOP'
            elif(stmt_type == 4):
                chk_stmt = self.re_detect_while_loop_stmt
                print_stmt = "while()"    
                event_type = 'LOOP'
            elif(stmt_type == 5):
                chk_stmt = '.*'
                print_stmt = 'for(;;)'
                event_type = 'LOOP'
            cond_str_to_parse = [cond_temp_var + '=' +  re.findall("^\s*" + chk_stmt, line)[0].replace(' ', '').strip(' ')]           
            print(cond_str_to_parse)
            self.parse_event_seq_cntr += 1
            self.parse_event_sequence_dict[self.parse_event_seq_cntr] = (event_type, cond_temp_var)
            if(self.expression_syntax_parser(cond_str_to_parse, line, ln_num)):
                print("INFO: " + print_stmt + " statement at line: " + str(ln_num) + ': ' + line)
                self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1, sw_expn=cond_temp_var)
                return cond_temp_var
            else:
                self.print_error_msg_ext("ERROR: Failed condition evaluation at line: ", line, ln_num)



    def chk_for_loop_n_upd(self, line, ln_num):
        print("INFO: Entering for loop checker for line: " + str(ln_num) + ': ' + line)
        for_stmt_match_obj = re.search(self.re_for_stmt, line)
        if(for_stmt_match_obj):
            print("INFO: Detected 'for' statement: " + line)
            for_var, for_cond, for_var_inc_dec = re.findall(self.re_for_stmt, line)[0]
            for_var, for_cond, for_var_inc_dec = for_var.strip(' '), for_cond.replace(' ', '').strip(' '), for_var_inc_dec.replace(' ', '').strip(' ')
            chk_var_init = self.chk_var_dec_or_assignmnt(for_var+';', ln_num)
            if(chk_var_init):
                condvar = self.condition_chkr(for_cond, ln_num, 5)
                if(self.chk_standalone_var_inc_dec_stmt(for_var_inc_dec+';', ln_num)):
                    self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1, sw_expn='')
                    self.for_mngr.update_fsm_state(self.for_mngr.fsm_transition_events[0])
                    return 1
                elif(self.chk_var_dec_or_assignmnt(for_var_inc_dec+';', ln_num)):
                    self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1, sw_expn='')
                    self.for_mngr.update_fsm_state(self.for_mngr.fsm_transition_events[0])
                    return 1
                else:
                    return 0   
                self.for_mngr.push_cond_var(condvar)
            else:
                return 0
        else:
            return 0



    def chk_while_n_upd(self, line, ln_num):
        print("INFO: Entering while checker for line: " + str(ln_num) + ': ' + line)
        while_match_obj = re.search(self.re_detect_while_loop_stmt, line)
        if(while_match_obj):
            print("INFO: Detected while statement: " + line)
            condvar = self.condition_chkr(line, ln_num, 4)
            self.while_mngr.update_fsm_state(self.while_mngr.fsm_transition_events[0])
            print(condvar)
            self.while_mngr.push_cond_var(condvar)
            return 1
        else:
            return 0


    def chk_do_while_loop_n_upd(self, line, ln_num):
        print("INFO: Entering do-while checker for line: " + str(ln_num) + ': ' + line)
        do_stmt_match_obj = re.search(self.re_detect_do_stmt, line)
        while_stmt_match_obj = re.search(self.re_detect_while_from_dowhile, line)
        if(do_stmt_match_obj):
            print("INFO: Detected do statement: " + line)
            self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1)
            self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[0])
            if(self.do_while_mngr.current_state == self.do_while_mngr.fsm_states[3]):
                return 0
            else:
                return 1
        elif(while_stmt_match_obj):
            print("INFO: Detected while from do-while statement: " + line)
            condvar = self.condition_chkr(line, ln_num, 3)
            print("INFO: do_while manager FSM state before while(); detection: ", self.do_while_mngr.cur_nstd_opn_brace_cntr )
            self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[1])
            print("INFO: do_while manager FSM state after while(); detection: ", self.do_while_mngr.cur_nstd_opn_brace_cntr )
            self.do_while_mngr.push_cond_var(condvar)
            if(self.do_while_mngr.current_state == self.do_while_mngr.fsm_states[3]):
                return 0
            else:
                return 1
        else:
            return 0


    def chk_switch_case_n_upd(self, line, ln_num):
        print("INFO: Entering switch-case checker for line: " + str(ln_num) + ': ' + line)
        sw_stmt_match_obj = re.search(self.re_detect_switch_stmt, line)
        case_stmt_match_obj = re.search(self.re_detect_case_n_value, line)
        default_stmt_match_obj = re.search(self.re_detect_sw_default_stmt, line)
        if(sw_stmt_match_obj):
            print("INFO: Detected switch statement: " + line)
            condvar = self.condition_chkr(line, ln_num, 2)
            print("INFO: LAST switch_expn value: ", self.parse_event_sequence_dict[self.parse_event_seq_cntr][1])
            expn = self.parse_event_sequence_dict[self.parse_event_seq_cntr][1]
            self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[0], sw_expn=expn, case_value='')
            self.sw_case_mngr.push_cond_var(condvar)
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
        print("INFO: Entering if-else checker for line: " + str(ln_num) + ': ' + line)
        if_stmt_match_obj = re.search("^\s*" + self.re_if_stmt, line)
        elseif_stmt_mstch_obj = re.search("^\s*" + self.re_elseif_else, line)
        else_w_cbrace_match_obj = re.search("^\s*" + self.re_else_only_w_brackt, line)
        print(if_stmt_match_obj)
        print(self.if_else_mngr.current_state)
        if(if_stmt_match_obj and (self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[0] or self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[2] or self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[3] or self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[4])):
            print("INFO: detected if() statement at line: " + str(ln_num) + ': ' + line)
            condvar = self.condition_chkr(line, ln_num, stmt_type=0)
            self.if_else_mngr.update_fsm_state(0)
            self.if_else_mngr.push_cond_var(condvar)
            return 1
        elif(elseif_stmt_mstch_obj and self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[1]):
            print("INFO: detected else if() statement at line: " + str(ln_num) + ': ' + line)
            condvar = self.condition_chkr(line, ln_num, stmt_type=1)
            self.if_else_mngr.update_fsm_state(4)
            self.if_else_mngr.push_cond_var(condvar)
            return 1
        elif(else_w_cbrace_match_obj and self.if_else_mngr.current_state == self.if_else_mngr.fsm_states[1]):
            print("INFO: detected else statement at line: " + str(ln_num) + ': ' + line)
            self.chk_cbrace_reqmnt_n_upd(line, ln_num, 1)
            self.if_else_mngr.update_fsm_state(5)
            return 1
        else:
            return 0
        
        
    def chk_standalone_var_inc_dec_stmt(self, line, ln_num):
        var_pre_incdec_match_obj = re.search(self.re_pre_inc_or_dec_stmt, line)
        var_post_incdec_match_obj = re.search(self.re_post_inc_or_dec_stmt, line)
        if(var_pre_incdec_match_obj or var_post_incdec_match_obj):
            var_processed = self.pre_process_increment_or_decrement(line.replace(' ', '').strip(';').strip(' ').strip('\n'))
            self.pre_or_post_inc_dec_parse_event_handlr(var_processed, 0)   
            return 1
        else:
            return 0


    def chk_var_dec_or_assignmnt(self, line, ln_num):
        print("INFO: Entered var declaration or assignment checker for line : " + line + ': ' + str(ln_num))
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
                var_only_lst = [re.sub(self.re_get_exp, '',  rm_semicoln_nl_sp).strip(' ')]
                redec_lst = self.chk_var_re_dec_exp_syntx(var_only_lst)
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
            self.while_mngr.update_fsm_state(self.while_mngr.fsm_transition_events[2])
            self.for_mngr.update_fsm_state(self.for_mngr.fsm_transition_events[2])
            return 1
        else:
            return 0
        
        
            
    def chk_cbrace_reqmnt_n_upd(self, line, ln_num = None, ln_is_mn_fn = 0, sw_expn=""):
        print("INFO: Entering open brace checker for line: " + str(ln_num) + ': ' + line)
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
                    self.while_mngr.update_fsm_state(self.while_mngr.fsm_transition_events[3])
                    self.for_mngr.update_fsm_state(self.for_mngr.fsm_transition_events[3])
                    if(re.search("^\s*$", ln_splt_at_cbrace[1]) ):
                        pass
                    else:
                        self.chk_var_dec_or_assignmnt(ln_splt_at_cbrace[1], ln_num)
                else:
                    self.print_error_msg_ext("ERROR: Syntax error at line num: ",  line, ln_num)
            print("INFO: Detected and processed '{' for line: " + str(ln_num) + ': ' + line)
            return 1
        else:
            print("INFO: Exiting open brace checker w/o { detection for line: " + str(ln_num) + ': ' + line)
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
                    retd_condvar_ifelse = self.if_else_mngr.update_fsm_state(self.if_else_mngr.fsm_transition_events[3])
                    retd_condvar_sw_case = self.sw_case_mngr.update_fsm_state(self.sw_case_mngr.fsm_transition_events[4])
                    retd_condvar_dowhile = self.do_while_mngr.update_fsm_state(self.do_while_mngr.fsm_transition_events[4])
                    retd_condvar_while = self.while_mngr.update_fsm_state(self.while_mngr.fsm_transition_events[1])
                    retd_condvar_for = self.for_mngr.update_fsm_state(self.for_mngr.fsm_transition_events[1])
                    if(retd_condvar_sw_case):
                        print("ENTERED SW CS RET COND VAR")
                        self.parse_event_seq_cntr += 1
                        self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('SWITCH-CASE-END', retd_condvar_sw_case)                   
                    if(retd_condvar_ifelse):
                        self.parse_event_seq_cntr += 1
                        self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('IF-END', retd_condvar_ifelse)
                    if(retd_condvar_dowhile):
                        self.parse_event_seq_cntr += 1
                        self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('DO-WHILE-END', retd_condvar_dowhile)
                    if(retd_condvar_while):
                        self.parse_event_seq_cntr += 1
                        self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('WHILE-END', retd_condvar_while)
                    if(retd_condvar_for):
                        self.parse_event_seq_cntr += 1
                        self.parse_event_sequence_dict[self.parse_event_seq_cntr] = ('FOR-END', retd_condvar_for)                
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

def split_file_lines_at_brace_or_semicolon(file_lines_new_line_rmd):
    print(file_lines_new_line_rmd)
    for_lst = re.findall("\s*for\s*(\(.*?;.*?;.*?\))\s*{\s*", file_lines_new_line_rmd)
    tmp_cnt_var = 0
    for_cond_rpl_str_lst = []
    for condlst in for_lst:
        file_lines_new_line_rmd = file_lines_new_line_rmd.replace(condlst, '_tmp_'+str(tmp_cnt_var))
        for_cond_rpl_str_lst.append('_tmp_'+str(tmp_cnt_var))
        tmp_cnt_var += 1
    print(for_lst)
    print(file_lines_new_line_rmd)
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace(';', ';\n')
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace(':', ':\n')
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace('{', '{\n')
    file_lines_new_line_rmd = file_lines_new_line_rmd.replace('}', '\n}\n')  
    for condlst_i in range(len(for_lst)):
        file_lines_new_line_rmd = file_lines_new_line_rmd.replace(for_cond_rpl_str_lst[len(for_lst)-condlst_i-1], for_lst[len(for_lst)-condlst_i-1])
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
    formatted_file_lns = split_file_lines_at_brace_or_semicolon(file_lines_new_line_rmd)
    return formatted_file_lns

def start_fl_parse(file_lns):
    prog_obj = ParserNOperationSeqr(default_svr_lvl)
    # Go into loop for each line #
    for line_num in range(len(file_lns)):
        line_n = line_num+1
        # print("TEST: Event seq:")
        # print(prog_obj.current_scope_var_list)
        # print(prog_obj.scope_var_lst_stck)
        # print(prog_obj.done_scope_var_lst_stck) 
        # print("TEST: if..else current state: ", prog_obj.if_else_mngr.current_state)
        # print("TEST: switch case current state: ", prog_obj.sw_case_mngr.current_state)
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
        elif(prog_obj.chk_standalone_var_inc_dec_stmt(file_lns[line_num], line_n)):
            continue
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
        elif(prog_obj.chk_while_n_upd(file_lns[line_num], line_n)):
            continue
        elif(prog_obj.chk_for_loop_n_upd(file_lns[line_num], line_n)):
            continue
        # Previous src code line was entry into main fn but with no open cbrace -> chk for that now #
        elif(prog_obj.chk_cbrace_reqmnt_n_upd(file_lns[line_num], ln_num=line_n, ln_is_mn_fn=1)):
            continue
        else:
            prog_obj.print_error_msg_ext("WIP: UNKNOWN syntax at line: ", file_lns[line_num], line_n)          
    #print(prog_obj.expecting_cls_cbrace)   
    if(prog_obj.expecting_cls_cbrace != 0):
        prog_obj.print_error_msg_ext("ERROR: unclosed { in program: line:", file_lns[len(file_lns)-1], len(file_lns)-1)
        
    
    
    
# Main script begins #
#if(__name__ == "__main__"):
start_time = time.time()
flist = ["test_no_stmt.c"]#get_file_list_for_compile()
for fl in flist:
    fl_lns = get_file_lines_list(fl)
    print(fl_lns)
    final_fl_lns = reformat_n_comments_rmd_file_lines(fl_lns)
    print('\n'.join(final_fl_lns))
    start_fl_parse(final_fl_lns)
print("Program runtime:")
print(f"--- {time.time() - start_time:.6f} seconds ---")