import numpy as _numpy
from scipy.stats import uniform as _uniform
from scipy.stats import maxwell as _maxwell
from scipy.optimize import fminbound as _fminbound

from .flybys import *

_pc3_to_au3 = ((_numpy.pi**3)/272097792000000000) # 1 parsec^-3 to AU^-3

def _scale(sigma):
  '''
    Converts velocity dispersion (sigma) to scale factor for Maxwell-Boltzmann distributions.
  '''
  return _numpy.sqrt((_numpy.pi*_numpy.square(sigma))/(3.0*_numpy.pi - 8.0))

def _IMF(upper_limit, size=1):
  '''
    Returns an order or magnitude Initial Mass Function (IMF) generator for producing random mass samples.
  '''
  if upper_limit <= 1: return imf_gen_1(size)
  elif upper_limit <= 10: return imf_gen_10(size)
  elif upper_limit <= 100: return imf_gen_100(size)
  else: raise AssertionError('The upper mass limit is too high.')

class StellarEnvironment:
  '''
    This is the AIRBALL StellarEnvironment class.
    It encapsulates the relevant data for a static stellar environment.

    # Example
    my_env = airball.StellarEnvironment(stellar_density=100, velocity_dispersion=10, upper_mass_limit=100, name='My Environment')
    my_star = my_env.random_star()

    If a `maximum_impact_parameter` is not given, AIRBALL attempts to estimate a reasonable one.
    There are predefined subclasses for the LocalNeighborhood, a generic OpenCluster, a generic GlobularCluster, and the Milky Way center GalacticBulge and GalacticCore.
  '''
  def __init__(self, stellar_density, velocity_dispersion, upper_mass_limit, maximum_impact_parameter=None, name=None):
    self._density = stellar_density * _pc3_to_au3 # AU^{-3}
    self.velocity = velocity_dispersion # km/s
    assert upper_mass_limit <= 100, 'The upper mass limit is too high.'
    self.mass_limit = upper_mass_limit # Msun
    self._median_mass = None
    self._maximum_impact_parameter = maximum_impact_parameter
    if name is not None: self.name = name
    else: name = 'Stellar Environment'

  def random_star(self, maximum_impact_parameter=None, size=1):
    '''
      Computes a random star from a stellar environment.
      Returns: Mass (Msun), Impact Parameter (AU), Velocity (km/s)
    '''
    max_impact = None
    if maximum_impact_parameter is not None: max_impact = maximum_impact_parameter
    else: max_impact = self.maximum_impact_parameter
    v = _maxwell.rvs(scale=_scale(self.velocity), size=size) # Velocity of the star at infinity.
    b = max_impact * _numpy.sqrt(_uniform.rvs(size=size)) # Impact parameter of the star.
    m = _IMF(self.mass_limit, size=size) # Mass of the star.
    if size > 1: return _numpy.array([m,b,v])
    else: return _numpy.array([m[0], b[0], v[0]])

  def stats(self):
    ''' 
    Prints a summary of the current stats of the Stellar Environment.
    '''
    s = self.name
    s += "\n------------------------------------------\n"
    s += "Stellar Density:     {0:12.4g} pc^-3\n".format(self._density/_pc3_to_au3)
    s += "Velocity Dispersion: {0:12.4g} km/s\n".format(self.velocity)
    s += "Mass Range:          0.01 - {0:5.4g} Msun\n".format(self.mass_limit)
    s += "Median Mass:         {0:12.4g} Msun\n".format(self.median_mass)
    s += "Max Impact Param:    {0:12.4g} AU\n".format(self.maximum_impact_parameter)
    s += "------------------------------------------"
    print(s)

  @property
  def median_mass(self):
    '''
      Compute the rough median mass of the environment
    '''
    if self._median_mass is None:
      self._median_mass = _numpy.median(_IMF(self.mass_limit, size=int(1e6)))
    return self._median_mass
  
  @median_mass.setter
  def median_mass(self, value):
    self._median_mass = value

  @property
  def maximum_impact_parameter(self):
    '''
      Compute an estimate for the largest impact parameter to affect a Sun-Neptune system.
    '''
    if self._maximum_impact_parameter is None:
      _f = lambda b: _numpy.log10(_numpy.abs(1e-16 - _numpy.abs(relative_energy_change(1.0, 5.2e-05, 30.2, 0.013, self.mass_limit, b, _numpy.sqrt(2.0)*_scale(self.velocity)))))
      bs = _numpy.logspace(1, 6, 1000)
      b0 = bs[_numpy.argmin(_f(bs))]
      self._maximum_impact_parameter = _fminbound(_f, b0/5, 5*b0)
    return self._maximum_impact_parameter
  
  @maximum_impact_parameter.setter
  def maximum_impact_parameter(self, value):
    self._maximum_impact_parameter = value
  

class LocalNeighborhood(StellarEnvironment):
  _maximum_impact_parameter = 10000 # AU
  name = 'Local Neighborhood'
  short_name = 'Local'

  def __init__(self):
    self._density = 0.14 * _pc3_to_au3 # AU^{-3}
    self.velocity = 26 # km/s
    self.mass_limit = 10 # Msun
    self._median_mass = None

class OpenCluster(StellarEnvironment):
  _maximum_impact_parameter = 1000 # AU
  name = 'Open Cluster'
  short_name = 'Open'
  
  def __init__(self):
    self._density = 100 * _pc3_to_au3 # AU^{-3}
    self.velocity = 1 # km/s
    self.mass_limit = 100 # Msun
    self._median_mass = None

class GlobularCluster(StellarEnvironment):
  _maximum_impact_parameter = 5000 # AU
  name = 'Globular Cluster'
  short_name = 'Globular'
  
  def __init__(self):
    self._density = 1000 * _pc3_to_au3 # AU^{-3}
    self.velocity = 10 # km/s
    self.mass_limit = 1 # Msun
    self._median_mass = None

class GalacticBulge(StellarEnvironment):
  _maximum_impact_parameter = 50000 # AU
  name = 'Milky Way Bulge'
  short_name = 'Bulge'
  
  def __init__(self):
    self._density = 50 * _pc3_to_au3 # AU^{-3}
    self.velocity = 120 # km/s
    self.mass_limit = 10 # Msun
    self._median_mass = None

class GalacticCore(StellarEnvironment):
  _maximum_impact_parameter = 50000 # AU
  name = 'Milky Way Core'
  short_name = 'Core'
  
  def __init__(self):
    self._density = 10000 * _pc3_to_au3 # AU^{-3}
    self.velocity = 170 # km/s
    self.mass_limit = 10 # Msun
    self._median_mass = None