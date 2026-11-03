import sys
import os
import pandas as pd

# =============================
# KLASIFIKASI TIPHON
# =============================
def tiphon_delay(d):
    if d < 150:
        return "Sangat Baik"
    elif d < 300:
        return "Baik"
    else:
        return "Buruk"

def tiphon_jitter(j):
    if j < 20:
        return "Sangat Baik"
    elif j < 50:
        return "Baik"
    else:
        return "Buruk"

def tiphon_throughput(t_mbps):
    if t_mbps >= 2:
        return "Sangat Baik"
    elif t_mbps >= 1:
        return "Baik"
    elif t_mbps >= 0.512:
        return "Cukup"
    else:
        return "Buruk"

# =============================
# VALIDASI INPUT
# =============================
if len(sys.argv) < 2:
    print("Usage: python qos_csv.py <file.csv/tsv>")
    sys.exit(1)

file_path = sys.argv[1]

# =============================
# LOAD FILE (CSV / TSV)
# =============================
ext = os.path.splitext(file_path)[1].lower()

if ext == ".tsv":
    df = pd.read_csv(file_path, sep="\t", encoding="utf-16", engine="python")
else:
    df = pd.read_csv(file_path, sep=",", encoding="utf-8", engine="python")

df.columns = df.columns.str.lower()

# =============================
# DETEKSI KOLOM PENTING
# =============================
time_cols = [c for c in df.columns if 'time' in c]
len_cols  = [c for c in df.columns if 'len' in c]

if not time_cols or not len_cols:
    print("Kolom time / length tidak ditemukan")
    sys.exit(1)

time_col = time_cols[0]
len_col  = len_cols[0]

df[time_col] = pd.to_numeric(df[time_col], errors='coerce')
df[len_col]  = pd.to_numeric(df[len_col], errors='coerce')

df = df.dropna(subset=[time_col, len_col])
df = df.sort_values(time_col)

# =============================
# DURASI
# =============================
start = df[time_col].min()
end   = df[time_col].max()
duration = end - start

# =============================
# THROUGHPUT
# =============================
throughput = (df[len_col].sum() * 8) / duration
throughput_mbps = throughput / 1e6
throughput_class = tiphon_throughput(throughput_mbps)

# =============================
# DELAY & JITTER
# =============================
df["delay"]  = df[time_col].diff()
df["jitter"] = df["delay"].diff().abs()

avg_delay  = df["delay"].mean() * 1000
avg_jitter = df["jitter"].mean() * 1000

delay_class  = tiphon_delay(avg_delay)
jitter_class = tiphon_jitter(avg_jitter)

# =============================
# PACKET LOSS (WIRESHARK BASED)
# =============================
loss_cols = [c for c in df.columns if 'lost_segment' in c]

if loss_cols:
    lost_packets = df[loss_cols[0]].notna().sum()
else:
    lost_packets = 0

total_packets = len(df)
packet_loss_percent = (lost_packets / total_packets) * 100 if total_packets > 0 else 0

# =============================
# BANDWIDTH (PEAK / SECOND)
# =============================
df["sec"] = (df[time_col] - start).astype(int)
bandwidth = (df.groupby("sec")[len_col].sum() * 8).max()

# =============================
# OUTPUT
# =============================
print("\n=== QoS RESULT ===")
print(f"Duration        : {duration:.2f} s")
print(f"Throughput      : {throughput_mbps:.2f} Mbps ({throughput_class})")
print(f"Avg Delay       : {avg_delay:.2f} ms ({delay_class})")
print(f"Avg Jitter      : {avg_jitter:.2f} ms ({jitter_class})")
print(f"Packet Loss     : {packet_loss_percent:.2f} % ({lost_packets} packet)")
print(f"Max Bandwidth   : {bandwidth/1e6:.2f} Mbps (Peak per second)")
