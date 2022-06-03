import argparse
from datetime import datetime
import json
import logging
try: 
    import pandas as pd
    from matplotlib import pyplot as plt
    import mplcursors
except ImportError as e:
    logging.error("%s" % (str(e.msg)))


logging.basicConfig(level=logging.WARN, 
  format="%(asctime)s %(levelname)s %(thread)d %(funcName)s %(message)s",
  handlers=[
    logging.StreamHandler()
  ])


class DMTEntry(object):
    def __init__(self, date, mem, top):
        self.date = date
        self.mem = mem
        self.top = top

    @property
    def todatetime(self):
        return datetime.fromisoformat(self.date.strip('\n')).isoformat() 
        
    @property
    def datetime(self):
        return datetime.fromisoformat(self.date.strip('\n'))

    @property
    def meminfo(self):
        r = self.mem
        r = dict(x.strip().split(None,1) for x in r.split('\n') if x != "")
        r = {key.strip(':'): item.strip() for key, item in r.items()}
        r = {k: int(v.strip(' kB')) for (k,v) in r.items()}
        return r

    @property
    def processinfo(self):
        keys = ["PID","USER","PR","NI","VIRT","RES","SHR","S","CPU","MEM","TIME","NAME"]
        lkeys = ["PID","VIRT","RES","SHR"]
        fkeys = ["CPU", "MEM"]
        r = self.top.split("\n")[7::]
        r = [dict(zip(keys, i.split())) for i in r if i != ""]
        for i in r:
            for k,v in i.items():
                if k in lkeys:
                    try:
                        i[k] = int(v)
                    except ValueError:
                        i[k] = str(v)
                elif k in fkeys:
                    try:
                        i[k] = float(v)
                    except ValueError:
                        i[k] = str(v)
        return r

    def tojson(self):
        r = {"Timestamp" : self.datetime}
        r["MemInfo"] = self.meminfo
        r["Processes"] = self.processinfo
        return json.dumps(r)


def parseFile(file):
    try:
        with open(file, "r") as f:
            data = f.readlines()
    except Exception as e:
        logging.error("%s" % (str(e.msg)))
    output = []
    count = 0
    D = False
    M = False
    T = False
    doc = DMTEntry(date="", mem="", top="")
    for line in data:
        if line == "D\n":
            D = True
            if D and M and T: #New DMTEntry
                output.append(doc)
                count += 1
                logging.info("Processed records %s" % str(count))
                M = False
                T = False
                doc = DMTEntry(date="", mem="", top="")
                continue
            continue
        if line == "M\n":
            M = True
            continue
        if line == "T\n":
            T = True
            continue
        if D and M and T:
            doc.top += line
        if D and M and not T:
            doc.mem += line
        if D and not M and not T:
            doc.date += line
    return output


def exportjson(outfile, data):
    try:
        with open(outfile, 'w') as f:
            for i in data:
                f.write(i.tojson())
                f.write("\n")
    except Exception as e:
        logging.error("%s" % (str(e.msg)))


def plot_meminfo(eventRecords):
    metrics = ["MemTotal", "MemFree", "MemAvailable", "Active", "Inactive", "Active(anon)", "Inactive(anon)", "Active(file)", "Inactive(file)"]
    for i in metrics:
        j = [(eventRecord.meminfo[i], eventRecord.datetime) for eventRecord in eventRecords]
        xdata = [k[1] for k in j]
        ydata = [k[0] for k in j]
        plt.plot(xdata, ydata, label=i)
    plt.title("MemInfo")
    plt.ylabel("Memory Kb")
    plt.xlabel("Time")
    plt.legend(metrics)
    plt.xticks(rotation=90)
    plt.ticklabel_format(axis='y', style='plain')
    mplcursors.cursor(hover=True)
    plt.show()


