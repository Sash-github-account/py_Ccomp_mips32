# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 19:21:41 2024

@author: nsash

Summary: Contains the class to convert intermediate dictionary created by ParserNOperationSeqr object into a sequencee of assembly instructions 

Version 1:
    -> Added initial code for IR2AssmblyConvrtr class
    -> method to process parserNopernseqr's parse_event_dict added: initial version W.I.P

"""
import re
from py_Ccomp_mips32_release_version import ParserNOperationSeqr as PnOseqr

class IR2AssmblyConvrtr:
    #==== INFO NEEDED ======#
    # 1. Instruction types templates #
    # 2. Register set information #
    # 3. How to map ddress space #
    opcd_instrtyp_map = {0:'R', 35:'L', 43:'S', 4:'B', 2:'J'}
    
    
    def __init__(self, base_size):
        self.data_sec_BA = base_size*4
        self.used_addr_cntr = 0
        self.assembly_instr_lst = []
        self.unused_reg_lst = [
                            "r31",
                            "r30",
                            "r29",
                            "r28",
                            "r27",
                            "r26",
                            "r25",
                            "r24",
                            "r23",
                            "r22",
                            "r21",
                            "r20",
                            "r19",
                            "r18",
                            "r17",
                            "r16",
                            "r15",
                            "r14",
                            "r13",
                            "r12",
                            "r11",
                            "r10",
                            "r9",
                            "r8",
                            "r7",
                            "r6",
                            "r5",
                            "r4",
                            "r3",
                            "r2",
                            "r1"
                            ]
        self.used_regs_stk = []
        self.var_addr_map = {}
        self.data_base_addr_reg = ''


 
    def find_operator(self, opr_str):
        for op in PnOseqr.operator_lst_precedence_h2l:
            if op in opr_str:
                return op
        return None


    def init_system_setup(self):
        self.data_base_addr_reg = self.get_unused_reg()
        


    def get_unused_reg(self):
        reg = self.unused_reg_lst.pop()
        self.used_regs_stk.append(reg)
        return reg

    def construct_st_instr(self, rt, target_var):
        rs = self.data_base_addr_reg
        addr_offst = self.var_addr_map[target_var]
        st_instr_str = 'sw' + ' $' + rt + ' ' + str(addr_offst) + '(' + " $" + rs + ')'
        return rt, st_instr_str        


    def construct_ld_instr(self, var):
        rs = self.data_base_addr_reg
        rt = self.get_unused_reg()
        addr_offst = self.var_addr_map[var]
        ld_instr_str = 'lw' + ' $' + rt + ' ' + str(addr_offst) + '(' + " $" + rs + ')'
        return ld_instr_str
        
    
    def get_operation_assem_token_for_R_instr(self, opr):
        if(opr == '+'):
            opr_str_tkn = 'add'
        elif(opr == '-'):
            opr_str_tkn = 'sub'
        elif(opr == '&'):
            opr_str_tkn = 'AND'
        elif(opr == '|'):
            opr_str_tkn = 'OR'
        elif(opr == '<<'):
            opr_str_tkn = 'slt'
        else:
            print('ASSEM ERROR')
        return opr_str_tkn

    def construct_R_type_instruction_seq(self, rs, rt, opr, shamt):
        rd = self.get_unused_reg()
        opr_str = self.get_operation_assem_token_for_R_instr(opr)
        R_instr_str = opr_str + ' $' + rd + ' $' + rs + ' $' + rt
        return rd, R_instr_str
        
        
    def construct_arith_operation_instr_seq(self, target_var, opnd_var1, opnd_var2, opr, shamt = 0):
        rs, lw_inst1 = self.construct_ld_instr(opnd_var1)
        rt, lw_inst2 = self.construct_ld_instr(opnd_var2)
        rd, arith_inst_str = self.construct_R_type_instruction_seq(rs, rt, opr, shamt)
        st_instr_str = self.construct_st_instr(rt, target_var)
        self.assembly_instr_lst.append(lw_inst1)
        self.assembly_instr_lst.append(lw_inst2)
        self.assembly_instr_lst.append(arith_inst_str)
        self.assembly_instr_lst.append(st_instr_str)
        
        
    def process_event_seq(self, event_seq_dict):
        self.init_system_setup()
        for i in range(len(list(event_seq_dict.values()))):
            if event_seq_dict[i][0] == 'DECLARATION':
                self.var_addr_map[event_seq_dict[i][1]] = self.used_addr_cntr
                self.used_addr_cntr += 4
            elif(re.search(PnOseqr.re_get_var_name, event_seq_dict[i][0])):
                opr_fnd = self.find_operator(event_seq_dict[i][1])
                if(opr_fnd):
                    opnd_lst = re.findall("(" + PnOseqr.re_get_var_name + ')', event_seq_dict[i][1])
                    