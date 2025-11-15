#!/usr/bin/python

from collections import namedtuple
import time
import sys

class Edge:
    def __init__ (self, origin=None, weight = 0):
        self.origin = origin
        self.weight = weight

    def bump(self, w=1):
        self.weight += w

    def __repr__(self):
        return "edge: {0} {1}".format(self.origin, self.weight)
        
class Airport:
    def __init__ (self, iden=None, name=None):
        self.code = iden
        self.name = name
        self.routes = []
        self.routeHash = dict()
        self.outweight = 0.0
        self.pageIndex = None
        self.rank = 0.0

    def add_route(self, dst_index, w=1):
        e = self.routeHash.get(dst_index)
        if e is None:
            e = Edge(origin=dst_index, weight=w)
            self.routeHash[dst_index] = e
            self.routes.append(e)
        else:
            e.bump(w)
        self.outweight += w

    @property
    def is_dangling(self):
        return self.outweight == 0.0

    def __repr__(self):
        return f"{self.code}\t{self.pageIndex}\t{self.name}"

edgeList = [] # list of Edge
edgeHash = dict() # hash of edge to ease the match
airportList = [] # list of Airport
airportHash = dict() # hash key IATA code -> Airport

def readAirports(fd):
    print("Reading Airport file from {0}".format(fd))
    airportsTxt = open(fd, "r");
    cont = 0
    for line in airportsTxt.readlines():
        a = Airport()
        try:
            temp = line.split(',')
            if len(temp[4]) != 5 :
                raise Exception('not an IATA code')
            a.name=temp[1][1:-1] + ", " + temp[3][1:-1]
            a.code=temp[4][1:-1]
        except Exception as inst:
            pass
        else:
            cont += 1
            airportList.append(a)
            airportHash[a.code] = a
    airportsTxt.close()
    print(f"There were {cont} Airports with IATA code")
    for idx, a in enumerate(airportList):
        a.pageIndex = idx


def readRoutes(fd):
    print(f"Reading Routes file from {fd}")
    total = 0
    accepted = 0
    with open(fd, "r", encoding="utf-8") as fr:
        for line in fr:
            total += 1
            temp = line.split(',')
            if len(temp) < 6:
                continue

            src = temp[2].strip().upper()
            dst = temp[4].strip().upper()

            if len(src) != 3 or len(dst) != 3:
                continue
            a_src = airportHash.get(src)
            a_dst = airportHash.get(dst)
            if a_src is None or a_dst is None:
                continue

            a_src.add_route(a_dst.pageIndex, 1)
            accepted += 1

    print(f"Accepted route records: {accepted} / {total}")

    num_vertices = len(airportList)
    num_edges = sum(len(a.routeHash) for a in airportList)
    num_dangling = sum(1 for a in airportList if a.outweight == 0.0)
    print(f"Vertices: {num_vertices}, unique edges: {num_edges}, dangling: {num_dangling}")

def computePageRanks():
    L = 0.85
    eps = 1e-10
    max_iter = 200

    n = len(airportList)
    if n == 0:
        return 0

    for a in airportList:
        a.rank = 1.0 / n

    last_delta = None
    for it in range(1, max_iter + 1):
        dangling_mass = sum(a.rank for a in airportList if a.outweight == 0.0)
        base = (1.0 - L) / n + L * dangling_mass / n
        Q = [base] * n

        for a in airportList:
            if a.outweight == 0.0:
                continue
            scale = L * a.rank / a.outweight
            for e in a.routes:
                Q[e.origin] += scale * e.weight

        s = sum(Q)
        if s != 0.0:
            Q = [x / s for x in Q]

        delta = 0.0
        for i, a in enumerate(airportList):
            delta += abs(Q[i] - a.rank)
            a.rank = Q[i]

        if it == 1 or it % 10 == 0:
            print(f"iter={it:3d}  delta={delta:.3e}  sum={sum(Q):.12f}  dangling_mass={dangling_mass:.6f}")

        last_delta = delta
        if delta < eps:
            print(f"Converged at iter={it}  delta={delta:.3e}  sum={sum(Q):.12f}")
            return it

    print(f"Stopped at max_iter={max_iter}  last_delta={last_delta:.3e}  sum={sum(a.rank for a in airportList):.12f}")
    return max_iter

def outputPageRanks():
    order = sorted(range(len(airportList)),
                   key=lambda i: airportList[i].rank,
                   reverse=True)
    with open("pagerank_airports.txt", "w", encoding="utf-8") as f:
        for i in order:
            a = airportList[i]
            f.write(f"{a.rank:.12f}\t{a.name}\n")

    print("Top-10:")
    for pos, i in enumerate(order[:10], 1):
        a = airportList[i]
        print(f"{pos:2d}. {a.rank:.8f}  {a.name}")

def main(argv=None):
    readAirports("data/airports.txt")
    readRoutes("data/routes.txt")
    time1 = time.time()
    iterations = computePageRanks()
    time2 = time.time()
    outputPageRanks()
    print("#Iterations:", iterations)
    print("Time of computePageRanks():", time2 - time1)
    print(f"Sum of ranks: {sum(a.rank for a in airportList):.12f}")


if __name__ == "__main__":
    sys.exit(main())
