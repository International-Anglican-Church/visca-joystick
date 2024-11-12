from plotly import graph_objects as go

from visca_over_ip import CachingCamera as Camera
# from visca_over_ip import Camera

num_cams = 3

sensitivity_tables = {
    'pan': {'joy': [0, 0.05, 0.3, 0.7, 0.9, 1], 'cam': [0, 0, 2, 8, 15, 20]},
    'tilt': {'joy': [0, 0.07, 0.3, 0.65, 0.85, 1], 'cam': [0, 0, 3, 6, 14, 18]},
    'zoom': {'joy': [0, 0.1, 1], 'cam': [0, 0, 7]},
}

ips = ['172.16.0.201', '172.16.0.202', '172.16.0.206']


if __name__ == '__main__':
    from numpy import interp

    fig = go.Figure()
    for name in ['pan', 'tilt']:
        x = [i * .001 for i in range(1000)]
        y = interp(x, sensitivity_tables[name]['joy'], sensitivity_tables[name]['cam'])
        y = [round(val) for val in y]
        fig.add_trace(go.Scatter(x=x, y=y, name=name))

    fig.show()
