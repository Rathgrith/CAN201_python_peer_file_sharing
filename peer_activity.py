from main import *

# peer checking its directory
# and work out its sending queue by interaction of 2 classes


class local_directory:
    def __init__(self):
        self.dir_dict = {}
        self.updater()

    def updater(self):
        file_list = traverse('./share')
        for files in file_list:
            self.update(files)

    def update(self, files):
        self.dir_dict[files] = os.path.getsize(files)

    def query(self, file):
        return self.dir_dict[file]


class History:
    def __init__(self):
        if os.path.exists('./history.json'):
            with open('./history.json', 'r') as h:
                self.history = load(h)
            h.close()
        else:
            self.history = {}

    def refresh_history(self):
        with open('./history.json', 'w') as h:
            dump({}, h)
        h.close()

    def dequeue(self, filename):
        self.history[filename] = os.path.getmtime(filename)
        with open('./history.json', 'w') as h:
            dump(self.history, h)
        h.close()

    def enqueue(self, filename):
        self.history.pop(filename)
        with open('./history.json', 'w') as h:
            dump(self.history, h)
        h.close()

    def query(self, filename):
        if not filename in history:
            return False
        else:
            return history(filename)

    def sending_queue(self):
        file_list = traverse(('./share'))
        sendingqueue = []
        for filename in file_list:
            if os.path.isdir(filename) is False:
                if filename.endswith('.temp') is False:
                    if filename not in self.history:
                        sendingqueue.append(filename)
                    elif os.path.getmtime(filename) != self.history[filename]:
                        sendingqueue.append(filename)
        return sendingqueue


def checking_connection(filesocket):
    if filesocket._closed:
        raise Exception

    else:
        filesocket.settimeout(None)
        # have to be blocking style
        return True


def send_and_receive(filesocket, history):
    socket_flag = checking_connection(filesocket)
    if socket_flag == True:
        sending_queue = history.sending_queue()
        global ip
        print("To", ip,"checking queue......")
        if len(sending_queue) > 0:
            send_routine(history, sending_queue, filesocket)
        else:
            while True:
                try:
                    receive_status = recv_file(filesocket, history)
                    filesocket.settimeout(0.9)
                    # 连接空置0.9s后进入except
                    if receive_status is True:
                        pass
                    else:
                        break
                except:
                    break



# sender functions:

def make_header(file):
    file_b = file.encode()
    msg = struct.pack('!I', os.path.getsize(file))
    msg += struct.pack('!I', len(file_b))
    msg += struct.pack('!d', os.path.getmtime(file))
    msg += file_b
    return msg

def send_header(file, filesocket):
    message = make_header(file)
    filesocket.send(message)

def send_routine(history, sending_queue, filesocket):
    for file in sending_queue:
        send_header(file, filesocket)
        with open(file, 'rb') as f:
            filesocket.sendfile(f)
            f.close()
        history.dequeue(file)
    filesocket.send(struct.pack('!IId', 0, 0, 0.0))
    # deny msg

# receiver functions

def parse_header_information(msg):
    size, filenamesize, modtime = struct.unpack('!IId', msg)
    return size, filenamesize, modtime

def write_files_and_folders(filename):
    folderflag = os.path.exists(os.path.split(filename)[0])
    if not folderflag:
        foldername = os.path.split(filename)[0]
        os.mkdir(foldername)
    global ip
    print("From", ip, "writing...", filename)

def downloader(filesocket, received_data, filename, size, modtime):
    if not os.path.exists(filename):
        write_files_and_folders(filename)
        with open(filename + '.temp', 'wb') as f:
            # avoid interruption
            while not received_data == size:
                try:
                    if (size - received_data >= 51200):
                        # a buffer mechanism is set
                        reading_data = filesocket.recv(51200)
                    else:
                        reading_data = filesocket.recv(size - received_data)
                except:
                    return False
                    # receiving error, cancel the downloading
                try:
                    f.write(reading_data)
                    received_data += len(reading_data)
                except:
                    break
                    # writing error, retransmit chunks
        f.close()
    else:
        if modtime > os.path.getmtime(filename):
            write_files_and_folders(filename)
            with open(filename + '.temp', 'wb') as f:
                while not received_data == size:
                    try:
                        if (size - received_data >= 51200):
                            reading_data = filesocket.recv(51200)
                        else:
                            reading_data = filesocket.recv(size - received_data)
                    except:
                        return False
                    try:
                        f.write(reading_data)
                        received_data += len(reading_data)
                    except:
                        break
            f.close()

def recv_file(filesocket, sending_history):
    local_status = local_directory()
    waiting_flag = True
    data_index = 0
    try:
        header = filesocket.recv(16)
        size, path_len, modtime = parse_header_information(header)
    except:
        return False
    if path_len != 0:
        filename = filesocket.recv(path_len).decode()
        downloader(filesocket, data_index, filename, size, modtime)
        os.rename(filename + '.temp', filename)
        # after completed transmission,
        # rename the temp file
        global ip
        print("From", ip, 'received', filename)
        sending_history.dequeue(filename)
        currentfilesize = local_status.query(filename)
    else:
        print("no files need to be received by")
        return False
    return waiting_flag and currentfilesize == size



