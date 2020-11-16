"""
Research tool for brute forcing the tempo quantization of a DAW.

- Pick a known automation segment (e.g. 60 -> 120 BPM over 4 beats)
- Measure the DAW time elapsed
- Compute the time elapsed for practical candidate temo quantizations (the
  first 13ish powers of 2)
- See which candidate matches the DAW
"""

import numpy as np

def time_elapsed_interval(start, end, interval, quant):
    """
    Standalone implementation of time elapsed across a linear automation.

    @param start: Start BPM
    @param end: End BPM
    @param interval: Number of beats
    @param quant: Candidate tempo quantization (power of 2; e.g. 16th, 32rd
                  note etc)
    """
    bpms = np.linspace(start, end, quant+1)[:-1]
    spbs = 60 / bpms
    width = interval / quant
    return (spbs * width).sum()

def main():
    for i in range(13):
        quant = 2 ** i
        print(quant, time_elapsed_interval(60, 120, 4, quant))

if __name__ == '__main__':
    main()
