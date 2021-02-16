'''
Set the parameters for Covasim.
'''

import numpy as np
import sciris as sc
from .settings import options as cvo # For setting global options
from . import misc as cvm
from . import defaults as cvd

__all__ = ['make_pars', 'reset_layer_pars', 'get_prognoses']


def make_pars(set_prognoses=False, prog_by_age=True, version=None, **kwargs):
    '''
    Create the parameters for the simulation. Typically, this function is used
    internally rather than called by the user; e.g. typical use would be to do
    sim = cv.Sim() and then inspect sim.pars, rather than calling this function
    directly.

    Args:
        set_prognoses (bool): whether or not to create prognoses (else, added when the population is created)
        prog_by_age   (bool): whether or not to use age-based severity, mortality etc.
        kwargs        (dict): any additional kwargs are interpreted as parameter names
        version       (str):  if supplied, use parameters from this Covasim version

    Returns:
        pars (dict): the parameters of the simulation
    '''
    pars = {}

    # Population parameters
    pars['pop_size']     = 20e3     # Number of agents, i.e., people susceptible to SARS-CoV-2
    pars['pop_infected'] = 20       # Number of initial infections
    pars['pop_type']     = 'random' # What type of population data to use -- 'random' (fastest), 'synthpops' (best), 'hybrid' (compromise)
    pars['location']     = None     # What location to load data from -- default Seattle

    # Simulation parameters
    pars['start_day']  = '2020-03-01' # Start day of the simulation
    pars['end_day']    = None         # End day of the simulation
    pars['n_days']     = 60           # Number of days to run, if end_day isn't specified
    pars['rand_seed']  = 1            # Random seed, if None, don't reset
    pars['verbose']    = cvo.verbose  # Whether or not to display information during the run -- options are 0 (silent), 1 (default), 2 (everything)

    # Rescaling parameters
    pars['pop_scale']         = 1    # Factor by which to scale the population -- e.g. pop_scale=10 with pop_size=100e3 means a population of 1 million
    pars['rescale']           = True # Enable dynamic rescaling of the population -- starts with pop_scale=1 and scales up dynamically as the epidemic grows
    pars['rescale_threshold'] = 0.05 # Fraction susceptible population that will trigger rescaling if rescaling
    pars['rescale_factor']    = 1.2  # Factor by which the population is rescaled on each step

    # Network parameters, generally initialized after the population has been constructed
    pars['contacts']        = None  # The number of contacts per layer; set by reset_layer_pars() below
    pars['dynam_layer']     = None  # Which layers are dynamic; set by reset_layer_pars() below
    pars['beta_layer']      = None  # Transmissibility per layer; set by reset_layer_pars() below
    pars['n_imports']       = 0     # Average daily number of imported cases (actual number is drawn from Poisson distribution)

    # Basic disease transmission parameters
    pars['beta_dist']       = dict(dist='neg_binomial', par1=1.0, par2=0.45, step=0.01) # Distribution to draw individual level transmissibility; dispersion from https://www.researchsquare.com/article/rs-29548/v1
    pars['viral_dist']      = dict(frac_time=0.3, load_ratio=2, high_cap=4) # The time varying viral load (transmissibility); estimated from Lescure 2020, Lancet, https://doi.org/10.1016/S1473-3099(20)30200-0

    # Parameters that control settings and defaults for multi-strain runs
    pars['strains']         = None  # Structure for storing strain info
    pars['n_strains']       = 1  # The number of strains currently circulating in the population
    pars['max_strains']     = 30    # For allocating memory with numpy arrays
    pars['cross_immunity']  = 0.5   # Default cross-immunity protection factor
    pars['immunity']        = None  # Matrix of immunity and cross-immunity factors, set by set_immunity() below

    # Strain-specific disease transmission parameters. By default, these are set up for a single strain, but can all be modified for multiple strains
    pars['beta']            = 0.016 # Beta per symptomatic contact; absolute value, calibrated
    pars['asymp_factor']    = 1.0  # Multiply beta by this factor for asymptomatic cases; no statistically significant difference in transmissibility: https://www.sciencedirect.com/science/article/pii/S1201971220302502
    pars['init_immunity']   = 1.0  # Default initial immunity
    pars['half_life']       = dict(asymptomatic=180, mild=180, severe=180)
    pars['dur'] = {}
        # Duration parameters: time for disease progression
    pars['dur']['exp2inf']  = dict(dist='lognormal_int', par1=4.6, par2=4.8) # Duration from exposed to infectious; see Lauer et al., https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7081172/, subtracting inf2sim duration
    pars['dur']['inf2sym']  = dict(dist='lognormal_int', par1=1.0, par2=0.9) # Duration from infectious to symptomatic; see Linton et al., https://doi.org/10.3390/jcm9020538
    pars['dur']['sym2sev']  = dict(dist='lognormal_int', par1=6.6, par2=4.9) # Duration from symptomatic to severe symptoms; see Linton et al., https://doi.org/10.3390/jcm9020538
    pars['dur']['sev2crit'] = dict(dist='lognormal_int', par1=3.0, par2=7.4) # Duration from severe symptoms to requiring ICU; see Wang et al., https://jamanetwork.com/journals/jama/fullarticle/2761044
        # Duration parameters: time for disease recovery
    pars['dur']['asym2rec'] = dict(dist='lognormal_int', par1=8.0,  par2=2.0) # Duration for asymptomatic people to recover; see Wölfel et al., https://www.nature.com/articles/s41586-020-2196-x
    pars['dur']['mild2rec'] = dict(dist='lognormal_int', par1=8.0,  par2=2.0) # Duration for people with mild symptoms to recover; see Wölfel et al., https://www.nature.com/articles/s41586-020-2196-x
    pars['dur']['sev2rec']  = dict(dist='lognormal_int', par1=14.0, par2=2.4) # Duration for people with severe symptoms to recover, 22.6 days total; see Verity et al., https://www.medrxiv.org/content/10.1101/2020.03.09.20033357v1.full.pdf
    pars['dur']['crit2rec'] = dict(dist='lognormal_int', par1=14.0, par2=2.4) # Duration for people with critical symptoms to recover, 22.6 days total; see Verity et al., https://www.medrxiv.org/content/10.1101/2020.03.09.20033357v1.full.pdf
    pars['dur']['crit2die'] = dict(dist='lognormal_int', par1=6.2,  par2=1.7) # Duration from critical symptoms to death, 17.8 days total; see Verity et al., https://www.medrxiv.org/content/10.1101/2020.03.09.20033357v1.full.pdf
        # Severity parameters: probabilities of symptom progression
    pars['rel_symp_prob']   = 1.0  # Scale factor for proportion of symptomatic cases
    pars['rel_severe_prob'] = 1.0  # Scale factor for proportion of symptomatic cases that become severe
    pars['rel_crit_prob']   = 1.0  # Scale factor for proportion of severe cases that become critical
    pars['rel_death_prob']  = 1.0  # Scale factor for proportion of critical cases that result in death
    pars['prog_by_age']     = prog_by_age # Whether to set disease progression based on the person's age
    pars['prognoses']       = None # The actual arrays of prognoses by age; this is populated later

    # Efficacy of protection measures
    pars['iso_factor']   = None # Multiply beta by this factor for diagnosed cases to represent isolation; set by reset_layer_pars() below
    pars['quar_factor']  = None # Quarantine multiplier on transmissibility and susceptibility; set by reset_layer_pars() below
    pars['quar_period']  = 14  # Number of days to quarantine for; assumption based on standard policies

    # Events and interventions
    pars['interventions'] = []   # The interventions present in this simulation; populated by the user
    pars['analyzers']     = []   # Custom analysis functions; populated by the user
    pars['timelimit']     = None # Time limit for the simulation (seconds)
    pars['stopping_func'] = None # A function to call to stop the sim partway through

    # Health system parameters
    pars['n_beds_hosp']    = None # The number of hospital (adult acute care) beds available for severely ill patients (default is no constraint)
    pars['n_beds_icu']     = None # The number of ICU beds available for critically ill patients (default is no constraint)
    pars['no_hosp_factor'] = 2.0  # Multiplier for how much more likely severely ill people are to become critical if no hospital beds are available
    pars['no_icu_factor']  = 2.0  # Multiplier for how much more likely critically ill people are to die if no ICU beds are available

    # Update with any supplied parameter values and generate things that need to be generated
    pars.update(kwargs)
    reset_layer_pars(pars)
    if set_prognoses: # If not set here, gets set when the population is initialized
        pars['prognoses'] = get_prognoses(pars['prog_by_age'], version=version) # Default to age-specific prognoses
    pars = initialize_immunity(pars)  # Initialise immunity

    # If version is specified, load old parameters
    if version is not None:
        version_pars = cvm.get_version_pars(version, verbose=pars['verbose'])
        for key in pars.keys(): # Only loop over keys that have been populated
            if key in version_pars: # Only replace keys that exist in the old version
                pars[key] = version_pars[key]

    return pars


