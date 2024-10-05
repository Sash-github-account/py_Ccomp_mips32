# -*- coding: utf-8 -*-
"""
Created on Thu Jul 25 19:21:41 2024

@author: nsash

Summary: Contains the class to convert intermediate dictionary created by ParserNOperationSeqr object into a sequencee of assembly instructions 

Version 2:
    -> Added pseudo-method for multiplication operation

"""
import re
from py_Ccomp_mips32_release_version import ParserNOperationSeqr as PnOseqr

class IR2AssmblyConvrtr:
    """
    This class converts an intermediate representation (IR) dictionary created by 
    the ParserNOperationSeqr object into a sequence of MIPS32 assembly instructions.
    """
    
    opcd_instrtyp_map = {0:'R', 35:'L', 43:'S', 4:'B', 2:'J'}
    
    
    def __init__(self, base_size):
        """Initializes the IR2AssmblyConvrtr class, setting up the base address, unused registers,
        and other internal state variables for generating assembly instructions.
       
        Parameters:
           base_size (int): The size of the base data section (used for address mapping).
        """       
        self.data_section_base_address = (base_size)*4
        self.used_address_counter = 0
        self.assembly_instruction_list = []
        self.unused_register_list = [
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
        self.used_register_stack = []
        self.variable_address_map = {str(base_size*4):self.data_section_base_address, '0':(base_size*4+4), '1':(base_size*4+8)}
        self.data_section_base_address = (self.data_section_base_address+3)*4
        self.current_assembly_address = 0
        self.data_section_base_address_register = ''


 
    def find_operator(self, opr_str):
        """
        Finds the operator in the intermediate representation string.

        Parameters:
            opr_str (str): The string containing the operation.
        
        Returns:
            str: The operator found in the string, or None if no operator is found.
        """
        for op in PnOseqr.operator_lst_precedence_h2l:
            if op in opr_str:
                return op
        return None



    def init_system_setup(self):
        """
        Initializes the system by setting up the data base address register and
        adding the first 'lw' instruction to load the base address into a register.
        """
        self.data_section_base_address_register = self.get_unused_reg()
        # lw self.data_section_base_address_register, self.data_section_base_address('r0')
        init_lw_instr_str = 'lw ' +  '$' + self.data_section_base_address_register + ' ' + str(self.data_section_base_address) +'($r0)'
        self.update_assem_instr_lst([init_lw_instr_str])
        pass



    def get_unused_reg(self):
        """
        Retrieves an unused register from the available register list.
        
        Returns:
            str: The name of the unused register.
        """
        reg = self.unused_register_list.pop()
        self.used_register_stack.append(reg)
        return reg



    def construct_st_instr(self, rt, target_var):
        """
        Constructs a 'store word' (sw) instruction to store the value from a register.
        
        Parameters:
            rt (str): The register that holds the value to store.
            target_var (str): The target variable (memory address) where the value will be stored.
        
        Returns:
            tuple: The register and the store instruction string.
        """
        rs = self.data_section_base_address_register
        addr_offst = self.variable_address_map[target_var]
        st_instr_str = 'sw' + ' $' + rt + ' ' + str(addr_offst) + '(' + " $" + rs + ')'
        return rt, st_instr_str        


    def construct_ld_instr(self, var):
        """
        Constructs a 'load word' (lw) instruction to load a value from memory into a register.
        
        Parameters:
            var (str): The variable (memory address) to load from.
        
        Returns:
            str: The load word instruction string.
        """
        rs = self.data_section_base_address_register
        rt = self.get_unused_reg()
        addr_offst = self.variable_address_map[var]
        ld_instr_str = 'lw' + ' $' + rt + ' ' + str(addr_offst) + '(' + " $" + rs + ')'
        return rt, ld_instr_str
        
    
    def get_operation_assem_token_for_R_instr(self, opr):
        """
        Maps an operator to its corresponding R-type instruction token.
        
        Parameters:
            opr (str): The operator (e.g., '+', '-', '&').
        
        Returns:
            str: The corresponding assembly instruction (e.g., 'add', 'sub', 'AND').
        """
        if(opr == '+'):
            opr_str_tkn = 'add'
        elif(opr == '-'):
            opr_str_tkn = 'sub'
        elif(opr == '&'):
            opr_str_tkn = 'AND'
        elif(opr == '|'):
            opr_str_tkn = 'OR'
        elif(opr == '<'):
            opr_str_tkn = 'slt'
        else:
            print('ASSEM ERROR')
        return opr_str_tkn



    def construct_R_type_instruction_seq(self, rs, rt, opr, shamt, rd_in = '', override_dest = 0):
        """
        Constructs an R-type assembly instruction for arithmetic or logical operations.
        
        Parameters:
            rs (str): The source register 1.
            rt (str): The source register 2.
            opr (str): The operation to perform ('+', '-', '<', etc.).
            shamt (int): The shift amount (default 0).
            rd_in (str): The destination register (optional).
            override_dest (bool): If True, use rd_in as the destination register.
        
        Returns:
            tuple: The destination register and the R-type instruction string.
        """
        if(override_dest):
            rd = rd_in
        else:
            rd = self.get_unused_reg()
        opr_str = self.get_operation_assem_token_for_R_instr(opr)
        R_instr_str = opr_str + ' $' + rd + ' $' + rs + ' $' + rt
        return rd, R_instr_str


    def construct_br_eq_instruction(self, rs, rt, br_offset):
        """
        Constructs a 'branch on equal' (beq) instruction.
        
        Parameters:
            rs (str): The first register to compare.
            rt (str): The second register to compare.
            br_offset (int): The offset for the branch.
        
        Returns:
            str: The branch instruction string.
        """
        if(br_offset > 32767):
            br_offset_in = 32767
        elif(br_offset < -32768):
            br_offset_in = -32768
        else:
            br_offset_in = br_offset
        br_instr_str = 'beq ' + '$' + rs + ' $' + rt + ' ' + str(br_offset_in)
        return br_instr_str


    def construct_j_type_instruction(self, address):
        """
        Constructs a jump instruction.
        
        Parameters:
            address (int): The target jump address.
        
        Returns:
            str: The jump instruction string.
        """
        j_instr_str = 'jmp ' + str(address)
        return j_instr_str


    def return_register(self, reglist):
        """
        Returns registers to the unused register list after they are no longer needed.
        
        Parameters:
            reglist (list): The list of registers to return to the unused pool.
        """
        for item in reglist:
            reg = self.used_register_stack.pop()
            self.unused_register_list.append(reg)
        pass
        
   
    def update_assem_instr_lst(self, assem_instr_str_lst):
        """
        Updates the internal assembly instruction list with a list of new instructions.
        
        Parameters:
            assem_instr_str_lst (list): A list of new assembly instruction strings.
        """
        for asm_instr in assem_instr_str_lst:
            self.assembly_instruction_list.append(asm_instr)
            self.current_assembly_address += 1 
        pass
 
    
    def handle_new_constants(self, varlst):
        """
        Handles new constants by adding them to the variable address map.
        
        Parameters:
            varlst (list): A list of variable or constant names to check.
        """
        for item in varlst:
            if(re.search('^[0-9]+$', item)):
                if item not in self.variable_address_map.keys():
                    self.variable_address_map[item] = self.used_address_counter
                    self.used_address_counter += 4
        pass
    
    
  
    def construct_basic_32bmips_operation_instr_seq(self, target_var, opnd_var1, opnd_var2, opr, shamt = 0):
        """
        Constructs a basic MIPS32 instruction sequence for arithmetic or logical operations
        (such as addition, subtraction, etc.) between two operands.
        
        Parameters:
            target_var (str): The destination variable where the result will be stored.
            opnd_var1 (str): The first operand (source register or constant).
            opnd_var2 (str): The second operand (source register or constant).
            opr (str): The operation to be performed (e.g., '+', '-', '&').
            shamt (int): Shift amount, default is 0.
        
        Returns:
            None: The method updates the assembly instruction list internally.
        """
        rs, lw_inst1 = self.construct_ld_instr(opnd_var1)
        rt, lw_inst2 = self.construct_ld_instr(opnd_var2)
        rd, arith_inst_str = self.construct_R_type_instruction_seq(rs, rt, opr, shamt)
        rt, st_instr_str = self.construct_st_instr(rt, target_var)
        bsc_m32b_op_instr_seq = [lw_inst1, lw_inst2, arith_inst_str, st_instr_str]
        self.update_assem_instr_lst(bsc_m32b_op_instr_seq)
        self.return_register([rs, rt, rd])
        pass
        
        
    def process_multiplication_operation(self, target_var, opnd_var1, opnd_var2):
        """
        Constructs a sequence of MIPS assembly instructions to perform multiplication
        of two operands, followed by storing the result in the target variable.
        
        Parameters:
            target_var (str): The destination variable where the result will be stored.
            opnd_var1 (str): The first operand (source register or constant).
            opnd_var2 (str): The second operand (source register or constant).
        
        Returns:
            None: The method updates the assembly instruction list internally.
        """
        # load const 0 in a reg0 #
        reg0, lw_inst1 = self.construct_ld_instr('0')
        # load opnd_var1 val into another reg1 #
        reg1, lw_inst2 = self.construct_ld_instr(opnd_var1)        
        # load opnd_var2 into 3rd reg2 #
        reg2, lw_inst3 = self.construct_ld_instr(opnd_var2)  
        # load const 1 in reg4 #
        reg4, lw_inst4 = self.construct_ld_instr('1') 
        # load const 0 in reg5 ie., reg5 = 'r0' #
        reg5, lw_inst5 = self.construct_ld_instr('0') 
        # add reg0 + reg1 into reg0 #
        reg0, add_inst = self.construct_R_type_instruction_seq(reg0, reg1, '+', 0, rd_in=reg0, override_dest=1)
        # sub reg2 - reg4 into reg2
        reg2, sub_inst = self.construct_R_type_instruction_seq(reg2, reg4, '-', 0, rd_in=reg2, override_dest=1)
        # set reg6 if less than: reg5 < reg2
        reg6, slt_inst = self.construct_R_type_instruction_seq(reg5, reg2, '<', 0)
        # branch on equal: reg6 == reg4 : -(4*3=12) #
        br_instr = self.construct_br_eq_instruction(reg6, reg4,  -(4*3))
        # sw reg0 to target_var address #
        reg0, st_instr_str = self.construct_st_instr(reg0, target_var)
        # append instr strs #
        mul_instr_seq = [lw_inst1, lw_inst2, lw_inst3, lw_inst4, lw_inst5, add_inst, sub_inst, slt_inst, br_instr, st_instr_str]
        self.update_assem_instr_lst(mul_instr_seq)
        # return used regs #
        ret_reg_lst = [reg0, reg1, reg2, reg4, reg5, reg6]
        self.return_register(ret_reg_lst)
        pass
        
 
    def process_divisionNmodulo_operation(self, target_var, opnd_var1, opnd_var2, opr):
        """
         Constructs a sequence of MIPS assembly instructions to perform division or 
         modulo operations between two operands, followed by storing the result 
         in the target variable.
        
         Parameters:
             target_var (str): The destination variable where the result will be stored.
             opnd_var1 (str): The first operand (source register or constant).
             opnd_var2 (str): The second operand (source register or constant).
             opr (str): The operation ('/' for division, '%' for modulo).
        
         Returns:
             None: The method updates the assembly instruction list internally.
         """
        # load const 0 in a reg0 #
        reg0, lw_inst1 = self.construct_ld_instr('0')
        # load opnd_var1 val into another reg1 #
        reg1, lw_inst2 = self.construct_ld_instr(opnd_var1) 
        # load opnd_var2 into 3rd reg2 #
        reg2, lw_inst3 = self.construct_ld_instr(opnd_var2) 
        # load const 1 in reg4 #
        reg4, lw_inst4 = self.construct_ld_instr('1')
        # load const 0 in reg5 ie., reg5 = 'r0' #
        reg5, lw_inst5 = self.construct_ld_instr('0') 
        # set reg6 if less than: reg1 < reg2 #
        reg6, slt_inst = self.construct_R_type_instruction_seq(reg1, reg2, '<', 0)
        # branch on equal: reg6 == reg4 : (4*4) #
        br_instr = self.construct_br_eq_instruction(reg6, reg4,  (4*4))
        # sub reg1 - reg2 into reg1 #
        reg1, sub_inst = self.construct_R_type_instruction_seq(reg1, reg2, '-', 0, rd_in=reg1, override_dest=1)
        # add reg0 + reg4 into reg0 #
        reg0, add_inst = self.construct_R_type_instruction_seq(reg0, reg4, '+', 0, rd_in=reg0, override_dest=1)
        # jump to -4*4 #
        jmp_inst = self.construct_j_type_instruction(-(4*4))
        # sw reg0 if division or sw reg1 if modulo to target_var address #
        if(opr == '/'):
            reg0, st_instr_str = self.construct_st_instr(reg0, target_var)
        else:
            reg1, st_instr_str = self.construct_st_instr(reg1, target_var)
        # append instr strs #
        div_mod_instr_seq = [lw_inst1, lw_inst2, lw_inst3, lw_inst4, lw_inst5, slt_inst, br_instr, sub_inst, add_inst, jmp_inst, st_instr_str]
        self.update_assem_instr_lst(div_mod_instr_seq)
        # return used regs #
        ret_reg_lst = [reg0, reg1, reg2, reg4, reg5, reg6]
        self.return_register(ret_reg_lst)
        pass
 
    
    def process_grteq_lsteq_ops(self, target_var, opnd_var1, opnd_var2, opr):
        """
        Constructs MIPS assembly instructions for greater than or equal (>=) or 
        less than or equal (<=) comparisons between two operands, followed by 
        storing the result in the target variable.
        
        Parameters:
            target_var (str): The destination variable where the result will be stored.
            opnd_var1 (str): The first operand (source register or constant).
            opnd_var2 (str): The second operand (source register or constant).
            opr (str): The comparison operator ('>=' or '<=').
        
        Returns:
            None: The method updates the assembly instruction list internally.
        """
        if(opr == '>='):
            op1 = opnd_var2
            op2 = opnd_var1
        else:
            op1 = opnd_var1
            op2 = opnd_var2
        # load op1 in reg1 #
        reg1, lw_inst1 = self.construct_ld_instr(op1) 
        # load op2 in reg2 #
        reg2, lw_inst2 = self.construct_ld_instr(op2)
        # load const 1 into reg3 #
        reg3, lw_inst3 = self.construct_ld_instr('1')
        # branch if op1 == op2 to (4*2) #
        br_instr = self.construct_br_eq_instruction(reg1, reg2,  (4*2))
        # set reg3 if op1 < op2 #
        reg3, slt_inst = self.construct_R_type_instruction_seq(reg1, reg2, '<', 0, rd_in=reg3, override_dest=1)
        # store reg3 to target_var #
        reg3, st_instr_str = self.construct_st_instr(reg3, target_var)
        # append instr strs #
        grteq_lsteq_instr_seq = [lw_inst1, lw_inst2, lw_inst3, br_instr, slt_inst, st_instr_str]
        self.update_assem_instr_lst(grteq_lsteq_instr_seq)
        # return used regs #
        ret_reg_lst = [reg3, reg1, reg2]
        self.return_register(ret_reg_lst)
        pass
    


    def process_cond_AND_OR_ops(self, target_var, opnd_var1, opnd_var2, opr):
        """
        Constructs MIPS assembly instructions for logical AND (&&) and OR (||) 
        operations between two operands, followed by storing the result in the target variable.
        
        Parameters:
            target_var (str): The destination variable where the result will be stored.
            opnd_var1 (str): The first operand (source register or constant).
            opnd_var2 (str): The second operand (source register or constant).
            opr (str): The logical operator ('&&' for AND, '||' for OR).
        
        Returns:
            None: The method updates the assembly instruction list internally.
        """
        # load const 0 into reg0 = r0 #
        reg0, lw_inst0 = self.construct_ld_instr('0')
        # load const 1 into reg1 #
        reg1, lw_inst1 = self.construct_ld_instr('1')
        # load op1 into reg2 #
        reg2, lw_inst2 = self.construct_ld_instr(opnd_var1)
        # load op2 into reg3 #
        reg3, lw_inst3 = self.construct_ld_instr(opnd_var2)
        # set reg4 if reg0 < reg2
        reg4, slt_inst1 = self.construct_R_type_instruction_seq(reg0, reg2, '<', 0)
        # set reg5 if reg0 < reg3
        reg5, slt_inst2 = self.construct_R_type_instruction_seq(reg0, reg3, '<', 0)
        # R type AND/OR on reg4 &/| reg5 in reg6 based on opr
        reg6, arith_inst_str = self.construct_R_type_instruction_seq(reg4, reg5, opr, 0)
        # store reg6 into target_var #
        reg6, st_instr_str = self.construct_st_instr(reg6, target_var)
        # append instr strs #
        cond_AND_OR_instr_seq = [lw_inst0, lw_inst1, lw_inst2, lw_inst3, slt_inst1, slt_inst2, st_instr_str]
        self.update_assem_instr_lst(cond_AND_OR_instr_seq)
        # return used regs #
        ret_reg_lst = [reg0, reg3, reg1, reg2, reg4, reg5, reg6]
        self.return_register(ret_reg_lst)
        pass


    def process_cond_equ_noteq_ops(self, target_var, opnd_var1, opnd_var2, opr):
        """
        Constructs MIPS assembly instructions for equality (==) and inequality (!=) 
        comparisons between two operands, followed by storing the result in the target variable.
        
        Parameters:
            target_var (str): The destination variable where the result will be stored.
            opnd_var1 (str): The first operand (source register or constant).
            opnd_var2 (str): The second operand (source register or constant).
            opr (str): The comparison operator ('==' for equality, '!=' for inequality).
        
        Returns:
            None: The method updates the assembly instruction list internally.
        """
        # load op1 into reg2 #
        reg2, lw_inst0 = self.construct_ld_instr(opnd_var1)
        # load op2 into reg3 #
        reg3, lw_inst1 = self.construct_ld_instr(opnd_var2)
        # load const 1 into reg1 (if opr = '==') --or-- load const 0 into reg1 (if opr = '!=') #
        if opr == '!=':
            reg1, lw_inst2 = self.construct_ld_instr('0')
        else:
            reg1, lw_inst2 = self.construct_ld_instr('1')
        # branch if reg2 == reg3 to 4*2 #
        br_instr = self.construct_br_eq_instruction(reg2, reg3,  (4*2))
        # load const 0 into reg1 (if opr = '==') --or-- load const 1 into reg1 (if opr = '!=') #
        if opr == '!=':
            reg1, lw_inst3 = self.construct_ld_instr('0')
        else:
            reg1, lw_inst3 = self.construct_ld_instr('1')
        # store reg1 to addr(target_var) #
        reg1 = st_instr_str = self.construct_st_instr(reg1, target_var)
        # append instr strs #
        cond_equ_noteq_instr_seq = [lw_inst0, lw_inst1, lw_inst2, br_instr, lw_inst3, st_instr_str]
        self.update_assem_instr_lst(cond_equ_noteq_instr_seq)
        # return used regs #
        ret_reg_lst = [reg3, reg1, reg2]
        self.return_register(ret_reg_lst)
        pass
    
    
    def process_assignment_translation(self, event_seq_dict, ir_entry_num):
        """
        Processes an event sequence dictionary entry, decodes operation and operands, kicks of corresponding assembly 
        code.
        
        Parameters:
            event_seq_dict (dict): The event sequence dictionary mapping events to operations.
            ir_entry_num (int): IR dict entry number being processed
            
        Returns:
            None: The method updates the assembly instruction list internally.
        """
        i = ir_entry_num
        opr_fnd = self.find_operator(event_seq_dict[i][1])
        opnd_lst = re.findall("(" + PnOseqr.re_get_var_name + ')', event_seq_dict[i][1])
        print(opnd_lst)
        if(len(opnd_lst) > 1):
            self.handle_new_constants(opnd_lst)
            isany_instr_op = opr_fnd == '+' or opr_fnd == '-' or opr_fnd == '&' or opr_fnd == '|' or opr_fnd == '<'
            if(isany_instr_op):  
                self.construct_basic_32bmips_operation_instr_seq( event_seq_dict[i][0], opnd_lst[0], opnd_lst[1], opr_fnd, 0)
            elif(opr_fnd == '>'):
                opr_fnd = '<'
                self.construct_basic_32bmips_operation_instr_seq( event_seq_dict[i][0], opnd_lst[1], opnd_lst[0], opr_fnd, 0)
            elif(opr_fnd == '*'):
                self.process_multiplication_operation(event_seq_dict[i][0], opnd_lst[0], opnd_lst[1])
            elif(opr_fnd == '/' or opr_fnd == '%'):
                self.process_divisionNmodulo_operation(event_seq_dict[i][0], opnd_lst[0], opnd_lst[1], opr_fnd)
            elif(opr_fnd == '>=' or opr_fnd == '<='):
                self.process_grteq_lsteq_ops(event_seq_dict[i][0], opnd_lst[0], opnd_lst[1], opr_fnd)
            elif(opr_fnd == '&&' or opr_fnd == '||'):
                self.process_cond_AND_OR_ops(event_seq_dict[i][0], opnd_lst[0], opnd_lst[1], opr_fnd)
            elif(opr_fnd == '==' or opr_fnd == '!='):
                self.process_cond_equ_noteq_ops(event_seq_dict[i][0], opnd_lst[0], opnd_lst[1], opr_fnd)
            else:
                print("ERROR: Assembler Failed: " + str(i))
        else:
            if(len(opnd_lst) == 1):
                rt = self.get_unused_reg()
                rt, st_instr_str = self.construct_st_instr(rt, event_seq_dict[i][0])
                self.update_assem_instr_lst([st_instr_str])
                self.return_register([rt])
            elif(len(opnd_lst) == 0):
                if(re.search("[0-9]+", event_seq_dict[i][1])):
                    self.handle_new_constants(opnd_lst)
                    rt = self.get_unused_reg()
                    rt, st_instr_str = self.construct_st_instr(rt, event_seq_dict[i][0])
                    self.update_assem_instr_lst([st_instr_str])
                    self.return_register([rt])
                else:
                    print("ERROR: Assembler Failed: " + str(i))
            else:
                print("ERROR: Assembler Failed: " + str(i))
    
    
        
    def process_event_seq(self, event_seq_dict):
        """
        Processes an event sequence dictionary to generate corresponding MIPS 
        assembly instructions for each event.
        
        Parameters:
            event_seq_dict (dict): The event sequence dictionary mapping events to operations.
        
        Returns:
            None: The method updates the assembly instruction list internally.
        """
        self.init_system_setup()
        for i in range(1, len(list(event_seq_dict.values())), 1):
            search_PEDMAS_variable = re.search("PEDMAStmpvar[0-9]+", event_seq_dict[i][0])
            if event_seq_dict[i][0] == '@DECLARATION' or search_PEDMAS_variable:
                self.used_address_counter += 4
                if(search_PEDMAS_variable):
                    self.variable_address_map[search_PEDMAS_variable.group()] = self.used_address_counter
                    self.process_assignment_translation(event_seq_dict, i)
                else:
                    self.variable_address_map[event_seq_dict[i][1]] = self.used_address_counter
            elif(re.search(PnOseqr.re_get_var_name, event_seq_dict[i][0])):
                self.process_assignment_translation(event_seq_dict, i)
    
    
    
test_dict = {1: ('@DECLARATION', 'a'),
2: ('a', '5'),
3: ('@DECLARATION', 'b'),
4: ('b', '10'),
5: ('@DECLARATION', 'c'),
6: ('c', '20'),
7: ('@DECLARATION', 'd'),
8: ('d', '0'),
9: ('@DECLARATION', 'e'),
10: ('e', '0'),
11: ('PEDMAStmpvar0', 'a+b'),
12: ('d', 'PEDMAStmpvar0'),
13: ('PEDMAStmpvar1', 'c-b'),
14: ('e', 'PEDMAStmpvar1'),
15: ('PEDMAStmpvar2', 'd*e'),
16: ('d', 'PEDMAStmpvar2'),
17: ('PEDMAStmpvar3', 'd/a'),
18: ('e', 'PEDMAStmpvar3'),
19: ('PEDMAStmpvar4', 'd%c'),
20: ('d', 'PEDMAStmpvar4'),
21: ('PEDMAStmpvar5', 'e&a'),
22: ('d', 'PEDMAStmpvar5'),
23: ('PEDMAStmpvar6', 'd|b'),
24: ('e', 'PEDMAStmpvar6'),
25: ('PEDMAStmpvar7', 'a^d'),
26: ('b', 'PEDMAStmpvar7'),
27: ('PEDMAStmpvar8', 'a<<2'),
28: ('e', 'PEDMAStmpvar8'),
29: ('PEDMAStmpvar9', 'b>>1'),
30: ('d', 'PEDMAStmpvar9')}
                    
asmconvrtr = IR2AssmblyConvrtr(95)
asmconvrtr.process_event_seq(test_dict)
for item in asmconvrtr.assembly_instruction_list:
    print(item)
print(asmconvrtr.used_register_stack)