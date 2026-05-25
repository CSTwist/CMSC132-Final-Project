from bin_convert import HalfPrecision, Length
from storage import register, memory, variable

# Complete OpCode Table: maps operation to (Execute bit, Write bit, Category Code)
operations = {
    "MOD":   ("1", "1", "000"),
    "ADD":   ("1", "1", "001"),
    "CB":    ("1", "1", "001"),
    "CF":    ("1", "1", "001"),
    "SUB":   ("1", "1", "010"),
    "CMP":   ("1", "1", "010"),
    "MUL":   ("1", "1", "011"),
    "DIV":   ("1", "1", "100"),
    "JEQ":   ("1", "0", "000"),
    "JNE":   ("1", "0", "001"),
    "JLT":   ("1", "0", "010"),
    "JLE":   ("1", "0", "011"),
    "JGT":   ("1", "0", "100"),
    "JGE":   ("1", "0", "101"),
    "JMP":   ("1", "0", "110"),
    "MOV":   ("0", "1", "000"),
    "ADDPC": ("0", "1", "000"),
    "CALL":  ("0", "1", "001"),
    "RET":   ("0", "1", "010"),
    "SCAN":  ("0", "1", "011"),
    "PRNT":  ("0", "0", "000"),
    "EOP":   ("0", "0", "001"),
    "FUNC":  ("0", "0", "001"),
}

