# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 23:04:19 2024

@author: nsash

Summary: Modules for testing each of the branch/loop manager FSM

Version 1:
    -> Added module to do unit testing on do-while manager to fix bugs identified by test_branch_loop_operations_combined.c
    
    
Opens:
    -> Add testers for other FSMs as well

"""
from py_Ccomp_mips32_release_version import ParserNOperationSeqr as comp
from py_Ccomp_mips32_release_version import DoWhileManager as dwm
from py_Ccomp_mips32_release_version import get_file_lines_list
from py_Ccomp_mips32_release_version import reformat_n_comments_rmd_file_lines
import re
import time


def find_key_from_value_in_dict(my_dict, value_to_find):
    key = list(my_dict.keys())[list(my_dict.values()).index(value_to_find)]
    return key



def do_while_event_generator(file_lines):
    event_list = []
    for line in file_lines:
        if(re.search(comp.re_detect_do_stmt, line)):
            event_list.append(0)
        elif(re.search(comp.re_detect_while_from_dowhile, line)):
            event_list.append(1)
        elif(len(line.split('{')) > 1):
            event_list.append(3)
        elif(len(line.split('}')) > 1):
            event_list.append(4)
        else:
            event_list.append(2)
    return event_list



def do_while_loop_fsm_tester(flist):
    dowhile_mngr = dwm()
    fsm_states = {
    0 : "waiting for 'do' stmt,",
    1 : "waiting for while cls brace,",
    2 : "nxt should be while,",
    3 : "error, exit,",
    }    
    for fl in flist:
        fl_lns = get_file_lines_list(fl)
        print(fl_lns)
        final_fl_lns = reformat_n_comments_rmd_file_lines(fl_lns)
        print('\n'.join(final_fl_lns))
        event_list = do_while_event_generator(final_fl_lns)
        print("Event list: ", event_list)
        for eventnum in range(len(event_list)):
            print('==========================================')
            print('FSM state before event: ', fsm_states[dowhile_mngr.current_state])
            print('FSM cur open brace before event: ', dowhile_mngr.cur_nstd_opn_brace_cntr)
            print('Event: ', event_list[eventnum])
            print('File line corresponding to event: ', final_fl_lns[eventnum])
            dowhile_mngr.update_fsm_state(event_list[eventnum])
            print('FSM cur open brace after event: ', dowhile_mngr.cur_nstd_opn_brace_cntr)
            print('FSM state after event: ', fsm_states[dowhile_mngr.current_state])
            print('==========================================')
            if(dowhile_mngr.current_state == find_key_from_value_in_dict(fsm_states, "error, exit,")):
                break



# Main script begins #
if(__name__ == "__main__"):
    start_time = time.time()
    flist = ['test_branch_loop_operations_combined.c']
    do_while_loop_fsm_tester(flist)
    print("Program runtime:")
    print(f"--- {time.time() - start_time:.6f} seconds ---")