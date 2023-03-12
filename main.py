import sys

# Initialize
fetchIndex = 1 # Currently fetched index
committedInsts = 0 # Currently commited instructions

    # Queues
fetchDecode_queue = []
decodeRename_queue = []
renameDispatch_queue = []

    # Map table
map_table = {}

with open("input/"+sys.argv[1]) as f: # import in file based on execution argument
    data = f.readlines()

    # Prepare lines for processing
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
    # Initalize free list
free_list = [] 
for x in range(0,preg_count):
    free_list.append(x)


# Fetch stage
def fetch(fetchIndex): 
    bundle = data[fetchIndex:1+(issue_width*fetchIndex)]
    for n in bundle:
        fetchDecode_queue.append(n)
    

         
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
def rename():
    # Only perform if enough insts to continue, else stall
    if (len(free_list) >=  issue_width):
        for n in range(0,issue_width):
            inst = decodeRename_queue.pop(0)
            # Compare regs in current inst to others in bundle to identify dependencies
            for i in range(0, issue_width-(n+1)):
                cmp_inst = decodeRename_queue[i]
                rar_check = set(inst['read']).intersection(cmp_inst['read'])
                raw_check = set(inst['write']).intersection(cmp_inst['read'])
                war_check = set(inst['read']).intersection(cmp_inst['write'])
                waw_check = set(inst['write']).intersection(cmp_inst['write'])
                # WAR/WAW require hardware renaming
                if war_check: 
                    pass
                    # look in free list, update map table, update inst dict, update free list
                if waw_check:
                    pass
            renameDispatch_queue.append(inst)
        
        

#while (committedInsts < instCount):
fetch(fetchIndex)
decode()
print(decodeRename_queue)
rename()
