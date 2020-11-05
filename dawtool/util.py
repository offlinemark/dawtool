from decimal import Decimal, ROUND_UP


def format_time(total_seconds, hours_fmt=False, precise=False, sep=':', hours_pad=True):
    """
    Convert total_seconds float into a string of the form "02:33:44". total_seconds amounts
    greater than a day will still use hours notation.

    Output is either in minutes "00:00" formatting or hours "00:00:00" formatting.
    Not possible to only produce seconds or days+, etc.

    hours_fmt: Force output to have an hours fields even if the total_seconds
      is less than an hour.
    """

    total_sec = total_seconds if precise else int(total_seconds)
    mins, secs = divmod(total_sec, 60)
    hours, mins = divmod(int(mins), 60)

    if precise:
        fmt_str_mins = '{:02}:{:06.3f}'
        fmt_str_hours = '{:02}:{:02}:{:06.3f}'
    else:
        fmt_str_mins = '{:02}:{:02}'
        if hours_pad:
            fmt_str_hours = '{:02}:{:02}:{:02}'
        else:
            fmt_str_hours = '{}:{:02}:{:02}'

    ret = ''
    if not hours and not hours_fmt:
        ret = fmt_str_mins.format(mins, secs)
    else:
        ret = fmt_str_hours.format(hours, mins, secs)

    return ret.replace(':', sep)

#####

def power_of_two(x):
    return (x & (x-1)) == 0

def beat2measure(beat):
    deci = beat - int(beat)
    beatn = int(beat)
    measure = beatn / 4 + 1
    return measure

def linspace(start, end, totalelem):
    """
    Basically same as numpy.linspace. Cut [start, end] into an array with
    totalelem elements (including start and end) that are an even distance
    apart
    """
    if totalelem == 1:
        return [start]
    gaps = totalelem - 1
    dist = (end-start)/gaps
    return [start + (i*dist) for i in range(totalelem)]

###

def calc_time_elapsed_theoretical(first_bpm, second_bpm, domain):
    """
    Calculate time elapsed between two tempo automation points expressed
    as BPM, over the domain of n beats (float).

    Construct the seconds per beat function to be integrated over the domain.
    """

    # scipy is slow to import, so only do so if we need to.
    import scipy.integrate as integrate

    # vertical line - return 0
    if domain == 0:
        return 0.0

    # horizontal line
    if first_bpm == second_bpm:
        first_spb = 60/first_bpm
        return first_spb * domain

    # sloped line. this can technically handle horizontal too, but it's
    # possibly faster to avoid scipy if we can?
    # construct function for BPM, convert to SPB, then integrate.
    slope = (second_bpm - first_bpm)/domain
    bpm_func = lambda x: slope*x + first_bpm
    spb_func = lambda x: 60/bpm_func(x)
    result, err = integrate.quad(spb_func, 0, domain)
    return result

def spb(bpm):
    'seconds per beat'
    return 60 / bpm
