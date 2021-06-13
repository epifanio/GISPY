from ipygis import get_center, ztwms_control, move_buttons
from bokeh.plotting import curdoc
from ipyleaflet import Map, WMSLayer, LayersControl, WidgetControl, basemaps, FullScreenControl, LayersControl, \
    MeasureControl
from ipywidgets import Box, VBox, HBox, Layout, HTML, Dropdown, Button
from ipywidgets_bokeh import IPyWidget
from bokeh.layouts import column, row, widgetbox, layout
from projections import get_common_crs, get_projection
import functools
# import ipyvuetify as v

global m
global ztwms_controls
global wms_urls

curdoc_element = curdoc()
args = curdoc_element.session_context.request.arguments

wms_urls = [i.decode() for i in args.get('url')] # [::-1]

common_crs = get_common_crs(wms_urls)

import ipywidgets as widgets

def move_layer_up(c, x):
    global wms_urls
    wms_urls.insert(c-1, wms_urls.pop(c))
    reload_view('')

def move_layer_down(c, x):
    global wms_urls
    wms_urls.insert(c+1, wms_urls.pop(c))
    reload_view('')


class print_button(widgets.Button):
    def __init__(self, m=None, index=None):
        self.button = widgets.Button(description="Click Me!")
        self.index = index

    def on_button_clicked(self, index):
        index = self.index
        print(self.index)

    def get_button(self):
        self.button.on_click(self.on_button_clicked)
        return self.button

def get_basemap(wms_url, crs, center=None, zoom=None):
    global m
    prj_dict = get_projection(crs)
    wms_baselayer = WMSLayer(
        url='https://public-wms.met.no/backgroundmaps/northpole.map?bgcolor=0x6699CC&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities',
        layers="world",
        format="image/png",
        transparent=True,
        min_zoom=1,
        crs=prj_dict,
    )
    if not center:
        center = [0.0, 0.0]
    if not zoom:
        zoom = 5
    m = Map(basemap=wms_baselayer, center=center, scroll_wheel_zoom=True, crs=prj_dict, zoom=zoom)
    m.layout.width = '90%'
    m.layout.height = '95%'
    layers_control = LayersControl(position='topright')
    m.add_control(FullScreenControl())
    m.add_control(layers_control)

    measure = MeasureControl(
        position='bottomleft',
        active_color='orange',
        primary_length_unit='kilometers'
    )
    m.add_control(measure)
    m.on_interaction(handle_interaction)
    return m


def update_map(m, ztwms_controls, crs):
    prj_dict = get_projection(crs)
    for i in ztwms_controls:
        i.ztwms.crs = prj_dict
        m.add_layer(i.ztwms)
    m.center = get_center(ztwms_controls[0].wms)
    return m


form_layout = Layout(
    display='flex',
    flex_flow='row',
    justify_content='space-between',
    height='100%',
    width='100%',
)


def handle_interaction(**kwargs):
    # mouseup, mouseover, mousemove, preclick, click
    global ztwms_controls
    if kwargs.get("type") == "mousemove":
        lat, lon = kwargs.get("coordinates")
        lat = "%.2f" % round(lat, 4)
        lon = "%.2f" % round(lon, 4)
        lonlat_label.value = f'<p style="font-size:100%;"><b>Latitude: {lat}, Longitude: {lon}</b></p>'
    if kwargs.get('type') == 'click':
        lat, lon = kwargs.get("coordinates")
        lat = "%.2f" % round(lat, 4)
        lon = "%.2f" % round(lon, 4)
        outclick_label.value = f'<p style="font-size:100%;"><b>Latitude: {lat}, Longitude: {lon}</b></p>'
    if kwargs.get('type') == 'mousedown':
        print(m.bounds, ztwms_controls)
        for i in ztwms_controls:
            # print('type widget: ', str(type(i.wms_control.children[0].children[1])))
            print('layer: ', str(i.wms_control.children[1].value).strip())
            print('opacity: ', str(i.wms_control.children[2].value).strip())
            print('style: ', str(i.wms_control.children[3].value).strip())
            print('time: ', str(i.wms_control.children[4].value).strip())
            print('elevation: ', str(i.wms_control.children[5].value).strip())


def reload_view(change):
    global m
    global ztwms_controls
    global wms_urls
    m = get_basemap(wms_urls[0], int(crs_selector.value.split(':')[1]))
    ztwms_controls_new = [ztwms_control(wms_url=v, crs=int(crs_selector.value.split(':')[1]), m=m, ipygis_key=str(i))
                          for i, v in enumerate(wms_urls)]

    m = update_map(m, ztwms_controls_new, int(crs_selector.value.split(':')[1]))
    ztwms_controls = ztwms_controls_new
    control_box = VBox([i.wms_control for i in ztwms_controls[::-1]])  ### ?
    for i, v in enumerate(control_box.children):
        move_up = Button(description='^', layout=Layout(width='30px', height='30px'))
        move_up.on_click(functools.partial(move_layer_up, i))
        move_down = Button(description='v', layout=Layout(width='30px', height='30px'))
        move_down.on_click(functools.partial(move_layer_down, i))
        v.children[0].children += (HBox([move_up,
                                         move_down]), )
        print('executed', i)
    map_container = Box([VBox([crs_selector, lonlat_label, control_box, outclick_label]), m], layout=form_layout)
    wrapper = IPyWidget(widget=map_container)
    layout = column([wrapper], sizing_mode='scale_both')
    curdoc_element.clear()
    curdoc_element.add_root(layout)


crs_selector = Dropdown(
    options=common_crs,
    value=common_crs[0],
    description='<font style="text-align:left;"><b>CRS:</b></font>',
    layout=Layout(max_width="280px", max_height="35px"),
)

crs_selector.observe(reload_view, "value")

lonlat_label = HTML()
outclick_label = HTML()

init_prj = int(crs_selector.value.split(':')[1])

def initiate_map(wms_urls, init_prj, form_layout, crs_selector, lonlat_label, outclick_label):
    # get selected basemap
    m = get_basemap(wms_urls[0], init_prj)
    ztwms_controls = [ztwms_control(wms_url=v, crs=init_prj, m=m, ipygis_key=str(i)) for i, v in enumerate(wms_urls)]
    m = update_map(m, ztwms_controls, init_prj)
    control_box = VBox([i.wms_control for i in ztwms_controls[::-1]])
    for i, v in enumerate(control_box.children):
        move_up = Button(description='^', layout=Layout(width='30px', height='30px'))
        move_up.on_click(functools.partial(move_layer_up, i))
        move_down = Button(description='v', layout=Layout(width='30px', height='30px'))
        move_down.on_click(functools.partial(move_layer_down, i))
        v.children[0].children += (HBox([move_up,
                                         move_down]), )
    map_container = Box([VBox([crs_selector, lonlat_label, control_box, outclick_label]), m],
                        layout=form_layout)
    return m, ztwms_controls, map_container


m, ztwms_controls, map_container = initiate_map(wms_urls, init_prj, form_layout, crs_selector, lonlat_label,
                                                outclick_label)

wrapper = IPyWidget(widget=map_container)
layout = column([wrapper], sizing_mode='scale_both')

curdoc_element.add_root(layout)
