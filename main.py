from map_util import get_center, ztwms_control
from bokeh.plotting import curdoc
from ipyleaflet import Map, WMSLayer, LayersControl, WidgetControl, basemaps, FullScreenControl, LayersControl, \
    MeasureControl
from ipywidgets import Box, VBox, Layout, HTML, Dropdown
from ipywidgets_bokeh import IPyWidget
from bokeh.layouts import column, row, widgetbox, layout
from projections import get_common_crs, get_projection

global m
m = {}
global ztwms_controls
curdoc_element = curdoc()
args = curdoc_element.session_context.request.arguments

wms_urls = [i.decode() for i in args.get('url')]
common_crs = get_common_crs(wms_urls)
ztwms_controls = [ztwms_control(i, 4326) for i in wms_urls]
wms_url = str(args.get('url')[0].decode())  # wms_urls[0]
ztwms = ztwms_control(wms_url, 4326)


def get_widget_state():
    state={}

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
            print('layer: ', str(i.wms_control.children[1].value).strip())
            print('opacity: ', str(i.wms_control.children[2].value).strip())
            print('style: ', str(i.wms_control.children[3].value).strip())
            print('time: ', str(i.wms_control.children[4].value).strip())
            print('elevation: ', str(i.wms_control.children[5].value).strip())


form_layout = Layout(
    display='flex',
    flex_flow='row',
    justify_content='space-between',
    height='100%',
    width='100%',
)


def get_map(wms_url, ztwms_controls, crs, center=None, zoom=None):
    global m
    prj_dict = get_projection(crs)
    # set baselayer by looking  at common projections / crs provided
    # get baselayers(crs) <- run this from  outside get_map() to populate a drop-down menu
    # and use it as input parameter to get map
    # basemap = getbasemap(prj_dict)
    wms_baselayer = WMSLayer(
        url='https://public-wms.met.no/backgroundmaps/northpole.map?bgcolor=0x6699CC&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities',
        layers="world",
        format="image/png",
        transparent=True,
        min_zoom=1,
        crs=prj_dict,
    )
    ztwms = ztwms_control(wms_url, crs)
    # m = Map(basemap={}, center=get_center(ztwms.wms), scroll_wheel_zoom=True, crs=prj_dict, zoom=5)
    if not center:
        center = get_center(ztwms.wms)
    if not zoom:
        zoom = 5
    m = Map(basemap=wms_baselayer, center=center, scroll_wheel_zoom=True, crs=prj_dict, zoom=zoom)
    m.layout.width = '90%'
    m.layout.height = '95%'
    for i in ztwms_controls:
        i.ztwms.crs = prj_dict
        m.add_layer(i.ztwms)
        # widget_control = WidgetControl(widget=i.wms_control, position="topright")
        # m.add_control(widget_control)
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


def placeholder(change):
    global m
    global ztwms_controls
    ztwms_controls_new = [ztwms_control(i, int(crs_selector.value.split(':')[1])) for i in wms_urls]
    for i, v in enumerate(ztwms_controls_new):
        v.wms_control.children[1].value=ztwms_controls[i].wms_control.children[1].value
        v.wms_control.children[2].value=ztwms_controls[i].wms_control.children[2].value
        v.wms_control.children[3].value=ztwms_controls[i].wms_control.children[3].value
        v.wms_control.children[4].value=ztwms_controls[i].wms_control.children[4].value
        v.wms_control.children[5].value=ztwms_controls[i].wms_control.children[5].value
    # get selected basemap
    m = get_map(wms_url, ztwms_controls_new, int(crs_selector.value.split(':')[1]), center=m.center, zoom=m.zoom)
    ztwms_controls=ztwms_controls_new
    layers_control = LayersControl(position='topright')

    control_box = VBox([i.wms_control for i in ztwms_controls])
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

crs_selector.observe(placeholder, "value")

lonlat_label = HTML()
outclick_label = HTML()

init_prj = int(crs_selector.value.split(':')[1])


def initiate_map(wms_urls, init_prj, form_layout, crs_selector, lonlat_label, outclick_label):
    ztwms_controls = [ztwms_control(i, init_prj) for i in wms_urls]
    # get selected basemap
    m = get_map(wms_url, ztwms_controls, init_prj)
    # layers_control = LayersControl(position='topright')

    control_box = VBox([i.wms_control for i in ztwms_controls])
    map_container = Box([VBox([crs_selector, lonlat_label, control_box, outclick_label]), m], layout=form_layout)
    wrapper = IPyWidget(widget=map_container)
    layout = column([wrapper], sizing_mode='scale_both')
    return m, ztwms_controls, layout


# control_box = VBox([i.wms_control for i in ztwms_controls])

# m = get_map(wms_url, ztwms_controls, int(crs_selector.value.split(':')[1]))

m, ztwms_controls, layout = initiate_map(wms_urls, init_prj, form_layout, crs_selector, lonlat_label, outclick_label)

curdoc_element.add_root(layout)
