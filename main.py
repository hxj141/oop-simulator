import sys

# Initialize parameters
fetchIndex = 1 # Currently fetched index
committedInsts = 0 # Currently commited instructions
iq_size = 256
rob_size = 256
# Clock is 2D dict, one dimension is the stage, the other is the instruction 
clock = {'fe':-1, 'de':0, 're':1, 'di':2, 'is':3, 'wb':4, 'co':5}
time_log = {1:clock} # Initialize clocks one below their initial time for inst 1
    # Stage Queues
fetchDecode_queue = []
decodeRename_queue = []
renameDispatch_queue = []
issueWB_queue = []
WBcommit_queue = []

    # Instruction queues
issue_queue = []
rob = []
lsq = []

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
    # Attach PC to the instructions
    if l != 0:
        data[l].append(l)
        
instCount = len(data) - 1 # Total instructions
    #Process first line into parameters
preg_count = data[0][0] # Number of physical registers in system
issue_width = data[0][1] # Width of pipeline

    # Initalize free list, ready table and map table, first 32 elements are mapped
overwrite_dict = {} # Temporary buffer for tracking overwrites until time for ROB comes

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
    clock['fe'] += 1
    bundle = data[fetchIndex:1+(issue_width*fetchIndex)]
    for n in bundle:
        fetchDecode_queue.append(n)
        clocklog('fe', n[4])
# Decode stage
def decode():
    # Move to new queue
    clock['de'] += 1
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
        instDict['pc'] = inst[4]
        clocklog('de', instDict['pc'])

def rename():
    clock['re'] += 1
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
            clocklog('re', inst['pc'])
    
def dispatch():
    clock['di'] += 1
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
        # Send to IQ
        issue_queue.append(inst)
        clocklog('di', inst['pc'])
        # Send to LSQ if Load/Store
        if (inst['inst'] == 'L') | (inst['inst'] == 'S'):
            lsq.append(inst)
        # Send to ROB, but also track replacement
        #inst_rob = {k:v for k,v in inst.items()}
        inst_rob = inst
        for w in inst_rob['write']:
            inst_rob['replaced'] = overwrite_dict[w]
            inst_rob['done'] = False
        rob.append(inst_rob)
    
def issue():
    clock['is'] += 1
    global issue_queue
    if (len(issue_queue) >= issue_width):
        # Pre-sort by age in ascending order so oldest are always prioritized
        issue_queue = sorted(issue_queue, key=lambda d: d['age'])
        selected = 0 
        imax = len(issue_queue)
        for n in range(0,imax):
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
                clocklog('is', inst['pc'])
                selected += 1
        # After instructions have been selected, wake up all the dependent ones
        for s in range(0,selected):
            dep_list = issueWB_queue[-1-s]['write'] 
            for d in dep_list:
                ready_table[d] = True
    
def writeback():
    clock['wb'] += 1
    if (len(issueWB_queue) >= issue_width):
        for n in range(0,issue_width):
            inst = issueWB_queue.pop(0)
            # Mark instructions as done, dont do this for stores until commit
            inst['done'] = True
            WBcommit_queue.append(inst)
            clocklog('wb', inst['pc'])
    
def commit():
    clock['co'] += 1
    # Get first inst in ROB that's done, since we're not doing branch prediction, just stick to IQ
    if (len(WBcommit_queue) >= issue_width):
        inst = WBcommit_queue[0]
        for n in range(0,issue_width):
            if inst['done'] == True:
                inst = WBcommit_queue.pop(0)
                if inst['inst'] != 'S':
                    free_list.append(inst['replaced'])
                clocklog('co', inst['pc'])
            else:
                print("This shouldn't happen!")
    
# Log clock time for given inst at given stage
def clocklog(stage, inst):
    time_log[inst] = clock
def output_format():
    print(time_log)

#while (committedInsts < instCount):
for t in range(0,13):
    fetch(fetchIndex)
    decode()
    rename()
    dispatch()
    issue()
    writeback()
    commit()
    fetchIndex += 1
output_format()
    #print(time_log)
#for t in range(0, instCount):
 #   for item in time_log.items():
  #      print(item[1][t])
   #     if item[0] == 'co':
    #        print('\n')
     #   else:
      #      pass
        #print("ROB", rob, '\nLSQ', lsq)
#    print(issue_queue)
#    print(issueWB_queue)
#    print(clock)
#    print(map_table)
#    print(overwrite_dict)
