# Rebalancer.py

# To do:
# * Modularize, with default args for current, target, and adjustments?
# * Group things as structs to halve the array count
# * isValidAmount -> isValidFloat(s, max)
# * isValidSymbol -> isValidSymbol(s, max_length)


import csv


MAX_ALLOCATION = 200000  # Max amount allocated to any one security

current_syms = []
current_vals = []
current_pcs = []
target_syms = []
target_pcs = []
adjustment_syms = []
adjustment_vals = []


def csval(v):
    return '{:,.0f}'.format(v)


def myAssert(shouldBeTrue, errorMsg):
    if not shouldBeTrue:
        print errorMsg
        exit()


def isValidSymbol(s):
    if (len(s) <= 0):
        print "*** Symbol length <= 0"
        return False
    if  (len(s) > 5):
        print "*** Symbol length too long"
        return False
    if (not s.isalpha()):
        print "*** Symbol contains non-alpha char"
        return False
    return True


def isValidPercentage(s):
    if not isValidAmount(s):
        print "*** Percentage is not a valid amount"
        return False
    v = float(s)
    if (v < 0.0 or v > 100.0):
        print "*** Percentage not in range: [0 - 100]"
        return False
    return True


def isValidAmount(s):
    if (len(s) <= 0):
        print "*** Amount length <= 0"
        return False
    if (s.replace('.', '', 1).isdigit() is False):
        print "*** Amount contains invalid character"
        return False
    v = float(s)
    if (v < 0 or v > 200000):
        print "*** Amount (%s) > MAX_ALLOCATION (%s)" % \
            (csval(v), csval(MAX_ALLOCATION))
        return False
    return True

print "\n******** Rebalancer ********"

# Read current allocations
with open('current.csv') as allocations_file:
    csv_reader = csv.reader(allocations_file, delimiter=',')
    i = 0
    for row in csv_reader:
        # Ignore first header row.
        # This also avoids the annoyance that MS Excel csv-utf8 format seems to
        # encode the first character wrong (!)
        if i != 0:
            sym = row[0].strip()
            val = row[1].strip().lstrip('$')
            myAssert(isValidSymbol(sym),
                     "*** Current table: Invalid symbol")
            myAssert(isValidAmount(val),
                     "*** Current table: Invalid amount")
            current_syms.append(sym)
            current_vals.append(float(val))
        i += 1

# Verify current syms unique
myAssert(len(current_syms) == len(set(current_syms)),
         "Current table: Duplicate symbol.")

# Read target allocations
with open('target.csv') as targets_file:
    csv_reader = csv.reader(targets_file, delimiter=',')
    i = 0
    for row in csv_reader:
        # Ignore first (header) row.
        # This also avoids the annoyance that MS Excel csv-utf8 format seems to
        # encode the first character wrong (!)
        if i != 0:
            sym = row[0].strip()
            pc = row[1].strip().rstrip('%%')
            print row
            myAssert(isValidSymbol(sym),
                     "*** Target table - invalid symbol")
            myAssert(isValidPercentage(pc),
                     "*** Target table - invalid percentage")
            target_syms.append(sym)
            target_pcs.append(float(pc))
        i += 1

# Verify target syms unique
myAssert(len(target_syms) == len(set(target_syms)),
         "*** Target table: Duplicate symbol.")

# Verify target percentages add up to 100%
# Normalize to 100 from 1.0, if necessary
target_sum = sum(target_pcs)
if (abs(target_sum - 1.0) < 0.01):
    i = 0
    for i in range(len(target_syms)):
        target_pcs[i] *= 100.0
    target_sum = sum(target_pcs)  # Recalculate

myAssert(abs(target_sum - 100.0) < 1.0,
         "*** Target table - sum(percentages) != 100.0")

# Calculate current percentages
current_sum = sum(current_vals)
for i in range(len(current_syms)):
    pc = 100 * (current_vals[i] / current_sum)
    current_pcs.append(pc)

print "\nCurrent Allocations:"
num_current_gt0 = 0
for i in range(len(current_syms)):
    c_sym = current_syms[i]
    c_val = current_vals[i]
    c_pc = current_pcs[i]
    if c_val != 0:
        num_current_gt0 += 1
        print "\t%s\t$%s\t\t(%s %%)" % \
            (c_sym, csval(c_val), csval(c_pc))
if num_current_gt0 > 0:
    print "\t-------------"
    print "\tTotal: $%s" % csval(current_sum)

print "\nTarget Allocations:"
for i in range(len(target_syms)):
    print "\t%s\t%0.1f%%" % (target_syms[i], target_pcs[i])

# Calculate adjustments
# Adjustments for symbols in the current table
for i in range(len(current_syms)):

    # Find symbol in targets
    sym = current_syms[i]
    c_val = current_vals[i]
    a_val = 0
    if sym in target_syms:
        j = target_syms.index(sym)
        t_pc = target_pcs[j] / 100.0
        t_val = t_pc * current_sum
        a_val = t_val - c_val
    else:
        a_val = -c_val
    adjustment_syms.append(sym)
    adjustment_vals.append(a_val)

# Adjustments for symbols NOT in current table
for i in range(len(target_syms)):
    t_sym = target_syms[i]
    if t_sym not in current_syms:
        t_pc = target_pcs[i] / 100
        t_val = t_pc * current_sum
        adjustment_syms.append(t_sym)
        adjustment_vals.append(t_val)

print "\nAdjustments:"
num_adjustments = 0
for i in range(len(adjustment_syms)):
    a_sym = adjustment_syms[i]
    adj = adjustment_vals[i]
    if abs(adj) > 100.0:  # Only show adjustments > $X
        add_or_sub = "Add" if (adj >= 0) else "Subtract"
        print "\t%s\t%s $%s" % (a_sym, add_or_sub, csval(abs(adj)))
        num_adjustments += 1
if num_adjustments == 0:
    print "\t(None)"
print "\n"
