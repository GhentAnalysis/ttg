#
# Class to hold a float and its Gaussian uncertainty
#
from math import sqrt
import numbers

class UncFloat():

  def __init__(self, val, sigma=0):
    if type(val)==type(()):
      if not len(val)==2:                        raise ValueError( "Not possible to construct UncFloat from tuple %r"%val )
      if not isinstance(val[0], numbers.Number): raise ValueError("Not a number: %r"%val[0])
      if not isinstance(val[1], numbers.Number): raise ValueError("Not a number: %r"%val[1])
      self.val   = float(val[0])
      self.sigma = float(val[1])
    elif type(val)==type({}):
      self.__init__((val['val'], val['sigma']))
    else:
      self.__init__((val, sigma))

  def __add__(self, other):
    if not type(other)==type(self):
      if other == 0 or other == None: return self
      elif self == 0 or self == None: return other
      else: raise ValueError( "Can't add, two objects should be UncFloat but is %r."%(type(other)) )
    val   = self.val+other.val
    sigma = sqrt(self.sigma**2+other.sigma**2)
    return UncFloat(val, sigma)

  def __iadd__(self, other):
    self = self + other
    return self

  def __radd__(self, other):
    return self + other

  def __sub__(self, other):
    if not type(other)==type(self):
      raise ValueError( "Can't add, two objects should be UncFloat but is %r."%(type(other)) )
    val   = self.val-other.val
    sigma = sqrt(self.sigma**2+other.sigma**2)
    return UncFloat(val, sigma)

  def __mul__(self, other):
    if not (isinstance(other, numbers.Number) or type(other)==type(self)):
      raise ValueError( "Can't multiply, %r is not a float, int or UncFloat"%type(other) )
    if type(other)==type(self):
      val   = self.val*other.val
      sigma = sqrt((self.sigma*other.val)**2+(self.val*other.sigma)**2)
    elif isinstance(other, numbers.Number):
      val   = self.val*other
      sigma = self.sigma*other
    else:
      raise NotImplementedError("This should never happen.")
    return UncFloat(val, sigma)

  def __rmul__(self, other):
    return self.__mul__(other)

  def __div__(self, other):
    if not ( isinstance(other, numbers.Number) or type(other)==type(self)):
      raise ValueError( "Can't divide, %r is not a float, int or UncFloat"%type(other) )
    if type(other)==type(self):
      val = self.val/other.val
      sigma = (1./other.val)*sqrt(self.sigma**2+((self.val*other.sigma)/other.val)**2)
    elif isinstance(other, numbers.Number):
      val   = self.val/other
      sigma = self.sigma/other
    else:
      raise NotImplementedError("This should never happen.")
    return UncFloat(val, sigma)

  def __lt__(self, other):
    if type(other)==type(self):             return self.val < other.val
    elif isinstance(other, numbers.Number): return self.val < other
    else:                                   raise ValueError("Can only compare with UncFloat, float or int, got %r" % type(other))

  def __gt__(self, other):
    if type(other)==type(self):             return self.val > other.val
    elif isinstance(other, numbers.Number): return self.val > other
    else:                                   raise ValueError("Can only compare with UncFloat, float or int, got %r" % type(other))

  def __eq__(self, other): return not self < other and not self > other
  def __ge__(self, other): return not self < other
  def __le__(self, other): return not self > other
  def __ne__(self, other): return self < other or self > other
  def __abs__(self):       return UncFloat(abs(self.val), self.sigma)
  def __str__(self):       return str(self.val)+'+-'+str(self.sigma)
  def __repr__(self):      return self.__str__()
