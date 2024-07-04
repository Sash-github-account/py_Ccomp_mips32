# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 12:50:59 2024

@author: nsash

Version: 1: NF
    Base

C compiler for MIPS-NS ISA
    -> Supports only int 32b data type
    -> Supports arithmetic operations BOARDMAS priority
    -> No support for pre-processing
    -> No support for function calls, only void main()
    -> Conditionals and loops supported
    -> Comments only supported at start of line, ie., an entire line can be a comment but there can be no comments in lines where there is code
    -> Currently supports only one statement per line

References + credits:
    -> https://www.geeksforgeeks.org/variables-in-c/
    -> https://www.w3schools.com/python/python_regex.asp
    -> https://regex101.com/
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
    main_fn_entered = 0
    expecting_opn_cbrace = 0
    expecting_cls_cbrace = 0
    
    def __init__(self, svr_lvl):
        self.svr_lvl = svr_lvl
        self.mn_fn_def_ln_num = None
        self.var_dec_ln_dict = {}
        self.variable_names_lst = []
        
    def __str__(self):
        return f"(Main funtion at line: {self.mn_fn_def_ln_num})"

    def print_error_msg_ext(self, msg_strng, line, ln_num):
        print(msg_strng + str(ln_num) + ' ' + line)
        sys.exit()  

    def chk_expression_syntx_n_upd_state(self, line, ln_num, ln_is_var_dec):
        syntax_match_obj = re.search("^\s*[a-zA-Z_]+[0-9]*[a-zA-Z_]*\s*(=\s*[a-zA-z_\s\(\)\+\-\/\*\^\%0-9]*\s*)?;\s*", line)
        if(syntax_match_obj):
            var_n_pure_exp_lst = syntax_match_obj.group().strip(' ').split('=')
            if(ln_is_var_dec and self.chk_var_re_dec([var_n_pure_exp_lst[0]], line, ln_num)):
                

    def chk_var_re_dec(self, new_var_lst, line, ln_num):
        for var in new_var_lst:
            if var in self.variable_names_lst:
                self.print_error_msg_ext("ERROR: Variable re-declaration at line: ", line, ln_num)
            else:
                self.variable_names_lst += new_var_lst
                return 1

    def chk_var_declaration_syntx(self, line, ln_num):
        var_dec_ln_match_obj = re.search("^\s*(void|int)(\s*[a-zA-Z_]+[0-9]*[a-zA-Z_]*\s*(=\s*[a-zA-z_\s\(\)\+\-\/\*\^\%0-9]*\s*)?,?)*;\s*", line)
        if(var_dec_ln_match_obj):
            declr_key_word_n_semicoln_rmd = re.sub("\s*", '', re.sub('(void|int)', '', var_dec_ln_match_obj.group()).strip("\n").strip(" ").strip(";")).split(',')
            if(self.chk_var_re_dec(declr_key_word_n_semicoln_rmd, line, ln_num, 1)):
                self.var_dec_ln_dict[ln_num] = line
                print("INFO: Found variable declaration at line: " + str(ln_num)+": " + line)
                return 1
        else:
            self.print_error_msg_ext("ERROR: Syntax error at line num: ",  line, ln_num)
            
    def chk_cbrace_reqmnt_n_upd(self, line, ln_num = None, ln_is_mn_fn = 0):
        ln_splt_at_cbrace = line.split("{")
        if (len(ln_splt_at_cbrace) > 1):
            print("INFO: Found main func. open cbrace at line:" + str(ln_num))
            if(ln_is_mn_fn):
                self.expecting_opn_cbrace = 0
                self.expecting_cls_cbrace = 1
            else:
                if ((re.search("\s*", ln_splt_at_cbrace[0]))):
                    self.expecting_opn_cbrace = 0
                    self.expecting_cls_cbrace = 1
                    if(re.search("^\s*$", ln_splt_at_cbrace[1]) ):
                        pass
                    else:
                        self.chk_var_declaration_syntx(ln_splt_at_cbrace[1], ln_num)
                else:
                    self.print_error_msg_ext("ERROR: Syntax error at line num: ",  line, ln_num)
        else:
            self.expecting_opn_cbrace = 1

    def chk_cbrace_closure(self, line, ln_num):
        ln_splt_at_cbrace = line.split("}")
        if(len(ln_splt_at_cbrace) > 1):
            if(ln_splt_at_cbrace[1].strip(' ').strip('\n') != ''):
                self.print_error_msg_ext("ERROR: Scbrace closure syntax error at line: ", line, ln_num)
            else:
                if(ln_splt_at_cbrace[0] == ''):
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



#def process_file_list(fl_lst):
#    for fl in fl_lst:


def start_fl_parse(file_lns):
    prog_obj = Program_obj(default_svr_lvl)
    # Go into loop for each line #
    for line_num in range(len(file_lns)):
        line_n = line_num+1
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
        elif(prog_obj.chk_var_declaration_syntx(file_lns[line_num], line_n)):
            continue
        else:
            print("WIP, line num: " + str(line_n))
              

            
        # Check stand alone var init #
            # Check if var name in var dict #
            # upd var val in dict #
            
        # Check if arithmetic/logical operation and upd val in var dict corresponding to appriate var #
        
        # Check if branch  'if() else if() else' or 'switch() case x:'   and upd brn state vars
    
        # Check for loop syntax and upd loop state var #
    
    
    
# Main script begins #
if(__name__ == "__main__"):
    flist = get_file_list_for_compile()
    for fl in flist:
        fl_lns = get_file_lines_list(fl)
        start_fl_parse(fl_lns)