def plot_process_res(eventRecords, pids=None):
    if pids == None:
        pids = set([item["PID"] for sublist in eventRecords for item in sublist.processinfo])
    else:
        pids = set(pids)
    imgs = []
    for i in pids:
        j = [(item["PID"],item["NAME"],item["RES"],sublist.datetime) for sublist in eventRecords for item in sublist.processinfo if item["PID"] == i]
        ydata = [k[2] for k in j]
        xdata = [k[3] for k in j]
        name = str(j[0][0]) + " " + str(j[0][1])
        imgs.append(name)
        plt.plot(xdata, ydata, label=name)
    plt.legend(imgs)
    plt.title("Process RES Info")
    plt.xlabel("Time")
    plt.ylabel("Memory Kb")
    plt.xticks(rotation=90)
    plt.ticklabel_format(axis='y', style='plain')
    mplcursors.cursor(hover=True)
    plt.show()


def plot_process_shr(eventRecords, pids=None):
    if pids == None:
        pids = set([item["PID"] for sublist in eventRecords for item in sublist.processinfo])
    else:
        pids = set(pids)
    imgs = []
    for i in pids:
        j = [(item["PID"],item["NAME"],item["SHR"],sublist.datetime) for sublist in eventRecords for item in sublist.processinfo if item["PID"] == i]
        ydata = [k[2] for k in j]
        xdata = [k[3] for k in j]
        name = str(j[0][0]) + " " + str(j[0][1])
        imgs.append(name)
        plt.plot(xdata, ydata, label=name)
    plt.legend(imgs)
    plt.title("Process SHR Info")
    plt.xlabel("Time")
    plt.ylabel("Memory Kb")
    plt.xticks(rotation=90)
    plt.ticklabel_format(axis='y', style='plain')
    mplcursors.cursor(hover=True)
    plt.show()


def plot_process_cpu(eventRecords, pids=None):
    if pids == None:
        pids = set([item["PID"] for sublist in eventRecords for item in sublist.processinfo])
    else:
        pids = set(pids)
    imgs = []
    for i in pids:
        j = [(item["PID"],item["NAME"],item["CPU"],sublist.datetime) for sublist in eventRecords for item in sublist.processinfo if item["PID"] == i]
        ydata = [k[2] for k in j]
        xdata = [k[3] for k in j]
        name = str(j[0][0]) + " " + str(j[0][1])
        imgs.append(name)
        plt.plot(xdata, ydata, label=name)
    plt.legend(imgs)
    plt.title("Process %CPU Info")
    plt.xlabel("Time")
    plt.ylabel("Percent CPU")
    plt.xticks(rotation=90)
    plt.ticklabel_format(axis='y', style='plain')
    mplcursors.cursor(hover=True)
    plt.show()
    

def plot_process_mem(eventRecords, pids=None):
    if pids == None:
        pids = set([item["PID"] for sublist in eventRecords for item in sublist.processinfo])
    else:
        pids = set(pids)
    imgs = []
    for i in pids:
        j = [(item["PID"],item["NAME"],item["MEM"],sublist.datetime) for sublist in eventRecords for item in sublist.processinfo if item["PID"] == i]
        ydata = [k[2] for k in j]
        xdata = [k[3] for k in j]
        name = str(j[0][0]) + " " + str(j[0][1])
        imgs.append(name)
        plt.plot(xdata, ydata, label=name)
    plt.legend(imgs)
    plt.title("Process %MEM Info")
    plt.xlabel("Time")
    plt.ylabel("Percent MEM")
    plt.xticks(rotation=90)
    plt.ticklabel_format(axis='y', style='plain')
    mplcursors.cursor(hover=True)
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="DMT analyzer")
    parser.add_argument('-f', help='infile', required=True)
    parser.add_argument('-o', help='outfile', required=False)
    parser.add_argument('-t', help='Plot Types', choices=["meminfo","res","shr","cpu","mem"], required=False)
    parser.add_argument('-p', help='PIDs', required=False)
    args = vars(parser.parse_args())
    file = args["f"]
    data = parseFile(file)
    if args["o"]:
        outfile = args["o"]
        exportjson(outfile, data)
    if args["p"]:
        pids = [int(x) for x in args["p"].split(',')]
    else:
        pids = None
    if args["t"]:
        plottype = args["t"]
        if plottype == "meminfo":
            plot_meminfo(data)
        if plottype == "res":
            plot_process_res(data, pids)
        if plottype == "shr":
            plot_process_shr(data, pids)
        if plottype == "cpu":
            plot_process_cpu(data, pids)
        if plottype == "mem":
            plot_process_mem(data, pids)