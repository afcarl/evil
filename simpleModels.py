from  __future__ import print_function, division
from lib import *
from run import *

@setting
def SA(): return o(
    p=0.25,
    cooling=1,
    kmax=1000,
    epsilon=0.01,
    cxt={},
    era=100,
    lives=5,
    verbose=False)
           
class ZDT1(Function):
  def f1(i,state):
    return state['0']
  def f2(i,state):
    g = 1 + 9 * sum(state[str(x)] for x in range(30))/30
    return g * round(1- sqrt(state['0']/g))
  def things(i):
    d =dict(T  = Time(),
            f1 = Aux("f1",obj=i.f1,goal=lt),
            f2 = Aux("f2",obj=i.f2,goal=lt))
    for x in xrange(30):
      d[str(x)] =  Aux(str(x),lo=0,hi=1,touch=True)
    return Things(**d)

class DTLZ7(Function):
  "Has M-1 disconnected regions"
  def s(i,st,n): return st[str(n)]
    
  def __init__(i,m=20):
    i.m = m # which w eill process as 0 ... i.m - 1
  def g(i,st):
    return  1 + 9/i.m * sum(i.s(st,x) for x in xrange(0,i.m))
  def h(i,st,g):
    return i.m - sum([i.s(st,x)/(1+g)*(1+sin(3*pi*i.s(st,x)))
                      for x in xrange(0,i.m - 1)])
  def fn(i,n):
    return lambda st:i.f(n,st)
  def f(i,n,st):
    if n < (i.m - 2) :
      return i.s(st,n)
    else:
      g = i.g(st,)
      h = i.h(st,g)
      return (1 + g)*h
  def things(i):
    d = dict(T=Time())
    for x in xrange(i.m):
      d[    str(x)]= Aux(str(x),lo=0,hi=1, touch=True)
      d["f"+str(x)]= Aux(str(x),lo=0,hi=1, obj = i.fn(x))
    return Things(**d)
#tip: every new model is a big deal. new pony to ride. or, at least, to debug


def sa(fun, p=None, cooling=None,kmax=None,
            epsilon=None, cxt=None, era=None,
            lives=None, verbose=None):
  eb = None
  def p(old,new,t): return e**((new-old)/(t+1))
  def decs()      : return decisions(fun.things(),cxt)
  def mutant(st)  : return mutate(fun.things(),st,cxt,p)
  def objs(st)    : return fun.things().objectives(st)
  def baseline()  : [ seen(decs()) for _ in xrange(era) ]
  def improving() :
    return last and last.scores.above(now.scores,epsilon)
  def seen(st): 
    st = objs(st)
    now.add(st)
    always.add(st)
    score = always.overall(st)
    if score < eb:
      now.scores += score
    return st,score
  #=======================
  last, now, always = None, Log(fun.things()), Log(fun.things())
  baseline()
  life = lives
  k = 0
  s,e = sb,eb = seen(decs())
  if verbose: say("[%2s] %.3f "% (life,eb))
  while True:
    if eb < epsilon  : verbose and say("="); break
    if life < 1      : verbose and say("x"); break
    if k > kmax - era: verbose and say("0"); break
    k += 1
    mark = "."
    sn,en = seen(mutant(s))
    if en < eb:
      sb,eb = sn,en
      if verbose: say("\033[7m!\033[m")
    if en < e:
      s,e = sn,en 
      mark = "+"
    elif p(e,en,(k/kmax)**(1/cooling)) < r():
      s,e = sn, en
      mark="?"
    if k % era: 
      if verbose: say(mark)
    else: 
      if verbose:
        say("\n[%2s] %.3f %s" % (life,eb,mark))
      life = lives if improving() else life - 1
      last, now  = now, Log(fun.things())
  if verbose:
    print("\n");print(dict(eb=eb,life=life,k=k))
  return sb,eb
 
def _sa1():
  # if i added cxt, worse final scores
   with study('ZDT1',use(SA,lives=9,kmax=1000,era=100,
                         epsilon =0.01,p=0.33,cooling=0.1,
                         verbose=True)):
     s,e=sa(ZDT1())
     print("")
     print(e)

#_sa1()

def _sa2():
  # if i added cxt, worse final scores
  with study('DTZL',use(SA,lives=9,kmax=10000,era=200,
                        epsilon=0.01,p=0.33,cooling=0.10,
                        verbose=True)):
    s,e=sa(DTLZ7(),**the.SA)
    print(e)                   

#_sa2()

@setting
def DE(): return o(
    f=0.5, cf=0.5, pop=10, kmax=1000,
    epsilon=0.01, cxt={}, 
    lives=5, verbose=False)

def de(fun, f=None, cf=None, pop=None, kmax=None,
            epsilon=None, cxt=None,
            lives=None, verbose=None):
  eb  = 1e32
  def any1(): st,_ = any(all); return st
  def decs()      : return decisions(fun.things(),cxt)
  def mutant()    : return smear(fun.things(),
                                 any1(),any1(), any1(),
                                 f=f,cf=cf,cxt=cxt)
  def objs(st)    : return fun.things().objectives(st)
  def improving() :
    return last and last.scores.above(now.scores,epsilon)
  def seen(st): 
    st = objs(st)
    now.add(st)
    always.add(st)
    score = always.overall(st)
    now.scores += score
    if score < eb:
      score = eb
    return st,score
  #=======================
  last, now, always = None, Log(fun.things()), Log(fun.things())
  life = lives
  k = 0
  era =  pop*len(fun.things().decs)
  all = [seen(decs())] * era
  while True:
    if eb < epsilon  : verbose and say("="); break
    if life < 1      : verbose and say("x"); break
    if k > kmax - era: verbose and say("0"); break
    more = 0
    for pos in xrange(era):
       parent,score0 = all[pos]
       child,score = seen(mutant())
       k += 1
       if (score < score0):
         more += 1
         all[pos] = child
    if k % era: 
      if verbose: say(" ",more)
    else: 
      if verbose:
        say("\n[%2s] %.3f %s" % (life,eb,more))
      life = lives if improving() else life - 1
      last, now  = now, Log(fun.things())
  if verbose:
    print("\n");print(dict(eb=eb,life=life,k=k))
  return eb

#smeagin


def _de1():
  # if i added cxt, worse final scores
  with study('ZDT1',use(DE,verbose=True)):
    print(the.DE)
    e=de(ZDT1(),**the.DE)
    print(e)                   

_de1()