class Instruction:
    @staticmethod
    def decodeMSG(msg):
        """
        Converts dashes, underscores, and special terms to target characters.
        """
        msg = msg.replace("minus", "-")
        msg = msg.replace("under", "_")
        msg = msg.replace("-_", "\n")
        msg = msg.replace("_", "\t")
        msg = msg.replace("-", " ")
        return msg

    @staticmethod
    def _resolveVarAddr(operand, default=0):
        try:
            val = variable.load(operand)
            return int(val)
        except KeyError:
            return default

    @staticmethod
    def encodeOp(operand):
        """
        Translates a single operand into its corresponding Addressing Mode 
        and Binary representation of the target location.
        """
        try:
            val = float(operand)
            if val.is_integer():
                val = int(val)
            return HalfPrecision.hpdec2bin(val)
        except ValueError:
            pass

        # Handle message string
        if type(operand) == type(str()) and operand.startswith("M:"):
            msg_text = Instruction.decodeMSG(operand[2:])
            mi = variable.data.get("MI", 0)
            variable.data["MSG"][mi] = msg_text
            variable.data["MI"] = mi + 1
            return "010" + Length.addZeros(mi, 7)

        operand = operand.strip()
        has_paren = False
        if operand.startswith("(") and operand.endswith(")"):
            has_paren = True
            operand = operand[1:-1].strip()

        mode_code = ""
        addr_val = 0
        leftmost_bit = ""

        if has_paren:
            if 'Z' in operand:
                operand = operand.replace('Z', '').replace('+', '').replace('-', '').strip()
                if any(r in operand for r in ["R", "PC", "ACC", "BR", "XR", "IR", "JR", "CR"]):
                    mode_code = "100"
                    leftmost_bit = "0"
                    addr_val = Instruction._resolveVarAddr(operand, 0)
                elif operand in variable.data:
                    mode_code = "101"
                    leftmost_bit = "1"
                    addr_val = Instruction._resolveVarAddr(operand)
                else:
                    val = int(operand) if operand else 0
                    if val >= 0:
                        mode_code = "110"
                        leftmost_bit = "0"
                        addr_val = val
                    else:
                        mode_code = "111"
                        leftmost_bit = "1"
                        addr_val = abs(val)
                addr_str = leftmost_bit + Length.addZeros(addr_val, 6)
                return mode_code + addr_str

            elif 'Y' in operand:
                operand = operand.replace('Y', '').replace('+', '').replace('-', '').strip()
                if any(r in operand for r in ["R", "PC", "ACC", "BR", "XR", "IR", "JR", "CR"]):
                    mode_code = "000"
                    leftmost_bit = "0"
                    addr_val = Instruction._resolveVarAddr(operand, 0)
                elif operand in variable.data:
                    mode_code = "001"
                    leftmost_bit = "1"
                    addr_val = Instruction._resolveVarAddr(operand)
                else:
                    val = int(operand) if operand else 0
                    if val >= 0:
                        mode_code = "010"
                        leftmost_bit = "0"
                        addr_val = val
                    else:
                        mode_code = "011"
                        leftmost_bit = "1"
                        addr_val = abs(val)
                addr_str = leftmost_bit + Length.addZeros(addr_val, 6)
                return mode_code + addr_str

            elif 'X' in operand:
                operand = operand.replace('X', '').replace('+', '').replace('-', '').strip()
                if any(r in operand for r in ["R", "PC", "ACC", "BR", "XR", "IR", "JR", "CR"]):
                    mode_code = "100"
                    leftmost_bit = "0"
                    addr_val = Instruction._resolveVarAddr(operand, 0)
                elif operand in variable.data:
                    mode_code = "100"
                    leftmost_bit = "1"
                    addr_val = Instruction._resolveVarAddr(operand)
                else:
                    val = int(operand) if operand else 0
                    mode_code = "101"
                    if val >= 0:
                        leftmost_bit = "0"
                        addr_val = val
                    else:
                        leftmost_bit = "1"
                        addr_val = abs(val)
                addr_str = leftmost_bit + Length.addZeros(addr_val, 6)
                return mode_code + addr_str

            else:
                if '+' in operand:
                    mode_code = "110"
                    operand = operand.replace('+', '').strip()
                elif '-' in operand:
                    mode_code = "111"
                    operand = operand.replace('-', '').strip()
                elif any(r in operand for r in ["R", "PC", "ACC", "BR", "XR", "IR", "JR", "CR"]):
                    mode_code = "001"
                else:
                    mode_code = "011"

                addr_val = Instruction._resolveVarAddr(operand, int(operand) if operand.isdigit() else 0)
                return mode_code + Length.addZeros(addr_val, 7)

        else:
            if any(r in operand for r in ["R", "PC", "ACC", "BR", "XR", "IR", "JR", "CR"]):
                mode_code = "000"
            else:
                mode_code = "010"

            addr_val = Instruction._resolveVarAddr(operand, int(operand) if operand.isdigit() else 0)
            return mode_code + Length.addZeros(addr_val, 7)

    @staticmethod
    def encode(inst):
        """
        Compiles a raw assembly instruction line into a 32-bit binary layout.
        """
        inst = inst.strip()
        parts = inst.split(None, 1)
        op = parts[0].upper()

        if op == 'FUNC':
            return "0".zfill(32)

        operands = []
        if len(parts) > 1:
            operands = [o.strip() for o in parts[1].split(",")]

        # Simplify abstract operations into basic instructions
        if op == "CB":
            op = "ADD"
            operands.append("BR")
        elif op == "CF":
            op = "ADD"
            operands.append("BR")
        elif op == "CMP":
            op = "SUB"
            operands.insert(0, "JR")
        elif op == "ADDPC":
            op = "MOV"
            if len(operands) > 1:
                operands[1] = f"({operands[1]}+Z)"

        if op not in operations:
            raise ValueError(f"Unknown operation: {op}")

        E, W, Cat = operations[op]
        opcode_bin = E + W + Cat

        ib_bin = "0"
        rb_bin = "0"
        op1_bin = "0".zfill(10)
        op2_bin = "0".zfill(15)

        if len(operands) > 0:
            op1_bin = Instruction.encodeOp(operands[0])

        if len(operands) > 1:
            encoded_op2 = Instruction.encodeOp(operands[1])
            if len(encoded_op2) == 16:  # Immediate mode
                ib_bin = "1"
                op2_bin = encoded_op2[:15]
            else:
                ib_bin = "0"
                if 'Y' in operands[1] or 'Z' in operands[1]:
                    rb_bin = "1"
                op2_bin = encoded_op2 + "00000"

        return opcode_bin + ib_bin + op1_bin + rb_bin + op2_bin

    @staticmethod
    def encodeProgram(program):
        """
        Processes an input file or assembly list and writes instructions to Memory.
        """
        if type(program) == type(str()):
            with open(program, "r") as f:
                lines = f.readlines()
        else:
            lines = list(program)

        inst_list = []
        block_cnt = 0
        in_multiline_comment = False
        current_addr = int(register.load(variable.data["BR"]))
        start_mem_addr = current_addr

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('x'):
                continue
            if line.startswith('z'):
                in_multiline_comment = not in_multiline_comment
                continue
            if in_multiline_comment:
                continue

            parts = line.split(None, 1)
            op = parts[0].upper()

            if op in ['CB', 'CF']:
                operand = parts[1].strip()
                block_addr = variable.data[operand]
                memory.store(block_addr, current_addr)
                encoded_inst = Instruction.encode(line)
                inst_list.insert(block_cnt, encoded_inst)
                block_cnt += 1
                current_addr += 1
            else:
                encoded_inst = Instruction.encode(line)
                inst_list.append(encoded_inst)
                current_addr += 1

        # Store block count in BR register
        register.store(variable.data["BR"], block_cnt)

        # Store instructions starting at physical instruction base (address 9)
        for idx, encoded_inst in enumerate(inst_list):
            memory.store(start_mem_addr + idx, encoded_inst)