# Define which parameters need to be specified as a dictionary by layer -- define here so it's available at the module level for sim.py
layer_pars = ['beta_layer', 'contacts', 'dynam_layer', 'iso_factor', 'quar_factor']


def reset_layer_pars(pars, layer_keys=None, force=False):
    '''
    Helper function to set layer-specific parameters. If layer keys are not provided,
    then set them based on the population type. This function is not usually called
    directly by the user, although it can sometimes be used to fix layer key mismatches
    (i.e. if the contact layers in the population do not match the parameters). More
    commonly, however, mismatches need to be fixed explicitly.

    Args:
        pars (dict): the parameters dictionary
        layer_keys (list): the layer keys of the population, if available
        force (bool): reset the parameters even if they already exist
    '''

    # Specify defaults for random -- layer 'a' for 'all'
    layer_defaults = {}
    layer_defaults['random'] = dict(
        beta_layer  = dict(a=1.0), # Default beta
        contacts    = dict(a=20),  # Default number of contacts
        dynam_layer = dict(a=0),   # Do not use dynamic layers by default
        iso_factor  = dict(a=0.2), # Assumed isolation factor
        quar_factor = dict(a=0.3), # Assumed quarantine factor
    )

    # Specify defaults for hybrid -- household, school, work, and community layers (h, s, w, c)
    layer_defaults['hybrid'] = dict(
        beta_layer  = dict(h=3.0, s=0.6, w=0.6, c=0.3),  # Per-population beta weights; relative; in part based on Table S14 of https://science.sciencemag.org/content/sci/suppl/2020/04/28/science.abb8001.DC1/abb8001_Zhang_SM.pdf
        contacts    = dict(h=2.0, s=20,  w=16,  c=20),   # Number of contacts per person per day, estimated
        dynam_layer = dict(h=0,   s=0,   w=0,   c=0),    # Which layers are dynamic -- none by default
        iso_factor  = dict(h=0.3, s=0.1, w=0.1, c=0.1),  # Multiply beta by this factor for people in isolation
        quar_factor = dict(h=0.6, s=0.2, w=0.2, c=0.2),  # Multiply beta by this factor for people in quarantine
    )

    # Specify defaults for SynthPops -- same as hybrid except for LTCF layer (l)
    l_pars = dict(beta_layer=1.5,
                  contacts=10,
                  dynam_layer=0,
                  iso_factor=0.2,
                  quar_factor=0.3
    )
    layer_defaults['synthpops'] = sc.dcp(layer_defaults['hybrid'])
    for key,val in l_pars.items():
        layer_defaults['synthpops'][key]['l'] = val

    # Choose the parameter defaults based on the population type, and get the layer keys
    try:
        defaults = layer_defaults[pars['pop_type']]
    except Exception as E:
        errormsg = f'Cannot load defaults for population type "{pars["pop_type"]}": must be hybrid, random, or synthpops'
        raise ValueError(errormsg) from E
    default_layer_keys = list(defaults['beta_layer'].keys()) # All layers should be the same, but use beta_layer for convenience

    # Actually set the parameters
    for pkey in layer_pars:
        par = {} # Initialize this parameter
        default_val = layer_defaults['random'][pkey]['a'] # Get the default value for this parameter

        # If forcing, we overwrite any existing parameter values
        if force:
            par_dict = defaults[pkey] # Just use defaults
        else:
            par_dict = sc.mergedicts(defaults[pkey], pars.get(pkey, None)) # Use user-supplied parameters if available, else default

        # Figure out what the layer keys for this parameter are (may be different between parameters)
        if layer_keys:
            par_layer_keys = layer_keys # Use supplied layer keys
        else:
            par_layer_keys = list(sc.odict.fromkeys(default_layer_keys + list(par_dict.keys())))  # If not supplied, use the defaults, plus any extra from the par_dict; adapted from https://www.askpython.com/python/remove-duplicate-elements-from-list-python

        # Construct this parameter, layer by layer
        for lkey in par_layer_keys: # Loop over layers
            par[lkey] = par_dict.get(lkey, default_val) # Get the value for this layer if available, else use the default for random
        pars[pkey] = par # Save this parameter to the dictionary

    return


