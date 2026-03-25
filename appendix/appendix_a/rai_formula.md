# RAI Formula and Variable Definitions

The Renewable Accessibility Index (RAI) is constructed as a weighted composite of three normalized metrics:

RAI_i = w_s * S_i + w_t * T_i + w_p * P_i

Where for county i:

- S_i = normalized renewable surplus ratio score
- T_i = normalized transmission capacity density score
- P_i = normalized proximity score

Variable definitions:

- **Transmission capacity density (GW-miles per sq mile)**: total GW-miles of transmission in county / county area.
- **High-voltage line count (>=345 kV)**: count of high-voltage lines in county.
- **Proximity to renewable surplus counties**: distance (miles) to nearest county where renewable capacity > 2x estimated demand.

Weighting schemes in sensitivity test:

1) Equal weights: surplus 0.33, transmission density 0.33, proximity 0.33 (implemented as 0.33/0.33/0.34 for sum=1)
2) Transmission-heavy: surplus 0.20, transmission density 0.60, proximity 0.20
3) Surplus-heavy: surplus 0.60, transmission density 0.20, proximity 0.20

Quartiles are assigned Q1 (top 25%) to Q4 (bottom 25%) under each scheme.
