import streamlit as st
import numpy

# -----------------------------------------------------------------------------
# Classes Definition
# -----------------------------------------------------------------------------
class midhaul:
    def __init__(self, chBW=100, mimoLayers=2, noOfSectors=3, modulation="256QAM", tddFactor=0.8, band='FR1DL'):
        self.chBW = chBW
        self.modulation = modulation
        self.mimoLayers = mimoLayers
        self.noOfSectors = noOfSectors
        self.tddFactor = tddFactor
        self.band = band
        
        self.qamToBit = {
            "QPSK": 2, "8QAM": 3, "16QAM": 4, "32QAM": 5, "64QAM": 6, 
            "128QAM": 7, "256QAM": 8, "512QAM": 9, "1024QAM": 10, 
            "2048QAM": 11, "4096QAM": 12, "8192QAM": 13, "16384QAM": 14
        }
        
        self.chBWToNrbAndTone = { 
            20: [106, 15], 40: [216, 15], 50: [270, 15], 100: [273, 30],
            200: [264, 60], 400: [264, 120], 800: [124, 480], 1000: [148, 480]
        }
        
        OHlist = {'FR1DL': 0.14, 'FR1UL': 0.08, 'FR2DL': 0.18, 'FR2UL': 0.1}
        self.OH = OHlist[band]
        self.transportOH = 0.1
        self.scalingFactor = 1
        
    def capacityPeak(self):
        ToneSpacing = self.chBWToNrbAndTone[self.chBW][1]
        mu = numpy.log10(ToneSpacing / 15.0) / numpy.log10(2)
        Tsu = 1E-3 / (14 * 2**mu)
        Rmax = 948 / 1024
        Nrb = self.chBWToNrbAndTone[self.chBW][0]
        capacityPeak = 1E-6 * self.mimoLayers * self.qamToBit[self.modulation] * self.scalingFactor * Rmax * Nrb * 12 / Tsu * (1 - self.OH) * (1 + self.transportOH) * self.tddFactor
        return capacityPeak
        
    def totalCapacityPeak(self):
        return self.capacityPeak() * self.noOfSectors
        
    def totalCapacityNGMN(self):
        meanBusyTime = 0.3 * self.capacityPeak()
        return max([self.capacityPeak(), self.noOfSectors * meanBusyTime])
              
    def totalCapacityConservative(self):
        meanBusyTime = 0.3 * self.capacityPeak()
        return self.capacityPeak() + (self.noOfSectors - 1) * meanBusyTime


class fronthaul:
    def __init__(self, chBW=100, mimoLayers=2, noOfSectors=3, tddFactor=1.0, band='FR1DL', bfp=[9, 4]):
        self.chBW = chBW
        self.mimoLayers = mimoLayers
        self.noOfSectors = noOfSectors
        self.tddFactor = tddFactor
        self.band = band
        self.bfp = bfp
        
        self.chBWToNrbAndTone = { 
            20: [106, 15], 40: [216, 15], 50: [270, 15], 100: [273, 30],
            200: [264, 60], 400: [264, 120], 800: [124, 480], 1000: [148, 480]
        }
        
        OHlist = {'FR1DL': 0.1, 'FR1UL': 0.0, 'FR2DL': 0.1, 'FR2UL': 0.0}
        self.OH = OHlist[band]
        
    def capacityPeak(self):
        ToneSpacing = self.chBWToNrbAndTone[self.chBW][1]
        mu = numpy.log10(ToneSpacing / 15.0) / numpy.log10(2)
        Tsu = 1E-3 / (14 * 2**mu)
        Nrb = self.chBWToNrbAndTone[self.chBW][0]
        # Adding tddFactor to fronthaul calculation to keep behavior aligned with midhaul logic
        capacityPeak = 2E-9 * (1 + self.OH) * self.mimoLayers * Nrb * (12 * self.bfp[0] + self.bfp[1]) / Tsu * self.tddFactor
        return capacityPeak
    
    def totalCapacityPeak(self):
        return self.capacityPeak() * self.noOfSectors
    
    def totalCapacityNGMN(self):
        meanBusyTime = 0.5 * self.capacityPeak()
        return max([self.capacityPeak(), self.noOfSectors * meanBusyTime])
              
    def totalCapacityConservative(self):
        meanBusyTime = 0.5 * self.capacityPeak()
        return self.capacityPeak() + (self.noOfSectors - 1) * meanBusyTime