def get_prognoses(by_age=True, version=None):
    '''
    Return the default parameter values for prognoses

    The prognosis probabilities are conditional given the previous disease state.

    Args:
        by_age (bool): whether to use age-specific values (default true)

    Returns:
        prog_pars (dict): the dictionary of prognosis probabilities
    '''

    if not by_age: # All rough estimates -- almost always, prognoses by age (below) are used instead
        prognoses = dict(
            age_cutoffs  = np.array([0]),
            symp_probs   = np.array([0.75]),
            severe_probs = np.array([0.10]),
            crit_probs   = np.array([0.04]),
            death_probs  = np.array([0.01]),
        )
    else:
        prognoses = dict(
            age_cutoffs   = np.array([0,       10,      20,      30,      40,      50,      60,      70,      80,      90,]),     # Age cutoffs (lower limits)
            sus_ORs       = np.array([0.34,    0.67,    1.00,    1.00,    1.00,    1.00,    1.24,    1.47,    1.47,    1.47]),    # Odds ratios for relative susceptibility -- from Zhang et al., https://science.sciencemag.org/content/early/2020/05/04/science.abb8001; 10-20 and 60-70 bins are the average across the ORs
            trans_ORs     = np.array([1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00]),    # Odds ratios for relative transmissibility -- no evidence of differences
            comorbidities = np.array([1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00,    1.00]),    # Comorbidities by age -- set to 1 by default since already included in disease progression rates
            symp_probs    = np.array([0.50,    0.55,    0.60,    0.65,    0.70,    0.75,    0.80,    0.85,    0.90,    0.90]),    # Overall probability of developing symptoms (based on https://www.medrxiv.org/content/10.1101/2020.03.24.20043018v1.full.pdf, scaled for overall symptomaticity)
            severe_probs  = np.array([0.00050, 0.00165, 0.00720, 0.02080, 0.03430, 0.07650, 0.13280, 0.20655, 0.24570, 0.24570]), # Overall probability of developing severe symptoms (derived from Table 1 of https://www.imperial.ac.uk/media/imperial-college/medicine/mrc-gida/2020-03-16-COVID19-Report-9.pdf)
            crit_probs    = np.array([0.00003, 0.00008, 0.00036, 0.00104, 0.00216, 0.00933, 0.03639, 0.08923, 0.17420, 0.17420]), # Overall probability of developing critical symptoms (derived from Table 1 of https://www.imperial.ac.uk/media/imperial-college/medicine/mrc-gida/2020-03-16-COVID19-Report-9.pdf)
            death_probs   = np.array([0.00002, 0.00002, 0.00010, 0.00032, 0.00098, 0.00265, 0.00766, 0.02439, 0.08292, 0.16190]), # Overall probability of dying -- from O'Driscoll et al., https://www.nature.com/articles/s41586-020-2918-0; last data point from Brazeau et al., https://www.imperial.ac.uk/mrc-global-infectious-disease-analysis/covid-19/report-34-ifr/
        )
    prognoses = relative_prognoses(prognoses) # Convert to conditional probabilities

    # If version is specified, load old parameters
    if version is not None:
        version_prognoses = cvm.get_version_pars(version, verbose=False)['prognoses']
        for key in version_prognoses.keys(): # Only loop over keys that have been populated
            if key in version_prognoses: # Only replace keys that exist in the old version
                prognoses[key] = np.array(version_prognoses[key])

    # Check that lengths match
    expected_len = len(prognoses['age_cutoffs'])
    for key,val in prognoses.items():
        this_len = len(prognoses[key])
        if this_len != expected_len:
            errormsg = f'Lengths mismatch in prognoses: {expected_len} age bins specified, but key "{key}" has {this_len} entries'
            raise ValueError(errormsg)

    return prognoses


