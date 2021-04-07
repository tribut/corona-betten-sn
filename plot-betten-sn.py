#!/usr/bin/env python3

# %% Imports
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import urllib.request as request
import json
import locale

# %% Fetch remote data
hospital_url = 'https://www.coronavirus.sachsen.de/corona-statistics/rest/hospitalDevelopment.jsp'
incidence_url = 'https://www.coronavirus.sachsen.de/corona-statistics/rest/incidenceDevelopment.jsp'

hospital_data = json.loads(request.urlopen(hospital_url).read())
incidence_data = json.loads(request.urlopen(incidence_url).read())

# %% Post-processing remote data
incidence_saxony = None
for incidence_set in incidence_data:
    if incidence_set['boundingArea'] == 'Sachsen gesamt':
        incidence_saxony = incidence_set['incidenceDevelopment']
        break

if incidence_saxony is None:
    raise SystemExit('Oh noes, saxony is gone...')
else:
    incidence_start = datetime.datetime.fromisoformat(incidence_saxony['startDate'])
    incidence_x = np.array(
        [incidence_start + datetime.timedelta(days=x) for x in
        range(len(incidence_saxony['values']))])
    incidence_saxony['values'] = np.array(
        incidence_saxony['values']).astype(np.double)
    incidence_mask = np.isfinite(incidence_saxony['values'])

hospital_x, occupied_beds = zip(*(hospital_data['numberOfOccupiedBeds']))
_, occupied_beds_its = zip(*(hospital_data['numberOfOccupiedItsBeds']))

# %% Create plot
locale.setlocale(locale.LC_ALL, 'de_DE.UTF_8')
px = 1 / plt.rcParams['figure.dpi']
fig, ax_beds = plt.subplots(figsize=(800*px, 450*px))
ax_incidence = ax_beds.twinx()

# ax_beds.set_xlim(datetime.datetime(2020, 12, 1, 0, 0), incidence_x[-1])
ax_beds.set_xlim(incidence_x[0], incidence_x[-1])

p1, = ax_beds.plot_date(
    mdates.epoch2num(np.divide(hospital_x, 1000)),
    np.subtract(occupied_beds, occupied_beds_its),
    '-', color='tab:brown', label='Belegt auf C19-Normalstation')
p3, = ax_beds.plot_date(
    mdates.epoch2num(np.divide(hospital_x, 1000)),
    occupied_beds,
    ':', color=p1.get_color(), label='Belegt mit C19 gesamt')
bed_threshold = 1300
ax_beds.axhline(y=bed_threshold, color='red', linestyle="--")
ax_beds.text(ax_beds.get_xlim()[0] + 1, bed_threshold*1.05, 'Erneuter Lockdown', color='red')

p2, = ax_incidence.plot_date(
    incidence_x[incidence_mask],
    incidence_saxony['values'][incidence_mask],
    '-', color='green', label='Inzidenz Sachsen')

ax_beds.set_ylabel("Betten")
ax_incidence.set_ylabel("7-Tages-Inzidenz")

ax_beds.yaxis.label.set_color(p1.get_color())
ax_incidence.yaxis.label.set_color(p2.get_color())

tkw = dict(size=4, width=1.5)
ax_beds.tick_params(axis='y', colors=p1.get_color(), **tkw)
ax_incidence.tick_params(axis='y', colors=p2.get_color(), **tkw)

ax_beds.legend(handles=[p1, p3, p2])  # loc='upper left')

fmt_major = mdates.MonthLocator(interval=1)
# fmt_major = mdates.WeekdayLocator()
ax_beds.xaxis.set_major_locator(fmt_major)
fmt_minor = mdates.DayLocator(interval=1)
ax_beds.xaxis.set_minor_locator(fmt_minor)

fig.autofmt_xdate()

# %% Save plot
fig.savefig('inzidenz-betten.pdf')
