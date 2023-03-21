import sys

# Initialize parameters
fetchIndex = 1 # Currently fetched index
committedInsts = 0 # Currently commited instructions

# Initialize clocks one below their initial time
clock = {'fe':-1, 'de':0, 're':1, 'di':2, 'is':3, 'wb',4, 'co':5}

    # Queues
fetchDecode_queue = []
decodeRename_queue = []
renameDispatch_queue = []

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

    # Initalize free list and map table, first 32 elements are mapped
overwrite_dict = {} # Not sure if correct, new:old format
free_list = [] 
for x in range(32,preg_count):
    free_list.append(x)
map_table = {}
for x in range(0,32):
    map_table[x] = 'p'+str(x)

# Fetch stage
def fetch(fetchIndex): 
    bundle = data[fetchIndex:1+(issue_width*fetchIndex)]
    for n in bundle:
        fetchDecode_queue.append(n)
    clock['fe'] = clock['fe'] + 1
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
    clock['de'] = clock['de'] + 1
def rename():
    # Only perform if enough insts to continue, else stall
    if (len(free_list) >=  issue_width):
        for n in range(0,issue_width):
            inst = decodeRename_queue.pop(0)
            # Start with the reads
            for r in range(0,len(inst['read'])):
                inst['read'][r] = map_table[inst['read'][r]]
            # Pull from free list, send overwritten to ROB, 
            for w in range(0,len(inst['write'])):
                new_reg = free_list.pop(0)
                overwrite_dict[new_reg] = inst['write'][w] # Not sure if to send to ROB here, might need to account for blank mapping
                map_table[inst['write'][w]] = new_reg
                inst['write'][w] = map_table[inst['write'][w]]
            # Compare regs in current inst to others in bundle to identify dependencies
            for i in decodeRename_queue:
                cmp_inst = i
                war_check = set(cmp_inst['write']).intersection(inst['read'])
                waw_check = set(cmp_inst['write']).intersection(inst['write'])
                # WAR/WAW require hardware renaming
                if war_check:
                    
                if waw_check:
                    # look in free list, update map table, update inst dict, update free list
                for r in inst['write']:
                      
            renameDispatch_queue.append(inst)
    else:
        pass
    clock['re'] = clock['re'] + 1
def dispatch():
    inst = renameDispatch_queue.pop(inst)
    clock['di'] = clock['di'] + 1

#while (committedInsts < instCount):
for t in range(0,1):
    fetch(fetchIndex)
    decode()
    print(decodeRename_queue)
    rename()
