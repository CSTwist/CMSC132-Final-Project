from bin_convert import HalfPrecision, Length
from storage import register, memory, variable

class Access:
    @staticmethod
    def data(addr, flow):
        """
        Loads the value that follows the flow of storage from the specified address.
        Example: data('PC', ['var', 'reg']) gets the address of PC from 'variable',
        then gets the value at that address in 'register'.
        """
        curr_val = addr
        for step in flow:
            if step == 'var':
                curr_val = variable.load(curr_val)
            elif step == 'reg':
                curr_val = register.load(curr_val)
            elif step == 'mem':
                curr_val = memory.load(curr_val)
        return curr_val

    @staticmethod
    def store(typ, addr, value):
        """
        Stores a value to the specified storage type ('memory' or 'register') at the address.
        """
        if typ == 'memory':
            memory.store(addr, value)
        elif typ == 'register':
            register.store(addr, value)


class AddressingMode:
    @staticmethod
    def immediate(var):
        """
        Immediate addressing mode. Returns a decimal converted from Half Precision format.
        """
        if type(var) == type(str()) and len(var) == Length.precision:
            return HalfPrecision.hpbin2dec(var)
        return var

    @staticmethod
    def relative(displace):
        """
        Relative addressing mode. Adds PC to displacement, returning the value in memory.
        """
        pc_val = Access.data('PC', ['var', 'reg'])
        eff_addr = int(pc_val + displace)
        return memory.load(eff_addr)

    @staticmethod
    def based(displace):
        """
        Based addressing mode. Adds BR value to displacement, returning the value in memory.
        """
        br_val = Access.data('BR', ['var', 'reg'])
        eff_addr = int(br_val + displace)
        return memory.load(eff_addr)

    @staticmethod
    def indexed(displace):
        """
        Indexed addressing mode. Adds XR value to displacement.
        Returns: (effective address, value it points to in memory)
        """
        xr_val = Access.data('XR', ['var', 'reg'])
        eff_addr = int(xr_val + displace)
        return eff_addr, memory.load(eff_addr)

    @staticmethod
    def register(reg_addr):
        """
        Register addressing mode. Converts reg_addr to decimal.
        Returns: (effective register address, register value, register storage object)
        """
        if type(reg_addr) == type(str()) and len(reg_addr) == Length.precision:
            eff_addr = int(HalfPrecision.hpbin2dec(reg_addr))
        elif type(reg_addr) == type(str()):
            eff_addr = int(reg_addr, 2)
        else:
            eff_addr = int(reg_addr)
        return eff_addr, register.load(eff_addr), register

    @staticmethod
    def register_indirect(reg_addr):
        """
        Register indirect addressing mode. Reads the memory address stored inside a register.
        Returns: (effective address, value it points to in memory)
        """
        if type(reg_addr) == type(str()) and len(reg_addr) == Length.precision:
            reg_idx = int(HalfPrecision.hpbin2dec(reg_addr))
        elif type(reg_addr) == type(str()):
            reg_idx = int(reg_addr, 2)
        else:
            reg_idx = int(reg_addr)
        eff_addr = int(register.load(reg_idx))
        return eff_addr, memory.load(eff_addr)

    @staticmethod
    def direct(var_addr):
        """
        Direct addressing mode. Address contains the direct memory location.
        Returns: (effective address, value in memory)
        """
        if type(var_addr) == type(str()) and len(var_addr) == Length.precision:
            eff_addr = int(HalfPrecision.hpbin2dec(var_addr))
        elif type(var_addr) == type(str()):
            eff_addr = int(var_addr, 2)
        else:
            eff_addr = int(var_addr)
        return eff_addr, memory.load(eff_addr)

    @staticmethod
    def indirect(var_addr):
        """
        Indirect addressing mode. Memory address contains the address of the target.
        Returns: (effective address, value in memory)
        """
        if type(var_addr) == type(str()) and len(var_addr) == Length.precision:
            var_idx = int(HalfPrecision.hpbin2dec(var_addr))
        elif type(var_addr) == type(str()):
            var_idx = int(var_addr, 2)
        else:
            var_idx = int(var_addr)
        eff_addr = int(memory.load(var_idx))
        return eff_addr, memory.load(eff_addr)

    @staticmethod
    def autoinc(reg_addr):
        """
        Auto-increment addressing mode. Reads memory address from register,
        then increments register value by 1.
        Returns: (effective address, value in memory)
        """
        if type(reg_addr) == type(str()) and len(reg_addr) == Length.precision:
            reg_idx = int(HalfPrecision.hpbin2dec(reg_addr))
        elif type(reg_addr) == type(str()):
            reg_idx = int(reg_addr, 2)
        else:
            reg_idx = int(reg_addr)
        eff_addr = int(register.load(reg_idx))
        val = memory.load(eff_addr)
        register.store(reg_idx, eff_addr + 1)
        return eff_addr, val

    @staticmethod
    def autodec(reg_addr):
        """
        Auto-decrement addressing mode. Decrements register value by 1,
        then reads the memory address from register.
        Returns: (effective address, value in memory)
        """
        if type(reg_addr) == type(str()) and len(reg_addr) == Length.precision:
            reg_idx = int(HalfPrecision.hpbin2dec(reg_addr))
        elif type(reg_addr) == type(str()):
            reg_idx = int(reg_addr, 2)
        else:
            reg_idx = int(reg_addr)
        reg_val = int(register.load(reg_idx))
        new_reg_val = reg_val - 1
        register.store(reg_idx, new_reg_val)
        eff_addr = new_reg_val
        val = memory.load(eff_addr)
        return eff_addr, val