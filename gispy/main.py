from ipygis_ok import get_center, ztwms_control
from bokeh.plotting import curdoc
from ipyleaflet import Map, WMSLayer, FullScreenControl, LayersControl, \
    MeasureControl
from ipywidgets import VBox, HBox, Layout, HTML, Button
from ipywidgets_bokeh import IPyWidget
from bokeh.layouts import column, row
from bokeh.models import Button as bkButton
from bokeh.models import Select, Spacer
from projections import get_common_crs, get_projection
import functools
from fontawesome.fontawesome_icon import FontAwesomeIcon

global m
global ztwms_controls
global wms_urls
global wrap_controller_menu

curdoc_element = curdoc()
args = curdoc_element.session_context.request.arguments

wms_urls = [i.decode() for i in args.get('url')]  # [::-1]

common_crs = get_common_crs(wms_urls)


def move_layer_down(index, k):
    global wms_urls
    print(wms_urls)
    if index >= 1 and index <= len(wms_urls):
        wms_urls.insert(index - 1, wms_urls.pop(index))
        reload_view('', '', '')
    else:
        wms_urls
    print(wms_urls)


def move_layer_up(index, k):
    global wms_urls
    print(wms_urls)
    if index <= len(wms_urls) - 2:
        wms_urls.insert(index + 1, wms_urls.pop(index))
        reload_view('', '', '')
    else:
        wms_urls
    print(wms_urls)


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
    m.layout.width = '100%'
    m.layout.height = '100%'
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
            print('layer: ', str(i.wms_control.children[1].children[0].value).strip())
            print('opacity: ', str(i.wms_control.children[1].children[1].value).strip())
            print('style: ', str(i.wms_control.children[1].children[2].value).strip())
            print('time: ', str(i.wms_control.children[1].children[3].value).strip())
            print('elevation: ', str(i.wms_control.children[1].children[4].value).strip())


def reload_view(value, old, new):
    global m
    global ztwms_controls
    global wms_urls
    global wrap_controller_menu
    zoom = m.zoom
    center = m.center
    m = get_basemap(wms_urls[0], int(crs_selector.value.split(':')[1]))
    ztwms_controls_new = [ztwms_control(wms_url=v, crs=int(crs_selector.value.split(':')[1]), m=m, ipygis_key=str(i))
                          for i, v in enumerate(wms_urls)]

    m = update_map(m, ztwms_controls_new, int(crs_selector.value.split(':')[1]))
    m.zoom = zoom
    m.center = center
    ztwms_controls = ztwms_controls_new
    # control_box = VBox([i.wms_control for i in ztwms_controls[::-1]])  ### ?
    control_box = VBox([i.wms_control for i in ztwms_controls[::-1]],
                       layout=Layout(max_height="900px", display='block'))

    for i, v in enumerate(control_box.children[::-1]):
        move_up = Button(description='^',
                         layout=Layout(width='30px', height='30px'),
                         )
        move_up.on_click(functools.partial(move_layer_up, i))
        move_down = Button(description='v',
                           layout=Layout(width='30px', height='30px'),
                           )
        move_down.on_click(functools.partial(move_layer_down, i))
        v.children[0].children += (HBox([move_up,
                                         move_down],
                                        ),
                                   )
        print('executed', i)

    wrap_controller_menu = IPyWidget(widget=control_box,
                                     width_policy='fit'
                                     )
    wrap_map_container = IPyWidget(widget=m, sizing_mode='scale_both', height=900)

    wrap_outclick_label = IPyWidget(widget=outclick_label, width_policy='fit', height=40)
    wrap_lonlat_label = IPyWidget(widget=lonlat_label, width_policy='fit', height=40)

    metadata_button = bkButton(icon=FontAwesomeIcon(icon_name="map", size=2),
                               label="",
                               height=50,
                               width=50, width_policy='fixed')  # ,

    def show_hide_metadata(event):
        if wrap_controller_menu.visible:
            wrap_controller_menu.visible = False
        else:
            wrap_controller_menu.visible = True

    metadata_button.on_click(show_hide_metadata)

    menu_control = column([metadata_button, crs_selector, wrap_lonlat_label, wrap_outclick_label], height_policy='fit')
    wrap_controller_menu_scroll = column([wrap_controller_menu], height=500, height_policy='fit')
    layout = row([menu_control, wrap_map_container, Spacer(width=10, height=10, sizing_mode='fixed'),
                  wrap_controller_menu_scroll], height_policy='fit', sizing_mode='scale_both')

    curdoc_element.clear()
    curdoc_element.add_root(layout)
    wrap_controller_menu.visible = False
    wrap_controller_menu.visible = True


