import sys
import numpy as np

# CONSTANTS
mjup2mearth = 317.8284065946748  # 1 Mjup in Mearth

template_setup = """

[kima]
obs_after_HARPS_fibers: true / false
GP: true / false
hyperpriors: true / false
trend: true / false

file: filename.txt
units: ms / kms
skip: 0
"""


def need_model_setup(exception):
    print()
    print("[FATAL] Couldn't find the file kima_model_setup.txt")
    print("Probably didn't include a call to save_setup() in the")
    print("RVModel constructor (this is the recommended solution).")
    print("As a workaround, create a file called `kima_model_setup.txt`,")
    print("and add to it (after editting!) the following options:")
    print(template_setup)

    sys.tracebacklimit = 0
    raise exception



def read_datafile(datafile, skip):
    """
    Read data from `datafile` for multiple instruments.
    Can be str, in which case the 4th column is assumed to contain an integer
    identifier of the instrument.
    Or list, in which case each element will be one different filename
    containing three columns each.
    """
    if isinstance(datafile, list):
        data = np.empty((0,3))
        obs = np.empty((0,))
        for i, df in enumerate(datafile):
            d = np.loadtxt(df, usecols=(0,1,2), skiprows=skip)
            data = np.append(data, d, axis=0)
            obs = np.append(obs, (i+1)*np.ones((d.shape[0])))
        return data, obs
    else:
        data = np.loadtxt(datafile, usecols=(0,1,2), skiprows=skip)
        obs = np.loadtxt(datafile, usecols=(3,), skiprows=skip, dtype=int)
        return data, obs


def show_tips():
    """ Show a few tips on how to use kima """
    tips = (
        "Press Ctrl+C in any of kima's plots to copy the figure.",
        "Run 'kima-showresults all' to plot every figure.",
        "Use the 'kima-template' script to create a new bare-bones directory.")
    if np.random.rand() < 0.2:  # only sometimes, otherwise it's annoying :)
        tip = np.random.choice(tips)
        print('[kima TIP] ' + tip)


def apply_argsort(arr1, arr2, axis=-1):
    """
    Apply arr1.argsort() on arr2, along `axis`.
    """
    # check matching shapes
    assert arr1.shape == arr2.shape, "Shapes don't match!"

    i = list(np.ogrid[[slice(x) for x in arr1.shape]])
    i[axis] = arr1.argsort(axis)
    return arr2[i]


def percentile68_ranges(a, min=None, max=None):
    if min is None and max is None:
        mask = np.ones_like(a, dtype=bool)
    elif min is None:
        mask = a < max
    elif max is None:
        mask = a > min
    else:
        mask = (a > min) & (a < max)
    lp, median, up = np.percentile(a[mask], [16, 50, 84])
    return (median, up - median, median - lp)


def percentile68_ranges_latex(a, min=None, max=None):
    median, plus, minus = percentile68_ranges(a, min, max)
    return r'$%.2f ^{+%.2f} _{-%.2f}$' % (median, plus, minus)


def clipped_mean(arr, min, max):
    """ Mean of `arr` between `min` and `max` """
    mask = (arr > min) & (arr < max)
    return np.mean(arr[mask])


def clipped_std(arr, min, max):
    """ std of `arr` between `min` and `max` """
    mask = (arr > min) & (arr < max)
    return np.std(arr[mask])


def get_planet_mass(P, K, e, star_mass=1.0, full_output=False, verbose=False):
    """
    Calculate the planet (minimum) mass Msini given
    orbital period `P`, semi-amplitude `K`, eccentricity `e`, and stellar mass.
    Units:
        P [days]
        K [m/s]
        e []
        star_mass [Msun]
    Returns:
        if P is float: Msini [Mjup], Msini [Mearth]
        if P is array:
            if full_output: mean Msini [Mjup], std Msini [Mjup], Msini [Mjup] (array)
            else: mean Msini [Mjup], std Msini [Mjup], mean Msini [Mearth], std Msini [Mearth]
    """
    if verbose: print('Using star mass = %s solar mass' % star_mass)

    if isinstance(P, float):
        # calculate for one value of the orbital period
        # then K, e, and star_mass should also be floats
        assert isinstance(K, float) and isinstance(e, float)
        assert isinstance(star_mass, float)

        m_mj = 4.919e-3 * star_mass**(2. / 3) * P**(
            1. / 3) * K * np.sqrt(1 - e**2)
        m_me = m_mj * mjup2mearth
        return m_mj, m_me
    else:
        # calculate for an array of periods
        if isinstance(star_mass, tuple) or isinstance(star_mass, list):
            # include (Gaussian) uncertainty on the stellar mass
            star_mass = star_mass[0] + star_mass[1] * np.random.randn(P.size)

        m_mj = 4.919e-3 * star_mass**(2. / 3) * P**(
            1. / 3) * K * np.sqrt(1 - e**2)
        m_me = m_mj * mjup2mearth

        if full_output:
            return m_mj.mean(), m_mj.std(), m_mj
        else:
            return (m_mj.mean(), m_mj.std(), m_me.mean(), m_me.std())


def get_planet_mass_latex(P, K, e, star_mass=1.0, earth=False, **kargs):
    out = get_planet_mass(P, K, e, star_mass, full_output=True, verbose=False)

    if isinstance(P, float):
        if earth:
            return '$%f$' % out[1]
        else:
            return '$%f$' % out[0]
    else:
        if earth:
            return percentile68_ranges_latex(out[2]*mjup2mearth)
        else:
            return percentile68_ranges_latex(out[2])


def get_planet_semimajor_axis(P, K, star_mass=1.0, full_output=False,
                              verbose=False):
    """
    Calculate the semi-major axis of the planet's orbit given
    orbital period `P`, semi-amplitude `K`, and stellar mass.
    Units:
        P [days]
        K [m/s]
        star_mass [Msun]
    Returns:
        if P is float: a [AU]
        if P is array:
            if full_output: mean a [AU], std a [AU], a [AU] (array)
            else: mean a [AU], std a [AU]
    """
    if verbose: print('Using star mass = %s solar mass' % star_mass)

    # gravitational constant G in AU**3 / (Msun * day**2), to the power of 1/3
    f = 0.0666378476025686

    if isinstance(P, float):
        # calculate for one value of the orbital period
        # then K and star_mass should also be floats
        assert isinstance(K, float)
        assert isinstance(star_mass, float)
        a = f * star_mass**(1. / 3) * (P / (2 * np.pi))**(2. / 3)
        return a  # in AU
    else:
        if isinstance(star_mass, tuple) or isinstance(star_mass, list):
            star_mass = star_mass[0] + star_mass[1] * np.random.randn(P.size)
        a = f * star_mass**(1. / 3) * (P / (2 * np.pi))**(2. / 3)

        if full_output:
            return a.mean(), a.std(), a
        else:
            return a.mean(), a.std()


def get_planet_semimajor_axis_latex(P, K, star_mass=1.0, earth=False, **kargs):
    out = get_planet_semimajor_axis(P, K, star_mass, full_output=True,
                                    verbose=False)
    if isinstance(P, float):
        return '$%f$' % out
    else:
        return '$%f$' % out[0]



def lighten_color(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])
