# run.py

from bin_convert import HalfPrecision, Length
from storage import register, memory, variable
from addressing import AddressingMode
from compiler import Instruction

class Except:
    def __init__(self, msg, occur=True):
        self.message = msg
        self.occur = occur
        self.ret = None

    def dispMSG(self):
        print(self.message)

    def isOccur(self):
        return self.occur

    def setReturn(self, value):
        self.ret = value

    def getReturn(self):
        return self.ret


class Program:
    def __init__(self, program):
        # Automatically compile the program to storage on startup
        Instruction.encodeProgram(program)

    @staticmethod
    def exception(name, value):
        """
        Produces custom exception values depending on input arguments.
        """
        if name == 'DivByZero':
            op1, op2 = value
            exc = Except("Exception encountered: Division by zero.")
            if op1 == 0 and op2 == 0:
                exc.setReturn("Infinity")
            elif op2 == 0:
                exc.setReturn("undefined")
            return exc
        return None

    def write(self, dest, src, movecode):
        """
        Coordinates standard data movements and specialized execution side-effects.
        """
        if movecode == 1:    # CALL execution sequence
            pc_val = register.load(variable.data["PC"])
            register.store(variable.data["CR"], pc_val)
        elif movecode == 2:  # RET execution sequence
            cr_val = register.load(variable.data["CR"])
            register.store(variable.data["PC"], cr_val)
        elif movecode == 3:  # SCAN operation
            msg_idx = int(src)
            msg_text = variable.data["MSG"].get(msg_idx, "")
            user_input = input(msg_text)
            try:
                src_val = float(user_input)
                if src_val.is_integer():
                    src_val = int(src_val)
            except ValueError:
                src_val = user_input
            src = src_val

        # Execute default write-back (src value to dest storage address)
        if isinstance(dest, tuple):
            addr, storage_obj = dest
            # Safely force key values to integers to guarantee correct index matches
            addr = int(addr) if type(addr) in [int, float] else addr
            storage_obj.store(addr, src)

    def execute(self, op1_val, op2_val, opcode):
        """
        Calculates arithmetic results or evaluates condition parameters for jumps.
        """
        E = opcode[0]
        W = opcode[1]
        Cat = opcode[2:5]

        if W == '1':
            if Cat == "000":    # MOD
                return op1_val % op2_val
            elif Cat == "001":  # ADD
                return op1_val + op2_val
            elif Cat == "010":  # SUB
                return op1_val - op2_val
            elif Cat == "011":  # MUL
                return op1_val * op2_val
            elif Cat == "100":  # DIV
                if op2_val == 0:
                    exc = self.exception('DivByZero', (op1_val, op2_val))
                    exc.dispMSG()
                    return exc.getReturn()
                return op1_val / op2_val
        else:
            jr_val = register.load(variable.data["JR"])
            condition = False
            if Cat == "000":    # JEQ
                condition = (jr_val == 0)
            elif Cat == "001":  # JNE
                condition = (jr_val != 0)
            elif Cat == "010":  # JLT
                condition = (jr_val < 0)
            elif Cat == "011":  # JLE
                condition = (jr_val <= 0)
            elif Cat == "100":  # JGT
                condition = (jr_val > 0)
            elif Cat == "101":  # JGE
                condition = (jr_val >= 0)
            elif Cat == "110":  # JMP
                condition = True
            
            if condition:
                # Update program counter to jump target address
                register.store(variable.data["PC"], op1_val)
            return None

    def getOp(self, inscode, is_rb=False):
        """
        Decodes operand addresses using appropriate register/memory modes.
        """
        if len(inscode) == 15:
            return HalfPrecision.hpbin2dec(inscode + "0")

        mode = inscode[0:3]
        addr = inscode[3:10]

        if is_rb:
            # Based Mode handling
            if mode == "000":
                leftmost = int(addr[0])
                val_part = int(addr[1:], 2)
                displace = register.load(val_part)
                return AddressingMode.based(displace)
            elif mode == "001":
                leftmost = int(addr[0])
                val_part = int(addr[1:], 2)
                displace = memory.load(val_part)
                return AddressingMode.based(displace)
            elif mode == "010":
                val_part = int(addr[1:], 2)
                return AddressingMode.based(val_part)
            elif mode == "011":
                val_part = int(addr[1:], 2)
                return AddressingMode.based(-val_part)
            # Relative Mode handling
            elif mode == "100":
                leftmost = int(addr[0])
                val_part = int(addr[1:], 2)
                displace = register.load(val_part)
                return AddressingMode.relative(displace)
            elif mode == "101":
                leftmost = int(addr[0])
                val_part = int(addr[1:], 2)
                displace = memory.load(val_part)
                return AddressingMode.relative(displace)
            elif mode == "110":
                val_part = int(addr[1:], 2)
                return AddressingMode.relative(val_part)
            elif mode == "111":
                val_part = int(addr[1:], 2)
                return AddressingMode.relative(-val_part)

        if mode == "000":
            eff_addr, val, stor = AddressingMode.register(addr)
            return (eff_addr, stor)
        elif mode == "001":
            eff_addr, val = AddressingMode.register_indirect(addr)
            return (eff_addr, memory)
        elif mode == "010":
            eff_addr, val = AddressingMode.direct(addr)
            return (eff_addr, memory)
        elif mode == "011":
            eff_addr, val = AddressingMode.indirect(addr)
            return (eff_addr, memory)
        elif mode == "100":
            leftmost = int(addr[0])
            val_part = int(addr[1:], 2)
            if leftmost == 0:
                displace = register.load(val_part)
            else:
                displace = memory.load(val_part)
            eff_addr, val = AddressingMode.indexed(displace)
            return (eff_addr, memory)
        elif mode == "101":
            leftmost = int(addr[0])
            val_part = int(addr[1:], 2)
            displace = val_part if leftmost == 0 else -val_part
            eff_addr, val = AddressingMode.indexed(displace)
            return (eff_addr, memory)
        elif mode == "110":
            eff_addr, val = AddressingMode.autoinc(addr)
            return (eff_addr, memory)
        elif mode == "111":
            eff_addr, val = AddressingMode.autodec(addr)
            return (eff_addr, memory)

    def run(self):
        """
        Executes the emulator's core fetch-decode-execute loop.
        """
        monadic_niladic = []

        while True:
            ir_val = int(register.load(variable.data["IR"]))
            inst_code = memory.load(ir_val)

            # Terminate if instruction is not in 32-bit layout or is all-zeros (EOP/FUNC)
            if type(inst_code) != type(str()) or len(inst_code) != 32 or inst_code == "0".zfill(32):
                break

            opcode = inst_code[0:5]
            ib = inst_code[5]
            op1_code = inst_code[6:16]
            rb = inst_code[16]

            # Decode Op1 parameters
            op1_res = self.getOp(op1_code)
            if isinstance(op1_res, tuple):
                op1_val = op1_res[1].load(op1_res[0])
            else:
                op1_val = op1_res

            # Detect instruction format parameters to check for second operand
            has_op2 = True
            E = opcode[0]
            W = opcode[1]
            Cat = opcode[2:5]
            if E == "1" and W == "0":  # Jump Commands
                has_op2 = False
            elif E == "0" and W == "1" and Cat in ["001", "010"]:  # CALL / RET commands
                has_op2 = False

            op2_res = None
            op2_val = None
            if has_op2:
                if ib == "1":
                    op2_code = inst_code[17:32]
                    op2_res = self.getOp(op2_code)
                else:
                    op2_code = inst_code[17:27]
                    op2_res = self.getOp(op2_code, is_rb=(rb == "1"))

                if isinstance(op2_res, tuple):
                    op2_val = op2_res[1].load(op2_res[0])
                else:
                    op2_val = op2_res

            # Execute cycle
            result = None
            if E == "1":
                result = self.execute(op1_val, op2_val, opcode)

            # Write-back cycle
            if W == "1":
                if E == "1":
                    self.write(op1_res, result, 0)
                else:
                    if Cat == "000":    # MOV
                        self.write(op1_res, op2_val, 0)
                    elif Cat == "001":  # CALL
                        dest = (variable.data["PC"], register)
                        self.write(dest, op1_val, 1)
                    elif Cat == "010":  # RET
                        dest = (variable.data["ACC"], register)
                        self.write(dest, op1_val, 2)
                    elif Cat == "011":  # SCAN
                        msg_idx = op2_res[0] if isinstance(op2_res, tuple) else op2_val
                        self.write(op1_res, msg_idx, 3)

            # Output Printing
            if E == "0" and W == "0":
                if Cat == "000":        # PRNT
                    msg_idx = int(op2_res[0] if isinstance(op2_res, tuple) else op2_val)
                    msg = variable.data["MSG"].get(msg_idx, "")
                    val_str = str(int(op1_val)) if isinstance(op1_val, float) and op1_val.is_integer() else str(op1_val)
                    print(f"{val_str} {msg}" if msg else val_str)

            # Update instruction registers (PC and IR)
            pc_val = register.load(variable.data["PC"])
            register.store(variable.data["IR"], pc_val)
            register.store(variable.data["PC"], pc_val + 1)


if __name__ == "__main__":
    import sys
    # Runs the compiler and virtual runner if executed directly via terminal
    if len(sys.argv) > 1:
        prog = Program(sys.argv[1])
        prog.run()