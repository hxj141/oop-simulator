import sys

# Initialize parameters
fetchIndex = 1 # Currently fetched index
committedInsts = 0 # Currently commited instructions
iq_size = 256
rob_size = 256
# Initialize clocks one below their initial time
clock = {'fe':-1, 'de':0, 're':1, 'di':2, 'is':3, 'wb':4, 'co':5}

    # Queues
fetchDecode_queue = []
decodeRename_queue = []
renameDispatch_queue = []
issueWB_queue = []
issue_queue = []

    # Prepare lines for processing
with open("input/"+sys.argv[1]) as f: # import in file based on execution argument
    data = f.readlines()
for l in range(0,len(data)):
    data[l] = data[l].split(',') #Create list out of lines
    for i in range(0,len(data[l])): 
        data[l][i].replace('\n','') # Remove unnecessary linebreaks
        try: # Cast all strings of ints to ints
            data[l][i] = int(data[l][i])
        except ValueError:
            pass
instCount = len(data) - 1 # Total instructions
    #Process first line into parameters
preg_count = data[0][0] # Number of physical registers in system
issue_width = data[0][1] # Width of pipeline

    # Initalize free list, ready table and map table, first 32 elements are mapped
overwrite_dict = {} # Not sure if correct, new:old format
map_table = {}
ready_table = {}
free_list = [] 
for x in range(32,preg_count):
    free_list.append('p'+str(x))
for x in range(0,32):
    map_table[x] = 'p'+str(x)
for x in range(0,preg_count):
    if x < 32:
        ready_table['p'+str(x)] = True
    else:
        ready_table['p'+str(x)] = False
# Fetch stage
def fetch(fetchIndex): 
    bundle = data[fetchIndex:1+(issue_width*fetchIndex)]
    for n in bundle:
        fetchDecode_queue.append(n)
    clock['fe'] += 1
# Decode stage
def decode():
    # Move to new queue
    for n in range(0,issue_width):
        inst = fetchDecode_queue.pop(0)
        # Identify producers and consumers based on the instruction type
        match inst[0]:
            case 'L':
                instDict = {'inst':'L', 'read':[inst[3]], 'write':[inst[1]]}
                decodeRename_queue.append(instDict)
            case 'S':
                instDict = {'inst':'S', 'read':[inst[1]], 'write':[]}
                decodeRename_queue.append(instDict)
            case 'R':
                instDict = {'inst':'R', 'read':[inst[1],inst[2]], 'write':[inst[3]]}
                decodeRename_queue.append(instDict)    
            case 'I':
                instDict = {'inst':'I', 'read':[inst[1]], 'write':[inst[2]]}
                decodeRename_queue.append(instDict)
    clock['de'] += 1
def rename():
    # Only perform if enough insts to continue, else stall
    if (len(free_list) >=  issue_width):
        for n in range(0,issue_width):
            inst = decodeRename_queue.pop(0)
            # Start with the reads
            for r in range(0,len(inst['read'])):
                inst['read'][r] = map_table[inst['read'][r]]
            # Pull from free list, track overwritten reg, update map table,  update inst dict
            for w in range(0,len(inst['write'])):
                new_reg = free_list.pop(0)
                overwrite_dict[new_reg] = 'p' + str(inst['write'][w]) # Not sure if to send to ROB here, might need to account for blank mapping
                map_table[inst['write'][w]] = new_reg
                inst['write'][w] = map_table[inst['write'][w]]
            renameDispatch_queue.append(inst)
    clock['re'] += 1
def dispatch():
    for n in range(0,issue_width):
        inst = renameDispatch_queue.pop(0)
        # Add an aging property to the instruction
        if not issue_queue:
            inst['age'] = 0
        else:
            inst['age'] = issue_queue[-1]['age'] + 1
        # Update ready table for destination entries
        for w in range(0,len(inst['write'])):
            ready_table[w] = False
        issue_queue.append(inst)
    clock['di'] += 1
def issue():  
    global issue_queue
    if (len(issue_queue) >= issue_width):
        # Pre-sort by age in ascending order so oldest are always prioritized
        issue_queue = sorted(issue_queue, key=lambda d: d['age'])
        selected = 0 
        for n in range(0,len(issue_queue)):
            if (selected >= issue_width): # Stop when you've selected N instructions
                break
            inst = issue_queue[n-selected]
            #Check if dependent instructions are ready, if so, select and place into WB
            rcheck_flag = 1
            for r in inst['read']:
                if ready_table[r] == False:
                    rcheck_flag = 0
            if rcheck_flag:
                issueWB_queue.append(issue_queue.pop(n-selected))
                selected += 1
        # After instructions have been selected, wake up all the dependent ones
        for s in range(0,selected):
            dep_list = issueWB_queue[-1-s]['write'] 
            for d in dep_list:
                ready_table[d] = True
    clock['is'] += 1
#while (committedInsts < instCount):
for t in range(0,1):
    fetch(fetchIndex)
    decode()
    rename()
    dispatch()
    issue()
    print(ready_table)
#    print(issue_queue)
#    print(issueWB_queue)
#    print(clock)
#    print(map_table)
#    print(overwrite_dict)
