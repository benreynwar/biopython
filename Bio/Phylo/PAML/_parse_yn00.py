# Copyright (C) 2011 by Brandon Invergo (b.invergo@gmail.com)
# This code is part of the Biopython distribution and governed by its
# license. Please see the LICENSE file that should have been included
# as part of this package.

import re

def parse_ng86(lines, results):
    """ Parse the Nei & Gojobori (1986) section of the resuls.
    Nei_Gojobori results are organized in a lower 
    triangular mattrix, with the sequence names labeling
    the rows and statistics in the format:
    w (dN dS) per column
    Example row (2 columns):
    0.0000 (0.0000 0.0207) 0.0000 (0.0000 0.0421)"""
    sequences = []
    for line in lines:
        # Find all floating point numbers in this line
        line_floats_res = re.findall("-*\d+\.\d+", line)
        line_floats = [float(val) for val in line_floats_res] 
        matrix_row_res = re.match("(.+)\s{5,15}",line)
        if matrix_row_res is not None:
            seq_name = matrix_row_res.group(1).strip()
            sequences.append(seq_name)
            results[seq_name] = {}
            for i in range(0, len(line_floats), 3):
                NG86 = {}
                NG86["omega"] = line_floats[i]
                NG86["dN"] = line_floats[i+1]
                NG86["dS"] = line_floats[i+2]
                results[seq_name][sequences[i//3]] = {"NG86":NG86}
                results[sequences[i//3]][seq_name] = {"NG86":NG86}
    return (results, sequences)
 
def parse_yn00(lines, results, sequences):
    """ Parse the Yang & Nielsen (2000) part of the results.
    Yang & Nielsen results are organized in a table with
    each row comprising one pairwise species comparison.
    Rows are labeled by spequence number rather than by
    sequence name."""
    
    # Example (header row and first table row):
    # seq. seq.     S       N        t   kappa   omega     dN +- SE    dS +- SE
    # 2    1    67.3   154.7   0.0136  3.6564  0.0000 -0.0000 +- 0.0000  0.0150
    # +- 0.0151
    for line in lines:
        # Find all floating point numbers in this line
        line_floats_res = re.findall("-*\d+\.\d+", line)
        line_floats = [float(val) for val in line_floats_res] 
        row_res = re.match("\s+(\d+)\s+(\d+)", line)
        if row_res is not None:
            seq1 = int(row_res.group(1))
            seq2 = int(row_res.group(2))
            seq_name1 = sequences[seq1-1]
            seq_name2 = sequences[seq2-1]
            YN00 = {}
            YN00["S"] = line_floats[0]
            YN00["N"] = line_floats[1]
            YN00["t"] = line_floats[2]
            YN00["kappa"] = line_floats[3]
            YN00["omega"] = line_floats[4]
            YN00["dN"] = line_floats[5]
            YN00["dN SE"] = line_floats[6]
            YN00["dS"] = line_floats[7]
            YN00["dS SE"] = line_floats[8]
            results[seq_name1][seq_name2]["YN00"] = YN00
            results[seq_name2][seq_name1]["YN00"] = YN00
            seq_name1 = None
            seq_name2 = None
    return results

def parse_others(lines, results, sequences):
    """Parse the results from the other methods.

    The remaining methods are grouped together. Statistics
    for all three are listed for each of the pairwise 
    species comparisons, with each method's results on its
    own line.
    The stats in this section must be handled differently
    due to the possible presence of NaN values, which won't
    get caught by my typical "line_floats" method used above.
    """
    # Example:
    # 2 (Pan_troglo) vs. 1 (Homo_sapie)

    # L(i):      143.0      51.0      28.0  sum=    222.0
    # Ns(i):    0.0000    1.0000    0.0000  sum=   1.0000
    # Nv(i):    0.0000    0.0000    0.0000  sum=   0.0000
    # A(i):     0.0000    0.0200    0.0000
    # B(i):    -0.0000   -0.0000   -0.0000
    # LWL85:  dS =  0.0227 dN =  0.0000 w = 0.0000 S =   45.0 N =  177.0
    # LWL85m: dS =    -nan dN =    -nan w =   -nan S =   -nan N =   -nan (rho = -nan)
    # LPB93:  dS =  0.0129 dN =  0.0000 w = 0.0000
    seq_name1 = None
    seq_name2 = None
    for line in lines:
        comp_res = re.match("\d+ \((.+)\) vs. \d+ \((.+)\)", line)
        if comp_res is not None:
            seq_name1 = comp_res.group(1)
            seq_name2 = comp_res.group(2)
        elif seq_name1 is not None and seq_name2 is not None:
            if "dS =" in line:
                stats = {}
                line_stats = line.split(":")[1].strip()
                stats_split = line_stats.split()
                for i in range(0, len(stats_split), 3):
                    stat = stats_split[i].strip("()")
                    if stat == "w":
                        stat = "omega"
                    try:
                        value = stats_split[i+2].strip("()")
                    except IndexError:
                        raise ValueError("Problem with stats line: %r" % line)
                    try:
                        stats[stat] = float(value)
                    except:
                        stats[stat] = None
                if "LWL85:" in line:
                    results[seq_name1][seq_name2]["LWL85"] = stats
                    results[seq_name2][seq_name1]["LWL85"] = stats
                elif "LWL85m" in line:
                    results[seq_name1][seq_name2]["LWL85m"] = stats
                    results[seq_name2][seq_name1]["LWL85m"] = stats
                elif "LPB93" in line:
                    results[seq_name1][seq_name2]["LPB93"] = stats
                    results[seq_name2][seq_name1]["LPB93"] = stats
    return results
