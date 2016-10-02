#!/usr/bin/env python

class State(object):
   call = 0 # shared state variable
   def next_state(self,cls):
      print '-> %s' % (cls.__name__,),
      self.__class__ = cls

   def show_state(self,i):
      print '%2d:%2d:%s' % (self.call,i,self.__class__.__name__),

class State1(State):
   __call = 0  # state variable
   def __call__(self,ok):
      self.show_state(self.__call)
      self.call += 1
      self.__call += 1
      # transition
      if ok: self.next_state(State2)
      print '' # force new line

class State2(State):
   __call = 0
   def __call__(self,ok):
      self.show_state(self.__call)
      self.call += 1
      self.__call += 1
      # transition
      if ok: self.next_state(State3)
      else: self.next_state(State1)
      print '' # force new line

class State3(State):
   __call = 0
   def __call__(self,ok):
      self.show_state(self.__call)
      self.call += 1
      self.__call += 1
      # transition
      if not ok: self.next_state(State2)
      print '' # force new line

if __name__ == '__main__':
   sm = State1()
   for v in [1,1,1,0,0,0,1,1,0,1,1,0,0,1,0,0,1,0,0]:
      sm(v)
   print '---------'
   print vars(sm)