def relative_prognoses(prognoses):
    '''
    Convenience function to revert absolute prognoses into relative (conditional)
    ones. Internally, Covasim uses relative prognoses.
    '''
    out = sc.dcp(prognoses)
    out['death_probs']  /= out['crit_probs']   # Conditional probability of dying, given critical symptoms
    out['crit_probs']   /= out['severe_probs'] # Conditional probability of symptoms becoming critical, given severe
    out['severe_probs'] /= out['symp_probs']   # Conditional probability of symptoms becoming severe, given symptomatic
    return out


def absolute_prognoses(prognoses):
    '''
    Convenience function to revert relative (conditional) prognoses into absolute
    ones. Used to convert internally used relative prognoses into more readable
    absolute ones.

    **Example**::

        sim = cv.Sim()
        abs_progs = cv.parameters.absolute_prognoses(sim['prognoses'])
    '''
    out = sc.dcp(prognoses)
    out['severe_probs'] *= out['symp_probs']   # Absolute probability of severe symptoms
    out['crit_probs']   *= out['severe_probs'] # Absolute probability of critical symptoms
    out['death_probs']  *= out['crit_probs']   # Absolute probability of dying
    return out


def initialize_immunity(pars):
    '''
    Helper function to initialize the immunity matrices.
    Matrix is of size sim['max_strains']*sim['max_strains'] and is initialized with default values
    '''
    # If initial immunity/cross immunity factors are provided, use those, otherwise use defaults
    pars['immunity'] = np.full((pars['max_strains'], pars['max_strains']), np.nan, dtype=cvd.default_float)
    for i in range(pars['n_strains']):
        pars['immunity'][i, i] = pars['init_immunity']
    return pars