crs_selector = Select(title='CRS',
                      value=common_crs[0],
                      options=common_crs,
                      css_classes=['custom_select'])
crs_selector.on_change('value', reload_view)

lonlat_label = HTML()
outclick_label = HTML()

init_prj = int(crs_selector.value.split(':')[1])


def initiate_map(wms_urls, init_prj):  # , top_box
    # get selected basemap
    m = get_basemap(wms_urls[0], init_prj)
    ztwms_controls = [ztwms_control(wms_url=v, crs=init_prj, m=m, ipygis_key=str(i)) for i, v in enumerate(wms_urls)]
    m = update_map(m, ztwms_controls, init_prj)
    control_box = VBox([i.wms_control for i in ztwms_controls[::-1]],
                       layout=Layout(max_height="900px", display='block'))

    for i, v in enumerate(control_box.children[::-1]):
        move_up = Button(description='^',
                         layout=Layout(width='30px', height='30px'),
                         )
        move_up.on_click(functools.partial(move_layer_up, i))
        move_down = Button(description='v',
                           layout=Layout(width='30px', height='30px'),
                           )
        move_down.on_click(functools.partial(move_layer_down, i))
        v.children[0].children += (HBox([move_up, move_down],
                                        ),
                                   )

    return m, ztwms_controls, control_box


m, ztwms_controls, controller_menu = initiate_map(wms_urls,
                                                  init_prj,
                                                  )

wrap_controller_menu = IPyWidget(widget=controller_menu, width_policy='fit')
wrap_map_container = IPyWidget(widget=m, sizing_mode='scale_both', height=900)

wrap_outclick_label = IPyWidget(widget=outclick_label, width_policy='fit', height=40)
wrap_lonlat_label = IPyWidget(widget=lonlat_label, width_policy='fit', height=40)

metadata_button = bkButton(icon=FontAwesomeIcon(icon_name="map", size=2),
                           label="",
                           height=50,
                           width=50, width_policy='fixed')  # ,


def show_hide_metadata(event):
    if wrap_controller_menu.visible:
        wrap_controller_menu.visible = False
    else:
        wrap_controller_menu.visible = True


metadata_button.on_click(show_hide_metadata)

menu_control = column([metadata_button, crs_selector, wrap_lonlat_label, wrap_outclick_label], height_policy='fit')

wrap_controller_menu_scroll = column([wrap_controller_menu], height=500, height_policy='fit')

layout = row(
    [menu_control, wrap_map_container, Spacer(width=10, height=10, sizing_mode='fixed'), wrap_controller_menu_scroll],
    height_policy='fit', sizing_mode='scale_both')

curdoc_element.add_root(layout)

# http://localhost:5000/gispy? \
#  url=https://thredds.met.no/thredds/wms/sea/norkyst800m/24h/aggregate_be?SERVICE=WMS&REQUEST=GetCapabilities \
# &url=https://thredds.met.no/thredds/wms/cmems/si-tac/cmems_obs-si_arc_phy-siconc_nrt_L4-auto_P1D_aggregated?service=WMS&version=1.3.0&request=GetCapabilities \
# &url=http://nbswms.met.no/thredds/wms_ql/NBS/S1A/2021/05/18/EW/S1A_EW_GRDM_1SDH_20210518T070428_20210518T070534_037939_047A42_65CD.nc?SERVICE=WMS&REQUEST=GetCapabilities
