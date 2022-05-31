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
    def datetime(self):
        return datetime.fromisoformat(self.date.strip('\n')).isoformat() 

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
        longkeys = ["PID","VIRT","RES","SHR"]
        r = self.top.split("\n")[7::]
        r = [dict(zip(keys, i.split())) for i in r if i != ""]
        for i in r:
            for k,v in i.items():
                if k in longkeys:
                    try:
                        i[k] = int(v)
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


def splotmem(data):
    x_time = [i.datetime for i in data]
    y1_memavail = [i.meminfo["MemAvailable"] for i in data]
    y2_memtotal = [i.meminfo["MemTotal"] for i in data]
    plt.plot(x_time, y1_memavail)
    plt.plot(x_time, y2_memtotal)
    plt.title("MemInfo")
    plt.ylabel("Memory Kb")
    plt.xlabel("DateTime")
    plt.legend(["MemAvailable","MemTotal"])
    plt.xticks(rotation=90)
    plt.show()


def splotproc(data):
    pids = set([item["PID"] for sublist in data for item in sublist.processinfo])
    imgs = []
    for i in pids:
        k = [(item["PID"],item["NAME"],item["RES"],sublist.datetime) for sublist in data for item in sublist.processinfo if item["PID"] == i]
        ydata = [j[2] for j in k]
        xdata = [j[3] for j in k]
        name = str(k[0][0]) + " " + str(k[0][1])
        imgs.append(name)
        if len(k) != len(xdata):
            logging.warn("Process Time mismatch for pid %s " % name)
        plt.plot(xdata, ydata, label=name)
    plt.legend(imgs)
    plt.title("ProcInfo")
    plt.xlabel("DateTime")
    plt.ylabel("Memory Kb")
    plt.xticks(rotation=90)
    plt.ticklabel_format(axis='y', style='plain')
    mplcursors.cursor(hover=True)
    plt.show()
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="DMT analyzer")
    parser.add_argument('-f', help='infile', required=True)
    parser.add_argument('-o', help='outfile', required=False)
    parser.add_argument('-p', help='plot', required=False)
    args = vars(parser.parse_args())
    file = args["f"]
    data = parseFile(file)
    if args["o"]:
        outfile = args["o"]
        exportjson(outfile, data)
    if args["p"]:
        splotmem(data)
        splotproc(data)