# -----------------------------------------------------------------------------
# Streamlit UI Definition
# -----------------------------------------------------------------------------
st.set_page_config(page_title="O-RAN Capacity Calculator", layout="wide")

st.title("📡 O-RAN Capacity Calculator")
st.markdown("Calculate Fronthaul and Midhaul capacities based on O-RAN standards.")

# Sidebar Configuration
st.sidebar.header("Configuration Parameters")

link_type = st.sidebar.radio("Select Link Type", ["Midhaul", "Fronthaul"])

st.sidebar.subheader("General Settings")
chBW_options = [20, 40, 50, 100, 200, 400, 800, 1000]
chBW = st.sidebar.selectbox("Channel Bandwidth (MHz)", chBW_options, index=3)

band_options = ['FR1DL', 'FR1UL', 'FR2DL', 'FR2UL']
band = st.sidebar.selectbox("Band Type", band_options, index=0)

mimoLayers = st.sidebar.number_input("MIMO Layers", min_value=1, max_value=64, value=2, step=1)
noOfSectors = st.sidebar.number_input("Number of Sectors", min_value=1, max_value=12, value=3, step=1)
tddFactor = st.sidebar.slider("TDD Factor", min_value=0.0, max_value=1.0, value=0.8 if link_type == "Midhaul" else 1.0, step=0.05)

# Conditional Inputs based on Link Type
if link_type == "Midhaul":
    st.sidebar.subheader("Midhaul Specifics")
    mod_options = ["QPSK", "8QAM", "16QAM", "32QAM", "64QAM", "128QAM", "256QAM", "512QAM", "1024QAM", "2048QAM", "4096QAM", "8192QAM", "16384QAM"]
    modulation = st.sidebar.selectbox("Modulation", mod_options, index=6)
    
    # Initialize the class
    calculator = midhaul(chBW=chBW, mimoLayers=mimoLayers, noOfSectors=noOfSectors, modulation=modulation, tddFactor=tddFactor, band=band)

else:
    st.sidebar.subheader("Fronthaul Specifics (BFP)")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        bfp_mantissa = st.number_input("Mantissa Bits", min_value=1, max_value=16, value=9, step=1)
    with col2:
        bfp_exponent = st.number_input("Exponent Bits", min_value=0, max_value=8, value=4, step=1)
    
    # Initialize the class
    calculator = fronthaul(chBW=chBW, mimoLayers=mimoLayers, noOfSectors=noOfSectors, tddFactor=tddFactor, band=band, bfp=[bfp_mantissa, bfp_exponent])

# -----------------------------------------------------------------------------
# Results Display
# -----------------------------------------------------------------------------
st.subheader(f"Results for {link_type}")
st.write("Using the parameters defined in the sidebar, here are the calculated capacities.")

# Generate metrics
c_peak = calculator.capacityPeak()
c_total_peak = calculator.totalCapacityPeak()
c_ngmn = calculator.totalCapacityNGMN()
c_conservative = calculator.totalCapacityConservative()

# Display side-by-side metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Single Sector Peak", value=f"{c_peak:,.2f}")
    
with col2:
    st.metric(label="Total Peak", value=f"{c_total_peak:,.2f}")
    
with col3:
    st.metric(label="Total NGMN", value=f"{c_ngmn:,.2f}")
    
with col4:
    st.metric(label="Total Conservative", value=f"{c_conservative:,.2f}")

st.divider()
st.markdown("**Note:** The units reflect the raw values returned by the underlying Python class algorithms (usually Mbps for Midhaul and Gbps for Fronthaul formulas containing `1E-6` and `2E-9` respectively).")