def update_immunity(pars, create=True, update_strain=None, immunity_from=None, immunity_to=None,
                    init_immunity=None, half_life=None):
    '''
    Helper function to update the immunity and half_life matrices.
    Matrix is of size sim['max_strains']*sim['max_strains'] and takes the form:
                A       B       ...
        array([[1.0,   1.0,    ...],
               [0.4,   1.0,    ...],
               ...,    ...,    ...])
    ... meaning that people who've had strand A have perfect protection against strand B, but
    people who've had strand B have an initial 40% protection against getting strand A.
    The matrix has nan entries outside of any active strains. The diagonals represent immunity
    against the same strain, meaning people who've had strand A have perfect protection against
    strand A, the same for B.

    Args:
        pars (dict): the parameters dictionary
        update_strain: the index of the strain to update
        immunity_from (array): used when adding a new strain; specifies the immunity protection against existing strains from having the new strain
        immunity_to (array): used when adding a strain; specifies the immunity protection against the new strain from having one of the existing strains
        half_life (dicts): dictionary of floats for half life of new strain

    **Example 1**: #TODO NEEDS UPDATING
        # Adding a strain C to the example above. Strain C gives perfect immunity against strain A
        # and 90% immunity against strain B. People who've had strain A have 50% immunity to strain C,
        # and people who've had strain B have 70% immunity to strain C
        cross_immunity = update_cross_immunity(pars, update_strain=2, immunity_from=[1. 0.9], immunity_to=[0.5, 0.7])
                A       B       C       ...
        array([[1.0,    1.0,    0.5     ...],
               [0.4,    1.0,    0.7     ...],
               [1.0,    0.9,    1.0     ...],
               ...,     ...,    ...,    ...])

    '''
    if create:
        # Cross immunity values are set if there is more than one strain circulating
        # if 'n_strains' isn't provided, assume it's 1
        if not pars.get('n_strains'):
            pars['n_strains'] = 1
        pars = initialize_immunity(pars)
        ns = pars['n_strains'] # Shorten

        # Update all strain-specific values
        for par,val in pars['strains'].items():
            if pars.get(par):
                pars[par] = sc.promotetolist(pars[par]) + sc.promotetolist(val)

        # Update own-immunity, if values have been supplied
        pars['immunity'][:ns, :ns] = pars['cross_immunity']
        if pars.get('init_immunity'):  # Values have been supplied for own-immunity
            np.fill_diagonal(pars['immunity'][:ns,:ns], pars['init_immunity'])

    # Update immunity for a strain if supplied
    if update_strain is not None:

        immunity = pars['immunity']
        # check that immunity_from, immunity_to and init_immunity are provided and the right length.
        # Else use default values
        if immunity_from is None:
            print('Immunity from pars not provided, using default value')
            immunity_from = [pars['cross_immunity']]*pars['n_strains']
        if immunity_to is None:
            print('Immunity to pars not provided, using default value')
            immunity_to = [pars['cross_immunity']]*pars['n_strains']
        if init_immunity is None:
            print('Initial immunity not provided, using default value')
            init_immunity = pars['init_immunity']

        immunity_from   = sc.promotetolist(immunity_from)
        immunity_to     = sc.promotetolist(immunity_to)

        # create the immunity[update_strain,] and immunity[,update_strain] arrays
        new_immunity_row    = np.full(pars['max_strains'], np.nan, dtype=cvd.default_float)
        new_immunity_column = np.full(pars['max_strains'], np.nan, dtype=cvd.default_float)
        for i in range(pars['n_strains']+1):
            if i != update_strain:
                new_immunity_row[i] = immunity_from[i]
                new_immunity_column[i] = immunity_to[i]
            else:
                new_immunity_row[i] = new_immunity_column[i] = init_immunity

        immunity[update_strain, :] = new_immunity_row
        immunity[:, update_strain] = new_immunity_column

        pars['immunity'] = immunity

    return pars
